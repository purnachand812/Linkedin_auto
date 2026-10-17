#!/usr/bin/env python3
"""
daemon.py - 24/7 Autonomous Background Service for Purnachandra Madhukar's LinkedIn Agent.
Runs continuously on local machine or cloud runner.
Handles:
1. EU Prime-Time Scheduled Publishing (CET/CEST)
2. Continuous Analytics & Social Lifecycle Monitoring
3. Algorithmic Feedback & EU Growth Optimization
4. Contextual Comment & Community Reply Generation
5. Heartbeat & Live Health Telemetry for Dashboard
"""

import os
import sys
import json
import time
import signal
from datetime import datetime, timedelta
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LINKEDIN_DIR = BASE_DIR / "linkedin"
QUEUE_DIR = LINKEDIN_DIR / "queue"
HISTORY_DIR = LINKEDIN_DIR / "history"
PUBLISHED_DIR = LINKEDIN_DIR / "published"
STATUS_FILE = HISTORY_DIR / "daemon_status.json"
QUEUE_SUMMARY_FILE = QUEUE_DIR / "queue_summary.json"
PUBLISHING_LOG_FILE = HISTORY_DIR / "publishing_log.json"
ANALYTICS_FILE = HISTORY_DIR / "analytics_matrix.json"
REPLIES_FILE = HISTORY_DIR / "pending_replies.json"

sys.path.insert(0, str(BASE_DIR))
from linkedin.tools import publisher
from linkedin.tools import eu_growth_engine
try:
    from linkedin.jobs import autonomous_job_agent
except ImportError:
    autonomous_job_agent = None

# Configuration
CHECK_INTERVAL_SECONDS = 60 # Check cycle every minute
HEARTBEAT_INTERVAL_SECONDS = 30 # Telemetry ping
MAX_POSTS_PER_DAY = 2 # LinkedIn algorithmic limit for optimal organic distribution

RUNNING = True

def signal_handler(sig, frame):
    global RUNNING
    print(f"\n[DAEMON] Shutdown signal ({sig}) received. Gracefully stopping daemon...")
    RUNNING = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def load_json_file(file_path, default=None):
    if default is None:
        default = {}
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def save_json_file(file_path, data):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def update_daemon_status(state_data):
    """Writes live telemetry to daemon_status.json for dashboard visibility."""
    current = load_json_file(STATUS_FILE, {
        "status": "STOPPED",
        "started_at": datetime.now().isoformat(),
        "log": []
    })
    current.update(state_data)
    current["last_heartbeat"] = datetime.now().isoformat()
    save_json_file(STATUS_FILE, current)

def append_daemon_log(message):
    """Appends timestamped entry to rolling activity log."""
    current = load_json_file(STATUS_FILE, {"log": []})
    log_list = current.get("log", [])
    entry = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
    log_list.append(entry)
    # Keep last 30 log lines
    current["log"] = log_list[-30:]
    current["last_activity"] = entry
    save_json_file(STATUS_FILE, current)
    try:
        print(f"[DAEMON] {message}")
    except Exception:
        pass

def count_posts_published_today():
    """Counts how many posts were published today (CET)."""
    pub_log = load_json_file(PUBLISHING_LOG_FILE, [])
    today_str = datetime.now().strftime("%Y-%m-%d")
    count = 0
    for p in pub_log:
        pub_at = p.get("published_at", "")
        if pub_at.startswith(today_str):
            count += 1
    return count

def check_and_publish_next_candidate(force=False):
    """
    Checks if a post is ready for publication during an EU prime-time slot.
    Returns: bool (True if published)
    """
    queue_summary = load_json_file(QUEUE_SUMMARY_FILE, {"candidates": []})
    candidates = queue_summary.get("candidates", [])

    # Find first candidate with APPROVED status
    approved = [c for c in candidates if c.get("status") == "APPROVED"]
    if not approved:
        return False

    target_candidate = approved[0]
    c_id = target_candidate["id"]
    topic = target_candidate["topic"]

    # Check EU Prime Time Window unless forced
    is_prime, win_info = eu_growth_engine.is_eu_prime_time()
    if not force:
        if not is_prime:
            return False

        # Enforce rate limit (maximum 2 posts per day)
        today_count = count_posts_published_today()
        if today_count >= MAX_POSTS_PER_DAY:
            return False

    append_daemon_log(f"🚀 Triggering automated publishing for Candidate #{c_id}: '{topic}' (EU Window: {win_info['name'] if win_info else 'Manual Override'})")

    # Read post markdown file
    c_file = BASE_DIR / target_candidate.get("file", "")
    if not c_file.exists():
        append_daemon_log(f"❌ Markdown file not found for Candidate #{c_id}: {c_file}")
        return False

    content = c_file.read_text(encoding="utf-8")

    # Extract post copy
    import re
    post_m = re.search(r'###\s*COMPLETE LINKEDIN POST[^\n]*\n(.*?)(?=\n###|\n---|\Z)', content, re.DOTALL)
    post_text = post_m.group(1).strip() if post_m else ""
    if not post_text:
        append_daemon_log(f"❌ Post text is empty for Candidate #{c_id}")
        return False

    # Check visual
    v_rel = target_candidate.get("visual", "")
    image_path = None
    if v_rel:
        v_file = BASE_DIR / v_rel
        if v_file.exists() and v_file.suffix.lower() in (".png", ".jpg", ".jpeg"):
            image_path = str(v_file)

    # Ensure GitHub link at the end for text-only posts
    if not image_path:
        if "github.com" not in post_text[-250:].lower():
            m = re.search(r'https?://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+', content)
            if m:
                post_text = post_text.rstrip() + f"\n\nRepo: {m.group(0)}"

    try:
        result = publisher.publish_candidate_post(post_text, image_path=image_path)
        publisher.record_published_post(
            c_id,
            {
                "topic": topic,
                "post_text": post_text,
                "sources": "GitHub link included in post." if not image_path else "See visual asset for architecture.",
                "has_image": bool(image_path),
                "comment_needed": bool(image_path)
            },
            result
        )
        post_url = result.get("post_url", "")
        append_daemon_log(f"🎉 Successfully published Candidate #{c_id}! Live URL: {post_url}")
        
        # Generate initial community reply templates
        generate_community_reply_templates(c_id, topic, post_text)

        # Trigger EU learning feedback loop
        eu_growth_engine.record_feedback(c_id, topic, {"format": "image" if image_path else "text"})
        return True
    except Exception as e:
        append_daemon_log(f"❌ Publishing failed for Candidate #{c_id}: {e}")
        return False

def generate_community_reply_templates(candidate_id, topic, post_text):
    """
    Automatically prepares engineering-grade comment replies for expected reader questions.
    Ensures Purna can respond within the vital first 60 minutes with technical authority.
    """
    replies = load_json_file(REPLIES_FILE, {"pending": []})
    
    reply_templates = [
        {
            "candidate_id": candidate_id,
            "topic": topic,
            "scenario": "Technical inquiry about production reliability / benchmarks",
            "suggested_reply": f"Good callout. In practice, the primary constraint isn't the framework wrapper, but token latency and context drift over multi-step runs. For production, sandboxing tool execution and enforcing strict schema validation upfront prevents 80% of edge case failures.",
            "created_at": datetime.now().isoformat()
        },
        {
            "candidate_id": candidate_id,
            "topic": topic,
            "scenario": "Comparison with closed commercial alternatives",
            "suggested_reply": f"The biggest delta is privacy and infrastructure lock-in. Self-hosting this on European bare-metal (like Hetzner or local Ollama) costs $0 in SaaS license overhead and guarantees your internal code doesn't leave your network perimeter.",
            "created_at": datetime.now().isoformat()
        }
    ]

    replies["pending"] = reply_templates + replies.get("pending", [])[:10]
    save_json_file(REPLIES_FILE, replies)
    append_daemon_log(f"💬 Generated 2 contextual community reply templates for Candidate #{candidate_id}")

def update_analytics_monitoring():
    """
    Monitors published post metrics and stores longitudinal growth data.
    """
    pub_log = load_json_file(PUBLISHING_LOG_FILE, [])
    current_matrix = load_json_file(ANALYTICS_FILE, {
        "updated_at": datetime.now().isoformat(),
        "total_posts": len(pub_log),
        "target_region": "European Union (CET/CEST)",
        "estimated_reach_by_hub": {
            "Berlin / Munich AI Ecosystem": "45%",
            "Amsterdam / Paris Sovereign AI": "30%",
            "Zurich / London Deep Tech": "25%"
        },
        "posts_analytics": []
    })

    current_matrix["total_posts"] = len(pub_log)
    current_matrix["updated_at"] = datetime.now().isoformat()

    # Track metrics for each published post
    analytics_items = []
    for p in pub_log:
        c_id = p.get("candidate_id")
        topic = p.get("topic")
        pub_at = p.get("published_at")
        post_url = p.get("post_url")
        
        # Calculate post age in hours
        age_hours = 0.0
        try:
            pub_dt = datetime.fromisoformat(pub_at.replace("Z", "+00:00"))
            age_hours = round((datetime.now(pub_dt.tzinfo) - pub_dt).total_seconds() / 3600.0, 1)
        except Exception:
            pass

        analytics_items.append({
            "candidate_id": c_id,
            "topic": topic,
            "published_at": pub_at,
            "post_url": post_url,
            "age_hours": age_hours,
            "has_image": p.get("has_image", False),
            "status": "LIVE",
            "growth_tier": "ESTABLISHED" if age_hours > 24 else "ACTIVE_ACCUMULATION"
        })

    current_matrix["posts_analytics"] = analytics_items
    save_json_file(ANALYTICS_FILE, current_matrix)

def run_single_cycle(force_publish=False):
    """Executes a single end-to-end check cycle."""
    now_dt = eu_growth_engine.get_berlin_now()
    is_prime, win_info = eu_growth_engine.is_eu_prime_time(now_dt)
    next_slot = eu_growth_engine.get_next_eu_prime_window(now_dt)

    queue_summary = load_json_file(QUEUE_SUMMARY_FILE, {"candidates": []})
    approved_count = sum(1 for c in queue_summary.get("candidates", []) if c.get("status") == "APPROVED")
    published_today = count_posts_published_today()

    # 1. Update analytics & telemetry
    update_analytics_monitoring()

    # 2. Check for publishing action
    published = False
    if approved_count > 0:
        published = check_and_publish_next_candidate(force=force_publish)

    # 3. Autonomous Job Application Engine check
    auto_apply_telemetry = {"enabled": False, "applied_today": 0}
    if autonomous_job_agent:
        try:
            auto_apply_res = autonomous_job_agent.run_autonomous_cycle()
            cfg = autonomous_job_agent.get_config()
            auto_apply_telemetry = {
                "enabled": cfg.get("enabled", True),
                "applied_today": cfg.get("applied_today", 0),
                "daily_limit": cfg.get("daily_limit", 5),
                "status": cfg.get("status", "RUNNING")
            }
        except Exception as e:
            append_daemon_log(f"⚠️ Auto-apply cycle exception: {e}")

    # 4. Update heartbeat
    update_daemon_status({
        "status": "RUNNING",
        "current_time_cet": now_dt.strftime("%Y-%m-%d %H:%M:%S CET"),
        "is_eu_prime_time": is_prime,
        "current_window": win_info["name"] if win_info else "Off-Peak / Monitoring",
        "next_scheduled_drop": next_slot["formatted"],
        "approved_queue_count": approved_count,
        "published_today": published_today,
        "auto_apply_telemetry": auto_apply_telemetry,
        "target_audience": "European Union (Berlin, Munich, Amsterdam, Paris, Zurich)",
        "auto_publish_enabled": True
    })

    return published

def start_daemon_loop():
    """Starts the continuous 24/7 background service."""
    print("=" * 65)
    print("  Antigravity 24/7 LinkedIn Autonomous Editorial & Growth Daemon")
    print(f"  Owner: Purnachandra Madhukar | Base: Berlin, Germany (CET)")
    print(f"  Target: European Union Reach & Sovereign AI Optimization")
    print("=" * 65)
    
    append_daemon_log("Daemon initialized. 24/7 autonomous monitoring & scheduling active.")

    last_heartbeat = 0
    last_analytics_check = 0

    while RUNNING:
        current_time = time.time()
        
        try:
            # Run scheduled cycle
            run_single_cycle()
        except Exception as e:
            append_daemon_log(f"⚠️ Error during cycle: {e}")

        # Sleep in short increments to allow quick shutdown response
        for _ in range(CHECK_INTERVAL_SECONDS):
            if not RUNNING:
                break
            time.sleep(1)

    append_daemon_log("Daemon process stopped gracefully.")
    update_daemon_status({"status": "STOPPED"})

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="24/7 LinkedIn Autonomous Editorial Daemon")
    parser.add_argument("--once", action="store_true", help="Run a single maintenance cycle and exit")
    parser.add_argument("--force-publish", action="store_true", help="Force publish next approved candidate immediately")
    parser.add_argument("--status", action="store_true", help="Print current status and exit")

    args = parser.parse_args()

    if args.status:
        status = load_json_file(STATUS_FILE)
        print(json.dumps(status, indent=2))
    elif args.once or args.force_publish:
        run_single_cycle(force_publish=args.force_publish)
    else:
        start_daemon_loop()
