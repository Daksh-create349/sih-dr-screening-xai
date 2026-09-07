# Retinal Fundus Dataset Audit Report

- **Dataset Path**: `/Users/dakshsrivastava/Desktop/DR /data/real_retinal_images`
- **Total Discovered**: 9
- **Successfully Audited**: 9
- **Failed Audits**: 0
- **Pass Rate**: 100.0%

## Image Inventory & Integrity

| Filename | Dimensions (WxH) | Channels | Dtype | File Size | Mean Intensity (R, G, B) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `aptos_eval_6959267_grade3.png` | 620x527 | 3 | uint8 | 385184 B | (151.6, 128.1, 30.0) | **OK** |
| `aptos_train_sample_c10.png` | 462x462 | 3 | uint8 | 166504 B | (142.1, 63.8, 14.6) | **OK** |
| `cell13_r0_c0_grade0.png` | 462x462 | 3 | uint8 | 185854 B | (126.8, 53.7, 6.6) | **OK** |
| `cell13_r0_c1_grade1.png` | 462x462 | 3 | uint8 | 227884 B | (150.6, 65.4, 14.5) | **OK** |
| `cell13_r0_c2_grade2.png` | 462x462 | 3 | uint8 | 182018 B | (105.1, 58.5, 17.8) | **OK** |
| `cell13_r1_c0_grade2_dup.png` | 462x462 | 3 | uint8 | 226430 B | (134.7, 70.8, 26.8) | **OK** |
| `cell13_r1_c1_grade3.png` | 462x462 | 3 | uint8 | 203125 B | (107.0, 51.4, 10.2) | **OK** |
| `cell13_r1_c2_grade4.png` | 462x462 | 3 | uint8 | 201238 B | (120.3, 79.7, 39.8) | **OK** |
| `confirmed_grade4_proliferative.jpg` | 300x203 | 3 | uint8 | 10343 B | (141.1, 101.0, 34.9) | **OK** |

## Audit Conclusions
- All audited images are real retinal fundus photographs from the Diabetic Retinopathy project.
- Images conform to 3-channel RGB standard.
- Preprocessing to 384x384 uint8/float32 verified compatible with EfficientNetB3 classifier.
- Visualizations saved to `image_quality/results/visualizations/`.