"""Inference engine and integrated IQA-upstream DR screening pipeline.

Provides:
1. predict_image: Single-image 5-class DR prediction and referable evaluation.
2. predict_batch: Batch inference for multiple retinal images.
3. run_screening_pipeline: End-to-end upstream IQA routing:
   - GOOD: Direct classification on original image.
   - BORDERLINE: Automated enhancement -> re-check -> classification on enhanced image if accepted.
   - UNGRADEABLE: Classifier strictly bypassed, image rejected, operator recapture guidance provided.
"""

from pathlib import Path
from typing import Dict, Any, List, Union, Optional, Sequence
import numpy as np

try:
    import keras  # type: ignore
except ImportError:
    try:
        from tensorflow import keras  # type: ignore
    except ImportError:
        keras = None

from image_quality.io import load_raw_image
from image_quality.enhancement import enhance_clahe, enhance_image
from image_quality.report import generate_quality_report, CLINICAL_SAFETY_DISCLAIMER
from classifier.model import load_classifier_model
from classifier.preprocessing import (
    prepare_input_tensor,
    prepare_batch_tensors,
    preprocess_classifier_image,
)
from classifier.referable import (
    evaluate_referable_dr,
    get_dr_grade_name,
    REFERABLE_THRESHOLD,
    DR_GRADE_NAMES,
)


def predict_image(
    image_or_path: Union[str, Path, np.ndarray],
    model: Optional[Any] = None,
    referable_threshold: float = REFERABLE_THRESHOLD,
    crop_borders: bool = True,
) -> Dict[str, Any]:
    """Execute 5-class DR inference on a single retinal image.

    Args:
        image_or_path: File path or RGB NumPy array.
        model: Optional pre-loaded Keras model. If None, loads cached model.
        referable_threshold: Calibrated cutoff for referable DR (default: 0.33).
        crop_borders: Whether to crop black background borders.

    Returns:
        dict: Complete prediction payload with 5-class probabilities and referable decision.
    """
    if model is None:
        model = load_classifier_model()

    input_tensor = prepare_input_tensor(image_or_path, crop_borders=crop_borders)

    # Forward pass: model has internal softmax on dense_3
    # Use model(tensor, training=False) for deterministic inference without layer dropout/augmentation
    raw_output = model(input_tensor, training=False).numpy()[0]

    # Convert to float and re-normalize strictly so sum is exactly 1.0
    probs_sum = float(np.sum(raw_output))
    if probs_sum > 0:
        norm_probs = raw_output / probs_sum
    else:
        norm_probs = raw_output

    predicted_grade = int(np.argmax(norm_probs))
    top_confidence = float(norm_probs[predicted_grade])
    class_name = get_dr_grade_name(predicted_grade)

    prob_dict = {
        grade: round(float(norm_probs[grade]), 5) for grade in range(len(norm_probs))
    }

    referable_result = evaluate_referable_dr(
        norm_probs, threshold=referable_threshold
    )

    return {
        "predicted_grade": predicted_grade,
        "class_name": class_name,
        "probabilities": prob_dict,
        "confidence": round(top_confidence, 5),
        "model_identifier": getattr(model, "name", "EfficientNetB3_DR"),
        "referable": referable_result,
    }


def predict_batch(
    images_or_paths: Sequence[Union[str, Path, np.ndarray]],
    model: Optional[Any] = None,
    referable_threshold: float = REFERABLE_THRESHOLD,
    crop_borders: bool = True,
) -> List[Dict[str, Any]]:
    """Execute batch 5-class DR inference on multiple retinal images.

    Args:
        images_or_paths: List of file paths or RGB NumPy arrays.
        model: Optional pre-loaded Keras model. If None, loads cached model.
        referable_threshold: Calibrated cutoff for referable DR (default: 0.33).
        crop_borders: Whether to crop black background borders.

    Returns:
        list[dict]: List of prediction payloads.
    """
    if not images_or_paths:
        return []

    if model is None:
        model = load_classifier_model()

    batch_tensor = prepare_batch_tensors(
        images_or_paths, crop_borders=crop_borders
    )
    raw_outputs = model(batch_tensor, training=False).numpy()

    results = []
    for raw_output in raw_outputs:
        probs_sum = float(np.sum(raw_output))
        norm_probs = raw_output / probs_sum if probs_sum > 0 else raw_output
        predicted_grade = int(np.argmax(norm_probs))
        top_confidence = float(norm_probs[predicted_grade])
        class_name = get_dr_grade_name(predicted_grade)

        prob_dict = {
            grade: round(float(norm_probs[grade]), 5)
            for grade in range(len(norm_probs))
        }

        referable_result = evaluate_referable_dr(
            norm_probs, threshold=referable_threshold
        )

        results.append(
            {
                "predicted_grade": predicted_grade,
                "class_name": class_name,
                "probabilities": prob_dict,
                "confidence": round(top_confidence, 5),
                "model_identifier": getattr(model, "name", "EfficientNetB3_DR"),
                "referable": referable_result,
            }
        )

    return results


def run_screening_pipeline(
    image_or_path: Union[str, Path, np.ndarray],
    model: Optional[Any] = None,
    referable_threshold: float = REFERABLE_THRESHOLD,
    save_enhanced_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute integrated end-to-end DR screening pipeline with upstream IQA routing.

    Workflow:
    1. Real Image -> Image Quality Assessment (IQA).
    2. GOOD -> Route directly to classifier using original image.
    3. BORDERLINE -> Automated enhancement (CLAHE).
         If enhancement accepted -> Route to classifier using enhanced image.
         If enhancement rejected -> Stop, do not route to classifier.
    4. UNGRADEABLE -> Stop immediately. Bypasses classifier completely. Return recapture feedback.

    Args:
        image_or_path: File path or RGB NumPy array.
        model: Optional pre-loaded Keras model.
        referable_threshold: Calibrated cutoff for referable DR (default: 0.33).
        save_enhanced_dir: Optional directory to persist derived enhanced images.

    Returns:
        dict: Comprehensive screening report integrating IQA, enhancement, classification,
              referable screening, and operator instructions.
    """
    # 1. Run upstream IQA and generate structured report
    iqa_report = generate_quality_report(
        image_or_path,
        attempt_enhancement_if_borderline=True,
        enhancement_save_dir=save_enhanced_dir,
    )

    initial_quality = iqa_report["initial_quality_status"]
    final_quality = iqa_report["quality_status"]
    composite_score = float(iqa_report["composite_score"])
    component_scores = iqa_report["component_scores"]
    enhancement = iqa_report["enhancement"]
    recommended_action = iqa_report["recommended_action"]
    operator_message = iqa_report["operator_message"]
    recapture_feedback = iqa_report.get("recapture_feedback")

    # Determine image routing
    classifier_result: Optional[Dict[str, Any]] = None
    image_sent_to_classifier: Optional[str] = None
    classifier_run: bool = False
    active_image_array: Optional[np.ndarray] = None

    if initial_quality == "GOOD":
        # Direct routing to classifier with original image
        if isinstance(image_or_path, (str, Path)):
            active_image_array = load_raw_image(image_or_path)
        else:
            active_image_array = image_or_path.copy()

        image_sent_to_classifier = "original"
        classifier_result = predict_image(
            active_image_array,
            model=model,
            referable_threshold=referable_threshold,
        )
        classifier_run = True

    elif initial_quality == "BORDERLINE":
        # Check if enhancement was accepted
        if enhancement.get("accepted") is True:
            # Load or generate enhanced image
            enh_path = enhancement.get("enhanced_image_path")
            if enh_path is not None and Path(enh_path).exists():
                active_image_array = load_raw_image(enh_path)
            else:
                orig_img = (
                    load_raw_image(image_or_path)
                    if isinstance(image_or_path, (str, Path))
                    else image_or_path.copy()
                )
                enh_method = enhancement.get("method", "clahe")
                active_image_array, _ = enhance_image(orig_img, method=enh_method)

            image_sent_to_classifier = f"enhanced_{enhancement.get('method', 'clahe')}"
            classifier_result = predict_image(
                active_image_array,
                model=model,
                referable_threshold=referable_threshold,
            )
            classifier_run = True
        else:
            # Enhancement rejected - classifier bypassed
            image_sent_to_classifier = None
            classifier_result = None
            classifier_run = False

    elif initial_quality == "UNGRADEABLE":
        # Strictly bypass classifier - image rejected
        image_sent_to_classifier = None
        classifier_result = None
        classifier_run = False

    # Extract prediction details if classifier was run
    if classifier_run and classifier_result is not None:
        predicted_dr_grade = classifier_result["predicted_grade"]
        predicted_dr_class = classifier_result["class_name"]
        probabilities = classifier_result["probabilities"]
        confidence = classifier_result["confidence"]
        is_referable = classifier_result["referable"]["is_referable"]
        referable_probability = classifier_result["referable"]["referable_probability"]
        referable_status = (
            "Referable DR" if is_referable else "Non-Referable DR"
        )
        model_identifier = classifier_result["model_identifier"]
        screening_action = (
            f"Screening completed: {predicted_dr_class} ({referable_status})."
        )
    else:
        predicted_dr_grade = None
        predicted_dr_class = None
        probabilities = None
        confidence = None
        is_referable = None
        referable_probability = None
        referable_status = "N/A (Image Rejected by IQA)"
        model_identifier = None
        screening_action = f"Screening halted by IQA quality gate ({final_quality})."

    # Save active image for visualization or traceability if needed
    return {
        "image_filename": iqa_report["image_identifier"],
        "image_path": iqa_report["image_path"],
        "iqa_status": initial_quality,
        "focus_score": component_scores.get("focus_score", component_scores.get("focus", 0.0)),
        "illumination_score": component_scores.get("illumination_score", component_scores.get("illumination", 0.0)),
        "fov_score": component_scores.get("fov_score", component_scores.get("fov", 0.0)),
        "centering_score": component_scores.get("centering_score", component_scores.get("centering", 0.0)),
        "composite_score": iqa_report["initial_composite_score"],
        "enhancement_attempted": bool(enhancement.get("attempted", False)),
        "enhancement_method": enhancement.get("method"),
        "enhancement_accepted": enhancement.get("accepted"),
        "enhancement_delta_composite": enhancement.get("delta_composite"),
        "final_quality_status": final_quality,
        "effective_composite_score": composite_score,
        "image_sent_to_classifier": image_sent_to_classifier,
        "classifier_run": classifier_run,
        "predicted_dr_grade": predicted_dr_grade,
        "predicted_dr_class": predicted_dr_class,
        "probabilities": probabilities,
        "confidence": confidence,
        "referable": is_referable,
        "referable_probability": referable_probability,
        "referable_status": referable_status,
        "operator_action": recommended_action,
        "operator_message": operator_message,
        "recapture_feedback": recapture_feedback,
        "model_identifier": model_identifier,
        "screening_action": screening_action,
        "clinical_safety_disclaimer": CLINICAL_SAFETY_DISCLAIMER,
        "active_image_array": active_image_array,
    }
