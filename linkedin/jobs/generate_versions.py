#!/usr/bin/env python3
"""
generate_versions.py - Generates the 3 specialized European Union Europass CV versions for Dandu Purnachandra Madhukar:
1. Data Science & Predictive Analytics (Werkstudent / Intern)
2. Machine Learning & Generative AI Engineering (Werkstudent / Intern)
3. Product Analytics, Business Intelligence & Project Management (Werkstudent / Part-time)
"""

import shutil
from pathlib import Path

JOBS_DIR = Path(__file__).resolve().parent
RESUMES_DIR = JOBS_DIR / "resumes"
RESUMES_DIR.mkdir(parents=True, exist_ok=True)

MASTER_CV = JOBS_DIR / "europass_cv_purna.html"
shutil.copy(MASTER_CV, RESUMES_DIR / "europass_cv_purna.html")

master_html = MASTER_CV.read_text(encoding="utf-8")

# =========================================================================
# VERSION 1: DATA SCIENCE & PREDICTIVE ANALYTICS
# =========================================================================
v1_html = master_html

v1_html = v1_html.replace(
    "<title>Europass Curriculum Vitae - Dandu Purnachandra Madhukar</title>",
    "<title>Europass CV - Dandu Purnachandra Madhukar (Data Science & Predictive Analytics)</title>"
)
v1_html = v1_html.replace(
    "Europass CV &bull; Dandu Purnachandra Madhukar (Part-Time / Werkstudent / Internship)",
    "Europass CV &bull; Dandu Purnachandra Madhukar &bull; Track: Data Science &amp; Predictive Analytics"
)
v1_html = v1_html.replace(
    "Werkstudent / Intern &bull; Data Science, Machine Learning &amp; AI Engineering (Berlin, Germany)",
    "Werkstudent / Intern &bull; Data Science &amp; Predictive Analytics (Berlin, Germany)"
)
v1_html = v1_html.replace(
    "Results-driven Software Engineer transitioning into Data Science, with 1+ year of production engineering experience and product building. Skilled in Python, Machine Learning, SQL, LLM integrations, and full-stack delivery. Incoming MSc Data Science student at GISMA University Berlin. Currently seeking Part-Time, Internship, or Werkstudent roles in Data Science, Machine Learning, or Product Analytics in Berlin.",
    "Data Science Master's student at GISMA University Berlin specializing in Predictive Analytics, Statistical Modeling, and Big Data. 1+ year of production engineering experience optimizing complex SQL databases, deploying Redis in-memory caching, and training supervised machine learning pipelines (82% accuracy). Actively seeking a Werkstudent or Internship role in Data Science, Statistical Analysis, or Business Data Engineering in Berlin."
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
    "Europass CV &bull; Dandu Purnachandra Madhukar (Part-Time / Werkstudent / Internship)",
    "Europass CV &bull; Dandu Purnachandra Madhukar &bull; Track: Machine Learning &amp; Generative AI"
)
v2_html = v2_html.replace(
    "Werkstudent / Intern &bull; Data Science, Machine Learning &amp; AI Engineering (Berlin, Germany)",
    "Werkstudent / Intern &bull; Machine Learning &amp; Generative AI Engineering (Berlin, Germany)"
)
v2_html = v2_html.replace(
    "Results-driven Software Engineer transitioning into Data Science, with 1+ year of production engineering experience and product building. Skilled in Python, Machine Learning, SQL, LLM integrations, and full-stack delivery. Incoming MSc Data Science student at GISMA University Berlin. Currently seeking Part-Time, Internship, or Werkstudent roles in Data Science, Machine Learning, or Product Analytics in Berlin.",
    "Applied Machine Learning &amp; Generative AI Engineer with hands-on experience integrating LLMs, building NLP pipelines (87% intent classification), and deploying autonomous agent systems. Built an AI Germany Navigation assistant in React Native and an autonomous 24/7 LinkedIn research agent. Incoming MSc Data Science student at GISMA University Berlin. Seeking a Werkstudent or Internship role in Machine Learning, GenAI, or Applied AI in Berlin."
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
    "Europass CV &bull; Dandu Purnachandra Madhukar (Part-Time / Werkstudent / Internship)",
    "Europass CV &bull; Dandu Purnachandra Madhukar &bull; Track: Product Analytics, BI &amp; Project Management"
)
v3_html = v3_html.replace(
    "Werkstudent / Intern &bull; Data Science, Machine Learning &amp; AI Engineering (Berlin, Germany)",
    "Werkstudent / Part-Time &bull; Product Analytics, Business Intelligence &amp; Tech Project Management (Berlin, Germany)"
)
v3_html = v3_html.replace(
    "Results-driven Software Engineer transitioning into Data Science, with 1+ year of production engineering experience and product building. Skilled in Python, Machine Learning, SQL, LLM integrations, and full-stack delivery. Incoming MSc Data Science student at GISMA University Berlin. Currently seeking Part-Time, Internship, or Werkstudent roles in Data Science, Machine Learning, or Product Analytics in Berlin.",
    "Technical Product Builder and Software Engineer with proven expertise in CRM architecture, business intelligence dashboards, and agile project delivery. Built the Auslandly Consultancy CRM with real-time Supabase sync and LMS analytics tracking 10,000+ students. Experienced in CI/CD release management (saving 8 engineering hours weekly) and digital transformation modules at GISMA University Berlin. Seeking a Werkstudent or Part-Time role in Product Analytics, BI, or Tech Project Management in Berlin."
)

(RESUMES_DIR / "europass_cv_bi_product.html").write_text(v3_html, encoding="utf-8")
print("Generated: europass_cv_bi_product.html")

print("All 3 specialized Europass CV versions generated successfully!")
