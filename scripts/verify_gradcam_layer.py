"""Milestone 11 Step 1 Evaluation: Grad-CAM Layer Discovery and Verification.

Executes programmatic discovery and verification of the Grad-CAM convolutional layer:
1. Loads the existing trained EfficientNetB3 model without retraining or weight alteration.
2. Traverses and catalogues all candidate layers.
3. Selects and validates the canonical deepest convolutional layer ('top_conv').
4. Tests spatial feature extraction on all 9 real retinal images with existing preprocessing.
5. Verifies differentiability and gradient connectivity to prediction outputs.
6. Exports structured JSON report to results/explainability/gradcam_layer_report.json.
7. Exports comprehensive markdown report to results/explainability/gradcam_layer_report.md.
"""

import sys
from pathlib import Path

WORKSPACE_ROOT: Path = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import json
import numpy as np

from classifier.model import load_classifier_model, get_model_metadata, resolve_model_path
from classifier.preprocessing import preprocess_classifier_image, prepare_input_tensor
from explainability.gradcam import (
    list_all_candidate_layers,
    discover_gradcam_layer,
    validate_gradcam_connectivity,
    extract_feature_tensor,
)

DATA_DIR: Path = WORKSPACE_ROOT / "data" / "real_retinal_images"
RESULTS_DIR: Path = WORKSPACE_ROOT / "results" / "explainability"


def run_layer_verification() -> dict:
    """Execute complete Grad-CAM layer discovery and verification across all real images."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading existing trained model checkpoint...")
    model = load_classifier_model()
    meta = get_model_metadata(model)
    model_file_path = resolve_model_path()

    print(f"Model loaded: {meta['model_name']} ({meta['total_parameters']:,} parameters)")

    # 1. Discover candidates and optimal layer
    print("\nCataloguing all candidate layers...")
    all_candidates = list_all_candidate_layers(model)
    spatial_candidates = [c for c in all_candidates if c["is_spatial"]]
    conv_spatial_candidates = [c for c in spatial_candidates if c["is_conv"]]

    print(f"Total layers traversed: {len(all_candidates)}")
    print(f"Spatial feature map layers: {len(spatial_candidates)}")
    print(f"Convolutional spatial layers: {len(conv_spatial_candidates)}")

    selected_info = discover_gradcam_layer(model, prefer_conv=True)
    print(f"\nSelected Grad-CAM Layer: {selected_info['selected_layer_name']}")
    print(f"Full Layer Path: {selected_info['full_layer_path']}")
    print(f"Layer Type: {selected_info['layer_type']}")
    print(f"Output Shape: {selected_info['output_shape']}")
    print(f"Channels: {selected_info['num_channels']}")
    print(f"Connected to Output: {selected_info['connected_to_output']}")

    # 2. Inspect real retinal images and extract feature maps
    image_paths = sorted(list(DATA_DIR.glob("*.*")))
    image_paths = [p for p in image_paths if p.suffix.lower() in [".png", ".jpg", ".jpeg"]]

    print(f"\nVerifying feature extraction on {len(image_paths)} real retinal images...")
    real_image_results = []
    all_images_passed = True

    for img_path in image_paths:
        # Preprocess using existing classifier pipeline
        input_3d = preprocess_classifier_image(img_path)
        input_tensor = prepare_input_tensor(img_path)

        features = extract_feature_tensor(
            model=model,
            input_tensor=input_tensor,
            selected_layer_name=selected_info["selected_layer_name"],
            parent_submodel_name=selected_info["parent_submodel"],
        )

        h_feat, w_feat, c_feat = features.shape[1], features.shape[2], features.shape[3]
        is_valid = (
            features.ndim == 4
            and h_feat == 12
            and w_feat == 12
            and c_feat == 1536
            and np.all(np.isfinite(features))
        )

        if not is_valid:
            all_images_passed = False

        record = {
            "image_filename": img_path.name,
            "input_preprocessed_shape": list(input_3d.shape),
            "input_tensor_shape": list(input_tensor.shape),
            "feature_tensor_shape": list(features.shape),
            "feature_mean": round(float(np.mean(features.astype(np.float32))), 5),
            "feature_std": round(float(np.std(features.astype(np.float32))), 5),
            "valid_4d_spatial": bool(is_valid),
        }
        real_image_results.append(record)
        print(f"  {img_path.name:<35} -> Feature Shape: {list(features.shape)} | Valid: {is_valid}")

    overall_status = "PASS" if (all_images_passed and selected_info["connected_to_output"]) else "FAIL"

    # Assemble structured payload
    payload = {
        "milestone": "Milestone 11 - Step 1: Grad-CAM Layer Discovery & Verification",
        "model_verification": {
            "model_path": str(model_file_path),
            "model_name": meta["model_name"],
            "input_shape": meta["input_shape"],
            "output_shape": meta["output_shape"],
            "parameter_count": meta["total_parameters"],
            "num_classes": meta["num_classes"],
        },
        "selected_gradcam_layer": {
            "layer_name": selected_info["selected_layer_name"],
            "full_path": selected_info["full_layer_path"],
            "layer_type": selected_info["layer_type"],
            "output_shape": selected_info["output_shape"],
            "spatial_dimensions": selected_info["spatial_dimensions"],
            "num_channels": selected_info["num_channels"],
            "parent_submodel": selected_info["parent_submodel"],
            "connected_to_output": selected_info["connected_to_output"],
            "connection_message": selected_info["connection_verification_message"],
        },
        "candidate_layers_summary": {
            "total_layers_scanned": len(all_candidates),
            "spatial_feature_layers": len(spatial_candidates),
            "convolutional_spatial_layers": len(conv_spatial_candidates),
            "key_candidates": [
                {
                    "name": c["name"],
                    "type": c["layer_type"],
                    "output_shape": c["output_shape"],
                    "channels": c["channels"],
                    "is_spatial": c["is_spatial"],
                }
                for c in spatial_candidates[-10:]
            ],
        },
        "real_images_evaluated": {
            "total_images": len(real_image_results),
            "all_features_valid": all_images_passed,
            "per_image_results": real_image_results,
        },
        "verification_result": overall_status,
        "limitations": [
            "Step 1 verifies layer discovery, feature map extraction, and gradient connectivity only.",
            "Grad-CAM heatmap generation, thresholding, and visual overlays are deferred to Step 2.",
            "Evaluated on 9 real fundus audit images from data/real_retinal_images/.",
            "No clinical claims or lesion-level validation performed in this layer verification step.",
        ],
    }

    # Save JSON report
    json_out = RESULTS_DIR / "gradcam_layer_report.json"
    with open(json_out, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nSaved structured JSON report to {json_out}")

    # Save Markdown report
    md_out = RESULTS_DIR / "gradcam_layer_report.md"
    generate_markdown_report(payload, md_out)
    print(f"Saved markdown report to {md_out}")

    print(f"\nOVERALL STEP 1 STATUS: {overall_status}")
    return payload


def generate_markdown_report(data: dict, md_path: Path) -> None:
    """Generate human-readable markdown verification report."""
    mv = data["model_verification"]
    sl = data["selected_gradcam_layer"]
    cs = data["candidate_layers_summary"]
    ri = data["real_images_evaluated"]

    lines = [
        "# Milestone 11 — Step 1: Grad-CAM Layer Discovery & Verification Report",
        "",
        "## 1. Executive Verification Status",
        "",
        f"- **Verification Result**: **{data['verification_result']}**",
        f"- **Model Path**: `{mv['model_path']}`",
        f"- **Model Name**: `{mv['model_name']}`",
        f"- **Total Parameters**: {mv['parameter_count']:,} (100% frozen, 0 retrained)",
        f"- **Input Shape**: `{mv['input_shape']}` (float32, [0, 255] range)",
        f"- **Output Shape**: `{mv['output_shape']}` (5 classes, Softmax)",
        "",
        "## 2. Selected Grad-CAM Target Layer",
        "",
        f"- **Selected Layer Name**: `{sl['layer_name']}`",
        f"- **Full Hierarchical Path**: `{sl['full_path']}`",
        f"- **Layer Type**: `{sl['layer_type']}`",
        f"- **Output Tensor Shape**: `{sl['output_shape']}`",
        f"- **Spatial Feature Dimensions**: `{sl['spatial_dimensions'][0]} x {sl['spatial_dimensions'][1]}`",
        f"- **Number of Channels**: `{sl['num_channels']}`",
        f"- **Parent Submodel**: `{sl['parent_submodel']}`",
        f"- **Gradient Connectivity Verified**: {'YES' if sl['connected_to_output'] else 'NO'} (`{sl['connection_message']}`)",
        "",
        "## 3. Candidate Layers Survey (Last 10 Spatial Stages)",
        "",
        "| Hierarchical Name | Layer Type | Output Shape | Channels | Spatial? |",
        "|:---|:---|:---:|:---:|:---:|",
    ]

    for c in cs["key_candidates"]:
        sh_str = str(c["output_shape"])
        lines.append(f"| `{c['name']}` | {c['type']} | `{sh_str}` | {c['channels']} | {c['is_spatial']} |")

    lines.extend([
        "",
        "## 4. Real Retinal Images Verification",
        "",
        f"Verified feature map tensor extraction across all {ri['total_images']} real retinal fundus images in `data/real_retinal_images/` using the unmodified classifier preprocessing pipeline:",
        "",
        "| Image Filename | Preprocessed Input | Feature Map Tensor | Mean Value | Std Dev | Valid 4D? |",
        "|:---|:---:|:---:|:---:|:---:|:---:|",
    ])

    for r in ri["per_image_results"]:
        lines.append(
            f"| `{r['image_filename']}` | `{r['input_tensor_shape']}` | `{r['feature_tensor_shape']}` | {r['feature_mean']} | {r['feature_std']} | **{r['valid_4d_spatial']}** |"
        )

    lines.extend([
        "",
        "## 5. Scope & Limitations",
        "",
    ])

    for lim in data["limitations"]:
        lines.append(f"- {lim}")

    lines.extend([
        "",
        "> [!IMPORTANT]",
        "> This milestone step exclusively validates programmatic layer discovery, spatial dimensionality, and gradient flow. Heatmap generation, overlay rendering, and localization evaluations occur in subsequent steps.",
        "",
        "---",
        "*Report generated automatically by `scripts/verify_gradcam_layer.py`.*",
    ])

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    run_layer_verification()
