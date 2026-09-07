"""Image loading and preprocessing utilities for retinal fundus images."""

from pathlib import Path
from typing import Dict, Tuple, Union, Any, Optional
import numpy as np
from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None


def is_opencv_available() -> bool:
    """Check if OpenCV (cv2) is installed and available."""
    return cv2 is not None


def load_raw_image(image_path: Union[str, Path]) -> np.ndarray:
    """Load a retinal fundus image from disk as an RGB uint8 NumPy array.

    Uses OpenCV if available, falling back to PIL.

    Args:
        image_path: Path to the image file.

    Returns:
        np.ndarray: Loaded image in RGB format with shape (H, W, 3) and dtype uint8.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If image file cannot be read or decoded.
    """
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found at: {path}")

    # Primary path: OpenCV
    if cv2 is not None:
        bgr = cv2.imread(str(path))
        if bgr is not None:
            return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    # Fallback / PIL path
    try:
        with Image.open(path) as pil_img:
            return np.array(pil_img.convert("RGB"), dtype=np.uint8)
    except Exception as exc:
        raise ValueError(f"Cannot read/decode image: {path}") from exc


def crop_black_borders(image: np.ndarray, tol: int = 10) -> np.ndarray:
    """Crop uninformative black background borders around the retinal fundus circle.

    Replicates the border-cropping logic from the Diabetic Retinopathy classifier pipeline.

    Args:
        image: RGB image array.
        tol: Threshold intensity below which pixels are treated as black background.

    Returns:
        np.ndarray: Cropped RGB image array.
    """
    if image.ndim == 2:
        gray = image
    elif image.shape[2] == 3:
        if cv2 is not None:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = np.dot(image[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)
    else:
        raise ValueError(f"Unexpected image shape: {image.shape}")

    mask = gray > tol
    coords = np.argwhere(mask)

    if coords.size > 0:
        y0, x0 = coords.min(axis=0)
        y1, x1 = coords.max(axis=0) + 1
        if (y1 - y0) > 0 and (x1 - x0) > 0:
            return image[y0:y1, x0:x1]

    return image


def preprocess_image(
    image_or_path: Union[str, Path, np.ndarray],
    target_size: Tuple[int, int] = (384, 384),
    crop_borders: bool = True,
) -> np.ndarray:
    """Preprocess a retinal fundus image matching the project's EfficientNetB3 classifier pipeline.

    1. Loads image (if path provided).
    2. Crops non-retinal black borders (optional, default True).
    3. Resizes to target_size (width, height) using INTER_AREA (OpenCV) or BOX (PIL).
    4. Casts to float32 retaining [0, 255] range for EfficientNet compatibility.

    Args:
        image_or_path: Image path or loaded RGB NumPy array.
        target_size: Target (width, height) resolution (default: (384, 384)).
        crop_borders: Whether to crop black background borders.

    Returns:
        np.ndarray: Preprocessed float32 image array of shape (target_size[1], target_size[0], 3).
    """
    if isinstance(image_or_path, (str, Path)):
        image = load_raw_image(image_or_path)
    else:
        image = image_or_path.copy()

    if crop_borders:
        image = crop_black_borders(image)

    target_w, target_h = target_size

    if cv2 is not None:
        resized = cv2.resize(image, (target_w, target_h), interpolation=cv2.INTER_AREA)
    else:
        pil_img = Image.fromarray(image)
        resample = getattr(Image.Resampling, "BOX", Image.BILINEAR)
        resized = np.array(pil_img.resize((target_w, target_h), resample=resample))

    return resized.astype(np.float32)


def get_image_metadata(image_path: Union[str, Path]) -> Dict[str, Any]:
    """Inspect and extract detailed metadata from a retinal image file.

    Args:
        image_path: Path to the image file.

    Returns:
        dict: Metadata containing dimensions, channels, dtype, file size, and intensity statistics.
    """
    path = Path(image_path)
    raw_img = load_raw_image(path)
    file_size_bytes = path.stat().st_size

    return {
        "filename": path.name,
        "path": str(path.resolve()),
        "extension": path.suffix.lower(),
        "file_size_bytes": file_size_bytes,
        "height": int(raw_img.shape[0]),
        "width": int(raw_img.shape[1]),
        "channels": int(raw_img.shape[2]) if raw_img.ndim == 3 else 1,
        "dtype": str(raw_img.dtype),
        "min_pixel": float(np.min(raw_img)),
        "max_pixel": float(np.max(raw_img)),
        "mean_pixel": float(np.mean(raw_img)),
        "std_pixel": float(np.std(raw_img)),
    }
