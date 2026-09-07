"""Classifier input preprocessing pipeline.

Matches the exact preprocessing used during EfficientNetB3 model training
in the project notebook (Cell 8 & Cell 39):
1. Loads RGB image array or file path.
2. Crops non-retinal black borders (grayscale threshold > 10, bounding box).
3. Resizes to (384, 384) with OpenCV INTER_AREA interpolation.
4. Casts to float32 retaining the [0, 255] intensity range (internal norm).
5. Prepares 4D batch tensor of shape (batch_size, 384, 384, 3).
"""

from pathlib import Path
from typing import Union, Tuple, Any, Sequence
import cv2
import numpy as np

from image_quality.io import load_raw_image


TARGET_IMAGE_SIZE: Tuple[int, int] = (384, 384)


def get_retinal_crop_box(
    image: Any,
    tol: int = 10,
) -> Tuple[int, int, int, int]:
    """Return bounding box (x, y, w, h) for retinal content above threshold.

    Args:
        image: RGB uint8 or float32 image array.
        tol: Grayscale intensity threshold for background separation.

    Returns:
        tuple[int, int, int, int]: (x, y, width, height) bounding box.
    """
    img_uint8 = np.clip(image, 0, 255).astype(np.uint8)
    gray = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2GRAY)
    mask = np.where(gray > tol, 255, 0).astype(np.uint8)
    coords = cv2.findNonZero(mask)

    if coords is not None:
        x_coord, y_coord, box_w, box_h = cv2.boundingRect(coords)
        if box_w > 0 and box_h > 0:
            return int(x_coord), int(y_coord), int(box_w), int(box_h)
    h_img, w_img = image.shape[:2]
    return 0, 0, int(w_img), int(h_img)


def crop_retinal_borders(image: Any, tol: int = 10) -> Any:
    """Crop uninformative black background borders matching notebook Cell 8.

    Args:
        image: RGB uint8 or float32 image array.
        tol: Grayscale intensity threshold for background separation.

    Returns:
        np.ndarray: Cropped image.
    """
    x_c, y_c, box_w, box_h = get_retinal_crop_box(image, tol=tol)
    return image[y_c:y_c + box_h, x_c:x_c + box_w]


def preprocess_classifier_image(
    image_or_path: Union[str, Path, Any],
    target_size: Tuple[int, int] = TARGET_IMAGE_SIZE,
    crop_borders: bool = True,
) -> np.ndarray:
    """Prepare a retinal fundus image for EfficientNetB3 inference.

    Args:
        image_or_path: File path or RGB NumPy array.
        target_size: Desired (width, height) resolution (default: (384, 384)).
        crop_borders: Whether to crop black background borders.

    Returns:
        np.ndarray: 3D float32 array in [0.0, 255.0].
    """
    if isinstance(image_or_path, (str, Path)):
        image = load_raw_image(image_or_path)
    elif isinstance(image_or_path, np.ndarray):
        image = image_or_path.copy()
    else:
        raise TypeError(
            f"Expected file path or np.ndarray, got {type(image_or_path)}"
        )

    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(
            f"Expected 3-channel RGB image, got shape {image.shape}"
        )

    if crop_borders:
        image = crop_retinal_borders(image)

    target_w, target_h = target_size
    resized = cv2.resize(
        image, (target_w, target_h), interpolation=cv2.INTER_AREA
    )

    # Values in [0, 255] float32 - DO NOT rescale by 1/255.0
    return resized.astype(np.float32)


def prepare_input_tensor(
    image_or_path: Union[str, Path, Any],
    target_size: Tuple[int, int] = TARGET_IMAGE_SIZE,
    crop_borders: bool = True,
) -> np.ndarray:
    """Preprocess single image and expand batch dimension to (1, H, W, C).

    Args:
        image_or_path: File path or RGB NumPy array.
        target_size: Resolution (width, height).
        crop_borders: Whether to crop black background borders.

    Returns:
        np.ndarray: 4D float32 array of shape (1, 384, 384, 3).
    """
    img_3d = preprocess_classifier_image(
        image_or_path,
        target_size=target_size,
        crop_borders=crop_borders,
    )
    return np.expand_dims(img_3d, axis=0)


def prepare_batch_tensors(
    images_or_paths: Sequence[Union[str, Path, np.ndarray]],
    target_size: Tuple[int, int] = TARGET_IMAGE_SIZE,
    crop_borders: bool = True,
) -> np.ndarray:
    """Preprocess a list of images or paths into a 4D batch tensor.

    Args:
        images_or_paths: List of file paths or RGB NumPy arrays.
        target_size: Resolution (width, height).
        crop_borders: Whether to crop black background borders.

    Returns:
        np.ndarray: 4D float32 array of shape (N, 384, 384, 3).
    """
    if not images_or_paths:
        raise ValueError("Cannot prepare batch tensor from empty list.")

    processed = [
        preprocess_classifier_image(
            item,
            target_size=target_size,
            crop_borders=crop_borders,
        )
        for item in images_or_paths
    ]
    return np.stack(processed, axis=0)
