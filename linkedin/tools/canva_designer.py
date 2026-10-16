#!/usr/bin/env python3
"""
canva_designer.py - Human-Designed Canva-Style Visual Generator for Purna's LinkedIn Assistant.
Generates pixel-perfect 1080x1350 PNG editorial graphics using HTML5/CSS3 rendering via Chrome.
Looks handcrafted in Canva or Figma by a senior technical designer.
Zero cliché AI fantasy art (no glowing robot heads, circuit boards, or cheesy clip-art).
"""

import os
import sys
from pathlib import Path
from html2image import Html2Image

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LINKEDIN_DIR = BASE_DIR / "linkedin"
VISUALS_DIR = LINKEDIN_DIR / "visuals"
VISUALS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize html2image renderer at 1080x1350 portrait canvas (LinkedIn 4:5 ratio)
hti = Html2Image(output_path=str(VISUALS_DIR), size=(1080, 1350))

GLOBAL_STYLES = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap');

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  width: 1080px;
  height: 1350px;
  background-color: #080C14;
  background-image: 
    radial-gradient(circle at 85% 12%, rgba(56, 189, 248, 0.12) 0%, transparent 40%),
    radial-gradient(circle at 15% 85%, rgba(99, 102, 241, 0.10) 0%, transparent 45%),
    radial-gradient(circle at 50% 50%, rgba(15, 23, 42, 0.6) 0%, transparent 100%);
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: #F8FAFC;
  padding: 56px 60px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  position: relative;
  -webkit-font-smoothing: antialiased;
}

/* Subtle Grid Background Pattern */
.grid-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-size: 40px 40px;
  background-image: 
    linear-gradient(to right, rgba(255, 255, 255, 0.02) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
  pointer-events: none;
  z-index: 1;
}

.content-wrapper {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  flex: 1;
  justify-content: space-between;
}

/* Header Section */
.header-section {
  margin-bottom: 24px;
}

.category-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(56, 189, 248, 0.10);
  border: 1px solid rgba(56, 189, 248, 0.28);
  color: #38BDF8;
  padding: 7px 16px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.category-tag .pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #38BDF8;
  box-shadow: 0 0 10px #38BDF8;
}

h1.main-title {
  font-size: 48px;
  font-weight: 800;
  line-height: 1.15;
  margin-top: 18px;
  letter-spacing: -0.025em;
  color: #FFFFFF;
}

.gradient-text-cyan {
  background: linear-gradient(135deg, #38BDF8 0%, #818CF8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.gradient-text-emerald {
  background: linear-gradient(135deg, #34D399 0%, #38BDF8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  font-size: 20px;
  line-height: 1.5;
  color: #94A3B8;
  margin-top: 12px;
  max-width: 920px;
}

/* Footer Section */
.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.10);
  margin-top: 24px;
  z-index: 2;
}

.author-box {
  display: flex;
  align-items: center;
  gap: 14px;
}

.author-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0284C7 0%, #4F46E5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 18px;
  color: #FFFFFF;
  border: 2px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
}

.author-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.author-name {
  font-size: 18px;
  font-weight: 700;
  color: #F8FAFC;
}

.author-thesis {
  font-size: 14px;
  color: #94A3B8;
  font-weight: 500;
}

.repo-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  color: #38BDF8;
  background: rgba(56, 189, 248, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.28);
  padding: 8px 18px;
  border-radius: 8px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Callout Box / The Catch */
.catch-banner {
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(245, 158, 11, 0.35);
  border-radius: 14px;
  padding: 18px 24px;
  display: flex;
  align-items: center;
  gap: 18px;
  margin-top: 18px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.catch-badge {
  font-size: 12px;
  font-weight: 800;
  color: #F59E0B;
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.35);
  padding: 6px 12px;
  border-radius: 6px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  white-space: nowrap;
}

.catch-text {
  font-size: 15px;
  line-height: 1.45;
  color: #E2E8F0;
  font-weight: 500;
}

/* Spec Chips Row */
.spec-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 18px;
}

.spec-chip {
  background: #0E1626;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.spec-chip-label {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  color: #64748B;
  letter-spacing: 0.05em;
}

.spec-chip-val {
  font-size: 15px;
  font-weight: 700;
  color: #F8FAFC;
}
"""

def generate_comparison_graphic(
    category_tag="Autonomous Agent Architecture",
    main_title="Closed Paywalls vs <span class='gradient-text-cyan'>Open-Source Agents</span>",
    subtitle="Why senior engineers are migrating from closed AI subscriptions to open Model Context Protocol tooling.",
    left_badge="Closed SaaS Editor",
    left_title="Cursor / Copilot",
    left_price="$20 / month",
    left_subprice="Recurring Cloud Subscription",
    left_points=[
        ("Proprietary Cloud Paywall", "Hardcoded monthly seat tax per developer"),
        ("Closed Tool Ecosystem", "Vendor-controlled integration marketplace"),
        ("Remote Code Scanning", "Private intellectual property leaves your network"),
        ("Prompt Lock-In", "No direct access to agent system prompts or hooks")
    ],
    left_metric="Privacy: ❌ Sent to Cloud",
    right_badge="Open MCP Standard",
    right_title="Cline + Ollama",
    right_price="$0 / month",
    right_subprice="100% Free MIT Open Source",
    right_points=[
        ("100% Local Execution", "Runs entirely inside your local VS Code environment"),
        ("Open MCP Standard", "Connect to any Model Context Protocol tool or DB"),
        ("Zero Vendor Lock-In", "Switch between Claude, DeepSeek, or local Ollama"),
        ("Surgical File Diffs", "Review and approve every code change before commit")
    ],
    right_metric="Privacy: ✓ 100% On-Device",
    specs=[
        ("Model Flexibility", "Any LLM (Local / Cloud API)"),
        ("Tool Protocol", "Open MCP Standard"),
        ("License & Code", "$0 MIT Open Source")
    ],
    catch_title="The Engineering Catch",
    catch_text="Free open-source code does not mean free LLM tokens. Multi-file refactoring runs through frontier models still cost $0.50–$2.00 per task in API usage.",
    footer_repo="github.com/cline/cline",
    save_filename="visual_cline.png"
):
    """
    Template 1: Rich Side-by-Side Canva-Style Comparison Graphic
    """
    left_items_html = ""
    for title, desc in left_points:
        left_items_html += f"""
        <div class="card-point">
          <div class="point-icon point-icon-red">&times;</div>
          <div class="point-text">
            <strong>{title}</strong>
            <span>{desc}</span>
          </div>
        </div>
        """

    right_items_html = ""
    for title, desc in right_points:
        right_items_html += f"""
        <div class="card-point">
          <div class="point-icon point-icon-green">&#10003;</div>
          <div class="point-text">
            <strong>{title}</strong>
            <span>{desc}</span>
          </div>
        </div>
        """

    specs_html = ""
    for lbl, val in specs:
        specs_html += f"""
        <div class="spec-chip">
          <div class="spec-chip-label">{lbl}</div>
          <div class="spec-chip-val">{val}</div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
{GLOBAL_STYLES}

.comparison-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  flex: 1;
  margin-top: 10px;
}}

.compare-card {{
  border-radius: 18px;
  padding: 30px 28px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.4);
  position: relative;
}}

.card-left {{
  background: linear-gradient(180deg, #101624 0%, #0C101A 100%);
  border: 1px solid rgba(239, 68, 68, 0.25);
}}

.card-right {{
  background: linear-gradient(180deg, #0D1B2A 0%, #091320 100%);
  border: 1.5px solid rgba(16, 185, 129, 0.4);
  box-shadow: 0 16px 45px rgba(16, 185, 129, 0.08);
}}

.card-badge {{
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 6px 14px;
  border-radius: 6px;
  width: fit-content;
}}
.badge-red {{ background: rgba(239, 68, 68, 0.15); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.3); }}
.badge-green {{ background: rgba(16, 185, 129, 0.15); color: #6EE7B7; border: 1px solid rgba(16, 185, 129, 0.35); }}

.card-header-group {{
  margin-top: 14px;
}}

.card-title {{
  font-size: 30px;
  font-weight: 800;
  color: #FFFFFF;
}}

.price-container {{
  margin: 10px 0 16px 0;
}}
.card-price {{
  font-size: 44px;
  font-weight: 800;
  line-height: 1;
}}
.price-red {{ color: #EF4444; }}
.price-green {{ color: #10B981; }}
.card-subprice {{
  font-size: 13px;
  color: #94A3B8;
  font-weight: 600;
  margin-top: 4px;
}}

.points-stack {{
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}}

.card-point {{
  display: flex;
  align-items: flex-start;
  gap: 12px;
}}

.point-icon {{
  width: 22px;
  height: 22px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 800;
  flex-shrink: 0;
  margin-top: 2px;
}}
.point-icon-red {{ background: rgba(239, 68, 68, 0.2); color: #EF4444; }}
.point-icon-green {{ background: rgba(16, 185, 129, 0.2); color: #10B981; }}

.point-text {{
  display: flex;
  flex-direction: column;
  gap: 2px;
}}
.point-text strong {{
  font-size: 15px;
  color: #F1F5F9;
  font-weight: 700;
}}
.point-text span {{
  font-size: 13px;
  color: #94A3B8;
  line-height: 1.35;
}}

.card-metric-footer {{
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 13px;
  font-weight: 700;
}}
.metric-red {{ color: #F87171; }}
.metric-green {{ color: #34D399; }}
</style>
</head>
<body>
  <div class="grid-overlay"></div>
  <div class="content-wrapper">
    <!-- Header -->
    <div class="header-section">
      <div class="category-tag"><span class="pulse-dot"></span> {category_tag}</div>
      <h1 class="main-title">{main_title}</h1>
      <p class="subtitle">{subtitle}</p>
    </div>

    <!-- Comparison Cards -->
    <div class="comparison-grid">
      <!-- Left Card -->
      <div class="compare-card card-left">
        <div>
          <div class="card-badge badge-red">{left_badge}</div>
          <div class="card-header-group">
            <div class="card-title">{left_title}</div>
            <div class="price-container">
              <div class="card-price price-red">{left_price}</div>
              <div class="card-subprice">{left_subprice}</div>
            </div>
          </div>
          <div class="points-stack">
            {left_items_html}
          </div>
        </div>
        <div class="card-metric-footer metric-red">{left_metric}</div>
      </div>

      <!-- Right Card -->
      <div class="compare-card card-right">
        <div>
          <div class="card-badge badge-green">{right_badge}</div>
          <div class="card-header-group">
            <div class="card-title">{right_title}</div>
            <div class="price-container">
              <div class="card-price price-green">{right_price}</div>
              <div class="card-subprice">{right_subprice}</div>
            </div>
          </div>
          <div class="points-stack">
            {right_items_html}
          </div>
        </div>
        <div class="card-metric-footer metric-green">{right_metric}</div>
      </div>
    </div>

    <!-- Specs Row -->
    <div class="spec-strip">
      {specs_html}
    </div>

    <!-- Catch Callout -->
    <div class="catch-banner">
      <div class="catch-badge">{catch_title}</div>
      <div class="catch-text">{catch_text}</div>
    </div>

    <!-- Footer -->
    <div class="footer">
      <div class="author-box">
        <div class="author-avatar">PM</div>
        <div class="author-details">
          <div class="author-name">Purnachandra Madhukar</div>
          <div class="author-thesis">MSc Data Science &bull; Autonomous Agent Architecture, Berlin</div>
        </div>
      </div>
      <div class="repo-badge">{footer_repo}</div>
    </div>
  </div>
</body>
</html>
"""
    hti.screenshot(html_str=html, save_as=save_filename)
    print(f"[OK] Canva Comparison Visual generated: linkedin/visuals/{save_filename}")
    return VISUALS_DIR / save_filename

def generate_workflow_graphic(
    category_tag="Computer-Use & Browser Automation",
    main_title="Vision-Based GUI Control: <span class='gradient-text-cyan'>3-Step Loop</span>",
    subtitle="How OS-level visual computer-use agents operate desktop software without traditional APIs.",
    steps=[
        {
            "num": "01",
            "badge": "Input Capture",
            "title": "4K Screen Frame Snapshot",
            "desc": "Captures raw desktop pixels across macOS, Windows, and Linux. Operates purely through screen frames without requiring application accessibility APIs or DOM hooks.",
            "spec": "Resolution: 1080p–4K native",
            "status": "Zero API Dependency"
        },
        {
            "num": "02",
            "badge": "Reasoning Core",
            "title": "Multimodal Vision Planner",
            "desc": "Grounds natural language intent against visual UI elements, calculates exact relative click coordinates (X, Y), and plans the next OS-level mouse or keyboard interaction.",
            "spec": "Model: Claude 3.5 Sonnet / Gemini Vision",
            "status": "3–5 sec Latency per Frame"
        },
        {
            "num": "03",
            "badge": "Execution & Feedback",
            "title": "OS Mouse & Keyboard Actions",
            "desc": "Dispatches physical mouse clicks, drag events, and keystrokes inside an isolated container sandbox, verifying state changes via subsequent screenshot frames.",
            "spec": "Sandbox: Docker / QEMU Isolation",
            "status": "Strict VM Isolation Required"
        }
    ],
    catch_title="Production Reality",
    catch_text="Computer-use agents run at 3–5 seconds per step. They are incredible for workflows with zero APIs, but 20x slower and costlier than standard REST API automations.",
    specs=[
        ("Input Modality", "Raw Screen Frame Pixels"),
        ("Action Surface", "OS Mouse / Keyboard Events"),
        ("Safety Boundary", "Strict Sandboxed VM Required")
    ],
    footer_repo="github.com/simular-ai/agent-s3",
    save_filename="visual_agent_s3.png"
):
    """
    Template 2: Rich Step-by-Step Execution Workflow Graphic
    """
    steps_html = ""
    for s in steps:
        steps_html += f"""
        <div class="step-card">
          <div class="step-sidebar">
            <div class="step-circle">{s['num']}</div>
          </div>
          <div class="step-main">
            <div class="step-header">
              <div class="step-meta">
                <span class="step-badge">{s['badge']}</span>
                <span class="step-spec-inline">{s['spec']}</span>
              </div>
              <div class="step-status">{s['status']}</div>
            </div>
            <div class="step-title">{s['title']}</div>
            <div class="step-desc">{s['desc']}</div>
          </div>
        </div>
        """

    specs_html = ""
    for lbl, val in specs:
        specs_html += f"""
        <div class="spec-chip">
          <div class="spec-chip-label">{lbl}</div>
          <div class="spec-chip-val">{val}</div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
{GLOBAL_STYLES}

.workflow-container {{
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  margin-top: 10px;
}}

.step-card {{
  background: linear-gradient(180deg, #0F172A 0%, #0A101D 100%);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 16px;
  padding: 24px 26px;
  display: flex;
  gap: 20px;
  align-items: flex-start;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
  position: relative;
}}

.step-circle {{
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(56, 189, 248, 0.12);
  border: 1.5px solid rgba(56, 189, 248, 0.35);
  color: #38BDF8;
  font-family: 'JetBrains Mono', monospace;
  font-size: 20px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}}

.step-main {{
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}}

.step-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
}}

.step-meta {{
  display: flex;
  align-items: center;
  gap: 10px;
}}

.step-badge {{
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #94A3B8;
}}

.step-spec-inline {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #64748B;
}}

.step-status {{
  font-size: 12px;
  font-weight: 700;
  color: #38BDF8;
  background: rgba(56, 189, 248, 0.1);
  border: 1px solid rgba(56, 189, 248, 0.25);
  padding: 4px 10px;
  border-radius: 6px;
}}

.step-title {{
  font-size: 22px;
  font-weight: 700;
  color: #FFFFFF;
}}

.step-desc {{
  font-size: 14.5px;
  line-height: 1.5;
  color: #94A3B8;
  font-weight: 450;
}}
</style>
</head>
<body>
  <div class="grid-overlay"></div>
  <div class="content-wrapper">
    <!-- Header -->
    <div class="header-section">
      <div class="category-tag"><span class="pulse-dot"></span> {category_tag}</div>
      <h1 class="main-title">{main_title}</h1>
      <p class="subtitle">{subtitle}</p>
    </div>

    <!-- Workflow Steps -->
    <div class="workflow-container">
      {steps_html}
    </div>

    <!-- Specs Row -->
    <div class="spec-strip">
      {specs_html}
    </div>

    <!-- Catch Callout -->
    <div class="catch-banner">
      <div class="catch-badge">{catch_title}</div>
      <div class="catch-text">{catch_text}</div>
    </div>

    <!-- Footer -->
    <div class="footer">
      <div class="author-box">
        <div class="author-avatar">PM</div>
        <div class="author-details">
          <div class="author-name">Purnachandra Madhukar</div>
          <div class="author-thesis">MSc Data Science &bull; Autonomous Agent Architecture, Berlin</div>
        </div>
      </div>
      <div class="repo-badge">{footer_repo}</div>
    </div>
  </div>
</body>
</html>
"""
    hti.screenshot(html_str=html, save_as=save_filename)
    print(f"[OK] Canva Workflow Visual generated: linkedin/visuals/{save_filename}")
    return VISUALS_DIR / save_filename

def generate_code_contrast_graphic(
    category_tag="AI Agent Architecture & Python",
    main_title="Tool Calling: <span class='gradient-text-emerald'>Typed Validation</span> vs Prompt Guessing",
    subtitle="Why senior backend engineers treat agent tools like typed FastAPI endpoints instead of hoping LLMs format JSON keys.",
    old_title="The Old Way: Prompt Strings & Dict Guessing",
    old_code="""# Prompting the LLM and praying for valid schema
prompt = \"\"\"
Output valid JSON:
{ "user_id": int, "threshold": float }
Do not include extra keys.
\"\"\"
response = llm.generate(prompt)
# Fragile regex & schema parsing:
data = json.loads(response) # Runtime Crash on invalid JSON!
run_query(data["user_id"])  # KeyNotFoundError / Type Mismatch""",
    new_title="Pydantic AI: Typed Dependency Injection",
    new_code="""from pydantic_ai import Agent, RunContext

agent = Agent('anthropic:claude-3-5-sonnet')

@agent.tool
def get_user_data(ctx: RunContext[Database], user_id: int) -> UserRecord:
    # 1. user_id is statically validated before function runs
    # 2. Database session is injected directly from context
    # 3. Output is strictly typed as UserRecord
    return ctx.deps.db.query(user_id)""",
    specs=[
        ("Schema Validation", "Static Pydantic V2 Models"),
        ("Context Injection", "FastAPI-Style Dependency Injection"),
        ("Model Support", "OpenAI, Anthropic, Gemini, Ollama")
    ],
    catch_title="The Engineering Catch",
    catch_text="Pydantic guarantees runtime type safety, not semantic truth. It prevents invalid argument types from crashing your backend, but business logic checks still belong in your code.",
    footer_repo="github.com/pydantic/pydantic-ai",
    save_filename="visual_pydantic_ai.png"
):
    """
    Template 3: Code Contrast / Architecture Graphic (Clean VS Code Dark Style)
    """
    specs_html = ""
    for lbl, val in specs:
        specs_html += f"""
        <div class="spec-chip">
          <div class="spec-chip-label">{lbl}</div>
          <div class="spec-chip-val">{val}</div>
        </div>
        """

    # Format syntax colors for mockup
    def highlight_code(code_str, is_good=True):
        lines = code_str.strip().split("\n")
        highlighted = []
        for line in lines:
            safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if safe_line.strip().startswith("#"):
                highlighted.append(f"<span style='color: #64748B;'>{safe_line}</span>")
            elif "@" in safe_line:
                highlighted.append(f"<span style='color: #F59E0B;'>{safe_line}</span>")
            elif "def " in safe_line or "from " in safe_line or "import " in safe_line or "return " in safe_line:
                highlighted.append(f"<span style='color: #818CF8;'>{safe_line}</span>")
            elif "Crash" in safe_line or "Error" in safe_line:
                highlighted.append(f"<span style='color: #EF4444; font-weight: bold;'>{safe_line}</span>")
            else:
                highlighted.append(f"<span style='color: #CBD5E1;'>{safe_line}</span>")
        return "<br>".join(highlighted)

    old_highlighted = highlight_code(old_code, is_good=False)
    new_highlighted = highlight_code(new_code, is_good=True)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
{GLOBAL_STYLES}

.code-split {{
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  margin-top: 10px;
}}

.code-box {{
  border-radius: 16px;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
}}

.box-bad {{
  background: #0E131E;
  border: 1px solid rgba(239, 68, 68, 0.3);
}}

.box-good {{
  background: #0B1622;
  border: 1.5px solid rgba(16, 185, 129, 0.45);
  box-shadow: 0 12px 35px rgba(16, 185, 129, 0.08);
}}

.code-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
}}

.code-label-bad {{
  font-size: 13px;
  font-weight: 800;
  text-transform: uppercase;
  color: #F87171;
  letter-spacing: 0.06em;
}}

.code-label-good {{
  font-size: 13px;
  font-weight: 800;
  text-transform: uppercase;
  color: #34D399;
  letter-spacing: 0.06em;
}}

.window-dots {{
  display: flex;
  gap: 6px;
}}

.window-dot {{
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
}}

pre.code-content {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  line-height: 1.5;
  overflow: hidden;
  white-space: pre-wrap;
}}
</style>
</head>
<body>
  <div class="grid-overlay"></div>
  <div class="content-wrapper">
    <!-- Header -->
    <div class="header-section">
      <div class="category-tag"><span class="pulse-dot"></span> {category_tag}</div>
      <h1 class="main-title">{main_title}</h1>
      <p class="subtitle">{subtitle}</p>
    </div>

    <!-- Code Contrast Panels -->
    <div class="code-split">
      <!-- Old Box -->
      <div class="code-box box-bad">
        <div class="code-header">
          <div class="code-label-bad">{old_title}</div>
          <div class="window-dots"><div class="window-dot"></div><div class="window-dot"></div><div class="window-dot"></div></div>
        </div>
        <pre class="code-content">{old_highlighted}</pre>
      </div>

      <!-- New Box -->
      <div class="code-box box-good">
        <div class="code-header">
          <div class="code-label-good">{new_title}</div>
          <div class="window-dots"><div class="window-dot"></div><div class="window-dot"></div><div class="window-dot"></div></div>
        </div>
        <pre class="code-content">{new_highlighted}</pre>
      </div>
    </div>

    <!-- Specs Row -->
    <div class="spec-strip">
      {specs_html}
    </div>

    <!-- Catch Callout -->
    <div class="catch-banner">
      <div class="catch-badge">{catch_title}</div>
      <div class="catch-text">{catch_text}</div>
    </div>

    <!-- Footer -->
    <div class="footer">
      <div class="author-box">
        <div class="author-avatar">PM</div>
        <div class="author-details">
          <div class="author-name">Purnachandra Madhukar</div>
          <div class="author-thesis">MSc Data Science &bull; Autonomous Agent Architecture, Berlin</div>
        </div>
      </div>
      <div class="repo-badge">{footer_repo}</div>
    </div>
  </div>
</body>
</html>
"""
    hti.screenshot(html_str=html, save_as=save_filename)
    print(f"[OK] Canva Code Contrast Visual generated: linkedin/visuals/{save_filename}")
    return VISUALS_DIR / save_filename

def build_all_canva_visuals():
    """Generates the full suite of Canva-style visual assets for all active candidates."""
    print("=== Generating High-Quality Canva-Style Technical Visuals ===")

    # Candidate 1: Cline
    generate_comparison_graphic(
        category_tag="Autonomous Agent Architecture",
        main_title="Closed Paywalls vs <span class='gradient-text-cyan'>Open-Source Agents</span>",
        subtitle="Why senior engineers are migrating from closed AI subscriptions to open Model Context Protocol tooling.",
        left_badge="Closed SaaS Editor",
        left_title="Cursor / Copilot",
        left_price="$20 / month",
        left_subprice="Recurring Cloud Subscription",
        left_points=[
            ("Proprietary Cloud Paywall", "Hardcoded monthly seat tax per developer"),
            ("Closed Tool Ecosystem", "Vendor-controlled integration marketplace"),
            ("Remote Code Scanning", "Private intellectual property leaves your network"),
            ("Prompt Lock-In", "No direct access to agent system prompts or hooks")
        ],
        left_metric="Privacy: ❌ Sent to Cloud",
        right_badge="Open MCP Standard",
        right_title="Cline + Ollama",
        right_price="$0 / month",
        right_subprice="100% Free MIT Open Source",
        right_points=[
            ("100% Local Execution", "Runs entirely inside your local VS Code environment"),
            ("Open MCP Standard", "Connect to any Model Context Protocol tool or DB"),
            ("Zero Vendor Lock-In", "Switch between Claude, DeepSeek, or local Ollama"),
            ("Surgical File Diffs", "Review and approve every code change before commit")
        ],
        right_metric="Privacy: ✓ 100% On-Device",
        specs=[
            ("Model Flexibility", "Any LLM (Local / Cloud API)"),
            ("Tool Protocol", "Open MCP Standard"),
            ("License & Code", "$0 MIT Open Source")
        ],
        catch_title="The Engineering Catch",
        catch_text="Free open-source code does not mean free LLM tokens. Multi-file refactoring runs through frontier models still cost $0.50–$2.00 per task in API usage.",
        footer_repo="github.com/cline/cline",
        save_filename="visual_cline.png"
    )

    # Candidate 2: OpenClaw
    generate_comparison_graphic(
        category_tag="Local AI & Privacy",
        main_title="Self-Hosted Gateway vs <span class='gradient-text-cyan'>Cloud SaaS</span>",
        subtitle="Why keeping agent permissions on your own hardware solves the enterprise data privacy boundary.",
        left_badge="Cloud Assistant SaaS",
        left_title="Zapier / Cloud AI",
        left_price="$20 / user",
        left_subprice="Per Seat / Per Month",
        left_points=[
            ("Cloud Credential Storage", "API keys and auth tokens stored on 3rd-party servers"),
            ("Unrestricted Chat Scans", "Cloud services scan private Slack and Discord channels"),
            ("Usage Tiers & Rate Limits", "Monthly execution caps on essential automation runs"),
            ("Zero Hardware Cost", "No home server or idle electricity requirements")
        ],
        left_metric="Boundary: ❌ Third-Party Cloud",
        right_badge="OpenClaw Gateway",
        right_title="Local Self-Hosted",
        right_price="$0 / code",
        right_subprice="100% Free MIT Open Source",
        right_points=[
            ("Local Hardware Boundary", "Keys and execution stay strictly on your local machine"),
            ("Docker Process Sandbox", "Isolates tool runs inside lightweight local containers"),
            ("Direct Model Connectors", "Talks to Ollama, LM Studio, or frontier cloud models"),
            ("Full Channel Ownership", "Bridges WhatsApp, Telegram, and Discord privately")
        ],
        right_metric="Boundary: ✓ 100% Self-Hosted",
        specs=[
            ("Process Isolation", "Docker Container Sandboxing"),
            ("Channel Connectors", "WhatsApp, Telegram, Discord"),
            ("Idle Power Draw", "30W–60W on Home Server")
        ],
        catch_title="The Hardware Catch",
        catch_text="Self-hosting requires maintaining a 24/7 home server or Mac Mini (30W–60W idle draw), plus configuring reverse proxies and firewall ports yourself.",
        footer_repo="github.com/openclaw/openclaw",
        save_filename="visual_openclaw.png"
    )

    # Candidate 3: Agent S3
    generate_workflow_graphic(
        category_tag="Computer-Use & Browser Automation",
        main_title="Vision-Based GUI Control: <span class='gradient-text-cyan'>3-Step Loop</span>",
        subtitle="How OS-level visual computer-use agents operate desktop software without traditional APIs.",
        steps=[
            {
                "num": "01",
                "badge": "Input Capture",
                "title": "4K Screen Frame Snapshot",
                "desc": "Captures raw desktop pixels across macOS, Windows, and Linux. Operates purely through screen frames without requiring application accessibility APIs or DOM hooks.",
                "spec": "Resolution: 1080p–4K native",
                "status": "Zero API Dependency"
            },
            {
                "num": "02",
                "badge": "Reasoning Core",
                "title": "Multimodal Vision Planner",
                "desc": "Grounds natural language intent against visual UI elements, calculates exact relative click coordinates (X, Y), and plans the next OS-level mouse or keyboard interaction.",
                "spec": "Model: Claude 3.5 Sonnet / Gemini Vision",
                "status": "3–5 sec Latency per Frame"
            },
            {
                "num": "03",
                "badge": "Execution & Feedback",
                "title": "OS Mouse & Keyboard Actions",
                "desc": "Dispatches physical mouse clicks, drag events, and keystrokes inside an isolated container sandbox, verifying state changes via subsequent screenshot frames.",
                "spec": "Sandbox: Docker / QEMU Isolation",
                "status": "Strict VM Isolation Required"
            }
        ],
        catch_title="Production Reality",
        catch_text="Computer-use agents run at 3–5 seconds per step. They are incredible for workflows with zero APIs, but 20x slower and costlier than standard REST API automations.",
        specs=[
            ("Input Modality", "Raw Screen Frame Pixels"),
            ("Action Surface", "OS Mouse / Keyboard Events"),
            ("Safety Boundary", "Strict Sandboxed VM Required")
        ],
        footer_repo="github.com/simular-ai/agent-s3",
        save_filename="visual_agent_s3.png"
    )

    # Candidate 4: MarkItDown
    generate_comparison_graphic(
        category_tag="Practical AI Automation & RAG",
        main_title="RAG Quality: Raw OCR vs <span class='gradient-text-emerald'>Structured Markdown</span>",
        subtitle="Why a simple 1-line Python document converter does more for retrieval accuracy than complex vector tricks.",
        left_badge="Legacy Unstructured Parsing",
        left_title="Raw PDF Parsers",
        left_price="Broken Layout",
        left_subprice="Garbage In, Hallucinations Out",
        left_points=[
            ("Fragmented Table Data", "Columns turn into scrambled flat text strings"),
            ("Lost Heading Hierarchy", "Chunking breaks semantic parent-child relationships"),
            ("Hallucinated Answers", "Vector search retrieves corrupt, out-of-order chunks"),
            ("Paid API Tiers", "Cloud parsers charge $0.01–$0.05 per processed page")
        ],
        left_metric="RAG Accuracy: ❌ High Hallucinations",
        right_badge="Microsoft MarkItDown",
        right_title="Structured Markdown",
        right_price="Exact Tables",
        right_subprice="100% Free MIT Open Source",
        right_points=[
            ("Preserved Data Tables", "Converts multi-column Excel & PDF tables into GFM"),
            ("Clean Markdown Syntax", "Retains H1–H4 headers, bullet lists, and code blocks"),
            ("High Retrieval Precision", "Embeddings capture genuine semantic document structure"),
            ("Multi-Format Support", "PDF, DOCX, XLSX, PPTX, WAV, and HTML in one command")
        ],
        right_metric="RAG Accuracy: ✓ High Precision",
        specs=[
            ("Supported Formats", "PDF, DOCX, XLSX, PPTX, HTML"),
            ("Output Standard", "GitHub Flavored Markdown"),
            ("Execution Cost", "$0 / Local Python Pipeline")
        ],
        catch_title="The Extraction Catch",
        catch_text="Complex multi-column financial statements and handwritten forms still confuse pure heuristic parsers. When layout gets too tangled, layout-aware vision models are required.",
        footer_repo="github.com/microsoft/markitdown",
        save_filename="visual_markitdown.png"
    )

    # Candidate 5: Aider
    generate_workflow_graphic(
        category_tag="Open-Source AI Agent / Terminal",
        main_title="Git-Aware Coding: <span class='gradient-text-cyan'>Diffs as Agent Memory</span>",
        subtitle="Why using local git commit logs beats complex vector stores for preventing code edit hallucinations.",
        steps=[
            {
                "num": "01",
                "badge": "Repository Mapping",
                "title": "Tree-Sitter AST & Git Context",
                "desc": "Builds a concise map of entire repository symbols and active git branch state, sending only the relevant file interfaces to the LLM to save token budget.",
                "spec": "Context: Tree-Sitter Symbol Graph",
                "status": "Lightweight & Fast"
            },
            {
                "num": "02",
                "badge": "Code Editing",
                "title": "Multi-File Unified Diffs",
                "desc": "Generates surgical diff patches across targeted files using OpenRouter, Claude, or local Ollama models, eliminating whole-file rewriting hallucinations.",
                "spec": "Format: Unified Git Diffs",
                "status": "Token-Efficient Context"
            },
            {
                "num": "03",
                "badge": "Safety Boundary",
                "title": "Automatic Staged Commits",
                "desc": "Automatically commits every valid edit trajectory with a descriptive message. If tests fail or code breaks, execute instant rollback via git reset.",
                "spec": "Rollback: Instant Git Reset",
                "status": "Automatic Rollback Protection"
            }
        ],
        catch_title="The Developer Reality",
        catch_text="Aider gives you superpowers in terminal workflows, but you remain the senior code reviewer. You still must read every diff before pushing to production branches.",
        specs=[
            ("Code Editing Mechanism", "Unified Search/Replace Diffs"),
            ("Context Compression", "Tree-Sitter Repo Map"),
            ("Safety Mechanism", "Auto-Staged Git Commits")
        ],
        footer_repo="github.com/aider-ai/aider",
        save_filename="visual_aider.png"
    )

    # Candidate 8: Pydantic AI
    generate_code_contrast_graphic(
        category_tag="AI Agent Architecture & Python",
        main_title="Tool Calling: <span class='gradient-text-emerald'>Typed Validation</span> vs Prompt Guessing",
        subtitle="Why senior backend engineers treat agent tools like typed FastAPI endpoints instead of hoping LLMs format JSON keys.",
        specs=[
            ("Schema Validation", "Static Pydantic V2 Models"),
            ("Context Injection", "FastAPI-Style Dependency Injection"),
            ("Model Support", "OpenAI, Anthropic, Gemini, Ollama")
        ],
        catch_title="The Engineering Catch",
        catch_text="Pydantic guarantees runtime type safety, not semantic truth. It prevents invalid argument types from crashing your backend, but business logic checks still belong in your code.",
        footer_repo="github.com/pydantic/pydantic-ai",
        save_filename="visual_pydantic_ai.png"
    )

    # Candidate 6: Smolagents
    generate_comparison_graphic(
        category_tag="Autonomous Agent Architecture",
        main_title="Agent Actions: <span class='gradient-text-cyan'>Executable Code</span> vs JSON Dictionaries",
        subtitle="Why Hugging Face's smolagents writes Python code actions instead of nesting bloated JSON tool calls.",
        left_badge="Traditional Agent Frameworks",
        left_title="JSON Tool Calling",
        left_price="N-Step Latency",
        left_subprice="Bloated Schema Overhead",
        left_points=[
            ("Sequential Tool Calls", "Requires a full LLM roundtrip for every single function"),
            ("Bloated JSON Tokens", "Serializes massive JSON payloads back and forth"),
            ("Hard to Loop & Branch", "Cannot write simple for-loops or conditional logic"),
            ("Syntax Hallucinations", "Frequently fails on nested JSON quotes and commas")
        ],
        left_metric="Efficiency: ❌ High Token Overhead",
        right_badge="Hugging Face smolagents",
        right_title="Code-First Actions",
        right_price="1-Step Code",
        right_subprice="100% Free Apache 2.0 Code",
        right_points=[
            ("Direct Python Execution", "LLM writes concise Python snippets to solve tasks"),
            ("Loops & Control Flow", "Executes loops, filters, and math in a single step"),
            ("Lightweight Core (<1K Lines)", "Under 1,000 lines of code with zero framework bloat"),
            ("Secure AST Sandbox", "Safely intercepts dangerous operations before execution")
        ],
        right_metric="Efficiency: ✓ 3x Fewer LLM Calls",
        specs=[
            ("Action Format", "Native Python Code Snippets"),
            ("Core Footprint", "Under 1,000 Lines of Code"),
            ("Safety Layer", "AST Sandboxed Interpreter")
        ],
        catch_title="The Security Catch",
        catch_text="Running LLM-generated code requires strict sandboxing. While smolagents uses an AST interpreter, production multi-tenant environments require Docker or WebAssembly isolation.",
        footer_repo="github.com/huggingface/smolagents",
        save_filename="visual_smolagents.png"
    )

    # Candidate 7: IBM Docling
    generate_comparison_graphic(
        category_tag="Practical AI Workflows / Document Processing",
        main_title="RAG Parsing: Layout-Aware Vision vs <span class='gradient-text-emerald'>Flat OCR</span>",
        subtitle="Why IBM Docling's local layout engine prevents the data hallucinations plaguing enterprise RAG pipelines.",
        left_badge="Legacy PDF Parsers",
        left_title="Flat Text Extractors",
        left_price="Corrupt Data",
        left_subprice="Unstructured Text Chunks",
        left_points=[
            ("Lost Reading Order", "Multi-column scientific papers get jumbled together"),
            ("Destroyed Data Tables", "Financial numbers disconnect from their column headers"),
            ("Zero Math/Code Support", "LaTeX formulas and code blocks get shredded into noise"),
            ("Expensive Cloud APIs", "Third-party APIs charge per page and store your data")
        ],
        left_metric="Retrieval: ❌ Disconnected Rows",
        right_badge="IBM Docling (MIT)",
        right_title="Layout-Aware Vision",
        right_price="$0 Local",
        right_subprice="Runs 100% On Your Hardware",
        right_points=[
            ("Document Layout Analysis", "Identifies headers, captions, figures, and footnotes"),
            ("TableFormer Architecture", "Reconstructs complex merged tables with high fidelity"),
            ("Native LaTeX & Markdown", "Exports cleanly into GitHub Markdown and LaTeX"),
            ("Zero Data Leakage", "Executes locally on CPU/GPU without cloud calls")
        ],
        right_metric="Retrieval: ✓ Pixel-Accurate Tables",
        specs=[
            ("Model Engine", "TableFormer Layout Vision"),
            ("Output Formats", "Markdown, JSON, LaTeX, HTML"),
            ("Processing Cost", "$0 / Local Compute Engine")
        ],
        catch_title="The Compute Catch",
        catch_text="Layout models require local compute. Processing complex 50-page scanned manuals takes notable CPU/GPU time compared to lightweight regex parsing.",
        footer_repo="github.com/DS4SD/docling",
        save_filename="visual_docling.png"
    )

    # Candidate 9: Crawl4AI
    generate_comparison_graphic(
        category_tag="Free & Open-Source AI Agent / Data Pipelines",
        main_title="Web Scraping for LLMs: <span class='gradient-text-cyan'>Local Playwright</span> vs Cloud SaaS",
        subtitle="Why teams are swapping Firecrawl subscriptions for a self-hosted Python web crawler built specifically for AI pipelines.",
        left_badge="Cloud Scraping SaaS",
        left_title="Firecrawl / Cloud Scrapers",
        left_price="$99 / mo",
        left_subprice="Recurring Cloud Subscription",
        left_points=[
            ("Monthly Credit Caps", "Hits rate limits during large batch scraping runs"),
            ("Third-Party Telemetry", "Target URLs and scraped data flow through cloud servers"),
            ("Per-Page Metering", "Costs escalate rapidly as agent crawls deeper paths"),
            ("Vendor Lock-In", "Tied to cloud proprietary extraction APIs")
        ],
        left_metric="Data Privacy: ❌ Cloud Logged",
        right_badge="Crawl4AI (Local)",
        right_title="Local Async Crawler",
        right_price="$0 / mo",
        right_subprice="100% Free Apache 2.0 Code",
        right_points=[
            ("Blazing Fast Async Crawling", "Powered by async Playwright for 4x faster execution"),
            ("Clean LLM Markdown", "Strips ads, banners, and CSS to save token context"),
            ("Dynamic JS & Scroll Support", "Handles SPAs, infinite scrolls, and click events"),
            ("Zero Cloud Fees", "Runs directly on your laptop, VPS, or Docker container")
        ],
        right_metric="Data Privacy: ✓ 100% Self-Hosted",
        specs=[
            ("Engine", "Async Playwright & Chromium"),
            ("Output Extraction", "Token-Optimized Markdown"),
            ("Execution Cost", "$0 / Zero Cloud Subscription")
        ],
        catch_title="The Infrastructure Catch",
        catch_text="Headless Chromium uses real RAM. Crawling 500 pages in parallel requires managing concurrency and handling Cloudflare/proxy rotation yourself.",
        footer_repo="github.com/unclecode/crawl4ai",
        save_filename="visual_crawl4ai.png"
    )

    print("=== All Canva Visuals Built Successfully! ===")

if __name__ == "__main__":
    build_all_canva_visuals()
