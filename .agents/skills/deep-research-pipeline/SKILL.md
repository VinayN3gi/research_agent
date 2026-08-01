---
name: deep-research-pipeline
description: Best practices for search query expansion, multi-provider web search, clean markdown extraction, content scoring, and citation generation.
---

# Deep Research Pipeline Skill Guidelines

When implementing search, scraping, ranking, and citation pipelines:

## 1. Search Query Expansion & Multi-Provider Search
- **Expansion**: Translate single user prompt into 3-5 distinct, targeted search queries covering different angles (e.g. historical context, current technical state, competitive landscape, benchmarks).
- **Multi-Provider Architecture**:
  - Primary provider: Tavily API / Serper API (structured search results)
  - Secondary provider: Exa API (semantic similarity search) / Brave Search
  - Implement a fallback chain: If primary provider fails or returns < 3 results, automatically execute fallback search.

## 2. Reading & Content Extraction (Firecrawl / Jina Reader)
- **Do NOT scrape raw HTML manually**.
- Use **Firecrawl API** (`https://api.firecrawl.dev/v1/scrape`) or **Jina Reader** (`https://r.jina.ai/{url}`) to retrieve pre-cleaned Markdown.
- Clean up returned Markdown: strip excessive navigation menus, footers, advertisements, and non-informative boilerplate code blocks.
- Set a hard character cap per scraped page (e.g., ~8,000 to 12,000 characters) to preserve LLM context budget.

## 3. Content Ranking & Deduction
- Score extracted text segments by relevance to sub-questions using lightweight embedding similarity or fast LLM evaluation.
- Deduplicate overlapping pages and redundant domains.

## 4. Citation & Reference Mapping
- Assign every unique source URL a persistent index (`[1]`, `[2]`, `[3]...`).
- When writing report sections, require the LLM to tag facts with `[X]` corresponding exactly to the source index.
- Append a clean `## References` section at the bottom of generated reports with metadata:
  - Title
  - Author / Publisher
  - URL
  - Accessed Date
