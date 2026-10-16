# AI-Powered LinkedIn Editorial, Research, Visual, and Publishing Agent

A native, research-first technical LinkedIn content creation system and AI Trend Radar built for **Purnachandra Madhukar** (Full-stack software engineer & MSc Data Science student in Berlin, researching autonomous LLM agent architecture).

Designed to proactively discover AI developments, research claims against primary evidence, draft posts in Purna's voice, generate catchy vector/visual assets, audit quality, manage a 5-post approval queue, and publish via authorized integrations.

---

## 📁 SYSTEM DIRECTORY STRUCTURE

```
linkedin/
│
├── voice.md               # Persona, writing rules, forbidden slop list
├── instructions.md        # System specification & operational guardrails
├── sources.md             # Primary source registry (papers, LMSYS, SWE-bench, pricing)
├── tested-tools.md        # Log of actual personal tests (never populated with fake tests)
├── editorial-history.json # Long-term content memory (topics, repos, posts covered)
│
├── queue/                 # 5-post candidate queue & approval state tracking
├── drafts/                # Drafted candidate post markdown deliverables
├── published/             # Archive log of approved and published posts
├── visuals/               # Generated visual assets (SVG vector graphics & PNGs)
├── sources/               # Research briefs & raw paper notes
└── history/               # Long-term publishing logs
```

---

## ⚡ AUTOMATED WORKFLOW & COMMAND SUITE

When you say `"What's ready?"`, `"Build my five posts."`, or `"Find today's best AI topics."`, the agent executes:

`AI TREND DISCOVERY → RESEARCH → FIND 5 STRONG TOPICS → WRITE 5 POSTS → CREATE 5 VISUALS → FACT-CHECK → EDITORIAL REVIEW → 5-POST APPROVAL QUEUE → MY APPROVAL → AUTHORIZED PUBLISHING`

### Available Commands:

1. **`/li-trends`**: Discover top current AI opportunities and rank them out of 100.
2. **`/li-post`**: If no topic: discover trends → create 5 candidates → generate 5 visuals → queue for approval. If topic supplied: research → write post → generate visual → queue.
3. **`/li-queue`**: Display active candidate posts waiting in the 5-post approval queue.
4. **`/li-publish`**: Safely publish approved candidates via authorized LinkedIn API if available, or report status.
5. **`/li-agent`**: Find free/open-source AI agents and paid-tool replacements.
6. **`/li-research`**: Perform technical investigation on a paper, repo, or model.
7. **`/li-compare`**: Compare models or tools side-by-side with evidence.
8. **`/li-visual`**: Generate or refine visual graphics/diagrams via `generate_image` or SVG vector files.
9. **`/li-human`**: Strip AI fingerprint/slop and score draft quality using `detect.py`.
10. **`/li-comment`**: Prepare clean First Comment primary source links.
11. **`/li-plan`**: Generate a 7-day editorial calendar balanced across content beats.

---

## 🎯 MANDATORY SYSTEM GUARDRAILS

1. **Explicit Approval Gate:** No post is published without explicit user approval (`"Approve 1 and 3"`, `"Approve all"`).
2. **Publishing Safety:** Unofficial browser automation (Puppeteer, Playwright, cookie scraping) is strictly forbidden for publishing. Official authorized APIs are used when available; otherwise execution stops safely after approval state.
3. **The "Free" Rule:** Open-source code license vs API token costs vs local GPU/electricity. *"Free to download ≠ free to operate."*
4. **The "What It Replaces" Audit:** Identify specific paid software (Cursor, Perplexity Pro, Zapier) that could be saved.
5. **Agent Security:** Always append a sandboxing warning for code/file/terminal/browser agents: *"Don't give an experimental agent your production credentials. Sandbox it first."*
6. **Catchy Visuals:** Every candidate includes a generated visual asset saved in `linkedin/visuals/`.
7. **Writing Voice:** Dry, sarcastic line one punching up at hype; short paragraphs; varied rhythm; NO em dashes (`—`); NO slop words (`delve`, `leverage`, `game-changer`, `revolutionary`).
