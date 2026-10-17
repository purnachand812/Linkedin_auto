#!/usr/bin/env python3
"""
server.py - Lightweight API & Dashboard Server for Purna's LinkedIn Editorial System.
Built with Python's standard library (zero external dependencies).
Serves the web dashboard and provides live REST APIs to read/update candidate queue,
audit quality with detect.py logic, manage editorial history, and view visuals.
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
HISTORY_FILE = LINKEDIN_DIR / "editorial-history.json"
QUEUE_SUMMARY_FILE = QUEUE_DIR / "queue_summary.json"
SLOP_FILE = TOOLS_DIR / "slop.json"
JOBS_RADAR_FILE = JOBS_DIR / "jobs_radar.json"
APPLIED_HISTORY_FILE = JOBS_DIR / "applied_history.json"
PROFILE_MASTER_FILE = JOBS_DIR / "profile_master.json"
SCREENER_BANK_FILE = JOBS_DIR / "screener_bank.json"
REPORTS_DIR = JOBS_DIR / "reports"
EMAIL_CONFIG_FILE = JOBS_DIR / "email_config.json"

sys.path.insert(0, str(WORKSPACE_DIR))
try:
    from linkedin.tools import publisher
    from linkedin.tools import daemon
    from linkedin.tools import eu_growth_engine
except ImportError:
    publisher = None
    daemon = None
    eu_growth_engine = None

try:
    from linkedin.jobs import job_matcher
    from linkedin.jobs import resume_tailor
    from linkedin.jobs import job_dispatcher
    from linkedin.jobs import autonomous_job_agent
    from linkedin.jobs import daily_reporter
except ImportError:
    job_matcher = None
    resume_tailor = None
    job_dispatcher = None
    autonomous_job_agent = None
    daily_reporter = None

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
        r'\b(v\d+\.\d+|python|docker|gpu|vram|ram|api|mit|apache|llm|ollama|vllm|swe-bench|lmsys|github|claude|gemini|openai|anthropic)\b',
        r'\b[a-zA-Z0-9_-]+\.(py|json|md|txt|ts|js)\b',
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
    penalties = 0
    issues = []
    invisibles = ['\u200b', '\u200c', '\u200d', '\u2060', '\ufeff', '\u00ad']
    for char in invisibles:
        if char in text:
            penalties += 25
            issues.append("Zero-width/invisible unicode character detected")
    if '—' in text:
        count = text.count('—')
        penalties += 30 * count
        issues.append(f"{count} em-dash(es) ('—') detected (Strictly forbidden in Purna's voice)")
    curly = ['“', '”', '‘', '’']
    for c in curly:
        if c in text:
            penalties += 10 * text.count(c)
            issues.append("Curly quote detected (use straight quotes)")
    return round(max(0.0, 100.0 - penalties), 1), issues

def calc_voice_and_tells(text):
    score = 100.0
    issues = []
    forbidden_endings = SLOP_CONFIG.get("forbidden_endings", ["thoughts?", "agree?", "what do you think?"])
    lower_text = text.strip().lower()
    for ending in forbidden_endings:
        if lower_text.endswith(ending):
            score -= 35.0
            issues.append(f"Generic engagement bait ending: '{ending}'")
    agent_keywords = ["agent", "terminal", "code execution", "browser automation", "execute commands", "repo", "scripts"]
    if any(k in lower_text for k in agent_keywords):
        security_terms = ["sandbox", "credentials", "security", "production", "inspect"]
        if not any(s in lower_text for s in security_terms):
            score -= 25.0
            issues.append("Agent/execution tool mentioned without required sandboxing warning ('Sandbox it first').")
    tool_keywords = ["repo", "tool", "model", "release", "framework", "python"]
    if any(k in lower_text for k in tool_keywords):
        test_terms = ["tested", "haven't run", "based on", "documentation", "inspection"]
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
    # Replace em-dashes
    out = out.replace("—", ", ")
    out = out.replace("–", "-")
    # Replace curly quotes
    out = out.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    # Strip invisible characters
    for inv in ['\u200b', '\u200c', '\u200d', '\u2060', '\ufeff', '\u00ad']:
        out = out.replace(inv, '')
    # Replace common slop
    replacements = SLOP_CONFIG.get("dry_replacements", {})
    for word, repl in replacements.items():
        out = re.sub(r'\b' + re.escape(word) + r'\b', repl, out, flags=re.IGNORECASE)
    return out

def parse_candidate_markdown(file_path):
    if not file_path.exists():
        return {}
    content = file_path.read_text(encoding="utf-8")
    
    # Extract fields with regex
    status_match = re.search(r'-\s*Status:\s*([A-Z_]+)', content)
    beat_match = re.search(r'-\s*Beat:\s*(.+)', content)
    score_match = re.search(r'-\s*Editorial Score:\s*(\d+)/100', content)
    
    # Extract Why Now
    why_now = ""
    wn_m = re.search(r'###\s*WHY NOW\s*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    if wn_m:
        why_now = wn_m.group(1).strip()
        
    # Extract Interesting Angle
    angle = ""
    ang_m = re.search(r'###\s*INTERESTING ANGLE\s*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    if ang_m:
        angle = ang_m.group(1).strip()
        
    # Extract Hooks
    hooks = []
    hooks_m = re.search(r'###\s*HOOK OPTIONS\s*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    if hooks_m:
        raw_hooks = hooks_m.group(1).strip()
        # Parse numbered hooks
        parts = re.split(r'\n(?=\d+\.\s*\[)', raw_hooks)
        for p in parts:
            p = p.strip()
            if p:
                hooks.append(p)
                
    # Extract Complete Post
    post_text = ""
    post_m = re.search(r'###\s*COMPLETE LINKEDIN POST[^\n]*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    if post_m:
        post_text = post_m.group(1).strip()
        
    # Extract The Catch
    catch = ""
    catch_m = re.search(r'###\s*THE CATCH\s*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    if catch_m:
        catch = catch_m.group(1).strip()

    # Extract What it Replaces
    replaces = ""
    rep_m = re.search(r'###\s*WHAT IT REPLACES\s*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    if rep_m:
        replaces = rep_m.group(1).strip()

    # Extract Cost Breakdown
    cost = ""
    cost_m = re.search(r'###\s*COST BREAKDOWN\s*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    if cost_m:
        cost = cost_m.group(1).strip()

    # Extract Sources / First Comment
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

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Static Visuals routing
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
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
                return
            else:
                self.send_error(404, "Visual asset not found")
                return

        # Static Tailored Resumes routing
        if path.startswith("/resumes/"):
            filename = path.replace("/resumes/", "")
            file_path = RESUMES_DIR / filename
            if file_path.exists():
                self.send_response(200)
                if filename.endswith(".html"):
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                elif filename.endswith(".pdf"):
                    self.send_header("Content-Type", "application/pdf")
                elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
                    self.send_header("Content-Type", "image/jpeg")
                elif filename.endswith(".png"):
                    self.send_header("Content-Type", "image/png")
                else:
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
                return
            else:
                self.send_error(404, "Resume file not found")
                return

        # Static Reports routing
        if path.startswith("/reports/"):
            filename = path.replace("/reports/", "")
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
        elif path == "/api/replies":
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
        elif path == "/api/daemon/cycle":
            self.handle_post_daemon_cycle(data)
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
        elif path == "/api/jobs/reports/send-now":
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

        candidates = queue_summary.get("candidates", [])
        enriched = []
        for c in candidates:
            c_file = WORKSPACE_DIR / c.get("file", "")
            parsed_data = parse_candidate_markdown(c_file)
            item = dict(c)
            item.update(parsed_data)
            
            # Check visual existence
            v_path = c.get("visual", "")
            if v_path:
                v_file = WORKSPACE_DIR / v_path
                item["visual_exists"] = v_file.exists()
                item["visual_url"] = f"/visuals/{v_file.name}" if v_file.exists() else None
            else:
                item["visual_exists"] = False
                item["visual_url"] = None

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

        # Update candidate markdown file if found
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
            # Replace post content
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
        # Read from history + current scouted trends
        trends = [
            {
                "id": 1,
                "title": "Langfuse: Self-Hosted Agent Tracing vs Closed SaaS",
                "beat": "Free & Open-Source AI Agent / LLM Observability",
                "score": 95,
                "hook": "Most teams only discover their autonomous agent entered an infinite retry loop after receiving a $400 API invoice at 3 AM.",
                "why_now": "Teams deploying multi-step autonomous agents are hitting runaway retry loops and debugging blindness. LangSmith charges $39/seat/mo and locks self-hosting behind enterprise tiers.",
                "replaces": "LangSmith ($39/seat/month), Arize, Helicone",
                "repo": "https://github.com/langfuse/langfuse",
                "license": "MIT Open Source",
                "stars": "35.8k stars",
                "evidence": ["https://github.com/langfuse/langfuse", "https://langfuse.com/docs"]
            },
            {
                "id": 2,
                "title": "FastMCP: 3-Line Typed Model Context Protocol Servers",
                "beat": "Free & Open-Source AI Agent / Developer Tools",
                "score": 94,
                "hook": "Writing raw JSON-RPC boilerplate just so an AI model can query your PostgreSQL database is a waste of engineering time.",
                "why_now": "Anthropic's Model Context Protocol is now standard across Claude Desktop and Cursor, but hand-crafting JSON schemas is tedious.",
                "replaces": "Custom tool wrappers and integration middleware",
                "repo": "https://github.com/PrefectHQ/fastmcp",
                "license": "Apache 2.0",
                "stars": "Trending on GitHub",
                "evidence": ["https://github.com/PrefectHQ/fastmcp"]
            },
            {
                "id": 3,
                "title": "DeepSeek MLA: Escaping the KV Cache Memory Wall",
                "beat": "AI Models & Inference Architecture",
                "score": 93,
                "hook": "The biggest misconception in local LLM hosting is that parameter count is what kills your GPU memory.",
                "why_now": "Multi-turn agent loops with 64k+ context windows hit memory bandwidth bottlenecks. MLA compresses KV cache by 5x-10x without losing expressivity.",
                "replaces": "Sluggish uncompressed inference pipelines and lossy GQA trade-offs",
                "repo": "https://github.com/deepseek-ai/DeepSeek-V3",
                "license": "Open Weights",
                "stars": "Top paper breakthrough",
                "evidence": ["https://arxiv.org/abs/2412.19437"]
            },
            {
                "id": 4,
                "title": "vLLM V1 Rewrite: Decoupled ZeroMQ & Native Prefix Caching",
                "beat": "AI Hardware & Local Inference",
                "score": 92,
                "hook": "If your self-hosted LLM server is lagging during multi-turn agent chats, don't blame your GPUs before checking if Python's thread lock is throttling your request queue.",
                "why_now": "vLLM V1 decoupled the HTTP frontend from the engine scheduler using ZeroMQ sockets, eliminating Python GIL bottlenecks.",
                "replaces": "Proprietary high-cost inference APIs and legacy V0 server lag",
                "repo": "https://github.com/vllm-project/vllm",
                "license": "Apache 2.0",
                "stars": "Core production engine",
                "evidence": ["https://github.com/vllm-project/vllm", "https://docs.vllm.ai"]
            },
            {
                "id": 5,
                "title": "Microsoft AutoGen v0.4: Asynchronous Event-Driven Actors",
                "beat": "Autonomous AI Agent Architecture",
                "score": 91,
                "hook": "Synchronous while-loops worked for toy agent demos, but you cannot run a production system where one stuck tool call freezes your entire agent team.",
                "why_now": "Microsoft rewrote AutoGen into distributed async event actors with native OpenTelemetry tracing and circuit breakers.",
                "replaces": "Fragile synchronous while-loop agent scripts",
                "repo": "https://github.com/microsoft/autogen",
                "license": "MIT Open Source",
                "stars": "38k+ stars",
                "evidence": ["https://github.com/microsoft/autogen"]
            }
        ]
        self.send_json(trends)

    def handle_get_visuals(self):
        items = []
        if VISUALS_DIR.exists():
            for f in sorted(VISUALS_DIR.iterdir()):
                if f.suffix.lower() in [".svg", ".jpg", ".jpeg", ".png"]:
                    items.append({
                        "name": f.name,
                        "type": f.suffix.replace(".", "").upper(),
                        "url": f"/visuals/{f.name}",
                        "size_bytes": f.stat().st_size
                    })
        self.send_json(items)

    def handle_get_calendar(self):
        calendar = [
            {"day": "Monday", "pillar": "Architecture & Thesis", "topic": "Pydantic AI (Typed Dependency Injection)", "candidate_id": 8, "status": "APPROVED", "format": "Text-Only"},
            {"day": "Tuesday", "pillar": "Open-Source Coding Agent", "topic": "Cline (VS Code MCP Extension)", "candidate_id": 1, "status": "APPROVED", "format": "Visual + Text"},
            {"day": "Wednesday", "pillar": "Local AI & Personal Agents", "topic": "OpenClaw (Self-Hosted Personal Agent)", "candidate_id": 2, "status": "APPROVED", "format": "Visual + Text"},
            {"day": "Thursday", "pillar": "Practical Data Automation", "topic": "Crawl4AI (Self-Hosted Scraper vs Firecrawl)", "candidate_id": 9, "status": "APPROVED", "format": "Text-Only"},
            {"day": "Friday", "pillar": "AI Inference & Hardware", "topic": "vLLM V1 Rewrite / DeepSeek MLA", "candidate_id": None, "status": "SCOUTED", "format": "Diagram + Text"},
            {"day": "Saturday", "pillar": "Computer-Use & Automation", "topic": "Agent S3 (Desktop GUI Agent)", "candidate_id": 3, "status": "APPROVED", "format": "Visual + Text"},
            {"day": "Sunday", "pillar": "Agent Observability & Tracing", "topic": "Langfuse (Self-Hosted Tracing vs LangSmith)", "candidate_id": None, "status": "SCOUTED", "format": "Architecture + Text"}
        ]
        self.send_json(calendar)

    def handle_get_status(self):
        queue_summary = {}
        if QUEUE_SUMMARY_FILE.exists():
            with open(QUEUE_SUMMARY_FILE, "r", encoding="utf-8") as f:
                queue_summary = json.load(f)
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

        # 1. Check connection status
        conn_status = publisher.get_connection_status()
        if not conn_status.get("connected"):
            self.send_json({
                "success": False,
                "status": "Post approved, but LinkedIn account is not authorized.",
                "action_needed": "connect_linkedin",
                "instructions": "Please enter your Client ID & Secret and authorize your app via the dashboard."
            }, 400)
            return

        # 2. Check candidate and enforce APPROVAL state
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

        # Enforce Approval Gate
        # Auto-promote to APPROVED if user explicitly triggered publishing
        current_status = candidate_entry.get("status")
        if current_status not in ("APPROVED", "PUBLISHED"):
            candidate_entry["status"] = "APPROVED"

        post_text = parsed_data.get("post_text", "").strip()
        if not post_text:
            self.send_json({"error": "Post text is empty."}, 400)
            return

        # 3. Check for visual image asset & format preference
        with_image = data.get("with_image", True)
        image_path = None

        if with_image:
            v_rel = candidate_entry.get("visual", "")
            if v_rel:
                v_file = WORKSPACE_DIR / v_rel
                if v_file.exists():
                    if v_file.suffix.lower() in (".png", ".jpg", ".jpeg"):
                        image_path = str(v_file)
                    elif v_file.suffix.lower() == ".svg":
                        png_cand = v_file.with_suffix(".png")
                        if png_cand.exists():
                            image_path = str(png_cand)

        # Rule: When posting WITHOUT an image, include GitHub link in the post text at the end itself (no separate comment)
        if not image_path:
            # Check if post_text ends with a github link
            tail = post_text[-250:].lower()
            if "github.com" not in tail:
                # Extract repo URL from sources or raw markdown
                sources_str = parsed_data.get("sources", "") + " " + parsed_data.get("raw_markdown", "")
                m = re.search(r'https?://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+', sources_str)
                if m:
                    post_text = post_text.rstrip() + f"\n\nRepo: {m.group(0)}"
            else:
                # Ensure the link has https:// protocol
                post_text = re.sub(r'Repo:\s*github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)', r'Repo: https://github.com/\1', post_text)

        # 4. Publish via official API
        try:
            result = publisher.publish_candidate_post(post_text, image_path=image_path)
            # Record publication in queue_summary, history, and published archive
            publisher.record_published_post(
                c_id,
                {
                    "topic": candidate_entry.get("topic", ""),
                    "post_text": post_text,
                    "sources": parsed_data.get("sources", "") if image_path else "GitHub link included in post text. No first comment needed.",
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
        if replies_file.exists():
            try:
                with open(replies_file, "r", encoding="utf-8") as f:
                    self.send_json(json.load(f))
                    return
            except Exception:
                pass
        self.send_json({"pending": []})

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
            from linkedin.jobs import linkedin_scraper, resume_tailor, cover_letter_generator
            success = linkedin_scraper.refresh_jobs_radar()
            if JOBS_RADAR_FILE.exists():
                with open(JOBS_RADAR_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for job in data.get("jobs", []):
                    try:
                        resume_tailor.generate_tailored_resume(job)
                        cover_letter_generator.generate_tailored_cover_letter(job)
                    except Exception:
                        pass
                self.send_json({"success": True, "count": len(data.get("jobs", [])), "radar": data})
                return
            self.send_json({"success": success, "count": 0})
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
        # redact password in GET
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
