"""Referable Diabetic Retinopathy screening logic.

Implements the clinical screening task separating non-referable cases
(Grade 0-1) from referable cases requiring specialist ophthalmologic review (Grade 2-4).

Uses the exact calibrated threshold (0.33) established in the original project
notebook (Cell 39) applied to the cumulative probability of Grades 2, 3, and 4:
referable_probability = sum(probabilities[2:5]) >= 0.33
"""

from typing import Dict, Any, List, Union
import numpy as np


DR_GRADE_NAMES: Dict[int, str] = {
    0: "No DR",
    1: "Mild DR",
    2: "Moderate DR",
    3: "Severe DR",
    4: "Proliferative DR",
}

# Calibrated referable threshold recovered from original project notebook Cell 39
REFERABLE_THRESHOLD: float = 0.33


def get_dr_grade_name(grade: int) -> str:
    """Return clinical grade name for integer DR grade (0-4)."""
    return DR_GRADE_NAMES.get(int(grade), f"Unknown Grade {grade}")


def evaluate_referable_dr(
    probabilities: Union[List[float], np.ndarray],
    threshold: float = REFERABLE_THRESHOLD,
) -> Dict[str, Any]:
    """Evaluate whether 5-class prediction distribution warrants referable screening alert.

    Level 0-1 = Non-Referable (No DR, Mild DR)
    Level 2-4 = Referable (Moderate, Severe, Proliferative DR)

    Cumulative probability of grades 2, 3, and 4 is compared against the threshold.

    Args:
        probabilities: 5-element array or list of softmax probabilities.
        threshold: Decision threshold for referable probability (default: 0.33).

    Returns:
        dict: Screening result with referable status, probability, threshold, and recommendation.
    """
    probs = np.array(probabilities, dtype=float)
    if len(probs) != 5:
        raise ValueError(f"Expected 5-element probability array, got {len(probs)}")

    # Referable probability = P(Grade 2) + P(Grade 3) + P(Grade 4)
    referable_prob = float(np.sum(probs[2:5]))
    is_referable = bool(referable_prob >= threshold)

    predicted_grade = int(np.argmax(probs))

    if is_referable:
        category = "Referable DR"
        clinical_action = "Referral recommended: schedule comprehensive ophthalmologic examination."
    else:
        category = "Non-Referable DR"
        clinical_action = "Routine annual diabetic eye screening recommended."

    return {
        "is_referable": is_referable,
        "referable_probability": round(referable_prob, 4),
        "threshold": float(threshold),
        "screening_category": category,
        "clinical_action": clinical_action,
        "derived_from_predicted_grade": predicted_grade >= 2,
        "grade_components": {
            "p_grade_2_moderate": round(float(probs[2]), 4),
            "p_grade_3_severe": round(float(probs[3]), 4),
            "p_grade_4_proliferative": round(float(probs[4]), 4),
        },
    }
