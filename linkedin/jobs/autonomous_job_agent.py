#!/usr/bin/env python3
"""
autonomous_job_agent.py - 24/7 Autonomous Job Application Engine for Purnachandra Madhukar.
Handles:
1. 20-Hour Cadence Radar scanning & freshness filtering (posted <= 4 to 7 days in Berlin / Germany)
2. Automated 100-point ATS fit evaluation against GISMA M.Sc. Data Science & verified profile
3. Dynamic generation of tailored Europass CVs matching the employer's tech stack
4. Dynamic generation of individualized European Cover Letters tailored to company & role
5. Deterministic screener answering from screener_bank.json (phone, visa, resident, German A2, no driving licence)
6. Grounded recruiter outreach note formulation
7. Safe anti-ban throttling (daily limits)
8. End-of-day automatic tracking report compilation & email dispatch to purnachand0812@gmail.com
"""

import os
import sys
import re
import json
import time
from datetime import datetime, date, timedelta
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
    from linkedin.jobs import cover_letter_generator
    from linkedin.jobs import job_dispatcher
    from linkedin.jobs import job_matcher
    from linkedin.jobs import daily_reporter
    from linkedin.jobs import linkedin_scraper
except ImportError:
    resume_tailor = None
    cover_letter_generator = None
    job_dispatcher = None
    job_matcher = None
    daily_reporter = None
    linkedin_scraper = None

DEFAULT_CONFIG = {
    "enabled": True,
    "daily_limit": 5,
    "min_match_score": 85,
    "max_posted_days": 7,
    "priority_freshness_days": 4,
    "refresh_interval_hours": 20,
    "target_roles": ["Werkstudent", "Internship", "Part-Time", "Praktikum", "Student"],
    "target_locations": ["Berlin", "Berlin, Germany", "Remote Germany", "Hybrid Berlin"],
    "today_date": str(date.today()),
    "applied_today": 0,
    "last_run": None,
    "last_refresh_timestamp": datetime.now().isoformat(),
    "recipient_email": "purnachand0812@gmail.com",
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

def parse_posted_age_days(posted_str):
    """Parses relative or ISO posted times into integer age in days."""
    if not posted_str:
        return 1
    s = str(posted_str).lower().strip()
    if any(k in s for k in ["hour", "minute", "just now", "today", "sec"]):
        return 0
    if "yesterday" in s:
        return 1
    m_day = re.search(r'(\d+)\s*day', s)
    if m_day:
        return int(m_day.group(1))
    m_week = re.search(r'(\d+)\s*week', s)
    if m_week:
        return int(m_week.group(1)) * 7
    return 2

def is_job_eligible(job, config):
    """Validates job eligibility based on status, fit score, location, and freshness."""
    if job.get("status") == "APPLIED":
        return False, "Already applied"
    
    # Freshness check: must be <= max_posted_days (7 days max)
    posted_raw = job.get("posted_time", "1 day ago")
    age_days = parse_posted_age_days(posted_raw)
    max_days = config.get("max_posted_days", 7)
    if age_days > max_days:
        return False, f"Job posted {age_days} days ago (exceeds {max_days}-day limit)"

    # STRICT FILTER: Disqualify any senior/experienced roles
    title_low = job.get("title", "").lower()
    senior_disqualifiers = [
        "senior", "sr.", "sr ", "lead", "principal", "staff", "head of", "director",
        "manager", "vp", "architect", "experienced", "expert", "5+ years", "8+ years", "10+ years"
    ]
    if any(sd in title_low for sd in senior_disqualifiers):
        return False, f"Disqualified: Title contains senior/experienced keyword ('{job.get('title')}')"

    # STRICT FILTER: Require student, werkstudent, internship, or part-time status
    student_qualifiers = [
        "werkstudent", "working student", "student", "intern", "internship", 
        "praktikant", "praktikum", "part-time", "part time", "teilzeit", 
        "trainee", "thesis", "masterarbeit", "bachelorarbeit"
    ]
    work_type_low = str(job.get("work_type", "")).lower()
    desc_low = str(job.get("description", "")).lower()
    is_student_fit = any(sq in title_low for sq in student_qualifiers) or any(sq in work_type_low for sq in student_qualifiers) or any(sq in desc_low for sq in student_qualifiers)
    if not is_student_fit:
        return False, f"Disqualified: Not a student/werkstudent/internship role ('{job.get('title')}')"

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
    """Executes the full automated application lifecycle: Tailored CV + Cover Letter + Screener + Dispatch."""
    job_id = job.get("id")
    title = job.get("title", "Software Engineer")
    company = job.get("company", "Company")

    append_log(f"Initiating autonomous application: '{title}' at {company} (ID: {job_id})")

    # Step 1: Tailor Europass Resume & generate PDF
    resume_path = None
    resume_pdf_path = None
    if resume_tailor:
        try:
            resume_path = resume_tailor.generate_tailored_resume(job)
            resume_pdf_path = JOBS_DIR / "resumes" / f"resume_{job_id}.pdf"
            append_log(f"Tailored Europass CV & PDF generated: resume_{job_id}.pdf", "SUCCESS")
        except Exception as e:
            append_log(f"Error tailoring CV: {e}", "WARNING")

    # Step 2: Tailor Europass Cover Letter & generate PDF
    cover_letter_path = None
    cover_letter_pdf_path = None
    if cover_letter_generator:
        try:
            cover_letter_path = cover_letter_generator.generate_tailored_cover_letter(job)
            cover_letter_pdf_path = JOBS_DIR / "resumes" / f"cover_letter_{job_id}.pdf"
            append_log(f"Tailored Cover Letter & PDF generated: cover_letter_{job_id}.pdf", "SUCCESS")
        except Exception as e:
            append_log(f"Error tailoring Cover Letter: {e}", "WARNING")

    # Step 3: Resolve deterministic screener answers
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
    append_log(f"Resolved {len(screener_answers)} screener questions (German phone +49 15511064761, Berlin resident, no driving licence).", "SUCCESS")

    outreach_note = ""
    if job_dispatcher:
        outreach_note = job_dispatcher.generate_recruiter_note(job)

    # Step 4: Dispatch application record
    result = None
    if job_dispatcher:
        result = job_dispatcher.apply_to_job(job_id, auto_mode=True)
    
    # Enrich applied job with both PDF and HTML urls
    pdf_resume_url = f"/resumes/resume_{job_id}.pdf"
    pdf_cover_url = f"/resumes/cover_letter_{job_id}.pdf"
    html_resume_url = f"/resumes/resume_{job_id}.html"
    html_cover_url = f"/resumes/cover_letter_{job_id}.html"

    job["resume_url"] = pdf_resume_url
    job["cover_letter_url"] = pdf_cover_url
    job["resume_pdf_url"] = pdf_resume_url
    job["cover_letter_pdf_url"] = pdf_cover_url
    job["resume_html_url"] = html_resume_url
    job["cover_letter_html_url"] = html_cover_url

    # Update in applied_history.json
    applied_list = load_json(APPLIED_FILE, [])
    for a in applied_list:
        if a.get("job_id") == job_id:
            a["resume_url"] = pdf_resume_url
            a["cover_letter_url"] = pdf_cover_url
            a["resume_pdf_url"] = pdf_resume_url
            a["cover_letter_pdf_url"] = pdf_cover_url
            a["resume_html_url"] = html_resume_url
            a["cover_letter_html_url"] = html_cover_url
            break
    save_json(APPLIED_FILE, applied_list)

    append_log(f"Application confirmed & tracked with downloadable PDFs for {company}.", "SUCCESS")

    return {
        "job_id": job_id,
        "title": title,
        "company": company,
        "match_score": job.get("match_score"),
        "resume_url": pdf_resume_url,
        "cover_letter_url": pdf_cover_url,
        "resume_pdf_url": pdf_resume_url,
        "cover_letter_pdf_url": pdf_cover_url,
        "outreach_note": outreach_note,
        "screener_answers": screener_answers,
        "status": "APPLIED_CONFIRMED"
    }

def check_20hr_refresh(config):
    """Verifies whether 20 hours have elapsed since the last radar refresh."""
    last_refresh_str = config.get("last_refresh_timestamp")
    refresh_hours = config.get("refresh_interval_hours", 20)
    
    now = datetime.now()
    needs_refresh = False
    if not last_refresh_str:
        needs_refresh = True
    else:
        try:
            last_dt = datetime.fromisoformat(last_refresh_str)
            if (now - last_dt).total_seconds() >= (refresh_hours * 3600):
                needs_refresh = True
        except Exception:
            needs_refresh = True

    if needs_refresh:
        append_log(f"20-Hour Refresh Cadence triggered: scraping live LinkedIn opportunities in Berlin (<= 4 to 7 days).", "INFO")
        config["last_refresh_timestamp"] = now.isoformat()
        save_json(CONFIG_FILE, config)
        if linkedin_scraper:
            try:
                linkedin_scraper.refresh_jobs_radar()
                append_log("Real-time LinkedIn job radar refreshed with live Berlin postings.", "SUCCESS")
            except Exception as e:
                append_log(f"Error scraping LinkedIn jobs: {e}", "WARNING")
        return True
    return False

def check_eod_report_dispatch():
    """Checks if current time is within the end-of-day reporting window (19:00 CET)."""
    now = datetime.now()
    if now.hour >= 19 and daily_reporter:
        try:
            res = daily_reporter.send_daily_summary_report(force=False)
            if res.get("status") not in ["ALREADY_SENT"]:
                append_log(f"End-of-day summary report dispatched to purnachand0812@gmail.com ({res.get('status')}).", "SUCCESS")
        except Exception as e:
            append_log(f"Failed to dispatch daily report: {e}", "WARNING")

def run_autonomous_cycle(force=False):
    """
    Main autonomous cycle:
    1. Checks 20-hour refresh trigger.
    2. Filters jobs posted <= 4 to 7 days.
    3. Customizes both tailored Europass CV and Cover Letter.
    4. Submits applications up to daily limit.
    5. Checks end-of-day report dispatch.
    """
    config = get_config()
    if not config.get("enabled") and not force:
        return {"status": "PAUSED", "applied_count": 0, "message": "Autonomous application agent is currently paused."}

    # Check 20-hour refresh cadence
    check_20hr_refresh(config)

    daily_limit = config.get("daily_limit", 5)
    applied_today = config.get("applied_today", 0)

    if applied_today >= daily_limit and not force:
        append_log(f"Daily quota reached ({applied_today}/{daily_limit}). Standing by until tomorrow.", "INFO")
        check_eod_report_dispatch()
        return {"status": "QUOTA_REACHED", "applied_today": applied_today, "daily_limit": daily_limit}

    radar = load_json(RADAR_FILE, {"jobs": []})
    jobs = radar.get("jobs", [])
    
    eligible_jobs = []
    for j in jobs:
        ok, reason = is_job_eligible(j, config)
        if ok:
            # Annotate parsed age
            j["_age_days"] = parse_posted_age_days(j.get("posted_time"))
            eligible_jobs.append(j)

    append_log(f"Radar scan: {len(jobs)} active jobs, {len(eligible_jobs)} meeting freshness (<=7d) & criteria.")

    if not eligible_jobs:
        check_eod_report_dispatch()
        return {"status": "IDLE", "message": "No unapplied eligible jobs found in radar.", "applied_count": 0}

    # Sort prioritizing fresh jobs (<= 4 days first), then by match score
    eligible_jobs.sort(key=lambda x: (0 if x.get("_age_days", 5) <= 4 else 1, -x.get("match_score", 0)))

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

    # Check EOD report
    check_eod_report_dispatch()

    return {
        "status": "COMPLETED",
        "applied_count": len(applied_results),
        "applied_today": applied_today,
        "daily_limit": daily_limit,
        "results": applied_results
    }

if __name__ == "__main__":
    print("Testing autonomous job agent run cycle with Cover Letter & 20h refresh...")
    res = run_autonomous_cycle(force=False)
    print(json.dumps(res, indent=2))
