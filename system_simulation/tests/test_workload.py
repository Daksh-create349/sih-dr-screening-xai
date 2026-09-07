"""Unit tests for workload modeling and arrival rate formulas."""

import pytest
from system_simulation.workload import (
    WorkloadConfig,
    WorkloadModel,
    calculate_workload_rates,
)


def test_workload_default_rates():
    """Verify standard 100k annual patients workload rates."""
    cfg = WorkloadConfig(
        annual_patients=100000,
        working_days_per_year=250,
        working_hours_per_day=8.0,
        images_per_patient=1,
    )
    rates = calculate_workload_rates(cfg)

    # 100,000 / 250 = 400 patients / day
    assert rates["patient_rates"]["patients_per_day"] == 400.0

    # 400 / 8 = 50 patients / hour
    assert rates["patient_rates"]["patients_per_hour"] == 50.0

    # 50 / 3600 = ~0.0138889 pts/s
    assert abs(rates["patient_rates"]["patients_per_second"] - (50.0 / 3600.0)) < 1e-6  # noqa: E501

    # Inter-arrival interval = 1 / lambda = 72 seconds
    assert rates["patient_rates"]["mean_arrival_interval_seconds"] == 72.0

    # Operating hours: 250 * 8 = 2000 hours
    assert rates["operating_time"]["operating_hours_per_year"] == 2000.0

    # Parameters classification
    assert rates["parameters_classification"]["annual_patients"] == "TARGET"
    assert rates["parameters_classification"]["working_days_per_year"] == "ASSUMED"  # noqa: E501


def test_workload_model_wrapper():
    """Verify WorkloadModel object-oriented wrapper."""
    model = WorkloadModel(WorkloadConfig(annual_patients=50000))
    rates = model.compute_rates()
    assert rates["patient_rates"]["patients_per_day"] == 200.0
    assert rates["patient_rates"]["patients_per_hour"] == 25.0


def test_workload_multi_images_per_patient():
    """Verify 2 images per patient doubles image rates."""
    cfg = WorkloadConfig(annual_patients=100000, images_per_patient=2)
    rates = calculate_workload_rates(cfg)

    assert rates["image_rates"]["images_per_day"] == 800.0
    assert rates["image_rates"]["images_per_hour"] == 100.0
    assert rates["patient_rates"]["patients_per_day"] == 400.0


def test_workload_invalid_inputs():
    """Verify validation errors for zero or negative values."""
    with pytest.raises(ValueError, match="annual_patients"):
        calculate_workload_rates(WorkloadConfig(annual_patients=0))

    with pytest.raises(ValueError, match="working_days_per_year"):
        calculate_workload_rates(WorkloadConfig(working_days_per_year=-10))

    with pytest.raises(ValueError, match="working_hours_per_day"):
        calculate_workload_rates(WorkloadConfig(working_hours_per_day=0))

    with pytest.raises(ValueError, match="images_per_patient"):
        calculate_workload_rates(WorkloadConfig(images_per_patient=-1))
