"""Automated tests for model architecture and preprocessing verification."""

from pathlib import Path

from validation.model_protocol import (
    verify_model_architecture,
    verify_preprocessing_protocol,
    run_model_protocol_verification,
    generate_model_protocol_markdown,
)

REAL_IMAGE_PATH: Path = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "real_retinal_images"
    / "cell13_r0_c0_grade0.png"
)


def test_verify_model_architecture_spec():
    """Verify frozen model architecture invariants against loaded weights."""
    arch = verify_model_architecture()

    assert arch["status"] == "PASS"
    assert arch["verified_against_frozen_spec"] is True
    assert arch["input_shape"] == [None, 384, 384, 3]
    assert arch["output_shape"] == [None, 5]
    assert arch["num_classes"] == 5
    assert arch["param_count"] == 11184436
    assert len(arch["issues"]) == 0


def test_verify_preprocessing_protocol_real_image():
    """Verify preprocessing conforms strictly to EfficientNetB3 standard."""
    assert REAL_IMAGE_PATH.exists(), f"Image missing: {REAL_IMAGE_PATH}"
    prep = verify_preprocessing_protocol(REAL_IMAGE_PATH)

    assert prep["status"] == "PASS"
    assert prep["verified_against_frozen_spec"] is True
    assert prep["target_image_size"] == [384, 384]
    assert prep["tested_tensor_shape"] == [1, 384, 384, 3]
    assert prep["tested_dtype"] == "float32"
    assert 0.0 <= prep["value_range"][0]
    assert prep["value_range"][1] <= 255.0
    assert len(prep["crop_box"]) == 4
    assert len(prep["issues"]) == 0


def test_run_model_protocol_verification():
    """Verify end-to-end model and preprocessing protocol runner."""
    res = run_model_protocol_verification(REAL_IMAGE_PATH)

    assert res["overall_status"] == "PASS"
    assert res["architecture_verification"]["status"] == "PASS"
    assert res["preprocessing_verification"]["status"] == "PASS"


def test_generate_model_protocol_markdown():
    """Verify model protocol markdown report generation."""
    res = run_model_protocol_verification(REAL_IMAGE_PATH)
    md = generate_model_protocol_markdown(res)

    assert "# Model & Preprocessing Protocol Verification Report" in md
    assert "11,184,436" in md
    assert "[None, 384, 384, 3]" in md
    assert "cv2.INTER_AREA" in md
