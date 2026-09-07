"""Automated test suite for retinal image enhancement pipeline (image_quality.enhancement).

Validates:
- Original retinal files are strictly never overwritten
- Enhanced outputs are valid RGB uint8 images matching source dimensions
- No NaN, Inf, or out-of-bound values in output arrays
- Candidate methods ('clahe', 'unsharp', 'ben_graham', 'denoise') run reliably
- Enhancement API returns complete documented dictionary structures
- Mathematical correctness of before/after score differences
- Safeguards catch over-enhancement (e.g. Ben Graham chromaticity distortion)
- Rejected enhancement falls back to original image
- Invalid inputs, dimensions, and unknown methods are rejected safely
- End-to-end evaluation on real borderline retinal images
"""

import tempfile
from pathlib import Path
import pytest
import numpy as np

from image_quality.enhancement import (
    enhance_clahe,
    enhance_unsharp_mask,
    enhance_ben_graham,
    enhance_denoise,
    enhance_image,
    compute_distortion_metrics,
    evaluate_enhancement,
    select_best_enhancement,
    DEFAULT_SAFEGUARD_THRESHOLDS,
)
from image_quality.io import load_raw_image


DATA_DIR = Path("/Users/dakshsrivastava/Desktop/DR /data/real_retinal_images")
BORDERLINE_IMAGE_FILES = [
    "cell13_r1_c1_grade3.png",
    "cell13_r0_c1_grade1.png",
    "aptos_train_sample_c10.png",
    "cell13_r0_c0_grade0.png",
    "cell13_r0_c2_grade2.png",
]


def test_candidate_methods_produce_valid_arrays():
    """Verify all candidate methods produce valid RGB uint8 arrays with finite values."""
    img_path = DATA_DIR / BORDERLINE_IMAGE_FILES[0]
    img = load_raw_image(img_path)

    methods = [
        ("clahe", enhance_clahe(img)),
        ("unsharp", enhance_unsharp_mask(img)),
        ("ben_graham", enhance_ben_graham(img)),
        ("denoise", enhance_denoise(img)),
    ]

    for name, enh in methods:
        assert isinstance(enh, np.ndarray), f"Method {name} did not return ndarray"
        assert enh.shape == img.shape, f"Method {name} altered image shape"
        assert enh.dtype == np.uint8, f"Method {name} output dtype is {enh.dtype}, expected uint8"
        assert np.all(np.isfinite(enh)), f"Method {name} produced non-finite values"
        assert enh.min() >= 0 and enh.max() <= 255


def test_enhance_image_dispatch_api():
    """Verify enhance_image dispatch function with different methods."""
    img_path = DATA_DIR / BORDERLINE_IMAGE_FILES[0]

    for m in ["clahe", "unsharp", "ben_graham", "denoise"]:
        arr, meta = enhance_image(img_path, method=m)
        assert isinstance(arr, np.ndarray)
        assert meta["method"] == m
        assert "parameters" in meta
        assert meta["output_dtype"] == "uint8"


def test_enhance_image_invalid_method_raises():
    """Verify unknown method name raises ValueError."""
    img_path = DATA_DIR / BORDERLINE_IMAGE_FILES[0]
    with pytest.raises(ValueError, match="Unknown enhancement method"):
        enhance_image(img_path, method="magic_filter")


def test_invalid_input_shapes_and_types_raise():
    """Verify invalid shapes (e.g. 2D or 4D) and types raise appropriate errors."""
    with pytest.raises(TypeError):
        enhance_image(12345)

    invalid_2d = np.zeros((100, 100), dtype=np.uint8)
    with pytest.raises(ValueError, match="3-channel RGB"):
        enhance_clahe(invalid_2d)

    invalid_4d = np.zeros((10, 10, 10, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="3-channel RGB"):
        enhance_unsharp_mask(invalid_4d)


def test_original_file_never_overwritten():
    """Verify source files are strictly unchanged after enhancement operations."""
    test_file = DATA_DIR / BORDERLINE_IMAGE_FILES[0]
    mtime_before = test_file.stat().st_mtime
    size_before = test_file.stat().st_size
    bytes_before = test_file.read_bytes()

    with tempfile.TemporaryDirectory() as tmpdir:
        res = select_best_enhancement(test_file, save_dir=Path(tmpdir))
        assert Path(res["saved_enhanced_path"]).exists()
        assert Path(res["saved_enhanced_path"]) != test_file

    mtime_after = test_file.stat().st_mtime
    size_after = test_file.stat().st_size
    bytes_after = test_file.read_bytes()

    assert mtime_before == mtime_after
    assert size_before == size_after
    assert bytes_before == bytes_after


def test_distortion_metrics_mathematical_properties():
    """Verify distortion metrics between identical and modified images."""
    img_path = DATA_DIR / BORDERLINE_IMAGE_FILES[0]
    img = load_raw_image(img_path)

    # Identical images must yield zero distortion
    zero_dist = compute_distortion_metrics(img, img)
    assert pytest.approx(zero_dist["delta_e"], abs=1e-2) == 0.0
    assert pytest.approx(zero_dist["chroma_shift"], abs=1e-2) == 0.0
    assert pytest.approx(zero_dist["dark_clip_diff_pct"], abs=1e-2) == 0.0
    assert pytest.approx(zero_dist["bright_clip_diff_pct"], abs=1e-2) == 0.0
    assert pytest.approx(zero_dist["gradient_ratio"], abs=1e-2) == 1.0


def test_ben_graham_triggers_safeguard_color_distortion():
    """Verify Ben Graham method is rejected by the chromaticity safeguard."""
    img_path = DATA_DIR / BORDERLINE_IMAGE_FILES[0]
    img = load_raw_image(img_path)
    bg_img = enhance_ben_graham(img)

    eval_res = evaluate_enhancement(img, bg_img, method="ben_graham")
    assert eval_res["accepted"] is False
    assert any("color distortion" in v.lower() for v in eval_res["safeguard_violations"])
    assert eval_res["final_routing"]["active_image_source"] == "original_fallback"


def test_evaluate_enhancement_score_differences_math():
    """Verify score difference arithmetic (after - before) is strictly correct."""
    img_path = DATA_DIR / BORDERLINE_IMAGE_FILES[0]
    img = load_raw_image(img_path)
    enh = enhance_clahe(img)

    eval_res = evaluate_enhancement(img, enh, method="clahe")
    diffs = eval_res["score_differences"]
    b = eval_res["before_scores"]
    a = eval_res["after_scores"]

    expected_delta_comp = round(a["composite_score"] - b["composite_score"], 2)
    assert pytest.approx(diffs["delta_composite"], abs=0.01) == expected_delta_comp

    expected_delta_focus = round(a["component_scores"]["focus_score"] - b["component_scores"]["focus_score"], 2)
    assert pytest.approx(diffs["delta_focus"], abs=0.01) == expected_delta_focus


def test_select_best_enhancement_in_memory_array():
    """Verify select_best_enhancement accepts in-memory numpy arrays."""
    img_path = DATA_DIR / BORDERLINE_IMAGE_FILES[0]
    img = load_raw_image(img_path)

    res = select_best_enhancement(img, candidate_methods=["clahe", "unsharp"])
    assert "best_method" in res
    assert res["best_method"] in ["clahe", "unsharp", "none_fallback_original"]
    assert "all_evaluations" in res
    assert len(res["all_evaluations"]) == 2


@pytest.mark.parametrize("filename", BORDERLINE_IMAGE_FILES)
def test_real_borderline_images_enhancement_pipeline_end_to_end(filename):
    """Verify end-to-end enhancement evaluation on all 5 real borderline retinal images."""
    img_path = DATA_DIR / filename
    res = select_best_enhancement(img_path, candidate_methods=["clahe", "unsharp", "ben_graham", "denoise"])

    assert res["best_method"] in ["clahe", "unsharp", "denoise", "none_fallback_original"]
    best_eval = res["selected_evaluation"]
    if best_eval is not None:
        assert best_eval["accepted"] is True
        # Verify no safeguard violations in accepted output
        assert len(best_eval["safeguard_violations"]) == 0
        # Verify composite score did not degrade
        assert best_eval["score_differences"]["delta_composite"] >= 0.0
