# Integrated Screening Pipeline vs Classifier-Only Benchmark Report

**Execution Timestamp**: `2026-09-07T13:51:14.877459+00:00`  
**Protocol Version**: `1.0.0`  
**Model Checkpoint**: `/Users/dakshsrivastava/Desktop/DR /model/MODEL_V2_80pct_backup.keras` (FROZEN)  
**Production Referable Threshold**: `0.33`  

---

## 1. Objective
To establish a rigorous, scientifically honest, and reproducible quantitative comparison between the **Single-Technique Classifier-Only Baseline** (Mode A) and the **Integrated Clinical Screening Pipeline** (Mode B: Upstream IQA -> Quality Gate -> Automated CLAHE Enhancement -> Deep Classifier -> Referable Triage), isolating whether the integrated quality pipeline provides measurable improvements while preserving strict data honesty.

## 2. Evaluation Protocol
Evaluation strictly adheres to the frozen protocol specifications:
- **Model State**: Completely frozen (`model/MODEL_V2_80pct_backup.keras`). Zero fine-tuning, zero weight edits.
- **Mode A (Classifier-Only)**: Real image -> Retinal border crop -> Resize (384x384, INTER_AREA) -> EfficientNetB3 -> Softmax -> Sum P(Grade 2..4) >= 0.33.
- **Mode B (Integrated Pipeline)**: Real image -> Focus/Illumination/FOV/Centering IQA -> Quality Gate (GOOD: Direct classifier; BORDERLINE: CLAHE enhancement -> recheck -> classifier; UNGRADEABLE: Strictly rejected, zero fabricated prediction).
- **Fairness Rule**: No comparing classifier-only on one set vs integrated pipeline on a different set. Identical labelled cohorts evaluated across both pathways.
- **Data Honesty**: Zero synthetic or mock clinical data. Every metric derived from actual pipeline execution.

## 3. Model Architecture & Parameters
- **Model Identifier**: `APTOS_DR_EfficientNetB3`
- **Input Dimensions**: `[None, 384, 384, 3]`
- **Preprocessing Routine**: `APTOS_Crop_INTER_AREA_384x384_v1`
- **Class Count**: 5 classes (`0: No DR`, `1: Mild DR`, `2: Moderate DR`, `3: Severe DR`, `4: Proliferative DR`)
- **Internal Activation**: Softmax output on dense classification head
- **Referable Definition**: Positive = Grades 2, 3, 4; Negative = Grades 0, 1
- **Screening Operating Threshold**: `0.33` on sum P(Grade 2..4)

## 4. Baseline Definitions
| Baseline ID | Name | Pipeline Description | IQA Gating | Enhancement |
| :--- | :--- | :--- | :---: | :---: |
| **Mode A** | Classifier-Only | Raw Image -> Crop/Resize 384x384 -> EfficientNetB3 -> Referable Triage | No | No |
| **Mode B** | Integrated Pipeline | Raw Image -> IQA -> Gate -> (GOOD/BORDERLINE-CLAHE) -> Classifier -> Referable | Yes | Yes (CLAHE) |

## 5. Dataset Details
- **Evaluated Local Cohort**: `Local Real Retinal Fundus Integration Set` (9 images)
- **Evaluation Category**: `engineering_integration_verification`
- **Clinical Validity**: `False` (9 images serve strictly for end-to-end integration and determinism verification; not an independent clinical trial cohort.)
- **Historical Held-Out Test Set**: 366 genuine APTOS images evaluated in Colab during model development
- **Full Third-Party Release**: Train = 2930, Validation = 366, Test = 366 (total = 3662)

## 6. Dataset Split Contamination Audit Warning
> [!WARNING]
> **CRITICAL AUDIT FINDING**: Dataset contamination detected across released splits. Metrics from this split should not be interpreted as a clean independent clinical benchmark.
> 
> A cryptographic SHA-256 hash audit of the released third-party APTOS split revealed **46 duplicate image hash groups** crossing partition boundaries:
> - **40 same-label cross-split duplicate groups** (test-train data leakage)
> - **6 conflicting-label cross-split duplicate groups** (ground-truth diagnostic label discordance)
> 
> **Scientific Consequence**: Any re-evaluation on the released Kaggle splits is contaminated by partition leakage. Accordingly, the historical held-out test performance is preserved as the genuine reference, and neither split is represented as a clean external clinical trial.

## 7. Upstream IQA Routing & Quality Gate Analysis
- **Total Evaluated**: 9
- **GOOD Quality**: 4 (44.4%) -> routed directly to classifier
- **BORDERLINE Quality**: 5 (55.6%) -> routed to CLAHE enhancement
- **UNGRADEABLE Quality**: 0 (0.0%) -> strictly rejected, zero inference
- **Actually Classified**: 9 (100.0% coverage)
- **Rejected Count**: 0 (0.0%)


## 8. Mode A: Classifier-Only Results
- **5-Class Accuracy**: 33.33%
- **Macro Precision**: 40.00%
- **Macro Recall**: 30.00%
- **Macro F1**: 33.33%
- **Referable Binary Accuracy**: 55.56%
- **Referable Sensitivity**: 50.00%
- **Referable Specificity**: 66.67%
- **Referable Precision (PPV)**: 75.00%
- **Referable NPV**: 40.00%
- **Confusion Matrix 2x2**: `TN: 2, FP: 1, FN: 3, TP: 3`


## 9. Mode B: Integrated Screening Pipeline Results
- **5-Class Accuracy**: 33.33%
- **Macro Precision**: 40.00%
- **Macro Recall**: 30.00%
- **Macro F1**: 33.33%
- **Referable Binary Accuracy**: 44.44%
- **Referable Sensitivity**: 50.00%
- **Referable Specificity**: 33.33%
- **Referable Precision (PPV)**: 60.00%
- **Referable NPV**: 25.00%
- **Confusion Matrix 2x2**: `TN: 1, FP: 2, FN: 3, TP: 3`


## 10. Enhancement Effect Analysis (Borderline Acquisitions)
Direct comparison for images where automated CLAHE enhancement was accepted:

| Image Filename | True Grade | Orig Pred | Enh Pred | Orig P(Ref) | Enh P(Ref) | ΔP(Ref) | Decision Shift | ΔComposite Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `aptos_train_sample_c10.png` | Grade 0 | Grade 2 | Grade 2 | 0.591 | 0.665 | +0.075 | No | +5.8 |
| `cell13_r0_c0_grade0.png` | Grade 0 | Grade 1 | Grade 1 | 0.323 | 0.510 | +0.188 | **YES** | +8.6 |
| `cell13_r0_c1_grade1.png` | Grade 1 | Grade 0 | Grade 0 | 0.000 | 0.000 | -0.000 | No | +7.2 |
| `cell13_r0_c2_grade2.png` | Grade 2 | Grade 0 | Grade 0 | 0.000 | 0.000 | +0.000 | No | +9.6 |
| `cell13_r1_c1_grade3.png` | Grade 3 | Grade 3 | Grade 3 | 0.996 | 1.000 | +0.003 | No | +4.5 |

- **Empirical Observation**: CLAHE enhancement improved optical composite quality scores across all 5 borderline acquisitions (+4.5 to +9.6 points). However, enhancement did not alter predicted 5-class DR grades on these samples. For `cell13_r0_c0_grade0.png`, contrast stretching raised P(Grade 2..4) from 0.323 to 0.510, crossing the 0.33 threshold into a false referable referral. This quantitatively confirms the project advisory: *'Enhancement improves image presentation but does not restore uncaptured clinical information.'*

## 11. Referable DR Screening Triage Comparison
| Metric | Mode A (Classifier-Only) | Mode B (Integrated Pipeline) | Delta (B - A) | Historical Held-Out Reference |
| :--- | :---: | :---: | :---: | :---: |
| **Threshold** | 0.33 | 0.33 | 0.00 | 0.5 (Default) / 0.1181 (Val-Tuned) |
| **Binary Accuracy** | 55.56% | 44.44% | -11.12% | 93.44% |
| **Sensitivity** | 50.00% | 50.00% | +0.00% | 89.78% (99.27% @ 0.1181) |
| **Specificity** | 66.67% | 33.33% | -33.34% | 95.63% (88.21% @ 0.1181) |
| **Precision (PPV)** | 75.00% | 60.00% | -15.00% | 92.48% (83.44% @ 0.1181) |
| **NPV** | 40.00% | 25.00% | -15.00% | N/A |

## 12. 5-Class Multiclass Performance Comparison
| Metric | Mode A (Classifier-Only) | Mode B (Integrated Pipeline) | Delta (B - A) | Historical Held-Out Reference |
| :--- | :---: | :---: | :---: | :---: |
| **Overall Accuracy** | 33.33% | 33.33% | +0.00% | 81.15% |
| **Macro Precision** | 40.00% | 40.00% | +0.00% | Recomputed 78.4% |
| **Macro Recall** | 30.00% | 30.00% | +0.00% | Recomputed 67.2% |
| **Macro F1** | 33.33% | 33.33% | +0.00% | Recomputed 70.3% |
| **Weighted F1** | 37.04% | 37.04% | +0.00% | Recomputed 80.9% |

## 13. Rejected & Screening Coverage Analysis
- **Classifier-Only Coverage**: 100.0% (all acquisitions forced through inference regardless of optical quality)
- **Integrated Pipeline Coverage**: 100.0% classified, 0.0% rejected
- **Quality Gatekeeper Safety Invariant**: Images failing basic focus, illumination, or FOV gates are stopped with actionable recapture instructions, protecting patients against ungrounded automated classifications.

## 14. Scientific Limitations
1. **Integration Subset Scale**: The 9 locally available real retinal images provide end-to-end integration and determinism verification, not statistical power for generalizable clinical conclusions.
2. **Dataset Contamination**: The third-party APTOS release suffers from 46 duplicate hash groups across splits, preventing uncontaminated re-benchmarking.
3. **Absence of Clean Prospective Benchmark**: Canonical prospective cohorts (e.g. Messidor-2, EyePACS external) require dedicated hospital institutional ethics or exceed local download limits.
4. **Image Resolution**: Low-resolution thumbnail crops (cell13 series) capture restricted receptive fields compared to 50-degree diagnostic fundus cameras.

## 15. Interpretation & Engineering Conclusion
> **Question**: *Does the available real-data evidence demonstrate that the integrated pipeline outperforms the classifier-only baseline?*
> 
> **Answer**: **INCONCLUSIVE**
> 
> **Rationale**: Comparison is limited by dataset contamination on the public APTOS release (46 cross-split duplicate hash groups) and small size of the local real-image integration set (9 images). On the 9 integration samples, 5-class accuracy was identical (33.33%), while referable accuracy shifted from 44.44% to 33.33% due to border-image CLAHE contrast boosting. Clinical superiority cannot be claimed without a certified, uncontaminated prospective external benchmark.

## 16. Exact Reproducibility Commands
```bash
# 1. Run integrated comparative benchmark runner
python scripts/run_integrated_benchmark.py

# 2. Run automated validation test suite
pytest -q validation/tests/test_integrated_benchmark.py

# 3. Run full project backend regression suite
pytest -q
```
