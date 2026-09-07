"""Anatomical retinal localization and context region mapping module.

Localizes physiological fundus landmarks (retinal boundary, optic disc
candidate, and approximate macular/foveal region) using transparent image
geometry and photometric heuristics. Partitions the retina into anatomical
context regions and computes Grad-CAM feature attribution distribution.

STRICT CLINICAL SAFETY NOTICE:
Landmark localization and context regions provide geometric orientation for
model feature attribution. They are NOT lesion detectors, do NOT segment
pathology, and do NOT constitute clinical diagnosis.
"""

from typing import Dict, Any, Optional, Tuple
import cv2
import numpy as np

from image_quality.field_of_view import (
    detect_retinal_field,
    locate_optic_disc_candidate,
)


def estimate_macular_region(
    image: Any,
    retina_mask: Any,
    optic_disc: Dict[str, Any],
    retina_center: Tuple[float, float],
    retina_radius: float,
) -> Dict[str, Any]:
    """Estimate approximate foveal / macular region using retinal geometry.

    In standard retinal fundus photography:
    - The optic disc lies on the nasal side.
    - The fovea/macula is displaced temporally from the optic disc by ~2.5
      disc diameters (approx. 5-6 disc radii) and slightly inferior.
    - In macula-centered photos, this places the macula near geometric center.
    - Photometrically, the foveal avascular zone (FAZ) exhibits localized dark
      absorption (luminance/green channel minimum).

    Args:
        image: RGB image array (H, W, 3).
        retina_mask: 2D boolean mask of retinal foreground.
        optic_disc: Dictionary returned by locate_optic_disc_candidate.
        retina_center: (cx, cy) of the retinal foreground circle.
        retina_radius: Estimated radius of retinal circle in pixels.

    Returns:
        dict: Macular candidate metadata including center, radius, confidence,
              method, and status.
    """
    h_img, w_img = image.shape[:2]

    # If optic disc is not detected or unreliable, fallback to geometric center
    has_od = optic_disc.get("detected", False)
    od_center = optic_disc.get("center")
    if not has_od or od_center is None:
        if np.any(retina_mask):
            cx, cy = retina_center
            nom_r = max(15.0, retina_radius * 0.10)
            return {
                "detected": True,
                "center": [round(float(cx), 1), round(float(cy), 1)],
                "center_x": round(float(cx), 1),
                "center_y": round(float(cy), 1),
                "radius": round(float(nom_r), 1),
                "confidence": 0.35,
                "method": "geometric_center_default_fallback",
                "status": "low_confidence",
                "is_reliable": False,
                "notes": (
                    "Optic disc unavailable; defaulted to retinal center."
                ),
            }
        return {
            "detected": False,
            "center": None,
            "center_x": None,
            "center_y": None,
            "radius": None,
            "confidence": 0.0,
            "method": "geometric_center_default_fallback",
            "status": "not_reliably_localized",
            "is_reliable": False,
            "notes": "Retinal foreground could not be determined.",
        }

    od_cx, od_cy = od_center
    od_r = float(optic_disc.get("radius") or (retina_radius * 0.07))
    ret_cx, ret_cy = retina_center

    # Direction vector from optic disc towards retinal center
    dx = ret_cx - od_cx
    dy = ret_cy - od_cy
    dist_od_center = float(np.hypot(dx, dy))

    if dist_od_center > 0.0:
        dir_x = dx / dist_od_center
        dir_y = dy / dist_od_center
    else:
        # Default temporal direction towards image right
        dir_x, dir_y = 1.0, 0.0

    # Expected anatomical distance: ~5.5 disc radii (~2.5 disc diameters)
    expected_dist = min(5.5 * od_r, dist_od_center * 1.15)
    nom_x = od_cx + dir_x * expected_dist
    nom_y = od_cy + dir_y * expected_dist

    # Refine within localized search window using green channel minimum
    search_r = int(round(max(15.0, od_r * 0.85)))
    x0 = max(0, int(round(nom_x - search_r)))
    x1 = min(w_img, int(round(nom_x + search_r + 1)))
    y0 = max(0, int(round(nom_y - search_r)))
    y1 = min(h_img, int(round(nom_y + search_r + 1)))

    refined_x, refined_y = nom_x, nom_y
    photometric_found = False

    if x1 > x0 and y1 > y0:
        green = image[:, :, 1].astype(np.float32)
        blur_green = cv2.GaussianBlur(green, (11, 11), 0)
        sub_patch = blur_green[y0:y1, x0:x1]
        sub_mask = retina_mask[y0:y1, x0:x1]

        valid_patch = np.where(sub_mask, sub_patch, np.inf)
        if np.any(np.isfinite(valid_patch)):
            min_idx = np.unravel_index(
                np.argmin(valid_patch), valid_patch.shape
            )
            refined_y = float(y0 + min_idx[0])
            refined_x = float(x0 + min_idx[1])
            photometric_found = True

    # Ensure estimated point lies within retinal foreground
    ix = int(np.clip(round(refined_x), 0, w_img - 1))
    iy = int(np.clip(round(refined_y), 0, h_img - 1))
    in_retina = bool(retina_mask[iy, ix])

    macula_r = max(15.0, od_r * 1.2)
    od_conf = float(optic_disc.get("confidence", 0.5))

    if in_retina and photometric_found:
        conf = round(float(min(0.90, 0.5 * od_conf + 0.35)), 2)
        status = "high_confidence" if conf >= 0.70 else "moderate_confidence"
    elif in_retina:
        conf = round(float(min(0.60, 0.4 * od_conf + 0.20)), 2)
        status = "moderate_confidence"
    else:
        conf = 0.25
        status = "low_confidence"

    return {
        "detected": True,
        "center": [round(refined_x, 1), round(refined_y, 1)],
        "center_x": round(refined_x, 1),
        "center_y": round(refined_y, 1),
        "radius": round(float(macula_r), 1),
        "confidence": conf,
        "method": "geometric_displacement_and_photometric_minimum",
        "status": status,
        "is_reliable": bool(conf >= 0.65),
        "notes": (
            "Macular candidate estimated via temporal displacement from optic "
            "disc and local photometric absorption minimum."
        ),
    }


def localize_retinal_anatomy(
    image: Any,
    tol: int = 15,
) -> Dict[str, Any]:
    """Localize retinal field, optic disc, and macular candidate landmarks.

    Args:
        image: RGB image array of shape (H, W, 3).
        tol: Grayscale intensity threshold for background separation.

    Returns:
        dict: Complete anatomical localization data structure.
    """
    img_rgb = np.asarray(image, dtype=np.uint8)
    h_img, w_img = img_rgb.shape[:2]

    # 1. Retinal field foreground segmentation
    field_data = detect_retinal_field(img_rgb, tol=tol)
    retina_mask = field_data["mask"]
    bx, by, bw, bh = field_data["bounding_box"]
    ret_cx = float(bx + bw / 2.0)
    ret_cy = float(by + bh / 2.0)
    ret_r = float(min(bw, bh) / 2.0)

    # 2. Optic disc candidate localization
    od_meta = locate_optic_disc_candidate(img_rgb, retina_mask)

    # 3. Approximate macular region estimation
    macula_meta = estimate_macular_region(
        image=img_rgb,
        retina_mask=retina_mask,
        optic_disc=od_meta,
        retina_center=(ret_cx, ret_cy),
        retina_radius=ret_r,
    )

    return {
        "image_dimensions": [h_img, w_img],
        "retinal_field": {
            "bounding_box": [bx, by, bw, bh],
            "center": [round(ret_cx, 1), round(ret_cy, 1)],
            "center_x": round(ret_cx, 1),
            "center_y": round(ret_cy, 1),
            "radius": round(ret_r, 1),
            "area_pixels": int(field_data["retinal_area_pixels"]),
            "coverage_pct": float(field_data["coverage_pct"]),
            "aspect_ratio": float(field_data["aspect_ratio"]),
        },
        "optic_disc": od_meta,
        "macula": macula_meta,
        "retina_mask": retina_mask,
    }


def define_anatomical_regions(
    image_shape: Tuple[int, int],
    retina_mask: Any,
    retina_center: Tuple[float, float],
    retina_radius: float,
    optic_disc: Dict[str, Any],
    macula: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate 2D binary masks for standard retinal context regions.

    Coordinate Conventions:
    - superior_retina: pixels where y < retina_center_y within retina_mask
    - inferior_retina: pixels where y >= retina_center_y within retina_mask
    - nasal_retina: hemisphere containing the optic disc candidate
    - temporal_retina: hemisphere opposite to optic disc (containing macula)
    - posterior_pole: central circular zone (radius <= 0.55 * retina_radius)
    - peripheral_retina: outer annular zone (radius > 0.75 * retina_radius)
    - optic_disc_region: circular zone around optic disc candidate
    - macular_region: circular zone around macular candidate

    Args:
        image_shape: (height, width) of the full canvas.
        retina_mask: 2D boolean mask of retinal foreground.
        retina_center: (cx, cy) center of retinal circle.
        retina_radius: Radius of retinal circle.
        optic_disc: Optic disc localization metadata.
        macula: Macula localization metadata.

    Returns:
        dict: Mapping of region name to 2D boolean numpy array mask.
    """
    h_img, w_img = image_shape[:2]
    y_grid, x_grid = np.ogrid[:h_img, :w_img]

    ret_cx, ret_cy = retina_center
    dist_from_center = np.hypot(x_grid - ret_cx, y_grid - ret_cy)

    # 1. Whole retinal foreground
    fg_mask = retina_mask.copy()

    # 2. Superior and Inferior hemispheres
    superior_mask = fg_mask & (y_grid < ret_cy)
    inferior_mask = fg_mask & (y_grid >= ret_cy)

    # 3. Nasal and Temporal hemispheres
    has_od = optic_disc.get("detected", False)
    od_center = optic_disc.get("center")
    if has_od and od_center is not None:
        od_cx = od_center[0]
        if od_cx >= ret_cx:
            # Optic disc on right side -> right eye (OD) -> right is nasal
            nasal_mask = fg_mask & (x_grid >= ret_cx)
            temporal_mask = fg_mask & (x_grid < ret_cx)
        else:
            # Optic disc on left side -> left eye (OS) -> left is nasal
            nasal_mask = fg_mask & (x_grid < ret_cx)
            temporal_mask = fg_mask & (x_grid >= ret_cx)
    else:
        # Default partition if OD orientation unknown
        nasal_mask = fg_mask & (x_grid >= ret_cx)
        temporal_mask = fg_mask & (x_grid < ret_cx)

    # 4. Depth regions: Posterior Pole and Periphery
    posterior_pole_mask = (
        fg_mask & (dist_from_center <= (0.55 * retina_radius))
    )
    peripheral_mask = fg_mask & (dist_from_center > (0.75 * retina_radius))

    # 5. Optic disc landmark region
    od_region_mask = np.zeros((h_img, w_img), dtype=bool)
    if has_od and od_center is not None:
        od_x, od_y = od_center
        od_r = float(optic_disc.get("radius") or (retina_radius * 0.08))
        d_od = np.hypot(x_grid - od_x, y_grid - od_y)
        od_region_mask = fg_mask & (d_od <= (1.5 * od_r))

    # 6. Macular landmark region
    macular_region_mask = np.zeros((h_img, w_img), dtype=bool)
    has_mac = macula.get("detected", False)
    mac_center = macula.get("center")
    if has_mac and mac_center is not None:
        mac_x, mac_y = mac_center
        mac_r = float(macula.get("radius") or (retina_radius * 0.10))
        d_mac = np.hypot(x_grid - mac_x, y_grid - mac_y)
        macular_region_mask = fg_mask & (d_mac <= (1.5 * mac_r))

    return {
        "retinal_foreground": fg_mask,
        "superior_retina": superior_mask,
        "inferior_retina": inferior_mask,
        "nasal_retina": nasal_mask,
        "temporal_retina": temporal_mask,
        "posterior_pole": posterior_pole_mask,
        "peripheral_retina": peripheral_mask,
        "optic_disc_region": od_region_mask,
        "macular_region": macular_region_mask,
    }


def compute_attention_region_statistics(
    warped_cam: Any,
    anatomical_regions: Dict[str, Any],
    attention_threshold: float = 0.5,
) -> Dict[str, Any]:
    """Compute Grad-CAM attention mass, mean, max, and overlap by region.

    Args:
        warped_cam: 2D float32 array in [0.0, 1.0] matching image canvas.
        anatomical_regions: Dictionary of masks from define_anatomical_regions.
        attention_threshold: Threshold above which pixels count as high att.

    Returns:
        dict: Per-region statistical summary dictionary.
    """
    fg_mask = anatomical_regions.get("retinal_foreground")
    if fg_mask is None or not np.any(fg_mask):
        fg_mask = np.ones_like(warped_cam, dtype=bool)

    total_retinal_pixels = int(np.sum(fg_mask))
    total_retinal_mass = float(np.sum(warped_cam[fg_mask]))
    high_att_mask = (warped_cam >= attention_threshold) & fg_mask
    total_high_att_pixels = int(np.sum(high_att_mask))

    region_stats = {}

    for name, mask in anatomical_regions.items():
        region_pixels = int(np.sum(mask))
        if region_pixels > 0:
            reg_cam = warped_cam[mask]
            att_mean = float(np.mean(reg_cam))
            att_max = float(np.max(reg_cam))
            att_mass = float(np.sum(reg_cam))
            area_frac = float(region_pixels / total_retinal_pixels)
        else:
            att_mean = 0.0
            att_max = 0.0
            att_mass = 0.0
            area_frac = 0.0

        if total_retinal_mass > 0.0:
            mass_frac = float(att_mass / total_retinal_mass)
        else:
            mass_frac = 0.0

        if total_high_att_pixels > 0:
            reg_high = (warped_cam >= attention_threshold) & mask
            reg_high_pixels = int(np.sum(reg_high))
            overlap_frac = float(reg_high_pixels / total_high_att_pixels)
        else:
            overlap_frac = 0.0

        region_stats[name] = {
            "attention_mean": round(att_mean, 6),
            "attention_max": round(att_max, 6),
            "attention_mass": round(att_mass, 4),
            "attention_fraction": round(min(1.0, max(0.0, mass_frac)), 4),
            "overlap_fraction": round(min(1.0, max(0.0, overlap_frac)), 4),
            "region_area_fraction": round(min(1.0, max(0.0, area_frac)), 4),
            "pixel_count": region_pixels,
        }

    return {
        "attention_threshold": float(attention_threshold),
        "total_retinal_attention_mass": round(total_retinal_mass, 4),
        "total_high_attention_pixels": total_high_att_pixels,
        "region_statistics": region_stats,
    }


def extract_top_attention_bounding_box(
    warped_cam: Any,
    retinal_mask: Optional[Any] = None,
    threshold_ratio: float = 0.65,
) -> Dict[str, Any]:
    """Extract compact bounding box enclosing peak Grad-CAM cluster.

    IMPORTANT: This is an attention attribution bounding box only.
    It does NOT segment or identify a biological lesion.

    Args:
        warped_cam: 2D float32 Grad-CAM heatmap in [0.0, 1.0].
        retinal_mask: Optional boolean mask restricting attention search.
        threshold_ratio: Activation fraction relative to max (default: 0.65).

    Returns:
        dict: Bounding box [x, y, w, h], area fraction, mean and max attention.
    """
    cam = np.asarray(warped_cam, dtype=np.float32)
    if retinal_mask is not None:
        cam_masked = np.where(retinal_mask, cam, 0.0)
    else:
        cam_masked = cam

    max_val = float(np.max(cam_masked))
    if max_val <= 1e-4:
        return {
            "bounding_box": [0, 0, 0, 0],
            "x": 0,
            "y": 0,
            "width": 0,
            "height": 0,
            "area_fraction": 0.0,
            "mean_attention": 0.0,
            "max_attention": 0.0,
            "status": "diffuse_or_zero_attention",
        }

    thresh_val = max(0.30, max_val * threshold_ratio)
    binary_high = (cam_masked >= thresh_val).astype(np.uint8)

    num_labels, labels, stats, centroids = (
        cv2.connectedComponentsWithStats(binary_high)
    )
    if num_labels <= 1:
        return {
            "bounding_box": [0, 0, 0, 0],
            "x": 0,
            "y": 0,
            "width": 0,
            "height": 0,
            "area_fraction": 0.0,
            "mean_attention": 0.0,
            "max_attention": 0.0,
            "status": "diffuse_or_zero_attention",
        }

    # Select largest contiguous high-attention component
    largest_idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    bx = int(stats[largest_idx, cv2.CC_STAT_LEFT])
    by = int(stats[largest_idx, cv2.CC_STAT_TOP])
    bw = int(stats[largest_idx, cv2.CC_STAT_WIDTH])
    bh = int(stats[largest_idx, cv2.CC_STAT_HEIGHT])

    comp_mask = (labels == largest_idx)
    mean_att = float(np.mean(cam[comp_mask]))
    max_att = float(np.max(cam[comp_mask]))

    h_img, w_img = cam.shape[:2]
    total_pixels = h_img * w_img
    area_frac = float((bw * bh) / total_pixels) if total_pixels > 0 else 0.0

    return {
        "bounding_box": [bx, by, bw, bh],
        "x": bx,
        "y": by,
        "width": bw,
        "height": bh,
        "area_fraction": round(area_frac, 4),
        "mean_attention": round(mean_att, 6),
        "max_attention": round(max_att, 6),
        "status": "localized_attention_cluster",
    }
