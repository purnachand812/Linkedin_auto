# WORKFLOW: /li-visual (Catchy Technical Visual & Image Asset Generator)

**Trigger Command:** `/li-visual <post text, topic, or image description>`  
**Goal:** Design and generate high-impact visual assets (editorial graphics, architecture diagrams, side-by-side comparisons, or multi-slide carousel blueprints) and save them to `linkedin/visuals/`.

---

## EXECUTION STEPS

### STEP 1: FORMAT & RATIO SELECTION
Determine the most effective visual format:
1. **Single-Image Editorial Graphic / Infographic:** 4:5 Portrait ratio (`1080×1350px`) for maximum feed real estate, or 1.91:1 Landscape (`1200×627px`).
2. **Side-by-Side Comparison:** 4:5 Portrait canvas contrasting Paid vs Free, Benchmark vs Reality, or Architecture A vs Architecture B.
3. **Step-by-Step Workflow Diagram:** Labeled functional blocks showing how an agent or tool operates.
4. **Open-Source Spotlight:** Highlight key specs, license, stars, hardware requirements, and replaced subscriptions.
5. **Multi-Slide Carousel (Sequential Explainer):** Consistent 1080×1350px portrait slides (Slide 1: Hook headline; Slide 2: Problem; Slide 3: Architecture; Slide 4: Evidence/Workflow; Slide 5: The Catch/Cost; Slide 6: Takeaway).

---

### STEP 2: TECHNICAL-EDITORIAL DESIGN SYSTEM
Enforce strict visual quality guidelines:
- **Canvas Aesthetic:** Sleek dark mode background (`#0B0F19`, `#0F172A`, `#1E293B`) or crisp technical canvas (`#F8FAFC`).
- **Typography & Layout:** Clean monospaced or modern sans-serif typography, high contrast text, generous negative space.
- **Color Palette:** Restrained palette—electric cyan (`#06B6D4`), indigo (`#6366F1`), slate gray (`#64748B`), and signal green/amber accents (`#10B981`, `#F59E0B`).
- **Headline Text:** Bold, concise, 3 to 9 words max. Short labels only—NO paragraph dumps.
- **NO CLICHE AI IMAGERY:** Strictly avoid glowing holographic robot heads, blue circuit board brains, stock corporate humanoids, or generic futuristic particle grids. Focus on diagrams, comparisons, and structured technical layouts.

---

### STEP 3: PROGRAMMATIC CANVA/FIGMA RENDERING VIA `canva_designer.py`
1. For technical editorial graphics, side-by-side comparisons, code architectures, and workflow diagrams, use `linkedin/tools/canva_designer.py`.
2. This produces razor-sharp, pixel-perfect 1080×1350 PNG files using Google Chrome headless rendering:
   - Zero AI distortion, zero glowing cyber brains, zero weird clipart.
   - Clean structural cards, badges, high-contrast Plus Jakarta Sans & JetBrains Mono typography.
   - Balanced vertical layout filling the 4:5 frame without empty dead zones.
   - Purnachandra Madhukar's authentic author bio bar and GitHub repository badge.
3. If an artistic conceptual background is needed, use `generate_image` as a texture/accent layer, but enforce clean typography and vector structure via `canva_designer.py`.
4. Save the resulting image asset into `linkedin/visuals/` directory and link it in `queue_summary.json`.

---

### STEP 4: DELIVERABLE OUTPUT
Present:
1. **Visual Concept & Rationale:** Why this format fits the post.
2. **Generated Visual Asset Link:** Markdown image link to the saved file in `linkedin/visuals/`.
3. **Carousel Slide Specification (if multi-slide):** Text and layout breakdown for each slide.
4. **Fact & Number Check:** Verification that all displayed data match primary evidence.
