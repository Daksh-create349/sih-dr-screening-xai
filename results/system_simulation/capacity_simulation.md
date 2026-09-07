# System-Level Throughput, Capacity & Scalability Simulation Report

**Milestone**: Milestone 13 - Step 2: Python System-Level Capacity Simulation  
**Classification**: Simulink-Equivalent Engineering Capacity Analysis  
**Target Workload**: 100,000 patients/year (TARGET)  
**Weighted Service Time**: 2.3973 s / patient (2397.292 ms)  
**Single-Worker Status**: CAPACITY_AVAILABLE (Utilization = 3.33%)  

---

## 1. Operational Workload Parameters & Conversion

| Parameter | Value | Classification | Formula / Source |
|---|---|---|---|
| Annual Patients | 100,000 | TARGET | Project clinical requirement |
| Clinic Days / Year | 250 days | ASSUMED | Standard outpatient calendar |
| Operating Hours / Day | 8.0 hours | ASSUMED | Standard clinic shift |
| Arrival Rate (lambda) | 0.013889 pts/s | CALCULATED | 100,000 / (250 * 8 * 3600) |
| Hourly Arrival Rate | 50.0 pts/hr | CALCULATED | 100,000 / (250 * 8) |
| Inter-Arrival Interval | 72.0 s | CALCULATED | 1 / lambda |

---

## 2. Theoretical Processing Capacity (Single Worker)

- **Service Time per Patient (Weighted)**: 2.3973 s
- **Throughput Capacity**: 0.42 patients/s (1501.7 patients/hr)
- **Daily Capacity (8h shift)**: 12,014 patients/day
- **Annual Capacity (250 days)**: 3,003,391 patients/year
- **Headroom relative to 100k**: +2903.4%
- **Status**: **CAPACITY_AVAILABLE** — System possesses ample computational headroom (rho < 0.80) to comfortably sustain target screening workload.

---

## 3. Resource Allocation Scenarios & Bottleneck Analysis

| Scenario | Workers | Reviewers | Annual Capacity | Worker Util (%) | Reviewer Util (%) | Primary Bottleneck | 100k Supported? |
|---|---|---|---|---|---|---|---|
| **Minimal (1 Worker, 1 Reviewer)** | 1 | 1 | 3,003,391 | 3.3% | 66.7% | CLINICAL_REVIEWERS | **YES** |
| **Balanced (2 Workers, 1 Reviewer)** | 2 | 1 | 6,006,783 | 1.7% | 66.7% | CLINICAL_REVIEWERS | **YES** |
| **High-Throughput (4 Workers, 2 Reviewers)** | 4 | 2 | 12,013,565 | 0.8% | 33.3% | CLINICAL_REVIEWERS | **YES** |

> **Key Insight**: Clinical specialist review is the primary operational bottleneck. Even with 1 AI worker handling 100k annual patients easily, 1 ophthalmologist reviewing referable cases (~40% prevalence = 20 cases/hr) operates at 66.7% capacity. Adding compute workers further shifts the bottleneck exclusively to the clinical workforce.

---

## 4. Shift Queue Dynamics (M/M/c Simulation)

- **Simulated Shift**: 8 hours (28,800 s, Seed=42)
- **Total Inbound Patients**: 406
- **Completed Screenings**: 406
- **Mean Queue Length**: 0.0 patients (P95: 0.0 patients, Max: 0 patients)
- **Mean Wait Time**: 0.02 s (0.00 min)
- **P95 Wait Time**: 0.0 s (0.00 min)
- **Max Wait Time**: 1.83 s (0.03 min)

---

## 5. Network Bandwidth & Storage Infrastructure

- **Mean Bandwidth Required**: 0.0221 Mbps (22,081 bps)
- **Peak Image Bandwidth**: 0.0428 Mbps (42,799 bps)
- **Daily Ingestion Volume**: 75.8 MB (0.074 GB)
- **Annual Storage Requirement**: 18.5 GB (0.018 TB)
- **Conclusion**: Bandwidth is negligible (<0.1 Mbps continuous), allowing remote clinic screening over standard broadband.

---

## 6. Engineering Limitations & Clinical Disclaimers

1. **Simulation vs Real World**: This is a mathematical engineering capacity simulation. Real clinics experience bursty walk-ins rather than smooth Poisson arrivals.
2. **Hardware Environment**: Profiling executed on host Apple Silicon CPU. Dedicated cloud GPU or server nodes will yield different service distributions.
3. **Clinical Review Assumption**: 30 cases/hour per clinician is a planning assumption requiring site-specific clinical validation.
4. **No Clinical Benchmark**: The 9 retinal images provided runtime data only; no clinical sensitivity/specificity claims are made from this simulation.
