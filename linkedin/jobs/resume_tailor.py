#!/usr/bin/env python3
"""
resume_tailor.py - Dynamic ATS 1-Page Resume & Cover Letter Generator for Purna's Career Pipeline.
Generates clean, single-page, ATS-optimized HTML/PDF documents that emphasize verified projects
matching the employer's specific tech stack (zero false hallucinations).
"""

import os
import sys
import json
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
    Generates a tailored 1-page HTML resume emphasizing the skills and projects
    most relevant to the targeted job.
    Returns: file path to generated HTML resume.
    """
    RESUMES_DIR.mkdir(parents=True, exist_ok=True)
    profile = load_profile()
    
    job_id = job_info.get("id", "job-generic")
    title = job_info.get("title", "AI Engineer")
    company = job_info.get("company", "Company")
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

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{profile.get('full_name')} - Resume ({company} - {title})</title>
  <style>
    @page {{ size: A4; margin: 12mm 15mm; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #1e293b;
      line-height: 1.45;
      font-size: 9.5pt;
      background: #ffffff;
      padding: 15mm;
    }}
    .header {{
      border-bottom: 2px solid #0f172a;
      padding-bottom: 8px;
      margin-bottom: 12px;
    }}
    .name {{
      font-size: 18pt;
      font-weight: 800;
      color: #0f172a;
      letter-spacing: -0.02em;
    }}
    .sub-title {{
      font-size: 10.5pt;
      color: #0284c7;
      font-weight: 600;
      margin-top: 2px;
    }}
    .contact-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 8.5pt;
      color: #475569;
      margin-top: 6px;
    }}
    .contact-row a {{ color: #0284c7; text-decoration: none; }}
    
    .section {{
      margin-bottom: 11px;
    }}
    .section-title {{
      font-size: 10pt;
      font-weight: 700;
      color: #0f172a;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      border-bottom: 1px solid #cbd5e1;
      padding-bottom: 2px;
      margin-bottom: 6px;
    }}
    
    .item {{
      margin-bottom: 6px;
    }}
    .item-header {{
      display: flex;
      justify-content: space-between;
      font-weight: 700;
      color: #0f172a;
    }}
    .item-sub {{
      display: flex;
      justify-content: space-between;
      color: #475569;
      font-size: 8.5pt;
      font-style: italic;
      margin-bottom: 2px;
    }}
    .bullet-list {{
      padding-left: 14px;
      list-style-type: square;
    }}
    .bullet-list li {{
      margin-bottom: 2px;
      font-size: 9pt;
      color: #334155;
    }}
    
    .skills-grid {{
      display: grid;
      grid-template-columns: 120px 1fr;
      row-gap: 3px;
      font-size: 8.5pt;
    }}
    .skill-cat {{ font-weight: 700; color: #0f172a; }}
    .skill-val {{ color: #334155; }}
    
    .target-badge {{
      display: inline-block;
      background: #e0f2fe;
      color: #0369a1;
      padding: 1px 6px;
      border-radius: 4px;
      font-size: 8pt;
      font-weight: 600;
    }}
  </style>
</head>
<body>

  <div class="header">
    <div class="name">{profile.get('full_name')}</div>
    <div class="sub-title">{profile.get('title')} &bull; Berlin, Germany</div>
    <div class="contact-row">
      <span>📍 {profile.get('location')}</span>
      <span>✉️ {profile.get('email')}</span>
      <span>🔗 <a href="{profile.get('linkedin_url')}">LinkedIn</a></span>
      <span>💻 <a href="{profile.get('github_url')}">GitHub</a></span>
      <span class="target-badge">Tailored for: {company} ({title})</span>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Education</div>
    <div class="item">
      <div class="item-header">
        <span>Master of Science in Data Science</span>
        <span>2024 &ndash; Expected 2026</span>
      </div>
      <div class="item-sub">
        <span>Berlin University of Applied Sciences</span>
        <span>Berlin, Germany</span>
      </div>
      <ul class="bullet-list">
        <li><strong>Research Thesis:</strong> Autonomous LLM Agent Architecture: Trajectory Hallucination Detection &amp; Attribution Using Internal Model Activations.</li>
        <li><strong>Focus:</strong> Applied Neural Networks, Multi-Agent Systems, High-Performance Inference, and Sovereign Cloud Architecture.</li>
      </ul>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Verified Engineering &amp; AI Agent Projects</div>
"""

    for p in projects[:3]:
        techs = ", ".join(p.get("technologies", []))
        html += f"""
    <div class="item">
      <div class="item-header">
        <span>{p.get('name')}</span>
        <span>{p.get('role')}</span>
      </div>
      <div class="item-sub">
        <span>Technologies: {techs}</span>
      </div>
      <ul class="bullet-list">
        <li>{p.get('description')}</li>
        <li><strong>Impact:</strong> {p.get('impact')}</li>
      </ul>
    </div>
"""

    skills = profile.get("technical_skills", {})
    html += f"""
  </div>

  <div class="section">
    <div class="section-title">Technical Expertise</div>
    <div class="skills-grid">
      <div class="skill-cat">Languages:</div>
      <div class="skill-val">{", ".join(skills.get('languages', []))}</div>
      <div class="skill-cat">AI &amp; Frameworks:</div>
      <div class="skill-val">{", ".join(skills.get('ai_frameworks', []))}</div>
      <div class="skill-cat">Backend &amp; DevOps:</div>
      <div class="skill-val">{", ".join(skills.get('backend_cloud', []))}</div>
      <div class="skill-cat">Core Domains:</div>
      <div class="skill-val">{", ".join(skills.get('specializations', []))}</div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Work Authorization</div>
    <p style="font-size: 8.5pt; color: #475569;">
      <strong>Germany &amp; EU:</strong> Legal authorization to work in Germany (Student / Resident Work Permit). No visa sponsorship required for Germany.
    </p>
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
        "title": "AI Agent Engineer",
        "company": "DeepAgent AI Labs GmbH",
        "tech_stack": ["Python", "FastAPI", "Pydantic", "PyTorch"]
    }
    path = generate_tailored_resume(sample_job)
    print("Generated tailored resume at:", path)
