#!/usr/bin/env python3
"""
server.py - Lightweight API & Dashboard Server for Purna's LinkedIn Editorial System.
Built with Python's standard library (zero external dependencies).
Serves the web dashboard and provides live REST APIs to read/update candidate queue,
audit quality with detect.py logic, manage editorial history, view visuals & PDF carousels,
run AI Trend Radar v2.0, run Empirical Sandbox Benchmarks, and manage the 360° Berlin Job Hub.
"""

import os
import sys
import json
import re
import math
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PORT = 3000
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent
LINKEDIN_DIR = WORKSPACE_DIR / "linkedin"
QUEUE_DIR = LINKEDIN_DIR / "queue"
VISUALS_DIR = LINKEDIN_DIR / "visuals"
TOOLS_DIR = LINKEDIN_DIR / "tools"
JOBS_DIR = LINKEDIN_DIR / "jobs"
RESUMES_DIR = JOBS_DIR / "resumes"
PACKETS_DIR = JOBS_DIR / "packets"
HISTORY_FILE = LINKEDIN_DIR / "editorial-history.json"
QUEUE_SUMMARY_FILE = QUEUE_DIR / "queue_summary.json"
SLOP_FILE = TOOLS_DIR / "slop.json"
JOBS_RADAR_FILE = JOBS_DIR / "jobs_radar.json"
APPLIED_HISTORY_FILE = JOBS_DIR / "applied_history.json"
PROFILE_MASTER_FILE = JOBS_DIR / "profile_master.json"
SCREENER_BANK_FILE = JOBS_DIR / "screener_bank.json"
REPORTS_DIR = JOBS_DIR / "reports"
EMAIL_CONFIG_FILE = JOBS_DIR / "email_config.json"
BENCHMARKS_FILE = LINKEDIN_DIR / "history" / "sandbox_benchmarks.json"
WEEKLY_AUDIT_FILE = LINKEDIN_DIR / "history" / "weekly_audit_report.json"

sys.path.insert(0, str(WORKSPACE_DIR))
try:
    from linkedin.tools import publisher
    from linkedin.tools import daemon
    from linkedin.tools import eu_growth_engine
    from linkedin.tools import trend_radar
    from linkedin.tools import sandbox_tester
    from linkedin.tools import weekly_growth_analyst
    from linkedin.tools import comment_engine
except ImportError:
    publisher = None
    daemon = None
    eu_growth_engine = None
    trend_radar = None
    sandbox_tester = None
    weekly_growth_analyst = None
    comment_engine = None

try:
    from linkedin.jobs import job_matcher
    from linkedin.jobs import resume_tailor
    from linkedin.jobs import cover_letter_generator
    from linkedin.jobs import job_dispatcher
    from linkedin.jobs import autonomous_job_agent
    from linkedin.jobs import daily_reporter
    from linkedin.jobs import multi_source_radar
except ImportError:
    job_matcher = None
    resume_tailor = None
    cover_letter_generator = None
    job_dispatcher = None
    autonomous_job_agent = None
    daily_reporter = None
    multi_source_radar = None


def load_slop_config():
    if SLOP_FILE.exists():
        with open(SLOP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"forbidden_words": [], "forbidden_phrases": [], "forbidden_endings": [], "dry_replacements": {}}


SLOP_CONFIG = load_slop_config()


# --- Detection Panel Logic (from detect.py) ---
def calc_burstiness(text):
    sentences = [s.strip() for s in re.split(r'[.!?\n]+', text) if len(s.strip()) > 0]
    if len(sentences) <= 1:
        return 50.0
    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std_dev = math.sqrt(variance)
    cv = std_dev / mean if mean > 0 else 0
    return round(min(100.0, cv * 120.0), 1)


def calc_specificity(text):
    tokens = text.split()
    if not tokens:
        return 0.0
    specific_patterns = [
        r'\d+(\.\d+)?k?',
        r'\$\d+|\€\d+',
        r'\b(v\d+\.\d+|python|docker|gpu|vram|ram|api|mit|apache|llm|ollama|vllm|sglang|deepseek|autogen|whisper|swe-bench|lmsys|github|claude|gemini|openai|anthropic)\b',
        r'\b[a-zA-Z0-9_-]+\.(py|json|md|txt|ts|js|pdf)\b',
        r'https?://',
        r'%',
        r'\b(tested|untested|benchmark|repo|commit|license|heuristic|heuristics|script|scripts|plugin|workflow)\b'
    ]
    matches = sum(len(re.findall(pat, text, re.IGNORECASE)) for pat in specific_patterns)
    density = matches / len(tokens)
    return round(min(100.0, density * 650.0), 1)


def calc_slop_density(text):
    words = text.split()
    if not words:
        return 100.0, 0, []
    forbidden_words = SLOP_CONFIG.get("forbidden_words", [])
    forbidden_phrases = SLOP_CONFIG.get("forbidden_phrases", [])
    detected = []
    slop_count = 0
    for phrase in forbidden_phrases:
        found = re.findall(re.escape(phrase), text, re.IGNORECASE)
        if found:
            slop_count += len(found) * 2
            detected.append(f"Phrase: '{phrase}'")
    for word in forbidden_words:
        found = re.findall(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE)
        if found:
            slop_count += len(found)
            detected.append(f"Word: '{word}'")
    per_100 = (slop_count / len(words)) * 100.0
    score = max(0.0, 100.0 - (per_100 * 25.0))
    return round(score, 1), slop_count, detected


def calc_fingerprint(text):
    penalties = 0.0
    issues = []
    if '—' in text:
        em_count = text.count('—')
        penalties += em_count * 30.0
        issues.append(f"{em_count} em-dash(es) ('—') detected")
    invisibles = ['\u200b', '\u200c', '\u200d', '\u2060', '\ufeff', '\u00ad']
    inv_count = sum(text.count(c) for c in invisibles)
    if inv_count > 0:
        penalties += inv_count * 25.0
        issues.append(f"{inv_count} hidden Unicode character(s)")
    curly_count = sum(text.count(c) for c in ['“', '”', '‘', '’'])
    if curly_count > 0:
        penalties += 15.0
        issues.append(f"{curly_count} curly quote(s) detected")
    return max(0.0, round(100.0 - penalties, 1)), issues


def calc_voice_and_tells(text):
    score = 100.0
    issues = []
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return 0.0, ["Empty draft"]
    last_line = lines[-1].lower()
    for ending in SLOP_CONFIG.get("forbidden_endings", []):
        if ending in last_line:
            score -= 25.0
            issues.append(f"Generic engagement bait ending: '{ending}'")
    lower_text = text.lower()
    agent_keywords = ["agent", "terminal", "code execution", "browser automation", "execute commands", "repo", "scripts"]
    if any(k in lower_text for k in agent_keywords):
        security_terms = ["sandbox", "credentials", "security", "production", "inspect"]
        if not any(s in lower_text for s in security_terms):
            score -= 25.0
            issues.append("Agent/execution tool mentioned without required sandboxing warning ('Sandbox it first').")
    tool_keywords = ["repo", "tool", "model", "release", "framework", "python"]
    if any(k in lower_text for k in tool_keywords):
        test_terms = ["tested", "haven't run", "haven't benchmarked", "based on", "documentation", "inspection"]
        if not any(t in lower_text for t in test_terms):
            score -= 20.0
            issues.append("Discusses tool/model without explicit tested vs untested status declaration.")
    return max(0.0, round(score, 1)), issues


def evaluate_draft(text):
    burstiness = calc_burstiness(text)
    specificity = calc_specificity(text)
    slop_score, slop_count, detected_slop = calc_slop_density(text)
    fingerprint, fp_issues = calc_fingerprint(text)
    voice_score, voice_issues = calc_voice_and_tells(text)
    checks = [burstiness, specificity, slop_score, fingerprint, voice_score]
    mean_score = sum(checks) / len(checks)
    min_score = min(checks)
    final_score = round((mean_score * 0.6) + (min_score * 0.4), 1)
    return {
        "final_score": final_score,
        "burstiness": burstiness,
        "specificity": specificity,
        "slop_score": slop_score,
        "slop_count": slop_count,
        "detected_slop": detected_slop,
        "fingerprint": fingerprint,
        "fingerprint_issues": fp_issues,
        "voice_score": voice_score,
        "voice_issues": voice_issues,
        "verdict": "PASS" if final_score >= 80.0 else "REVIEW NEEDED"
    }


def humanize_text(text):
    out = text
    out = out.replace("—", ", ")
    out = out.replace("–", "-")
    out = out.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    for inv in ['\u200b', '\u200c', '\u200d', '\u2060', '\ufeff', '\u00ad']:
        out = out.replace(inv, '')
    replacements = SLOP_CONFIG.get("dry_replacements", {})
    for word, repl in replacements.items():
        out = re.sub(r'\b' + re.escape(word) + r'\b', repl, out, flags=re.IGNORECASE)
    return out


def parse_candidate_markdown(file_path):
    if not file_path.exists():
        return {}
    content = file_path.read_text(encoding="utf-8")

    status_match = re.search(r'-\s*Status:\s*([A-Z_]+)', content)
    beat_match = re.search(r'-\s*Beat:\s*(.+)', content)
    score_match = re.search(r'-\s*Editorial Score:\s*(\d+)/100', content)

    why_now = ""
    wn_m = re.search(r'###\s*WHY NOW\s*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    if wn_m:
        why_now = wn_m.group(1).strip()

    angle = ""
    ang_m = re.search(r'###\s*INTERESTING ANGLE\s*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    if ang_m:
        angle = ang_m.group(1).strip()

    hooks = []
    hooks_m = re.search(r'###\s*HOOK OPTIONS\s*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    if hooks_m:
        raw_hooks = hooks_m.group(1).strip()
        parts = re.split(r'\n(?=\d+\.\s*\[)', raw_hooks)
        for p in parts:
            p = p.strip()
            if p:
                hooks.append(p)

    post_text = ""
    post_m = re.search(r'###\s*COMPLETE LINKEDIN POST[^\n]*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    if post_m:
        post_text = post_m.group(1).strip()

    catch = ""
    catch_m = re.search(r'###\s*THE CATCH\s*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    if catch_m:
        catch = catch_m.group(1).strip()

    replaces = ""
    rep_m = re.search(r'###\s*WHAT IT REPLACES\s*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    if rep_m:
        replaces = rep_m.group(1).strip()

    cost = ""
    cost_m = re.search(r'###\s*COST BREAKDOWN\s*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    if cost_m:
        cost = cost_m.group(1).strip()

    sources = ""
    src_m = re.search(r'###\s*(?:PRIMARY SOURCES|SOURCES)[^\n]*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    if src_m:
        sources = src_m.group(1).strip()

    return {
        "status": status_match.group(1) if status_match else "WAITING_FOR_APPROVAL",
        "beat": beat_match.group(1) if beat_match else "Free & Open-Source AI Agent",
        "score": int(score_match.group(1)) if score_match else 90,
        "why_now": why_now,
        "angle": angle,
        "hooks": hooks,
        "post_text": post_text,
        "catch": catch,
        "replaces": replaces,
        "cost": cost,
        "sources": sources,
        "raw_markdown": content
    }


class EditorialHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Static Visuals routing (supports SVG, PNG, JPG, PDF Carousels, and HTML Carousel decks)
        if path.startswith("/visuals/"):
            filename = path.replace("/visuals/", "")
            file_path = VISUALS_DIR / filename
            if file_path.exists():
                self.send_response(200)
                if filename.endswith(".svg"):
                    self.send_header("Content-Type", "image/svg+xml")
                elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
                    self.send_header("Content-Type", "image/jpeg")
                elif filename.endswith(".png"):
                    self.send_header("Content-Type", "image/png")
                elif filename.endswith(".pdf"):
                    self.send_header("Content-Type", "application/pdf")
                    self.send_header("Content-Disposition", f'inline; filename="{filename}"')
                elif filename.endswith(".html"):
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
                return
            else:
                self.send_error(404, "Visual asset not found")
                return

        # Pre-Mapped 1-Click ATS Application Packets routing
        if path.startswith("/packets/") or path.startswith("/linkedin/jobs/packets/"):
            filename = path.replace("/linkedin/jobs/packets/", "").replace("/packets/", "")
            file_path = PACKETS_DIR / filename
            if file_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
                return
            else:
                self.send_error(404, "ATS packet not found")
                return

        # Mobile Portal / Student Jobs Hub routing
        if path in ["/mobile", "/jobs", "/hub"]:
            portal_file = WORKSPACE_DIR / "index.html"
            if portal_file.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(portal_file.read_bytes())
                return

        # Static Tailored Resumes routing (supports both /resumes/ and /linkedin/jobs/resumes/)
        if path.startswith("/resumes/") or path.startswith("/linkedin/jobs/resumes/"):
            filename = path.replace("/linkedin/jobs/resumes/", "").replace("/resumes/", "")
            file_path = RESUMES_DIR / filename

            # JIT on-demand PDF compilation if HTML exists
            if not file_path.exists() and filename.endswith(".pdf"):
                html_path = file_path.with_suffix(".html")
                if html_path.exists():
                    try:
                        from linkedin.jobs import pdf_converter
                        pdf_converter.convert_html_to_pdf(html_path, file_path)
                    except Exception as e:
                        print(f"[PDF JIT Error] Could not compile {filename}: {e}")

            if file_path.exists():
                self.send_response(200)
                if filename.endswith(".html"):
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                elif filename.endswith(".pdf"):
                    self.send_header("Content-Type", "application/pdf")
                    self.send_header("Content-Disposition", f'inline; filename="{filename}"')
                elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
                    self.send_header("Content-Type", "image/jpeg")
                elif filename.endswith(".png"):
                    self.send_header("Content-Type", "image/png")
                else:
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
                return
            else:
                self.send_error(404, "Resume file not found")
                return

        # Static Reports routing (supports both /reports/ and /linkedin/jobs/reports/)
        if path.startswith("/reports/") or path.startswith("/linkedin/jobs/reports/"):
            filename = path.replace("/linkedin/jobs/reports/", "").replace("/reports/", "")
            file_path = REPORTS_DIR / filename
            if file_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
                return
            else:
                self.send_error(404, "Report file not found")
                return

        # Static Workspace Routing for /linkedin/
        if path.startswith("/linkedin/"):
            rel_p = path.lstrip("/")
            file_path = WORKSPACE_DIR / rel_p
            if file_path.exists() and file_path.is_file():
                self.send_response(200)
                if rel_p.endswith(".json"):
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                elif rel_p.endswith(".html"):
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                elif rel_p.endswith(".pdf"):
                    self.send_header("Content-Type", "application/pdf")
                elif rel_p.endswith(".jpg") or rel_p.endswith(".jpeg"):
                    self.send_header("Content-Type", "image/jpeg")
                elif rel_p.endswith(".png"):
                    self.send_header("Content-Type", "image/png")
                else:
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
                return
            else:
                self.send_error(404, f"File not found: {path}")
                return

        # OAuth routes
        if path == "/auth/linkedin":
            if not publisher:
                self.send_error(500, "Publisher module not available")
                return
            try:
                auth_url = publisher.get_auth_url()
                self.send_response(302)
                self.send_header("Location", auth_url)
                self.end_headers()
                return
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"<h3>OAuth Setup Needed</h3><p>{e}</p><p><a href='/'>&larr; Return to Dashboard</a></p>".encode("utf-8"))
                return

        if path == "/auth/callback":
            if not publisher:
                self.send_error(500, "Publisher module not available")
                return
            qs = parse_qs(parsed.query)
            code = qs.get("code", [None])[0]
            error = qs.get("error_description", qs.get("error", [None]))[0]
            if error:
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"<h3>LinkedIn Authorization Failed</h3><p>{error}</p><p><a href='/'>&larr; Return to Dashboard</a></p>".encode("utf-8"))
                return
            if code:
                try:
                    publisher.exchange_code_for_token(code)
                    self.send_response(302)
                    self.send_header("Location", "/?linkedin_connected=true")
                    self.end_headers()
                    return
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(f"<h3>Token Exchange Failed</h3><p>{e}</p><p><a href='/'>&larr; Return to Dashboard</a></p>".encode("utf-8"))
                    return

        # API Endpoints
        if path == "/api/queue":
            self.handle_get_queue()
        elif path == "/api/history":
            self.handle_get_history()
        elif path == "/api/trends":
            self.handle_get_trends()
        elif path == "/api/benchmarks":
            self.handle_get_benchmarks()
        elif path == "/api/visuals":
            self.handle_get_visuals()
        elif path == "/api/calendar":
            self.handle_get_calendar()
        elif path == "/api/status":
            self.handle_get_status()
        elif path == "/api/daemon/status":
            self.handle_get_daemon_status()
        elif path == "/api/analytics":
            self.handle_get_analytics()
        elif path in ("/api/replies", "/api/comments"):
            self.handle_get_replies()
        elif path == "/api/jobs/radar":
            self.handle_get_jobs_radar()
        elif path == "/api/jobs/radar/refresh":
            self.handle_refresh_jobs_radar()
        elif path == "/api/jobs/applied":
            self.handle_get_jobs_applied()
        elif path == "/api/jobs/profile":
            self.handle_get_jobs_profile()
        elif path == "/api/jobs/auto-apply/status":
            self.handle_get_auto_apply_status()
        elif path == "/api/jobs/reports/latest":
            self.handle_get_latest_report()
        elif path == "/api/jobs/email-config":
            self.handle_get_email_config()
        elif path == "/api/linkedin/status":
            if publisher:
                self.send_json(publisher.get_connection_status())
            else:
                self.send_json({"configured": False, "connected": False})
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b'{}'
        try:
            data = json.loads(post_body.decode('utf-8'))
        except Exception:
            data = {}

        if path == "/api/candidate/status":
            self.handle_post_candidate_status(data)
        elif path == "/api/detect":
            self.handle_post_detect(data)
        elif path == "/api/humanize":
            self.handle_post_humanize(data)
        elif path == "/api/candidate/save":
            self.handle_post_candidate_save(data)
        elif path == "/api/publish":
            self.handle_post_publish(data)
        elif path == "/api/trends/scout":
            self.handle_post_trends_scout(data)
        elif path == "/api/benchmarks/run":
            self.handle_post_benchmarks_run(data)
        elif path == "/api/daemon/cycle":
            self.handle_post_daemon_cycle(data)
        elif path == "/api/comments/post":
            self.handle_post_comment_live(data)
        elif path == "/api/comments/generate":
            self.handle_post_comment_generate(data)
        elif path == "/api/comments/batch":
            self.handle_post_comment_batch(data)
        elif path == "/api/linkedin/credentials":
            self.handle_post_linkedin_credentials(data)
        elif path == "/api/jobs/score":
            self.handle_post_jobs_score(data)
        elif path == "/api/jobs/apply":
            self.handle_post_jobs_apply(data)
        elif path == "/api/jobs/radar/refresh":
            self.handle_refresh_jobs_radar()
        elif path == "/api/jobs/auto-apply/toggle":
            self.handle_post_auto_apply_toggle(data)
        elif path == "/api/jobs/auto-apply/run-now":
            self.handle_post_auto_apply_run_now(data)
        elif path == "/api/jobs/auto-apply/config":
            self.handle_post_auto_apply_config(data)
        elif path in ("/api/jobs/reports/send-now", "/api/jobs/report/send-now"):
            self.handle_post_report_send_now(data)
        elif path == "/api/jobs/email-config":
            self.handle_post_email_config(data)
        else:
            self.send_error(404, "Unknown API route")

    def send_json(self, data_obj, code=200):
        body = json.dumps(data_obj, indent=2).encode('utf-8')
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_get_queue(self):
        queue_summary = {}
        if QUEUE_SUMMARY_FILE.exists():
            with open(QUEUE_SUMMARY_FILE, "r", encoding="utf-8") as f:
                queue_summary = json.load(f)

        if daemon:
            queue_summary = daemon.sync_published_candidates_in_queue(queue_summary)

        candidates = queue_summary.get("candidates", [])
        enriched = []
        for c in candidates:
            c_file = WORKSPACE_DIR / c.get("file", "")
            parsed_data = parse_candidate_markdown(c_file)
            orig_status = c.get("status")
            item = dict(c)
            item.update(parsed_data)
            if orig_status == "PUBLISHED":
                item["status"] = "PUBLISHED"

            v_path = c.get("visual", "")
            if v_path:
                v_file = WORKSPACE_DIR / v_path
                item["visual_exists"] = v_file.exists()
                item["visual_url"] = f"/visuals/{v_file.name}" if v_file.exists() else None
                # Provide PNG preview thumbnail when primary asset is a PDF carousel
                if v_file.suffix.lower() == ".pdf":
                    png_thumb = VISUALS_DIR / v_file.name.replace("carousel_", "visual_").replace(".pdf", ".png")
                    item["visual_thumb_url"] = f"/visuals/{png_thumb.name}" if png_thumb.exists() else None
                else:
                    item["visual_thumb_url"] = item["visual_url"]
            else:
                item["visual_exists"] = False
                item["visual_url"] = None
                item["visual_thumb_url"] = None

            enriched.append(item)

        self.send_json({
            "queue_id": queue_summary.get("queue_id", "queue-active"),
            "updated_at": queue_summary.get("updated_at", ""),
            "candidates": enriched
        })

    def handle_post_candidate_status(self, data):
        c_id = data.get("id")
        new_status = data.get("status")
        if not c_id or not new_status:
            self.send_json({"error": "id and status required"}, 400)
            return

        if not QUEUE_SUMMARY_FILE.exists():
            self.send_json({"error": "queue_summary.json not found"}, 500)
            return

        with open(QUEUE_SUMMARY_FILE, "r", encoding="utf-8") as f:
            queue_summary = json.load(f)

        target_file = None
        for c in queue_summary.get("candidates", []):
            if c.get("id") == c_id:
                c["status"] = new_status
                target_file = WORKSPACE_DIR / c.get("file", "")
                break

        with open(QUEUE_SUMMARY_FILE, "w", encoding="utf-8") as f:
            json.dump(queue_summary, f, indent=2)

        if target_file and target_file.exists():
            content = target_file.read_text(encoding="utf-8")
            content = re.sub(r'-\s*Status:\s*[A-Z_]+', f'- Status: {new_status}', content)
            target_file.write_text(content, encoding="utf-8")

        self.send_json({
            "success": True,
            "id": c_id,
            "status": new_status,
            "message": f"Candidate {c_id} status updated to {new_status}"
        })

    def handle_post_candidate_save(self, data):
        c_id = data.get("id")
        post_text = data.get("post_text")
        if not c_id or not post_text:
            self.send_json({"error": "id and post_text required"}, 400)
            return

        with open(QUEUE_SUMMARY_FILE, "r", encoding="utf-8") as f:
            queue_summary = json.load(f)

        target_file = None
        for c in queue_summary.get("candidates", []):
            if c.get("id") == c_id:
                target_file = WORKSPACE_DIR / c.get("file", "")
                break

        if target_file and target_file.exists():
            content = target_file.read_text(encoding="utf-8")
            pattern = r'(###\s*COMPLETE LINKEDIN POST[^\n]*\n)(.*?)(?=\n###|\n---|\Z)'
            replacement = r'\g<1>\n' + post_text.strip() + '\n\n'
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            target_file.write_text(new_content, encoding="utf-8")
            self.send_json({"success": True, "message": f"Candidate {c_id} saved successfully"})
        else:
            self.send_json({"error": "Candidate file not found"}, 404)

    def handle_post_detect(self, data):
        text = data.get("text", "")
        res = evaluate_draft(text)
        self.send_json(res)

    def handle_post_humanize(self, data):
        text = data.get("text", "")
        cleaned = humanize_text(text)
        res = evaluate_draft(cleaned)
        self.send_json({
            "cleaned_text": cleaned,
            "evaluation": res
        })

    def handle_get_history(self):
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                self.send_json(json.load(f))
        else:
            self.send_json({"topics": []})

    def handle_get_trends(self):
        trends = []
        if trend_radar and hasattr(trend_radar, "CURATED_BREAKTHROUGHS"):
            for item in trend_radar.CURATED_BREAKTHROUGHS:
                trends.append({
                    "id": item["id"],
                    "title": item["topic"],
                    "beat": item["beat"],
                    "score": item["score"],
                    "hook": item["hook_selected"],
                    "why_now": item["why_now"],
                    "replaces": item["replaces"],
                    "repo": item["repo"],
                    "license": item["license"],
                    "stars": f"Format: {item.get('format', 'image-attached')}",
                    "evidence": [item["repo"]]
                })

        # Also append live GitHub discoveries from editorial-history.json
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    ed = json.load(f)
                for idx, t in enumerate(ed.get("topics", [])):
                    if t.get("id", "").startswith("live-gh-"):
                        trends.append({
                            "id": 100 + idx,
                            "title": t.get("title", "GitHub AI Breakthrough"),
                            "beat": t.get("category", "Free & Open-Source AI Agent"),
                            "score": t.get("score", 88),
                            "hook": t.get("angle", "Open-source self-hosted alternative"),
                            "why_now": f"Scouted live from GitHub API on {t.get('date', 'today')}.",
                            "replaces": "Proprietary SaaS workflow wrappers",
                            "repo": t.get("primary_source", "https://github.com"),
                            "license": "Open Source",
                            "stars": "Live GitHub Scout",
                            "evidence": [t.get("primary_source", "")]
                        })
            except Exception:
                pass

        self.send_json(trends)

    def handle_post_trends_scout(self, data):
        if not trend_radar:
            self.send_json({"success": False, "error": "trend_radar module not loaded"}, 500)
            return
        try:
            discovered = trend_radar.fetch_live_github_and_arxiv_trends()
            added = trend_radar.replenish_queue(render_visuals=False)
            self.send_json({
                "success": True,
                "live_discovered": len(discovered),
                "candidates_queued": added,
                "discoveries": discovered
            })
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 500)

    def handle_get_benchmarks(self):
        if BENCHMARKS_FILE.exists():
            try:
                with open(BENCHMARKS_FILE, "r", encoding="utf-8") as f:
                    self.send_json(json.load(f))
                    return
            except Exception:
                pass
        self.send_json({"runs": []})

    def handle_post_benchmarks_run(self, data):
        if not sandbox_tester:
            self.send_json({"success": False, "error": "sandbox_tester module not loaded"}, 500)
            return
        try:
            res = sandbox_tester.analyze_local_repo_footprint(str(LINKEDIN_DIR))
            sandbox_tester.log_benchmark_result(res, update_markdown=True)
            self.send_json({"success": True, "result": res})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 500)

    def handle_get_visuals(self):
        items = []
        if VISUALS_DIR.exists():
            for f in sorted(VISUALS_DIR.iterdir()):
                ext = f.suffix.lower()
                if ext in [".svg", ".jpg", ".jpeg", ".png", ".pdf"]:
                    thumb_url = f"/visuals/{f.name}"
                    if ext == ".pdf":
                        png_comp = VISUALS_DIR / f.name.replace("carousel_", "visual_").replace(".pdf", ".png")
                        if png_comp.exists():
                            thumb_url = f"/visuals/{png_comp.name}"
                    items.append({
                        "name": f.name,
                        "type": "PDF CAROUSEL" if ext == ".pdf" else ext.replace(".", "").upper(),
                        "url": f"/visuals/{f.name}",
                        "thumb_url": thumb_url,
                        "size_bytes": f.stat().st_size
                    })
        self.send_json(items)

    def handle_get_calendar(self):
        calendar = [
            {"day": "Monday", "pillar": "Agent KV Cache & Serving", "topic": "SGLang RadixAttention (Multi-Turn Agent KV Cache Reuse)", "candidate_id": 13, "status": "PUBLISHED", "format": "5-Slide PDF Carousel"},
            {"day": "Tuesday", "pillar": "AI Models & Inference Architecture", "topic": "DeepSeek Multi-Head Latent Attention (MLA) & KV Cache Compression", "candidate_id": 14, "status": "PUBLISHED", "format": "Canva Comparison + Text"},
            {"day": "Wednesday", "pillar": "AI Hardware & Local Inference", "topic": "vLLM V1 Architecture (Decoupled ZeroMQ Engine & GIL Removal)", "candidate_id": 15, "status": "PUBLISHED", "format": "Canva Comparison + Text"},
            {"day": "Thursday", "pillar": "Autonomous Agent Architecture", "topic": "Microsoft AutoGen v0.4 (Event-Driven Actor Architecture)", "candidate_id": 16, "status": "APPROVED", "format": "Canva Comparison + Text"},
            {"day": "Friday", "pillar": "Research & Thesis Discovery", "topic": "Internal Hidden-State Probing for Agent Trajectory Hallucinations", "candidate_id": 17, "status": "APPROVED", "format": "Text-Only (Dwell-Optimized)"},
            {"day": "Saturday", "pillar": "Everyday AI Automation", "topic": "faster-whisper (Local CTranslate2 GPU Audio Transcription vs Cloud SaaS)", "candidate_id": 18, "status": "APPROVED", "format": "Canva Comparison + Text"},
            {"day": "Sunday", "pillar": "7-Day Telemetry & Queue Replenishment", "topic": "Weekly Growth Audit & Live GitHub Trend Scout v2.0", "candidate_id": None, "status": "AUTOMATED", "format": "System Telemetry"}
        ]
        self.send_json(calendar)

    def handle_get_status(self):
        queue_summary = {}
        if QUEUE_SUMMARY_FILE.exists():
            with open(QUEUE_SUMMARY_FILE, "r", encoding="utf-8") as f:
                queue_summary = json.load(f)
        if daemon:
            queue_summary = daemon.sync_published_candidates_in_queue(queue_summary)
        candidates = queue_summary.get("candidates", [])
        counts = {
            "total": len(candidates),
            "approved": sum(1 for c in candidates if c.get("status") == "APPROVED"),
            "waiting": sum(1 for c in candidates if c.get("status") == "WAITING_FOR_APPROVAL"),
            "published": sum(1 for c in candidates if c.get("status") == "PUBLISHED"),
            "draft": sum(1 for c in candidates if c.get("status") == "DRAFT")
        }
        self.send_json({
            "status": "online",
            "counts": counts,
            "port": PORT
        })

    def handle_post_linkedin_credentials(self, data):
        if not publisher:
            self.send_json({"error": "Publisher module not available"}, 500)
            return
        cid = data.get("client_id", "").strip()
        csec = data.get("client_secret", "").strip()
        ruri = data.get("redirect_uri", "").strip() or publisher.DEFAULT_REDIRECT_URI

        if not cid or not csec:
            self.send_json({"error": "Both Client ID and Client Secret are required."}, 400)
            return

        creds = publisher.load_credentials()
        creds["client_id"] = cid
        creds["client_secret"] = csec
        creds["redirect_uri"] = ruri
        publisher.save_credentials(creds)
        self.send_json({
            "success": True,
            "status": publisher.get_connection_status()
        })

    def handle_post_publish(self, data):
        c_id = data.get("id")
        if not c_id:
            self.send_json({"error": "Candidate ID is required."}, 400)
            return

        if not publisher:
            self.send_json({"error": "Publisher module not available"}, 500)
            return

        conn_status = publisher.get_connection_status()
        if not conn_status.get("connected"):
            self.send_json({
                "success": False,
                "status": "Post approved, but LinkedIn account is not authorized.",
                "action_needed": "connect_linkedin",
                "instructions": "Please enter your Client ID & Secret and authorize your app via the dashboard."
            }, 400)
            return

        queue_summary = {}
        if QUEUE_SUMMARY_FILE.exists():
            with open(QUEUE_SUMMARY_FILE, "r", encoding="utf-8") as f:
                queue_summary = json.load(f)

        candidate_entry = None
        for c in queue_summary.get("candidates", []):
            if str(c.get("id")) == str(c_id):
                candidate_entry = c
                break

        if not candidate_entry:
            self.send_json({"error": f"Candidate #{c_id} not found."}, 404)
            return

        c_file = WORKSPACE_DIR / candidate_entry.get("file", "")
        parsed_data = parse_candidate_markdown(c_file)
        topic = candidate_entry.get("topic", "")

        current_status = candidate_entry.get("status")
        if current_status not in ("APPROVED", "PUBLISHED"):
            candidate_entry["status"] = "APPROVED"

        post_text = parsed_data.get("post_text", "").strip()
        if not post_text:
            self.send_json({"error": "Post text is empty."}, 400)
            return

        raw_sources = parsed_data.get("sources", "")
        clean_sources = "\n".join(
            line for line in raw_sources.splitlines()
            if not line.strip().startswith(">")
        ).strip()

        with_image = data.get("with_image", True)
        image_path = None

        if with_image and candidate_entry.get("format") != "text-only":
            v_rel = candidate_entry.get("visual", "")
            if v_rel:
                v_file = WORKSPACE_DIR / v_rel
                if v_file.exists():
                    if v_file.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf"):
                        image_path = str(v_file)
                    elif v_file.suffix.lower() == ".svg":
                        png_cand = v_file.with_suffix(".png")
                        if png_cand.exists():
                            image_path = str(png_cand)

        if not image_path:
            tail = post_text[-250:].lower()
            if "github.com" not in tail and "arxiv.org" not in tail:
                sources_str = parsed_data.get("sources", "") + " " + parsed_data.get("raw_markdown", "")
                m = re.search(r'https?://(?:github\.com|arxiv\.org)/[a-zA-Z0-9_./-]+', sources_str)
                if m:
                    post_text = post_text.rstrip() + f"\n\nRepo: {m.group(0)}"
            else:
                post_text = re.sub(r'Repo:\s*github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)', r'Repo: https://github.com/\1', post_text)

        try:
            result = publisher.publish_candidate_post(
                post_text,
                image_path=image_path,
                first_comment_text=clean_sources if image_path else None,
                document_title=topic,
                candidate_id=c_id,
                topic=topic,
                allow_repost=bool(data.get("allow_repost", False))
            )
            publisher.record_published_post(
                c_id,
                {
                    "topic": topic,
                    "post_text": post_text,
                    "sources": clean_sources if image_path else "GitHub link included in post text. No first comment needed.",
                    "has_image": bool(image_path),
                    "comment_needed": bool(image_path)
                },
                result
            )
            self.send_json({
                "success": True,
                "status": "PUBLISHED",
                "has_image": bool(image_path),
                "comment_needed": bool(image_path),
                "first_comment_posted": result.get("first_comment_posted", False),
                "post_id": result.get("post_id"),
                "post_url": result.get("post_url"),
                "published_at": result.get("published_at"),
                "candidate_id": c_id
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_json({
                "success": False,
                "error": f"LinkedIn Publishing Failed: {str(e)}",
                "candidate_id": c_id
            }, 500)

    def handle_get_daemon_status(self):
        status_file = LINKEDIN_DIR / "history" / "daemon_status.json"
        if status_file.exists():
            try:
                with open(status_file, "r", encoding="utf-8") as f:
                    self.send_json(json.load(f))
                    return
            except Exception:
                pass

        if eu_growth_engine:
            now_dt = eu_growth_engine.get_berlin_now()
            is_prime, win = eu_growth_engine.is_eu_prime_time(now_dt)
            next_slot = eu_growth_engine.get_next_eu_prime_window(now_dt)
            self.send_json({
                "status": "RUNNING",
                "current_time_cet": now_dt.strftime("%Y-%m-%d %H:%M:%S CET"),
                "is_eu_prime_time": is_prime,
                "current_window": win["name"] if win else "Off-Peak / Monitoring",
                "next_scheduled_drop": next_slot["formatted"],
                "target_audience": "European Union (Berlin, Munich, Amsterdam, Paris, Zurich)",
                "auto_publish_enabled": True
            })
        else:
            self.send_json({"status": "IDLE"})

    def handle_get_analytics(self):
        analytics_file = LINKEDIN_DIR / "history" / "analytics_matrix.json"
        learnings_file = LINKEDIN_DIR / "history" / "eu_reach_learnings.json"
        data = {}
        if WEEKLY_AUDIT_FILE.exists():
            try:
                with open(WEEKLY_AUDIT_FILE, "r", encoding="utf-8") as f:
                    audit_data = json.load(f)
                    data.update(audit_data)
            except Exception:
                pass
        if analytics_file.exists():
            try:
                with open(analytics_file, "r", encoding="utf-8") as f:
                    data["analytics"] = json.load(f)
            except Exception:
                pass
        if learnings_file.exists():
            try:
                with open(learnings_file, "r", encoding="utf-8") as f:
                    data["learnings"] = json.load(f)
            except Exception:
                pass
        self.send_json(data)

    def handle_get_replies(self):
        replies_file = LINKEDIN_DIR / "history" / "pending_replies.json"
        comment_log_file = LINKEDIN_DIR / "history" / "comment_engagement_log.json"
        ext_comments_file = LINKEDIN_DIR / "history" / "external_comments_log.json"
        radar_file = LINKEDIN_DIR / "history" / "external_engagement_radar.json"
        payload = {"pending": [], "comments_posted": [], "external_comments": [], "external_stream_posts": [], "radar_items": []}
        if replies_file.exists():
            try:
                with open(replies_file, "r", encoding="utf-8") as f:
                    payload.update(json.load(f))
            except Exception:
                pass
        if comment_log_file.exists():
            try:
                with open(comment_log_file, "r", encoding="utf-8") as f:
                    c_data = json.load(f)
                    payload["comments_posted"] = c_data.get("comments_posted", [])
                    payload["total_live_comments"] = c_data.get("total_live_comments", len(payload["comments_posted"]))
            except Exception:
                pass
        if ext_comments_file.exists():
            try:
                with open(ext_comments_file, "r", encoding="utf-8") as f:
                    e_data = json.load(f)
                    payload["external_comments"] = e_data.get("external_comments", [])
                    payload["total_external_comments"] = e_data.get("total_external_comments", len(payload["external_comments"]))
            except Exception:
                pass
        if radar_file.exists():
            try:
                with open(radar_file, "r", encoding="utf-8") as f:
                    r_data = json.load(f)
                    payload["radar_items"] = r_data.get("radar_items", [])
                    payload["external_stream_posts"] = r_data.get("external_stream_posts", [])
            except Exception:
                pass
        self.send_json(payload)

    def handle_post_comment_live(self, data):
        if not comment_engine:
            self.send_json({"success": False, "error": "comment_engine module not loaded"}, 500)
            return
        target_urn = data.get("post_urn") or data.get("post_url") or ""
        comment_text = data.get("comment_text", "")
        topic = data.get("topic", "")
        candidate_id = data.get("candidate_id")
        allow_dup = bool(data.get("allow_duplicate", False))
        try:
            res = comment_engine.post_live_comment_to_linkedin(
                target_urn_or_url=target_urn,
                comment_text=comment_text,
                topic=topic,
                candidate_id=candidate_id,
                allow_duplicate=allow_dup
            )
            self.send_json(res, 200 if res.get("success") else 400)
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 500)

    def handle_post_comment_generate(self, data):
        if not comment_engine:
            self.send_json({"success": False, "error": "comment_engine module not loaded"}, 500)
            return
        post_text = data.get("post_text", "")
        post_url = data.get("post_url", "")
        author_name = data.get("author_name", "")
        auto_post = bool(data.get("auto_post", False))
        try:
            gen = comment_engine.generate_post_based_comments(post_text, post_url=post_url, author_name=author_name)
            if auto_post and gen.get("extracted_urn") and gen.get("generated_comments"):
                first_comment = gen["generated_comments"][0]["text"]
                live_res = comment_engine.post_live_comment_to_linkedin(
                    target_urn_or_url=gen["extracted_urn"],
                    comment_text=first_comment,
                    topic=gen.get("topic_summary", "External LinkedIn Post"),
                    allow_duplicate=True
                )
                gen["live_post_result"] = live_res
            self.send_json({"success": True, **gen})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 500)

    def handle_post_comment_batch(self, data):
        if not comment_engine:
            self.send_json({"success": False, "error": "comment_engine module not loaded"}, 500)
            return
        try:
            res = comment_engine.run_live_auto_comment_batch()
            self.send_json({"success": True, **res})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 500)

    def handle_post_daemon_cycle(self, data):
        force = data.get("force_publish", False)
        if daemon:
            try:
                pub = daemon.run_single_cycle(force_publish=force)
                self.send_json({"success": True, "published": pub})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 500)
        else:
            self.send_json({"error": "Daemon module not loaded"}, 500)

    def handle_get_jobs_radar(self):
        if JOBS_RADAR_FILE.exists():
            try:
                with open(JOBS_RADAR_FILE, "r", encoding="utf-8") as f:
                    self.send_json(json.load(f))
                    return
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
                return
        self.send_json({"jobs": []})

    def handle_refresh_jobs_radar(self):
        try:
            if multi_source_radar:
                radar_data = multi_source_radar.refresh_360_berlin_radar()
            else:
                from linkedin.jobs import linkedin_scraper
                linkedin_scraper.refresh_jobs_radar()
                with open(JOBS_RADAR_FILE, "r", encoding="utf-8") as f:
                    radar_data = json.load(f)

            if JOBS_RADAR_FILE.exists():
                with open(JOBS_RADAR_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for job in data.get("jobs", []):
                    try:
                        if resume_tailor:
                            resume_tailor.generate_tailored_resume(job)
                        if cover_letter_generator:
                            cover_letter_generator.generate_tailored_cover_letter(job)
                    except Exception:
                        pass
                if job_dispatcher and hasattr(job_dispatcher, "backfill_applied_packets"):
                    job_dispatcher.backfill_applied_packets()
                self.send_json({"success": True, "count": len(data.get("jobs", [])), "radar": data})
                return
            self.send_json({"success": True, "count": 0})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 500)

    def handle_get_jobs_applied(self):
        if APPLIED_HISTORY_FILE.exists():
            try:
                with open(APPLIED_HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.send_json(json.load(f))
                    return
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
                return
        self.send_json([])

    def handle_get_jobs_profile(self):
        prof = {}
        screen = {}
        if PROFILE_MASTER_FILE.exists():
            try:
                with open(PROFILE_MASTER_FILE, "r", encoding="utf-8") as f:
                    prof = json.load(f)
            except Exception:
                pass
        if SCREENER_BANK_FILE.exists():
            try:
                with open(SCREENER_BANK_FILE, "r", encoding="utf-8") as f:
                    screen = json.load(f)
            except Exception:
                pass
        self.send_json({
            "profile": prof,
            "screener_bank": screen
        })

    def handle_post_jobs_score(self, data):
        if not job_matcher:
            self.send_json({"error": "Job matcher module not loaded"}, 500)
            return
        jd_text = data.get("jd_text", "").strip()
        role_title = data.get("role_title", "AI Engineer")
        company = data.get("company", "Tech Company")
        location = data.get("location", "Berlin, Germany")
        if not jd_text:
            self.send_json({"error": "Job description text is required"}, 400)
            return

        try:
            score_result = job_matcher.evaluate_job_match({
                "title": role_title,
                "company": company,
                "location": location,
                "description": jd_text
            })
            self.send_json(score_result)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_post_jobs_apply(self, data):
        if not job_dispatcher:
            self.send_json({"error": "Job dispatcher module not loaded"}, 500)
            return
        job_id = data.get("job_id")
        if not job_id:
            self.send_json({"error": "job_id is required"}, 400)
            return
        try:
            res = job_dispatcher.apply_to_job(job_id)
            self.send_json({"success": True, "application": res})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 500)

    def handle_get_auto_apply_status(self):
        if not autonomous_job_agent:
            self.send_json({"error": "Autonomous job agent module not loaded"}, 500)
            return
        cfg = autonomous_job_agent.get_config()
        logs = autonomous_job_agent.get_logs(limit=40)
        self.send_json({
            "config": cfg,
            "logs": logs
        })

    def handle_post_auto_apply_toggle(self, data):
        if not autonomous_job_agent:
            self.send_json({"error": "Autonomous job agent module not loaded"}, 500)
            return
        enabled = data.get("enabled")
        if enabled is None:
            cfg = autonomous_job_agent.get_config()
            enabled = not cfg.get("enabled", True)
        updated = autonomous_job_agent.update_config({"enabled": bool(enabled)})
        autonomous_job_agent.append_log(f"Auto-Apply toggled: {'ENABLED (Running 24/7)' if updated.get('enabled') else 'PAUSED'}")
        self.send_json({"success": True, "config": updated})

    def handle_post_auto_apply_run_now(self, data):
        if not autonomous_job_agent:
            self.send_json({"error": "Autonomous job agent module not loaded"}, 500)
            return
        try:
            autonomous_job_agent.append_log("Dashboard operator triggered instant Auto-Apply batch run.")
            res = autonomous_job_agent.run_autonomous_cycle(force=True)
            self.send_json({"success": True, "result": res})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 500)

    def handle_post_auto_apply_config(self, data):
        if not autonomous_job_agent:
            self.send_json({"error": "Autonomous job agent module not loaded"}, 500)
            return
        updates = {}
        if "daily_limit" in data:
            updates["daily_limit"] = int(data["daily_limit"])
        if "min_match_score" in data:
            updates["min_match_score"] = int(data["min_match_score"])
        updated = autonomous_job_agent.update_config(updates)
        self.send_json({"success": True, "config": updated})

    def handle_get_latest_report(self):
        latest_file = REPORTS_DIR / "latest_daily_report.html"
        email_cfg = {}
        if EMAIL_CONFIG_FILE.exists():
            try:
                with open(EMAIL_CONFIG_FILE, "r", encoding="utf-8") as f:
                    email_cfg = json.load(f)
            except Exception:
                pass
        self.send_json({
            "exists": latest_file.exists(),
            "report_url": "/reports/latest_daily_report.html" if latest_file.exists() else None,
            "email_config": email_cfg
        })

    def handle_get_email_config(self):
        if not daily_reporter:
            self.send_json({"error": "Daily reporter not loaded"}, 500)
            return
        cfg = daily_reporter.get_email_config()
        safe_cfg = dict(cfg)
        safe_cfg["has_password"] = bool(safe_cfg.get("smtp_password"))
        safe_cfg["smtp_password"] = "••••••••" if safe_cfg.get("smtp_password") else ""
        self.send_json(safe_cfg)

    def handle_post_report_send_now(self, data):
        if not daily_reporter:
            self.send_json({"error": "Daily reporter not loaded"}, 500)
            return
        try:
            res = daily_reporter.send_daily_summary_report(force=True)
            self.send_json({"success": True, "result": res})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 500)

    def handle_post_email_config(self, data):
        if not daily_reporter:
            self.send_json({"error": "Daily reporter not loaded"}, 500)
            return
        updates = {}
        if "recipient_email" in data:
            updates["recipient_email"] = str(data["recipient_email"]).strip()
        if "smtp_password" in data and data["smtp_password"] != "••••••••":
            updates["smtp_password"] = str(data["smtp_password"]).strip()
        if "send_hour_cet" in data:
            updates["send_hour_cet"] = int(data["send_hour_cet"])
        updated = daily_reporter.update_email_config(updates)
        safe_cfg = dict(updated)
        safe_cfg["has_password"] = bool(safe_cfg.get("smtp_password"))
        safe_cfg["smtp_password"] = "••••••••" if safe_cfg.get("smtp_password") else ""
        self.send_json({"success": True, "config": safe_cfg})


def run():
    server_address = ('', PORT)
    httpd = ThreadingHTTPServer(server_address, EditorialHandler)
    print(f"[OK] Antigravity LinkedIn Hub running at http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == '__main__':
    run()
