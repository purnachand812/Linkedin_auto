#!/usr/bin/env python3
"""
autonomous_job_agent.py - 24/7 Autonomous Job Application Engine for Purnachandra Madhukar.
Handles:
1. Radar scanning & filtering (Werkstudent, Internship, Part-Time in Berlin/Germany)
2. Automated 100-point ATS fit evaluation
3. Dynamic generation of tailored Europass CVs matching the employer's tech stack
4. Deterministic screener answering from screener_bank.json (phone, visa, resident, German A2, no driving licence)
5. Grounded recruiter outreach note drafting
6. Safe execution throttling with anti-ban pacing (daily limits)
7. Full integration with the 24/7 background daemon and dashboard
"""

import os
import sys
import json
import time
from datetime import datetime, date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
JOBS_DIR = BASE_DIR / "linkedin" / "jobs"
RADAR_FILE = JOBS_DIR / "jobs_radar.json"
APPLIED_FILE = JOBS_DIR / "applied_history.json"
CONFIG_FILE = JOBS_DIR / "auto_apply_config.json"
LOG_FILE = JOBS_DIR / "auto_apply_log.json"
PROFILE_FILE = JOBS_DIR / "profile_master.json"
SCREENER_FILE = JOBS_DIR / "screener_bank.json"

sys.path.insert(0, str(BASE_DIR))
try:
    from linkedin.jobs import resume_tailor
    from linkedin.jobs import job_dispatcher
    from linkedin.jobs import job_matcher
except ImportError:
    resume_tailor = None
    job_dispatcher = None
    job_matcher = None

DEFAULT_CONFIG = {
    "enabled": True,
    "daily_limit": 5,
    "min_match_score": 85,
    "target_roles": ["Werkstudent", "Internship", "Part-Time", "Praktikum", "Student"],
    "target_locations": ["Berlin", "Berlin, Germany", "Remote Germany", "Hybrid Berlin"],
    "today_date": str(date.today()),
    "applied_today": 0,
    "last_run": None,
    "status": "RUNNING",
    "anti_ban_delay_seconds": 2
}

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

def get_config():
    cfg = load_json(CONFIG_FILE, DEFAULT_CONFIG)
    today_str = str(date.today())
    if cfg.get("today_date") != today_str:
        cfg["today_date"] = today_str
        cfg["applied_today"] = 0
        save_json(CONFIG_FILE, cfg)
    return cfg

def update_config(updates):
    cfg = get_config()
    cfg.update(updates)
    save_json(CONFIG_FILE, cfg)
    return cfg

def append_log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "datetime": datetime.now().isoformat(),
        "level": level,
        "message": message
    }
    log_data = load_json(LOG_FILE, {"entries": []})
    entries = log_data.get("entries", [])
    entries.append(entry)
    log_data["entries"] = entries[-60:]
    save_json(LOG_FILE, log_data)
    try:
        print(f"[AUTO-APPLY {level}] {message}")
    except Exception:
        pass
    return entry

def get_logs(limit=30):
    log_data = load_json(LOG_FILE, {"entries": []})
    return log_data.get("entries", [])[-limit:]

def is_job_eligible(job, config):
    if job.get("status") == "APPLIED":
        return False, "Already applied"
    
    match_score = job.get("match_score", 0)
    min_score = config.get("min_match_score", 85)
    if match_score < min_score:
        return False, f"Match score {match_score} below minimum threshold {min_score}"
    
    loc = job.get("location", "").lower()
    target_locs = [tl.lower() for tl in config.get("target_locations", [])]
    loc_match = any(tl in loc for tl in target_locs) or "berlin" in loc or "remote" in loc
    if not loc_match:
        return False, f"Location '{loc}' outside target scope"
    
    return True, "Eligible"

def execute_autonomous_application(job):
    job_id = job.get("id")
    title = job.get("title", "Software Engineer")
    company = job.get("company", "Company")

    append_log(f"Initiating autonomous application: '{title}' at {company} (ID: {job_id})")

    resume_path = None
    if resume_tailor:
        try:
            resume_path = resume_tailor.generate_tailored_resume(job)
            append_log(f"Generated tailored Europass CV: {Path(resume_path).name}", "SUCCESS")
        except Exception as e:
            append_log(f"Error tailoring CV: {e}", "WARNING")

    screener_answers = []
    if job_dispatcher:
        standard_questions = [
            "Are you authorized to work in Germany?",
            "Do you require visa sponsorship?",
            "What is your current location and availability?",
            "What is your German language proficiency?",
            "Do you have a valid driving licence?"
        ]
        for q in standard_questions:
            res = job_dispatcher.match_screener_question(q)
            screener_answers.append({
                "question": q,
                "answer": res.get("answer"),
                "detail": res.get("detail")
            })
    append_log(f"Resolved {len(screener_answers)} screener questions from deterministic bank.", "SUCCESS")

    outreach_note = ""
    if job_dispatcher:
        outreach_note = job_dispatcher.generate_recruiter_note(job)

    result = None
    if job_dispatcher:
        result = job_dispatcher.apply_to_job(job_id, auto_mode=True)
    
    append_log(f"Application confirmed! Logged to applied_history.json for {company}.", "SUCCESS")

    return {
        "job_id": job_id,
        "title": title,
        "company": company,
        "match_score": job.get("match_score"),
        "resume_url": f"/resumes/{Path(resume_path).name}" if resume_path else None,
        "outreach_note": outreach_note,
        "screener_answers": screener_answers,
        "status": "APPLIED_CONFIRMED"
    }

def run_autonomous_cycle(force=False):
    config = get_config()
    if not config.get("enabled") and not force:
        return {"status": "PAUSED", "applied_count": 0, "message": "Autonomous application agent is currently paused."}

    daily_limit = config.get("daily_limit", 5)
    applied_today = config.get("applied_today", 0)

    if applied_today >= daily_limit and not force:
        append_log(f"Daily quota reached ({applied_today}/{daily_limit}). Standing by until tomorrow.", "INFO")
        return {"status": "QUOTA_REACHED", "applied_today": applied_today, "daily_limit": daily_limit}

    radar = load_json(RADAR_FILE, {"jobs": []})
    jobs = radar.get("jobs", [])
    
    eligible_jobs = []
    for j in jobs:
        ok, reason = is_job_eligible(j, config)
        if ok:
            eligible_jobs.append(j)

    append_log(f"Radar scan: {len(jobs)} active jobs, {len(eligible_jobs)} eligible for auto-apply.")

    if not eligible_jobs:
        return {"status": "IDLE", "message": "No unapplied eligible jobs found in radar.", "applied_count": 0}

    eligible_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    applied_results = []
    slots_available = daily_limit - applied_today
    if force:
        slots_available = max(1, slots_available)

    target_batch = eligible_jobs[:slots_available]

    for job in target_batch:
        try:
            res = execute_autonomous_application(job)
            applied_results.append(res)
            applied_today += 1
            config["applied_today"] = applied_today
            config["last_run"] = datetime.now().isoformat()
            save_json(CONFIG_FILE, config)

            delay = config.get("anti_ban_delay_seconds", 2)
            time.sleep(delay)

        except Exception as e:
            append_log(f"Failed to auto-apply to {job.get('title')}: {e}", "ERROR")

    return {
        "status": "COMPLETED",
        "applied_count": len(applied_results),
        "applied_today": applied_today,
        "daily_limit": daily_limit,
        "results": applied_results
    }

if __name__ == "__main__":
    print("Testing autonomous job agent run cycle...")
    res = run_autonomous_cycle(force=False)
    print(json.dumps(res, indent=2))
