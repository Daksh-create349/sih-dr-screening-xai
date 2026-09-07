"""CLI script to profile real retinal pipeline components and execution paths.

Executes actual wall-clock timing on the 9 real retinal images:
- Measures cold model load time and warm inference.
- Measures individual component execution times (A to J).
- Measures end-to-end execution across Path A, Path B, and Path C.
- Records actual file sizes of real retinal images.
- Writes:
    results/system_simulation/runtime_profile.json
    results/system_simulation/runtime_profile.md
"""

import argparse
from pathlib import Path
import json
import sys

# Ensure DR root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from system_simulation.profiling import run_pipeline_profiling  # noqa: E402
from system_simulation.reporting import generate_runtime_markdown  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Profile DR screening pipeline execution on real images."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=WORKSPACE_ROOT / "data" / "real_retinal_images",
        help="Path to directory containing real retinal fundus images.",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="Number of profiling repetitions per image (default: 3).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=WORKSPACE_ROOT / "results" / "system_simulation",
        help="Directory to save JSON and Markdown profile results.",
    )
    return parser.parse_args()


def main() -> int:
    """Execute profiling runner."""
    args = parse_args()

    print("==================================================")
    print("MILESTONE 13 - STEP 2: PIPELINE RUNTIME PROFILING")
    print("==================================================")
    print(f"Data Directory: {args.data_dir}")
    print(f"Repetitions per image: {args.repetitions}")
    print(f"Output Directory: {args.output_dir}")
    print("--------------------------------------------------")

    if not args.data_dir.exists():
        print(f"ERROR: Data directory not found: {args.data_dir}", file=sys.stderr)  # noqa: E501
        return 1

    try:
        # Run profiling
        print("Executing runtime profiling on real retinal images...")
        profile_data = run_pipeline_profiling(
            data_dir=args.data_dir,
            repetitions=args.repetitions,
        )

        args.output_dir.mkdir(parents=True, exist_ok=True)
        json_path = args.output_dir / "runtime_profile.json"
        md_path = args.output_dir / "runtime_profile.md"

        # Save JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2)
        print(f"[OK] Saved runtime profile JSON: {json_path}")

        # Save Markdown
        md_content = generate_runtime_markdown(profile_data)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"[OK] Saved runtime profile Markdown: {md_path}")

        # Summary output
        print("--------------------------------------------------")
        print(f"Images Profiled: {profile_data['image_count']} / 9")
        print(f"Cold Model Load: {profile_data['cold_model_load']['cold_load_seconds']} s")  # noqa: E501
        dist = profile_data["path_distribution"]
        print(f"Observed Paths: GOOD={dist.get('GOOD', 0)}, BORDERLINE={dist.get('BORDERLINE', 0)}, UNGRADEABLE={dist.get('UNGRADEABLE', 0)}")  # noqa: E501
        comps = profile_data["components"]
        print(f"Mean Classifier Warm Inference: {comps['classifier_inference']['mean_ms']} ms")  # noqa: E501
        print(f"Mean Grad-CAM Computation: {comps['gradcam_computation']['mean_ms']} ms")  # noqa: E501
        print(f"Mean E2E Pipeline Latency: {comps['pipeline_end_to_end']['mean_ms']} ms")  # noqa: E501
        print("==================================================")
        print("PROFILING STATUS: SUCCESS")
        print("==================================================")
        return 0

    except Exception as exc:
        print(f"ERROR during pipeline profiling: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
