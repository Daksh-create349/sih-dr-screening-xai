"""CLI script to execute the Integrated Pipeline vs Classifier-Only Benchmark.

Generates:
1. validation/results/integrated_benchmark_results.json
2. validation/results/raw_predictions.csv
3. validation/results/integrated_pipeline_benchmark_report.md
"""

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from validation.integrated_benchmark import run_comprehensive_benchmark
from validation.benchmark_report import generate_benchmark_markdown_report


def main() -> int:
    output_dir = WORKSPACE_ROOT / "validation" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("============================================================")
    print("RUNNING INTEGRATED PIPELINE vs CLASSIFIER-ONLY BENCHMARK")
    print("============================================================")
    print(f"Output directory: {output_dir}")

    payload = run_comprehensive_benchmark(output_dir=output_dir)

    report_path = output_dir / "integrated_pipeline_benchmark_report.md"
    generate_benchmark_markdown_report(payload, output_path=report_path)

    mode_a = payload["baseline_1_classifier_only"]
    mode_b = payload["baseline_2_integrated_pipeline"]
    conclusion = payload["engineering_conclusion"]

    print("\n--- RESULTS SUMMARY ---")
    print(f"Images Evaluated: {mode_a['num_evaluated']}")
    print(f"Mode A (Classifier-Only) 5-Class Accuracy: {mode_a['metrics_5class']['accuracy'] * 100:.2f}%")
    print(f"Mode B (Integrated) 5-Class Accuracy:      {mode_b['metrics_5class']['accuracy'] * 100:.2f}%")
    print(f"Mode A (Classifier-Only) Referable Acc:    {mode_a['metrics_referable']['binary_accuracy'] * 100:.2f}%")
    print(f"Mode B (Integrated) Referable Acc:         {mode_b['metrics_referable']['binary_accuracy'] * 100:.2f}%")
    print(f"Enhancement Events Evaluated:              {len(payload['enhancement_effect_analysis'])}")
    print(f"Engineering Conclusion:                    {conclusion['outperforms']}")
    print(f"Reports saved to {output_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
