"""CLI script to run mathematical workflow and capacity simulation.

Consumes empirical runtime profile measurements from:
    results/system_simulation/runtime_profile.json

Executes:
1. Workload arrival rate calculations (100,000 patients/year TARGET).
2. Processing capacity and utilization evaluations.
3. Multi-worker resource scenarios (1W/1R, 2W/1R, 4W/2R).
4. Analytical M/M/c queueing model (Erlang-C) & discrete-event shift
   simulation.
5. Network bandwidth and storage volume analysis from real image sizes.
6. Generates 8 Matplotlib visualization plots.
7. Generates:
    results/system_simulation/capacity_simulation.json
    results/system_simulation/capacity_simulation.md
    results/system_simulation/hackathon_summary.md
"""

import argparse
from pathlib import Path
import json
import sys

# Ensure DR root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from system_simulation.workload import (  # noqa: E402
    WorkloadConfig,
    calculate_workload_rates,
)
from system_simulation.capacity import (  # noqa: E402
    CapacityConfig,
    calculate_capacity_metrics,
    evaluate_resource_scenarios,
)
from system_simulation.queue_model import (  # noqa: E402
    compute_mmc_analytics,
    simulate_shift_queue,
)
from system_simulation.reporting import (  # noqa: E402
    calculate_bandwidth_metrics,
    generate_all_visualizations,
    generate_capacity_markdown,
    generate_hackathon_summary,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run system capacity simulation consuming profiling JSON."
    )
    parser.add_argument(
        "--profile-json",
        type=Path,
        default=WORKSPACE_ROOT / "results" / "system_simulation" / "runtime_profile.json",  # noqa: E501
        help="Path to measured runtime profile JSON.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=WORKSPACE_ROOT / "results" / "system_simulation",
        help="Directory to save simulation reports and plots.",
    )
    parser.add_argument(
        "--annual-patients",
        type=int,
        default=100000,
        help="Annual screening patient target (TARGET, default: 100,000).",
    )
    return parser.parse_args()


def main() -> int:
    """Execute capacity simulation runner."""
    args = parse_args()

    print("==================================================")
    print("MILESTONE 13 - STEP 2: CAPACITY & WORKLOAD SIMULATION")
    print("==================================================")
    print(f"Profile JSON Input: {args.profile_json}")
    print(f"Output Directory: {args.output_dir}")
    print(f"Annual Patients Target: {args.annual_patients:,}")
    print("--------------------------------------------------")

    if not args.profile_json.exists():
        print(
            f"ERROR: Runtime profile JSON not found at {args.profile_json}. "
            "Please run 'python scripts/profile_pipeline.py' first.",
            file=sys.stderr,
        )
        return 1

    try:
        # 1. Load empirical measurements
        with open(args.profile_json, "r", encoding="utf-8") as f:
            profile_data = json.load(f)

        print("[OK] Loaded measured runtime profile.")

        # 2. Workload model
        workload_cfg = WorkloadConfig(annual_patients=args.annual_patients)
        workload_data = calculate_workload_rates(workload_cfg)
        lambda_rate = workload_data["patient_rates"]["patients_per_second"]
        print(f"[OK] Workload Model: lambda = {lambda_rate:.6f} pts/s ({workload_data['patient_rates']['patients_per_hour']:.1f} pts/hr)")  # noqa: E501

        # 3. Capacity evaluation
        capacity_cfg = CapacityConfig()
        capacity_data = calculate_capacity_metrics(
            profile_data=profile_data,
            workload_cfg=workload_cfg,
            capacity_cfg=capacity_cfg,
            num_workers=1,
        )
        t_svc = capacity_data["service_time"]
        mu_rate = capacity_data["single_worker_throughput"]["patients_per_second"]  # noqa: E501
        print(f"[OK] Capacity Model: Weighted service time = {t_svc['weighted_service_time_seconds']:.4f} s (mu = {mu_rate:.2f} pts/s)")  # noqa: E501
        print(f"[OK] Status: {capacity_data['target_comparison']['status']} (utilization = {capacity_data['target_comparison']['utilization_pct']}%)")  # noqa: E501

        # 4. Resource scenarios
        scenario_data = evaluate_resource_scenarios(
            profile_data=profile_data,
            workload_cfg=workload_cfg,
            capacity_cfg=capacity_cfg,
        )
        print(f"[OK] Evaluated {len(scenario_data['scenarios'])} resource scenarios.")  # noqa: E501

        # 5. Queue model (Analytical + Discrete Event)
        mmc_analytics = compute_mmc_analytics(
            arrival_rate=lambda_rate,
            service_rate_per_worker=mu_rate,
            num_workers=1,
        )
        queue_sim = simulate_shift_queue(
            arrival_rate_per_sec=lambda_rate,
            service_time_sec_mean=t_svc["weighted_service_time_seconds"],
            service_time_sec_std=0.05,
            num_workers=1,
            shift_hours=8.0,
            seed=42,
        )
        queue_data = {
            "analytical_mmc": mmc_analytics,
            **queue_sim,
        }
        print(f"[OK] Queue Simulation: Mean queue = {queue_sim['queue_length']['mean']} pts, Mean wait = {queue_sim['waiting_time_seconds']['mean_s']} s")  # noqa: E501

        # 6. Bandwidth calculations
        bandwidth_data = calculate_bandwidth_metrics(
            image_size_metrics=profile_data["image_sizes"],
            workload_data=workload_data,
        )
        bw_mbps = bandwidth_data["network_throughput"]["mean_bandwidth_mbps"]
        vol_gb = bandwidth_data["data_volumes"]["annual_volume_gb"]
        print(f"[OK] Bandwidth Analysis: {bw_mbps:.4f} Mbps required, {vol_gb:.1f} GB/year storage")  # noqa: E501

        # 7. Generate visualizations
        args.output_dir.mkdir(parents=True, exist_ok=True)
        print("Generating Matplotlib visualization plots...")
        plots = generate_all_visualizations(
            profile_data=profile_data,
            capacity_data=capacity_data,
            scenario_data=scenario_data,
            queue_data=queue_data,
            bandwidth_data=bandwidth_data,
            output_dir=args.output_dir,
        )
        for p in plots:
            print(f"  [OK] Saved plot: {p.name}")

        # 8. Assemble combined simulation payload
        sim_payload = {
            "milestone": "Milestone 13 - Step 2: Capacity Simulation",
            "terminology_declaration": {
                "simulator_type": "Python system-level workflow/capacity simulation",  # noqa: E501
                "equivalence": "Simulink-equivalent system-level capacity analysis",  # noqa: E501
                "simulink_status": "MATLAB/Simulink unavailable on workstation; transparent Python model used.",  # noqa: E501
            },
            "workload": workload_data,
            "single_worker_capacity": capacity_data,
            "scenarios": scenario_data,
            "queue_analysis": queue_data,
            "bandwidth_and_storage": bandwidth_data,
        }

        # 9. Save JSON & Markdown
        sim_json_path = args.output_dir / "capacity_simulation.json"
        sim_md_path = args.output_dir / "capacity_simulation.md"
        summary_md_path = args.output_dir / "hackathon_summary.md"

        with open(sim_json_path, "w", encoding="utf-8") as f:
            json.dump(sim_payload, f, indent=2)
        print(f"[OK] Saved simulation JSON: {sim_json_path}")

        sim_md = generate_capacity_markdown(
            workload_data=workload_data,
            capacity_data=capacity_data,
            scenario_data=scenario_data,
            queue_data=queue_data,
            bandwidth_data=bandwidth_data,
        )
        with open(sim_md_path, "w", encoding="utf-8") as f:
            f.write(sim_md)
        print(f"[OK] Saved simulation Markdown: {sim_md_path}")

        summary_md = generate_hackathon_summary(
            profile_data=profile_data,
            capacity_data=capacity_data,
            scenario_data=scenario_data,
        )
        with open(summary_md_path, "w", encoding="utf-8") as f:
            f.write(summary_md)
        print(f"[OK] Saved hackathon summary: {summary_md_path}")

        print("==================================================")
        print(f"100K TARGET ANALYSIS: {capacity_data['target_comparison']['status']}")  # noqa: E501
        print("SIMULATION STATUS: SUCCESS")
        print("==================================================")
        return 0

    except Exception as exc:
        print(f"ERROR during capacity simulation: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
