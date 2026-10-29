# PUBLISHED POST: SGLang RadixAttention (Multi-Turn Agent KV Cache Reuse)
- **Candidate ID:** 13
- **Published Date:** 2026-10-29T17:19:01Z
- **Format:** Text-Only (Link in Post)
- **LinkedIn Post ID:** urn:li:share:7521621624278683649
- **LinkedIn Post URL:** https://www.linkedin.com/feed/update/urn:li:share:7521621624278683649/
- **Status:** Successful

---

### POST CONTENT
Your multi-turn AI agent isn't slow because the model is thinking hard. It's slow because your inference server re-reads the exact same 4,000-token system prompt on every single step.

When an autonomous agent executes a 15-step tool loop, the system prompt, JSON tool schemas, and conversation history get sent repeatedly. Traditional LLM serving engines treat each HTTP request in isolation, discarding or recomputing KV cache blocks the moment an agent branches into parallel tool calls.

The open-source inference engine sgl-project/sglang fixes this at the memory layer using RadixAttention:

1. KV Cache as a Radix Tree: Instead of flushing GPU memory after each response, SGLang retains KV cache tensors inside a Least-Recently-Used (LRU) Radix Tree.
2. Zero-Copy Prefix Sharing: When an agent spawns 5 parallel subagents or retries a failed tool call, all branches share the exact same physical GPU memory blocks for the common prompt prefix.
3. Structured Constrained Decoding: Uses compressed finite-state machines to jump forward multiple tokens at once when generating known JSON schema keys.

On paper, it delivers up to 5x higher throughput on multi-turn agent workloads compared to stateless serving baselines.
In practice, there is a strict prompt engineering catch:

Prefix caching only works if the top of your prompt is 100% deterministic. If you inject `datetime.now()` or a random request UUID into line 1 of your system prompt, you bust the Radix Tree cache on token 5 and force a full GPU prefill recomputation.

Free Apache 2.0 code means $0 licensing cost, but you still need a 24GB+ VRAM GPU to hold the KV cache tree in memory.

I haven't benchmarked this on a multi-node production cluster yet, but for engineers running local agent swarms in Docker, always sandbox your inference server and put dynamic timestamps at the bottom of the prompt.

Full open-source repository: github.com/sgl-project/sglang

#Python #AI #LLM #SoftwareEngineering #OpenSource #MachineLearning

---

> [!NOTE]
> Text-Only Post: GitHub link included directly in post text above. No separate first comment needed.
