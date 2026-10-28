#!/usr/bin/env python3
"""
cover_letter_generator.py - Generates ATS-optimized, grounded European cover letters
tailored specifically to the employer's Job Description (JD).
Outputs clean, printable 1-page HTML cover letters matching Europass typography.
"""

import os
import sys
import json
from datetime import datetime, date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
JOBS_DIR = BASE_DIR / "linkedin" / "jobs"
RESUMES_DIR = JOBS_DIR / "resumes"
PROFILE_FILE = JOBS_DIR / "profile_master.json"

RESUMES_DIR.mkdir(parents=True, exist_ok=True)

def generate_tailored_cover_letter(job_info, make_pdf=False):
    """
    Generates an individualized, high-signal cover letter in HTML
    tailored to the specific company, title, and tech stack in job_info.
    """
    job_id = job_info.get("id") or job_info.get("job_id", "job-custom")
    title = job_info.get("title", "Data Science & Machine Learning Engineer")
    company = job_info.get("company", "Innovative Technology Team")
    location = job_info.get("location", "Berlin, Germany")
    tech_stack = job_info.get("tech_stack", ["Python", "Machine Learning", "SQL"])
    tech_str = ", ".join(tech_stack[:4])
    work_type = job_info.get("work_type", "Werkstudent / Internship")

    today_formatted = datetime.now().strftime("%d %B %Y")

    # Match thematic angle based on JD keywords
    desc = (job_info.get("description", "") + " " + title).lower()

    if "predict" in desc or "data science" in desc or "big data" in desc:
        academic_pillar = "Methods of Prediction, Big Data Analytics, and Statistical Inference"
        project_highlight = "At Crack-ED, I optimised 15+ complex SQL queries and introduced Redis caching, slashing backend latency by 60% across an LMS serving over 10,000 students. In parallel, I built supervised classification pipelines achieving 82% validation accuracy."
    elif "nlp" in desc or "llm" in desc or "agent" in desc:
        academic_pillar = "Artificial Intelligence, LLM Agent Architectures, and Natural Language Processing"
        project_highlight = "I recently developed a React Native mobile application integrating local LLM pipelines to guide newcomers through German administrative procedures, and architected an autonomous 24/7 LinkedIn AI publishing engine using official REST APIs. During my NLP internship at Innomatics Research Labs, I trained intent classifiers achieving 87% accuracy."
    else:
        academic_pillar = "Business Intelligence, Data Visualisation, and Product Analytics"
        project_highlight = "I architected and delivered the Auslandly Consultancy CRM using React, Supabase, and PostgreSQL with real-time data sync, owning delivery end-to-end. At Crack-ED, I spearheaded sprint CI/CD pipelines and designed analytics dashboards tracking active user engagement."

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Cover Letter - Dandu Purnachandra Madhukar - {company}</title>
  <style>
    @page {{
      size: A4;
      margin: 18mm 20mm 18mm 20mm;
    }}
    body {{
      font-family: 'Arial', 'Helvetica', sans-serif;
      color: #1e293b;
      line-height: 1.55;
      font-size: 10pt;
      margin: 0;
      padding: 20px 25px;
      background: #ffffff;
    }}
    .back-btn-bar {{
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 1px solid #e2e8f0;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .back-link {{
      color: #0e3f8a;
      text-decoration: none;
      font-size: 8.5pt;
      font-weight: bold;
    }}
    .print-btn {{
      background: #0e3f8a;
      color: white;
      border: none;
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 8.5pt;
      cursor: pointer;
    }}
    @media print {{
      .back-btn-bar {{ display: none; }}
      body {{ padding: 0; }}
    }}
    .header-table {{
      width: 100%;
      border-bottom: 2px solid #0e3f8a;
      padding-bottom: 12px;
      margin-bottom: 16px;
    }}
    .candidate-name {{
      font-size: 16pt;
      font-weight: bold;
      color: #0e3f8a;
      letter-spacing: -0.3px;
    }}
    .candidate-sub {{
      font-size: 8.5pt;
      color: #475569;
      margin-top: 2px;
    }}
    .contact-info {{
      font-size: 8.5pt;
      color: #334155;
      text-align: right;
      line-height: 1.45;
    }}
    .contact-info a {{
      color: #0e3f8a;
      text-decoration: none;
    }}
    .meta-table {{
      width: 100%;
      margin-bottom: 16px;
      font-size: 9.5pt;
    }}
    .recipient-block {{
      color: #1e293b;
      line-height: 1.4;
    }}
    .date-block {{
      text-align: right;
      color: #64748b;
      font-size: 9pt;
    }}
    .subject-line {{
      font-size: 11pt;
      font-weight: bold;
      color: #0e3f8a;
      margin: 16px 0 12px 0;
      padding-bottom: 4px;
      border-bottom: 1px solid #cbd5e1;
    }}
    .salutation {{
      font-size: 10pt;
      font-weight: bold;
      margin-bottom: 10px;
    }}
    p {{
      margin: 0 0 11px 0;
      text-align: justify;
    }}
    .signature-block {{
      margin-top: 20px;
    }}
    .sig-name {{
      font-weight: bold;
      color: #0e3f8a;
      font-size: 10.5pt;
    }}
    .sig-title {{
      font-size: 8.5pt;
      color: #64748b;
      margin-top: 2px;
    }}
    .pill-badge {{
      display: inline-block;
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      color: #1e40af;
      padding: 1px 6px;
      border-radius: 3px;
      font-size: 7.5pt;
      font-weight: bold;
      margin-top: 4px;
    }}
  </style>
</head>
<body>

  <div class="back-btn-bar">
    <a href="/" onclick="if (history.length > 1) {{ history.back(); return false; }}" class="back-link">&larr; Return to Dashboard</a>
    <div>
      <span class="pill-badge">OFFICIAL EU STANDARD &bull; {work_type.upper()}</span>
      <button class="print-btn" onclick="window.print()">Print / PDF</button>
    </div>
  </div>

  <table class="header-table">
    <tr>
      <td style="vertical-align: top;">
        <div class="candidate-name">DANDU PURNACHANDRA MADHUKAR</div>
        <div class="candidate-sub">M.Sc. Data Science Student &bull; GISMA University of Applied Sciences, Berlin</div>
      </td>
      <td class="contact-info" style="vertical-align: top;">
        Berlin, Germany (Resident)<br>
        <strong>Tel:</strong> +49 15511064761<br>
        <strong>Email:</strong> <a href="mailto:purnachand0812@gmail.com">purnachand0812@gmail.com</a><br>
        <a href="https://linkedin.com/in/purnachanddandu" target="_blank">linkedin.com/in/purnachanddandu</a> &bull; <a href="https://github.com/purnachand812" target="_blank">github.com/purnachand812</a>
      </td>
    </tr>
  </table>

  <table class="meta-table">
    <tr>
      <td class="recipient-block">
        <strong>Hiring Team &bull; Talent Acquisition</strong><br>
        {company}<br>
        {location}
      </td>
      <td class="date-block" style="vertical-align: top;">
        Berlin, {today_formatted}
      </td>
    </tr>
  </table>

  <div class="subject-line">
    Subject: Application for {title} ({work_type})
  </div>

  <div class="salutation">
    Dear Hiring Team at {company},
  </div>

  <p>
    I am writing to express my strong enthusiasm for the <strong>{title}</strong> position at <strong>{company}</strong> in {location}. Currently residing in Berlin and enrolled in the M.Sc. Data Science program at GISMA University of Applied Sciences, I combine rigorous theoretical foundations with direct production experience in full-stack Python engineering, data processing, and machine learning systems ({tech_str}).
  </p>

  <p>
    My Master's specialization directly covers <strong>{academic_pillar}</strong>. {project_highlight} Through these initiatives, I have developed a disciplined approach to translating complex analytical problem sets into performant, reliable software implementations.
  </p>

  <p>
    During my tenure as a Software Engineering Intern at <strong>Crack-ED</strong> and NLP Intern at <strong>Innomatics Research Labs</strong>, I collaborated within Agile teams to build data processing pipelines, optimize application backends, and benchmark machine learning models. Combined with my GISMA Berlin Master's coursework and independent software builds (such as the Auslandly CRM and AI German Navigation assistant), I bring a structured engineering mindset focused on reliable code quality and clean documentation.
  </p>

  <p>
    As a registered Master's student based locally in Berlin, I possess full legal work authorization for student employment (Werkstudent up to 20 hours per week during the semester, and full-time during breaks) without requiring visa sponsorship. I communicate fluently in English, possess <strong>German A2</strong> proficiency which I am actively advancing, and can integrate seamlessly into your engineering team immediately.
  </p>

  <p>
    Thank you for your time and consideration. I welcome the opportunity to discuss in an interview how my technical skills and proactive work ethic can support {company}'s milestones.
  </p>

  <div class="signature-block">
    Sincerely,<br><br>
    <div class="sig-name">Dandu Purnachandra Madhukar</div>
    <div class="sig-title">
      M.Sc. Data Science Candidate &bull; GISMA Berlin<br>
      Berlin, Germany &bull; +49 15511064761
    </div>
  </div>

</body>
</html>
"""
    output_filename = f"cover_letter_{job_id}.html"
    output_file = RESUMES_DIR / output_filename
    output_file.write_text(html_content, encoding="utf-8")

    if make_pdf:
        # Generate companion PDF if requested
        pdf_path = RESUMES_DIR / f"cover_letter_{job_id}.pdf"
        try:
            from linkedin.jobs import pdf_converter
            pdf_converter.convert_html_to_pdf(output_file, pdf_path)
        except Exception as e:
            print(f"[Warning] Could not generate PDF cover letter: {e}")

    return output_file

if __name__ == "__main__":
    sample_job = {
        "id": "job-berlin-ws-001",
        "title": "Werkstudent / Working Student - Machine Learning & AI Engineering",
        "company": "DeepAgent AI Labs GmbH",
        "location": "Berlin, Germany (Hybrid - Mitte)",
        "work_type": "Werkstudent (up to 20 hrs/week)",
        "tech_stack": ["Python", "Machine Learning", "LLM Integration", "React Native"]
    }
    path = generate_tailored_cover_letter(sample_job)
    print("Generated Cover Letter:", path)
