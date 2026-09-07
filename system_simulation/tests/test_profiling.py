"""Unit tests for pipeline runtime profiling and bandwidth metrics."""

import json
from pathlib import Path
from system_simulation.profiling import (

    compute_timing_statistics,
    measure_file_sizes,
    measure_cold_model_load,
    get_system_environment_metadata,
)
from system_simulation.reporting import calculate_bandwidth_metrics
from system_simulation.workload import WorkloadConfig, calculate_workload_rates

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "real_retinal_images"  # noqa: E501


def test_system_environment_metadata():
    """Verify system environment metadata keys."""
    meta = get_system_environment_metadata()
    assert "python_version" in meta
    assert "platform" in meta
    assert "cpu_count" in meta
    assert meta["cpu_count"] >= 1


def test_compute_timing_statistics_empty():
    """Verify empty sample list returns zeros."""
    st = compute_timing_statistics([])
    assert st["sample_count"] == 0
    assert st["mean_ms"] == 0.0
    assert st["max_ms"] == 0.0


def test_compute_timing_statistics_known_values():
    """Verify timing statistics on known seconds values."""
    # 0.1s, 0.2s, 0.3s -> 100ms, 200ms, 300ms
    st = compute_timing_statistics([0.1, 0.2, 0.3])
    assert st["sample_count"] == 3
    assert abs(st["mean_ms"] - 200.0) < 1e-2
    assert abs(st["median_ms"] - 200.0) < 1e-2
    assert abs(st["min_ms"] - 100.0) < 1e-2
    assert abs(st["max_ms"] - 300.0) < 1e-2


def test_measure_real_image_sizes():
    """Verify measurement of actual retinal image sizes."""
    assert DATA_DIR.exists(), f"Image directory not found: {DATA_DIR}"
    image_paths = sorted([
        p for p in DATA_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in [".png", ".jpg", ".jpeg"]
    ])
    assert len(image_paths) == 9, f"Expected 9 real images, found {len(image_paths)}"  # noqa: E501

    size_metrics = measure_file_sizes(image_paths)
    assert size_metrics["count"] == 9
    assert size_metrics["mean_bytes"] > 0
    assert size_metrics["min_bytes"] > 0
    assert size_metrics["max_bytes"] >= size_metrics["min_bytes"]
    assert size_metrics["mean_mb"] > 0


def test_cold_model_load_timing():
    """Verify cold model load measurement returns positive duration."""
    res = measure_cold_model_load()
    assert res["cold_load_seconds"] > 0.0
    assert res["cold_load_ms"] > 0.0


def test_bandwidth_calculations():
    """Verify network bandwidth and volume conversions."""
    size_metrics = {
        "mean_bytes": 200000.0,  # 200 KB
        "median_bytes": 200000.0,
        "min_bytes": 100000,
        "max_bytes": 400000,
        "mean_mb": 0.1907,
    }
    workload = calculate_workload_rates(WorkloadConfig(annual_patients=100000))
    bw = calculate_bandwidth_metrics(size_metrics, workload)

    # 100,000 images/year over 2000 hours = 50 images/hr
    # = ~0.0138889 images/sec
    # 0.0138889 * 200,000 bytes * 8 bits = 22,222.2 bps = ~0.0222 Mbps

    assert bw["network_throughput"]["mean_bandwidth_mbps"] > 0.0
    assert bw["network_throughput"]["mean_bandwidth_mbps"] < 1.0  # tiny bandwidth  # noqa: E501
    assert bw["data_volumes"]["daily_volume_mb"] > 0.0
    assert bw["data_volumes"]["annual_volume_gb"] > 0.0


def test_json_serialization():
    """Verify complete profiling structure serializes without error."""
    sample_payload = {
        "status": "MEASURED",
        "sample_count": 9,
        "components": {
            "test_stage": compute_timing_statistics([0.05, 0.06]),
        },
    }
    dumped = json.dumps(sample_payload)
    loaded = json.loads(dumped)
    assert loaded["status"] == "MEASURED"
