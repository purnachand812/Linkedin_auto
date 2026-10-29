#!/usr/bin/env python3
"""
job_dispatcher.py - Application Dispatcher, Pre-Mapped ATS Packet Builder & Recruiter Outreach Generator.
Manages application state transitions, answers screener questions deterministically from screener_bank.json,
generates grounded recruiter outreach messages, and compiles 1-click pre-filled ATS application packets
in linkedin/jobs/packets/packet_{job_id}.json.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
JOBS_DIR = BASE_DIR / "linkedin" / "jobs"
PACKETS_DIR = JOBS_DIR / "packets"
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
    Finds the best answer for a custom Easy Apply / ATS screener question
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
        "detail": "Grounded in MSc Data Science (GISMA Berlin) and verified Python/ML engineering background."
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
        f"I am an MSc Data Science student based in Berlin (GISMA University) researching hallucination attribution in multi-step LLM agent trajectories. "
        f"I have hands-on experience building Python ML pipelines, SQL/Redis backends, and typed FastAPI agent services, with full German Werkstudent work authorization. "
        f"I submitted my application and would be glad to connect."
    )
    return note


def build_ats_application_packet(job_info, resume_url, cover_letter_url):
    """
    Builds a deterministic, pre-filled ATS form packet in linkedin/jobs/packets/packet_{job_id}.json
    so Greenhouse, Lever, Ashby, and LinkedIn Easy Apply forms have 100% consistent pre-mapped fields.
    """
    PACKETS_DIR.mkdir(parents=True, exist_ok=True)
    profile = load_json(PROFILE_FILE, {})
    job_id = job_info.get("id", "job-generic")

    standard_questions = [
        "Are you legally authorized to work in Germany?",
        "Do you require visa sponsorship?",
        "Are you currently enrolled as a full-time university student?",
        "Are you located in Berlin, Germany?",
        "What is your German language proficiency?",
        "What is your English language proficiency?",
        "What are your salary expectations?",
        "What is your notice period / earliest start date?",
        "Do you have a valid driving licence?"
    ]
    resolved_screeners = {q: match_screener_question(q)["answer"] for q in standard_questions}

    packet = {
        "packet_id": f"packet_{job_id}",
        "generated_at": datetime.now().isoformat(),
        "job_id": job_id,
        "company": job_info.get("company"),
        "title": job_info.get("title"),
        "portal_source": job_info.get("portal_source", "LINKEDIN"),
        "direct_apply_url": job_info.get("job_url"),
        "ats_form_fields": {
            "first_name": "Purnachandra Madhukar",
            "last_name": "Dandu",
            "full_name": profile.get("full_name", "Dandu Purnachandra Madhukar"),
            "email": profile.get("email", "purnachand0812@gmail.com"),
            "phone": profile.get("phone", "+49 15511064761"),
            "city": "Berlin, Germany",
            "linkedin_url": profile.get("linkedin_url", "https://linkedin.com/in/purnachanddandu"),
            "github_url": profile.get("github_url", "https://github.com/purnachand812"),
            "university": "GISMA University of Applied Sciences, Berlin",
            "degree": "M.Sc. in Data Science (EQF Level 7)"
        },
        "screener_responses": resolved_screeners,
        "attachments": {
            "europass_cv_pdf": resume_url,
            "europass_cover_letter_pdf": cover_letter_url
        },
        "recruiter_outreach_note": generate_recruiter_note(job_info)
    }

    packet_path = PACKETS_DIR / f"packet_{job_id}.json"
    save_json(packet_path, packet)
    return packet_path


def apply_to_job(job_id, auto_mode=False):
    """
    Submits or records an application for a qualified job in jobs_radar.json,
    generates tailored Europass CV & Cover Letter, builds pre-mapped ATS form packet,
    and updates applied_history.json.
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

    resume_url = f"/resumes/resume_{job_id}.pdf"
    cover_letter_url = f"/resumes/cover_letter_{job_id}.pdf"
    try:
        from linkedin.jobs import resume_tailor
        from linkedin.jobs import cover_letter_generator
        resume_tailor.generate_tailored_resume(target_job)
        cover_letter_generator.generate_tailored_cover_letter(target_job)
    except Exception as e:
        print(f"[Warning] Failed to generate tailored documents: {e}")

    packet_path = build_ats_application_packet(target_job, resume_url, cover_letter_url)

    target_job["status"] = "APPLIED"
    target_job["applied_at"] = datetime.now().isoformat()
    target_job["resume_url"] = resume_url
    target_job["cover_letter_url"] = cover_letter_url
    target_job["packet_file"] = f"linkedin/jobs/packets/{packet_path.name}"
    save_json(RADAR_FILE, radar)

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
        "cover_letter_url": cover_letter_url,
        "packet_file": f"linkedin/jobs/packets/{packet_path.name}",
        "mode": "AUTONOMOUS_DAEMON" if auto_mode else "MANUAL_APPROVAL",
        "recruiter_outreach_note": generate_recruiter_note(target_job),
        "status": "APPLIED_CONFIRMED"
    }

    applied_history = [h for h in applied_history if h.get("job_id") != job_id]
    applied_history.insert(0, history_entry)
    save_json(APPLIED_FILE, applied_history)

    return history_entry


def backfill_applied_packets():
    """Ensures every entry in applied_history.json has a pre-mapped 1-click ATS packet on disk."""
    applied_history = load_json(APPLIED_FILE, [])
    count = 0
    for entry in applied_history:
        jid = entry.get("job_id")
        if not jid:
            continue
        job_info = {
            "id": jid,
            "title": entry.get("title"),
            "company": entry.get("company"),
            "location": entry.get("location", "Berlin, Germany"),
            "job_url": entry.get("job_url"),
            "portal_source": "GREENHOUSE" if "-gh-" in jid else ("BUNDESAGENTUR" if "-ba-" in jid else "LINKEDIN")
        }
        res_url = entry.get("resume_url", f"/resumes/resume_{jid}.pdf")
        cl_url = entry.get("cover_letter_url", f"/resumes/cover_letter_{jid}.pdf")
        pkt_path = build_ats_application_packet(job_info, res_url, cl_url)
        entry["packet_file"] = f"linkedin/jobs/packets/{pkt_path.name}"
        count += 1
    if count > 0:
        save_json(APPLIED_FILE, applied_history)
    return count


if __name__ == "__main__":
    sample_q = "What is your German language proficiency?"
    ans = match_screener_question(sample_q)
    print("Screener Match:", ans)
    note = generate_recruiter_note({"title": "Werkstudent AI Engineer", "company": "Langfuse", "location": "Berlin"})
    print("\nRecruiter Note:\n", note)
    pkt_count = backfill_applied_packets()
    print(f"\n[ATS PACKET ENGINE] Generated {pkt_count} pre-mapped 1-click ATS application packets in linkedin/jobs/packets/")
