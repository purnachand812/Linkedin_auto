# PUBLISHED POST: Pydantic AI (Typed Dependency Injection vs Prompt Guessing)
- **Candidate ID:** 8
- **Published Date:** 2026-10-16T19:31:07Z
- **Format:** Image-Attached
- **LinkedIn Post ID:** urn:li:share:7516943821306372096
- **LinkedIn Post URL:** https://www.linkedin.com/feed/update/urn:li:share:7516943821306372096/
- **Status:** Successful

---

### POST CONTENT
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

### FIRST COMMENT (SOURCES)
> [!NOTE]
> If posting without an image, the GitHub link is included in the post above. No separate first comment is needed.

Primary evidence and documentation:
1. pydantic/pydantic-ai GitHub repository: https://github.com/pydantic/pydantic-ai
2. Pydantic AI Official Documentation: https://ai.pydantic.dev/
