"""Visualization tool for Retinal Evidence and Ground-Truth Inspection.

Implements Task 5:
Renders multi-panel visual inspection cards displaying:
1. Original fundus photograph
2. Optic disc candidate marker vs Ground-truth landmark
3. Fovea / Macula estimate vs Ground-truth landmark
4. Lesion ground truth masks (if available)
5. Clear clinical taxonomy banners distinguishing GROUND_TRUTH from DETECTED/ESTIMATED.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Union
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import cv2

from evidence.schema import (
    AnnotationStatus,
    EvidenceCategory,
    PointLandmark,
    SegmentationMask,
    RetinalEvidenceRecord,
)
from image_quality.io import load_raw_image


def render_evidence_inspection_card(
    image_or_path: Union[str, Path, np.ndarray],
    evidence_record: RetinalEvidenceRecord,
    output_path: Path,
    title_suffix: str = "",
) -> Path:
    """Render high-resolution inspection card contrasting landmarks and lesion channels."""
    img = load_raw_image(image_or_path) if isinstance(image_or_path, (str, Path)) else image_or_path
    h, w = img.shape[:2]

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 7), dpi=150)
    fig.patch.set_facecolor("#fafaf9")

    # Left: Raw Fundus with Landmark Overlays
    ax_left = axes[0]
    ax_left.imshow(img)
    ax_left.set_title(f"Fundus Image: {evidence_record.image_id} ({w}x{h})", fontsize=11, fontweight="bold", pad=8)

    # Plot Optic Disc
    od = evidence_record.optic_disc
    if od.is_available():
        color = "#00e5ff" if od.status == AnnotationStatus.GROUND_TRUTH else "#00b0ff"
        circ = patches.Circle((od.x, od.y), od.radius or 25.0, fill=False, edgecolor=color, linewidth=2.0)
        ax_left.add_patch(circ)
        ax_left.plot(od.x, od.y, marker="+", color=color, markersize=10, markeredgewidth=2)
        ax_left.text(
            od.x,
            od.y - (od.radius or 25.0) - 8,
            f"Optic Disc ({od.status.value})",
            color=color,
            fontsize=8,
            fontweight="bold",
            ha="center",
            bbox=dict(boxstyle="round,pad=0.2", fc="#000000", ec=color, alpha=0.7),
        )

    # Plot Fovea / Macula
    fov = evidence_record.fovea
    if fov.is_available():
        color = "#ffea00" if fov.status == AnnotationStatus.GROUND_TRUTH else "#ffd600"
        circ = patches.Circle((fov.x, fov.y), fov.radius or 30.0, fill=False, edgecolor=color, linewidth=2.0, linestyle="--")
        ax_left.add_patch(circ)
        ax_left.plot(fov.x, fov.y, marker="x", color=color, markersize=10, markeredgewidth=2)
        ax_left.text(
            fov.x,
            fov.y - (fov.radius or 30.0) - 8,
            f"Fovea ({fov.status.value})",
            color=color,
            fontsize=8,
            fontweight="bold",
            ha="center",
            bbox=dict(boxstyle="round,pad=0.2", fc="#000000", ec=color, alpha=0.7),
        )

    ax_left.axis("off")

    # Right: Structured Evidence Ledger Panel
    ax_right = axes[1]
    ax_right.axis("off")

    y = 0.95
    ax_right.text(0.02, y, "RETINAL EVIDENCE TAXONOMY LEDGER", fontsize=12, fontweight="bold", color="#1c1917")
    y -= 0.05
    ax_right.text(0.02, y, f"Spec Version: 1.0.0 | Image ID: {evidence_record.image_id}", fontsize=9, color="#78716c")
    y -= 0.06

    sections = [
        ("ANATOMICAL STRUCTURES", [
            ("Optic Disc", od.status.value, f"X={od.x:.1f}, Y={od.y:.1f} (R={od.radius:.1f})" if od.is_available() else "Unavailable", od.source),
            ("Fovea / Macula", fov.status.value, f"X={fov.x:.1f}, Y={fov.y:.1f} (R={fov.radius:.1f})" if fov.is_available() else "Unavailable", fov.source),
            ("Retinal Vessels", evidence_record.vessels.status.value, "Drive/STARE required" if evidence_record.vessels.status == AnnotationStatus.NOT_AVAILABLE else "Available", evidence_record.vessels.source),
        ]),
        ("LESION EVIDENCE CHANNELS", [
            ("Microaneurysms", evidence_record.microaneurysms.status.value, "Native patch crop needed", evidence_record.microaneurysms.source),
            ("Hard/Soft Exudates", evidence_record.exudates.status.value, "Pixel mask supported", evidence_record.exudates.source),
            ("Hemorrhages", evidence_record.hemorrhages.status.value, "Pixel mask supported", evidence_record.hemorrhages.source),
            ("Neovascularization", evidence_record.neovascularization.status.value, "Absent in IDRiD", "Not available in benchmark"),
        ]),
    ]

    for sec_title, items in sections:
        ax_right.text(0.02, y, sec_title, fontsize=10, fontweight="bold", color="#0f766e")
        y -= 0.04
        for name, status, details, src in items:
            badge_color = "#15803d" if status == "GROUND_TRUTH" else ("#0369a1" if status == "DETECTED" else ("#b45309" if status == "ESTIMATED" else "#991b1b"))
            ax_right.text(0.05, y, f"• {name}:", fontsize=9, fontweight="bold", color="#292524")
            ax_right.text(0.40, y, f"[{status}]", fontsize=8.5, fontweight="bold", color=badge_color)
            ax_right.text(0.60, y, f"{details}", fontsize=8.5, color="#57534e")
            y -= 0.035
        y -= 0.02

    # Scientific honesty note
    y -= 0.02
    ax_right.text(
        0.02,
        y,
        "STRICT PROVENANCE INVARIANT:\n"
        "Ground truth certified by clinical benchmark is never conflated with\n"
        "algorithmic detections or heuristic estimates.",
        fontsize=8.5,
        fontstyle="italic",
        color="#78716c",
        bbox=dict(boxstyle="round,pad=0.5", fc="#f5f5f4", ec="#e7e5e4"),
    )

    plt.tight_layout()
    plt.savefig(out_file, bbox_inches="tight", dpi=150)
    plt.close(fig)

    return out_file
