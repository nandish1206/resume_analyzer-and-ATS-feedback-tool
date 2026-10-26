# Resume Analyzer & ATS Feedback Tool

An AI-powered web application that analyzes resumes against a target job role or job description and provides ATS (Applicant Tracking System) feedback, skill-gap analysis, missing keywords, improvement suggestions, and interview preparation questions.

## Features

- **User Authentication** — Register and log in securely.
- **Resume Analysis** — Upload a resume and analyze it against a target role or job description.
- **ATS Feedback** — View an ATS score and job-match assessment.
- **Skill Gap Analysis** — Identify matched, missing, and underrepresented skills.
- **Keyword Analysis** — Discover important missing keywords.
- **Improvement Suggestions** — Get actionable recommendations to improve your resume.
- **Progress Checklist** — Track completed resume improvements.
- **Interview Questions** — Generate role-specific interview questions and request additional questions.
- **Analysis History** — Access previous resume analyses.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| HTML, CSS, JavaScript | Frontend and interactive UI |
| MySQL / TiDB | Database |
| SQLAlchemy | Database integration |
| Google Gemini API | AI-powered resume analysis and interview questions |
| Git & GitHub | Version control and source code hosting |

## Project Structure

```text
resume_analyzer/
├── app/
│   ├── static/
│   │   └── style.css
│   ├── templates/
│   ├── utils/
│   │   ├── gemini_service.py
│   │   ├── interview_questions.py
│   │   ├── resume_analysis.py
│   │   ├── score_calculator.py
│   │   └── text_extraction.py
│   ├── __init__.py
│   ├── extensions.py
│   ├── models.py
│   └── routes.py
├── tests/
├── .env.example
├── requirements.txt
├── run.py
└── README.md
```

*Note: Adjust the structure above if your actual repository differs.*

## Prerequisites

- Python installed on your system
- MySQL or a configured TiDB database
- Google Gemini API key
- Git

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd resume_analyzer
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual GitHub repository URL.

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file in the project root and configure the variables required by your application.

Typical settings may include:

```env
SECRET_KEY=your_secret_key
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=your_database_connection_string
```

Use the exact variable names expected by your application. Replace the example values with your own configuration. **Never commit `.env` or expose API keys and database credentials.**

### 5. Initialize the database

Follow your application's database setup process to create the required tables and configure the database connection.

### 6. Run the application

```bash
python run.py
```

Open the application in your browser:

http://127.0.0.1:5000

## Testing

Run the automated tests from the project root:

```bash
pytest -q
```

## Security

- Keep API keys and database credentials in environment variables.
- Do not commit `.env` or other files containing secrets.
- Protect authenticated routes and users' analysis history.
- Use secure configuration when deploying the application.

## Future Improvements

- Deploy the application to a production environment.
- Add more automated tests and error-handling coverage.
- Improve the user experience based on testing and feedback.

## Author

Developed as a Python and Flask project to explore AI-powered resume analysis, ATS feedback, and interview preparation.
