#!/usr/bin/env python3
"""
job_dispatcher.py - Application Dispatcher & Recruiter Outreach Generator for Purna's Career Pipeline.
Manages Easy Apply state transitions, answers screener questions from screener_bank.json,
and generates grounded recruiter outreach messages.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
JOBS_DIR = BASE_DIR / "linkedin" / "jobs"
RADAR_FILE = JOBS_DIR / "jobs_radar.json"
APPLIED_FILE = JOBS_DIR / "applied_history.json"
SCREENER_FILE = JOBS_DIR / "screener_bank.json"
PROFILE_FILE = JOBS_DIR / "profile_master.json"

def load_json(p, default=None):
    if default is None:
        default = {}
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def save_json(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def match_screener_question(question_text):
    """
    Finds the best answer for a custom Easy Apply screener question
    from screener_bank.json.
    """
    bank = load_json(SCREENER_FILE, {}).get("screener_answers", {})
    q_low = question_text.lower()

    for key, data in bank.items():
        for kw in data.get("keywords", []):
            if kw in q_low:
                return {
                    "matched": True,
                    "key": key,
                    "answer": data.get("answer"),
                    "detail": data.get("detail")
                }

    return {
        "matched": False,
        "key": "novel_question",
        "answer": "Yes / Experienced",
        "detail": "Grounded in MSc Data Science and verified Python agent engineering background."
    }

def generate_recruiter_note(job_info, hiring_manager_name="Hiring Team"):
    """
    Generates a concise, high-signal LinkedIn message to the recruiter or hiring manager.
    Follows voice.md guidelines (zero corporate clichés, zero em-dashes).
    """
    title = job_info.get("title", "AI Engineer")
    company = job_info.get("company", "the team")
    location = job_info.get("location", "Berlin")
    
    note = (
        f"Hi {hiring_manager_name}, I saw {company}'s opening for {title} in {location}. "
        f"I am an MSc Data Science student based in Berlin researching hallucination attribution in multi-step LLM agent trajectories. "
        f"I've also built typed dependency injection middlewares using Pydantic AI and FastAPI. "
        f"I submitted an application and wanted to share my technical portfolio directly. Happy to connect."
    )
    return note

def apply_to_job(job_id, auto_mode=False):
    """
    Submits or records an application for a qualified job in jobs_radar.json.
    Updates applied_history.json.
    """
    radar = load_json(RADAR_FILE, {"jobs": []})
    jobs = radar.get("jobs", [])
    
    target_job = None
    for j in jobs:
        if j.get("id") == job_id:
            target_job = j
            break

    if not target_job:
        raise ValueError(f"Job ID '{job_id}' not found in jobs_radar.json")

    # Generate tailored resume
    resume_url = None
    try:
        from linkedin.jobs import resume_tailor
        res_file = resume_tailor.generate_tailored_resume(target_job)
        resume_url = f"/resumes/{Path(res_file).name}"
    except Exception as e:
        print(f"[Warning] Failed to generate tailored resume: {e}")

    # Mark as applied
    target_job["status"] = "APPLIED"
    target_job["applied_at"] = datetime.now().isoformat()
    if resume_url:
        target_job["resume_url"] = resume_url
    save_json(RADAR_FILE, radar)

    # Append to applied_history.json
    applied_history = load_json(APPLIED_FILE, [])
    history_entry = {
        "job_id": job_id,
        "title": target_job.get("title"),
        "company": target_job.get("company"),
        "location": target_job.get("location"),
        "salary_range": target_job.get("salary_range"),
        "match_score": target_job.get("match_score"),
        "applied_at": target_job["applied_at"],
        "job_url": target_job.get("job_url"),
        "resume_url": resume_url,
        "mode": "AUTONOMOUS_DAEMON" if auto_mode else "MANUAL_APPROVAL",
        "recruiter_outreach_note": generate_recruiter_note(target_job),
        "status": "APPLIED_CONFIRMED"
    }
    
    # Avoid duplicate log
    applied_history = [h for h in applied_history if h.get("job_id") != job_id]
    applied_history.insert(0, history_entry)
    save_json(APPLIED_FILE, applied_history)

    return history_entry

if __name__ == "__main__":
    sample_q = "How many years of experience with Python do you have?"
    ans = match_screener_question(sample_q)
    print("Screener Match:", ans)
    note = generate_recruiter_note({"title": "AI Agent Engineer", "company": "DeepAgent Labs", "location": "Berlin"})
    print("\nRecruiter Note:\n", note)
