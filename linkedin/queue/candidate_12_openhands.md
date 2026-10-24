# CANDIDATE 12: OpenHands (Autonomous Software Engineer inside Docker Sandboxes)
- Status: APPROVED
- Format: Image-Attached (Canva-Style Human Designed Graphic)
- Beat: Free & Open-Source AI Agent / Code Automation
- Visual Asset: linkedin/visuals/visual_openhands.png
- Editorial Score: 93/100 (Timeliness: 20/20, Value: 25/25, Practicality: 20/20, Evidence: 15/15, Distinctiveness: 15/20)

---

### WHY NOW
OpenHands (formerly OpenDevin) surpassed 42k GitHub stars as the primary open-source alternative to proprietary coding agents, achieving top scores on SWE-bench by executing code exclusively inside isolated Docker containers.

---

### INTERESTING ANGLE
"Why Code Execution Agents Belong in Docker Sandboxes" - Handing an AI agent terminal access on your host machine is a security hazard. OpenHands isolates file edits, bash execution, and browser tests inside ephemeral Docker containers.

---

### HOOK OPTIONS
1. [Dry / Sarcastic - Selected]  
Paying $500 a month for a proprietary coding agent makes sense right up until you realize OpenHands runs the same SWE-bench workflow inside your own Docker container.

2. [Engineering Architecture Focus]  
Why treating autonomous agent tool calling as typed Python schemas eliminates protocol maintenance debt.

3. [Cost & Sovereignty Focus]  
Before signing another multi-thousand-dollar cloud SaaS contract, test whether self-hosted open-source tooling solves your production requirements.

---

### COMPLETE LINKEDIN POST

Paying $500 a month for a proprietary coding agent makes sense right up until you realize OpenHands runs the same SWE-bench workflow inside your own Docker container.

Every developer who has tested autonomous coding agents knows the biggest challenge isn't prompt engineering. It's blast radius. If an agent executes an erroneous rm command or writes an infinite loop in a script, running it on your primary machine can corrupt your local development environment.

The open-source project All-Hands-AI/OpenHands solves this by enforcing containerized boundaries:

1. Ephemeral Docker Containers: Every code modification, terminal command, and test run happens inside an isolated Docker sandbox.
2. Multi-File Git Operations: The agent clones your repository, creates a feature branch, edits code across multiple files, and runs unit tests until they pass.
3. Model Flexibility: Works with Claude 3.5 Sonnet, GPT-4o, or self-hosted models via Ollama without proprietary cloud lock-in.

On paper, it replaces closed $500/month autonomous coding betas.
In practice, there is an engineering reality:

Complex multi-file refactoring burns tokens rapidly. A 10-step iterative debugging cycle through Claude 3.5 Sonnet can easily consume $1.50 to $3.50 in raw API tokens per issue. If your unit tests aren't deterministic, the agent can loop indefinitely.

Free MIT code means $0 subscription cost, but managing token budgets requires strict max-iteration limits.

Don't give an experimental agent unrestricted system tools. Sandbox it first.

Full open-source repository: github.com/All-Hands-AI/OpenHands

#Python #SoftwareEngineering #AI #Docker #OpenSource #DevOps

---

### THE CATCH
Multi-turn autonomous loops consume substantial API tokens. Deterministic test suites and maximum iteration guards are mandatory to prevent runaway billing.

---

### WHAT IT REPLACES
Devin ($500/mo) / Cognition AI closed betas

---

### COST BREAKDOWN
- Software Cost: $0 (MIT License Open Source)
- Infrastructure Cost: Free MIT code; standard model token cost
- Memory / Compute: Runs on standard local Docker or developer hardware
- Setup Time: ~5 minutes

---

### TESTING STATUS
Not tested (Based on repository inspection and documentation)

---

### PRIMARY SOURCES (FIRST COMMENT)
> [!NOTE]
> Link is placed in the first comment to avoid LinkedIn outbound link reach penalties.

Primary evidence and documentation:
1. GitHub Repository: https://github.com/All-Hands-AI/OpenHands
2. License: MIT License
