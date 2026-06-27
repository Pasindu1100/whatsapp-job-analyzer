import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Setup paths relative to this script
SCRIPT_DIR = Path(__file__).parent
INPUT_JSON = SCRIPT_DIR / "../data/processed_jobs.json"
OUTPUT_JSON = SCRIPT_DIR / "../data/ai_analyzed_jobs.json"
SUMMARY_JSON = SCRIPT_DIR / "../data/job_analytics_summary.json"
RAW_DATA_DIR = SCRIPT_DIR / "../data/raw"

# Optional Ollama configuration for future enhancement.
OLLAMA_API_URL = "http://localhost:11434/api/generate"
TEXT_MODEL = "gemma"
VISION_MODEL = "llava"

PROMPT = """
You are a technical recruiter AI. Extract the following information from the provided job posting text/image.
Return ONLY a valid JSON object with these exact keys. If a detail is missing, use null.
Keys: "job_title", "company_name", "required_skills" (array of strings), "location", "email", "phone_number".
"""

SKILL_PATTERNS = [
    ("Python", r"\bpython\b"),
    ("PyTorch", r"\bpytorch\b"),
    ("MLOps", r"\bmlops\b"),
    ("SQL", r"\bsql\b"),
    ("Selenium", r"\bselenium\b"),
    ("QA", r"\bqa\b"),
    ("JavaScript", r"\bjavascript\b"),
    ("React.js", r"\breact(?:\.js)?\b"),
    ("Node.js", r"\bnode(?:\.js)?\b"),
    ("Java", r"\bjava\b"),
    ("Spring Boot", r"\bspring boot\b"),
    ("Microservices", r"\bmicroservices\b"),
    ("UI/UX", r"\bui/ux\b|\buser interface\b|\buser experience\b"),
    ("Figma", r"\bfigma\b"),
    ("HTML", r"\bhtml\b"),
    ("CSS", r"\bcss\b"),
    ("Agile", r"\bagile\b"),
    ("Power BI", r"\bpower bi\b"),
    ("Tableau", r"\btableau\b"),
    ("Data Analysis", r"\bdata analysis\b"),
    ("Machine Learning", r"\bmachine learning\b"),
    ("Data Science", r"\bdata science\b"),
]

JOB_TYPE_PATTERNS = [
    ("Contract", r"\bcontract\b"),
    ("Internship", r"\binternship\b|\bintern\b"),
    ("Full-Time", r"\bfull[- ]time\b"),
    ("Part-Time", r"\bpart[- ]time\b"),
    ("Remote", r"\bremote\b"),
    ("Hybrid", r"\bhybrid\b"),
]


def normalize_text(text):
    if not text:
        return ""
    text = text.replace("\u202f", " ").replace("\xa0", " ")
    text = text.replace("\r", "\n")
    return re.sub(r"\s+", " ", text).strip()


def extract_job_info(text):
    cleaned_text = normalize_text(text)
    extracted = {
        "job_title": None,
        "company_name": None,
        "required_skills": [],
        "location": None,
        "email": None,
        "phone_number": None,
        "job_type": None,
        "job_openings": [],
    }

    if not cleaned_text:
        return extracted

    # Email and phone number
    email_matches = re.findall(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", cleaned_text)
    phone_matches = re.findall(r"(?:\+?94|0)?\d{9,10}", cleaned_text)
    if email_matches:
        extracted["email"] = email_matches[0]
    if phone_matches:
        extracted["phone_number"] = phone_matches[0]

    # Company name from email domain or obvious company mention
    if extracted["email"]:
        domain = extracted["email"].split("@", 1)[1].split(".", 1)[0]
        extracted["company_name"] = domain.replace("-", " ").capitalize()
    for pattern in [
        r"(?i)\b(?:hiring|join|careers)\b[^\n]{0,40}\b([A-Z][A-Za-z0-9&. -]{2,30})\b",
        r"(?i)\b([A-Z][A-Za-z0-9&. -]{2,30})\b(?:is looking for|is hiring|is expanding)",
    ]:
        match = re.search(pattern, cleaned_text)
        if match and not extracted["company_name"]:
            extracted["company_name"] = match.group(1).strip()
            break

    # Job title
    title_patterns = [
        r"(?i)\b(?:we(?:'|’)re|we are)\s+hiring(?:\s*\||\s+for)?\s*([A-Za-z][A-Za-z0-9 .&/()\-]+)",
        r"(?i)\bjoin us as a ([A-Za-z][A-Za-z0-9 .&/()\-]+)",
        r"(?i)\b(?:position|role)\s*[:\-]\s*([A-Za-z][A-Za-z0-9 .&/()\-]+)",
    ]
    for pattern in title_patterns:
        match = re.search(pattern, cleaned_text)
        if match:
            extracted["job_title"] = match.group(1).strip(" -")
            break

    # Fallback title from well-known role keywords
    if not extracted["job_title"]:
        role_match = re.search(r"\b([A-Z][A-Za-z0-9 .&/()\-]+(?:Engineer|Developer|Analyst|Designer|Specialist|Consultant|Manager|Associate|Intern|Executive))\b", cleaned_text)
        if role_match:
            extracted["job_title"] = role_match.group(1).strip()

    # Skills
    skills = []
    for skill, pattern in SKILL_PATTERNS:
        if re.search(pattern, cleaned_text, flags=re.IGNORECASE):
            skills.append(skill)
    extracted["required_skills"] = skills

    # Location
    location_patterns = [
        r"(?i)\b(?:location|located|📍)\s*[:\-]?\s*([A-Za-z0-9, ./-]+)",
        r"(?i)\b(?:colombo|remote|sri lanka)\b",
    ]
    for pattern in location_patterns:
        match = re.search(pattern, cleaned_text)
        if match:
            if match.lastindex:
                raw_location = match.group(1).strip()
                if raw_location.lower().startswith("colombo"):
                    extracted["location"] = "Colombo, Sri Lanka"
                else:
                    extracted["location"] = raw_location
            else:
                matched_text = match.group(0).strip()
                if matched_text.lower() == "colombo":
                    extracted["location"] = "Colombo, Sri Lanka"
                else:
                    extracted["location"] = matched_text
            break

    # Job type
    for job_type, pattern in JOB_TYPE_PATTERNS:
        if re.search(pattern, cleaned_text, flags=re.IGNORECASE):
            extracted["job_type"] = job_type
            break

    # Job openings list from bullet-like lines or role mentions
    lines = [line.strip(" •*-•▪️🔹🔸") for line in cleaned_text.splitlines() if line.strip()]
    for line in lines:
        if len(line) < 4:
            continue
        if re.search(r"\b(?:Intern|Engineer|Developer|Analyst|Designer|Specialist|Consultant|Manager|Associate|Executive|Officer)\b", line):
            if line.lower().startswith(("we're", "we are", "join", "open", "position", "role")) or line[0] in "0123456789" or "•" in line or "-" in line:
                extracted["job_openings"].append(line)
    if extracted["job_title"] and not extracted["job_openings"]:
        extracted["job_openings"] = [extracted["job_title"]]

    return extracted


def analyze_jobs(records):
    job_titles = Counter()
    skills_counter = Counter()
    companies = Counter()
    locations = Counter()
    job_types = Counter()
    emails = Counter()

    for record in records:
        title = (record or {}).get("job_title")
        if title:
            job_titles[title] += 1
        for skill in (record or {}).get("required_skills", []) or []:
            skills_counter[skill] += 1
        company = (record or {}).get("company_name")
        if company:
            companies[company] += 1
        location = (record or {}).get("location")
        if location:
            locations[location] += 1
        job_type = (record or {}).get("job_type")
        if job_type:
            job_types[job_type] += 1
        email = (record or {}).get("email")
        if email:
            emails[email] += 1

    return {
        "total_jobs": len(records),
        "top_job_titles": [
            {"job_title": title, "count": count} for title, count in job_titles.most_common(10)
        ],
        "top_skills": [
            {"skill": skill, "count": count} for skill, count in skills_counter.most_common(15)
        ],
        "top_companies": [
            {"company": company, "count": count} for company, count in companies.most_common(10)
        ],
        "top_locations": [
            {"location": location, "count": count} for location, count in locations.most_common(10)
        ],
        "top_job_types": [
            {"job_type": job_type, "count": count} for job_type, count in job_types.most_common(10)
        ],
        "top_contacts": [
            {"email": email, "count": count} for email, count in emails.most_common(10)
        ],
    }


def extract_with_llm(text_content, image_filename=None):
    try:
        import requests
    except ImportError:
        return None

    payload = {
        "model": TEXT_MODEL,
        "prompt": f"{PROMPT}\n\nJob Posting Content:\n{text_content}",
        "stream": False,
        "format": "json",
    }

    if image_filename and (image_filename.endswith(".jpg") or image_filename.endswith(".png")):
        img_path = RAW_DATA_DIR / image_filename
        if img_path.exists():
            payload["model"] = VISION_MODEL
            payload["images"] = [image_to_base64(img_path)]

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=20)
        response.raise_for_status()
        return json.loads(response.json()["response"])
    except Exception as exc:
        print(f"AI extraction skipped: {exc}")
        return None


def image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return img_file.read().hex()


def build_analysis(input_json=INPUT_JSON, output_json=OUTPUT_JSON, summary_json=SUMMARY_JSON):
    with open(input_json, "r", encoding="utf-8") as handle:
        jobs_data = json.load(handle)

    analyzed_data = []
    for index, job in enumerate(jobs_data, start=1):
        raw_text = job.get("raw_text", "")
        extracted_info = extract_with_llm(raw_text, job.get("associated_media"))
        if not extracted_info:
            extracted_info = extract_job_info(raw_text)

        combined_record = {**job, **extracted_info}
        analyzed_data.append(combined_record)

    with open(output_json, "w", encoding="utf-8") as handle:
        json.dump(analyzed_data, handle, indent=4)

    analytics = analyze_jobs(analyzed_data)
    analytics["generated_at"] = datetime.now(timezone.utc).isoformat()
    with open(summary_json, "w", encoding="utf-8") as handle:
        json.dump(analytics, handle, indent=4)

    return analyzed_data, analytics


if __name__ == "__main__":
    print(f"Loading cleaned dataset from {INPUT_JSON.resolve()}...")
    analyzed_data, analytics = build_analysis()
    print(f"Successfully analyzed {analytics['total_jobs']} entries.")
    print("Top job titles:")
    for item in analytics["top_job_titles"][:5]:
        print(f"- {item['job_title']}: {item['count']}")
    print("Top skills:")
    for item in analytics["top_skills"][:10]:
        print(f"- {item['skill']}: {item['count']}")
    print(f"Results saved to {OUTPUT_JSON.resolve()} and {SUMMARY_JSON.resolve()}")