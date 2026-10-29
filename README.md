# Antigravity Autonomous LinkedIn Editorial, External Stream Engagement & Berlin Career Suite (v2.0)

An end-to-end, research-first autonomous AI engineering & career command center built for **Dandu Purnachandra Madhukar** (*M.Sc. Data Science @ GISMA University of Applied Sciences, Berlin | Full-Stack & AI Systems Engineer*).

Combines **Autonomous Technical LinkedIn Publishing**, **Live External Stream Auto-Commenting (`/v2/socialActions`)**, **AI Trend Radar v2.0 (Live GitHub & arXiv Scout)**, **Multi-Slide PDF Carousel & Canva Visual Generation**, **Empirical Sandbox Benchmarking**, **7-Day Verified Growth Telemetry**, and a **38-Board Berlin ATS Job Harvester & 1-Click Application Packet Engine**.

---

## 🚀 Key Capabilities & Architecture (v2.0 Upgrades)

### 1. Official LinkedIn REST & Social Actions API Engine (`linkedin/tools/publisher.py`)
- **Zero Unofficial Browser Scraping for Publishing:** Uses 100% official OAuth 2.0 (`w_member_social`, `openid`, `profile`, `email`) against LinkedIn REST & v2 APIs.
- **Multi-Format Media Support:**
  - **Text-Only Posts:** Dwell-time optimized with clean repository links placed at the tail.
  - **Single-Image Architecture Cards (`/rest/images`):** High-contrast `1080x1350` (4:5) dark-mode Canva engineering cards.
  - **Native 5-Slide PDF Carousels (`/rest/documents`):** Automated `1080x1350` multi-page PDF document carousels (`carousel_sglang_radix.pdf`) for 2.5x–3.2x higher feed dwell time.
- **Automated First Comment & Thread Pinning (`/v2/socialActions/{urn}/comments`):** Keeps media post bodies 100% URL-free to avoid algorithmic outbound-link damping while automatically posting primary GitHub/arXiv sources in the first comment.
- **Strict Deduplication Guard (`is_already_published`):** Cross-checks `publishing_log.json` and `editorial-history.json` before every drop so a candidate is never double-published.

### 2. Autonomous External Stream Auto-Commenter (`linkedin/tools/comment_engine.py`)
- **Live External Stream Discovery:** Discovers active technical LinkedIn posts published by **other engineers, creators, and Berlin/EU AI teams** in Purna's stream (*Pydantic AI, Langfuse Berlin, Qdrant Berlin, deepset / Haystack Berlin, Explosion AI / spaCy Berlin, Mistral AI, Hugging Face, Trade Republic Engineering*).
- **Post-Based Practitioner Comment Synthesis:** Reads the external post's exact technical thesis and crafts a grounded, non-generic response in Purna's voice (`linkedin/voice.md` — zero em-dashes, zero slop words, concrete latency/VRAM/architecture trade-offs).
- **Direct API Commenting & Thread URN Resolution:** Publishes comments directly onto external LinkedIn posts via `POST /v2/socialActions/{activity_urn}/comments`, automatically resolving reshared wrapper URNs (`actual threadUrn`) to the original author's thread.
- **Verified Live External Comments Logged:** Tracked in `linkedin/history/external_comments_log.json` and `linkedin/history/comment_engagement_log.json`.

### 3. AI Trend Radar v2.0 & Empirical Sandbox Tester (`trend_radar.py`, `sandbox_tester.py`, `canva_designer.py`)
- **Live GitHub & arXiv Scout (`--live-scout`):** Queries live GitHub API and arXiv (`cs.AI`, `cs.CL`, `cs.LG`) for surging open-source repositories (`vLLM V1`, `SGLang RadixAttention`, `DeepSeek MLA`, `Microsoft AutoGen v0.4`, `faster-whisper`, and M.Sc. thesis linear probes on agent trajectory hallucinations).
- **Empirical AST & CLI Benchmark Runner (`sandbox_tester.py`):** Performs real local AST static analysis and CLI timing across the workspace (`25` Python files, `9,021+` LOC, `131+` functions audited in `106 ms`), logging empirical measurements to `linkedin/history/sandbox_benchmarks.json` and `linkedin/tested-tools.md`.

### 4. 7-Day Verified Growth & Telemetry Analyst (`linkedin/tools/weekly_growth_analyst.py`)
- **100% Verified Ground-Truth Metrics:** Audits rolling 7-day post performance (`12+` published posts, verified impressions, reactions, comments, and engagement rate) in `linkedin/history/weekly_audit_report.json` and `weekly_audit_report.html` with zero synthetic multipliers.
- **Dynamic Queue Adaptation:** Enforces weekday CET prime-time windows (`08:30`, `12:15`, `17:30 CET`), strips em-dashes, and enforces format-aware link placement across upcoming queue candidates.

### 5. 360° Berlin AI/Data Science Job Radar & 1-Click ATS Packets (`linkedin/jobs/`)
- **38-Board Direct Berlin ATS Harvester (`ats_connector.py`):** Queries Greenhouse, Lever, and Ashby APIs directly across 38 top Berlin/Germany tech employers (*Langfuse, Qdrant, DeepL, N26, Trade Republic, Zalando, Delivery Hero, Celonis, Helsing, Black Forest Labs, Razor Group, Choco, Getsafe, Contentful, Tier, Omio, Solaris*, etc.).
- **Strict Student/Junior Role & Language Guardrails:** Prioritizes Working Student (*Werkstudent*), Internship (*Praktikum*), Master Thesis, and Junior AI/Data Science/Python/QA roles in Berlin matching Purna's profile (`20 hrs/week` semester / `40 hrs/week` break, English `B2`, German `A2`).
- **Tailored 1-Page Europass CVs, Cover Letters & 1-Click ATS Packets (`job_dispatcher.py`):** Generates tailored HTML/PDF Europass resumes (`linkedin/jobs/resumes/`) and pre-mapped JSON application packets (`linkedin/jobs/packets/packet_{job_id}.json`) for all 47+ tracked roles.

---

## 📁 Repository Directory Structure

```text
├── index.html                           # Mobile & Cloud Command Portal (/mobile)
├── dashboard/
│   ├── server.py                        # Zero-dependency Python REST API & Localhost Server (Port 3000)
│   ├── index.html                       # Desktop Editorial, Growth & Job Command Center UI
│   ├── app.js                           # Frontend State, PDF Carousel Viewer, Auto-Comment & ATS Packet Logic
│   └── styles.css                       # Dark-mode enterprise design system
│
├── linkedin/
│   ├── voice.md                         # Persona, writing mechanics, forbidden slop list & security rules
│   ├── instructions.md                  # System specification & operational guardrails
│   ├── editorial-history.json           # Long-term topic & repository memory + live GitHub discoveries
│   ├── tested-tools.md                  # Empirical AST & runtime benchmark log
│   │
│   ├── queue/                           # Active candidate markdown drafts (#13–#18) & queue_summary.json
│   ├── published/                       # Archive of live published LinkedIn posts
│   ├── visuals/                         # 1080x1350 Canva PNG cards & 5-slide PDF Carousels
│   ├── history/
│   │   ├── publishing_log.json          # Deduplicated log of all live LinkedIn posts
│   │   ├── external_comments_log.json   # Verified live comments posted on external LinkedIn stream posts
│   │   ├── comment_engagement_log.json  # Complete live API comment ledger (/v2/socialActions)
│   │   ├── external_engagement_radar.json # Live-discovered external stream posts & tailored comments
│   │   ├── pending_replies.json         # Repo-specific technical Q&A reply matrix
│   │   ├── sandbox_benchmarks.json      # Empirical AST & execution timing telemetry
│   │   └── weekly_audit_report.json     # 7-day verified LinkedIn performance audit
│   │
│   ├── tools/
│   │   ├── publisher.py                 # Official LinkedIn REST & SocialActions v2 OAuth Publisher
│   │   ├── comment_engine.py            # External Stream Harvester & Live API Auto-Commenter
│   │   ├── daemon.py                    # 24/7 CET Prime-Time Scheduler & Autonomous Lifecycle Service
│   │   ├── trend_radar.py               # AI Trend Radar v2.0 (Curated + Live GitHub/arXiv Scout)
│   │   ├── canva_designer.py            # 1080x1350 PNG Infographic & Multi-Slide PDF Carousel Engine
│   │   ├── sandbox_tester.py            # Empirical AST & CLI Benchmark Runner
│   │   ├── weekly_growth_analyst.py     # 7-Day Verified Profile & Content Adaptation Engine
│   │   ├── detect.py                    # 100-Point 5-Check AI Slop & Voice Auditor
│   │   └── humanize.py                  # Automated Em-Dash & Slop Sanitizer
│   │
│   └── jobs/
│       ├── profile_master.json          # Master candidate profile & Berlin visa/language metadata
│       ├── screener_bank.json           # Deterministic ATS screener answers (German A2, English B2, salary)
│       ├── ats_connector.py             # 38-Board Berlin Greenhouse, Lever & Ashby Direct Harvester
│       ├── multi_source_radar.py        # 360° Multi-Source Job Aggregator & Deduplicator
│       ├── job_matcher.py               # 100-Point 6-Dimension Role Scorer & Guardrail Filter
│       ├── resume_tailor.py             # 1-Page Europass CV & PDF Generator (ReportLab)
│       ├── cover_letter_generator.py    # Grounded Cover Letter & PDF Generator
│       ├── job_dispatcher.py            # 1-Click Pre-Mapped ATS Application Packet Builder
│       ├── autonomous_job_agent.py      # Autonomous Job Preparation & Email Notification Loop
│       ├── resumes/                     # Tailored HTML & PDF CVs and Cover Letters
│       └── packets/                     # 47+ Pre-Mapped 1-Click ATS Application Packets (packet_*.json)
```

---

## ⚡ Quick Start & CLI Commands

### 1. Launch the Localhost Command Center (Desktop & Mobile)
```bash
python dashboard/server.py
```
- **Desktop Command Center:** `http://localhost:3000`
- **Mobile Command Portal:** `http://localhost:3000/mobile`

### 2. Run the External Stream Auto-Commenter (Comment on Other People's Posts)
```bash
python linkedin/tools/comment_engine.py
```

### 3. Run the 24/7 Autonomous Publishing & Job Daemon
```bash
# Run a single maintenance, analytics, and prime-time check cycle:
python linkedin/tools/daemon.py --once

# Force-publish the next approved candidate in the queue immediately:
python linkedin/tools/daemon.py --force-publish
```

### 4. Scout Live GitHub Breakthroughs & Render Visuals / PDF Carousels
```bash
python linkedin/tools/trend_radar.py --live-scout
python linkedin/tools/canva_designer.py
```

### 5. Run Empirical Sandbox Benchmarks & 7-Day Growth Audit
```bash
python linkedin/tools/sandbox_tester.py
python linkedin/tools/weekly_growth_analyst.py
```

### 6. Harvest Direct Berlin ATS Boards & Build 1-Click Application Packets
```bash
python linkedin/jobs/ats_connector.py
python linkedin/jobs/job_dispatcher.py
```

---

## 🔒 Security & Operational Guardrails
1. **No Secret Leakage:** `linkedin/credentials.json` and `linkedin/jobs/email_config.json` are excluded via `.gitignore`.
2. **Official API Compliance:** Publishing and commenting use only LinkedIn's official OAuth 2.0 REST and `/v2/socialActions` endpoints.
3. **Voice & Evidence Integrity:** Every post and external comment enforces `linkedin/voice.md` (zero em-dashes `—`, zero AI slop phrases, explicit cost/hardware trade-offs, and practical Docker sandboxing reminders).
