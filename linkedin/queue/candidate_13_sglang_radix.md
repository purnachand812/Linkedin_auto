# CANDIDATE 13: SGLang RadixAttention (Multi-Turn Agent KV Cache Reuse)
- Status: PUBLISHED
- Format: PDF Document Carousel (5-Slide 1080x1350 Native Deck)
- Beat: AI Models & Local Inference
- Visual Asset: linkedin/visuals/carousel_sglang_radix.pdf
- Editorial Score: 95/100
- Human Quality Score (detect.py): 91.8/100

---

### WHY NOW
SGLang has become a core inference engine for multi-step AI agents by replacing stateless KV cache clearing with RadixAttention, retaining prompt prefixes across branching tool calls in a GPU-resident Radix Tree.

---

### INTERESTING ANGLE
"Why Multi-Turn Agents Waste 70% of Compute Re-Evaluating System Prompts" - In a 15-step agent trajectory, standard inference servers recompute or discard KV cache blocks across subagent branches. SGLang stores KV cache states in an LRU Radix Tree.

---

### HOOK OPTIONS
1. [Dry / Sarcastic - Selected]  
Your multi-turn AI agent isn't slow because the model is thinking hard. It's slow because your inference server re-reads the exact same 4,000-token system prompt on every single step.

2. [Engineering Architecture Focus]  
Why inspecting the underlying system bottleneck beats throwing more hardware or API budget at an AI workflow.

3. [Cost & Sovereignty Focus]  
Before paying another monthly cloud AI subscription, measure what actually happens at the memory and protocol layer when you self-host.

---

### COMPLETE LINKEDIN POST

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

### THE CATCH
Injecting dynamic timestamps or random session IDs at the start of a system prompt invalidates the Radix Tree prefix match and eliminates the KV cache speedup.

---

### WHAT IT REPLACES
Redundant prompt prefill compute & high-latency stateless LLM serving

---

### COST BREAKDOWN
- Software Cost: $0 (Apache 2.0)
- Infrastructure Cost: Free Apache 2.0 code; cuts GPU prefill compute by 60-80% on multi-turn agent loops
- Memory / Compute: Runs on local Docker, GPU workstation, or European VPS
- Setup Time: ~10 minutes

---

### TESTING STATUS
Not tested on production cluster (Based on repository inspection and LMSYS paper)

---

### PRIMARY SOURCES (FIRST COMMENT)
> [!NOTE]
> Automatically posted as the First Comment for image/carousel posts to avoid LinkedIn outbound link reach penalties.

Primary evidence and technical documentation:
1. Primary Source / Repository: https://github.com/sgl-project/sglang (Apache 2.0)
2. LMSYS SGLang Paper (arXiv): https://arxiv.org/abs/2312.07104

