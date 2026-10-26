from app.utils.resume_analysis import analyze_resume

sample_resume = """
Python Developer fresher.
Skills: Python, SQL, Flask, HTML, CSS.
Project: Built a Flask application with CRUD operations and MySQL.
Education: Computer Science Engineering.
"""

try:
    result = analyze_resume(
        resume_text=sample_resume,
        target_role="Python Developer",
        job_description=(
            "Seeking a fresher Python developer with Python, SQL, "
            "Flask, REST API, and database fundamentals."
        ),
    )

    print("ATS score:", result["ats_score"])
    print("Match percentage:", result["match_percentage"])
    print("Matched skills:", result["matched_skills"])
    print("Missing skills:", result["missing_skills"])
    print("Suggestions:", result["improvement_suggestions"])

except Exception as exc:
    print("Analysis test failed:", exc)