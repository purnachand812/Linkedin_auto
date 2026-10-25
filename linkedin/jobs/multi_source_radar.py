#!/usr/bin/env python3
"""
multi_source_radar.py - Unified Multi-Portal Job Opportunity Engine.
Orchestrates live harvesting from 3 complementary channels:
1. Direct ATS APIs (Greenhouse & Lever) for Berlin tech companies & scale-ups
2. Official Bundesagentur für Arbeit REST API (v6) for verified German Werkstudent contracts
3. LinkedIn Public Job Index (Easy Apply Berlin)

Harmonizes, deduplicates, scores (100-pt ATS fit), and auto-generates
tailored Europass CVs and individualized cover letters.
"""

import os
import sys
import re
import json
import time
from datetime import datetime, date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
JOBS_DIR = BASE_DIR / "linkedin" / "jobs"
RADAR_FILE = JOBS_DIR / "jobs_radar.json"
APPLIED_FILE = JOBS_DIR / "applied_history.json"
RESUMES_DIR = JOBS_DIR / "resumes"

sys.path.insert(0, str(BASE_DIR))

try:
    from linkedin.jobs import linkedin_scraper
    from linkedin.jobs import ats_connector
    from linkedin.jobs import bundesagentur_connector
    from linkedin.jobs import resume_tailor
    from linkedin.jobs import cover_letter_generator
    from linkedin.jobs import pdf_converter
except ImportError:
    linkedin_scraper = None
    ats_connector = None
    bundesagentur_connector = None
    resume_tailor = None
    cover_letter_generator = None
    pdf_converter = None

def load_applied_ids():
    applied_ids = set()
    if APPLIED_FILE.exists():
        try:
            with open(APPLIED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for entry in data:
                    if "job_id" in entry:
                        applied_ids.add(str(entry["job_id"]))
                    if "numeric_id" in entry:
                        applied_ids.add(str(entry["numeric_id"]))
        except Exception:
            pass
    return applied_ids

def deduplicate_jobs(jobs):
    """Deduplicates jobs by company + normalized title."""
    seen = set()
    unique = []
    for j in jobs:
        comp_clean = re.sub(r'[^a-zA-Z0-9]', '', (j.get("company") or "").lower())
        title_clean = re.sub(r'[^a-zA-Z0-9]', '', (j.get("title") or "").lower()[:25])
        key = f"{comp_clean}:{title_clean}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(j)
    return unique

def generate_documents_for_job(job, convert_pdf=False):
    """Generates tailored HTML for a single job instantly, with optional PDF conversion."""
    job_id = job.get("id")
    if not job_id:
        return

    try:
        # 1. Resume HTML (Instant ~2ms)
        res_html = resume_tailor.generate_tailored_resume(job)
        # 2. Cover Letter HTML (Instant ~2ms)
        cov_html = cover_letter_generator.generate_tailored_cover_letter(job)

        # 3. PDF generation if requested
        if convert_pdf and pdf_converter:
            res_pdf = Path(res_html).with_suffix(".pdf")
            if not res_pdf.exists() or res_pdf.stat().st_size < 1000:
                try:
                    pdf_converter.convert_html_to_pdf(res_html)
                except Exception as e:
                    print(f"[Warning] PDF resume conversion for {job_id}: {e}")

            cov_pdf = Path(cov_html).with_suffix(".pdf")
            if not cov_pdf.exists() or cov_pdf.stat().st_size < 1000:
                try:
                    pdf_converter.convert_html_to_pdf(cov_html)
                except Exception as e:
                    print(f"[Warning] PDF cover letter conversion for {job_id}: {e}")
    except Exception as e:
        print(f"[Document Engine Warning] Could not generate docs for {job_id}: {e}")

def _background_pdf_sync(jobs):
    """Background worker to ensure missing PDFs are compiled without blocking user response."""
    import threading
    def _worker():
        for j in jobs:
            try:
                generate_documents_for_job(j, convert_pdf=True)
            except Exception:
                pass
    t = threading.Thread(target=_worker, daemon=True)
    t.start()

def refresh_multi_source_radar(max_total=18):
    """
    Refreshes jobs_radar.json by concurrently aggregating:
    - Direct ATS (Greenhouse & Lever)
    - Bundesagentur für Arbeit (Official Gov Index)
    - LinkedIn Easy Apply
    """
    start_t = time.time()
    print("[MULTI-RADAR] Initiating 360-degree Berlin Job Discovery concurrently...")
    applied_ids = load_applied_ids()
    all_harvested = []

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def harvest_ats():
        if not ats_connector:
            return []
        try:
            return ats_connector.harvest_all_ats_jobs(max_results=7)
        except Exception as e:
            print(f"[MULTI-RADAR] ATS Harvester error: {e}")
            return []

    def harvest_ba():
        if not bundesagentur_connector:
            return []
        try:
            return bundesagentur_connector.harvest_bundesagentur_jobs(max_results=7)
        except Exception as e:
            print(f"[MULTI-RADAR] Bundesagentur Harvester error: {e}")
            return []

    def harvest_li():
        if not linkedin_scraper:
            return []
        try:
            jobs = linkedin_scraper.scrape_real_linkedin_jobs(max_results=6, max_days=7)
            for j in jobs:
                j["portal_source"] = "LINKEDIN"
                j["portal_name"] = "LinkedIn Easy Apply"
                j["source_badge"] = "LinkedIn"
            return jobs
        except Exception as e:
            print(f"[MULTI-RADAR] LinkedIn Scraper error: {e}")
            return []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futs = [
            executor.submit(harvest_ats),
            executor.submit(harvest_ba),
            executor.submit(harvest_li)
        ]
        for fut in as_completed(futs):
            try:
                res = fut.result()
                if res:
                    all_harvested.extend(res)
            except Exception:
                pass

    if not all_harvested:
        print("[MULTI-RADAR WARNING] No jobs fetched from any portal. Keeping existing radar.")
        return False

    # Deduplicate
    unique_jobs = deduplicate_jobs(all_harvested)

    # Mark status against applied history
    for j in unique_jobs:
        j_id = str(j.get("id", ""))
        num_id = str(j.get("numeric_id", ""))
        if j_id in applied_ids or num_id in applied_ids:
            j["status"] = "APPLIED"
        else:
            j["status"] = "OPEN"

    # Sort primarily by match score descending, then posted days ascending
    unique_jobs.sort(key=lambda x: (x.get("match_score", 0), -x.get("posted_days", 1)), reverse=True)
    selected_jobs = unique_jobs[:max_total]

    # Generate tailored HTML assets instantly (~30ms)
    print(f"[MULTI-RADAR] Generating tailored Europass CVs & Cover Letters for {len(selected_jobs)} positions...")
    for j in selected_jobs:
        generate_documents_for_job(j, convert_pdf=False)

    # Background PDF sync (non-blocking)
    _background_pdf_sync(selected_jobs)

    radar_payload = {
        "updated_at": datetime.now().isoformat(),
        "portal_counts": {
            "DIRECT_ATS": len([j for j in selected_jobs if j.get("portal_source") == "DIRECT_ATS"]),
            "BUNDESAGENTUR": len([j for j in selected_jobs if j.get("portal_source") == "BUNDESAGENTUR"]),
            "LINKEDIN": len([j for j in selected_jobs if j.get("portal_source") == "LINKEDIN"])
        },
        "active_search_filters": {
            "sources": [
                "Direct ATS (Greenhouse & Lever APIs)",
                "Bundesagentur für Arbeit (Official Gov v6 API)",
                "LinkedIn Public Index (Easy Apply)"
            ],
            "target_geo": "Berlin, Germany",
            "roles": [
                "Werkstudent Data Science",
                "Werkstudent Machine Learning",
                "Werkstudent AI",
                "Data Science Intern",
                "Working Student Python",
                "Working Student Analytics"
            ]
        },
        "jobs": selected_jobs
    }

    RADAR_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RADAR_FILE, "w", encoding="utf-8") as f:
        json.dump(radar_payload, f, indent=2)

    print(f"[MULTI-RADAR SUCCESS] Saved {len(selected_jobs)} cross-portal opportunities to jobs_radar.json!")
    return True

if __name__ == '__main__':
    refresh_multi_source_radar()
