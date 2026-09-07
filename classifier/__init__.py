"""Classifier module for Diabetic Retinopathy screening.

Integrates the trained EfficientNetB3 classifier downstream of the Image Quality Assessment (IQA) pipeline.
"""

from classifier.model import (
    load_classifier_model,
    get_model_metadata,
    clear_model_cache,
    DEFAULT_MODEL_PATH,
)
from classifier.preprocessing import (
    preprocess_classifier_image,
    prepare_input_tensor,
    prepare_batch_tensors,
    crop_retinal_borders,
    get_retinal_crop_box,
    TARGET_IMAGE_SIZE,
)
from classifier.referable import (
    evaluate_referable_dr,
    get_dr_grade_name,
    REFERABLE_THRESHOLD,
    DR_GRADE_NAMES,
)
from classifier.predictor import (
    predict_image,
    predict_batch,
    run_screening_pipeline,
)

__all__ = [
    "load_classifier_model",
    "get_model_metadata",
    "clear_model_cache",
    "DEFAULT_MODEL_PATH",
    "preprocess_classifier_image",
    "prepare_input_tensor",
    "prepare_batch_tensors",
    "crop_retinal_borders",
    "get_retinal_crop_box",
    "TARGET_IMAGE_SIZE",
    "evaluate_referable_dr",
    "get_dr_grade_name",
    "REFERABLE_THRESHOLD",
    "DR_GRADE_NAMES",
    "predict_image",
    "predict_batch",
    "run_screening_pipeline",
]
