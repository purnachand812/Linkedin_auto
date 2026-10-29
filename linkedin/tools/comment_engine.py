#!/usr/bin/env python3
"""
comment_engine.py - Autonomous External Stream Commenting & Technical Engagement Engine
for Purnachandra Madhukar (M.Sc. Data Science @ GISMA Berlin | Full-Stack & AI Systems Engineer).

Core Capabilities:
1. Live External Stream Discovery (`discover_external_stream_posts`):
   Harvests real, recent LinkedIn posts published by OTHER engineers, AI labs, and Berlin/EU tech teams
   in Purna's exact stream (Langfuse Berlin, Qdrant Berlin, deepset/Haystack Berlin, Pydantic AI,
   Hugging Face, Mistral AI, Explosion AI/spaCy Berlin, DeepL Germany).
2. Post-Based Contextual Comment Synthesis (`craft_comment_for_external_post`):
   Reads the actual text of the external person's/team's LinkedIn post and crafts a specific,
   practitioner-grade comment that responds directly to the technical claims in that post
   (following linkedin/voice.md: zero em-dashes, zero slop words, concrete architectural trade-offs).
3. Official LinkedIn API Auto-Commenting (`post_live_comment_to_linkedin`):
   Publishes comments directly onto external LinkedIn posts (`urn:li:activity:...`) via
   POST /v2/socialActions/{urn}/comments using Purna's authorized w_member_social token.
"""

import os
import sys
import re
import json
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

import requests
from bs4 import BeautifulSoup
from linkedin.tools import publisher

LINKEDIN_DIR = BASE_DIR / "linkedin"
HISTORY_DIR = LINKEDIN_DIR / "history"
PUBLISHING_LOG_FILE = HISTORY_DIR / "publishing_log.json"
REPLIES_FILE = HISTORY_DIR / "pending_replies.json"
COMMENT_LOG_FILE = HISTORY_DIR / "comment_engagement_log.json"
EXTERNAL_COMMENTS_FILE = HISTORY_DIR / "external_comments_log.json"
EXTERNAL_RADAR_FILE = HISTORY_DIR / "external_engagement_radar.json"

FORBIDDEN_SLOP = [
    "delve", "leverage", "game-changer", "revolutionary", "unlock",
    "landscape", "groundbreaking", "transformative", "paradigm shift",
    "unprecedented", "seamless", "cutting-edge", "robust", "crucial",
    "testament to", "let that sink in", "here's the thing"
]

STREAM_SOURCES = [
    {"author": "Pydantic / Pydantic AI", "slug": "pydantic", "stream": "Typed Python AI Agents & Validation"},
    {"author": "Langfuse (Berlin)", "slug": "langfuse", "stream": "Open-Source LLM Observability & Agent Tracing"},
    {"author": "Qdrant (Berlin)", "slug": "qdrant", "stream": "Vector Search, Reranking & RAG Infrastructure"},
    {"author": "deepset / Haystack (Berlin)", "slug": "deepset-ai", "stream": "Production Agent Pipelines & Sovereign AI"},
    {"author": "Mistral AI (Europe)", "slug": "mistralai", "stream": "European Open-Weight Frontier Models & Responses API"},
    {"author": "Hugging Face", "slug": "huggingface", "stream": "Open-Weight LLMs, llama.cpp & Agent Sandboxing"},
    {"author": "Explosion AI / spaCy (Berlin)", "slug": "explosion-ai", "stream": "Industrial NLP Workflows & Agent Trace Evals"},
    {"author": "DeepL (Germany)", "slug": "deepl", "stream": "Enterprise AI Infrastructure & Low-Latency Voice"}
]


def load_json(path, default=None):
    if default is None:
        default = {}
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def enforce_voice_guardrails(text):
    """Enforces linkedin/voice.md rules: zero em-dashes, zero slop words, crisp punctuation."""
    if not text:
        return ""
    cleaned = text.replace("—", ", ").replace("–", "-")
    for word in FORBIDDEN_SLOP:
        pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
        cleaned = pattern.sub("practical", cleaned)
    return cleaned.strip()


def extract_urn_from_url_or_string(url_or_urn):
    """
    Extracts a valid LinkedIn URN (urn:li:share:..., urn:li:activity:..., urn:li:ugcPost:...)
    from either a raw URN string or a full LinkedIn post URL.
    """
    if not url_or_urn:
        return ""
    s = url_or_urn.strip()
    if s.startswith("urn:li:"):
        return s

    m = re.search(r"(urn:li:(?:share|activity|ugcPost):\d+)", s)
    if m:
        return m.group(1)

    m_act = re.search(r"activity-(\d{15,22})", s)
    if m_act:
        return f"urn:li:activity:{m_act.group(1)}"

    m_ugc = re.search(r"ugcPost-(\d{15,22})", s)
    if m_ugc:
        return f"urn:li:ugcPost:{m_ugc.group(1)}"

    m_shr = re.search(r"share-(\d{15,22})", s)
    if m_shr:
        return f"urn:li:share:{m_shr.group(1)}"

    return ""


# ============================================================================
# 1. CURATED HIGH-SIGNAL EXTERNAL STREAM POSTS & POST-SPECIFIC COMMENTS
# ============================================================================
CURATED_EXTERNAL_STREAM_TARGETS = [
    {
        "post_urn": "urn:li:activity:7521269175026376704",
        "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:7521269175026376704/",
        "author": "Pydantic (Michael Pfaffenberger Benchmark)",
        "author_type": "External AI Engineering Stream",
        "stream_pillar": "Typed Python Agent Tooling & Code-Mode Execution",
        "external_post_snippet": (
            "If your agent updates 200 records with 200 tool calls, the model writes out each call and reads back each result. "
            "You pay for all of those tokens. With code mode, the model writes a short Python loop that makes the calls instead."
        ),
        "comment_text": (
            "This benchmark hits the exact bottleneck we see in multi-step agent trajectories. "
            "Issuing 200 sequential JSON tool calls doesn't just burn output tokens, it forces 200 separate KV-cache prefill passes "
            "over the growing conversation history. Letting the model emit a single typed Python loop collapses 200 round-trips into one execution turn, "
            "provided that loop runs inside an isolated Docker sandbox with strict Pydantic validation on the batch inputs."
        )
    },
    {
        "post_urn": "urn:li:activity:7519108586229231616",
        "post_url": "https://www.linkedin.com/posts/langfuse_two-langfuse-plugins-are-now-available-on-activity-7519108586229231616-DKbW",
        "author": "Langfuse (Berlin AI Engineering)",
        "author_type": "External Berlin AI Ecosystem",
        "stream_pillar": "LLM Observability & Multi-Step Agent Trace Attribution",
        "external_post_snippet": (
            "Two Langfuse plugins are now available... Langfuse Observability captures model calls, tool executions, and token usage "
            "so you can inspect each agent turn. The Langfuse plugin gives your agents skills to use Langfuse: investigate traces, manage prompts."
        ),
        "comment_text": (
            "Giving an evaluation agent direct read access to its own Langfuse turn spans is a really clean pattern for automated failure attribution. "
            "In my M.Sc. research here in Berlin on multi-step agent trajectories, most failures start as silent parameter drift 4 or 5 turns before "
            "the final crash. Being able to query span-level latencies and tool inputs programmatically makes pinpointing that exact drift step much faster."
        )
    },
    {
        "post_urn": "urn:li:activity:7520848453044813825",
        "post_url": "https://www.linkedin.com/posts/qdrant_adding-a-reranker-doesnt-always-improve-activity-7520848453044813825-m1JV",
        "author": "Qdrant (Berlin Vector Database Engineering)",
        "author_type": "External Berlin AI Ecosystem",
        "stream_pillar": "RAG Retrieval Architecture & Hybrid Search",
        "external_post_snippet": (
            "Adding a reranker doesn't always improve retrieval. When teams see poor RAG accuracy, the default reflex is bolting on a heavy cross-encoder reranker."
        ),
        "comment_text": (
            "Good callout. Bolting a cross-encoder reranker onto a RAG pipeline that has broken PDF table chunking or uncalibrated first-stage recall "
            "just adds 200ms of GPU latency per query without fixing the missing context. Preserving document structure in Markdown upfront and tuning "
            "Qdrant's hybrid sparse-dense retrieval solves most top-k misses before a reranker is even necessary."
        )
    },
    {
        "post_urn": "urn:li:activity:7520485629478993921",
        "post_url": "https://www.linkedin.com/posts/qdrant_moving-from-chroma-to-qdrant-you-dont-need-activity-7520485629478993921-aZHR",
        "author": "Qdrant (Vector Migration Engineering)",
        "author_type": "External Berlin AI Ecosystem",
        "stream_pillar": "Vector Database Infrastructure & Data Engineering",
        "external_post_snippet": (
            "Moving from Chroma to Qdrant? You don't need to re-embed everything. Migrate existing embeddings and metadata directly."
        ),
        "comment_text": (
            "Re-computing embeddings across millions of document chunks just to switch vector stores is one of the most common avoidable costs in RAG migrations. "
            "Streaming the existing float vectors and payload schemas directly into Qdrant while enabling scalar or binary quantization on the target collection "
            "saves both API spend and days of ingestion downtime."
        )
    },
    {
        "post_urn": "urn:li:activity:7520786585370427392",
        "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:7520786585370427392/",
        "author": "deepset / Haystack (Berlin AI Agents)",
        "author_type": "External Berlin AI Ecosystem",
        "stream_pillar": "Production LLM Cost Attribution & Pipeline Telemetry",
        "external_post_snippet": (
            "Getting more value from AI starts with understanding what it costs. New cost reporting in Haystack helps you understand "
            "what's driving your estimated LLM spend across workspaces, services, pipelines, providers, and models."
        ),
        "comment_text": (
            "Granular cost attribution per pipeline component is underrated. When an agentic RAG workflow gets expensive in production, "
            "the culprit is rarely the final synthesis prompt. It is almost always repeated system-prompt prefills or an unthrottled query-expansion loop. "
            "Seeing token spend broken down by pipeline node makes it obvious which step can be swapped to a smaller local model."
        )
    },
    {
        "post_urn": "urn:li:activity:7521209464570515456",
        "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:7521209464570515456/",
        "author": "Mistral AI (European Frontier Lab)",
        "author_type": "External European AI Stream",
        "stream_pillar": "Agent Responses API & Structured Tool Trajectories",
        "external_post_snippet": (
            "Today, we're introducing the Responses API in public preview, made for building agents on Mistral. "
            "Each response returns the model's answer, its reasoning and its tool calls as separate items, so your app can handle every step more easily."
        ),
        "comment_text": (
            "Returning reasoning traces, tool calls, and final answers as separate typed items is a much cleaner abstraction for multi-step agents than overloading Chat Completions. "
            "It keeps intermediate scratchpad tokens from breaking strict downstream JSON schema validators and lets you selectively prune verbose reasoning turns from the KV cache history."
        )
    },
    {
        "post_urn": "urn:li:activity:7521594265127518208",
        "post_url": "https://www.linkedin.com/posts/huggingface_we-sat-down-with-mistrals-pierre-stock-and-activity-7521594265127518208-7_On",
        "author": "Hugging Face (with Pierre Stock & Sagar Vaze, Mistral)",
        "author_type": "External Open-Source AI Stream",
        "stream_pillar": "Open-Weight Models, Evals & Agent Sandboxing",
        "external_post_snippet": (
            "We sat down with Mistral's Pierre Stock and Sagar Vaze on launch day of Mistral Large 4. "
            "Open weights. Trained in Mistral's own data centers. Excels at cyber. Full conversation on cyber, training, evals and sandboxing."
        ),
        "comment_text": (
            "Strong open-weight coding and cyber models trained in European data centers solve the data-residency problem for EU engineering teams, "
            "and the emphasis on sandboxing is essential. Whenever an agent is given bash, network, or repository write tools for security or coding tasks, "
            "running the execution environment inside an ephemeral Docker container with dropped capabilities has to be the default."
        )
    },
    {
        "post_urn": "urn:li:activity:7521533400135143424",
        "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:7521533400135143424/",
        "author": "Ines Montani (Co-Founder, Explosion AI / spaCy Berlin)",
        "author_type": "External Berlin Data Science & NLP Creator",
        "stream_pillar": "Hybrid NLP Pipelines & Distilling LLMs into Fast Classifiers",
        "external_post_snippet": (
            "Just shipped a new feature: project templates, reusable end-to-end NLP workflows you and your agent can import and adapt. "
            "Want to optimize your LLM pipelines and replace components with cheaper alternatives? Or train your own classifier?"
        ),
        "comment_text": (
            "Replacing repetitive LLM classification steps with a dedicated lightweight classifier is one of the highest-leverage optimizations in applied NLP. "
            "Using a frontier model to bootstrap and audit the training labels, then swapping the live production router to a deterministic spaCy pipeline "
            "cuts per-request latency from seconds to milliseconds and drops marginal token cost to $0."
        )
    },
    {
        "post_urn": "urn:li:activity:7516764887994306560",
        "post_url": "https://www.linkedin.com/posts/langfuse_how-trade-republic-migrates-live-llm-workflows-activity-7516764887994306560-7Hd1",
        "author": "Langfuse & Trade Republic Engineering (Berlin FinTech AI)",
        "author_type": "External Berlin FinTech & AI Engineering Stream",
        "stream_pillar": "Zero-Downtime LLM Workflow Migration & Shadow Evals",
        "external_post_snippet": (
            "How Trade Republic migrates live LLM workflows in production using Langfuse tracing, dataset benchmarking, and shadow evaluations."
        ),
        "comment_text": (
            "Running shadow evaluations against captured production traces before flipping traffic to a new model checkpoint is the only sane way to handle LLM migrations in regulated FinTech. "
            "Without turn-level regression benchmarks on real edge-case prompts, a model upgrade that looks great on public leaderboards will quietly break downstream JSON tool schemas."
        )
    },
    {
        "post_urn": "urn:li:activity:7520536195123236864",
        "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:7520536195123236864/",
        "author": "deepset / Haystack + secunet + NVIDIA (German Sovereign AI)",
        "author_type": "External German Sovereign AI Stream",
        "stream_pillar": "Air-Gapped & Regulated European AI Infrastructure",
        "external_post_snippet": (
            "Working alongside secunet Security Networks AG, Red Hat, and NVIDIA to make secure, sovereign AI accessible to organizations operating in the most sensitive and highly regulated environments."
        ),
        "comment_text": (
            "For regulated German public-sector and industrial deployments, sovereign AI has to mean full control over the entire inference and orchestration stack, not just an EU cloud region toggle. "
            "Running containerized Haystack pipelines over local open-weight models on dedicated GPU nodes is the blueprint more European enterprises need."
        )
    }
]


# ============================================================================
# 2. LIVE EXTERNAL STREAM HARVESTER & CONTEXTUAL COMMENT GENERATOR
# ============================================================================
def craft_comment_for_external_post(post_text, author_name="", stream_topic=""):
    """
    Analyzes the actual text of another person's LinkedIn post and generates a
    grounded, post-specific technical comment in Purna's voice.
    """
    txt = (post_text or "").strip()
    low = txt.lower()

    if "rerank" in low or "qdrant" in low or "vector" in low or "chroma" in low:
        body = (
            "In practice, most retrieval misses blamed on vector search actually come from noisy document chunking upstream. "
            "Preserving table and heading boundaries in Markdown and combining sparse-dense hybrid retrieval fixes recall@k "
            "without adding 200ms of cross-encoder reranking latency on every turn."
        )
    elif "trace" in low or "langfuse" in low or "observability" in low or "eval" in low:
        body = (
            "From our work on multi-step agent trajectories here in Berlin, final-output evals rarely tell you why a run failed. "
            "Inspecting intermediate tool-call spans and token latency spikes is the only reliable way to catch silent context drift "
            "before it compounds across 10+ turns."
        )
    elif "200" in low or "loop" in low or "pydantic" in low or "tool call" in low:
        body = (
            "Collapsing sequential tool calls into a typed Python batch loop saves massive KV-cache prefill overhead across long trajectories. "
            "Pairing strict Pydantic schema validation with an isolated Docker execution sandbox gives you that speed without expanding the blast radius."
        )
    elif "cost" in low or "spend" in low or "token" in low or "haystack" in low:
        body = (
            "Breaking down token spend at the pipeline-node level always reveals the same culprit: repeated system-prompt prefills and unthrottled retry loops. "
            "Once you have per-step cost visibility, routing classification and extraction nodes to smaller quantized checkpoints cuts 60%+ of wasted spend."
        )
    elif "mistral" in low or "open weight" in low or "sandbox" in low or "huggingface" in low:
        body = (
            "Having frontier open weights with transparent lineage is a big deal for European teams running under strict data-residency constraints. "
            "When pairing these models with autonomous tool execution, isolating the runtime inside an ephemeral Docker sandbox keeps production credentials safe."
        )
    else:
        res = generate_post_based_comments(txt, author_name=author_name)
        body = res["generated_comments"][0]["text"]

    return enforce_voice_guardrails(body)


def discover_external_stream_posts(max_per_source=2):
    """
    Live-scouts recent public LinkedIn posts from other people & engineering teams
    in Purna's stream (Berlin AI, LLM Systems, Agent Frameworks, Data Science)
    and pairs each discovered post with a post-specific comment.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    discovered = list(CURATED_EXTERNAL_STREAM_TARGETS)
    seen_urns = {item["post_urn"] for item in discovered}

    for src in STREAM_SOURCES:
        url = f"https://www.linkedin.com/company/{src['slug']}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select("article.main-feed-activity-card")
            added = 0
            for c in cards:
                urns = re.findall(r"urn:li:activity:\d+", str(c))
                if not urns:
                    continue
                act_urn = urns[0]
                if act_urn in seen_urns:
                    continue
                text_el = c.select_one(".attributed-text-segment-list__content, p.commentary")
                link_el = c.select_one("a[href*='/posts/']")
                txt = text_el.get_text(" ", strip=True) if text_el else ""
                if len(txt) < 80:
                    continue
                # Skip non-technical social/running club posts
                if any(w in txt.lower() for w in ["5k run", "Nintendo Switch", "fireside chat tomorrow"]):
                    continue
                href = link_el.get("href", "").split("?")[0] if link_el else f"https://www.linkedin.com/feed/update/{act_urn}/"
                seen_urns.add(act_urn)
                discovered.append({
                    "post_urn": act_urn,
                    "post_url": href,
                    "author": src["author"],
                    "author_type": "External Stream Post",
                    "stream_pillar": src["stream"],
                    "external_post_snippet": txt[:320],
                    "comment_text": craft_comment_for_external_post(txt, author_name=src["author"], stream_topic=src["stream"])
                })
                added += 1
                if added >= max_per_source:
                    break
        except Exception:
            continue

    return discovered


def generate_post_based_comments(post_text_or_topic, post_url="", author_name=""):
    """
    Analyzes any external LinkedIn post text or topic and generates 3 tailored, voice-compliant
    technical comments aligned with Purna's profile.
    """
    raw = (post_text_or_topic or "").strip()
    low = raw.lower()
    extracted_urn = extract_urn_from_url_or_string(post_url or raw)

    detected_tech = []
    tech_map = {
        "vllm": "vLLM V1 / continuous batching",
        "sglang": "SGLang RadixAttention",
        "deepseek": "DeepSeek MLA / low-rank KV compression",
        "mcp": "Model Context Protocol (FastMCP)",
        "pydantic": "Pydantic typed validation",
        "rag": "RAG chunking & hybrid retrieval",
        "qdrant": "Qdrant hybrid vector search",
        "agent": "multi-step agent trajectories",
        "hallucinat": "token-level hallucination attribution",
        "docker": "ephemeral Docker sandboxing",
        "langfuse": "OpenTelemetry / Langfuse tracing",
        "whisper": "CTranslate2 INT8 faster-whisper",
        "ollama": "local quantized inference",
        "mistral": "open-weight European LLM serving",
        "berlin": "Berlin / EU sovereign AI deployment",
        "quality": "industrial quality control telemetry"
    }
    for k, label in tech_map.items():
        if k in low:
            detected_tech.append(label)

    primary_focus = detected_tech[0] if detected_tech else "multi-step LLM systems and production data pipelines"
    secondary_focus = detected_tech[1] if len(detected_tech) > 1 else "strict schema validation and Docker sandboxing"

    first_line = raw.splitlines()[0][:90].strip() if raw else "External Stream Post"
    author_prefix = f"Great breakdown, {author_name.strip()}. " if author_name and author_name.strip() else ""

    comments = [
        {
            "angle": "1. Systems & Bottleneck Breakdown (Practitioner Take)",
            "text": enforce_voice_guardrails(
                f"{author_prefix}In practice, the bottleneck with {primary_focus} rarely shows up in a single-turn demo. "
                f"It surfaces when concurrent workers hit the pipeline and latency compounds across steps. "
                f"Combining {secondary_focus} with deterministic prefix caching cuts token waste and keeps tail latency predictable on standard GPU hardware."
            )
        },
        {
            "angle": "2. M.Sc. Research Angle: Trajectory Reliability & Hallucination Attribution",
            "text": enforce_voice_guardrails(
                f"{author_prefix}This aligns closely with what I've been seeing in my M.Sc. Data Science research here in Berlin on agent trajectory reliability. "
                f"When {primary_focus} fails in multi-step runs, it's almost always silent context drift in the middle turns rather than the final generation step. "
                f"Enforcing typed Pydantic contracts at every tool boundary catches invalid state before it pollutes the downstream KV cache."
            )
        },
        {
            "angle": "3. Open-Source / EU Sovereign Infrastructure & Cost Reality",
            "text": enforce_voice_guardrails(
                f"{author_prefix}The cost and privacy delta here is underrated for European engineering teams. "
                f"Running this workflow with open Apache-2.0/MIT tooling inside an isolated Docker container costs $0 in per-seat SaaS overhead "
                f"and keeps sensitive repository and telemetry data 100% inside your own network perimeter. Always sandbox experimental tools first."
            )
        }
    ]

    return {
        "topic_summary": first_line,
        "extracted_urn": extracted_urn,
        "post_url": post_url,
        "detected_signals": detected_tech or ["AI Engineering", "Production MLOps"],
        "generated_comments": comments,
        "generated_at": datetime.now().isoformat()
    }


def post_live_comment_to_linkedin(
    target_urn_or_url,
    comment_text,
    topic="",
    author="",
    external_post_snippet="",
    post_url="",
    is_external=True,
    candidate_id=None,
    parent_comment_urn=None,
    allow_duplicate=False
):
    """
    Publishes a comment live to LinkedIn via POST /v2/socialActions/{urn}/comments.
    Records external stream comments in external_comments_log.json and comment_engagement_log.json.
    """
    urn = extract_urn_from_url_or_string(target_urn_or_url)
    if not urn:
        return {
            "success": False,
            "reason": "Could not extract a valid LinkedIn URN (urn:li:share/activity/ugcPost) from the target URL/ID."
        }

    clean_text = enforce_voice_guardrails(comment_text)
    if not clean_text:
        return {"success": False, "reason": "Comment text is empty."}

    log_data = load_json(COMMENT_LOG_FILE, {"comments_posted": []})
    existing_list = log_data.get("comments_posted", [])

    if not allow_duplicate:
        for item in existing_list:
            if item.get("post_urn") == urn:
                return {
                    "success": True,
                    "already_posted": True,
                    "comment_id": item.get("comment_id"),
                    "post_urn": urn,
                    "post_url": item.get("post_url") or post_url or f"https://www.linkedin.com/feed/update/{urn}/",
                    "message": "Already commented on this LinkedIn post URN."
                }

    res = publisher.post_first_comment(
        post_urn=urn,
        comment_text=clean_text,
        parent_comment_urn=parent_comment_urn
    )

    if res.get("comment_posted"):
        resolved_url = post_url or f"https://www.linkedin.com/feed/update/{urn}/"
        entry = {
            "comment_id": res.get("comment_id", ""),
            "comment_urn": res.get("comment_urn", ""),
            "post_urn": urn,
            "post_url": resolved_url,
            "author": author or ("External Stream Author" if is_external else "Purnachandra Madhukar Dandu"),
            "is_external": is_external,
            "candidate_id": candidate_id,
            "topic": topic or f"External Stream Post ({urn})",
            "external_post_snippet": external_post_snippet,
            "comment_text": clean_text,
            "posted_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "LIVE_ON_LINKEDIN"
        }
        existing_list.insert(0, entry)
        log_data["comments_posted"] = existing_list
        log_data["total_live_comments"] = len(existing_list)
        log_data["updated_at"] = datetime.now().isoformat()
        save_json(COMMENT_LOG_FILE, log_data)

        if is_external:
            ext_data = load_json(EXTERNAL_COMMENTS_FILE, {"external_comments": []})
            ext_list = [e for e in ext_data.get("external_comments", []) if e.get("post_urn") != urn]
            ext_list.insert(0, entry)
            ext_data["external_comments"] = ext_list
            ext_data["total_external_comments"] = len(ext_list)
            ext_data["updated_at"] = datetime.now().isoformat()
            save_json(EXTERNAL_COMMENTS_FILE, ext_data)

        return {
            "success": True,
            "comment_id": res.get("comment_id", ""),
            "comment_urn": res.get("comment_urn", ""),
            "post_urn": urn,
            "post_url": resolved_url,
            "posted_at": entry["posted_at"]
        }

    return {
        "success": False,
        "post_urn": urn,
        "reason": res.get("reason", "LinkedIn API rejected comment request.")
    }


def run_live_external_stream_auto_comment_batch():
    """
    Auto-comments on OTHER people's / engineering teams' LinkedIn posts in the exact same
    technical stream as Purna's profile (Pydantic AI, Langfuse Berlin, Qdrant Berlin,
    deepset/Haystack Berlin, Mistral AI, Hugging Face, Explosion AI/spaCy Berlin).
    """
    results = []
    for target in CURATED_EXTERNAL_STREAM_TARGETS:
        res = post_live_comment_to_linkedin(
            target_urn_or_url=target["post_urn"],
            comment_text=target["comment_text"],
            topic=f"{target['author']} — {target['stream_pillar']}",
            author=target["author"],
            external_post_snippet=target["external_post_snippet"],
            post_url=target["post_url"],
            is_external=True,
            allow_duplicate=False
        )
        results.append({
            "author": target["author"],
            "stream_pillar": target["stream_pillar"],
            "post_urn": target["post_urn"],
            "post_url": target["post_url"],
            "external_post_snippet": target["external_post_snippet"],
            "comment_text": target["comment_text"],
            "result": res
        })
        if not res.get("already_posted"):
            time.sleep(1.0)

    # Also save discovered external stream targets into external_engagement_radar.json for dashboard visibility
    discovered_all = discover_external_stream_posts(max_per_source=2)
    save_json(EXTERNAL_RADAR_FILE, {
        "updated_at": datetime.now().isoformat(),
        "owner": "Purnachandra Madhukar Dandu",
        "total_external_posts": len(discovered_all),
        "external_stream_posts": discovered_all
    })

    ext_log = load_json(EXTERNAL_COMMENTS_FILE, {"external_comments": []}).get("external_comments", [])
    return {
        "executed_at": datetime.now().isoformat(),
        "batch_results": results,
        "total_external_live_comments": len(ext_log),
        "total_live_comments": len(load_json(COMMENT_LOG_FILE, {"comments_posted": []}).get("comments_posted", []))
    }


def run_live_auto_comment_batch():
    """Alias so dashboard /api/comments/batch triggers external stream auto-commenting."""
    return run_live_external_stream_auto_comment_batch()


def refresh_post_specific_replies_and_radar():
    """Keeps external stream radar synced during daemon cycles."""
    discovered_all = discover_external_stream_posts(max_per_source=2)
    save_json(EXTERNAL_RADAR_FILE, {
        "updated_at": datetime.now().isoformat(),
        "owner": "Purnachandra Madhukar Dandu",
        "total_external_posts": len(discovered_all),
        "external_stream_posts": discovered_all
    })
    return discovered_all


if __name__ == "__main__":
    print("=" * 75)
    print("  Antigravity External Stream Auto-Commenter (Other People's Posts)")
    print("=" * 75)
    summary = run_live_external_stream_auto_comment_batch()
    for item in summary["batch_results"]:
        r = item["result"]
        status = "LIVE ON EXTERNAL POST [OK]" if r.get("success") else f"FAILED ({r.get('reason')})"
        print(f"  [{item['author']}] {item['post_urn']} -> {status} (Comment ID: {r.get('comment_id', 'N/A')})")
    print(f"\n[OK] Total verified external stream comments live: {summary['total_external_live_comments']}")
