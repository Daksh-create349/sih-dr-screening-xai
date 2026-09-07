# Clinical Validation Dataset Audit Report

**Dataset Name**: APTOS 2019 Blindness Detection
**Protocol Version**: 1.0.0
**Audit Status**: `BLOCKED`
**Status Reason**: Benchmark blocked: labelled evaluation dataset not available locally.

---

## 1. Executive Summary

Benchmark blocked: labelled evaluation dataset not available locally.

> [!WARNING]
> **BENCHMARK BLOCKED**: Full labelled APTOS evaluation dataset
> (label CSVs and full image bundles) is not present locally.
> As required by strict clinical rules, 9 local integration
> test images will NOT be substituted as a pseudo-benchmark.
> Benchmark protocol is frozen, ready for execution once dataset
> archive is restored.

## 2. Discovered Splits Audit

| Split | CSV | Directory | Records | Resolved | Missing | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| *None* | *Not found* | *Not found* | 0 | 0 | 0 | `BLOCKED` |

## 3. Data Leakage Assessment

- **Cross-split leakage detected**: `False`

## 4. Historical Target Reference

- Historical Train Count: ~2,930
- Historical Validation Count: ~366
- Historical Test Count: ~366
- Historical Total: ~3,662

---

## 5. Next Steps

1. **Dataset Recovery**: Restore canonical APTOS archive.
2. **Manifest Verification**: Re-run audit script.
3. **Execute Benchmark**: Run frozen protocol on test split.
