# WORKFLOW: /li-post (LinkedIn Technical Post Generator with Catchy Visuals)

**Trigger Command:** `/li-post [optional topic, model name, tool name, or GitHub URL]`  
**Goal:** Generate a high-quality, research-first technical LinkedIn post written strictly in Purna's voice, accompanied by 3 dry hook options, a generated visual asset, clean first-comment sources, and a full 15-point quality audit.

---

## EXECUTION STEPS

When invoked, the assistant MUST execute the following 9-step pipeline:

### STEP 1: TOPIC SELECTION OR TREND DISCOVERY
- **If topic IS provided:** Categorize into core beat (Model Release, AI Tool, Open-Source Agent/Repo, or Technical Research).
- **If NO topic is provided:** Automatically invoke `/li-trends` to discover the 3–5 top current AI opportunities, present the shortlist, recommend the #1 topic, and proceed once confirmed.

---

### STEP 2: PRIMARY SOURCE GATHERING & REPO AUDIT
- Search via `search_web` for arXiv papers, official technical blog posts, LMSYS/SWE-bench leaderboards, and official pricing tables.
- If evaluating a GitHub repository:
  - Check stars, recent commits, license (MIT, Apache, AGPL, Commercial restrictions).
  - Verify local hardware requirements (GPU/VRAM) vs API key requirements (OpenAI, Anthropic, Gemini, OpenRouter).
  - Determine setup difficulty (`uv pip install` vs Docker vs CUDA compilation).

---

### STEP 3: "FREE" REALITY & "WHAT IT REPLACES" AUDITS
- **Apply the Free Rule:** Distinguish open-source code license vs inference API costs vs GPU electricity/hosting costs. Include: *"Free to download does not mean free to operate."*
- **Apply What-It-Replaces Audit:** Identify specific paid software (Cursor €20/mo, Perplexity Pro €20/mo, Otter.ai, etc.) that could be saved. Qualify replacement percentage based on evidence.

---

### STEP 4: AGENT SECURITY & TEST STATUS CHECK
- **Security Audit:** If the tool/agent executes code, modifies files, runs terminal commands, or automates browsers, append a practical security warning:  
  > *"Don't give an experimental agent your production credentials. Sandbox it first."*
- **Test Status Check:** Check `linkedin/tested-tools.md` and explicitly declare `"Tested on [workload]..."` vs `"Untested; analysis based on repository inspection..."`. Never invent test results.

---

### STEP 5: HOOK GENERATION (3 OPTIONS)
Generate 3 distinct hook options that punch up at AI marketing hype, benchmark theatre, or overblown promises:
1. **Option 1 (Dry / Sarcastic Hype Target):** Directly challenges marketing claims or benchmark footnotes.
2. **Option 2 (Engineering / Technical Focus):** Focuses on architecture, permissions, or system capabilities.
3. **Option 3 (Cost / Subscription Replacement Focus):** Focuses on paid subscription replacements or hidden token costs.

---

### STEP 6: DRAFT THE MAIN POST & FIRST COMMENT
Using the chosen hook direction, draft the post adhering to Purna's voice:
- Short paragraphs (1–3 lines).
- Varied sentence lengths (burstiness).
- Plain, precise technical facts.
- **The Catch:** Hidden costs, rate limits, setup friction, or vendor-reported benchmark gaps.
- NO em dashes (`—`), NO slop words (`delve`, `leverage`, `robust`, `seamless`, `game-changer`), NO generic engagement bait endings (`"Thoughts?"`).

**Link & Comment Rule:**
- **When posting WITHOUT an image (Text-Only):** Include the direct GitHub repository link at the very end of the post text itself (e.g. `Repo: https://github.com/owner/repo`). **Do NOT post or require a separate comment for the link.**
- **When posting WITH an image:** The visual graphic is attached to the post; compile all secondary source links into a First Comment block.

---

### STEP 7: GENERATE CATCHY VISUAL ASSET (`generate_image`)
1. Select format: Single-image editorial graphic, side-by-side comparison diagram, workflow infographic, or carousel blueprint.
2. Formulate a high-contrast dark mode design prompt (modern technical-editorial aesthetic, high contrast, crisp monospaced/sans typography, no glowing robot heads or circuit brain clichés).
3. Call `generate_image` tool to render the visual asset.
4. Save the image to `linkedin/visuals/<topic_name>.png`.

---

### STEP 8: HUMANIZER & QUALITY AUDIT PASS
Run quality verification pass:
- Run `linkedin/tools/detect.py` scoring pass (Burstiness, Specificity, Slop Density, Fingerprint, Voice & Tells).
- Confirm Human Quality Score >= 80/100.

---

### STEP 9: DELIVER COMPLETE PACKAGE
Return the full deliverable:
1. **Topic Analysis & Audit Breakdown**
2. **3 Hook Options**
3. **Draft LinkedIn Post**
4. **Generated Visual Asset** (Image link & concept explanation)
5. **First Comment Sources**
6. **Pre-Publication Quality & Safety Audit Report**
