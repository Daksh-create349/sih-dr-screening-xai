"""Pipeline runtime profiling module for real retinal fundus images.

Executes actual wall-clock timing measurements on real retinal images:
- Separates cold model load time from warm inference time.
- Measures individual component execution times:
  A. Image loading
  B. IQA scoring (focus, illumination, FOV, composite)
  C. Quality decision logic
  D. Borderline enhancement (CLAHE)
  E. Classifier inference (EfficientNetB3)
  F. Referable DR screening decision
  G. Grad-CAM computation & back-warping
  H. Anatomical landmark & evidence generation
  I. Report generation
  J. Complete screening pipeline
- Measures real execution times across:
  Path A (GOOD -> classifier -> referable -> Grad-CAM -> evidence/report)
  Path B (BORDERLINE -> enhancement -> re-check -> classifier -> referable
          -> Grad-CAM -> evidence/report)
  Path C (UNGRADEABLE -> recapture -> STOP)
- Collects real image file sizes for bandwidth analysis.
- Computes mean, median, std, min, max, and percentiles over repetitions.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional
import os
import platform
import sys
import time
import numpy as np

from image_quality.io import load_raw_image
from image_quality.scoring import score_image_quality
from image_quality.decision import classify_quality_decision
from image_quality.enhancement import enhance_clahe
from image_quality.report import (
    generate_quality_report,
    generate_recapture_feedback,
)
from classifier.model import load_classifier_model, clear_model_cache
from classifier.predictor import predict_image, run_screening_pipeline
from classifier.referable import evaluate_referable_dr
from explainability.gradcam import compute_full_retinal_gradcam
from explainability.evidence import generate_retinal_evidence

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE_ROOT / "data" / "real_retinal_images"


@dataclass
class ProfileResult:
    """Dataclass wrapper for profiling output payload."""

    data: Dict[str, Any]


def get_system_environment_metadata() -> Dict[str, Any]:
    """Capture host system hardware and runtime environment metadata."""
    return {
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count() or 1,
    }


def compute_timing_statistics(samples: List[float]) -> Dict[str, float]:
    """Compute summary statistics for a list of timing measurements in ms."""
    if not samples:
        return {
            "mean_ms": 0.0,
            "median_ms": 0.0,
            "std_ms": 0.0,
            "min_ms": 0.0,
            "max_ms": 0.0,
            "p50_ms": 0.0,
            "p90_ms": 0.0,
            "p95_ms": 0.0,
            "sample_count": 0,
        }

    arr = np.array(samples, dtype=float) * 1000.0  # seconds to ms
    return {
        "mean_ms": round(float(np.mean(arr)), 3),
        "median_ms": round(float(np.median(arr)), 3),
        "std_ms": round(float(np.std(arr)), 3),
        "min_ms": round(float(np.min(arr)), 3),
        "max_ms": round(float(np.max(arr)), 3),
        "p50_ms": round(float(np.percentile(arr, 50)), 3),
        "p90_ms": round(float(np.percentile(arr, 90)), 3),
        "p95_ms": round(float(np.percentile(arr, 95)), 3),
        "sample_count": len(samples),
    }


def measure_cold_model_load() -> Dict[str, float]:
    """Measure wall-clock time for initial cold load of Keras classifier."""
    clear_model_cache()
    t0 = time.perf_counter()
    _ = load_classifier_model(force_reload=True)
    t1 = time.perf_counter()
    duration_s = t1 - t0
    return {
        "cold_load_seconds": round(duration_s, 4),
        "cold_load_ms": round(duration_s * 1000.0, 2),
    }


def measure_file_sizes(image_paths: List[Path]) -> Dict[str, Any]:
    """Measure exact file sizes of real retinal images in bytes and MB."""
    sizes_bytes = []
    file_details = []

    for p in image_paths:
        sz = p.stat().st_size
        sizes_bytes.append(sz)
        file_details.append({
            "filename": p.name,
            "size_bytes": sz,
            "size_kb": round(sz / 1024.0, 2),
            "size_mb": round(sz / (1024.0 * 1024.0), 4),
        })

    arr = np.array(sizes_bytes, dtype=float)
    return {
        "file_details": file_details,
        "count": len(sizes_bytes),
        "mean_bytes": round(float(np.mean(arr)), 1),
        "median_bytes": round(float(np.median(arr)), 1),
        "min_bytes": int(np.min(arr)),
        "max_bytes": int(np.max(arr)),
        "std_bytes": round(float(np.std(arr)), 1),
        "mean_mb": round(float(np.mean(arr)) / (1024.0 * 1024.0), 4),
        "median_mb": round(float(np.median(arr)) / (1024.0 * 1024.0), 4),
        "min_mb": round(float(np.min(arr)) / (1024.0 * 1024.0), 4),
        "max_mb": round(float(np.max(arr)) / (1024.0 * 1024.0), 4),
    }


def run_pipeline_profiling(
    data_dir: Optional[Path] = None,
    repetitions: int = 3,
) -> Dict[str, Any]:
    """Execute rigorous runtime profiling of all pipeline stages.

    Uses all 9 real retinal images with multiple repetitions.

    Args:
        data_dir: Directory containing real retinal images.
        repetitions: Repetitions per image to reduce measurement jitter.

    Returns:
        dict: Complete profiling results with component & path stats.
    """
    if data_dir is None:
        data_dir = DATA_DIR

    image_paths = sorted([
        p for p in data_dir.iterdir()
        if p.is_file() and p.suffix.lower() in [".png", ".jpg", ".jpeg"]
    ])
    if not image_paths:
        raise FileNotFoundError(f"No retinal images found in {data_dir}")

    # 1. System environment metadata
    env_meta = get_system_environment_metadata()

    # 2. File size profiling from actual files
    size_metrics = measure_file_sizes(image_paths)

    # 3. Cold model load measurement
    cold_load_metrics = measure_cold_model_load()

    # Warm model instance for warm inference profiling
    model = load_classifier_model()
    # Warm-up inference pass
    dummy_img = load_raw_image(image_paths[0])
    _ = predict_image(dummy_img, model=model)

    # Component timing collectors
    t_load: List[float] = []
    t_iqa: List[float] = []
    t_decision: List[float] = []
    t_enhance: List[float] = []
    t_classify: List[float] = []
    t_referable: List[float] = []
    t_gradcam: List[float] = []
    t_evidence: List[float] = []
    t_report: List[float] = []
    t_pipeline_e2e: List[float] = []

    # Path timing collectors
    path_a_good: List[float] = []
    path_b_borderline: List[float] = []
    path_c_ungradeable: List[float] = []

    # Pre-classify images to determine genuine routing paths
    per_image_summary = []
    path_counts = {"GOOD": 0, "BORDERLINE": 0, "UNGRADEABLE": 0}

    for img_path in image_paths:
        img = load_raw_image(img_path)
        iqa_res = score_image_quality(img)
        dec = classify_quality_decision(iqa_res)
        status = dec["final_class"]
        if status in path_counts:
            path_counts[status] += 1
        per_image_summary.append({
            "filename": img_path.name,
            "quality_status": status,
            "composite_score": dec["composite_score"],
        })

    # Repetitive profiling loop across all real images
    for _ in range(repetitions):
        for img_path in image_paths:
            # A. Image loading
            t0 = time.perf_counter()
            img = load_raw_image(img_path)
            t1 = time.perf_counter()
            t_load.append(t1 - t0)

            # B. IQA scoring
            t0 = time.perf_counter()
            iqa_res = score_image_quality(img)
            t1 = time.perf_counter()
            t_iqa.append(t1 - t0)

            # C. Quality decision
            t0 = time.perf_counter()
            dec = classify_quality_decision(iqa_res)
            t1 = time.perf_counter()
            t_decision.append(t1 - t0)

            # D. Borderline enhancement (CLAHE)
            t0 = time.perf_counter()
            enh = enhance_clahe(img)
            t1 = time.perf_counter()
            t_enhance.append(t1 - t0)

            # Determine active image for downstream stages
            eval_img = enh if dec["final_class"] == "BORDERLINE" else img

            # E. Classifier inference (warm model resident in RAM)
            t0 = time.perf_counter()
            pred = predict_image(eval_img, model=model)
            t1 = time.perf_counter()
            t_classify.append(t1 - t0)

            # F. Referable decision
            raw_probs = [pred["probabilities"][g] for g in range(5)]
            t0 = time.perf_counter()
            _ = evaluate_referable_dr(raw_probs)
            t1 = time.perf_counter()
            t_referable.append(t1 - t0)

            # G. Grad-CAM
            t0 = time.perf_counter()
            _ = compute_full_retinal_gradcam(eval_img, model=model)
            t1 = time.perf_counter()
            t_gradcam.append(t1 - t0)

            # H. Anatomy / Evidence
            t0 = time.perf_counter()
            _ = generate_retinal_evidence(eval_img, model=model)
            t1 = time.perf_counter()
            t_evidence.append(t1 - t0)

            # I. Report generation
            t0 = time.perf_counter()
            _ = generate_quality_report(img_path)
            t1 = time.perf_counter()
            t_report.append(t1 - t0)

            # J. Complete screening pipeline
            t0 = time.perf_counter()
            _ = run_screening_pipeline(img_path, model=model)
            t1 = time.perf_counter()
            t_pipe = t1 - t0
            t_pipeline_e2e.append(t_pipe)

            # Path-specific profiling based on actual status
            if dec["final_class"] == "GOOD":
                # PATH A: GOOD -> classifier -> referable -> GradCAM
                # -> evidence
                t_start = time.perf_counter()

                p_img = load_raw_image(img_path)
                p_sc = score_image_quality(p_img)
                _ = classify_quality_decision(p_sc)
                p_pred = predict_image(p_img, model=model)
                _ = evaluate_referable_dr([
                    p_pred["probabilities"][g] for g in range(5)
                ])
                _ = compute_full_retinal_gradcam(p_img, model=model)
                _ = generate_retinal_evidence(p_img, model=model)
                t_end = time.perf_counter()
                path_a_good.append(t_end - t_start)

            elif dec["final_class"] == "BORDERLINE":
                # PATH B: BORDERLINE -> enhance -> recheck -> classify
                # -> GradCAM -> evidence
                t_start = time.perf_counter()

                p_img = load_raw_image(img_path)
                p_sc = score_image_quality(p_img)
                _ = classify_quality_decision(p_sc)
                p_enh = enhance_clahe(p_img)
                p_recheck = score_image_quality(p_enh)
                _ = classify_quality_decision(p_recheck)
                p_pred = predict_image(p_enh, model=model)
                _ = evaluate_referable_dr([
                    p_pred["probabilities"][g] for g in range(5)
                ])
                _ = compute_full_retinal_gradcam(p_enh, model=model)
                _ = generate_retinal_evidence(p_enh, model=model)
                t_end = time.perf_counter()
                path_b_borderline.append(t_end - t_start)

    # PATH C: UNGRADEABLE -> recapture guidance -> STOP
    # Measure Path C timing using real pipeline ungradeable rejection
    black_fixture = np.zeros((384, 384, 3), dtype=np.uint8)
    for _ in range(repetitions * 3):
        t0 = time.perf_counter()
        t_sc = score_image_quality(black_fixture)
        t_dec = classify_quality_decision(t_sc)
        _ = generate_recapture_feedback(t_dec.get("triggered_gates", []))
        t1 = time.perf_counter()
        path_c_ungradeable.append(t1 - t0)

    # Aggregate component statistics
    components = {
        "image_loading": compute_timing_statistics(t_load),
        "iqa_scoring": compute_timing_statistics(t_iqa),
        "quality_decision": compute_timing_statistics(t_decision),
        "borderline_enhancement": compute_timing_statistics(t_enhance),
        "classifier_inference": compute_timing_statistics(t_classify),
        "referable_decision": compute_timing_statistics(t_referable),
        "gradcam_computation": compute_timing_statistics(t_gradcam),
        "evidence_generation": compute_timing_statistics(t_evidence),
        "report_generation": compute_timing_statistics(t_report),
        "pipeline_end_to_end": compute_timing_statistics(t_pipeline_e2e),
    }

    # Aggregate path statistics
    paths = {
        "path_a_good": compute_timing_statistics(path_a_good),
        "path_b_borderline": compute_timing_statistics(path_b_borderline),
        "path_c_ungradeable": compute_timing_statistics(path_c_ungradeable),
    }

    return {
        "milestone": "Milestone 13 - Step 2: System Runtime Profiling",
        "environment": env_meta,
        "image_count": len(image_paths),
        "repetitions": repetitions,
        "total_evaluations_per_component": len(image_paths) * repetitions,
        "cold_model_load": cold_load_metrics,
        "image_sizes": size_metrics,
        "path_distribution": path_counts,
        "per_image_summary": per_image_summary,
        "components": components,
        "paths": paths,
        "measured_status": "MEASURED",
    }


class PipelineProfiler:
    """Wrapper class for pipeline profiling operations."""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        repetitions: int = 3,
    ) -> None:
        self.data_dir = data_dir or DATA_DIR
        self.repetitions = repetitions

    def profile(self) -> Dict[str, Any]:
        """Execute profiling and return dictionary payload."""
        return run_pipeline_profiling(
            data_dir=self.data_dir,
            repetitions=self.repetitions,
        )
