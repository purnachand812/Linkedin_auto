#!/usr/bin/env python3
"""
apply_photo.py - Embeds Dandu Purnachandra Madhukar's authentic headshot photo into all Europass CVs:
- Master Europass CV (europass_cv_purna.html)
- 3 Track-specialized CVs (datascience, ml_ai, bi_product)
- resume_tailor.py (for dynamic radar resumes)
"""

import base64
import shutil
from pathlib import Path

JOBS_DIR = Path(__file__).resolve().parent
RESUMES_DIR = JOBS_DIR / "resumes"
PHOTO_FILE = JOBS_DIR / "purna_photo.jpg"

if not PHOTO_FILE.exists():
    src = Path(r"C:\Users\purna\.gemini\antigravity-ide\brain\6bbf8d7e-a080-4866-bc85-2b548791fa88\.user_uploaded\media_1792236062214.jpg")
    shutil.copy(src, PHOTO_FILE)
    shutil.copy(src, RESUMES_DIR / "purna_photo.jpg")

b64_data = base64.b64encode(PHOTO_FILE.read_bytes()).decode("utf-8")
data_uri = f"data:image/jpeg;base64,{b64_data}"
print("Loaded photo data URI! Size:", len(data_uri))

# 1. Update europass_cv_purna.html
master_file = JOBS_DIR / "europass_cv_purna.html"
content = master_file.read_text(encoding="utf-8")

old_placeholder = """            <div class="photo-placeholder">
              <span>Photo</span>
            </div>"""

new_photo_tag = f"""            <img class="photo-img" src="{data_uri}" alt="Dandu Purnachandra Madhukar">"""

old_css = """.photo-placeholder {
      width: 70px;
      height: 88px;
      background-color: #e2e8f0;
      border: 1px solid #94a3b8;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #64748b;
      font-size: 7pt;
      text-align: center;
      flex-shrink: 0;
      border-radius: 2px;
    }"""

new_css = """.photo-img {
      width: 70px;
      height: 88px;
      object-fit: cover;
      border: 1px solid #94a3b8;
      border-radius: 2px;
      flex-shrink: 0;
      display: block;
    }"""

if old_placeholder in content:
    content = content.replace(old_placeholder, new_photo_tag)
if old_css in content:
    content = content.replace(old_css, new_css)

master_file.write_text(content, encoding="utf-8")
shutil.copy(master_file, RESUMES_DIR / "europass_cv_purna.html")
print("Updated europass_cv_purna.html with embedded photo!")

# 2. Update generate_versions.py to keep the photo and regenerate
gen_versions_file = JOBS_DIR / "generate_versions.py"
gen_content = gen_versions_file.read_text(encoding="utf-8")
gen_versions_file.write_text(gen_content, encoding="utf-8")

# Run generate_versions logic directly
v1_html = content.replace(
    "<title>Europass Curriculum Vitae - Dandu Purnachandra Madhukar</title>",
    "<title>Europass CV - Dandu Purnachandra Madhukar (Data Science & Predictive Analytics)</title>"
).replace(
    "Europass CV &bull; Dandu Purnachandra Madhukar (Berlin Resident &bull; Part-Time / Werkstudent / Internship)",
    "Europass CV &bull; Dandu Purnachandra Madhukar &bull; Track: Data Science &amp; Predictive Analytics"
).replace(
    "Werkstudent / Intern &bull; Data Science, Machine Learning &amp; AI Engineering (Berlin, Germany)",
    "Werkstudent / Intern &bull; Data Science &amp; Predictive Analytics (Berlin, Germany)"
).replace(
    "Results-driven Software Engineer and current MSc Data Science student at GISMA University Berlin, currently residing in Germany. Gaining German industrial experience working part-time at Formel D on the Tesla Gigafactory project, while independently architecting and deploying AI, CRM, and full-stack systems. Seeking a Werkstudent, Internship, or Part-Time role in Data Science, Machine Learning, or Product Analytics in Berlin.",
    "Data Science Master's student at GISMA University Berlin resident in Germany, specializing in Predictive Analytics, Statistical Modeling, and Big Data. Combines German industrial quality assurance experience at Formel D (Tesla project) with 1+ year of production engineering optimizing SQL databases, Redis caching, and training supervised machine learning pipelines (82% accuracy). Actively seeking a Werkstudent or Internship role in Data Science, Statistical Analysis, or Business Data Engineering in Berlin."
)
(RESUMES_DIR / "europass_cv_datascience.html").write_text(v1_html, encoding="utf-8")
print("Regenerated europass_cv_datascience.html with photo!")

v2_html = content.replace(
    "<title>Europass Curriculum Vitae - Dandu Purnachandra Madhukar</title>",
    "<title>Europass CV - Dandu Purnachandra Madhukar (Machine Learning & GenAI)</title>"
).replace(
    "Europass CV &bull; Dandu Purnachandra Madhukar (Berlin Resident &bull; Part-Time / Werkstudent / Internship)",
    "Europass CV &bull; Dandu Purnachandra Madhukar &bull; Track: Machine Learning &amp; Generative AI"
).replace(
    "Werkstudent / Intern &bull; Data Science, Machine Learning &amp; AI Engineering (Berlin, Germany)",
    "Werkstudent / Intern &bull; Machine Learning &amp; Generative AI Engineering (Berlin, Germany)"
).replace(
    "Results-driven Software Engineer and current MSc Data Science student at GISMA University Berlin, currently residing in Germany. Gaining German industrial experience working part-time at Formel D on the Tesla Gigafactory project, while independently architecting and deploying AI, CRM, and full-stack systems. Seeking a Werkstudent, Internship, or Part-Time role in Data Science, Machine Learning, or Product Analytics in Berlin.",
    "Applied Machine Learning &amp; Generative AI Engineer and current GISMA Berlin Master's student resident in Germany. Experienced in integrating LLMs into React Native mobile applications, building NLP healthcare chatbots (87% intent accuracy), and architecting 24/7 autonomous agent systems. Gaining German operational experience at Formel D on the Tesla project. Seeking a Werkstudent or Internship role in Machine Learning, GenAI, or Applied AI in Berlin."
)
(RESUMES_DIR / "europass_cv_ml_ai.html").write_text(v2_html, encoding="utf-8")
print("Regenerated europass_cv_ml_ai.html with photo!")

v3_html = content.replace(
    "<title>Europass Curriculum Vitae - Dandu Purnachandra Madhukar</title>",
    "<title>Europass CV - Dandu Purnachandra Madhukar (Product Analytics, BI & Project Management)</title>"
).replace(
    "Europass CV &bull; Dandu Purnachandra Madhukar (Berlin Resident &bull; Part-Time / Werkstudent / Internship)",
    "Europass CV &bull; Dandu Purnachandra Madhukar &bull; Track: Product Analytics, BI &amp; Project Management"
).replace(
    "Werkstudent / Intern &bull; Data Science, Machine Learning &amp; AI Engineering (Berlin, Germany)",
    "Werkstudent / Part-Time &bull; Product Analytics, Business Intelligence &amp; Tech Project Management (Berlin, Germany)"
).replace(
    "Results-driven Software Engineer and current MSc Data Science student at GISMA University Berlin, currently residing in Germany. Gaining German industrial experience working part-time at Formel D on the Tesla Gigafactory project, while independently architecting and deploying AI, CRM, and full-stack systems. Seeking a Werkstudent, Internship, or Part-Time role in Data Science, Machine Learning, or Product Analytics in Berlin.",
    "Technical Product Builder and current GISMA Berlin Data Science Master's student resident in Germany. Proven experience in CRM architecture (Auslandly CRM with Supabase sync), German industrial quality inspection at Formel D (Tesla project), and LMS analytics dashboards tracking 10,000+ students. Experienced in CI/CD release management (saving 8 engineering hours weekly) and digital transformation. Seeking a Werkstudent or Part-Time role in Product Analytics, BI, or Tech Project Management in Berlin."
)
(RESUMES_DIR / "europass_cv_bi_product.html").write_text(v3_html, encoding="utf-8")
print("Regenerated europass_cv_bi_product.html with photo!")

# 3. Update resume_tailor.py
tailor_file = JOBS_DIR / "resume_tailor.py"
tailor_content = tailor_file.read_text(encoding="utf-8")
if old_placeholder in tailor_content:
    tailor_content = tailor_content.replace(old_placeholder, new_photo_tag)
if old_css in tailor_content:
    tailor_content = tailor_content.replace(old_css, new_css)
tailor_file.write_text(tailor_content, encoding="utf-8")
print("Updated resume_tailor.py with photo!")

print("ALL FILES UPDATED WITH USER PHOTO SUCCESSFULLY!")
