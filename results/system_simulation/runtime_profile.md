# Real Retinal Pipeline Runtime Profiling Report

**Milestone**: Milestone 13 - Step 2: System Runtime Profiling  
**Status**: MEASURED (Empirical execution on real fundus images)  
**Images Profiled**: 9 real retinal images  
**Repetitions**: 3 per image  
**Total Executions**: 27 per component  

---

## 1. Host Execution Environment

- **Python Version**: 3.13.5 (`/opt/anaconda3/bin/python`)
- **Platform**: macOS-26.6.2-arm64-arm-64bit-Mach-O
- **Processor**: arm (arm64)
- **CPU Core Count**: 10
- **Cold Model Load Time**: 0.6192 s (619.23 ms)
- **Deployment Assumption**: In production screening, the model is resident in memory (warm inference).

---

## 2. Pipeline Component Timing Breakdown (Measured)

| Component | Mean (ms) | Median (ms) | Std (ms) | Min (ms) | Max (ms) | P95 (ms) |
|---|---|---|---|---|---|---|
| **A. Image Loading** | 4.125 | 4.364 | 1.147 | 1.158 | 6.702 | 5.315 |
| **B. IQA Scoring** | 21.206 | 21.923 | 3.092 | 13.055 | 26.422 | 24.346 |
| **C. Quality Decision** | 0.008 | 0.008 | 0.001 | 0.005 | 0.01 | 0.009 |
| **D. Borderline CLAHE Enhancement** | 5.32 | 3.075 | 11.379 | 1.583 | 63.178 | 4.724 |
| **E. Classifier Inference (Warm)** | 277.44 | 279.282 | 8.639 | 236.726 | 283.856 | 283.075 |
| **F. Referable DR Screening Decision** | 0.637 | 0.651 | 0.422 | 0.006 | 1.274 | 1.268 |
| **G. Grad-CAM Heatmap Computation** | 1026.382 | 1023.894 | 8.371 | 1014.946 | 1052.725 | 1045.515 |
| **H. Anatomical Evidence Layer** | 1044.899 | 1039.107 | 26.041 | 1017.9 | 1151.922 | 1086.902 |
| **I. Report Generation** | 202.355 | 328.561 | 155.397 | 14.891 | 355.727 | 354.304 |
| **J. Complete End-to-End Pipeline** | 489.919 | 608.322 | 160.146 | 290.313 | 658.142 | 654.437 |

---

## 3. Real Pipeline Path Latencies

- **Path A (GOOD)** (4 images observed): Mean = 2369.965 ms (P95 = 2425.698 ms)
- **Path B (BORDERLINE)** (5 images observed): Mean = 2419.153 ms (P95 = 2514.906 ms)
- **Path C (UNGRADEABLE)** (0 images observed): Mean = 15.513 ms (P95 = 16.636 ms)

---

## 4. Real Retinal Image File Sizes

- **Count**: 9 images
- **Mean Size**: 0.1895 MB (198,731.1 bytes)
- **Median Size**: 0.1919 MB (201,238.0 bytes)
- **Range**: [0.0099 MB, 0.3673 MB]
