# Enterprise Procurement Pipeline — ADK 2.0

Three runnable sample apps implement the **same procurement story** using three [ADK 2.0](https://adk.dev/2.0/) workflow styles. Each app has its own README with a flow diagram and file map.

| Agent folder | Paradigm | Details |
|--------------|----------|---------|
| [`graph_procurement_agent/`](graph_procurement_agent/) | **Graph** — `Workflow` edges, routing, parallel fan-out | [README](graph_procurement_agent/README.md) |
| [`dynamic_procurement_agent/`](dynamic_procurement_agent/) | **Dynamic** — Python orchestrator + `ctx.run_node` | [README](dynamic_procurement_agent/README.md) |
| [`collaborative_procurement_agent/`](collaborative_procurement_agent/) | **Collaborative** — coordinator + `sub_agents` | [README](collaborative_procurement_agent/README.md) |

**Conceptual guide:** [ADK_2.0.md](ADK_2.0.md)  
**Instructor timeline (optional):** [WORKSHOP_GUIDE.md](WORKSHOP_GUIDE.md)

## Which app should I run?

```mermaid
flowchart TD
  q{What do you want to explore?}
  q -->|Fixed pipeline + visible graph| graph[graph_procurement_agent]
  q -->|Branches and loops in Python| dynamic[dynamic_procurement_agent]
  q -->|Coordinator delegates to specialists| collab[collaborative_procurement_agent]
```

- **Graph:** Best starting point — see the full pipeline as `Workflow` edges in ADK Web UI.
- **Dynamic:** Same rules, but control flow lives in `orchestrator.py` (conditionals, `asyncio.gather`, `RequestInput` HITL).
- **Collaborative:** No root `Workflow` — a coordinator agent delegates to specialists.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env
```

Set `GOOGLE_API_KEY` in `.env` ([Google AI Studio](https://aistudio.google.com/)). Use `GOOGLE_GENAI_USE_VERTEXAI="FALSE"` for the Gemini API key path.

```bash
adk web .
```

Open `http://127.0.0.1:8000` and select an agent from the list.

**Console noise:** Each agent package configures quiet logging on import (default `ERROR`). Set `WORKSHOP_LOG_LEVEL=WARNING` in `.env` for more detail, or pass `--log_level` to `adk web`.

## Requirements

- Python 3.10+
- `google-adk==2.0.0`

## Project layout

```
adk-procurement-workshop/
├── graph_procurement_agent/      # Graph workflow
├── dynamic_procurement_agent/    # Dynamic orchestrator
├── collaborative_procurement_agent/
├── ADK_2.0.md
├── WORKSHOP_GUIDE.md
├── requirements.txt
└── .env.example
```

## Author

**Rohan Mitra** — Machine Learning Engineer & Researcher. Google Developer Expert — Cloud AI.

- Website: [rohanmitra.dev](https://rohanmitra.dev)
- LinkedIn: [linkedin.com/in/rohan-mitra14](https://www.linkedin.com/in/rohan-mitra14/)
