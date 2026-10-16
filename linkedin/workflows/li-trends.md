# WORKFLOW: /li-trends (AI Trend Radar & Editorial Scout)

**Trigger Commands / Prompts:**
- `/li-trends`
- `"What's trending?"`
- `"What should we post today?"`
- `"Find today's best topics."`
- `"Show me this week's AI trends."`
- `"Find free AI agents worth covering."`
- `"Find something interesting for LinkedIn."`

**Goal:** Proactively discover recent AI model releases, trending GitHub AI repos/agents, practical automation workflows, and research paper breakthroughs. Rank opportunities using a 100-point quality score and present a daily shortlist so Purna can choose a topic with one click.

---

## EXECUTION STEPS

### STEP 1: CATEGORY RADAR & DISCOVERY SEARCH
Perform web searches across 5 core categories (prioritizing the last 24–72 hours for daily reports, 7 days for weekly reviews):
1. **AI Model Releases & Benchmarks:** New models from OpenAI, Anthropic, Google DeepMind, Meta, DeepSeek, Mistral, Qwen; LMSYS Arena / SWE-bench updates; API pricing drops.
2. **Free & Open-Source AI Agents:** GitHub repos gaining momentum (browser automation, coding agents, local RAG, CLI tools, self-hosted workflows).
3. **Everyday Automation:** Practical workflows replacing paid software (Cursor, Perplexity Pro, Otter.ai, transcription/API wrappers).
4. **AI Hardware, Robotics & Local AI:** Self-hosted models (Ollama, vLLM, GGML/GGUF), AI devices, open hardware.
5. **Research & Technical Discoveries:** arXiv papers on agent architecture, hallucination detection/attribution, multi-step trajectory evaluation.

---

### STEP 2: 100-POINT EDITORIAL OPPORTUNITY SCORING
Evaluate each candidate against 6 criteria:
- **Timeliness (20 pts):** Is this new/developing within 24–72h (or 7d)?
- **Audience Value (25 pts):** Will software engineers, ML students, & data scientists gain concrete insight?
- **Practical Usefulness (20 pts):** Does it save time, automate work, or replace a paid subscription?
- **Evidence Quality (15 pts):** Are primary arXiv papers, official docs, pricing tables, or repo commits available?
- **Visual Potential (10 pts):** Can this be explained visually via a comparison chart, architecture flow, or infographic?
- **Distinctiveness (10 pts):** Is there an underexplored angle beyond repeating marketing press releases?

---

### STEP 3: DAILY SHORTLIST FORMAT (3–5 TOP CANDIDATES)
Present a structured shortlist containing:
- **Rank & Topic Name**
- **What Happened:** (2–3 factual sentences).
- **Why Now:** (Relevance & timing).
- **The Interesting Angle:** (Technical contrast, hidden limitation, or cost reality).
- **Who Should Care:** (Target developer/researcher profile).
- **Suggested Hook:** (One dry, sarcastic line in Purna's voice).
- **Potential Visual:** (Infographic, single-image comparison, or carousel concept).
- **Primary Evidence Links & Publication Dates**
- **Limitations / Missing Info:** (Unverified claims, API costs, missing benchmark baselines).
- **Editorial Score / 100**
- *For Open-Source Repos:* Repo URL, license type, star count/activity, local vs API requirements, paid replacement target, setup difficulty, sandboxing risk.

---

### STEP 4: EDITORIAL RECOMMENDATION & TRANSITION
After the shortlist, explicitly recommend **ONE strongest choice** explaining why it leads.
Support immediate follow-up user commands:
- `"Write topic [N]"` -> Proceeds directly to `/li-post` using gathered research.
- `"You choose"` -> Automatically picks #1 and starts post generation.
- `"Find more"` -> Performs another search sweep for fresh angles.
- `"Only free agents"` -> Filters search exclusively for open-source AI repos & paid tool replacements.

---

### STEP 5: EDITORIAL HISTORY LOGGING
Update `linkedin/editorial-history.json` with newly discovered topics, date, score, status, and sources to prevent duplicate recommendations.
