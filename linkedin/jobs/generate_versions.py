#!/usr/bin/env python3
"""
generate_versions.py - Generates the 3 specialized European Union Europass CV versions for Dandu Purnachandra Madhukar:
1. Data Science & Predictive Analytics (Werkstudent / Intern)
2. Machine Learning & Generative AI Engineering (Werkstudent / Intern)
3. Product Analytics, Business Intelligence & Project Management (Werkstudent / Part-time)
Strictly formatted for European Union Europass standards with balanced 2-page layout and student/intern roles.
"""

import shutil
from pathlib import Path

JOBS_DIR = Path(__file__).resolve().parent
RESUMES_DIR = JOBS_DIR / "resumes"
RESUMES_DIR.mkdir(parents=True, exist_ok=True)

MASTER_CV = JOBS_DIR / "europass_cv_purna.html"
shutil.copy(MASTER_CV, RESUMES_DIR / "europass_cv_purna.html")

master_html = MASTER_CV.read_text(encoding="utf-8")

BASE_STATEMENT = (
    "Data Science Master's student at GISMA University Berlin with practical experience in machine learning pipelines, "
    "predictive modeling, and SQL database optimization. Background includes software &amp; data engineering internship at Crack-ED "
    "(reducing query latency by 60%), data science internship at Innomatics (87% NLP intent classification), and graduate AI research. "
    "Resident in Berlin, Germany with full Werkstudent eligibility (up to 20 hrs/week during semester, 40 hrs/week during semester breaks; "
    "no visa sponsorship required). Seeking a Werkstudent or Internship role in Data Science, Machine Learning, or Data Engineering in Berlin."
)

# =========================================================================
# VERSION 1: DATA SCIENCE & PREDICTIVE ANALYTICS
# =========================================================================
v1_html = master_html

v1_html = v1_html.replace(
    "<title>Europass Curriculum Vitae - Dandu Purnachandra Madhukar</title>",
    "<title>Europass CV - Dandu Purnachandra Madhukar (Data Science & Predictive Analytics)</title>"
)
v1_html = v1_html.replace(
    "Europass CV &bull; Dandu Purnachandra Madhukar (Berlin Resident &bull; Part-Time / Werkstudent / Internship)",
    "Europass CV &bull; Dandu Purnachandra Madhukar &bull; Track: Data Science &amp; Predictive Analytics"
)
v1_html = v1_html.replace(
    "Werkstudent / Intern &bull; Data Science, Machine Learning &amp; AI Engineering (Berlin, Germany)",
    "Werkstudent / Intern &bull; Data Science &amp; Predictive Analytics (Berlin, Germany)"
)
v1_html = v1_html.replace(
    BASE_STATEMENT,
    "Data Science Master's student at GISMA University Berlin specializing in Predictive Modeling, Statistical Inference, and Big Data Analytics. Proven student and internship experience implementing supervised ML classification models (82% accuracy), building NLP chatbots (87% intent classification), and optimizing SQL backend queries by 60% at Crack-ED. Resident in Berlin, Germany with full Werkstudent rights (no visa sponsorship required). Seeking a Werkstudent or Internship role in Data Science, Predictive Analytics, or Data Engineering in Berlin."
)

(RESUMES_DIR / "europass_cv_datascience.html").write_text(v1_html, encoding="utf-8")
print("Generated: europass_cv_datascience.html")


# =========================================================================
# VERSION 2: MACHINE LEARNING & GENERATIVE AI ENGINEERING
# =========================================================================
v2_html = master_html

v2_html = v2_html.replace(
    "<title>Europass Curriculum Vitae - Dandu Purnachandra Madhukar</title>",
    "<title>Europass CV - Dandu Purnachandra Madhukar (Machine Learning & GenAI)</title>"
)
v2_html = v2_html.replace(
    "Europass CV &bull; Dandu Purnachandra Madhukar (Berlin Resident &bull; Part-Time / Werkstudent / Internship)",
    "Europass CV &bull; Dandu Purnachandra Madhukar &bull; Track: Machine Learning &amp; Generative AI"
)
v2_html = v2_html.replace(
    "Werkstudent / Intern &bull; Data Science, Machine Learning &amp; AI Engineering (Berlin, Germany)",
    "Werkstudent / Intern &bull; Machine Learning &amp; Generative AI Engineering (Berlin, Germany)"
)
v2_html = v2_html.replace(
    BASE_STATEMENT,
    "Applied Machine Learning &amp; AI Master's student at GISMA University Berlin specializing in Generative AI, LLM orchestration, and NLP pipelines. Demonstrated student and internship experience engineering NLP chatbots handling 500+ query types (87% intent accuracy), building AI navigation assistants in React Native with LLMs, and developing autonomous agent architectures. Resident in Berlin with full Werkstudent eligibility (no visa sponsorship required). Seeking a Werkstudent or Internship role in Machine Learning, Generative AI, or Applied AI in Berlin."
)

(RESUMES_DIR / "europass_cv_ml_ai.html").write_text(v2_html, encoding="utf-8")
print("Generated: europass_cv_ml_ai.html")


# =========================================================================
# VERSION 3: PRODUCT ANALYTICS, BI & TECH PROJECT MANAGEMENT
# =========================================================================
v3_html = master_html

v3_html = v3_html.replace(
    "<title>Europass Curriculum Vitae - Dandu Purnachandra Madhukar</title>",
    "<title>Europass CV - Dandu Purnachandra Madhukar (Product Analytics, BI & Project Management)</title>"
)
v3_html = v3_html.replace(
    "Europass CV &bull; Dandu Purnachandra Madhukar (Berlin Resident &bull; Part-Time / Werkstudent / Internship)",
    "Europass CV &bull; Dandu Purnachandra Madhukar &bull; Track: Product Analytics, BI &amp; Project Management"
)
v3_html = v3_html.replace(
    "Werkstudent / Intern &bull; Data Science, Machine Learning &amp; AI Engineering (Berlin, Germany)",
    "Werkstudent / Part-Time &bull; Product Analytics, Business Intelligence &amp; Tech Project Management (Berlin, Germany)"
)
v3_html = v3_html.replace(
    BASE_STATEMENT,
    "Data Science Master's student at GISMA University Berlin combining data analytics engineering with technical product building. Experienced in developing real-time student analytics dashboards tracking 10,000+ learners at Crack-ED, architecting cloud CRM databases (Auslandly CRM with Supabase sync), and managing CI/CD automated release pipelines (saving 8 engineering hours weekly). Resident in Berlin with full Werkstudent eligibility (no visa sponsorship required). Seeking a Werkstudent or Part-Time role in Product Analytics, Business Intelligence, or Tech Project Management in Berlin."
)

(RESUMES_DIR / "europass_cv_bi_product.html").write_text(v3_html, encoding="utf-8")
print("Generated: europass_cv_bi_product.html")

print("All 3 specialized Europass CV versions generated successfully!")
