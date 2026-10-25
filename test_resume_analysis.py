
from app.utils.resume_analysis import (
    build_resume_analysis_prompt,
    _validate_analysis,
)


def test_prompt_accepts_role_only():
    prompt = build_resume_analysis_prompt(
        resume_text="Python and SQL project experience.",
        target_role="Python Developer",
    )
    assert "Python Developer" in prompt
    assert "Not provided" in prompt


def test_prompt_accepts_job_description_only():
    prompt = build_resume_analysis_prompt(
        resume_text="Python and SQL project experience.",
        job_description="Seeking a Python developer with SQL skills.",
    )
    assert "Seeking a Python developer" in prompt


def test_prompt_accepts_both():
    prompt = build_resume_analysis_prompt(
        resume_text="Python and SQL project experience.",
        target_role="Python Developer",
        job_description="Python, SQL, and REST API skills required.",
    )
    assert "Python Developer" in prompt
    assert "REST API" in prompt


def test_prompt_rejects_both_inputs_empty():
    try:
        build_resume_analysis_prompt(
            resume_text="Python developer resume."
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_analysis_output_validation():
    result = _validate_analysis({
        "ats_score": 80,
        "match_percentage": 75,
        "summary": "Relevant skills are present.",
        "strengths": ["Python"],
        "matched_skills": ["SQL"],
        "missing_skills": [],
        "improvement_suggestions": ["Add project outcomes."],
        "keywords_missing": [],
        "experience_assessment": "Project experience is present.",
        "education_assessment": "Education details are available.",
        "interview_questions": ["Explain Python decorators."],
    })

    assert result["ats_score"] == 80
    assert result["match_percentage"] == 75
    assert isinstance(result["missing_skills"], list)


def test_analysis_rejects_invalid_score():
    data = {
        "ats_score": 120,
        "match_percentage": 75,
        "summary": "Assessment.",
        "strengths": [],
        "matched_skills": [],
        "missing_skills": [],
        "improvement_suggestions": [],
        "keywords_missing": [],
        "experience_assessment": "Assessment.",
        "education_assessment": "Assessment.",
        "interview_questions": [],
    }

    try:
        _validate_analysis(data)
    except Exception:
        pass
    else:
        raise AssertionError("Expected invalid score to be rejected")


if __name__ == "__main__":
    test_prompt_accepts_role_only()
    test_prompt_accepts_job_description_only()
    test_prompt_accepts_both()
    test_prompt_rejects_both_inputs_empty()
    test_analysis_output_validation()
    test_analysis_rejects_invalid_score()
    print("All resume analysis tests passed.")
