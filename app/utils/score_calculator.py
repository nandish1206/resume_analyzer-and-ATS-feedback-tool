
def calculate_resume_match_score(analysis_result: dict) -> int:
    """
    Calculate an estimated overall resume compatibility score.

    Formula:
        40% ATS score + 60% job match percentage

    Returns:
        An integer score between 0 and 100.
    """
    if not isinstance(analysis_result, dict):
        raise ValueError("Analysis result must be a dictionary.")

    ats_score = analysis_result.get("ats_score")
    match_percentage = analysis_result.get("match_percentage")

    for field, value in (
        ("ats_score", ats_score),
        ("match_percentage", match_percentage),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0 <= value <= 100
        ):
            raise ValueError(
                f"{field} must be a number between 0 and 100."
            )

    score = (0.40 * ats_score) + (0.60 * match_percentage)
    return round(score)


def get_score_label(score: int) -> str:
    """Return a human-readable interpretation of the score."""
    if isinstance(score, bool) or not isinstance(score, int):
        raise ValueError("Score must be an integer.")

    if not 0 <= score <= 100:
        raise ValueError("Score must be between 0 and 100.")

    if score >= 80:
        return "Strong match"
    if score >= 60:
        return "Moderate match"
    if score >= 40:
        return "Needs improvement"
    return "Low match"
