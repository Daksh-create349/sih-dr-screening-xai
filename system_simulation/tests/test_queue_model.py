"""Unit tests for M/M/c queueing theory and discrete-event simulation."""

import pytest
from system_simulation.queue_model import (
    AnalyticalQueueModel,
    DiscreteEventSimulation,
    compute_mmc_analytics,
    simulate_shift_queue,
)


def test_mmc_stable_single_server():
    """Verify analytical M/M/1 queue under stable load."""
    # lambda = 1.0 arrival/sec, mu = 2.0 service/sec (rho = 0.5)
    # Lq = rho^2 / (1 - rho) = 0.25 / 0.5 = 0.5
    # Wq = Lq / lambda = 0.5 / 1.0 = 0.5 sec
    res = compute_mmc_analytics(
        arrival_rate=1.0,
        service_rate_per_worker=2.0,
        num_workers=1,
    )
    assert res["stable"] is True
    assert abs(res["utilization"] - 0.5) < 1e-4
    assert abs(res["avg_queue_length_lq"] - 0.5) < 1e-4
    assert abs(res["avg_wait_time_queue_s"] - 0.5) < 1e-4
    assert abs(res["avg_system_length_l"] - 1.0) < 1e-4


def test_mmc_unstable_server():
    """Verify detection of unstable queue when arrival exceeds capacity."""
    res = compute_mmc_analytics(
        arrival_rate=5.0,
        service_rate_per_worker=2.0,
        num_workers=2,  # total capacity = 4.0 < 5.0
    )
    assert res["stable"] is False
    assert res["utilization"] >= 1.0
    assert res["avg_queue_length_lq"] == float("inf")


def test_mmc_invalid_inputs():
    """Verify validation for negative or zero rates."""
    with pytest.raises(ValueError):
        compute_mmc_analytics(0.0, 1.0, 1)
    with pytest.raises(ValueError):
        compute_mmc_analytics(1.0, 0.0, 1)
    with pytest.raises(ValueError):
        compute_mmc_analytics(1.0, 1.0, 0)


def test_discrete_event_simulation_deterministic():
    """Verify discrete-event queue simulation is deterministic with seed."""
    sim1 = simulate_shift_queue(
        arrival_rate_per_sec=0.01389,  # ~50 pts/hr
        service_time_sec_mean=0.8,
        service_time_sec_std=0.05,
        num_workers=1,
        shift_hours=1.0,  # 1 hour
        seed=123,
    )
    sim2 = simulate_shift_queue(
        arrival_rate_per_sec=0.01389,
        service_time_sec_mean=0.8,
        service_time_sec_std=0.05,
        num_workers=1,
        shift_hours=1.0,
        seed=123,
    )

    # Identical seed must yield identical arrivals and wait times
    assert sim1["total_arrivals"] == sim2["total_arrivals"]
    assert sim1["queue_length"]["mean"] == sim2["queue_length"]["mean"]
    assert sim1["waiting_time_seconds"]["mean_s"] == sim2["waiting_time_seconds"]["mean_s"]  # noqa: E501
    assert sim1["queue_length"]["mean"] >= 0.0
    assert sim1["waiting_time_seconds"]["mean_s"] >= 0.0


def test_analytical_and_discrete_wrappers():
    """Verify wrapper classes."""
    an_res = AnalyticalQueueModel.compute(1.0, 3.0, 1)
    assert an_res["stable"] is True

    des = DiscreteEventSimulation(shift_hours=0.5, seed=42)
    des_res = des.simulate(
        arrival_rate_per_sec=0.01,
        service_time_sec_mean=1.0,
    )
    assert des_res["total_arrivals"] > 0
