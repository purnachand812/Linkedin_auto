# PUBLISHED POST: Internal Hidden-State Probing for Agent Trajectory Hallucinations
- **Candidate ID:** 17
- **Published Date:** 2026-10-31T16:21:29Z
- **Format:** text-only
- **LinkedIn Post ID:** urn:li:share:7522331915173937152
- **LinkedIn Post URL:** https://www.linkedin.com/feed/update/urn:li:share:7522331915173937152/
- **First Comment Auto-Posted:** False
- **Status:** Successful

---

### POST CONTENT
Using GPT-4o as a judge to check if your agent just hallucinated is a great way to double your OpenAI bill and still miss the root cause.

In my MSc Data Science thesis research here in Berlin, I focus on hallucination detection and attribution across multi-step LLM agent trajectories. The most expensive mistake in production agent design is waiting until step 12 to realize the agent fabricated a tool parameter back at step 3.

The standard industry workaround is "LLM-as-a-Judge": running a second frontier model call to grade every step. That doubles your token bill, adds 2 to 4 seconds of latency per turn, and fails whenever the judge shares the same blind spots as the generator.

White-box internal signal probing offers a much faster engineering path:

1. Linear Activation Probes: Training a lightweight logistic classifier on the residual stream activations of middle-to-late transformer layers (typically layers 16 to 24 in a 32-layer model) separates truthful state grounding from confabulation in under 2ms.
2. Attention Entropy Spikes: Before an agent hallucinates a non-existent JSON key or file path, attention head entropy over the tool output context often spikes sharply compared to grounded retrieval steps.
3. Early Trajectory Circuit Breaking: Instead of paying for 8 more doomed reasoning steps, an activation probe flags the exact step where internal uncertainty diverged and triggers a deterministic retry or human handoff.

On paper, linear probes cost $0 in extra LLM tokens and run in microseconds.
In practice, there is a hard deployment catch:

You cannot read hidden-state residual streams from closed black-box APIs like Claude or GPT-4o. Internal activation probing requires serving open-weight models yourself via vLLM or PyTorch `register_forward_hook`, and probes must be recalibrated whenever you swap model families.

Never let an unmonitored agent execute destructive shell or database tools. Combine lightweight activation or schema guards with a strict Docker sandbox first.

Repo / Paper: https://arxiv.org/abs/2304.13734

---

> [!NOTE]
> Text-Only Post: GitHub link included directly in post text above. No separate first comment needed.
