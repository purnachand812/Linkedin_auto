# CANDIDATE 8: Pydantic AI (Typed Dependency Injection vs Prompt Guessing)
- Status: PUBLISHED
- Format: Image-Attached (Canva-Style Human Designed Code Architecture Graphic)
- LinkedIn Post URL: https://www.linkedin.com/feed/update/urn:li:share:7516943821306372096/
- Beat: Free & Open-Source AI Agent / Architecture
- Visual Asset: linkedin/visuals/visual_pydantic_ai.png
- Editorial Score: 95/100 (Timeliness: 20/20, Value: 25/25, Practicality: 20/20, Evidence: 14/15, Distinctiveness: 16/20)

---

### WHY NOW
Samuel Colvin and the core Pydantic team released pydantic/pydantic-ai, an open-source agent framework that brings FastAPI-style dependency injection, typed signatures, and runtime validation to LLM agent tools.

---

### INTERESTING ANGLE
"Why Typed Signatures Beat Prompt Guessing" - Most Python agent frameworks rely on 20 lines of prompt instructions hoping an LLM outputs valid JSON keys. Pydantic AI treats tools like typed API endpoints, validating types before function execution.

---

### HOOK OPTIONS
1. [Dry / Sarcastic - Selected]  
Most AI agent frameworks solve tool calling by writing 20 prompt guidelines and praying the LLM respects your dictionary keys. Pydantic AI does what backend engineers should have done on day one: treat agent tools like typed FastAPI endpoints.

2. [Engineering Focus]  
The hardest part of building production AI agents isn't the prompt. It's stopping the model from passing invalid string arguments into functions expecting integers and database sessions.

3. [Cost & Simplicity Focus]  
Before wrapping your codebase in another bloated agent framework with 40 class layers, test whether Pydantic's typed dependency injection handles your tool pipeline with standard Python.

---

### COMPLETE LINKEDIN POST (TEXT-ONLY)

Most AI agent frameworks solve tool calling by writing 20 prompt guidelines and praying the LLM respects your dictionary keys.

Pydantic AI does what backend engineers should have done on day one: treat agent tools like typed FastAPI endpoints.

The core frustration with building agents in Python isn't the model. It's the framework middleware. When you prompt an LLM to generate arguments for a database query or an API call, JSON strings break constantly. You get missing fields, wrong data types, and hallucinated schema keys.

The team behind Pydantic built pydantic/pydantic-ai to solve this with standard Python typing:

1. Static Type Validation: If a tool expects an integer customer_id and a float threshold, Pydantic validates the arguments before the function ever runs.
2. Dependency Injection: Just like FastAPI, your agent tools can inject database connections, API clients, and authenticated sessions directly into the execution context.
3. Model Agnostic: It works with Anthropic, OpenAI, Gemini, or local models via Ollama without wrapping your code in 40 arbitrary abstraction classes.

The catch? Type validation is not hallucination prevention.

Pydantic guarantees that arguments match your function signature. It does not stop an LLM from passing a syntactically valid ID that belongs to the wrong customer. Business logic checks still belong in your Python code.

Free MIT code means $0 software licensing costs. Your only expense is the standard API token bill from your model provider.

I haven't deployed this in a production multi-agent swarm yet, but for Python developers tired of fighting bloated agent frameworks, it feels like actual software engineering.

Repo: https://github.com/pydantic/pydantic-ai

---

### THE CATCH
Type validation verifies schema correctness, but cannot verify semantic truth. Logical verification still requires manual assertions.

---

### WHAT IT REPLACES
Replaces bloated prompt-chaining frameworks (LangChain, CrewAI) and custom regex JSON parsing loops.

---

### COST BREAKDOWN
- Software Cost: $0 (MIT Open Source)
- API Cost: Standard LLM token pricing (Anthropic, OpenAI, Gemini, or $0 with Ollama)
- Setup Time: 2 minutes (`pip install pydantic-ai`)

---

### TESTING STATUS
Not tested (Based on repository inspection and documentation).

---

### PRIMARY SOURCES (FIRST COMMENT - ONLY IF POSTED WITH IMAGE)
> [!NOTE]
> If posting without an image, the GitHub link is included in the post above. No separate first comment is needed.

Primary evidence and documentation:
1. pydantic/pydantic-ai GitHub repository: https://github.com/pydantic/pydantic-ai
2. Pydantic AI Official Documentation: https://ai.pydantic.dev/
