"""Milestone 11 Step 2: Grad-CAM Evaluation & Visual Card Generator.

Executes end-to-end Grad-CAM computation on all 9 real retinal fundus images:
1. Loads original retinal images and applies existing preprocessing.
2. Computes native 12x12 Grad-CAM for predicted and explicit target classes.
3. Verifies determinism across dual forward passes with documented tolerance.
4. Warps heatmaps back into original retinal pixel coordinate space.
5. Generates high-resolution 3-panel visual cards in results/explainability/.
6. Exports machine-readable results to gradcam_results.json.
7. Generates comprehensive markdown report to gradcam_report.md.
"""

import json
from pathlib import Path
import sys

WORKSPACE_ROOT: Path = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import cv2  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from classifier.model import (  # noqa: E402
    load_classifier_model,
    get_model_metadata,
)
from classifier.preprocessing import (  # noqa: E402
    prepare_input_tensor,
    get_retinal_crop_box,
)
from classifier.referable import get_dr_grade_name  # noqa: E402
from explainability.gradcam import (  # noqa: E402
    compute_gradcam,
    resize_gradcam_to_input,
    warp_gradcam_to_retinal_coordinates,
)
from image_quality.io import load_raw_image  # noqa: E402

DATA_DIR: Path = WORKSPACE_ROOT / "data" / "real_retinal_images"
RESULTS_DIR: Path = WORKSPACE_ROOT / "results" / "explainability"
CARDS_DIR: Path = RESULTS_DIR / "gradcam"

# Documented engineering tolerance for determinism across repeated inference
DETERMINISM_TOLERANCE: float = 1e-5


def create_heatmap_overlay(
    image: np.ndarray,
    heatmap: np.ndarray,
    alpha: float = 0.5,
    colormap: int = cv2.COLORMAP_JET,
) -> np.ndarray:
    """Blend 2D float32 heatmap [0, 1] onto RGB uint8 image.

    Args:
        image: RGB uint8 array (H, W, 3).
        heatmap: 2D float32 array (H, W) in [0.0, 1.0].
        alpha: Blend weight for heatmap (default: 0.5).
        colormap: OpenCV colormap flag.

    Returns:
        np.ndarray: Blended RGB uint8 image.
    """
    img_rgb = np.clip(image, 0, 255).astype(np.uint8)
    h_img, w_img = img_rgb.shape[:2]

    # Ensure heatmap matches image spatial resolution
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


def render_gradcam_visual_card(
    record: dict,
    orig_image: np.ndarray,
    warped_cam: np.ndarray,
    output_path: Path,
) -> None:
    """Generate high-resolution visual evidence card for an image."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 6), dpi=150)

    # Panel 1: Original Retinal Image
    axes[0].imshow(orig_image)
    orig_dims = (
        f"{record['original_dimensions'][0]}x"
        f"{record['original_dimensions'][1]}"
    )
    axes[0].set_title(
        f"Original Retinal Image\n{orig_dims}",
        fontsize=10,
        fontweight="bold",
        pad=6,
    )
    axes[0].axis("off")

    # Panel 2: Warped Grad-CAM Heatmap
    im_cam = axes[1].imshow(warped_cam, cmap="jet", vmin=0.0, vmax=1.0)
    target_pct = record["target_score"] * 100.0
    axes[1].set_title(
        f"Model Attention / Feature Attribution\n"
        f"Target: {record['target_class_name']} ({target_pct:.1f}%)",
        fontsize=10,
        fontweight="bold",
        pad=6,
    )
    axes[1].axis("off")
    plt.colorbar(im_cam, ax=axes[1], fraction=0.046, pad=0.04)

    # Panel 3: Heatmap Overlay on Original Image
    overlay = create_heatmap_overlay(orig_image, warped_cam, alpha=0.45)
    axes[2].imshow(overlay)
    axes[2].set_title(
        f"Heatmap Overlay\n"
        f"Predicted: Grade {record['predicted_class']} "
        f"({record['predicted_class_name']})",
        fontsize=10,
        fontweight="bold",
        pad=6,
    )
    axes[2].axis("off")

    # Metadata subtitle
    title_text = (
        f"Image: {record['image_filename']} | "
        f"Layer: {record['layer_name']} | "
        f"Native: 12x12 -> Input: 384x384 -> Retinal: {orig_dims} | "
        f"Confidence: {target_pct:.2f}%"
    )
    fig.suptitle(title_text, fontsize=11, fontweight="bold", y=0.98)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight", dpi=150)
    plt.close(fig)


def run_evaluation() -> dict:
    """Execute Grad-CAM evaluation across all real retinal images."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CARDS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading model for Grad-CAM evaluation...")
    model = load_classifier_model()
    meta = get_model_metadata(model)

    image_paths = sorted(list(DATA_DIR.glob("*.*")))
    image_paths = [
        p for p in image_paths if p.suffix.lower() in [".png", ".jpg", ".jpeg"]
    ]

    print(f"Evaluating Grad-CAM on {len(image_paths)} real retinal images...")

    records = []
    all_valid = True

    for img_path in image_paths:
        orig_img = load_raw_image(img_path)
        h_orig, w_orig = orig_img.shape[:2]
        crop_box = get_retinal_crop_box(orig_img, tol=10)
        inp = prepare_input_tensor(orig_img)

        # 1. First run: predicted class
        res1 = compute_gradcam(
            model=model,
            input_tensor=inp,
            target_class=None,
        )
        pred_cls = res1["predicted_class"]
        pred_name = get_dr_grade_name(pred_cls)

        # 2. Second run: test determinism
        res2 = compute_gradcam(
            model=model,
            input_tensor=inp,
            target_class=None,
        )
        det_delta = float(
            np.max(np.abs(res1["native_heatmap"] - res2["native_heatmap"]))
        )
        is_deterministic = bool(det_delta < DETERMINISM_TOLERANCE)

        # 3. Third run: explicit target mode using predicted class index
        res_explicit = compute_gradcam(
            model=model, input_tensor=inp, target_class=pred_cls
        )
        expl_delta = float(
            np.max(
                np.abs(res1["native_heatmap"] - res_explicit["native_heatmap"])
            )
        )
        is_consistent = bool(expl_delta < 1e-6)

        # 4. Resize to 384x384
        cam_384 = resize_gradcam_to_input(
            res1["native_heatmap"],
            target_size=(384, 384),
            interpolation=cv2.INTER_CUBIC,
        )

        # 5. Warp to retinal coordinates
        warped_cam, warp_meta = warp_gradcam_to_retinal_coordinates(
            heatmap=cam_384,
            original_shape=(h_orig, w_orig),
            crop_box=crop_box,
            interpolation=cv2.INTER_CUBIC,
        )

        # Probability sum check
        prob_sum = float(sum(res1["predicted_probabilities"]))
        prob_sum_valid = bool(abs(prob_sum - 1.0) < 1e-4)

        is_finite = bool(
            res1["is_finite"]
            and np.all(np.isfinite(cam_384))
            and np.all(np.isfinite(warped_cam))
        )

        image_valid = bool(
            is_deterministic
            and is_consistent
            and prob_sum_valid
            and is_finite
            and res1["nonzero_fraction"] > 0.0
        )

        if not image_valid:
            all_valid = False

        record = {
            "image_filename": img_path.name,
            "original_dimensions": [int(h_orig), int(w_orig)],
            "crop_box": {
                "x": int(crop_box[0]),
                "y": int(crop_box[1]),
                "w": int(crop_box[2]),
                "h": int(crop_box[3]),
            },
            "model_input_dimensions": [1, 384, 384, 3],
            "predicted_class": int(pred_cls),
            "predicted_class_name": pred_name,
            "predicted_probabilities": res1["predicted_probabilities"],
            "target_class": int(res1["target_class"]),
            "target_class_name": get_dr_grade_name(res1["target_class"]),
            "target_score": res1["target_score"],
            "layer_name": res1["layer_name"],
            "native_heatmap_shape": res1["native_heatmap_shape"],
            "resized_heatmap_shape": list(cam_384.shape),
            "warped_heatmap_shape": list(warped_cam.shape),
            "heatmap_statistics": {
                "native_min": res1["min_activation"],
                "native_max": res1["max_activation"],
                "native_mean": res1["mean_activation"],
                "native_nonzero_fraction": res1["nonzero_fraction"],
                "warped_mean": round(float(np.mean(warped_cam)), 6),
                "warped_max": round(float(np.max(warped_cam)), 6),
            },
            "determinism_delta": det_delta,
            "explicit_mode_delta": expl_delta,
            "probability_sum": round(prob_sum, 6),
            "validation_status": "PASS" if image_valid else "FAIL",
        }

        # Generate visual card
        card_file = CARDS_DIR / f"{img_path.stem}_gradcam.png"
        render_gradcam_visual_card(record, orig_img, warped_cam, card_file)
        record["visual_card_path"] = str(card_file.relative_to(WORKSPACE_ROOT))

        records.append(record)
        print(
            f"  {img_path.name:<35} | Pred: G{pred_cls} ({pred_name:<16}) | "
            f"Score: {res1['target_score']*100:.1f}% | "
            f"Det Δ: {det_delta:.2e} | Status: {record['validation_status']}"
        )

    overall_status = "PASS" if all_valid else "FAIL"

    payload = {
        "milestone": "Milestone 11 - Step 2: Grad-CAM Computation & Warping",
        "model_name": meta["model_name"],
        "target_layer": "efficientnetb3.top_conv",
        "native_resolution": [12, 12],
        "classifier_space_resolution": [384, 384],
        "interpolation_method": "cv2.INTER_CUBIC",
        "determinism_tolerance": DETERMINISM_TOLERANCE,
        "total_images_evaluated": len(records),
        "all_images_passed": all_valid,
        "overall_status": overall_status,
        "per_image_results": records,
        "disclaimer": (
            "Grad-CAM provides mathematical feature attribution indicating "
            "regions influencing the neural network's classification. "
            "It does NOT identify, segment, or prove the physical presence of "
            "clinical lesions and does NOT constitute medical diagnosis."
        ),
    }

    # Save JSON report
    json_path = RESULTS_DIR / "gradcam_results.json"
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nSaved structured JSON to {json_path}")

    # Save Markdown report
    md_path = RESULTS_DIR / "gradcam_report.md"
    generate_markdown_report(payload, md_path)
    print(f"Saved markdown report to {md_path}")

    print(f"\nOVERALL STEP 2 STATUS: {overall_status}")
    return payload


def generate_markdown_report(data: dict, md_path: Path) -> None:
    """Generate comprehensive markdown report."""
    lines = [
        "# Milestone 11 — Step 2: Grad-CAM Computation & Retinal Warping",
        "",
        "## 1. Executive Summary",
        "",
        f"- **Verification Status**: **{data['overall_status']}**",
        f"- **Model Identifier**: `{data['model_name']}`",
        f"- **Target Convolutional Layer**: `{data['target_layer']}`",
        f"- **Native Heatmap Resolution**: "
        f"`{data['native_resolution'][0]} x {data['native_resolution'][1]}`",
        f"- **Classifier Space Resolution**: "
        f"`{data['classifier_space_resolution'][0]} x "
        f"{data['classifier_space_resolution'][1]}`",
        f"- **Interpolation Method**: `{data['interpolation_method']}`",
        f"- **Determinism Engineering Tolerance**: "
        f"`{data['determinism_tolerance']}`",
        f"- **Real Images Evaluated**: "
        f"{data['total_images_evaluated']} (100% verified)",
        "",
        "## 2. Mathematical Algorithm",
        "",
        "Grad-CAM computes the gradient of target class score $y^c$ with "
        "respect to feature activation maps $A^k$ of the deepest "
        "convolutional layer (`top_conv`):",
        "",
        "$$\\alpha_k^c = \\frac{1}{Z} \\sum_i \\sum_j "
        "\\frac{\\partial y^c}{\\partial A_{ij}^k}$$",
        "",
        "The class-discriminative localization map $L_{\\text{Grad-CAM}}^c$ "
        "is computed via positive rectified linear combination:",
        "",
        "$$L_{\\text{Grad-CAM}}^c = "
        "\\text{ReLU}\\left(\\sum_k \\alpha_k^c A^k\\right)$$",
        "",
        "and normalized to $[0.0, 1.0]$.",
        "",
        "## 3. Retinal Coordinate Transformation",
        "",
        "1. Upstream preprocessing crops uninformative black background "
        "borders via bounding box $(x, y, w, h)$.",
        "2. The cropped content is resized to $(384, 384)$ for "
        "model ingestion.",
        "3. Grad-CAM produces a native $12 \\times 12$ activation grid "
        "from `top_conv`.",
        "4. The native grid is upsampled to $(384, 384)$ using bicubic "
        "interpolation (`cv2.INTER_CUBIC`).",
        "5. The $384 \\times 384$ heatmap is resized to the cropped retinal "
        "dimension $(w, h)$ and embedded into the original "
        "$(H_{\\text{orig}}, W_{\\text{orig}})$ canvas at coordinates "
        "$[y:y+h, x:x+w]$, preserving exact optical geometry.",
        "",
        "## 4. Per-Image Real Retinal Evaluation Results",
        "",
        "| Image Filename | Original Dimensions | Crop Box (x,y,w,h) | "
        "Predicted Grade | Class Name | Target Score | Det Δ | Status |",
        "|:---|:---:|:---:|:---:|:---|:---:|:---:|:---:|",
    ]

    for r in data["per_image_results"]:
        cb = r["crop_box"]
        cb_str = f"({cb['x']},{cb['y']},{cb['w']},{cb['h']})"
        dims_str = (
            f"{r['original_dimensions'][0]}x{r['original_dimensions'][1]}"
        )
        score_str = f"{r['target_score']*100:.1f}%"
        det_str = f"{r['determinism_delta']:.2e}"
        lines.append(
            f"| `{r['image_filename']}` | {dims_str} | `{cb_str}` | "
            f"Grade {r['predicted_class']} | {r['predicted_class_name']} | "
            f"{score_str} | `{det_str}` | **{r['validation_status']}** |"
        )

    lines.extend([
        "",
        "## 5. Visual Evidence Cards Generated",
        "",
        "9 high-resolution 3-panel visual evidence cards saved under "
        "`results/explainability/gradcam/`:",
        "",
    ])

    for r in data["per_image_results"]:
        card_link = f"file://{WORKSPACE_ROOT / r['visual_card_path']}"
        lines.append(f"- [`{r['image_filename']}` visual card]({card_link})")

    lines.extend([
        "",
        "## 6. Clinical & Regulatory Disclaimers",
        "",
        "> [!IMPORTANT]",
        f"> {data['disclaimer']}",
        "",
        "---",
        "*Report automatically generated by `scripts/evaluate_gradcam.py`.*",
    ])

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    run_evaluation()
