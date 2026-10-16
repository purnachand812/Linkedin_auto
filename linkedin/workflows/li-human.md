# WORKFLOW: /li-human (Draft Humanizer & Fingerprint Stripper)

**Trigger Command:** `/li-human <paste raw draft text or provide draft file path>`  
**Goal:** Strip AI fingerprint, em dashes, and slop vocabulary, score the draft across 5 quality checks, and output a humanized revision.

---

## EXECUTION STEPS

1. **Pass 1: Typography & Invisible Character Cleaning**
   - Strip all zero-width spaces (`\u200b`, `\u200c`, `\u200d`), soft hyphens (`\u00ad`), BOM (`\ufeff`), non-breaking spaces.
   - Strip em dashes (`—`) and replace with commas or full stops.
   - Convert curly quotes (`“`, `”`, `‘`, `’`) to straight quotes (`"`, `'`).

2. **Pass 2: Slop Vocabulary Stripping**
   - Detect and remove/replace all 113 forbidden slop words (`delve`, `leverage`, `robust`, `seamless`, `game-changer`, etc.).

3. **Pass 3: Structural & Voice Scoring (5 Checks)**
   - Burstiness (Sentence length variation).
   - Specificity (Concrete specs, numbers, prices, repos).
   - Slop Density (Count of forbidden terms per 100 words).
   - Fingerprint (Punctuation and hidden chars).
   - Voice & Tells (Dry first line, no engagement bait endings like "Thoughts?", security warning check if agent).

4. **Pass 4: Execute Python Detector Script**
   - Run `python linkedin/tools/detect.py <draft_file>` or equivalent inline analysis.

5. **Output Deliverable:**
   - Scorecard (0–100 Human Quality Score).
   - List of changes made.
   - Final humanized post draft ready to copy-paste.
