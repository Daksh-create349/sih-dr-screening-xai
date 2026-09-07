# Milestone 11 — Step 1: Grad-CAM Layer Discovery & Verification Report

## 1. Executive Verification Status

- **Verification Result**: **PASS**
- **Model Path**: `/Users/dakshsrivastava/Desktop/DR /model/MODEL_V2_80pct_backup.keras`
- **Model Name**: `APTOS_DR_EfficientNetB3_V2`
- **Total Parameters**: 11,184,436 (100% frozen, 0 retrained)
- **Input Shape**: `[None, 384, 384, 3]` (float32, [0, 255] range)
- **Output Shape**: `[None, 5]` (5 classes, Softmax)

## 2. Selected Grad-CAM Target Layer

- **Selected Layer Name**: `top_conv`
- **Full Hierarchical Path**: `efficientnetb3.top_conv`
- **Layer Type**: `Conv2D`
- **Output Tensor Shape**: `[None, 12, 12, 1536]`
- **Spatial Feature Dimensions**: `12 x 12`
- **Number of Channels**: `1536`
- **Parent Submodel**: `efficientnetb3`
- **Gradient Connectivity Verified**: YES (`Connected: gradients computed successfully (max absolute grad: 7.829666e-04).`)

## 3. Candidate Layers Survey (Last 10 Spatial Stages)

| Hierarchical Name | Layer Type | Output Shape | Channels | Spatial? |
|:---|:---|:---:|:---:|:---:|
| `efficientnetb3.block7b_activation` | Activation | `[None, 12, 12, 2304]` | 2304 | True |
| `efficientnetb3.block7b_se_excite` | Multiply | `[None, 12, 12, 2304]` | 2304 | True |
| `efficientnetb3.block7b_project_conv` | Conv2D | `[None, 12, 12, 384]` | 384 | True |
| `efficientnetb3.block7b_project_bn` | BatchNormalization | `[None, 12, 12, 384]` | 384 | True |
| `efficientnetb3.block7b_drop` | Dropout | `[None, 12, 12, 384]` | 384 | True |
| `efficientnetb3.block7b_add` | Add | `[None, 12, 12, 384]` | 384 | True |
| `efficientnetb3.top_conv` | Conv2D | `[None, 12, 12, 1536]` | 1536 | True |
| `efficientnetb3.top_bn` | BatchNormalization | `[None, 12, 12, 1536]` | 1536 | True |
| `efficientnetb3.top_activation` | Activation | `[None, 12, 12, 1536]` | 1536 | True |
| `efficientnetb3` | Functional | `[None, 12, 12, 1536]` | 1536 | True |

## 4. Real Retinal Images Verification

Verified feature map tensor extraction across all 9 real retinal fundus images in `data/real_retinal_images/` using the unmodified classifier preprocessing pipeline:

| Image Filename | Preprocessed Input | Feature Map Tensor | Mean Value | Std Dev | Valid 4D? |
|:---|:---:|:---:|:---:|:---:|:---:|
| `aptos_eval_6959267_grade3.png` | `[1, 384, 384, 3]` | `[1, 12, 12, 1536]` | -0.74631 | 3.64342 | **True** |
| `aptos_train_sample_c10.png` | `[1, 384, 384, 3]` | `[1, 12, 12, 1536]` | -1.07997 | 3.72404 | **True** |
| `cell13_r0_c0_grade0.png` | `[1, 384, 384, 3]` | `[1, 12, 12, 1536]` | -0.68527 | 3.27775 | **True** |
| `cell13_r0_c1_grade1.png` | `[1, 384, 384, 3]` | `[1, 12, 12, 1536]` | -0.86715 | 3.57855 | **True** |
| `cell13_r0_c2_grade2.png` | `[1, 384, 384, 3]` | `[1, 12, 12, 1536]` | -0.81512 | 3.46534 | **True** |
| `cell13_r1_c0_grade2_dup.png` | `[1, 384, 384, 3]` | `[1, 12, 12, 1536]` | -0.7857 | 3.67273 | **True** |
| `cell13_r1_c1_grade3.png` | `[1, 384, 384, 3]` | `[1, 12, 12, 1536]` | -0.61053 | 3.41666 | **True** |
| `cell13_r1_c2_grade4.png` | `[1, 384, 384, 3]` | `[1, 12, 12, 1536]` | -1.01439 | 4.38135 | **True** |
| `confirmed_grade4_proliferative.jpg` | `[1, 384, 384, 3]` | `[1, 12, 12, 1536]` | -1.1377 | 3.39868 | **True** |

## 5. Scope & Limitations

- Step 1 verifies layer discovery, feature map extraction, and gradient connectivity only.
- Grad-CAM heatmap generation, thresholding, and visual overlays are deferred to Step 2.
- Evaluated on 9 real fundus audit images from data/real_retinal_images/.
- No clinical claims or lesion-level validation performed in this layer verification step.

> [!IMPORTANT]
> This milestone step exclusively validates programmatic layer discovery, spatial dimensionality, and gradient flow. Heatmap generation, overlay rendering, and localization evaluations occur in subsequent steps.

---
*Report generated automatically by `scripts/verify_gradcam_layer.py`.*
