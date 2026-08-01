---
name: fastapi-sse-backend
description: Best practices for FastAPI backend setup, Server-Sent Events (SSE) streaming, async task execution, and database integration for Deep Research.
---

# FastAPI SSE Backend Skill Guidelines

When building the FastAPI backend for the Deep Research system:

## 1. Async First Architecture
- Use `async def` for all API endpoint routes and service functions.
- Use `httpx.AsyncClient` or async SDKs for external API calls (Tavily, Firecrawl, OpenAI, Anthropic, Gemini).
- Use `asyncpg` with `SQLAlchemy` async sessions for PostgreSQL storage.

## 2. Server-Sent Events (SSE) Streaming Pattern
- Implement streaming using `sse_starlette.sse.EventSourceResponse` or `StreamingResponse(media_type="text/event-stream")`.
- Structure SSE data frame events cleanly:
  ```json
  {
    "event": "agent_step",
    "data": {
      "agent": "Planner",
      "status": "in_progress",
      "message": "Generating sub-queries...",
      "payload": {}
    }
  }
  ```
- Standard Event Types:
  - `connected`: Handshake event
  - `agent_plan`: Emitted when research plan is formed
  - `agent_thought`: Live LLM streaming tokens
  - `source_found`: Emitted when new high-rank source is read
  - `report_chunk`: Emitted while writing the final report
  - `completed`: Final payload with full report and citation graph
  - `error`: Formatted error message if execution fails

## 3. API Route Organization
- `/api/research/start`: POST endpoint to initiate a research job.
- `/api/research/stream/{job_id}`: GET endpoint for SSE stream.
- `/api/research/history`: GET endpoint to list previous research reports.
- `/api/research/export/{job_id}?format=pdf|md`: GET endpoint to download compiled export formats.
