# WORKFLOW: /li-agent (Open-Source AI Agent Finder & Evaluator)

**Trigger Command:** `/li-agent <category or problem, e.g., browser automation, coding agent, transcription>`  
**Goal:** Search GitHub for open-source AI agents that solve real developer problems and evaluate whether they can replace paid AI subscriptions.

---

## EXECUTION STEPS

1. **GitHub & Web Search:** Search for active, open-source GitHub repositories matching the category.
2. **Repository Health Check:**
   - Stars, last commit date, open issues, release frequency.
   - License (MIT, Apache 2.0, Commercial restrictions).
3. **The "What It Replaces" Audit:**
   - Identify paid subscriptions (Cursor, Perplexity, Otter.ai, Browserless).
   - Evaluate feature coverage (Does it replace 20%, 80%, or 100% of the paid tool?).
4. **The "Free" Reality Audit:**
   - Software license vs API token costs (OpenAI/Anthropic/Gemini) vs local inference hardware costs.
5. **Security Audit:**
   - Code execution, file modification, API credentials risk -> Formulate sandboxing warning.
6. **Output Deliverable:**
   - Detailed repository evaluation breakdown ready for `/li-post`.
