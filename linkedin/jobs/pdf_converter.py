#!/usr/bin/env python3
"""
pdf_converter.py - High-Fidelity PDF Generation Engine for Resumes and Cover Letters.
Converts HTML Europass Resumes and Cover Letters to professional, printable PDF documents.
Uses Headless Chrome/Edge for 100% pixel-perfect vector rendering, with ReportLab pure-Python fallback.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def find_browser_executable():
    """Finds available Chrome or Edge binary on the system."""
    # 1. PATH search
    for name in ["chrome", "google-chrome", "chromium", "chromium-browser", "msedge"]:
        path = shutil.which(name)
        if path and os.path.exists(path):
            return path

    # 2. Windows standard installation locations
    windows_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
    ]
    for p in windows_paths:
        if os.path.exists(p):
            return p

    # 3. Linux standard locations
    linux_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/snap/bin/chromium"
    ]
    for p in linux_paths:
        if os.path.exists(p):
            return p

    return None

def convert_html_to_pdf(html_path, pdf_path=None):
    """
    Converts an HTML file to a clean, printable PDF document.
    html_path: Path or str to source HTML file.
    pdf_path: Optional destination Path or str. Defaults to same name with .pdf extension.
    Returns: Path object to generated PDF.
    """
    html_p = Path(html_path).resolve()
    if not html_p.exists():
        raise FileNotFoundError(f"HTML file not found: {html_p}")

    if pdf_path is None:
        pdf_p = html_p.with_suffix(".pdf")
    else:
        pdf_p = Path(pdf_path).resolve()

    pdf_p.parent.mkdir(parents=True, exist_ok=True)

    browser = find_browser_executable()
    if browser:
        try:
            # Use Chrome/Edge headless vector printing
            cmd = [
                browser,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                f"--print-to-pdf={str(pdf_p)}",
                str(html_p)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if res.returncode == 0 and pdf_p.exists() and pdf_p.stat().st_size > 1000:
                print(f"[PDF ENGINE] Generated PDF via {Path(browser).name}: {pdf_p.name} ({pdf_p.stat().st_size} bytes)")
                return pdf_p
        except Exception as e:
            print(f"[PDF WARNING] Browser PDF conversion failed: {e}. Falling back to ReportLab...")

    # Fallback: ReportLab fallback generator
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        import re

        raw_text = html_p.read_text(encoding="utf-8")
        clean_text = re.sub(r'<[^>]+>', ' ', raw_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        c = canvas.Canvas(str(pdf_p), pagesize=A4)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 800, "DANDU PURNACHANDRA MADHUKAR")
        c.setFont("Helvetica", 10)
        c.drawString(50, 785, "MSc Data Science Candidate • GISMA University Berlin • +49 15511064761")
        
        y = 750
        words = clean_text.split()
        line = []
        for word in words:
            line.append(word)
            if len(" ".join(line)) > 90:
                c.drawString(50, y, " ".join(line[:-1]))
                line = [word]
                y -= 14
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y = 800
        if line:
            c.drawString(50, y, " ".join(line))
        c.save()
        print(f"[PDF ENGINE] Generated PDF via ReportLab: {pdf_p.name}")
        return pdf_p
    except Exception as e:
        print(f"[PDF ERROR] All PDF conversion engines failed: {e}")
        return None

if __name__ == "__main__":
    test_html = BASE_DIR / "linkedin" / "jobs" / "europass_cv_purna.html"
    if test_html.exists():
        out = convert_html_to_pdf(test_html)
        print("Success:", out)
