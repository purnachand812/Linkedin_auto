# WORKFLOW: /li-publish (Authorized LinkedIn Publishing & Safety Guardrails)

**Trigger Commands:**
- `/li-publish`
- `"Publish approved"`

**Goal:** Safely publish candidate posts that have explicitly reached `APPROVED` status via official, authorized LinkedIn API integrations. Enforce strict safety guardrails preventing browser automation or credential scraping.

---

## EXECUTION STEPS

### STEP 1: VERIFY EXPLICIT APPROVAL STATE
Check `linkedin/queue/` for candidates marked with state: `APPROVED`.
- **Mandatory Guardrail:** NEVER publish candidates in `DRAFT`, `WAITING_FOR_APPROVAL`, `REJECTED`, or `REVISION_REQUIRED` state.
- Inform informal phrases ("looks good", "nice") do NOT trigger publishing without an explicit approval command (`"Approve [N]"`).

---

### STEP 2: AUTHORIZED PUBLISHING INTEGRATION CHECK
Inspect the environment for an official, authorized LinkedIn publishing integration or API access token:
- **Strict Prohibition:** NEVER use browser automation (Puppeteer, Playwright, Selenium, cookie extraction, session hijacking, or CAPTCHA bypass).
- **If official API / integration IS available:**
  1. Transition state: `APPROVED` → `PUBLISHING`.
  2. Upload visual asset from `linkedin/visuals/`.
  3. Create LinkedIn post with main post text.
  4. Post first comment with primary sources.
  5. Receive LinkedIn post ID response.
  6. Transition state: `PUBLISHING` → `PUBLISHED`.
  7. Log event in `linkedin/published/` and `linkedin/history/publishing_log.json`.

---

### STEP 3: SAFELY HANDLE UNAUTHORIZED / MISSING API STATUS
If an official publishing API or authorized integration is NOT configured in the environment:
- Stop execution cleanly after state `APPROVED`.
- Output exact status report:

```text
==================================================
⚠️ PUBLISHING STATUS REPORT
==================================================
Status: Post approved, but no authorised publishing method is available.
Candidate: [N] <Topic Title>
State: APPROVED (Saved in linkedin/queue/)

What was completed:
 - Primary source research & fact-check
 - LinkedIn post draft & First Comment sources
 - Generated visual asset saved in linkedin/visuals/
 - User approval recorded

What still needs to happen:
 - Official LinkedIn API authorization or manual copy-paste to LinkedIn.
 Note: Unofficial browser automation is strictly disabled for security and account safety.
==================================================
```
