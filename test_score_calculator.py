
from app.utils.score_calculator import (
    calculate_resume_match_score,
    get_score_label,
)

result = {
    "ats_score": 50,
    "match_percentage": 80,
}

score = calculate_resume_match_score(result)

assert score == 68
assert get_score_label(score) == "Moderate match"

assert calculate_resume_match_score({
    "ats_score": 100,
    "match_percentage": 100,
}) == 100

assert calculate_resume_match_score({
    "ats_score": 0,
    "match_percentage": 0,
}) == 0

try:
    calculate_resume_match_score({
        "ats_score": 120,
        "match_percentage": 80,
    })
except ValueError:
    pass
else:
    raise AssertionError("Invalid score should be rejected")

print("All score calculator tests passed.")
