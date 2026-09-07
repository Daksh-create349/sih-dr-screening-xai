"""Workload modeling and arrival rate calculation module.

Calculates operational screening workload parameters:
- Converts annual patient targets (e.g. 100,000 patients/year) into
  standardized temporal demand rates (per day, per hour, per second).
- Distinguishes TARGET requirements from ASSUMED operational parameters.
- Provides rigorous formulas and conversion utilities.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


@dataclass
class WorkloadConfig:
    """Configurable workload parameters for DR screening demand.

    Attributes:
        annual_patients: Target screening demand (TARGET).
        working_days_per_year: Operational clinic days per year (ASSUMED).
        working_hours_per_day: Operating shift hours per day (ASSUMED).
        images_per_patient: Number of retinal photographs per encounter.
    """

    annual_patients: int = 100000
    working_days_per_year: int = 250
    working_hours_per_day: float = 8.0
    images_per_patient: int = 1


def calculate_workload_rates(
    config: WorkloadConfig,
) -> Dict[str, Any]:
    """Calculate temporal arrival rates and demand volumes.

    Formulas:
        op_hours_year = working_days_per_year * working_hours_per_day
        operating_seconds_per_year = op_hours_year * 3600

        patients_per_day = annual_patients / working_days_per_year
        patients_per_hour = patients_per_day / working_hours_per_day
        patients_per_second = annual_patients / operating_seconds_per_year
        mean_arrival_interval_s = 1.0 / patients_per_second

    Args:
        config: WorkloadConfig instance.

    Returns:
        dict: Detailed breakdown of patient and image arrival rates.
    """
    if config.annual_patients <= 0:
        raise ValueError("annual_patients must be strictly positive.")
    if config.working_days_per_year <= 0:
        raise ValueError("working_days_per_year must be strictly positive.")
    if config.working_hours_per_day <= 0:
        raise ValueError("working_hours_per_day must be strictly positive.")
    if config.images_per_patient <= 0:
        raise ValueError("images_per_patient must be strictly positive.")

    op_hours_year = float(
        config.working_days_per_year * config.working_hours_per_day
    )
    op_sec_year = op_hours_year * 3600.0

    patients_per_day = float(
        config.annual_patients / config.working_days_per_year
    )
    patients_per_hour = float(patients_per_day / config.working_hours_per_day)
    patients_per_minute = float(patients_per_hour / 60.0)
    patients_per_second = float(config.annual_patients / op_sec_year)
    arrival_interval_s = float(1.0 / patients_per_second)

    images_per_day = patients_per_day * config.images_per_patient
    images_per_hour = patients_per_hour * config.images_per_patient
    images_per_minute = patients_per_minute * config.images_per_patient
    images_per_second = patients_per_second * config.images_per_patient

    return {
        "config": asdict(config),
        "parameters_classification": {
            "annual_patients": "TARGET",
            "working_days_per_year": "ASSUMED",
            "working_hours_per_day": "ASSUMED",
            "images_per_patient": "ASSUMED",
        },
        "operating_time": {
            "operating_hours_per_year": round(op_hours_year, 1),
            "operating_seconds_per_year": round(op_sec_year, 1),
        },
        "patient_rates": {
            "patients_per_year": config.annual_patients,
            "patients_per_day": round(patients_per_day, 2),
            "patients_per_hour": round(patients_per_hour, 2),
            "patients_per_minute": round(patients_per_minute, 4),
            "patients_per_second": round(patients_per_second, 6),
            "mean_arrival_interval_seconds": round(arrival_interval_s, 2),
        },
        "image_rates": {
            "images_per_year": config.annual_patients * config.images_per_patient,  # noqa: E501
            "images_per_day": round(images_per_day, 2),
            "images_per_hour": round(images_per_hour, 2),
            "images_per_minute": round(images_per_minute, 4),
            "images_per_second": round(images_per_second, 6),
        },
        "formula_notes": (
            "Arrival rate lambda = annual_patients / (working_days * "
            "working_hours * 3600). Mean inter-arrival time = 1 / lambda."
        ),
    }


@dataclass
class WorkloadRates:
    """Dataclass holding computed arrival rates."""

    rates: Dict[str, Any]


class WorkloadModel:
    """Object-oriented wrapper for workload demand calculations."""

    def __init__(self, config: Optional[WorkloadConfig] = None) -> None:
        self.config = config or WorkloadConfig()

    def compute_rates(self) -> Dict[str, Any]:
        """Compute temporal arrival rates for configured parameters."""
        return calculate_workload_rates(self.config)
