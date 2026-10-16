# TESTED & UNTESTED TOOLS LOG

This document explicitly logs which AI models, open-source repositories, and developer tools Purnachandra Madhukar has personally tested vs those analyzed purely via documentation and repository inspection.

---

## 1. PERSONALLY TESTED TOOLS & WORKFLOWS
*(Only add tools here after empirical testing with real workloads)*

- **LLM APIs in Production:** Worked with Anthropic, OpenAI, and Gemini APIs in software engineering tasks.
- **Agent Architectures:** Autonomous LLM agent trajectory analysis, multi-step error/hallucination tracking (thesis research focus).
- **Full-stack Dev Tools:** VS Code, Cursor, Git, Docker, Node.js, Python, TypeScript, PyTorch.
- **LinkedIn Format A/B Testing (2026-10-11):** Tested `smolagents` (text-only) vs `Docling` (image-attached). Confirmed text-only posts drive higher dwell time, impressions, and algorithmic feed reach than static single-image attachments. System policy updated to text-only default.

---

## 2. UNTESTED / DOCUMENTATION-RESEARCHED TOOLS
*(Every post mentioning these tools MUST state "I haven't run this yet" or "Based on documentation and repository inspection...")*

- Any newly discovered open-source agent repo unless explicitly tested locally.
- New model releases prior to hands-on testing on specific codebase tasks.

---

## 3. HOW TO UPDATE THIS LOG
When Purna tests a new tool or model:
1. Move the tool from Section 2 to Section 1.
2. Note the test date, workload (e.g., "Tested on a 50k LOC Next.js repo"), and empirical observations (e.g., latency, token count, failure modes).
