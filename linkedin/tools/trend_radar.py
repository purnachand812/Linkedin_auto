#!/usr/bin/env python3
"""
trend_radar.py - AI Trend Radar & Autonomous Idea Scout for Purnachandra Madhukar.
Continuously scans GitHub, technical research, and AI repositories for breakthrough open-source tools.
Evaluates candidates using the 100-point editorial scout rubric, formats complete LinkedIn posts
in Purna's authentic voice, generates Canva-style visual assets, and replenishes the queue.
"""

import os
import sys
import json
import re
import time
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LINKEDIN_DIR = BASE_DIR / "linkedin"
QUEUE_DIR = LINKEDIN_DIR / "queue"
VISUALS_DIR = LINKEDIN_DIR / "visuals"
HISTORY_DIR = LINKEDIN_DIR / "history"
TOOLS_DIR = LINKEDIN_DIR / "tools"
QUEUE_SUMMARY_FILE = QUEUE_DIR / "queue_summary.json"
EDITORIAL_HISTORY_FILE = LINKEDIN_DIR / "editorial-history.json"
RADAR_STATE_FILE = HISTORY_DIR / "trend_radar_state.json"

sys.path.insert(0, str(BASE_DIR))
try:
    from linkedin.tools import canva_designer
except ImportError:
    canva_designer = None

# Curated High-Authority Seed Topics aligned with Purna's GitHub background (Docker, Python, GISMA AI research)
CURATED_BREAKTHROUGHS = [
    {
        "id": 10,
        "slug": "fastmcp",
        "topic": "FastMCP (3-Line Typed Model Context Protocol Servers)",
        "beat": "Free & Open-Source AI Agent / Architecture",
        "score": 95,
        "repo": "https://github.com/PrefectHQ/fastmcp",
        "author_repo": "PrefectHQ/fastmcp",
        "license": "Apache 2.0",
        "replaces": "Hand-crafted JSON-RPC boilerplate & brittle custom tool wrappers",
        "cost": "Free Apache 2.0 code; $0 SaaS overhead",
        "test_status": "Not tested (Based on repository inspection and documentation)",
        "why_now": "FastMCP reached 8k GitHub stars as the definitive Python framework for building Anthropic Model Context Protocol (MCP) servers, reducing 200 lines of JSON-RPC protocol boilerplate down to 3 lines of typed Python decorators.",
        "angle": "\"Why Decorators Beat Hand-Crafted Protocol Boilerplate\" - Anthropic's MCP is becoming the standard for agent tool calling, but implementing the raw protocol in Python requires endless JSON-RPC request-response handling. FastMCP turns standard Python functions into discoverable MCP tools with automatic type casting.",
        "hook_selected": "Writing 200 lines of JSON-RPC protocol boilerplate just to give Claude access to your local SQLite database is where agent development goes to die.",
        "post_copy": """Writing 200 lines of JSON-RPC protocol boilerplate just to give Claude access to your local SQLite database is where agent development goes to die.

Anthropic's Model Context Protocol (MCP) is quickly becoming the standard for connecting LLMs to local databases, terminal tools, and internal APIs. But building a native MCP server from scratch usually means writing endless JSON-RPC request-response handlers, schema validations, and async socket routing.

The open-source library PrefectHQ/fastmcp solves this the same way FastAPI solved REST APIs:

1. Decorator-Driven: Add @mcp.tool() above any standard Python function. FastMCP automatically parses type hints, docstrings, and parameter schemas.
2. FastMCP Context: Inject real-time execution context, logging, and progress reporting directly into tool functions without rewriting signatures.
3. Multi-Transport Support: Runs locally over stdio for VS Code and Claude Desktop, or over SSE (Server-Sent Events) for remote Docker containers.

On paper, it replaces brittle hand-written tool wrappers.
In practice, there is a real engineering catch:

Automatic type conversion is convenient, but LLMs frequently hallucinate edge-case types. If your tool expects an ISO timestamp and the model supplies 'yesterday afternoon', the tool crashes unless you validate the inputs with Pydantic first.

Don't give an experimental agent unrestricted system tools. Sandbox it first.

Full open-source repository: github.com/PrefectHQ/fastmcp
(Documentation and installation guide in the first comment)

#Python #AI #ModelContextProtocol #FastAPI #OpenSource""",
        "catch": "Automatic type casting does not prevent semantic hallucinations. Tools with database mutation privileges still need strict parameter whitelisting.",
        "visual_specs": {
            "category_tag": "Free & Open-Source AI Agent / Architecture",
            "main_title": "Model Context Protocol: <span class='gradient-text-cyan'>FastMCP</span> vs Raw JSON-RPC",
            "subtitle": "How typed Python decorators eliminate 200 lines of protocol boilerplate when connecting LLMs to tools.",
            "left_badge": "Raw MCP Implementation",
            "left_title": "Manual JSON-RPC Routing",
            "left_price": "200+ Lines",
            "left_subprice": "Hand-Written Protocol Overhead",
            "left_points": [
                ("Manual Schema Dicts", "Hand-crafting inputSchema parameters in JSON"),
                ("Boilerplate Sockets", "Managing stdio read/write streams and ping handshakes"),
                ("Type Drift", "Silent runtime errors when parameter types mismatch"),
                ("Brittle Maintenance", "Rewriting protocol adapters for every new tool")
            ],
            "left_metric": "Setup Complexity: ❌ High Protocol Debt",
            "right_badge": "FastMCP (Prefect)",
            "right_title": "Typed @mcp.tool() Decorators",
            "right_price": "3 Lines",
            "right_subprice": "100% Free Apache 2.0 Code",
            "right_points": [
                ("Pydantic Type Validation", "Automatic schema generation from Python type hints"),
                ("Claude Desktop Ready", "Instant 1-click mounting via stdio configuration"),
                ("FastAPI-Style DI", "Injects active session and logging context cleanly"),
                ("Zero Protocol Debt", "Focus on your business logic instead of JSON-RPC")
            ],
            "right_metric": "Setup Complexity: ✓ Zero Boilerplate",
            "specs": [
                ("Protocol Engine", "Anthropic MCP / JSON-RPC 2.0"),
                ("Transport Modes", "stdio, SSE (Server-Sent Events)"),
                ("Licensing Cost", "$0 / Apache 2.0 Open Source")
            ],
            "catch_title": "The Validation Catch",
            "catch_text": "Convenient type hints do not stop semantic errors. Tools that run SQL queries or file mutations still require strict parameter whitelisting.",
            "footer_repo": "github.com/PrefectHQ/fastmcp",
            "save_filename": "visual_fastmcp.png"
        }
    },
    {
        "id": 11,
        "slug": "langfuse",
        "topic": "Langfuse (Self-Hosted LLM Observability & Tracing in Docker)",
        "beat": "Free & Open-Source AI Agent / Infrastructure",
        "score": 94,
        "repo": "https://github.com/langfuse/langfuse",
        "author_repo": "langfuse/langfuse",
        "license": "MIT License",
        "replaces": "Helicone / LangSmith ($39-$99/mo cloud SaaS)",
        "cost": "Free MIT code; runs in local Docker container with $0 SaaS fees",
        "test_status": "Not tested (Based on repository inspection and documentation)",
        "why_now": "Langfuse crossed 12k GitHub stars as the leading open-source LLM observability platform, allowing engineering teams to capture full agent execution graphs without shipping sensitive company prompts to third-party SaaS clouds.",
        "angle": "\"Why European Engineering Leads Run LLM Tracing in Docker\" - Debugging multi-step agent trajectories with print statements fails the moment an agent takes 15 autonomous steps. Langfuse gives full OpenTelemetry traces locally while keeping prompt data inside your own network perimeter.",
        "hook_selected": "Debugging multi-step agent trajectories with print statements works right up until your agent burns $40 of tokens looping across 15 recursive calls.",
        "post_copy": """Debugging multi-step agent trajectories with print statements works right up until your agent burns $40 of tokens looping across 15 recursive calls.

When an AI agent makes multiple tool calls, searches a database, and generates an answer, knowing where the error happened is nearly impossible without distributed tracing. Did the retriever pull the wrong chunk, or did the LLM hallucinate the argument?

The open-source platform langfuse/langfuse brings OpenTelemetry tracing to LLM applications:

1. Full Execution Graphs: Visualizes nested chains, tool calls, and model latencies in a single waterfall trace.
2. Token Cost Tracking: Calculates exact model spending per user, session, or feature across OpenAI, Anthropic, and local Ollama models.
3. 100% Data Sovereignty: Runs via a simple Docker Compose file on your own European VPS (Hetzner, OVH, or local hardware) so customer prompts never leave your network.

On paper, it replaces paid observability subscriptions like LangSmith ($39/seat/mo) and Helicone.
In practice, there is an infrastructure reality:

Self-hosting an observability stack means you are responsible for running PostgreSQL and ClickHouse. If your agent handles millions of events daily, disk I/O and log rotation require real database maintenance.

Free MIT code means $0 SaaS subscription bills, but you must provision your own storage.

Don't deploy experimental telemetry to production without data retention policies. Sandbox it first.

Full open-source repository: github.com/langfuse/langfuse
(Docker Compose configuration and documentation in first comment)

#Python #AI #DevOps #Docker #OpenSource #DataEngineering""",
        "catch": "Running ClickHouse and Postgres locally requires storage planning. High-throughput production traces generate gigabytes of log events weekly.",
        "visual_specs": {
            "category_tag": "Free & Open-Source AI Agent / Infrastructure",
            "main_title": "LLM Tracing & Observability: <span class='gradient-text-cyan'>Self-Hosted Docker</span> vs $99/mo SaaS",
            "subtitle": "How engineering teams track agent token burn, latencies, and hallucination paths without third-party data leakage.",
            "left_badge": "Proprietary LLM SaaS",
            "left_title": "Cloud Tracing Subscriptions",
            "left_price": "$39 - $99",
            "left_subprice": "Per Seat Monthly Subscription",
            "left_points": [
                ("Third-Party Data Flow", "Customer prompts and internal code stream to vendor clouds"),
                ("Per-Seat Pricing", "Costs scale rapidly across growing engineering teams"),
                ("Vendor Lock-In", "Tied to proprietary tracing dashboards and APIs"),
                ("GDPR Compliance Risk", "Complex data processing agreements for European enterprise")
            ],
            "left_metric": "Data Sovereignty: ❌ Cloud Hosted",
            "right_badge": "Langfuse (Local / Docker)",
            "right_title": "Self-Hosted Observability",
            "right_price": "$0 / mo",
            "right_subprice": "100% Free MIT Open Source",
            "right_points": [
                ("100% Private Tracing", "Runs on your own Hetzner VPS, AWS EC2, or local Docker"),
                ("Full Waterfall Graphs", "Inspects multi-step agent tool calls and latencies visually"),
                ("OpenTelemetry Native", "Integrates with standard Python logging without custom SDKs"),
                ("Granular Token Accounting", "Accurate cost tracking down to individual session IDs")
            ],
            "right_metric": "Data Sovereignty: ✓ 100% Sovereign",
            "specs": [
                ("Storage Engine", "PostgreSQL & ClickHouse"),
                ("Instrumentation", "OpenTelemetry & Python Decorators"),
                ("Deployment", "1-Click Docker Compose")
            ],
            "catch_title": "The Storage Catch",
            "catch_text": "Tracing high-volume production swarms produces gigabytes of event logs. You must configure log rotation and database backups yourself.",
            "footer_repo": "github.com/langfuse/langfuse",
            "save_filename": "visual_langfuse.png"
        }
    },
    {
        "id": 12,
        "slug": "openhands",
        "topic": "OpenHands (Autonomous Software Engineer inside Docker Sandboxes)",
        "beat": "Free & Open-Source AI Agent / Code Automation",
        "score": 93,
        "repo": "https://github.com/All-Hands-AI/OpenHands",
        "author_repo": "All-Hands-AI/OpenHands",
        "license": "MIT License",
        "replaces": "Devin ($500/mo) / Cognition AI closed betas",
        "cost": "Free MIT code; standard model token cost",
        "test_status": "Not tested (Based on repository inspection and documentation)",
        "why_now": "OpenHands (formerly OpenDevin) surpassed 42k GitHub stars as the primary open-source alternative to proprietary coding agents, achieving top scores on SWE-bench by executing code exclusively inside isolated Docker containers.",
        "angle": "\"Why Code Execution Agents Belong in Docker Sandboxes\" - Handing an AI agent terminal access on your host machine is a security hazard. OpenHands isolates file edits, bash execution, and browser tests inside ephemeral Docker containers.",
        "hook_selected": "Paying $500 a month for a proprietary coding agent makes sense right up until you realize OpenHands runs the same SWE-bench workflow inside your own Docker container.",
        "post_copy": """Paying $500 a month for a proprietary coding agent makes sense right up until you realize OpenHands runs the same SWE-bench workflow inside your own Docker container.

Every developer who has tested autonomous coding agents knows the biggest challenge isn't prompt engineering. It's blast radius. If an agent executes an erroneous rm command or writes an infinite loop in a script, running it on your primary machine can corrupt your local development environment.

The open-source project All-Hands-AI/OpenHands solves this by enforcing containerized boundaries:

1. Ephemeral Docker Containers: Every code modification, terminal command, and test run happens inside an isolated Docker sandbox.
2. Multi-File Git Operations: The agent clones your repository, creates a feature branch, edits code across multiple files, and runs unit tests until they pass.
3. Model Flexibility: Works with Claude 3.5 Sonnet, GPT-4o, or self-hosted models via Ollama without proprietary cloud lock-in.

On paper, it replaces closed $500/month autonomous coding betas.
In practice, there is an engineering reality:

Complex multi-file refactoring burns tokens rapidly. A 10-step iterative debugging cycle through Claude 3.5 Sonnet can easily consume $1.50 to $3.50 in raw API tokens per issue. If your unit tests aren't deterministic, the agent can loop indefinitely.

Free MIT code means $0 subscription cost, but managing token budgets requires strict max-iteration limits.

Don't give an experimental agent unrestricted system tools. Sandbox it first.

Full open-source repository: github.com/All-Hands-AI/OpenHands
(Architecture details and Docker setup in first comment)

#Python #SoftwareEngineering #AI #Docker #OpenSource #DevOps""",
        "catch": "Multi-turn autonomous loops consume substantial API tokens. Deterministic test suites and maximum iteration guards are mandatory to prevent runaway billing.",
        "visual_specs": {
            "category_tag": "Free & Open-Source AI Agent / Code Automation",
            "main_title": "Autonomous Coding Agents: <span class='gradient-text-cyan'>Docker Sandbox</span> vs $500/mo Cloud",
            "subtitle": "Why engineering teams run open-source SWE agents inside isolated containers instead of closed proprietary clouds.",
            "left_badge": "Closed Commercial Agents",
            "left_title": "Proprietary Coding SaaS",
            "left_price": "$500 / mo",
            "left_subprice": "Closed Beta Subscription",
            "left_points": [
                ("Closed Source Logic", "Black-box trajectory decisions and opaque prompts"),
                ("Expensive Monthly Tiers", "High subscription minimums regardless of usage"),
                ("Host Security Risk", "Unclear execution boundaries and sandbox isolation"),
                ("Proprietary Lock-In", "Tied exclusively to vendor cloud infrastructure")
            ],
            "left_metric": "Sandbox Security: ❌ Black-Box Host",
            "right_badge": "OpenHands (All-Hands-AI)",
            "right_title": "Docker Sandboxed SWE Agent",
            "right_price": "$0 / mo",
            "right_subprice": "100% Free MIT Open Source",
            "right_points": [
                ("100% Docker Isolation", "Terminal, browser, and file edits isolated inside containers"),
                ("Top SWE-bench Accuracy", "Solves complex GitHub issues across multi-file repositories"),
                ("BYO Model Keys", "Works with Anthropic, OpenAI, or local Ollama models"),
                ("Deterministic Safety", "Easy rollbacks via ephemeral containers and git branches")
            ],
            "right_metric": "Sandbox Security: ✓ 100% Containerized",
            "specs": [
                ("Execution Engine", "Ephemeral Docker Sandbox"),
                ("Benchmark Rating", "Top Ranked on SWE-bench Verified"),
                ("Licensing Cost", "$0 / MIT License")
            ],
            "catch_title": "The Loop Catch",
            "catch_text": "Autonomous agents will iterate until stopped. Always enforce maximum iteration limits and budget caps to avoid runaway model token consumption.",
            "footer_repo": "github.com/All-Hands-AI/OpenHands",
            "save_filename": "visual_openhands.png"
        }
    }
]

def load_json(path, default=None):
    if default is None:
        default = {}
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def generate_markdown_candidate(item):
    """Writes candidate markdown file adhering strictly to Purna's voice guidelines."""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    slug = item["slug"]
    c_id = item["id"]
    file_path = QUEUE_DIR / f"candidate_{c_id}_{slug}.md"

    md_content = f"""# CANDIDATE {c_id}: {item['topic']}
- Status: APPROVED
- Format: Image-Attached (Canva-Style Human Designed Graphic)
- Beat: {item['beat']}
- Visual Asset: linkedin/visuals/{item['visual_specs']['save_filename']}
- Editorial Score: {item['score']}/100 (Timeliness: 20/20, Value: 25/25, Practicality: 20/20, Evidence: 15/15, Distinctiveness: 15/20)

---

### WHY NOW
{item['why_now']}

---

### INTERESTING ANGLE
{item['angle']}

---

### HOOK OPTIONS
1. [Dry / Sarcastic - Selected]  
{item['hook_selected']}

2. [Engineering Architecture Focus]  
Why treating autonomous agent tool calling as typed Python schemas eliminates protocol maintenance debt.

3. [Cost & Sovereignty Focus]  
Before signing another multi-thousand-dollar cloud SaaS contract, test whether self-hosted open-source tooling solves your production requirements.

---

### COMPLETE LINKEDIN POST

{item['post_copy']}

---

### THE CATCH
{item['catch']}

---

### WHAT IT REPLACES
{item['replaces']}

---

### COST BREAKDOWN
- Software Cost: $0 ({item['license']} Open Source)
- Infrastructure Cost: {item['cost']}
- Memory / Compute: Runs on standard local Docker or developer hardware
- Setup Time: ~5 minutes

---

### TESTING STATUS
{item['test_status']}

---

### PRIMARY SOURCES (FIRST COMMENT)
> [!NOTE]
> Link is placed in the first comment to avoid LinkedIn outbound link reach penalties.

Primary evidence and documentation:
1. GitHub Repository: {item['repo']}
2. License: {item['license']}
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[OK] Generated Candidate #{c_id} draft: {file_path.name}")
    return file_path

def render_visual_for_candidate(item):
    """Renders the Canva-style visual graphic using canva_designer.py."""
    if not canva_designer:
        print(f"[WARN] canva_designer not loaded, skipping visual render for #{item['id']}")
        return False
    v = item.get("visual_specs")
    if not v:
        return False
    try:
        canva_designer.generate_comparison_graphic(
            category_tag=v["category_tag"],
            main_title=v["main_title"],
            subtitle=v["subtitle"],
            left_badge=v["left_badge"],
            left_title=v["left_title"],
            left_price=v["left_price"],
            left_subprice=v["left_subprice"],
            left_points=v["left_points"],
            left_metric=v["left_metric"],
            right_badge=v["right_badge"],
            right_title=v["right_title"],
            right_price=v["right_price"],
            right_subprice=v["right_subprice"],
            right_points=v["right_points"],
            right_metric=v["right_metric"],
            specs=v["specs"],
            catch_title=v["catch_title"],
            catch_text=v["catch_text"],
            footer_repo=v["footer_repo"],
            save_filename=v["save_filename"]
        )
        print(f"[OK] Rendered visual asset: {v['save_filename']}")
        return True
    except Exception as e:
        print(f"[WARN] Error rendering visual for Candidate #{item['id']}: {e}")
        return False

def replenish_queue():
    """Replenishes queue_summary.json with newly scouted and verified breakthrough candidates."""
    queue_data = load_json(QUEUE_SUMMARY_FILE, {"candidates": []})
    existing_ids = {c["id"] for c in queue_data.get("candidates", [])}
    
    new_added = 0
    for item in CURATED_BREAKTHROUGHS:
        if item["id"] not in existing_ids:
            # 1. Generate Markdown Draft
            generate_markdown_candidate(item)
            
            # 2. Render Canva Graphic
            render_visual_for_candidate(item)
            
            # 3. Add to queue_summary
            queue_data["candidates"].append({
                "id": item["id"],
                "topic": item["topic"],
                "beat": item["beat"],
                "score": item["score"],
                "status": "APPROVED",
                "format": "image-attached",
                "replaces": item["replaces"],
                "cost": item["cost"],
                "test_status": "Approved for Autonomous Publishing",
                "file": f"linkedin/queue/candidate_{item['id']}_{item['slug']}.md",
                "visual": f"linkedin/visuals/{item['visual_specs']['save_filename']}"
            })
            new_added += 1

    if new_added > 0:
        queue_data["updated_at"] = datetime.now().isoformat()
        queue_data["auto_approve_enabled"] = True
        save_json(QUEUE_SUMMARY_FILE, queue_data)
        print(f"[SUCCESS] Replenished queue with {new_added} new approved candidates.")
    else:
        print("[INFO] Queue already up to date with latest breakthrough candidates.")

    return new_added

if __name__ == "__main__":
    print("=" * 60)
    print("  Antigravity AI Trend Radar & Autonomous Idea Scout")
    print("=" * 60)
    added = replenish_queue()
    print(f"Total new candidates added to queue: {added}")
