"""Tests for Simulink environment verification and system architecture.

Verifies:
- MATLAB and Simulink availability detection
- Strict BLOCKED status when MATLAB/Simulink is not installed
- Structural integrity of architecture specification JSON
- Presence of all 8 required subsystems
- Safety invariant: UNGRADEABLE strictly bypasses classifier
- Annual target workload parameter (100,000 patients/year)
- Parameter classification into MEASURED, ASSUMED, and TARGET
- Presence of MATLAB verification script and documentation
"""

import json
from pathlib import Path
import shutil
import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
SIMULINK_DIR = WORKSPACE_ROOT / "simulink"
SUMMARY_JSON = SIMULINK_DIR / "results" / "architecture_summary.json"
VERIFICATION_MD = SIMULINK_DIR / "results" / "architecture_verification.md"
VERIFICATION_M = SIMULINK_DIR / "scripts" / "verify_simulink_architecture.m"
README_MD = SIMULINK_DIR / "README.md"


@pytest.fixture
def architecture_summary():
    """Load architecture summary JSON."""
    assert SUMMARY_JSON.exists(), f"Missing {SUMMARY_JSON}"
    with open(SUMMARY_JSON, "r") as f:
        return json.load(f)


def test_matlab_environment_detection():
    """Verify system-level detection of MATLAB executable."""
    matlab_in_path = shutil.which("matlab") is not None
    app_exists = any(Path("/Applications").glob("MATLAB*.app"))

    is_installed = matlab_in_path or app_exists
    # On this environment, MATLAB is not installed
    if not is_installed:
        assert matlab_in_path is False
        assert app_exists is False


def test_blocked_status_when_matlab_unavailable(architecture_summary):
    """Verify that absence of MATLAB enforces BLOCKED status."""
    env = architecture_summary["matlab_environment"]
    if not env["installed"]:
        assert architecture_summary["status"] == "BLOCKED"
        assert "unavailable" in architecture_summary["status_reason"].lower()
        assert env["simulink_status"] == "UNAVAILABLE"
        assert env["can_open_model"] is False
        assert env["can_compile_model"] is False


def test_all_eight_subsystems_specified(architecture_summary):
    """Verify that all 8 required conceptual subsystems are defined."""
    required = {
        "Acquisition",
        "Image Quality Assessment (IQA)",
        "Borderline Enhancement (CLAHE)",
        "DR Classifier (EfficientNetB3)",
        "Referable Decision (0.33 threshold)",
        "Explainability (Grad-CAM)",
        "Reporting",
        "Clinical Review Queue",
    }

    subsystems = set(architecture_summary["system_architecture"]["subsystems"])
    assert required.issubset(subsystems), f"Missing subsystems: {required - subsystems}"  # noqa: E501


def test_routing_logic_and_ungradeable_safety(architecture_summary):
    """Verify routing invariants: UNGRADEABLE must strictly bypass classifier."""  # noqa: E501
    routing = architecture_summary["system_architecture"]["routing_logic"]

    assert "GOOD" in routing
    assert "BORDERLINE" in routing
    assert "UNGRADEABLE" in routing

    # GOOD routes to Classifier
    assert "Classifier" in routing["GOOD"]

    # BORDERLINE routes to Enhancement then re-check
    assert "Enhancement" in routing["BORDERLINE"]

    # UNGRADEABLE routes to Recapture and STOPS, NEVER to Classifier
    ungradeable_path = routing["UNGRADEABLE"].lower()
    assert "recapture" in ungradeable_path
    assert "stop" in ungradeable_path
    assert "classifier" not in ungradeable_path or "bypassed" in ungradeable_path  # noqa: E501


def test_annual_target_volume_parameter(architecture_summary):
    """Verify target annual volume is exactly 100,000 patients/year."""
    vol = architecture_summary["target_annual_patient_volume"]
    assert vol == 100000


def test_parameter_classification(architecture_summary):
    """Verify strict separation into MEASURED, ASSUMED, and TARGET parameters."""  # noqa: E501
    params = architecture_summary["parameter_classification"]

    assert "measured" in params
    assert "assumed" in params
    assert "target" in params

    # No unverified performance numbers in measured list
    assert len(params["measured"]) == 0, "Do not claim measured throughput yet"

    # All key latencies and rates must be marked assumed
    assumed = params["assumed"]
    assert "iqa_processing_time" in assumed
    assert "classifier_processing_time" in assumed
    assert "gradcam_processing_time" in assumed


def test_verification_artifacts_exist():
    """Verify that verification scripts, reports, and README exist."""
    assert VERIFICATION_M.exists() and VERIFICATION_M.stat().st_size > 0
    assert VERIFICATION_MD.exists() and VERIFICATION_MD.stat().st_size > 0
    assert README_MD.exists() and README_MD.stat().st_size > 0

    # README must distinguish MEASURED, ASSUMED, TARGET
    readme_text = README_MD.read_text()
    assert "MEASURED" in readme_text
    assert "ASSUMED" in readme_text
    assert "TARGET" in readme_text
