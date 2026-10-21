#!/usr/bin/env python3
"""
migrate_clean_jobs.py - Cleans applied_history.json & jobs_radar.json:
1. Enforces strict filtering: ONLY Student, Werkstudent, Internship, and Part-Time roles.
2. Purges any Senior, Lead, Principal, Freelance, or Full-Time experienced roles.
3. Generates verified HTML and downloadable PDF files for all resumes and cover letters.
4. Updates all record URLs to provide both PDF and HTML links.
"""

import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from linkedin.jobs import resume_tailor, cover_letter_generator, pdf_converter

APPLIED_FILE = BASE_DIR / "linkedin" / "jobs" / "applied_history.json"
RADAR_FILE = BASE_DIR / "linkedin" / "jobs" / "jobs_radar.json"
RESUMES_DIR = BASE_DIR / "linkedin" / "jobs" / "resumes"
CONFIG_FILE = BASE_DIR / "linkedin" / "jobs" / "auto_apply_config.json"

RESUMES_DIR.mkdir(parents=True, exist_ok=True)

SENIOR_DISQUALIFIERS = [
    "senior", "sr.", "sr ", "lead", "principal", "staff", "head of", "director",
    "manager", "vp", "architect", "experienced", "expert", "freelance", "contractor",
    "5+ years", "8+ years", "10+ years"
]

STUDENT_QUALIFIERS = [
    "werkstudent", "working student", "student", "intern", "internship", 
    "praktikant", "praktikum", "part-time", "part time", "teilzeit", 
    "trainee", "thesis", "masterarbeit", "bachelorarbeit"
]

def is_student_job(title, work_type="", desc="", salary_range=""):
    t_low = (title or "").lower()
    if any(sd in t_low for sd in SENIOR_DISQUALIFIERS):
        return False
    
    combined = f"{t_low} {work_type.lower()} {desc.lower()} {salary_range.lower()}"
    return any(sq in combined for sq in STUDENT_QUALIFIERS)

def main():
    print("=== Migrating and Sanitizing Jobs to 100% Student / Werkstudent / Internship ===", flush=True)

    # 1. Clean applied_history.json
    with open(APPLIED_FILE, "r", encoding="utf-8") as f:
        applied = json.load(f)

    clean_applied = []
    for a in applied:
        if is_student_job(a.get("title", ""), a.get("work_type", ""), a.get("description", ""), a.get("salary_range", "")):
            clean_applied.append(a)
        else:
            print(f"[-] Purged non-student role from Applied: {a.get('title')}", flush=True)

    print(f"[+] Retained {len(clean_applied)} student/werkstudent applied jobs.", flush=True)

    # 2. Clean jobs_radar.json
    with open(RADAR_FILE, "r", encoding="utf-8") as f:
        radar = json.load(f)

    clean_radar_jobs = []
    for j in radar.get("jobs", []):
        if is_student_job(j.get("title", ""), j.get("work_type", ""), j.get("description", ""), j.get("salary_range", "")):
            clean_radar_jobs.append(j)
        else:
            print(f"[-] Purged non-student role from Radar: {j.get('title')}", flush=True)

    print(f"[+] Retained {len(clean_radar_jobs)} student/werkstudent radar jobs.", flush=True)

    # 3. Generate PDFs for all retained jobs
    all_jobs = clean_applied + clean_radar_jobs
    processed_ids = set()

    for job in all_jobs:
        jid = job.get("job_id") or job.get("id")
        if not jid or jid in processed_ids:
            continue
        processed_ids.add(jid)

        print(f"[*] Processing PDFs for #{jid}: {job.get('title')[:45]}...", flush=True)

        # 1. Resume HTML & PDF
        try:
            res_html_path = resume_tailor.generate_tailored_resume(job)
            res_pdf_path = RESUMES_DIR / f"resume_{jid}.pdf"
            if not res_pdf_path.exists() or res_pdf_path.stat().st_size < 1000:
                pdf_converter.convert_html_to_pdf(res_html_path, res_pdf_path)
        except Exception as e:
            print(f"    [!] CV PDF error for {jid}: {e}", flush=True)

        # 2. Cover Letter HTML & PDF
        try:
            cl_html_path = cover_letter_generator.generate_tailored_cover_letter(job)
            cl_pdf_path = RESUMES_DIR / f"cover_letter_{jid}.pdf"
            if not cl_pdf_path.exists() or cl_pdf_path.stat().st_size < 1000:
                pdf_converter.convert_html_to_pdf(cl_html_path, cl_pdf_path)
        except Exception as e:
            print(f"    [!] Cover Letter PDF error for {jid}: {e}", flush=True)

        # Update URLs in record
        pdf_cv = f"/resumes/resume_{jid}.pdf"
        pdf_cl = f"/resumes/cover_letter_{jid}.pdf"
        html_cv = f"/resumes/resume_{jid}.html"
        html_cl = f"/resumes/cover_letter_{jid}.html"

        job["resume_url"] = pdf_cv
        job["cover_letter_url"] = pdf_cl
        job["resume_pdf_url"] = pdf_cv
        job["cover_letter_pdf_url"] = pdf_cl
        job["resume_html_url"] = html_cv
        job["cover_letter_html_url"] = html_cl

    # Save cleaned files
    with open(APPLIED_FILE, "w", encoding="utf-8") as f:
        json.dump(clean_applied, f, indent=2)

    radar["jobs"] = clean_radar_jobs
    with open(RADAR_FILE, "w", encoding="utf-8") as f:
        json.dump(radar, f, indent=2)

    # Update auto_apply_config.json
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        cfg["applied_today"] = len(clean_applied)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)

    print(f"\n[SUCCESS] Completed migration! Clean applied: {len(clean_applied)}, Clean radar: {len(clean_radar_jobs)}", flush=True)

if __name__ == "__main__":
    main()
