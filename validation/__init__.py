"""Clinical validation dataset recovery and benchmark protocol package.

Defines protocols, dataset manifests, integrity audits, and evaluation metrics
for benchmarking the trained Diabetic Retinopathy classifier.
"""

from validation.dataset import (
    locate_dataset_assets,
    load_and_validate_split,
    check_data_leakage,
    generate_dataset_manifest,
)
from validation.model_protocol import (
    verify_model_architecture,
    verify_preprocessing_protocol,
    run_model_protocol_verification,
)
from validation.benchmark_protocol import (
    compute_5class_metrics,
    compute_referable_dr_metrics,
    compute_binary_metrics,
    get_frozen_benchmark_protocol_config,
)

__all__ = [
    "locate_dataset_assets",
    "load_and_validate_split",
    "check_data_leakage",
    "generate_dataset_manifest",
    "verify_model_architecture",
    "verify_preprocessing_protocol",
    "run_model_protocol_verification",
    "compute_5class_metrics",
    "compute_referable_dr_metrics",
    "compute_binary_metrics",
    "get_frozen_benchmark_protocol_config",
]
