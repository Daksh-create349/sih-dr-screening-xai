"""Service layer executing genuine DR screening pipeline without mock data."""

from pathlib import Path
from typing import Dict, Optional
import time
import uuid
import cv2
import numpy as np

from image_quality.scoring import score_image_quality
from image_quality.decision import classify_quality_decision
from image_quality.enhancement import enhance_clahe
from image_quality.report import generate_recapture_feedback
from classifier.model import load_classifier_model
from classifier.predictor import predict_image
from classifier.referable import evaluate_referable_dr, REFERABLE_THRESHOLD
from explainability.gradcam import compute_full_retinal_gradcam
from explainability.evidence import generate_retinal_evidence
from evidence.detector import (
    extract_deep_retinal_evidence,
    detect_optic_disc,
    detect_exudates,
    detect_hemorrhages,
    detect_soft_exudates,
    detect_retinal_vessels,
    detect_microaneurysms,
    is_torch_available,
)
from api.schemas import (
    ScreeningResponse,
    ImageQualityResponse,
    ClassificationResponse,
    ReferableResponse,
    ExplainabilityResponse,
    AnatomyResponse,
    EvidenceResponse,
    ProcessingResponse,
)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = WORKSPACE_ROOT / "results" / "api_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def create_evidence_overlay(
    raw_img: np.ndarray,
    disc_mask: Optional[np.ndarray] = None,
    exudates_mask: Optional[np.ndarray] = None,
    hemorrhages_mask: Optional[np.ndarray] = None,
    soft_exudates_mask: Optional[np.ndarray] = None,
    vessels_mask: Optional[np.ndarray] = None,
    microaneurysms_mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Render anatomical optic disc, hard exudate, hemorrhage, soft exudate lesion contours, microaneurysms, and retinal vascular tree onto fundus image."""
    overlay = raw_img.copy()
    if vessels_mask is not None and np.any(vessels_mask > 0):
        # Soft emerald highlight on retinal vascular tree
        v_idx = (vessels_mask > 0)
        overlay[v_idx] = (0.35 * overlay[v_idx] + 0.65 * np.array([0, 230, 160], dtype=np.uint8)).astype(np.uint8)
    if disc_mask is not None and np.any(disc_mask > 0):
        cnts, _ = cv2.findContours(
            (disc_mask > 0).astype(np.uint8) * 255,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        cv2.drawContours(overlay, cnts, -1, (0, 255, 255), 2)  # Cyan for Optic Disc
    if exudates_mask is not None and np.any(exudates_mask > 0):
        cnts, _ = cv2.findContours(
            (exudates_mask > 0).astype(np.uint8) * 255,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        cv2.drawContours(overlay, cnts, -1, (255, 215, 0), 2)  # Gold/Amber for Hard Exudates
    if hemorrhages_mask is not None and np.any(hemorrhages_mask > 0):
        cnts, _ = cv2.findContours(
            (hemorrhages_mask > 0).astype(np.uint8) * 255,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        cv2.drawContours(overlay, cnts, -1, (255, 45, 85), 2)  # Crimson/Coral Red for Hemorrhages
    if soft_exudates_mask is not None and np.any(soft_exudates_mask > 0):
        cnts, _ = cv2.findContours(
            (soft_exudates_mask > 0).astype(np.uint8) * 255,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        cv2.drawContours(overlay, cnts, -1, (160, 230, 255), 2)  # Soft Lavender-Cyan for Cotton Wool Spots
    if microaneurysms_mask is not None and np.any(microaneurysms_mask > 0):
        # Bright neon orange-amber circular markers for pinpoint microaneurysms
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            (microaneurysms_mask > 0).astype(np.uint8)
        )
        for i in range(1, num_labels):
            cx, cy = int(round(centroids[i][0])), int(round(centroids[i][1]))
            cv2.circle(overlay, (cx, cy), 3, (255, 140, 0), -1)  # Solid orange center
            cv2.circle(overlay, (cx, cy), 5, (255, 200, 0), 1)   # Yellow halo
    return overlay


def create_vessel_asset(raw_img: np.ndarray, vessels_mask: np.ndarray) -> np.ndarray:
    """Create high-contrast retinal angiogram style visualization of segmented vascular tree."""
    green = raw_img[:, :, 1]
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(green)
    base_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)

    v_idx = (vessels_mask > 0)
    base_rgb[v_idx] = (0.2 * base_rgb[v_idx] + 0.8 * np.array([0, 255, 160], dtype=np.uint8)).astype(np.uint8)
    return base_rgb


def create_gradcam_overlay(
    raw_img: np.ndarray,
    warped_cam: np.ndarray,
    alpha: float = 0.45,
) -> np.ndarray:
    """Blend float32 [0, 1] warped heatmap onto RGB image."""
    h, w = raw_img.shape[:2]
    if warped_cam.shape[:2] != (h, w):
        warped_cam = cv2.resize(
            warped_cam, (w, h), interpolation=cv2.INTER_CUBIC
        )
    cam_uint8 = np.uint8(np.clip(warped_cam, 0.0, 1.0) * 255)
    heatmap_bgr = cv2.applyColorMap(cam_uint8, cv2.COLORMAP_JET)
    heatmap_rgb = cv2.cvtColor(heatmap_bgr, cv2.COLOR_BGR2RGB)
    overlay = cv2.addWeighted(raw_img, 1.0 - alpha, heatmap_rgb, alpha, 0)
    return overlay


def run_screening_service(
    file_bytes: bytes,
    filename: str,
) -> ScreeningResponse:
    """Execute complete end-to-end DR screening on uploaded image bytes.

    Pipeline routing:
    1. Validation of image format and byte readability.
    2. Image Quality Assessment (IQA).
    3. Route according to quality gate:
       - UNGRADEABLE: Classifier strictly bypassed. Stop immediately.
       - BORDERLINE: Apply CLAHE enhancement. If accepted, proceed.
       - GOOD: Proceed directly with original image.
    4. Inference (EfficientNetB3).
    5. Referable screening evaluation.
    6. Grad-CAM feature attribution computation.
    7. Anatomical evidence extraction.
    8. Generate visual artifacts (overlay PNG) and return structured payload.
    """
    t_start = time.perf_counter()
    timings: Dict[str, float] = {}

    # 1. Validation
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format: '{ext}'. "
            "Please upload a standard retinal fundus image "
            "in PNG, JPG, or JPEG format."
        )

    if len(file_bytes) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")

    if len(file_bytes) > MAX_FILE_SIZE:
        size_mb = len(file_bytes) / (1024 * 1024)
        raise ValueError(
            f"Uploaded file exceeds the 25 MB limit ({size_mb:.2f} MB)."
        )

    # Decode image from buffer
    t0 = time.perf_counter()
    np_arr = np.frombuffer(file_bytes, np.uint8)
    bgr_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if bgr_img is None:
        raise ValueError(
            "Corrupted or unreadable image file. "
            "Unable to decode retinal fundus photograph."
        )
    orig_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
    t_dec = (time.perf_counter() - t0) * 1000.0
    timings["image_decoding_ms"] = round(t_dec, 2)

    result_id = str(uuid.uuid4())
    result_dir = CACHE_DIR / result_id
    result_dir.mkdir(parents=True, exist_ok=True)

    # Save original image in cache
    cv2.imwrite(
        str(result_dir / "original.png"),
        cv2.cvtColor(orig_img, cv2.COLOR_RGB2BGR),
    )

    # 2. Image Quality Assessment
    t0 = time.perf_counter()
    iqa_scoring = score_image_quality(orig_img)
    iqa_decision = classify_quality_decision(iqa_scoring)
    timings["iqa_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)

    initial_status = iqa_decision["final_class"]
    comp_scores = iqa_decision.get("component_scores", {})
    overall_score = float(iqa_decision["composite_score"])
    triggered_gates = iqa_decision.get("triggered_gates", [])

    enhancement_applied = False
    active_img = orig_img
    effective_status = initial_status

    # 3. Quality Routing Gate
    if initial_status == "UNGRADEABLE":
        # Classifier is STRICTLY BYPASSED
        recapture_msg = generate_recapture_feedback(triggered_gates)
        t_total = round((time.perf_counter() - t_start) * 1000.0, 2)

        return ScreeningResponse(
            result_id=result_id,
            filename=filename,
            screening_status="REJECTED_UNGRADEABLE",
            image_quality=ImageQualityResponse(
                overall_score=overall_score,
                decision=initial_status,
                focus=float(comp_scores.get("focus_score", 0.0)),
                illumination=float(comp_scores.get("illumination_score", 0.0)),
                fov=float(comp_scores.get("fov_score", 0.0)),
                centering=float(comp_scores.get("centering_score", 0.0)),
                enhancement_applied=False,
                initial_decision=initial_status,
                sub_decisions=iqa_scoring.get("sub_decisions"),
                recapture_guidance=recapture_msg,
            ),
            classification=None,
            referable=None,
            explainability=None,
            anatomy=None,
            evidence=None,
            processing=ProcessingResponse(
                total_time_ms=t_total,
                breakdown_ms=timings,
            ),
        )

    # 3. CLAHE Contrast Enhancement
    # Generate CLAHE enhanced asset for visual diagnostic comparison across all gradeable images
    enh_img = enhance_clahe(orig_img)
    cv2.imwrite(
        str(result_dir / "enhanced.png"),
        cv2.cvtColor(enh_img, cv2.COLOR_RGB2BGR),
    )

    if initial_status == "BORDERLINE":
        t0 = time.perf_counter()
        recheck_sc = score_image_quality(enh_img)
        recheck_dec = classify_quality_decision(recheck_sc)
        timings["enhancement_ms"] = round(
            (time.perf_counter() - t0) * 1000.0, 2
        )

        # Evaluate whether enhancement is accepted for downstream classifier
        if recheck_dec["composite_score"] >= overall_score:
            active_img = enh_img
            enhancement_applied = True
            effective_status = recheck_dec["final_class"]
            overall_score = float(recheck_dec["composite_score"])
            comp_scores = recheck_dec.get("component_scores", comp_scores)

    # 4. Deep Classifier Inference
    t0 = time.perf_counter()
    model = load_classifier_model()
    pred = predict_image(active_img, model=model)
    timings["classification_ms"] = round(
        (time.perf_counter() - t0) * 1000.0, 2
    )

    pred_grade = int(pred["predicted_grade"])
    pred_label = str(pred["class_name"])
    probs = {int(k): float(v) for k, v in pred["probabilities"].items()}
    top_prob = float(pred["confidence"])

    # 5. Referable DR Screening Decision
    t0 = time.perf_counter()
    raw_probs_list = [probs[g] for g in range(5)]
    ref_eval = evaluate_referable_dr(
        raw_probs_list, threshold=REFERABLE_THRESHOLD
    )
    timings["referable_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)

    # 6. Grad-CAM Computation & Visualization Overlay
    t0 = time.perf_counter()
    cam_data = compute_full_retinal_gradcam(
        active_img, model=model, target_class=pred_grade
    )
    warped_cam = cam_data["warped_retinal_heatmap"]
    overlay_img = create_gradcam_overlay(orig_img, warped_cam, alpha=0.45)

    # Save visual artifacts
    cam_uint8 = np.uint8(np.clip(warped_cam, 0.0, 1.0) * 255)
    cv2.imwrite(
        str(result_dir / "gradcam.png"),
        cv2.applyColorMap(cam_uint8, cv2.COLORMAP_JET),
    )
    cv2.imwrite(
        str(result_dir / "overlay.png"),
        cv2.cvtColor(overlay_img, cv2.COLOR_RGB2BGR),
    )
    timings["gradcam_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)

    # 7. Anatomical Evidence Generation
    t0 = time.perf_counter()
    ev_data = generate_retinal_evidence(
        active_img, model=model, target_class=pred_grade
    )
    timings["evidence_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)

    # 7b. Deep Anatomy & Lesion Segmentation (IDRiD U-Net Models)
    deep_record = None
    deep_lesions = None
    narrative_text = ev_data.get("narrative_summary") or ev_data.get("narrative") or ""

    if is_torch_available():
        try:
            t_deep = time.perf_counter()
            deep_record = extract_deep_retinal_evidence(
                active_img, image_id=result_id, device="cpu"
            )
            timings["deep_evidence_ms"] = round((time.perf_counter() - t_deep) * 1000.0, 2)
            deep_lesions = deep_record.provenance.get("lesion_statistics", {})

            # Synthesize clinical findings into narrative
            additions = []
            if deep_record.optic_disc.is_available():
                od = deep_record.optic_disc
                additions.append(f"Optic Disc localized at ({od.x}, {od.y}) with radius {od.radius}px.")

            exud_cnt = deep_lesions.get("exudate_clusters", 0)
            if exud_cnt > 0:
                area_pct = deep_lesions.get("exudate_area_fraction", 0.0) * 100.0
                csme_risk = deep_lesions.get("macular_edema_risk_level", "LOW")
                additions.append(
                    f"Hard Exudates detector localized {exud_cnt} clusters "
                    f"({area_pct:.2f}% retinal area). DME Risk: {csme_risk}."
                )

            hem_cnt = deep_lesions.get("hemorrhage_clusters", 0)
            if hem_cnt > 0:
                h_area_pct = deep_lesions.get("hemorrhage_area_fraction", 0.0) * 100.0
                h_pixels = deep_lesions.get("hemorrhage_pixels", 0)
                additions.append(
                    f"Retinal Hemorrhages detector localized {hem_cnt} foci "
                    f"({h_pixels} px, {h_area_pct:.2f}% retinal area) indicating active microvascular leakage."
                )

            se_cnt = deep_lesions.get("soft_exudate_clusters", 0)
            if se_cnt > 0:
                se_area_pct = deep_lesions.get("soft_exudate_area_fraction", 0.0) * 100.0
                additions.append(
                    f"Soft Exudates detector identified {se_cnt} cotton wool spots "
                    f"({se_area_pct:.2f}% retinal area) reflecting localized nerve fiber layer ischemia."
                )

            vessel_cnt = deep_lesions.get("vessel_major_branches", 0)
            if vessel_cnt > 0:
                v_density = deep_lesions.get("vessel_density", 0.0) * 100.0
                additions.append(
                    f"Retinal Vasculature mapped ({vessel_cnt} major arcade branches, {v_density:.1f}% vascular density)."
                )

            ma_cnt = deep_lesions.get("microaneurysm_count", 0)
            if ma_cnt > 0:
                ma_area_pct = deep_lesions.get("microaneurysm_area_fraction", 0.0) * 100.0
                additions.append(
                    f"Microaneurysm detector localized {ma_cnt} focal outpouchings "
                    f"({ma_area_pct:.3f}% retinal area) marking earliest pre-clinical capillary wall weakening."
                )

            if additions:
                narrative_text = f"{narrative_text} {' '.join(additions)}"

            # Render evidence contour overlay (Optic disc in cyan, Exudates in gold, Hemorrhages in crimson, Soft exudates in lavender, Vessels in emerald, MAs in orange)
            disc_m = detect_optic_disc(active_img, device="cpu")["mask"]
            exud_m = detect_exudates(active_img, device="cpu", disc_mask=disc_m)["mask"]
            hem_m = detect_hemorrhages(active_img, device="cpu", disc_mask=disc_m)["mask"]
            se_m = detect_soft_exudates(active_img, device="cpu", disc_mask=disc_m)["mask"]
            vessels_m = detect_retinal_vessels(active_img, device="cpu")["mask"]
            ma_m = detect_microaneurysms(active_img, vessel_mask=vessels_m, disc_mask=disc_m)["mask"]
            ev_overlay = create_evidence_overlay(
                orig_img,
                disc_mask=disc_m,
                exudates_mask=exud_m,
                hemorrhages_mask=hem_m,
                soft_exudates_mask=se_m,
                vessels_mask=vessels_m,
                microaneurysms_mask=ma_m,
            )
            cv2.imwrite(
                str(result_dir / "evidence_overlay.png"),
                cv2.cvtColor(ev_overlay, cv2.COLOR_RGB2BGR),
            )
            vessels_asset = create_vessel_asset(orig_img, vessels_m)
            cv2.imwrite(
                str(result_dir / "vessels.png"),
                cv2.cvtColor(vessels_asset, cv2.COLOR_RGB2BGR),
            )
        except Exception:
            pass

    t_total = round((time.perf_counter() - t_start) * 1000.0, 2)
    timings["total_pipeline_ms"] = t_total

    screening_status = (
        "BORDERLINE_PROCEEDED"
        if initial_status == "BORDERLINE"
        else "COMPLETED"
    )

    is_ref = bool(ref_eval["is_referable"])
    ref_status_str = "Referable DR" if is_ref else "Non-Referable DR"
    top_reg = ev_data.get("top_attention_region", "macular")
    landmarks = ev_data.get("anatomical_landmarks", {})

    return ScreeningResponse(
        result_id=result_id,
        filename=filename,
        screening_status=screening_status,
        image_quality=ImageQualityResponse(
            overall_score=overall_score,
            decision=effective_status,
            focus=float(comp_scores.get("focus_score", 0.0)),
            illumination=float(comp_scores.get("illumination_score", 0.0)),
            fov=float(comp_scores.get("fov_score", 0.0)),
            centering=float(comp_scores.get("centering_score", 0.0)),
            enhancement_applied=enhancement_applied,
            initial_decision=initial_status,
            sub_decisions=iqa_scoring.get("sub_decisions"),
            recapture_guidance=None,
            triggered_gates=triggered_gates,
            enhanced_url=f"/api/result/{result_id}/enhanced",
        ),
        classification=ClassificationResponse(
            predicted_class=pred_grade,
            predicted_label=pred_label,
            probabilities=probs,
            top_probability=top_prob,
            model_name=getattr(model, "name", "EfficientNetB3_DR"),
        ),
        referable=ReferableResponse(
            is_referable=is_ref,
            probability=float(ref_eval["referable_probability"]),
            threshold=float(ref_eval["threshold"]),
            status=ref_status_str,
        ),
        explainability=ExplainabilityResponse(
            gradcam_available=True,
            target_class=pred_grade,
            target_score=float(cam_data.get("target_score", 0.0)),
            heatmap_dimensions=list(warped_cam.shape[:2]),
            native_dimensions=[12, 12],
            layer_name="top_conv",
            attention_summary=(
                f"Peak Grad-CAM activation in {top_reg} region "
                f"targeting {pred_label}."
            ),
            gradcam_url=f"/api/result/{result_id}/gradcam",
            overlay_url=f"/api/result/{result_id}/overlay",
        ),
        anatomy=AnatomyResponse(
            optic_disc=landmarks.get("optic_disc"),
            macula=landmarks.get("macula"),
            top_attention_region=top_reg,
            top_attention_mass_pct=float(ev_data.get("top_attention_mass_pct", 0.0)),
            macular_overlap_pct=float(ev_data.get("macular_overlap_pct", 0.0)),
            optic_disc_overlap_pct=float(ev_data.get("optic_disc_overlap_pct", 0.0)),
            attention_bounding_box=ev_data.get("attention_bounding_box"),
            attention_statistics=ev_data.get("attention_statistics"),
        ),
        evidence=EvidenceResponse(
            narrative=narrative_text,
            lesions=deep_lesions,
            structured_record=deep_record.to_dict() if deep_record else None,
            disclaimer=ev_data.get("safety_disclaimer") or (
                "Image quality assessment, DR grading, and model attention "
                "provide technical decision support only; they do not "
                "constitute independent medical diagnosis."
            ),
        ),
        processing=ProcessingResponse(
            total_time_ms=t_total,
            breakdown_ms=timings,
        ),
    )


def get_cached_image_path(result_id: str, image_type: str) -> Optional[Path]:
    """Retrieve path to a cached image asset for a result ID."""
    # Sanitize inputs to avoid path traversal
    safe_id = "".join(c for c in result_id if c.isalnum() or c in "-_")
    if safe_id != result_id:
        return None

    if image_type not in {"original", "gradcam", "overlay", "enhanced", "evidence_overlay", "vessels"}:
        return None

    img_path = CACHE_DIR / safe_id / f"{image_type}.png"
    if img_path.exists() and img_path.is_file():
        return img_path
    return None
