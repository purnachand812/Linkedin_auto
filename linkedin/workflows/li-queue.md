# WORKFLOW: /li-queue (Approval Queue & State Management)

**Trigger Commands:**
- `/li-queue`
- `"What's waiting for approval?"`
- `"Show my queue"`

**Goal:** Display the 5 candidate posts currently in `WAITING_FOR_APPROVAL` state with their topic, score, hook, post snippet, visual link, cost breakdown, paid replacement target, test status, and sources. Allow user to approve, reject, or request revisions.

---

## EXECUTION STEPS

### STEP 1: LOAD CANDIDATE QUEUE
Read `linkedin/queue/queue_summary.json` or inspect files in `linkedin/queue/`.
If queue is empty, automatically trigger `/li-post` (or `/li-trends`) to build a fresh 5-post candidate queue.

---

### STEP 2: DISPLAY QUEUE STATE
Present the active queue using the standard format:

```text
==================================================
📊 LINKEDIN EDITORIAL CONTENT QUEUE
==================================================

[1] <Topic Title 1>
    • Beat: <Content Beat>
    • Score: <Score>/100
    • Status: WAITING_FOR_APPROVAL
    • Replaces: <Paid Tool>
    • Cost: <Cost Breakdown>
    • Test Status: <Testing Status Tag>
    • Visual: <Visual Asset Path>

[2] <Topic Title 2>
    • Beat: <Content Beat>
    • Score: <Score>/100
    • Status: WAITING_FOR_APPROVAL
...
```

---

### STEP 3: USER ACTION PROCESSING
Handle user commands:
- `"Approve 1 and 3"` -> Transitions #1 and #3 to `APPROVED`.
- `"Approve all"` -> Transitions all candidates to `APPROVED`.
- `"Reject 4"` -> Transitions #4 to `REJECTED`.
- `"Rewrite hook for 2"` -> Transitions #2 to `REVISION_REQUIRED` and regenerates hook options.
- `"Publish approved"` -> Invokes `/li-publish`.

---

### STEP 4: STATE PERSISTENCE
Update `linkedin/queue/queue_summary.json` and candidate files with updated state tags (`WAITING_FOR_APPROVAL`, `APPROVED`, `REJECTED`, `REVISION_REQUIRED`).
