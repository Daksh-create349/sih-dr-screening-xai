"""Automated tests for retinal image loading, preprocessing, and integrity verification."""

from pathlib import Path
import pytest
import numpy as np

from image_quality.io import (
    load_raw_image,
    preprocess_image,
    crop_black_borders,
    get_image_metadata,
)

# Root directory for real retinal images
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "real_retinal_images"


def get_real_image_paths():
    """Retrieve all real retinal fundus images in the dataset folder."""
    assert DATA_DIR.exists(), f"Data directory does not exist: {DATA_DIR}"
    valid_exts = {".png", ".jpg", ".jpeg"}
    images = sorted([p for p in DATA_DIR.iterdir() if p.suffix.lower() in valid_exts])
    return images


def test_real_retinal_dataset_exists_and_nonempty():
    """Rule 1 & 2: Verify real retinal fundus images exist and are not empty."""
    images = get_real_image_paths()
    assert len(images) > 0, f"No real retinal images found in {DATA_DIR}"
    assert len(images) >= 5, f"Expected representative sample of real retinal images, found {len(images)}"


@pytest.mark.parametrize(
    "image_path",
    get_real_image_paths(),
    ids=lambda p: p.name,
)
def test_load_raw_image_success(image_path: Path):
    """Verify load_raw_image correctly loads real image as RGB uint8 array."""
    img = load_raw_image(image_path)
    assert isinstance(img, np.ndarray), f"Expected np.ndarray, got {type(img)}"
    assert img.ndim == 3, f"Image {image_path.name} must have 3 dimensions, got {img.ndim}"
    assert img.shape[2] == 3, f"Image {image_path.name} must have 3 channels (RGB), got {img.shape[2]}"
    assert img.dtype == np.uint8, f"Image {image_path.name} dtype must be uint8, got {img.dtype}"
    assert img.shape[0] > 100 and img.shape[1] > 100, f"Image {image_path.name} resolution too low: {img.shape}"


@pytest.mark.parametrize(
    "image_path",
    get_real_image_paths(),
    ids=lambda p: p.name,
)
def test_real_image_pixel_distribution(image_path: Path):
    """Verify real retinal fundus image has valid dynamic range and variance (not blank/mock)."""
    img = load_raw_image(image_path)
    min_val = np.min(img)
    max_val = np.max(img)
    std_val = np.std(img)

    assert min_val >= 0, f"Pixel values cannot be negative: {min_val}"
    assert max_val <= 255, f"Pixel values cannot exceed 255: {max_val}"
    assert max_val > 50, f"Image {image_path.name} is too dark or empty (max={max_val})"
    assert std_val > 15.0, f"Image {image_path.name} has near-zero variance (std={std_val:.2f})"

    # Retinal images typically have distinct red channel dominance
    r_mean = np.mean(img[:, :, 0])
    b_mean = np.mean(img[:, :, 2])
    assert r_mean > b_mean, f"Retinal image {image_path.name} expected red channel mean ({r_mean:.1f}) > blue mean ({b_mean:.1f})"


@pytest.mark.parametrize(
    "image_path",
    get_real_image_paths(),
    ids=lambda p: p.name,
)
def test_preprocess_image_pipeline(image_path: Path):
    """Verify preprocessing matches the project's EfficientNetB3 pipeline: 384x384 float32."""
    processed = preprocess_image(image_path, target_size=(384, 384), crop_borders=True)

    assert isinstance(processed, np.ndarray)
    assert processed.shape == (384, 384, 3), f"Expected shape (384, 384, 3), got {processed.shape}"
    assert processed.dtype == np.float32, f"Expected dtype float32, got {processed.dtype}"
    assert np.min(processed) >= 0.0, f"Processed pixels must be >= 0.0, got {np.min(processed)}"
    assert np.max(processed) <= 255.0, f"Processed pixels must be <= 255.0, got {np.max(processed)}"


@pytest.mark.parametrize(
    "image_path",
    get_real_image_paths(),
    ids=lambda p: p.name,
)
def test_crop_black_borders(image_path: Path):
    """Verify border cropping maintains valid non-zero content and 3 channels."""
    img = load_raw_image(image_path)
    cropped = crop_black_borders(img, tol=10)

    assert isinstance(cropped, np.ndarray)
    assert cropped.ndim == 3 and cropped.shape[2] == 3
    assert cropped.shape[0] <= img.shape[0]
    assert cropped.shape[1] <= img.shape[1]
    assert cropped.size > 0


@pytest.mark.parametrize(
    "image_path",
    get_real_image_paths(),
    ids=lambda p: p.name,
)
def test_metadata_extraction(image_path: Path):
    """Verify get_image_metadata returns complete and correct structural attributes."""
    meta = get_image_metadata(image_path)

    expected_keys = {
        "filename",
        "path",
        "extension",
        "file_size_bytes",
        "height",
        "width",
        "channels",
        "dtype",
        "min_pixel",
        "max_pixel",
        "mean_pixel",
        "std_pixel",
    }
    assert expected_keys.issubset(meta.keys())
    assert meta["channels"] == 3
    assert meta["file_size_bytes"] > 0
    assert meta["height"] > 0 and meta["width"] > 0
    assert meta["dtype"] == "uint8"


def test_load_nonexistent_image_raises():
    """Verify proper exception on missing file."""
    with pytest.raises(FileNotFoundError):
        load_raw_image(DATA_DIR / "non_existent_retina_image_9999.png")


def test_load_corrupted_file_raises(tmp_path: Path):
    """Verify proper exception on corrupted or non-image file."""
    fake_file = tmp_path / "corrupted.png"
    fake_file.write_text("NOT_AN_IMAGE_CONTENT_HERE")
    with pytest.raises(ValueError):
        load_raw_image(fake_file)
