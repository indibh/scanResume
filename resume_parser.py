"""Deterministic parsing of common resume text patterns."""

from __future__ import annotations

import re
from datetime import date
from typing import Any


MONTHS = (
    "jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    "jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|"
    "nov(?:ember)?|dec(?:ember)?"
)
DATE_PATTERN = rf"(?:{MONTHS})?\s*\d{{4}}|present|current"
DATE_RANGE_RE = re.compile(
    rf"(?P<start>{DATE_PATTERN})\s*(?:-|–|—|to)\s*(?P<end>{DATE_PATTERN})",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
SECTION_RE = re.compile(
    r"^\s*(experience|work experience|employment|professional experience|"
    r"skills?|technical skills|education|academic background)\s*:?\s*$",
    re.IGNORECASE,
)

SKILL_CATEGORIES = {
    "programming_languages": {
        "python", "java", "javascript", "typescript", "c", "c++", "c#", "go",
        "rust", "ruby", "php", "kotlin", "swift", "scala", "r",
    },
    "frameworks_and_libraries": {
        "react", "angular", "vue", "django", "flask", "fastapi", "spring",
        "node.js", "node", ".net", "tensorflow", "pytorch", "pandas",
    },
    "databases": {
        "sql", "mysql", "postgresql", "postgres", "mongodb", "oracle",
        "redis", "dynamodb", "sqlite",
    },
    "cloud_and_devops": {
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
        "git", "github", "gitlab", "ci/cd",
    },
    "analytics_and_tools": {
        "excel", "tableau", "power bi", "powerbi", "spark", "hadoop",
        "machine learning", "deep learning", "nlp",
    },
}


def parse_resume(filename: str, text: str) -> dict[str, Any]:
    """Parse a resume into the public scanResume JSON schema."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    experience_lines, education_lines, skill_lines = _section_lines(lines)
    companies = _parse_companies(experience_lines)
    return {
        "filename": filename,
        "total_experience_years": _total_experience_years(text, companies),
        "companies": companies,
        "skills": _parse_skills(skill_lines or lines),
        "education": _parse_education(education_lines),
    }


def _section_lines(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    sections: dict[str, list[str]] = {"experience": [], "education": [], "skills": []}
    current = ""
    for line in lines:
        match = SECTION_RE.match(line)
        if match:
            heading = match.group(1).lower()
            if "skill" in heading:
                current = "skills"
            elif "education" in heading or "academic" in heading:
                current = "education"
            elif "experience" in heading or "employment" in heading:
                current = "experience"
            continue
        if current:
            sections[current].append(line)
    return sections["experience"], sections["education"], sections["skills"]


def _parse_companies(lines: list[str]) -> list[dict[str, Any]]:
    companies = []
    for index, line in enumerate(lines):
        date_match = DATE_RANGE_RE.search(line)
        if not date_match:
            continue
        before_dates = line[: date_match.start()].strip(" ,|:-")
        title, company = _title_and_company(before_dates)
        title = title or (lines[index - 1] if index else None)
        companies.append(
            {
                "company": company,
                "title": title if title != company else None,
                "start_date": _normalize_date(date_match.group("start")),
                "end_date": _normalize_date(date_match.group("end")),
                "duration_years": _duration_years(
                    date_match.group("start"), date_match.group("end")
                ),
            }
        )
    return companies


def _title_and_company(value: str) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    pieces = re.split(r"\s+[|@,-]\s+|\s+at\s+", value, maxsplit=1, flags=re.IGNORECASE)
    if len(pieces) == 1:
        return None, pieces[0].strip() or None
    return pieces[0].strip() or None, pieces[1].strip() or None


def _total_experience_years(text: str, companies: list[dict[str, Any]]) -> float | None:
    explicit = re.search(
        r"(?:total\s+)?(?:professional\s+)?experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*\+?\s*years?",
        text,
        re.IGNORECASE,
    )
    if explicit:
        return float(explicit.group(1))
    durations = [item["duration_years"] for item in companies if item["duration_years"]]
    return round(sum(durations), 1) if durations else None


def _duration_years(start: str, end: str) -> float | None:
    start_year = _year_from_date(start)
    end_year = date.today().year if end.lower() in {"present", "current"} else _year_from_date(end)
    if start_year is None or end_year is None or end_year < start_year:
        return None
    return float(end_year - start_year)


def _year_from_date(value: str) -> int | None:
    match = YEAR_RE.search(value)
    return int(match.group()) if match else None


def _normalize_date(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).title()


def _parse_skills(lines: list[str]) -> dict[str, list[str]]:
    text = " ".join(lines).lower()
    parsed = {}
    for category, skills in SKILL_CATEGORIES.items():
        found = sorted(
            (skill for skill in skills if re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", text)),
            key=str.lower,
        )
        parsed[category] = found
    return parsed


def _parse_education(lines: list[str]) -> list[dict[str, str | None]]:
    education = []
    degree_re = re.compile(
        r"\b(ph\.?d\.?|doctorate|master(?:'s)?|mba|bachelor(?:'s)?|b\.?tech\.?|"
        r"m\.?tech\.?|b\.?s\.?|m\.?s\.?|associate(?:'s)?)\b",
        re.IGNORECASE,
    )
    for line in lines:
        degree = degree_re.search(line)
        if not degree:
            continue
        years = YEAR_RE.findall(line)
        without_years = YEAR_RE.sub("", line).strip(" ,-")
        institution = re.split(
            r"\s+[-|,]\s+|\s+at\s+", without_years, maxsplit=1, flags=re.IGNORECASE
        )
        education.append(
            {
                "degree": degree.group(0),
                "institution": institution[-1].strip() if len(institution) > 1 else None,
                "field": None,
                "start_date": years[0] if len(years) > 1 else None,
                "end_date": years[-1] if years else None,
            }
        )
    return education
