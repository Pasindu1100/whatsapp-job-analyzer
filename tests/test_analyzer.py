import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analyzer import analyze_jobs, extract_job_info


def test_extract_job_info_from_text():
    text = """
    🚀 We’re Hiring | Machine Learning Engineer
    📍 Colombo, Sri Lanka | Contract | Hybrid
    We are looking for a Machine Learning Engineer to join our team.
    Skills: Python, PyTorch, MLOps, Data Pipelines
    Interested candidates, please apply or share your CV with us.
    https://zone24x7.com/careers/machine-learning-engineer/
    jobs@zone24x7.com
    """

    result = extract_job_info(text)

    assert result["job_title"] == "Machine Learning Engineer"
    assert result["company_name"] == "Zone24x7"
    assert "Python" in result["required_skills"]
    assert "PyTorch" in result["required_skills"]
    assert result["location"] == "Colombo, Sri Lanka"
    assert result["email"] == "jobs@zone24x7.com"
    assert result["job_type"] == "Contract"


def test_analyze_jobs_summarizes_top_skills_and_jobs():
    records = [
        {
            "job_title": "Machine Learning Engineer",
            "company_name": "Zone24x7",
            "required_skills": ["Python", "PyTorch", "MLOps"],
            "location": "Colombo, Sri Lanka",
            "email": "jobs@zone24x7.com",
            "job_type": "Contract",
        },
        {
            "job_title": "QA Engineer",
            "company_name": "Fexcon",
            "required_skills": ["Python", "Selenium", "QA"],
            "location": "Remote",
            "email": "jobs@fexcon.com",
            "job_type": "Internship",
        },
        {
            "job_title": "Machine Learning Engineer",
            "company_name": "Fexcon",
            "required_skills": ["Python", "SQL"],
            "location": "Colombo, Sri Lanka",
            "email": "jobs@fexcon.com",
            "job_type": "Full-Time",
        },
    ]

    analytics = analyze_jobs(records)

    assert analytics["top_job_titles"][0]["job_title"] == "Machine Learning Engineer"
    assert analytics["top_skills"][0]["skill"] == "Python"
    assert analytics["top_locations"][0]["location"] == "Colombo, Sri Lanka"
