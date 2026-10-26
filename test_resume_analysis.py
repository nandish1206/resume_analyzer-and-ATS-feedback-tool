from app.utils.resume_analysis import _validate_analysis
def test_analysis_output_validation():
    result = _validate_analysis({
        "ats_score": 80,
        "match_percentage": 75,
        "summary": "Relevant skills are present.",
        "strengths": ["Python"],
        "matched_skills": ["SQL"],
        "missing_skills": ["REST API"],
        "underrepresented_skills": [
            {
                "skill": "Flask",
                "resume_evidence": "Flask is listed in the project.",
                "evidence_gap": "The project description lacks implementation details.",
            }
        ],
        "skill_gap_recommendations": [
            {
                "skill": "REST API",
                "priority": "High",
                "recommendation": "Build and document a REST API project.",
            }
        ],
        "improvement_suggestions": ["Add project outcomes."],
        "keywords_missing": [],
        "experience_assessment": "Project experience is present.",
        "education_assessment": "Education details are available.",
        "interview_questions": ["Explain Python decorators."],
    })

    assert result["ats_score"] == 80
    assert result["match_percentage"] == 75
    assert result["matched_skills"] == ["SQL"]
    assert result["missing_skills"] == ["REST API"]

    assert result["underrepresented_skills"][0]["skill"] == "Flask"
    assert result["skill_gap_recommendations"][0]["priority"] == "High"
