import pytest
from system_simulation.capacity import (
    CapacityModel,
    calculate_capacity_metrics,
    compute_weighted_service_time_seconds,
    evaluate_resource_scenarios,
)


@pytest.fixture
def mock_profile_data():

    """Deterministic synthetic profile fixture for mathematical testing."""
    return {
        "paths": {
            "path_a_good": {"mean_ms": 500.0, "p95_ms": 600.0},
            "path_b_borderline": {"mean_ms": 800.0, "p95_ms": 950.0},
            "path_c_ungradeable": {"mean_ms": 100.0, "p95_ms": 120.0},
        },
        "path_distribution": {"GOOD": 4, "BORDERLINE": 5, "UNGRADEABLE": 1},
        "components": {
            "image_loading": {"mean_ms": 20.0},
            "iqa_scoring": {"mean_ms": 60.0},
            "borderline_enhancement": {"mean_ms": 50.0},
            "classifier_inference": {"mean_ms": 150.0},
            "referable_decision": {"mean_ms": 1.0},
            "gradcam_computation": {"mean_ms": 200.0},
            "evidence_generation": {"mean_ms": 30.0},
            "report_generation": {"mean_ms": 5.0},
            "pipeline_end_to_end": {"mean_ms": 516.0},
        },
    }


def test_compute_weighted_service_time(mock_profile_data):
    """Verify path-weighted service time calculation."""
    # Weights: 4/10=0.4, 5/10=0.5, 1/10=0.1
    # Expected ms: (0.4 * 500) + (0.5 * 800) + (0.1 * 100) = 200 + 400 + 10 = 610 ms  # noqa: E501
    svc = compute_weighted_service_time_seconds(mock_profile_data)
    assert abs(svc["weighted_service_time_ms"] - 610.0) < 1e-2
    assert abs(svc["weighted_service_time_seconds"] - 0.610) < 1e-4


def test_capacity_metrics_available(mock_profile_data):
    """Verify single-worker capacity with plenty of headroom."""
    # Weighted svc: 0.610s -> ~1.639 pts/s -> 5901.6 pts/hr -> 11,803,278 pts/year  # noqa: E501
    res = calculate_capacity_metrics(mock_profile_data, num_workers=1)
    comp = res["target_comparison"]
    assert comp["status"] == "CAPACITY_AVAILABLE"
    assert comp["utilization"] < 0.80
    assert comp["headroom_pct"] > 0
    assert res["cluster_capacity"]["annual_capacity_patients"] > 100000


def test_capacity_metrics_under_capacity():
    """Verify UNDER_CAPACITY classification when service time is very high."""
    slow_profile = {
        "paths": {
            "path_a_good": {"mean_ms": 100000.0, "p95_ms": 110000.0},  # 100s
            "path_b_borderline": {"mean_ms": 100000.0, "p95_ms": 110000.0},
            "path_c_ungradeable": {"mean_ms": 100000.0, "p95_ms": 110000.0},
        },
        "path_distribution": {"GOOD": 1, "BORDERLINE": 0, "UNGRADEABLE": 0},
        "components": {},
    }
    # 100s/pt -> 36 pts/hr -> 72,000 pts/yr (< 100k target)
    res = calculate_capacity_metrics(slow_profile, num_workers=1)
    comp = res["target_comparison"]
    assert comp["status"] == "UNDER_CAPACITY"
    assert comp["utilization"] > 1.0
    assert comp["headroom_pct"] < 0


def test_capacity_metrics_near_capacity():
    """Verify NEAR_CAPACITY classification when utilization is 80-100%."""
    # Target is 50 pts/hr. At 60 pts/hr capacity, util = 50/60 = 83.3%
    # 60 pts/hr = 60s per patient = 60,000 ms
    near_profile = {
        "paths": {
            "path_a_good": {"mean_ms": 60000.0, "p95_ms": 61000.0},
            "path_b_borderline": {"mean_ms": 60000.0, "p95_ms": 61000.0},
            "path_c_ungradeable": {"mean_ms": 60000.0, "p95_ms": 61000.0},
        },
        "path_distribution": {"GOOD": 1, "BORDERLINE": 0, "UNGRADEABLE": 0},
        "components": {},
    }
    res = calculate_capacity_metrics(near_profile, num_workers=1)
    comp = res["target_comparison"]
    assert comp["status"] == "NEAR_CAPACITY"
    assert 0.80 <= comp["utilization"] <= 1.0


def test_resource_scenarios_comparison(mock_profile_data):
    """Verify scenario evaluation across worker/reviewer counts."""
    eval_res = evaluate_resource_scenarios(mock_profile_data)
    scenarios = eval_res["scenarios"]
    assert len(scenarios) == 3

    s1, s2, s3 = scenarios[0], scenarios[1], scenarios[2]
    assert s1["workers"] == 1 and s1["reviewers"] == 1
    assert s2["workers"] == 2 and s2["reviewers"] == 1
    assert s3["workers"] == 4 and s3["reviewers"] == 2

    # Scaling worker capacity: 4W should have 4x capacity of 1W
    assert abs(s3["worker_capacity_annual"] - (4 * s1["worker_capacity_annual"])) < 10.0  # noqa: E501

    # In s2 with 2W, reviewer capacity is 30/hr vs 20/hr demand (66.7% util)
    # while worker util is tiny (<1%). Bottleneck must be CLINICAL_REVIEWERS.
    assert s2["primary_bottleneck"] == "CLINICAL_REVIEWERS"
    assert s2["supports_100k_target"] is True


def test_capacity_model_wrapper(mock_profile_data):
    """Verify CapacityModel class wrapper."""
    model = CapacityModel()
    m_res = model.evaluate_capacity(mock_profile_data, num_workers=2)
    assert m_res["num_workers"] == 2
    sc_res = model.evaluate_scenarios(mock_profile_data)
    assert len(sc_res["scenarios"]) == 3
