# CANDIDATE 2: OpenClaw (Self-Hosted Personal AI Agent)
- Status: APPROVED
- Beat: Free & Open-Source AI Agent / Local AI
- Editorial Score: 92/100 (Timeliness: 19/20, Value: 24/25, Practicality: 19/20, Evidence: 14/15, Visual: 8/10, Distinctiveness: 8/10)

---

### WHY NOW
OpenClaw (openclaw/openclaw) has crossed 20k stars on GitHub as a self-hosted personal AI agent framework that connects messaging tools (Slack, Telegram, Discord) to local system execution.

---

### INTERESTING ANGLE
"Local Agent Privacy vs Electricity Reality": Why developers are switching from cloud assistant SaaS to self-hosted agents, and the real hardware power cost of keeping an LLM gateway running 24/7.

---

### HOOK OPTIONS
1. [Dry / Sarcastic - Selected]  
Another cloud agent wants access to your Slack messages and file system. Naturally, OpenClaw keeps the permissions on your own hardware.

2. [Engineering Focus]  
Putting an AI agent control plane inside Telegram or Slack sounds convenient until you look at the credential boundary.

3. [Cost Focus]  
This self-hosted AI agent is free. The GPU VRAM and 60W electricity to run it 24/7 on your desktop are not.

---

### COMPLETE LINKEDIN POST

Another cloud agent wants access to your Slack messages and file system. Naturally, OpenClaw keeps the permissions on your own hardware.

The open-source repository openclaw/openclaw operates as a self-hosted personal AI agent. It links local model runtimes like Ollama, vLLM, or LM Studio directly into messaging channels like Slack, Discord, and Telegram via a Python local Gateway control plane.

On paper, it replaces paid workflow tools like Zapier ($20/mo) and cloud assistant subscriptions. In practice, self-hosting an always-on agent shifts the trade-off to local infrastructure friction.

Running a local background agent on macOS, Linux, or Windows WSL2 (or Termux on Android) means managing process supervision, Docker container permissions, and idle hardware power. A desktop running local GPU inference consumes 30W-60W of electricity 24/7. If you pair it with commercial OpenAI or Anthropic API tokens instead, continuous messaging loops still accumulate billing fees.

There is also a practical security consideration. Giving an agent access to your docker-compose.yml, repo commits, or local file directory requires strict least-privilege scoping.

I haven't run this on a production setup yet, but for privacy-conscious developers wanting self-hosted workspace automation under an MIT license, it is worth inspecting in a sandboxed Docker container.

Full open-source repository: github.com/openclaw/openclaw
(Direct link pinned in first comment)

---

### THE CATCH
Requires managing process supervision, Docker sandboxing, and keeping local hardware running continuously (30W-60W idle power overhead).

---

### WHAT IT REPLACES
Could replace paid Zapier / Make Slack automation tiers ($20/mo) and third-party cloud assistant subscriptions.

---

### COST BREAKDOWN
- Software Cost: $0 (MIT Open Source)
- API Cost: $0 with Ollama / local models, or standard API fees if using cloud providers
- Hosting / Power: 30W-60W idle electricity on home desktop/server
- Setup Time: 15 minutes (Docker / Python setup)

---

### TESTING STATUS
Not tested (Based on repository and documentation audit).

---

### SOURCES & FIRST COMMENT
- GitHub Repository: https://github.com/openclaw/openclaw (MIT License)
- Documentation: https://github.com/openclaw/openclaw#readme

---

### VISUAL ASSET & CONCEPT EXPLANATION
- Asset Path: linkedin/visuals/visual_openclaw.png
- Visual Concept: Side-by-side Architecture Diagram comparing Cloud SaaS Agent (SaaS fee + third-party privacy risk) vs OpenClaw Local Gateway (MIT license + local hardware privacy boundary).
