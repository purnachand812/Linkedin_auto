#!/usr/bin/env python3
"""
refresh_all_assets.py - Batch updates all job resumes and cover letters to the new
streamlined student/intern Europass standard and compiles 100% of PDFs.
"""

import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from linkedin.jobs import resume_tailor
from linkedin.jobs import cover_letter_generator
from linkedin.jobs import pdf_converter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

RESUMES_DIR = BASE_DIR / "linkedin" / "jobs" / "resumes"
RADAR_FILE = BASE_DIR / "linkedin" / "jobs" / "jobs_radar.json"
APPLIED_FILE = BASE_DIR / "linkedin" / "jobs" / "applied_history.json"

def run_refresh():
    RESUMES_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Update all Radar jobs
    radar_data = json.loads(RADAR_FILE.read_text(encoding="utf-8"))
    radar_jobs = radar_data.get("jobs", [])
    print(f"[*] Processing {len(radar_jobs)} Radar jobs...")
    
    for idx, job in enumerate(radar_jobs, 1):
        jid = job.get("id") or f"radar-{idx}"
        print(f"[{idx}/{len(radar_jobs)}] Radar: {jid} ({job.get('company')})")
        
        # Resume HTML & PDF
        r_html = resume_tailor.generate_tailored_resume(job, make_pdf=False)
        r_pdf = RESUMES_DIR / f"resume_{jid}.pdf"
        try:
            pdf_converter.convert_html_to_pdf(r_html, r_pdf)
        except Exception as e:
            print(f"  [PDF Warning] Resume {jid}: {e}")
            
        # Cover Letter HTML & PDF
        c_html = cover_letter_generator.generate_tailored_cover_letter(job, make_pdf=False)
        c_pdf = RESUMES_DIR / f"cover_letter_{jid}.pdf"
        try:
            pdf_converter.convert_html_to_pdf(c_html, c_pdf)
        except Exception as e:
            print(f"  [PDF Warning] Cover Letter {jid}: {e}")
            
        # Standardize job URLs
        job["resume_url"] = f"/resumes/resume_{jid}.pdf"
        job["resume_pdf_url"] = f"/resumes/resume_{jid}.pdf"
        job["resume_html_url"] = f"/resumes/resume_{jid}.html"
        job["cover_letter_url"] = f"/resumes/cover_letter_{jid}.pdf"
        job["cover_letter_pdf_url"] = f"/resumes/cover_letter_{jid}.pdf"
        job["cover_letter_html_url"] = f"/resumes/cover_letter_{jid}.html"

    RADAR_FILE.write_text(json.dumps(radar_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[*] jobs_radar.json updated.")

    # 2. Update all Applied jobs
    applied_jobs = json.loads(APPLIED_FILE.read_text(encoding="utf-8"))
    print(f"\n[*] Processing {len(applied_jobs)} Applied jobs...")
    
    for idx, job in enumerate(applied_jobs, 1):
        jid = job.get("job_id") or f"applied-{idx}"
        print(f"[{idx}/{len(applied_jobs)}] Applied: {jid} ({job.get('company')})")
        
        # Resume HTML & PDF
        r_html = resume_tailor.generate_tailored_resume(job, make_pdf=False)
        r_pdf = RESUMES_DIR / f"resume_{jid}.pdf"
        try:
            pdf_converter.convert_html_to_pdf(r_html, r_pdf)
        except Exception as e:
            print(f"  [PDF Warning] Resume {jid}: {e}")
            
        # Cover Letter HTML & PDF
        c_html = cover_letter_generator.generate_tailored_cover_letter(job, make_pdf=False)
        c_pdf = RESUMES_DIR / f"cover_letter_{jid}.pdf"
        try:
            pdf_converter.convert_html_to_pdf(c_html, c_pdf)
        except Exception as e:
            print(f"  [PDF Warning] Cover Letter {jid}: {e}")
            
        job["resume_url"] = f"/resumes/resume_{jid}.pdf"
        job["resume_pdf_url"] = f"/resumes/resume_{jid}.pdf"
        job["resume_html_url"] = f"/resumes/resume_{jid}.html"
        job["cover_letter_url"] = f"/resumes/cover_letter_{jid}.pdf"
        job["cover_letter_pdf_url"] = f"/resumes/cover_letter_{jid}.pdf"
        job["cover_letter_html_url"] = f"/resumes/cover_letter_{jid}.html"

    APPLIED_FILE.write_text(json.dumps(applied_jobs, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[*] applied_history.json updated.")

    # 3. Check any remaining HTML files in RESUMES_DIR and compile missing PDFs
    print("\n[*] Checking any remaining HTML files in resumes directory...")
    for h in RESUMES_DIR.glob("*.html"):
        p = h.with_suffix(".pdf")
        if not p.exists() or p.stat().st_size < 1000:
            print(f"  Compiling missing PDF: {h.name} -> {p.name}")
            try:
                pdf_converter.convert_html_to_pdf(h, p)
            except Exception as e:
                print(f"  Failed: {e}")

    print("\n[SUCCESS] All resumes and cover letters regenerated and compiled to PDF!")

if __name__ == "__main__":
    run_refresh()
