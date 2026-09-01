# portfolio-agent

The conversational AI agent running live on **[amayas.dev](https://amayas.dev)** — the widget in the bottom-right corner. Ask it anything about my work; it answers from a curated knowledge base and can pull my GitHub repositories in real time.

> Built by Amayas Mahmoudi, Data Engineer & Agentic AI.

## What it is

A production LLM agent, not a scripted chatbot. It runs on Google Cloud Run, scales to zero when nobody is talking to it, and falls back gracefully when quotas or the network fail.

## Stack

| Layer | Tech |
|---|---|
| Agent | Google ADK (Python) |
| Model | Gemini, with a model cascade on quota exhaustion |
| API | FastAPI (CORS restricted, rate limiting, Pydantic validation) |
| Hosting | Cloud Run (scale-to-zero, max 1 instance) |
| Secrets | Secret Manager |
| Analytics | BigQuery (partitioned, 90-day retention, no IP logged) |
| Tools | Live GitHub repositories fetch |

## Resilience (3 levels)

1. Primary Gemini model
2. Model cascade — falls to the next model on quota/`429`/`503`
3. Scripted fallback in the widget if the API is unreachable

## Design notes

- **The system prompt is public by design.** The agent's safety relies on containing no sensitive information, not on secrecy. Guardrails are tested against prompt injection and jailbreak attempts — feel free to try.
- **Privacy-first analytics.** Conversations are logged to BigQuery to improve the agent, without IP addresses and with automatic 90-day expiration.

## Status

Live in production. A full architecture write-up (diagram, design decisions, known limitations) is coming soon.

## License

MIT