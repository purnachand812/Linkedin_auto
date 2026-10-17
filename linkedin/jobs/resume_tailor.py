#!/usr/bin/env python3
"""
resume_tailor.py - Dynamic Official Europass 2-Page CV Generator for Dandu Purnachandra Madhukar.
Generates authentic European Union Europass CVs matching the European Commission Ares(2022)2356242 reference,
with CEFR language matrix, digital competence grid, verified work experience, and job-tailored project highlights.
"""

import os
import sys
import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
JOBS_DIR = BASE_DIR / "linkedin" / "jobs"
RESUMES_DIR = JOBS_DIR / "resumes"
PROFILE_FILE = JOBS_DIR / "profile_master.json"

def load_profile():
    if PROFILE_FILE.exists():
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def generate_tailored_resume(job_info):
    """
    Generates a tailored official European Union Europass 2-page CV emphasizing the skills and projects
    most relevant to the targeted job.
    Returns: file path to generated HTML resume.
    """
    RESUMES_DIR.mkdir(parents=True, exist_ok=True)
    profile = load_profile()
    
    job_id = job_info.get("id", "job-generic")
    title = job_info.get("title", "Data Scientist & ML Engineer")
    company = job_info.get("company", "Company")
    location = job_info.get("location", "Berlin, Germany")
    tech_stack = [t.lower() for t in job_info.get("tech_stack", [])]

    # Re-order projects so the most relevant project is first
    projects = list(profile.get("verified_projects", []))
    def project_relevance(p):
        score = 0
        p_tech = [t.lower() for t in p.get("technologies", [])]
        for t in tech_stack:
            if any(t in pt for pt in p_tech):
                score += 1
        return score

    projects.sort(key=project_relevance, reverse=True)

    # Format projects based on relevance
    projects_html = ""
    for idx, p in enumerate(projects[:3], 1):
        techs = ", ".join(p.get("technologies", []))
        projects_html += f"""
              <li><strong>{p.get('name')}:</strong> {p.get('description')} &bull; <strong>Impact:</strong> {p.get('impact')} <em>(Tech: {techs})</em></li>"""

    full_name = profile.get("full_name", "Dandu Purnachandra Madhukar")
    email = profile.get("email", "purnachand0812@gmail.com")
    phone = profile.get("phone", "+91 7288073766")
    linkedin_url = profile.get("linkedin_url", "https://linkedin.com/in/purnachanddandu")
    github_url = profile.get("github_url", "https://github.com/purnachand812")
    profile_summary = profile.get("profile_summary", (
        "Results-driven Software Engineer transitioning into Data Science, with 1+ year of production engineering "
        "experience delivering measurable business impact. Skilled in Python, Machine Learning, SQL, and full-stack "
        "development. Incoming MSc Data Science student at GISMA University Berlin. Seeking a Werkstudent role in Data Science or Machine Learning in Berlin."
    ))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Europass CV - {full_name} ({company} - {title})</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700;800&display=swap" rel="stylesheet">
  <style>
    @page {{
      size: A4 portrait;
      margin: 10mm 14mm 12mm 14mm;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: 'Open Sans', Arial, Helvetica, sans-serif;
      font-size: 8.5pt;
      color: #222222;
      line-height: 1.35;
      background-color: #f1f5f9;
      padding: 20px 0;
      -webkit-font-smoothing: antialiased;
    }}
    .cv-page {{
      width: 210mm;
      min-height: 297mm;
      margin: 0 auto 20px auto;
      background: #ffffff;
      padding: 14mm 16mm 14mm 16mm;
      box-shadow: 0 4px 15px rgba(0,0,0,0.1);
      position: relative;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    @media print {{
      body {{
        background: transparent !important;
        padding: 0 !important;
      }}
      .cv-page {{
        margin: 0 !important;
        padding: 8mm 12mm !important;
        box-shadow: none !important;
        width: 100% !important;
        min-height: auto !important;
        page-break-after: always;
      }}
      .no-print {{
        display: none !important;
      }}
    }}

    /* Europass Header */
    .europass-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 10px;
      padding-bottom: 2px;
    }}
    .header-left {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}
    .europass-logo {{
      display: flex;
      align-items: center;
      gap: 4px;
    }}
    .logo-stars {{
      width: 26px;
      height: 26px;
    }}
    .logo-text-euro {{
      font-size: 16pt;
      font-weight: 300;
      color: #0e3f8a;
      letter-spacing: -0.5px;
    }}
    .logo-text-pass {{
      font-size: 16pt;
      font-weight: 800;
      color: #0e3f8a;
      letter-spacing: -0.5px;
    }}
    .doc-title {{
      font-size: 9pt;
      color: #0e3f8a;
      margin-left: 20px;
      font-weight: 400;
    }}
    .header-right {{
      text-align: right;
      font-size: 7.5pt;
      color: #333333;
    }}
    .header-right .ref-code {{
      color: #555555;
      margin-bottom: 2px;
    }}
    .header-right .name-header {{
      color: #0e3f8a;
      font-weight: 600;
      font-size: 8.5pt;
    }}

    /* Section Divider with Blue Accent Box */
    .eu-section-divider {{
      display: flex;
      align-items: center;
      margin: 10px 0 6px 0;
    }}
    .eu-divider-line {{
      flex: 1;
      height: 1px;
      background-color: #93c5fd;
    }}
    .eu-divider-box {{
      width: 8px;
      height: 8px;
      background-color: #0e3f8a;
      margin-left: 2px;
    }}

    /* Two-column Layout */
    .eu-row {{
      display: flex;
      margin-bottom: 6px;
    }}
    .eu-left {{
      width: 29%;
      padding-right: 16px;
      text-align: right;
      font-size: 8pt;
      font-weight: 700;
      color: #0e3f8a;
      line-height: 1.3;
      letter-spacing: 0.2px;
    }}
    .eu-left.regular-label {{
      font-weight: 400;
      color: #333333;
      font-size: 7.8pt;
    }}
    .eu-left.dates {{
      font-weight: 400;
      color: #333333;
      font-size: 7.8pt;
    }}
    .eu-right {{
      width: 71%;
      font-size: 8.2pt;
      color: #222222;
      line-height: 1.35;
    }}

    /* Personal Info Box */
    .personal-info-container {{
      display: flex;
      gap: 14px;
    }}
    .photo-placeholder {{
      width: 80px;
      height: 100px;
      background-color: #e2e8f0;
      border: 1px solid #94a3b8;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #64748b;
      font-size: 7.5pt;
      text-align: center;
      flex-shrink: 0;
      border-radius: 2px;
    }}
    .personal-details {{
      flex: 1;
    }}
    .name-title {{
      font-size: 12pt;
      font-weight: 700;
      color: #0e3f8a;
      margin-bottom: 3px;
    }}
    .contact-item {{
      display: flex;
      align-items: center;
      gap: 5px;
      margin-bottom: 2px;
      font-size: 7.8pt;
      color: #333333;
    }}
    .contact-item svg {{
      width: 12px;
      height: 12px;
      color: #0284c7;
      flex-shrink: 0;
    }}
    .contact-item a {{
      color: #0e3f8a;
      text-decoration: none;
    }}
    .contact-item a:hover {{
      text-decoration: underline;
    }}
    .demographics-line {{
      margin-top: 4px;
      font-size: 7.5pt;
      color: #333333;
      padding-top: 2px;
      line-height: 1.3;
    }}
    .demographics-line span.label {{
      color: #0284c7;
      font-weight: 600;
    }}

    /* Job Applied For / Objective */
    .job-applied-title {{
      font-size: 8.8pt;
      font-weight: 700;
      color: #0e3f8a;
      line-height: 1.3;
    }}
    .personal-statement-text {{
      font-size: 8pt;
      color: #333333;
      margin-top: 3px;
      line-height: 1.35;
      text-align: justify;
    }}

    /* Experience / Education items */
    .position-title {{
      font-size: 8.8pt;
      font-weight: 700;
      color: #0e3f8a;
    }}
    .institution-name {{
      font-size: 8.2pt;
      color: #444444;
      margin-bottom: 3px;
    }}
    .eu-bullet-list {{
      list-style-type: none;
      padding-left: 0;
      margin-top: 2px;
      margin-bottom: 3px;
    }}
    .eu-bullet-list li {{
      position: relative;
      padding-left: 14px;
      margin-bottom: 2px;
      font-size: 8pt;
      line-height: 1.32;
    }}
    .eu-bullet-list li::before {{
      content: "▪";
      position: absolute;
      left: 2px;
      color: #0e3f8a;
      font-size: 8pt;
      top: -0.5px;
    }}
    .sector-line {{
      font-size: 7.5pt;
      color: #555555;
      margin-top: 2px;
    }}
    .sector-line span.label {{
      color: #0284c7;
      font-weight: 600;
    }}

    /* EQF Badge */
    .eqf-badge {{
      float: right;
      font-size: 7.2pt;
      color: #0284c7;
      font-weight: 600;
      text-align: right;
    }}

    /* Official Europass CEFR Table */
    .cefr-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 3px;
      margin-bottom: 3px;
      font-size: 7.2pt;
    }}
    .cefr-table th, .cefr-table td {{
      border: 1px solid #cbd5e1;
      padding: 3px 5px;
      text-align: center;
    }}
    .cefr-table th {{
      background-color: #f8fafc;
      color: #475569;
      font-weight: 600;
      font-size: 6.8pt;
    }}
    .cefr-table td.level-val {{
      font-weight: 700;
      color: #0e3f8a;
    }}
    .cefr-table td.cert-row {{
      font-size: 6.8pt;
      color: #64748b;
      font-style: italic;
      background-color: #fafafa;
      text-align: left;
      padding-left: 8px;
    }}
    .cefr-legend {{
      font-size: 6.5pt;
      color: #64748b;
      margin-top: 2px;
      line-height: 1.25;
    }}

    /* Digital Competence Matrix */
    .digital-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 3px;
      margin-bottom: 3px;
      font-size: 7.2pt;
    }}
    .digital-table th, .digital-table td {{
      border: 1px solid #cbd5e1;
      padding: 3px 5px;
      text-align: center;
    }}
    .digital-table th {{
      background-color: #f8fafc;
      color: #475569;
      font-size: 6.8pt;
    }}
    .digital-table th.main-header {{
      background-color: #f1f5f9;
      font-weight: 700;
      color: #0e3f8a;
      letter-spacing: 0.5px;
    }}
    .digital-table td.proficient {{
      color: #0e3f8a;
      font-weight: 700;
    }}
    .digital-table td.independent {{
      color: #0284c7;
      font-weight: 600;
    }}

    /* Footer */
    .europass-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px solid #e2e8f0;
      padding-top: 4px;
      margin-top: 10px;
      font-size: 6.8pt;
      color: #64748b;
    }}
    .europass-footer a {{
      color: #0e3f8a;
      text-decoration: none;
    }}

    /* Action bar */
    .action-toolbar {{
      width: 210mm;
      margin: 0 auto 12px auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #0e1726;
      border: 1px solid #334155;
      padding: 10px 16px;
      border-radius: 8px;
    }}
    .action-toolbar .title {{
      font-size: 9.5pt;
      font-weight: 700;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .btn-action {{
      background: #0284c7;
      color: #ffffff;
      border: none;
      padding: 6px 14px;
      border-radius: 4px;
      font-size: 8.5pt;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      text-decoration: none;
      transition: background 0.15s ease;
    }}
    .btn-action:hover {{
      background: #0369a1;
    }}
    .btn-secondary {{
      background: #1e293b;
      border: 1px solid #475569;
      color: #f8fafc;
    }}
    .btn-secondary:hover {{
      background: #334155;
    }}
  </style>
</head>
<body>

  <!-- Floating Toolbar -->
  <div class="action-toolbar no-print">
    <div class="title">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2">
        <circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>
      </svg>
      Europass CV &bull; {full_name} &bull; Targeted for {company}
    </div>
    <div style="display: flex; gap: 8px;">
      <a class="btn-action btn-secondary" href="javascript:history.back()">
        &larr; Back to Dashboard
      </a>
      <button class="btn-action" onclick="window.print()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>
        </svg>
        Print / Save to PDF (A4)
      </button>
    </div>
  </div>

  <!-- ==================== PAGE 1 ==================== -->
  <div class="cv-page">
    <div class="cv-content">
      <!-- Header -->
      <div class="europass-header">
        <div class="header-left">
          <div class="europass-logo">
            <svg class="logo-stars" viewBox="0 0 100 100" fill="none">
              <circle cx="50" cy="50" r="46" fill="#003399"/>
              <g fill="#FFCC00">
                <polygon points="50,14 52,20 58,20 53,24 55,30 50,26 45,30 47,24 42,20 48,20" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(30 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(60 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(90 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(120 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(150 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(180 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(210 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(240 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(270 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(300 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(330 50 50)" />
              </g>
            </svg>
            <span class="logo-text-euro" style="margin-left: 6px;">euro</span><span class="logo-text-pass">pass</span>
          </div>
          <span class="doc-title">Curriculum Vitae</span>
        </div>
        <div class="header-right">
          <div class="ref-code">Ref. Ares(2022)2356242 - 30/03/2022</div>
          <div class="name-header">{full_name}</div>
        </div>
      </div>

      <!-- PERSONAL INFORMATION -->
      <div class="eu-row" style="margin-top: 6px;">
        <div class="eu-left">
          PERSONAL INFORMATION
        </div>
        <div class="eu-right">
          <div class="personal-info-container">
            <div class="photo-placeholder">
              <span>Photo</span>
            </div>
            <div class="personal-details">
              <div class="name-title">{full_name}</div>
              
              <div class="contact-item">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
                <span>Berlin, Germany (Arriving 2025)</span>
              </div>
              <div class="contact-item">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>
                <span>{phone}</span>
                <span style="margin: 0 4px; color: #94a3b8;">|</span>
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
                <a href="mailto:{email}">{email}</a>
              </div>
              <div class="contact-item">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
                <span>LinkedIn: <a href="{linkedin_url}" target="_blank">{linkedin_url}</a></span>
              </div>
              <div class="contact-item">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                <span>GitHub: <a href="{github_url}" target="_blank">{github_url}</a></span>
              </div>

              <div class="demographics-line">
                <span class="label">Status</span> Incoming MSc Data Science Student at GISMA University Berlin &bull; Resident in Berlin<br>
                <span class="label">Work Authorization</span> Legal right to work in Germany (Werkstudent status &bull; No visa sponsorship required)
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- JOB APPLIED FOR / PERSONAL STATEMENT -->
      <div class="eu-row" style="margin-top: 8px;">
        <div class="eu-left">
          JOB APPLIED FOR<br>
          POSITION<br>
          PERSONAL STATEMENT
        </div>
        <div class="eu-right">
          <div class="job-applied-title">
            {title} &bull; {company} ({location})
          </div>
          <p class="personal-statement-text">
            {profile_summary}
          </p>
        </div>
      </div>

      <!-- WORK EXPERIENCE SECTION -->
      <div class="eu-section-divider">
        <div class="eu-divider-line"></div>
        <div class="eu-divider-box"></div>
      </div>

      <div class="eu-row">
        <div class="eu-left">
          WORK EXPERIENCE
        </div>
        <div class="eu-right"></div>
      </div>

      <!-- Work Experience Entry 1: Crack-ED -->
      <div class="eu-row">
        <div class="eu-left dates">
          Sep 2024 – Aug 2025
        </div>
        <div class="eu-right">
          <div class="position-title">Software Engineer</div>
          <div class="institution-name">Crack-ED &bull; Gurgaon, India</div>
          <ul class="eu-bullet-list">
            <li>Architected and deployed an LMS platform serving 1,000+ concurrent users, reducing system downtime by 35% and supporting 10,000+ student enrollments.</li>
            <li>Optimised 15+ critical SQL queries and implemented Redis caching, cutting average API response time from ~800ms to under 320ms &mdash; a 60% backend performance improvement.</li>
            <li>Built 3 real-time analytics dashboards tracking progress of 10,000+ students, enabling instructors to identify at-risk learners 40% faster.</li>
            <li>Implemented JWT + RBAC authentication securing a multi-role platform across students, instructors, and admins with zero reported security incidents.</li>
            <li>Automated end-to-end CI/CD pipelines using GitHub Actions, reducing deployment time from ~50 minutes to under 30 minutes &mdash; saving ~8 engineering hours per week.</li>
          </ul>
          <div class="sector-line"><span class="label">Business or sector</span> Educational Technology &amp; Enterprise Software Platforms</div>
        </div>
      </div>

      <!-- Work Experience Entry 2: Innomatics -->
      <div class="eu-row" style="margin-top: 6px;">
        <div class="eu-left dates">
          Mar 2023 – Jun 2023
        </div>
        <div class="eu-right">
          <div class="position-title">Data Science Intern</div>
          <div class="institution-name">Innomatics Research Labs &bull; Hyderabad, India</div>
          <ul class="eu-bullet-list">
            <li>Built an NLP healthcare chatbot handling 500+ query types, achieving 87% intent classification accuracy using Python and NLTK.</li>
            <li>Automated text preprocessing pipeline across 3 datasets totalling 50,000+ records, reducing manual preprocessing time by 20% (saving ~4 hours per sprint).</li>
            <li>Delivered tokenization, stemming, and intent classification pipeline reducing end-to-end chatbot response generation time by 30%.</li>
          </ul>
          <div class="sector-line"><span class="label">Business or sector</span> Artificial Intelligence &amp; Data Science Research</div>
        </div>
      </div>

      <!-- EDUCATION AND TRAINING SECTION -->
      <div class="eu-section-divider">
        <div class="eu-divider-line"></div>
        <div class="eu-divider-box"></div>
      </div>

      <div class="eu-row">
        <div class="eu-left">
          EDUCATION AND TRAINING
        </div>
        <div class="eu-right"></div>
      </div>

      <!-- Education Entry 1 -->
      <div class="eu-row">
        <div class="eu-left dates">
          2026 – 2028 (Expected)
        </div>
        <div class="eu-right">
          <span class="eqf-badge">EQF level 7</span>
          <div class="position-title">Master of Science (M.Sc.) in Data Science</div>
          <div class="institution-name">GISMA University of Applied Sciences &bull; Berlin, Germany</div>
          <ul class="eu-bullet-list">
            <li><strong>Core Focus:</strong> Advanced Data Science, Machine Learning, Statistical Inference, Predictive Analytics, Big Data Architectures.</li>
          </ul>
        </div>
      </div>

      <!-- Education Entry 2 -->
      <div class="eu-row" style="margin-top: 4px;">
        <div class="eu-left dates">
          2021 – 2024
        </div>
        <div class="eu-right">
          <span class="eqf-badge">EQF level 6</span>
          <div class="position-title">Bachelor of Technology (B.Tech.) in Computer Science (AI &amp; Machine Learning)</div>
          <div class="institution-name">Sai Spurthi Institute of Technology &bull; Telangana, India</div>
          <ul class="eu-bullet-list">
            <li><strong>Relevant Coursework:</strong> Machine Learning, Deep Learning, Neural Networks, Data Structures &amp; Algorithms, Probability &amp; Statistics, Database Systems.</li>
          </ul>
        </div>
      </div>

    </div>

    <!-- Page 1 Footer -->
    <div class="europass-footer">
      <div>&copy; European Union, 2002-2026 | <a href="https://europass.cedefop.europa.eu" target="_blank">europass.cedefop.europa.eu</a></div>
      <div>Page 1 / 2</div>
    </div>
  </div>

  <!-- ==================== PAGE 2 ==================== -->
  <div class="cv-page">
    <div class="cv-content">
      <!-- Header Page 2 -->
      <div class="europass-header">
        <div class="header-left">
          <div class="europass-logo">
            <svg class="logo-stars" viewBox="0 0 100 100" fill="none">
              <circle cx="50" cy="50" r="46" fill="#003399"/>
              <g fill="#FFCC00">
                <polygon points="50,14 52,20 58,20 53,24 55,30 50,26 45,30 47,24 42,20 48,20" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(30 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(60 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(90 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(120 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(150 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(180 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(210 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(240 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(270 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(300 50 50)" />
                <polygon points="68,19 70,25 76,25 71,29 73,35 68,31 63,35 65,29 60,25 66,25" transform="rotate(330 50 50)" />
              </g>
            </svg>
            <span class="logo-text-euro" style="margin-left: 6px;">euro</span><span class="logo-text-pass">pass</span>
          </div>
          <span class="doc-title">Curriculum Vitae</span>
        </div>
        <div class="header-right">
          <div class="name-header">{full_name}</div>
        </div>
      </div>

      <!-- PERSONAL SKILLS SECTION -->
      <div class="eu-section-divider">
        <div class="eu-divider-line"></div>
        <div class="eu-divider-box"></div>
      </div>

      <div class="eu-row">
        <div class="eu-left">
          PERSONAL SKILLS
        </div>
        <div class="eu-right"></div>
      </div>

      <!-- Mother Tongue -->
      <div class="eu-row">
        <div class="eu-left regular-label">
          Mother tongue(s)
        </div>
        <div class="eu-right">
          <strong>Telugu</strong> (Native)
        </div>
      </div>

      <!-- Other Languages (Official CEFR Framework Table) -->
      <div class="eu-row" style="margin-top: 3px;">
        <div class="eu-left regular-label">
          Other language(s)
        </div>
        <div class="eu-right">
          <table class="cefr-table">
            <thead>
              <tr>
                <th colspan="2">UNDERSTANDING</th>
                <th colspan="2">SPEAKING</th>
                <th>WRITING</th>
              </tr>
              <tr>
                <th style="width: 20%;">Listening</th>
                <th style="width: 20%;">Reading</th>
                <th style="width: 20%;">Spoken interaction</th>
                <th style="width: 20%;">Spoken production</th>
                <th style="width: 20%;">Writing</th>
              </tr>
            </thead>
            <tbody>
              <!-- English -->
              <tr>
                <td colspan="5" style="text-align: left; font-weight: 700; background: #f8fafc; color: #0e3f8a;">English</td>
              </tr>
              <tr>
                <td class="level-val">B2</td>
                <td class="level-val">B2</td>
                <td class="level-val">B2</td>
                <td class="level-val">B2</td>
                <td class="level-val">B2</td>
              </tr>
              <tr>
                <td colspan="5" class="cert-row">B2 &ndash; Upper Intermediate &bull; Professional working proficiency</td>
              </tr>
              <!-- Hindi -->
              <tr>
                <td colspan="5" style="text-align: left; font-weight: 700; background: #f8fafc; color: #0e3f8a;">Hindi</td>
              </tr>
              <tr>
                <td class="level-val">B2</td>
                <td class="level-val">B2</td>
                <td class="level-val">B2</td>
                <td class="level-val">B2</td>
                <td class="level-val">B2</td>
              </tr>
              <tr>
                <td colspan="5" class="cert-row">B2 &ndash; Upper Intermediate</td>
              </tr>
              <!-- German -->
              <tr>
                <td colspan="5" style="text-align: left; font-weight: 700; background: #f8fafc; color: #0e3f8a;">German</td>
              </tr>
              <tr>
                <td class="level-val">A1</td>
                <td class="level-val">A1</td>
                <td class="level-val">A1</td>
                <td class="level-val">A1</td>
                <td class="level-val">A1</td>
              </tr>
              <tr>
                <td colspan="5" class="cert-row">A1 &ndash; Beginner &bull; Currently learning</td>
              </tr>
            </tbody>
          </table>
          <div class="cefr-legend">
            Levels: A1/A2: Basic user - B1/B2: Independent user - C1/C2: Proficient user<br>
            <a href="https://europass.cedefop.europa.eu/resources/european-language-levels-cefr" target="_blank" style="color: #0e3f8a; text-decoration: none;">Common European Framework of Reference for Languages</a>
          </div>
        </div>
      </div>

      <!-- Communication Skills -->
      <div class="eu-row" style="margin-top: 5px;">
        <div class="eu-left regular-label">
          Communication skills
        </div>
        <div class="eu-right">
          <ul class="eu-bullet-list">
            <li>Strong technical and cross-functional communication developed by coordinating multi-role LMS platforms across students, instructors, and administrators at Crack-ED.</li>
            <li>Collaborative engineering within agile sprints across distributed data science teams at Innomatics Research Labs.</li>
          </ul>
        </div>
      </div>

      <!-- Organisational / Managerial Skills -->
      <div class="eu-row" style="margin-top: 3px;">
        <div class="eu-left regular-label">
          Organisational / managerial skills
        </div>
        <div class="eu-right">
          <ul class="eu-bullet-list">
            <li>CI/CD sprint release management: automated GitHub Actions pipelines saving ~8 engineering hours weekly.</li>
            <li>Data preprocessing coordination: managed data cleaning workflows across 3 datasets and 50,000+ records.</li>
          </ul>
        </div>
      </div>

      <!-- Job-related Skills -->
      <div class="eu-row" style="margin-top: 3px;">
        <div class="eu-left regular-label">
          Job-related skills
        </div>
        <div class="eu-right">
          <ul class="eu-bullet-list">
            <li><strong>Machine Learning &amp; AI:</strong> Scikit-learn, Random Forest, Logistic Regression, basic TensorFlow, Exploratory Data Analysis (EDA), feature engineering, cross-validation.</li>
            <li><strong>Natural Language Processing:</strong> NLTK, tokenization, stemming, text preprocessing, and intent classification pipelines (87% accuracy).</li>
            <li><strong>Backend &amp; Database Optimization:</strong> SQL query optimization (60% latency reduction), Redis caching, Django REST APIs, JWT + RBAC security.</li>
          </ul>
        </div>
      </div>

      <!-- Digital Competence (Official Self-Assessment Grid) -->
      <div class="eu-row" style="margin-top: 4px;">
        <div class="eu-left regular-label">
          Digital competence
        </div>
        <div class="eu-right">
          <table class="digital-table">
            <thead>
              <tr>
                <th colspan="5" class="main-header">SELF-ASSESSMENT</th>
              </tr>
              <tr>
                <th style="width: 20%;">Information processing</th>
                <th style="width: 20%;">Communication</th>
                <th style="width: 20%;">Content creation</th>
                <th style="width: 20%;">Safety</th>
                <th style="width: 20%;">Problem solving</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="independent">Independent user (B2)</td>
                <td class="proficient">Proficient user (C1)</td>
                <td class="independent">Independent user (B2)</td>
                <td class="independent">Independent user (B2)</td>
                <td class="proficient">Proficient user (C1)</td>
              </tr>
            </tbody>
          </table>
          <div class="cefr-legend">
            Levels: Basic user - Independent user - Proficient user &bull; <a href="https://europass.cedefop.europa.eu" target="_blank" style="color: #0e3f8a;">Digital competences - Self-assessment grid</a>
          </div>

          <ul class="eu-bullet-list" style="margin-top: 4px;">
            <li><strong>ML / AI Stack:</strong> Scikit-learn, TensorFlow (Basic), NLTK, Random Forest, Logistic Regression, NLP</li>
            <li><strong>Data &amp; Analytics:</strong> Python, Pandas, NumPy, SQL, PostgreSQL, EDA, Data Cleaning, Data Visualisation</li>
            <li><strong>Backend &amp; Cloud:</strong> Django, REST APIs, Redis, JWT Authentication, AWS EC2/S3, CI/CD (GitHub Actions), Docker (Basic)</li>
            <li><strong>Programming Languages:</strong> Python, JavaScript, TypeScript, SQL</li>
          </ul>
        </div>
      </div>

      <!-- Driving Licence -->
      <div class="eu-row" style="margin-top: 2px;">
        <div class="eu-left regular-label">
          Driving licence
        </div>
        <div class="eu-right">
          B
        </div>
      </div>

      <!-- ADDITIONAL INFORMATION SECTION -->
      <div class="eu-section-divider">
        <div class="eu-divider-line"></div>
        <div class="eu-divider-box"></div>
      </div>

      <div class="eu-row">
        <div class="eu-left">
          ADDITIONAL INFORMATION<br><br>
          <span style="font-weight: 400; color: #444; font-size: 7.2pt; text-transform: none;">
            Projects<br>
            Certifications<br>
            References
          </span>
        </div>
        <div class="eu-right">
          <div style="margin-bottom: 5px;">
            <strong style="color: #0e3f8a;">Tailored Key Projects (Targeting {company}):</strong>
            <ul class="eu-bullet-list">
{projects_html}
            </ul>
          </div>
          <div style="margin-bottom: 4px;">
            <strong style="color: #0e3f8a;">Certifications:</strong>
            <ul class="eu-bullet-list">
              <li><strong>Machine Learning Specialization:</strong> Andrew Ng, Coursera</li>
              <li><strong>Python for Data Science:</strong> Coursera</li>
              <li><strong>SQL for Data Analysis:</strong> Coursera</li>
            </ul>
          </div>
          <div>
            <strong style="color: #0e3f8a;">References:</strong>
            <ul class="eu-bullet-list">
              <li>Academic and employment references available upon request.</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- ANNEXES SECTION -->
      <div class="eu-section-divider">
        <div class="eu-divider-line"></div>
        <div class="eu-divider-box"></div>
      </div>

      <div class="eu-row">
        <div class="eu-left">
          ANNEXES
        </div>
        <div class="eu-right">
          <ul class="eu-bullet-list">
            <li>GISMA University of Applied Sciences admission &amp; enrollment verification (Berlin, Germany);</li>
            <li>B.Tech in Computer Science (Artificial Intelligence &amp; Machine Learning) Degree Certificate and Transcripts;</li>
            <li>Course certificates for Machine Learning Specialization, Python for Data Science, and SQL for Data Analysis (Coursera);</li>
            <li>Verified GitHub technical repository codebases: <a href="{github_url}" target="_blank" style="color: #0e3f8a;">github.com/purnachand812</a>.</li>
          </ul>
        </div>
      </div>

    </div>

    <!-- Page 2 Footer -->
    <div class="europass-footer">
      <div>&copy; European Union, 2002-2026 | <a href="https://europass.cedefop.europa.eu" target="_blank">europass.cedefop.europa.eu</a></div>
      <div>Page 2 / 2</div>
    </div>
  </div>

</body>
</html>
"""
    file_path = RESUMES_DIR / f"resume_{job_id}.html"
    file_path.write_text(html, encoding="utf-8")
    return file_path

if __name__ == "__main__":
    sample_job = {
        "id": "job-berlin-001",
        "title": "Werkstudent / Junior Data Scientist",
        "company": "DeepAgent AI Labs GmbH",
        "location": "Berlin, Germany",
        "tech_stack": ["Python", "Machine Learning", "Scikit-learn", "SQL", "Redis"]
    }
    path = generate_tailored_resume(sample_job)
    print("Generated tailored Europass resume at:", path)
