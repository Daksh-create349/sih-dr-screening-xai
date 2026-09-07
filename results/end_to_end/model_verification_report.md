# Model Loading & Checkpoint Verification Report

## Verification Details
- **Timestamp**: 2026-09-06
- **Model Checkpoint Path**: `model/MODEL_V2_80pct_backup.keras`
- **Target Real Path**: `/Users/dakshsrivastava/Desktop/Diabetic-Retinopathy-Trained/MODEL_V2_80pct_backup.keras`
- **File Exists**: True
- **File Size**: 224,119,603 bytes (213.74 MB)
- **Model Loading Status**: SUCCESS (`keras.models.load_model('model/MODEL_V2_80pct_backup.keras', compile=False)`)

## Architectural Specifications
- **Model Name**: `APTOS_DR_EfficientNetB3_V2`
- **Input Layer Shape**: `(None, 384, 384, 3)`
- **Output Layer Shape**: `(None, 5)`
- **Output Layer Name**: `dense_3`
- **Output Activation**: `softmax`
- **Total Parameters**: 11,184,436 (all preserved, 0 retrained, 0 modified)
- **Number of Functional / Sequential Layers**: 9 top-level stages:
  1. `input_layer_4` (InputLayer, shape (None, 384, 384, 3))
  2. `sequential` (Data augmentation: RandomFlip, RandomRotation, RandomZoom, RandomContrast; inactive during inference)
  3. `efficientnetb3` (Backbone with internal `rescaling_2`, `normalization_1`, `rescaling_3`)
  4. `global_average_pooling2d_1` (GAP)
  5. `batch_normalization_1` (BatchNormalization)
  6. `dropout_2` (Dropout rate 0.4)
  7. `dense_2` (Dense 256, ReLU)
  8. `dropout_3` (Dropout rate 0.3)
  9. `dense_3` (Dense 5, Softmax)

## Five Clinical Classes Verified
- **0**: No DR
- **1**: Mild DR
- **2**: Moderate DR
- **3**: Severe DR
- **4**: Proliferative DR

## Integrity Guarantees
1. No weights modified or re-initialized.
2. Model loaded with `compile=False` to preserve original frozen weights without re-compilation.
3. Native Keras 3 format compatibility verified.
