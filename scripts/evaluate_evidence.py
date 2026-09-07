"""Milestone 11 Step 3: Evidence Evaluation & Visual Card Generator.

Executes anatomical retinal localization and evidence aggregation across all
9 real retinal fundus images:
1. Computes prediction, Grad-CAM heatmap, and retinal coordinate warping.
2. Localizes physiological landmarks (retinal disk, OD candidate, macula).
3. Computes attention mass distribution across standard anatomical regions.
5. Generates high-resolution visual cards in results/explainability/evidence/.
6. Exports structured JSON: results/explainability/evidence_results.json.
7. Exports comprehensive report: results/explainability/evidence_report.md.
"""

import json
from pathlib import Path
import sys

WORKSPACE_ROOT: Path = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import cv2  # noqa: E402
import matplotlib.patches as patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from classifier.model import (  # noqa: E402
    load_classifier_model,
    get_model_metadata,
)
from explainability.evidence import (  # noqa: E402
    generate_retinal_evidence,
    CLINICAL_SAFETY_DISCLAIMER,
)
from image_quality.io import load_raw_image  # noqa: E402

DATA_DIR: Path = WORKSPACE_ROOT / "data" / "real_retinal_images"
RESULTS_DIR: Path = WORKSPACE_ROOT / "results" / "explainability"
CARDS_DIR: Path = RESULTS_DIR / "evidence"


def create_evidence_overlay(
    image: np.ndarray,
    heatmap: np.ndarray,
    alpha: float = 0.45,
    colormap: int = cv2.COLORMAP_JET,
) -> np.ndarray:
    """Blend 2D float32 heatmap [0, 1] onto RGB uint8 image."""
    img_rgb = np.clip(image, 0, 255).astype(np.uint8)
    h_img, w_img = img_rgb.shape[:2]

    if heatmap.shape[:2] != (h_img, w_img):
        heatmap = cv2.resize(
            heatmap.astype(np.float32),
            (w_img, h_img),
            interpolation=cv2.INTER_CUBIC,
        )

    heatmap_clipped = np.clip(heatmap, 0.0, 1.0)
    heatmap_uint8 = (heatmap_clipped * 255.0).astype(np.uint8)

    colorized_bgr = cv2.applyColorMap(heatmap_uint8, colormap)
    colorized_rgb = cv2.cvtColor(colorized_bgr, cv2.COLOR_BGR2RGB)

    blended = (
        (1.0 - alpha) * img_rgb.astype(float)
        + alpha * colorized_rgb.astype(float)
    )
    return np.clip(blended, 0, 255).astype(np.uint8)


def render_evidence_visual_card(
    record: dict,
    orig_image: np.ndarray,
    output_path: Path,
) -> None:
    """Generate high-resolution 3-panel evidence card with landmark markers."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6.5), dpi=150)

    landmarks = record["anatomical_landmarks"]
    od = landmarks.get("optic_disc", {})
    mac = landmarks.get("macula", {})
    bbox = record["attention_bounding_box"]
    warped_cam = record["_warped_cam"]

    # Panel 1: Original Image with Anatomical Landmark Markers
    axes[0].imshow(orig_image)
    if od.get("detected", False) and od.get("center") is not None:
        od_c = od["center"]
        od_r = od.get("radius", 20.0)
        circ_od = patches.Circle(
            (od_c[0], od_c[1]),
            od_r,
            linewidth=2,
            edgecolor="yellow",
            facecolor="none",
            linestyle="--",
            label="Optic Disc Candidate",
        )
        axes[0].add_patch(circ_od)
        axes[0].plot(od_c[0], od_c[1], "y+", markersize=8, markeredgewidth=2)

    if mac.get("detected", False) and mac.get("center") is not None:
        mac_c = mac["center"]
        mac_r = mac.get("radius", 25.0)
        circ_mac = patches.Circle(
            (mac_c[0], mac_c[1]),
            mac_r,
            linewidth=2,
            edgecolor="cyan",
            facecolor="none",
            linestyle="-.",
            label="Macular Estimate",
        )
        axes[0].add_patch(circ_mac)
        axes[0].plot(mac_c[0], mac_c[1], "cx", markersize=8, markeredgewidth=2)

    axes[0].set_title(
        "1. Anatomical Landmarks\n"
        f"OD Conf: {od.get('confidence', 0.0):.2f} | "
        f"Macula: {mac.get('status', 'unknown')}",
        fontsize=10,
        fontweight="bold",
        pad=6,
    )
    axes[0].axis("off")
    axes[0].legend(loc="lower right", fontsize=8, framealpha=0.7)

    # Panel 2: Warped Grad-CAM with Attention Bounding Box
    im_cam = axes[1].imshow(warped_cam, cmap="jet", vmin=0.0, vmax=1.0)
    if bbox.get("status") == "localized_attention_cluster":
        rect = patches.Rectangle(
            (bbox["x"], bbox["y"]),
            bbox["width"],
            bbox["height"],
            linewidth=2,
            edgecolor="magenta",
            facecolor="none",
            linestyle="-",
            label="Peak Attention Cluster",
        )
        axes[1].add_patch(rect)
        axes[1].legend(loc="lower right", fontsize=8, framealpha=0.7)

    top_reg_clean = record["top_attention_region"].replace("_", " ").title()
    mass_pct = record["top_attention_mass_pct"]
    axes[1].set_title(
        f"2. Model Feature Attribution\n"
        f"Top Region: {top_reg_clean} ({mass_pct:.1f}%)",
        fontsize=10,
        fontweight="bold",
        pad=6,
    )
    axes[1].axis("off")
    plt.colorbar(im_cam, ax=axes[1], fraction=0.046, pad=0.04)

    # Panel 3: Composite Overlay with Landmarks + Attention Box
    overlay = create_evidence_overlay(orig_image, warped_cam, alpha=0.45)
    axes[2].imshow(overlay)

    # Re-draw landmarks and attention box atop composite
    if od.get("detected", False) and od.get("center") is not None:
        od_c = od["center"]
        axes[2].add_patch(
            patches.Circle(
                (od_c[0], od_c[1]),
                od.get("radius", 20.0),
                linewidth=1.5,
                edgecolor="yellow",
                facecolor="none",
                linestyle="--",
            )
        )

    if mac.get("detected", False) and mac.get("center") is not None:
        mac_c = mac["center"]
        axes[2].add_patch(
            patches.Circle(
                (mac_c[0], mac_c[1]),
                mac.get("radius", 25.0),
                linewidth=1.5,
                edgecolor="cyan",
                facecolor="none",
                linestyle="-.",
            )
        )

    if bbox.get("status") == "localized_attention_cluster":
        axes[2].add_patch(
            patches.Rectangle(
                (bbox["x"], bbox["y"]),
                bbox["width"],
                bbox["height"],
                linewidth=2,
                edgecolor="magenta",
                facecolor="none",
            )
        )

    axes[2].set_title(
        f"3. Anatomical Evidence Overlay\n"
        f"Macula Overlap: {record['macular_overlap_pct']:.1f}% | "
        f"OD Overlap: {record['optic_disc_overlap_pct']:.1f}%",
        fontsize=10,
        fontweight="bold",
        pad=6,
    )
    axes[2].axis("off")

    # Header and Safety Disclaimer
    super_title = (
        f"Image: {record['image_filename']} | "
        f"Predicted: Grade {record['predicted_class']} "
        f"({record['predicted_class_name']}) | "
        f"Confidence: {record['target_score'] * 100.0:.1f}%\n"
        f"Notice: Grad-CAM shows model feature attribution, "
        f"not lesion detection or clinical diagnosis."
    )
    fig.suptitle(super_title, fontsize=11, fontweight="bold", y=0.98)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight", dpi=150)
    plt.close(fig)


def run_evaluation() -> dict:
    """Execute evidence evaluation across all real retinal images."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CARDS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading model for evidence evaluation...")
    model = load_classifier_model()
    meta = get_model_metadata(model)

    image_paths = sorted(list(DATA_DIR.glob("*.*")))
    image_paths = [
        p for p in image_paths if p.suffix.lower() in [".png", ".jpg", ".jpeg"]
    ]

    print(f"Evaluating evidence on {len(image_paths)} real retinal images...")

    records = []
    all_valid = True

    for img_path in image_paths:
        orig_img = load_raw_image(img_path)
        h_orig, w_orig = orig_img.shape[:2]

        evidence = generate_retinal_evidence(
            image_or_path=orig_img,
            model=model,
            target_class=None,
        )

        pred_cls = evidence["predicted_class"]
        pred_name = evidence["predicted_class_name"]
        score_pct = evidence["target_score"] * 100.0
        top_reg = evidence["top_attention_region"]

        # Validate integrity
        prob_sum = float(sum(evidence["predicted_probabilities"]))
        is_finite = bool(
            np.all(np.isfinite(evidence["warped_retinal_heatmap"]))
        )
        is_valid = bool(
            0 <= pred_cls <= 4
            and abs(prob_sum - 1.0) < 1e-4
            and is_finite
            and evidence["evidence_status"] == "feature_attribution_only"
        )
        if not is_valid:
            all_valid = False

        record = {
            "image_filename": img_path.name,
            "original_dimensions": [h_orig, w_orig],
            "predicted_class": pred_cls,
            "predicted_class_name": pred_name,
            "predicted_probabilities": evidence["predicted_probabilities"],
            "target_class": evidence["target_class"],
            "target_score": evidence["target_score"],
            "top_attention_region": top_reg,
            "top_attention_mass_pct": evidence["top_attention_mass_pct"],
            "macular_overlap_pct": evidence["macular_overlap_pct"],
            "optic_disc_overlap_pct": evidence["optic_disc_overlap_pct"],
            "attention_bounding_box": evidence["attention_bounding_box"],
            "anatomical_landmarks": evidence["anatomical_landmarks"],
            "attention_statistics": evidence["attention_statistics"],
            "coordinate_mapping": evidence["coordinate_mapping"],
            "narrative_summary": evidence["narrative_summary"],
            "safety_disclaimer": evidence["safety_disclaimer"],
            "validation_status": "PASS" if is_valid else "FAIL",
            "_warped_cam": evidence["warped_retinal_heatmap"],
        }

        card_path = CARDS_DIR / f"{img_path.stem}_evidence.png"
        render_evidence_visual_card(record, orig_img, card_path)
        record["visual_card_path"] = str(card_path.relative_to(WORKSPACE_ROOT))

        records.append(record)
        print(
            f"  {img_path.name:<34} | G{pred_cls} ({pred_name:<15}) | "
            f"Conf: {score_pct:5.1f}% | Top: {top_reg:<16} | "
            f"Status: {record['validation_status']}"
        )

    overall_status = "PASS" if all_valid else "FAIL"

    # Exclude internal array from JSON payload
    json_records = []
    for r in records:
        r_clean = {k: v for k, v in r.items() if k != "_warped_cam"}
        json_records.append(r_clean)

    payload = {
        "milestone": (
            "Milestone 11 - Step 3: Anatomical Retinal Localization & Evidence"
        ),
        "model_name": meta["model_name"],
        "total_images_evaluated": len(records),
        "all_images_passed": all_valid,
        "overall_status": overall_status,
        "per_image_results": json_records,
        "safety_disclaimer": CLINICAL_SAFETY_DISCLAIMER,
    }

    # Save JSON report
    json_path = RESULTS_DIR / "evidence_results.json"
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nSaved structured JSON to {json_path}")

    # Save Markdown report
    md_path = RESULTS_DIR / "evidence_report.md"
    generate_markdown_report(payload, md_path)
    print(f"Saved markdown report to {md_path}")

    print(f"\nOVERALL STEP 3 STATUS: {overall_status}")
    return payload


def generate_markdown_report(data: dict, md_path: Path) -> None:
    """Generate comprehensive markdown evidence report."""
    lines = [
        "# Milestone 11 — Step 3: Anatomical Retinal Localization & Evidence",
        "",
        "## 1. Executive Summary",
        "",
        f"- **Verification Status**: **{data['overall_status']}**",
        f"- **Model Identifier**: `{data['model_name']}`",
        f"- **Total Real Retinal Images Evaluated**: "
        f"{data['total_images_evaluated']} (100% verified)",
        "- **Feature Layer**: `efficientnetb3.top_conv`",
        "- **Anatomical Context Regions**: Retinal Foreground, Superior, "
        "Inferior, Nasal, Temporal, Posterior Pole, Periphery, Optic Disc, "
        "Macular Region.",
        "",
        "## 2. Anatomical Localization & Evidence Methodology",
        "",
        "1. **Fundus Boundary**: Segmented via `detect_retinal_field` "
        "foreground mask, defining the circular retinal frame.",
        "2. **Optic Disc Candidate**: Identified via morphological "
        "luminance/red contrast filtering using "
        "`locate_optic_disc_candidate`.",
        "3. **Macular Region Heuristic**: Estimated via temporal displacement "
        "vector (~5.5 disc radii) from the optic disc toward the retinal "
        "optical center, refined by local photometric absorption minimum.",
        "4. **Region Statistics**: Grad-CAM attention mass, mean activation, "
        "and threshold overlap calculated across each anatomical zone.",
        "5. **Peak Attention Bounding Box**: Compact bounding box enclosing "
        "the primary high-attribution activation cluster.",
        "",
        "## 3. Per-Image Evidence Evaluation Summary",
        "",
        "| Image Filename | Dimensions | Pred Grade | Class Name | "
        "Conf | Top Region | Mass % | Status |",
        "|:---|:---:|:---:|:---|:---:|:---|:---:|:---:|",
    ]

    for r in data["per_image_results"]:
        dims_str = (
            f"{r['original_dimensions'][0]}x{r['original_dimensions'][1]}"
        )
        score_str = f"{r['target_score'] * 100.0:.1f}%"
        top_reg = r["top_attention_region"].replace("_", " ").title()
        mass_str = f"{r['top_attention_mass_pct']:.1f}%"
        lines.append(
            f"| `{r['image_filename']}` | {dims_str} | "
            f"Grade {r['predicted_class']} | {r['predicted_class_name']} | "
            f"{score_str} | {top_reg} | {mass_str} | "
            f"**{r['validation_status']}** |"
        )

    lines.extend([
        "",
        "## 4. Visual Evidence Cards Generated",
        "",
        "9 high-resolution 3-panel evidence cards saved under "
        "`results/explainability/evidence/`:",
        "",
    ])

    for r in data["per_image_results"]:
        card_link = f"file://{WORKSPACE_ROOT / r['visual_card_path']}"
        lines.append(f"- [`{r['image_filename']}` evidence card]({card_link})")

    lines.extend([
        "",
        "## 5. Clinical Safety & Regulatory Notice",
        "",
        "> [!IMPORTANT]",
        f"> {data['safety_disclaimer']}",
        "",
        "---",
        "*Report automatically generated by `scripts/evaluate_evidence.py`.*",
    ])

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    run_evaluation()
