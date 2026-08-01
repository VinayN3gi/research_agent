---
name: langgraph-orchestration
description: Best practices, state schemas, and multi-agent graph patterns using LangGraph for Deep Research systems.
---

# LangGraph Orchestration Skill Guidelines

When building the multi-agent orchestration for the Deep Research system using LangGraph:

## 1. Graph State Architecture
- Always use explicit `TypedDict` or `Pydantic` models to define `ResearchState`.
- Mandatory state keys:
  - `user_query`: str
  - `research_plan`: list of sub-questions with status
  - `search_queries`: list of generated search terms
  - `raw_sources`: dictionary/list of fetched web pages (url, content, title, score)
  - `verified_facts`: list of extracted claims/facts with source attribution
  - `reflection_notes`: feedback from critique agent
  - `final_report`: Markdown report with inline numeric citations `[1]`, `[2]`
  - `status_logs`: log of execution steps for UI streaming

## 2. Agent Node Design
- **Supervisor/Planner Node**: Receives the query and generates a structured research plan (3-5 targeted sub-questions).
- **Search Node**: Executes multi-provider search requests in parallel for sub-questions.
- **Scraper/Reader Node**: Fetches page content via Firecrawl / Jina Reader in parallel.
- **Extraction & Verification Node**: Extracts relevant passages and verifies claims against source text.
- **Reflection Node**: Evaluates research depth. Decides conditional routing:
  - Route back to `Search Node` if coverage is inadequate or claims lack backing (up to `max_iterations`).
  - Route to `Writer Node` when research criteria are satisfied.
- **Writer & Citation Node**: Assembles final report deterministically with mapped citations.

## 3. Streaming and Event Handling
- Emit custom event tokens (`astream_events` v2) at every graph state transition.
- Capture node execution events (`on_chain_start`, `on_tool_end`, `on_chat_model_stream`) to stream live agent thoughts to FastAPI SSE.
