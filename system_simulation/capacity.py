"""System processing capacity, resource scenarios, and bottleneck module.

Evaluates operational capacity based on measured pipeline execution times:
- Single-worker and multi-worker theoretical throughput.
- Path-weighted end-to-end service times (GOOD, BORDERLINE, UNGRADEABLE).
- Utilization and headroom against the 100,000 patient/year target.
- Explicit classification: UNDER_CAPACITY, NEAR_CAPACITY, CAPACITY_AVAILABLE.
- Resource scenarios (1, 2, 4 processing workers; 1, 2 reviewers).
- Clinical reviewer throughput and bottleneck identification.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from system_simulation.workload import WorkloadConfig, calculate_workload_rates


@dataclass
class CapacityConfig:
    """Configurable parameters for throughput and capacity evaluation.

    Attributes:
        reviewer_cases_per_hour: Reviewer throughput capacity (ASSUMED).
        referable_prevalence: Fraction of cases requiring specialist review.
        path_distribution_weights: Custom weights for GOOD, BORDERLINE,
            and UNGRADEABLE path execution frequencies.
    """

    reviewer_cases_per_hour: float = 30.0  # ~2 mins/case review
    referable_prevalence: float = 0.40  # ~40% referral rate
    path_distribution_weights: Optional[Dict[str, float]] = None


def compute_weighted_service_time_seconds(
    profile_data: Dict[str, Any],
    custom_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Calculate path-weighted average service time in seconds.


    Args:
        profile_data: Dictionary output from run_pipeline_profiling.
        custom_weights: Optional custom dictionary of path probabilities.

    Returns:
        dict: Mean service time in seconds and path breakdown.
    """
    paths = profile_data["paths"]
    path_a_ms = paths["path_a_good"]["mean_ms"]
    path_b_ms = paths["path_b_borderline"]["mean_ms"]
    path_c_ms = paths["path_c_ungradeable"]["mean_ms"]

    # If measured paths have zero (fallback to component sum)
    if path_a_ms <= 0:
        comps = profile_data["components"]
        path_a_ms = (
            comps["image_loading"]["mean_ms"]
            + comps["iqa_scoring"]["mean_ms"]
            + comps["classifier_inference"]["mean_ms"]
            + comps["referable_decision"]["mean_ms"]
            + comps["gradcam_computation"]["mean_ms"]
            + comps["evidence_generation"]["mean_ms"]
            + comps["report_generation"]["mean_ms"]
        )

    if path_b_ms <= 0:
        comps = profile_data["components"]
        path_b_ms = (
            path_a_ms
            + comps["borderline_enhancement"]["mean_ms"]
            + comps["iqa_scoring"]["mean_ms"]
        )

    if path_c_ms <= 0:
        comps = profile_data["components"]
        path_c_ms = (
            comps["image_loading"]["mean_ms"]
            + comps["iqa_scoring"]["mean_ms"]
            + comps["quality_decision"]["mean_ms"]
        )

    # Path distribution weights
    if custom_weights is not None:
        w_a = float(custom_weights.get("GOOD", 0.70))
        w_b = float(custom_weights.get("BORDERLINE", 0.25))
        w_c = float(custom_weights.get("UNGRADEABLE", 0.05))
    else:
        # Compute empirical weights from profile data
        dist = profile_data.get("path_distribution", {})
        total_p = sum(dist.values()) if dist else 0
        if total_p > 0:
            w_a = dist.get("GOOD", 0) / total_p
            w_b = dist.get("BORDERLINE", 0) / total_p
            w_c = dist.get("UNGRADEABLE", 0) / total_p
        else:
            w_a, w_b, w_c = 0.70, 0.25, 0.05

    # Normalize weights
    sum_w = w_a + w_b + w_c
    if sum_w <= 0:
        w_a, w_b, w_c = 0.70, 0.25, 0.05
    else:
        w_a, w_b, w_c = w_a / sum_w, w_b / sum_w, w_c / sum_w

    weighted_ms = (w_a * path_a_ms) + (w_b * path_b_ms) + (w_c * path_c_ms)
    weighted_s = weighted_ms / 1000.0

    return {
        "weighted_service_time_ms": round(weighted_ms, 3),
        "weighted_service_time_seconds": round(weighted_s, 5),
        "path_breakdown_ms": {
            "path_a_good_ms": round(path_a_ms, 3),
            "path_b_borderline_ms": round(path_b_ms, 3),
            "path_c_ungradeable_ms": round(path_c_ms, 3),
        },
        "path_weights": {
            "good_weight": round(w_a, 4),
            "borderline_weight": round(w_b, 4),
            "ungradeable_weight": round(w_c, 4),
        },
    }


def calculate_capacity_metrics(
    profile_data: Dict[str, Any],
    workload_cfg: Optional[WorkloadConfig] = None,
    capacity_cfg: Optional[CapacityConfig] = None,
    num_workers: int = 1,
) -> Dict[str, Any]:
    """Calculate theoretical system processing capacity and utilization.

    Args:
        profile_data: Profiling results dictionary.
        workload_cfg: WorkloadConfig instance (default 100k target).
        capacity_cfg: CapacityConfig instance.
        num_workers: Number of concurrent processing worker processes.

    Returns:
        dict: Throughput, capacity, utilization, and status classification.
    """
    if workload_cfg is None:
        workload_cfg = WorkloadConfig()
    if capacity_cfg is None:
        capacity_cfg = CapacityConfig()

    workload = calculate_workload_rates(workload_cfg)
    target_patients_sec = workload["patient_rates"]["patients_per_second"]
    target_patients_hour = workload["patient_rates"]["patients_per_hour"]

    svc_info = compute_weighted_service_time_seconds(
        profile_data,
        custom_weights=capacity_cfg.path_distribution_weights,
    )
    t_svc_s = svc_info["weighted_service_time_seconds"]

    if t_svc_s <= 0:
        raise ValueError("Service time must be strictly positive.")

    # Single-worker capacity
    single_throughput_sec = 1.0 / t_svc_s
    single_throughput_hour = single_throughput_sec * 3600.0

    # Multi-worker capacity (linear scaling upper bound)
    cluster_throughput_sec = single_throughput_sec * num_workers
    cluster_throughput_hour = single_throughput_hour * num_workers

    op_hours_year = workload["operating_time"]["operating_hours_per_year"]
    op_hours_day = workload_cfg.working_hours_per_day

    daily_capacity_patients = cluster_throughput_hour * op_hours_day
    annual_capacity_patients = cluster_throughput_hour * op_hours_year

    # Utilization rho = arrival_rate / service_capacity
    utilization = target_patients_sec / cluster_throughput_sec

    # Headroom percentage: (capacity - target) / target * 100

    headroom_pct = (
        (annual_capacity_patients - workload_cfg.annual_patients)
        / workload_cfg.annual_patients
    ) * 100.0

    # Classification
    if utilization > 1.0:
        status = "UNDER_CAPACITY"
        status_desc = (
            "System demand exceeds processing capacity (rho > 1.0). "
            "Queue will grow unboundedly without additional compute resources."
        )
    elif utilization >= 0.80:
        status = "NEAR_CAPACITY"
        status_desc = (
            "System processing capacity is within 20% of target demand (0.80 <= rho <= 1.0). "  # noqa: E501
            "Vulnerable to arrival bursts and queueing latency spikes."
        )
    else:
        status = "CAPACITY_AVAILABLE"
        status_desc = (
            "System possesses ample computational headroom (rho < 0.80) "
            "to comfortably sustain target screening workload."
        )

    # Component breakdown (mean ms)
    comps = profile_data.get("components", {})
    cpu_ms = (
        comps.get("image_loading", {}).get("mean_ms", 0.0)
        + comps.get("iqa_scoring", {}).get("mean_ms", 0.0)
        + comps.get("borderline_enhancement", {}).get("mean_ms", 0.0)
        + comps.get("report_generation", {}).get("mean_ms", 0.0)
    )
    model_ms = comps.get("classifier_inference", {}).get("mean_ms", 0.0)
    xai_ms = (
        comps.get("gradcam_computation", {}).get("mean_ms", 0.0)
        + comps.get("evidence_generation", {}).get("mean_ms", 0.0)
    )

    return {
        "num_workers": num_workers,
        "service_time": svc_info,
        "single_worker_throughput": {
            "patients_per_second": round(single_throughput_sec, 4),
            "patients_per_minute": round(single_throughput_sec * 60.0, 2),
            "patients_per_hour": round(single_throughput_hour, 1),
        },
        "cluster_capacity": {
            "patients_per_second": round(cluster_throughput_sec, 4),
            "patients_per_hour": round(cluster_throughput_hour, 1),
            "patients_per_day": round(daily_capacity_patients, 1),
            "annual_capacity_patients": round(annual_capacity_patients, 0),
        },
        "target_comparison": {
            "target_annual_patients": workload_cfg.annual_patients,
            "target_patients_per_hour": round(target_patients_hour, 2),
            "utilization": round(utilization, 4),
            "utilization_pct": round(utilization * 100.0, 2),
            "headroom_pct": round(headroom_pct, 2),
            "status": status,
            "description": status_desc,
        },
        "timing_breakdown_ms": {
            "cpu_processing_ms": round(cpu_ms, 2),
            "model_inference_ms": round(model_ms, 2),
            "explainability_ms": round(xai_ms, 2),
        },
    }


def evaluate_resource_scenarios(
    profile_data: Dict[str, Any],
    workload_cfg: Optional[WorkloadConfig] = None,
    capacity_cfg: Optional[CapacityConfig] = None,
) -> Dict[str, Any]:
    """Simulate and compare predefined resource allocation scenarios.

    Scenarios:
        Scenario 1: 1 Processing Worker, 1 Reviewer
        Scenario 2: 2 Processing Workers, 1 Reviewer
        Scenario 3: 4 Processing Workers, 2 Reviewers

    Args:
        profile_data: Profiling data.
        workload_cfg: Workload configuration.
        capacity_cfg: Capacity configuration.

    Returns:
        dict: Comparative scenario outcomes and bottleneck analysis.
    """
    if workload_cfg is None:
        workload_cfg = WorkloadConfig()
    if capacity_cfg is None:
        capacity_cfg = CapacityConfig()

    workload = calculate_workload_rates(workload_cfg)
    target_pts_hour = workload["patient_rates"]["patients_per_hour"]

    # Review demand (cases per hour needing human specialist review)
    review_demand_hour = target_pts_hour * capacity_cfg.referable_prevalence

    scenario_definitions = [
        {"id": "scenario_1", "name": "Minimal (1 Worker, 1 Reviewer)", "workers": 1, "reviewers": 1},  # noqa: E501
        {"id": "scenario_2", "name": "Balanced (2 Workers, 1 Reviewer)", "workers": 2, "reviewers": 1},  # noqa: E501
        {"id": "scenario_3", "name": "High-Throughput (4 Workers, 2 Reviewers)", "workers": 4, "reviewers": 2},  # noqa: E501
    ]

    scenarios = []
    for sc in scenario_definitions:
        w_count = sc["workers"]
        r_count = sc["reviewers"]

        worker_eval = calculate_capacity_metrics(
            profile_data,
            workload_cfg=workload_cfg,
            capacity_cfg=capacity_cfg,
            num_workers=w_count,
        )

        # Reviewer capacity
        reviewer_cap_hour = float(r_count * capacity_cfg.reviewer_cases_per_hour)  # noqa: E501
        reviewer_util = (
            float(review_demand_hour / reviewer_cap_hour)
            if reviewer_cap_hour > 0
            else 0.0
        )

        w_util = worker_eval["target_comparison"]["utilization"]

        # Identify bottleneck
        if w_util > reviewer_util:
            bottleneck = "AI_PROCESSING_WORKERS"
            bottleneck_util = w_util
        else:
            bottleneck = "CLINICAL_REVIEWERS"
            bottleneck_util = reviewer_util

        scenarios.append({
            "scenario_id": sc["id"],
            "name": sc["name"],
            "workers": w_count,
            "reviewers": r_count,
            "worker_capacity_annual": worker_eval["cluster_capacity"]["annual_capacity_patients"],  # noqa: E501
            "worker_utilization_pct": worker_eval["target_comparison"]["utilization_pct"],  # noqa: E501
            "worker_status": worker_eval["target_comparison"]["status"],
            "reviewer_capacity_hourly": round(reviewer_cap_hour, 1),
            "reviewer_demand_hourly": round(review_demand_hour, 1),
            "reviewer_utilization_pct": round(reviewer_util * 100.0, 2),
            "primary_bottleneck": bottleneck,
            "system_limiting_utilization_pct": (
                round(bottleneck_util * 100.0, 2)
            ),
            "supports_100k_target": (w_util <= 1.0 and reviewer_util <= 1.0),
        })

    return {

        "target_annual_workload": workload_cfg.annual_patients,
        "scenarios": scenarios,
        "reviewer_parameters": {
            "reviewer_cases_per_hour": capacity_cfg.reviewer_cases_per_hour,
            "referable_prevalence": capacity_cfg.referable_prevalence,
            "parameter_type": "ASSUMPTION — requires operational validation",
        },
    }


@dataclass
class ScenarioResult:
    """Dataclass holding scenario evaluation results."""

    data: Dict[str, Any]


def evaluate_all_scenarios(
    profile_data: Dict[str, Any],
    workload_cfg: Optional[WorkloadConfig] = None,
    capacity_cfg: Optional[CapacityConfig] = None,
) -> Dict[str, Any]:
    """Alias for evaluate_resource_scenarios."""
    return evaluate_resource_scenarios(
        profile_data=profile_data,
        workload_cfg=workload_cfg,
        capacity_cfg=capacity_cfg,
    )


class CapacityModel:
    """Object-oriented wrapper for capacity evaluation."""

    def __init__(
        self,
        workload_cfg: Optional[WorkloadConfig] = None,
        capacity_cfg: Optional[CapacityConfig] = None,
    ) -> None:
        self.workload_cfg = workload_cfg or WorkloadConfig()
        self.capacity_cfg = capacity_cfg or CapacityConfig()

    def evaluate_capacity(
        self,
        profile_data: Dict[str, Any],
        num_workers: int = 1,
    ) -> Dict[str, Any]:
        """Calculate processing capacity for given worker count."""
        return calculate_capacity_metrics(
            profile_data=profile_data,
            workload_cfg=self.workload_cfg,
            capacity_cfg=self.capacity_cfg,
            num_workers=num_workers,
        )

    def evaluate_scenarios(
        self,
        profile_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate resource allocation scenarios."""
        return evaluate_resource_scenarios(
            profile_data=profile_data,
            workload_cfg=self.workload_cfg,
            capacity_cfg=self.capacity_cfg,
        )
