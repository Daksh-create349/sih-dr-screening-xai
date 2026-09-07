"""Automated tests for anatomical retinal localization and context regions.

Tests cover:
- Retinal field boundary extraction
- Optic disc candidate integration
- Macular / foveal estimation heuristic
- Low-confidence and fallback handling
- Anatomical context region partition consistency
- Attention statistics computation and mass conservation
- Top attention bounding box extraction
- Determinism on real retinal images
"""

from pathlib import Path
import numpy as np
import pytest

from explainability.anatomy import (
    localize_retinal_anatomy,
    define_anatomical_regions,
    compute_attention_region_statistics,
    extract_top_attention_bounding_box,
    estimate_macular_region,
)
from image_quality.io import load_raw_image

WORKSPACE_ROOT: Path = Path(__file__).resolve().parent.parent.parent
DATA_DIR: Path = WORKSPACE_ROOT / "data" / "real_retinal_images"
REAL_IMAGE_PATH: Path = DATA_DIR / "cell13_r0_c0_grade0.png"


def test_localize_retinal_anatomy_real_image():
    """Verify anatomical landmark localization on real retinal image."""
    assert REAL_IMAGE_PATH.exists(), f"Image missing: {REAL_IMAGE_PATH}"
    img = load_raw_image(REAL_IMAGE_PATH)
    h, w = img.shape[:2]

    res = localize_retinal_anatomy(img)

    assert "image_dimensions" in res
    assert res["image_dimensions"] == [h, w]

    # Retinal field
    field = res["retinal_field"]
    assert "bounding_box" in field
    assert "center" in field
    assert "radius" in field
    assert field["radius"] > 50.0
    assert 0 <= field["center_x"] < w
    assert 0 <= field["center_y"] < h

    # Optic disc
    od = res["optic_disc"]
    assert "detected" in od
    assert "confidence" in od
    if od["detected"]:
        assert od["center"] is not None
        assert 0 <= od["center"][0] < w
        assert 0 <= od["center"][1] < h
        assert od["radius"] > 0

    # Macula
    mac = res["macula"]
    assert "detected" in mac
    assert "center" in mac
    assert "confidence" in mac
    assert "status" in mac
    assert mac["status"] in [
        "high_confidence",
        "moderate_confidence",
        "low_confidence",
        "not_reliably_localized",
    ]
    if mac["detected"]:
        assert 0 <= mac["center_x"] < w
        assert 0 <= mac["center_y"] < h
        assert mac["radius"] > 0

    # Retinal mask
    mask = res["retina_mask"]
    assert mask.shape == (h, w)
    assert mask.dtype == bool
    assert np.any(mask)


def test_macular_fallback_when_od_missing():
    """Verify safe fallback to retinal center when optic disc is absent."""
    fake_mask = np.zeros((300, 300), dtype=bool)
    fake_mask[50:250, 50:250] = True
    fake_img = np.full((300, 300, 3), 128, dtype=np.uint8)

    missing_od = {"detected": False, "center": None, "radius": None}
    res = estimate_macular_region(
        image=fake_img,
        retina_mask=fake_mask,
        optic_disc=missing_od,
        retina_center=(150.0, 150.0),
        retina_radius=100.0,
    )

    assert res["detected"] is True
    assert res["status"] == "low_confidence"
    assert res["confidence"] == 0.35
    assert res["center"] == [150.0, 150.0]
    assert res["method"] == "geometric_center_default_fallback"


def test_macular_empty_foreground_handling():
    """Verify graceful handling when no foreground pixels exist."""
    empty_mask = np.zeros((200, 200), dtype=bool)
    fake_img = np.zeros((200, 200, 3), dtype=np.uint8)
    missing_od = {"detected": False, "center": None}

    res = estimate_macular_region(
        image=fake_img,
        retina_mask=empty_mask,
        optic_disc=missing_od,
        retina_center=(100.0, 100.0),
        retina_radius=50.0,
    )

    assert res["detected"] is False
    assert res["status"] == "not_reliably_localized"
    assert res["center"] is None


def test_define_anatomical_regions_consistency():
    """Verify anatomical context regions form consistent partitions."""
    h, w = 400, 400
    y, x = np.ogrid[:h, :w]
    # Synthetic circular retina mask centered at (200, 200) with radius 150
    dist = np.hypot(x - 200, y - 200)
    retina_mask = dist <= 150

    od_meta = {
        "detected": True,
        "center": [280.0, 200.0],  # Right side -> nasal
        "radius": 20.0,
    }
    mac_meta = {
        "detected": True,
        "center": [180.0, 200.0],  # Left side -> temporal
        "radius": 25.0,
    }

    regions = define_anatomical_regions(
        image_shape=(h, w),
        retina_mask=retina_mask,
        retina_center=(200.0, 200.0),
        retina_radius=150.0,
        optic_disc=od_meta,
        macula=mac_meta,
    )

    expected_keys = [
        "retinal_foreground",
        "superior_retina",
        "inferior_retina",
        "nasal_retina",
        "temporal_retina",
        "posterior_pole",
        "peripheral_retina",
        "optic_disc_region",
        "macular_region",
    ]
    for k in expected_keys:
        assert k in regions, f"Missing anatomical region: {k}"
        assert regions[k].shape == (h, w)
        assert regions[k].dtype == bool

    # Superior + Inferior must exactly equal full foreground
    sup_inf_union = regions["superior_retina"] | regions["inferior_retina"]
    assert np.array_equal(sup_inf_union, regions["retinal_foreground"])

    # Superior and Inferior must be mutually exclusive
    assert not np.any(regions["superior_retina"] & regions["inferior_retina"])

    # Nasal + Temporal must exactly equal full foreground
    nas_temp_union = regions["nasal_retina"] | regions["temporal_retina"]
    assert np.array_equal(nas_temp_union, regions["retinal_foreground"])

    # Nasal and Temporal must be mutually exclusive
    assert not np.any(regions["nasal_retina"] & regions["temporal_retina"])


def test_attention_region_statistics_mass_conservation():
    """Verify statistics computation satisfies mathematical bounds."""
    h, w = 300, 300
    # Heatmap with gradient from 0.0 to 1.0
    cam = np.linspace(0.0, 1.0, h * w, dtype=np.float32).reshape((h, w))

    retina_mask = np.ones((h, w), dtype=bool)
    regions = {
        "retinal_foreground": retina_mask,
        "superior_retina": np.zeros((h, w), dtype=bool),
        "inferior_retina": np.zeros((h, w), dtype=bool),
    }
    regions["superior_retina"][:150, :] = True
    regions["inferior_retina"][150:, :] = True

    stats = compute_attention_region_statistics(
        warped_cam=cam,
        anatomical_regions=regions,
        attention_threshold=0.5,
    )

    reg_stats = stats["region_statistics"]
    assert "retinal_foreground" in reg_stats
    assert reg_stats["retinal_foreground"]["attention_fraction"] == 1.0
    assert reg_stats["retinal_foreground"]["region_area_fraction"] == 1.0

    # Mass fraction of superior + inferior must sum to 1.0
    sup_frac = reg_stats["superior_retina"]["attention_fraction"]
    inf_frac = reg_stats["inferior_retina"]["attention_fraction"]
    assert abs((sup_frac + inf_frac) - 1.0) < 1e-4

    # All values must be finite and within [0, 1]
    for r_name, r_data in reg_stats.items():
        assert 0.0 <= r_data["attention_mean"] <= 1.0
        assert 0.0 <= r_data["attention_max"] <= 1.0
        assert 0.0 <= r_data["attention_fraction"] <= 1.0
        assert 0.0 <= r_data["overlap_fraction"] <= 1.0


def test_extract_top_attention_bounding_box():
    """Verify extraction of compact attention attribution bounding box."""
    cam = np.zeros((400, 400), dtype=np.float32)
    # Put strong activation at [100:150, 200:260] (h=50, w=60)
    cam[100:150, 200:260] = 0.95

    bbox = extract_top_attention_bounding_box(cam, threshold_ratio=0.7)

    assert bbox["status"] == "localized_attention_cluster"
    assert bbox["x"] == 200
    assert bbox["y"] == 100
    assert bbox["width"] == 60
    assert bbox["height"] == 50
    assert bbox["max_attention"] == pytest.approx(0.95, rel=1e-3)
    assert bbox["area_fraction"] > 0.0


def test_extract_top_attention_zero_input():
    """Verify zero or tiny attention yields safe status."""
    cam = np.zeros((200, 200), dtype=np.float32)
    bbox = extract_top_attention_bounding_box(cam)

    assert bbox["status"] == "diffuse_or_zero_attention"
    assert bbox["bounding_box"] == [0, 0, 0, 0]
    assert bbox["area_fraction"] == 0.0


def test_anatomical_localization_determinism():
    """Verify landmark localization is 100% deterministic across two runs."""
    img = load_raw_image(REAL_IMAGE_PATH)
    run1 = localize_retinal_anatomy(img)
    run2 = localize_retinal_anatomy(img)

    assert run1["retinal_field"]["center"] == run2["retinal_field"]["center"]
    assert run1["retinal_field"]["radius"] == run2["retinal_field"]["radius"]
    assert run1["optic_disc"]["center"] == run2["optic_disc"]["center"]
    assert run1["macula"]["center"] == run2["macula"]["center"]
    assert run1["macula"]["confidence"] == run2["macula"]["confidence"]
