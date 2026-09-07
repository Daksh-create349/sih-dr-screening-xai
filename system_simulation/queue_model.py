"""Screening queue simulation and analytical queueing theory model.

Implements:
- Multi-server M/M/c analytical queueing formulas (Erlang-C).
- Discrete-event queue simulation over an operational screening shift.
- Queue length dynamics, waiting times, and server utilization.
- Deterministic simulation mode for reproducible regression verification.
"""

from dataclasses import dataclass
from math import factorial
from typing import Dict, Any, List
import numpy as np


@dataclass
class SimPatient:
    """Dataclass representing an individual screening patient entity."""

    patient_id: int
    arrival_time_s: float
    start_time_s: float = 0.0
    completion_time_s: float = 0.0
    waiting_time_s: float = 0.0
    service_time_s: float = 0.0
    worker_id: int = 0


def compute_mmc_analytics(

    arrival_rate: float,
    service_rate_per_worker: float,
    num_workers: int = 1,
) -> Dict[str, Any]:
    """Calculate analytical steady-state M/M/c queueing metrics.

    Args:
        arrival_rate: Lambda (arrivals per second).
        service_rate_per_worker: Mu (service rate per worker in items/sec).
        num_workers: c (number of parallel worker servers).

    Returns:
        dict: Analytical queue length, wait times, and utilization.
    """
    if arrival_rate <= 0 or service_rate_per_worker <= 0 or num_workers <= 0:
        raise ValueError("Rates and worker counts must be strictly positive.")

    c = num_workers
    lam = float(arrival_rate)
    mu = float(service_rate_per_worker)
    a = lam / mu  # Offered load
    rho = a / c   # Server utilization

    if rho >= 1.0:
        return {
            "stable": False,
            "arrival_rate_per_sec": round(lam, 6),
            "service_rate_per_sec": round(mu, 4),
            "num_workers": c,
            "utilization": round(rho, 4),
            "erlang_c_prob_queue": 1.0,
            "avg_queue_length_lq": float("inf"),
            "avg_system_length_l": float("inf"),
            "avg_wait_time_queue_s": float("inf"),
            "avg_time_in_system_s": float("inf"),
            "note": "System unstable: arrival rate exceeds service capacity (rho >= 1.0).",  # noqa: E501
        }

    # Calculate P0 (Probability of 0 items in system)
    sum_terms = sum((a ** n) / factorial(n) for n in range(c))
    last_term = ((a ** c) / (factorial(c) * (1.0 - rho)))
    p0 = 1.0 / (sum_terms + last_term)

    # Erlang-C formula: P(Queueing)
    erlang_c = last_term * p0

    # Average queue length Lq (number of items waiting in queue)
    lq = (erlang_c * rho) / (1.0 - rho)

    # Average number of items in system L
    l_sys = lq + a

    # Average waiting time in queue Wq (Little's Law: Wq = Lq / lambda)
    wq = lq / lam

    # Average total time in system W = Wq + 1/mu
    w_sys = wq + (1.0 / mu)

    return {
        "stable": True,
        "arrival_rate_per_sec": round(lam, 6),
        "service_rate_per_sec": round(mu, 4),
        "num_workers": c,
        "utilization": round(rho, 4),
        "erlang_c_prob_queue": round(erlang_c, 4),
        "avg_queue_length_lq": round(lq, 3),
        "avg_system_length_l": round(l_sys, 3),
        "avg_wait_time_queue_s": round(wq, 3),
        "avg_wait_time_queue_min": round(wq / 60.0, 3),
        "avg_time_in_system_s": round(w_sys, 3),
        "avg_time_in_system_min": round(w_sys / 60.0, 3),
    }


def simulate_shift_queue(
    arrival_rate_per_sec: float,
    service_time_sec_mean: float,
    service_time_sec_std: float = 0.0,
    num_workers: int = 1,
    shift_hours: float = 8.0,
    seed: int = 42,
) -> Dict[str, Any]:
    """Execute dynamic discrete-event simulation of screening shift queue.

    Args:
        arrival_rate_per_sec: Average arrivals per second.
        service_time_sec_mean: Mean processing time per image in seconds.
        service_time_sec_std: Standard deviation of service time in seconds.
        num_workers: Number of parallel processing workers.
        shift_hours: Duration of simulated clinic shift in hours.
        seed: Random seed for deterministic reproducibility.

    Returns:
        dict: Simulated queue statistics and sampled time-series.
    """
    rng = np.random.default_rng(seed)
    total_seconds = int(shift_hours * 3600)

    # Generate Poisson arrivals
    expected_arrivals = int(arrival_rate_per_sec * total_seconds)
    if expected_arrivals <= 0:
        expected_arrivals = 1

    inter_arrivals = rng.exponential(
        1.0 / arrival_rate_per_sec, size=expected_arrivals * 2
    )
    arrival_times = np.cumsum(inter_arrivals)
    arrival_times = arrival_times[arrival_times <= total_seconds]
    num_arrivals = len(arrival_times)

    # Worker availability tracking (when each worker becomes free)
    worker_free_times = np.zeros(num_workers, dtype=float)

    wait_times: List[float] = []
    service_times: List[float] = []
    completion_times: List[float] = []

    for t_arr in arrival_times:
        # Assign to earliest available worker
        earliest_worker = int(np.argmin(worker_free_times))
        start_time = max(t_arr, worker_free_times[earliest_worker])
        wait_time = start_time - t_arr
        wait_times.append(wait_time)

        # Sample service time (clipped log-normal or Gaussian)
        if service_time_sec_std > 0:
            svc = float(
                rng.normal(service_time_sec_mean, service_time_sec_std)
            )
            svc = max(0.01, svc)
        else:
            svc = float(service_time_sec_mean)

        service_times.append(svc)
        comp_time = start_time + svc
        completion_times.append(comp_time)
        worker_free_times[earliest_worker] = comp_time

    # Sample queue lengths over time every 60 seconds
    time_grid = np.arange(0, total_seconds, 60)
    queue_lengths = []

    for t in time_grid:
        # Items arrived on or before t but started after t
        in_queue = sum(
            1 for i in range(num_arrivals)
            if (
                arrival_times[i] <= t
                and (arrival_times[i] + wait_times[i]) > t
            )
        )
        queue_lengths.append(in_queue)

    wait_arr = np.array(wait_times) if wait_times else np.array([0.0])
    q_arr = np.array(queue_lengths) if queue_lengths else np.array([0])

    return {
        "simulation_parameters": {
            "shift_hours": shift_hours,
            "total_seconds": total_seconds,
            "arrival_rate_per_sec": round(arrival_rate_per_sec, 6),
            "service_time_mean_s": round(service_time_sec_mean, 4),
            "num_workers": num_workers,
            "seed": seed,
        },
        "total_arrivals": num_arrivals,
        "total_completed": sum(1 for c in completion_times if c <= total_seconds),  # noqa: E501
        "queue_length": {
            "mean": round(float(np.mean(q_arr)), 2),
            "median": round(float(np.median(q_arr)), 2),
            "max": int(np.max(q_arr)),
            "p95": round(float(np.percentile(q_arr, 95)), 2),
        },
        "waiting_time_seconds": {
            "mean_s": round(float(np.mean(wait_arr)), 2),
            "median_s": round(float(np.median(wait_arr)), 2),
            "max_s": round(float(np.max(wait_arr)), 2),
            "p95_s": round(float(np.percentile(wait_arr, 95)), 2),
        },
        "time_series_sample": {
            "time_minutes": [round(float(t / 60.0), 1) for t in time_grid[::5]],  # sample every 5 min  # noqa: E501
            "queue_lengths": [int(q) for q in queue_lengths[::5]],
        },
    }


class AnalyticalQueueModel:
    """Wrapper for Erlang-C M/M/c analytical queue formulas."""

    @staticmethod
    def compute(
        arrival_rate: float,
        service_rate_per_worker: float,
        num_workers: int = 1,
    ) -> Dict[str, Any]:
        """Compute Erlang-C steady-state queue performance."""
        return compute_mmc_analytics(
            arrival_rate=arrival_rate,
            service_rate_per_worker=service_rate_per_worker,
            num_workers=num_workers,
        )


class DiscreteEventSimulation:
    """Wrapper for discrete-event shift queue simulation."""

    def __init__(
        self,
        shift_hours: float = 8.0,
        seed: int = 42,
    ) -> None:
        self.shift_hours = shift_hours
        self.seed = seed

    def simulate(
        self,
        arrival_rate_per_sec: float,
        service_time_sec_mean: float,
        service_time_sec_std: float = 0.0,
        num_workers: int = 1,
    ) -> Dict[str, Any]:
        """Execute discrete-event simulation over shift."""
        return simulate_shift_queue(
            arrival_rate_per_sec=arrival_rate_per_sec,
            service_time_sec_mean=service_time_sec_mean,
            service_time_sec_std=service_time_sec_std,
            num_workers=num_workers,
            shift_hours=self.shift_hours,
            seed=self.seed,
        )
