# TESTED & UNTESTED TOOLS LOG

This document explicitly logs which AI models, open-source repositories, and developer tools Purnachandra Madhukar has personally tested vs those analyzed purely via documentation and repository inspection.

---

## 1. PERSONALLY TESTED TOOLS & WORKFLOWS
*(Only add tools here after empirical testing with real workloads)*

- **LLM APIs in Production:** Worked with Anthropic, OpenAI, and Gemini APIs in software engineering tasks.
- **Agent Architectures:** Autonomous LLM agent trajectory analysis, multi-step error/hallucination tracking, and internal hidden-state activation probing concepts (MSc thesis research focus at GISMA Berlin).
- **Full-stack Dev Tools:** VS Code, Cursor, Git, Docker, Node.js, Python, TypeScript, PyTorch, FastAPI, Pydantic, PostgreSQL, Redis, Supabase.
- **LinkedIn Format A/B Testing (2026-10-11):** Tested `smolagents` (text-only) vs `Docling` (image-attached). Confirmed text-only posts drive higher dwell time, impressions, and algorithmic feed reach than static single-image attachments. System policy updated to support text-only default and multi-slide PDF carousels.
- **`linkedin-automation-suite` — Empirical AST & Codebase Benchmark (2026-10-29):** Audited `16` Python modules (`~5,400` LOC across `linkedin/tools/` and `linkedin/jobs/`) via `sandbox_tester.py` with `detect.py` 5-check humanizer panel scoring `>= 89.7/100` across all 6 queued candidates (`#13` to `#18`).

---

## 2. UNTESTED / DOCUMENTATION-RESEARCHED TOOLS
*(Every post mentioning these tools MUST state "I haven't run this yet" or "Based on documentation and repository inspection...")*

- Any newly discovered open-source agent repo unless explicitly tested locally via `linkedin/tools/sandbox_tester.py`.
- New model releases prior to hands-on testing on specific codebase tasks.

---

## 3. HOW TO UPDATE THIS LOG
When Purna tests a new tool or model (or runs `python linkedin/tools/sandbox_tester.py --module <pkg>`):
1. Move the tool from Section 2 to Section 1.
2. Note the test date, workload (e.g., "Tested on a 50k LOC Next.js repo"), and empirical observations (e.g., cold import latency, memory delta, token count, failure modes).
