# Model & Preprocessing Protocol Verification Report

**Protocol Status**: `PASS`

---

## 1. Model Architecture Verification

- **Architecture**: `APTOS_DR_EfficientNetB3_V2`
- **Input Shape**: `[None, 384, 384, 3]`
- **Output Shape**: `[None, 5]`
- **Classes**: `5`
- **Parameters**: `11,184,436`
- **Architecture Check**: `PASS`

## 2. Preprocessing Protocol Verification

- **Target Resolution**: `[384, 384]`
- **Processed Shape**: `[1, 384, 384, 3]`
- **Tensor Dtype**: `float32`
- **Value Range**: `[0.0, 251.0]`
- **Bounding Box**: `get_retinal_crop_box` (grayscale > 10)
- **Interpolation**: OpenCV `cv2.INTER_AREA` (matches training)
- **Preprocessing Check Status**: `PASS`

---

## 3. Compliance Summary

Zero code divergence confirmed. Existing classifier modules strictly
adhere to the frozen specification.
