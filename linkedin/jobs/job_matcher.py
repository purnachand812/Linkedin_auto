#!/usr/bin/env python3
"""
job_matcher.py - 100-Point Job Match Rubric & Keyword Analyzer for Purna's Career Pipeline.
Evaluates Job Descriptions (JDs) against verified technical skills, MSc thesis, and German/EU residency.
Only jobs scoring >= 80/100 qualify for tailored application generation.
"""

import os
import sys
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
JOBS_DIR = BASE_DIR / "linkedin" / "jobs"
PROFILE_FILE = JOBS_DIR / "profile_master.json"

def load_profile():
    if PROFILE_FILE.exists():
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

PROFILE = load_profile()

def evaluate_job_match(title_or_dict, company="Company", location="Berlin, Germany", description="", posted_hours=6, applicants_count=15):
    """
    Evaluates a job listing on a strict 100-point rubric:
    1. Tech Stack Match (35 pts)
    2. Seniority & Research Fit (25 pts)
    3. Location & Compliance (20 pts)
    4. Freshness & Applicant Urgency (20 pts)
    """
    if isinstance(title_or_dict, dict):
        d = title_or_dict
        title = d.get("title", "AI Engineer")
        company = d.get("company", company)
        location = d.get("location", location)
        description = d.get("description", "")
        posted_hours = d.get("posted_hours", posted_hours)
        applicants_count = d.get("applicants_count", applicants_count)
    else:
        title = title_or_dict

    text = f"{title} {description}".lower()
    
    # 1. Tech Stack Match (Max 35 pts)
    tech_score = 0
    matched_skills = []
    missing_skills = []

    skills_weights = {
        "python": 8,
        "pytorch": 6,
        "fastapi": 5,
        "pydantic": 4,
        "agent": 5,
        "llm": 5,
        "docker": 3,
        "sql": 3,
        "git": 2,
        "transformers": 4,
        "ollama": 3,
        "vllm": 3,
        "playwright": 3
    }

    for skill, weight in skills_weights.items():
        if re.search(r'\b' + re.escape(skill) + r'\b', text):
            tech_score += weight
            matched_skills.append(skill)
        else:
            if weight >= 4:
                missing_skills.append(skill)

    tech_pts = min(35, tech_score)

    # 2. Seniority & Research Fit (Max 25 pts)
    fit_score = 15 # Baseline
    # Positive triggers
    if any(k in text for k in ["working student", "werkstudent", "junior", "msc", "master", "entry level", "graduate"]):
        fit_score += 10
    elif any(k in text for k in ["autonomous agent", "hallucination", "tool-calling", "agent trajectory", "rag"]):
        fit_score += 10
    
    # Negative penalty for high-seniority requirements
    if any(k in text for k in ["8+ years", "10+ years", "director", "vp of engineering", "head of ai"]):
        fit_score -= 15

    fit_pts = max(0, min(25, fit_score))

    # 3. Location & Compliance Fit (Max 20 pts)
    loc_lower = location.lower()
    loc_score = 0
    if "berlin" in loc_lower or "berlin" in text:
        loc_score = 20 # Perfect local match in Berlin
    elif any(k in loc_lower for k in ["germany", "deutschland", "remote eu", "hybrid"]):
        loc_score = 16
    elif "remote" in loc_lower:
        loc_score = 14
    else:
        loc_score = 5

    loc_pts = min(20, loc_score)

    # 4. Freshness & Applicant Urgency (Max 20 pts)
    freshness_pts = 0
    if posted_hours <= 12:
        freshness_pts += 12
    elif posted_hours <= 24:
        freshness_pts += 8
    elif posted_hours <= 48:
        freshness_pts += 4

    if applicants_count <= 20:
        freshness_pts += 8
    elif applicants_count <= 40:
        freshness_pts += 4

    total_score = tech_pts + fit_pts + loc_pts + min(20, freshness_pts)

    return {
        "total_score": total_score,
        "qualified": total_score >= 80,
        "breakdown": {
            "tech_stack_pts": tech_pts,
            "seniority_fit_pts": fit_pts,
            "location_compliance_pts": loc_pts,
            "freshness_urgency_pts": min(20, freshness_pts)
        },
        "matched_skills": matched_skills,
        "missing_skills": missing_skills[:4],
        "recommendation": "APPLY_HIGH_PRIORITY" if total_score >= 90 else ("QUALIFIED" if total_score >= 80 else "SKIP")
    }

if __name__ == "__main__":
    sample_jd = "We need an AI Agent Engineer in Berlin using Python, FastAPI, and PyTorch for local LLM inference with Ollama. Working student or junior role."
    res = evaluate_job_match("AI Agent Engineer", "DeepTech Berlin", "Berlin, Germany", sample_jd, 4, 12)
    print(json.dumps(res, indent=2))
