---
name: nextjs-research-ui
description: Best practices for Next.js research dashboard UI, real-time SSE event consumption, Framer Motion progress animations, and dynamic markdown report rendering.
---

# Next.js Research UI Skill Guidelines

When building the frontend dashboard for the Deep Research system:

## 1. Real-time Agent Progress Feed
- Use `EventSource` (or `@microsoft/fetch-event-source` for POST SSE support) to listen to backend streams.
- Render active execution steps with Framer Motion animated timeline icons:
  - `Planner`: Spinner -> Checklist of sub-questions
  - `Search Agent`: Live list of search queries executed
  - `Reading Agent`: Favicon + domain badge stream of read pages
  - `Reflection`: Self-correction badges
  - `Writer`: Live streaming Markdown response text

## 2. Dynamic Report Viewer
- Render generated Markdown using `react-markdown` with `remark-gfm` and `rehype-highlight`.
- Custom citation component for `[1]`, `[2]`:
  - Show interactive hover card / popover with source title, snippet, and direct link.

## 3. Aesthetic Guidelines (Per Agent System Prompt)
- Dark mode theme with sleek HSL accents (indigo/violet glow for research status).
- Modern Google Font (`Inter` or `Outfit`).
- Glassmorphism panels for live agent status and plan progress cards.
- Clean export toolbar (Copy Markdown, Download PDF, Share link).
