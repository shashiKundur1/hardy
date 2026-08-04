# Hardy — buy it once

**A shop that vets what you're about to buy.**

Hardy is a storefront for durable goods with an AI agent that watches how you shop and
recommends what will actually last. It tracks what you view, search, and return to; once it has
enough signal an agent reasons over that behaviour, retrieves from a vector database, and writes
you a personal case for the one worth buying — citing who owns the brand today, whether parts
will exist in 2032, what the warranty really covers, and what the thing costs **per year of use**
rather than at the till.

Built for the **SmartReco Build Challenge 2026** (Krish Naik × Mesh API).

> Every other entrant builds an agent that persuades you to buy *more*. Hardy uses the identical
> mandated architecture — behavioural tracking, dual-write to SQL and a vector DB, agentic RAG,
> persuasive copy, every AI call through Mesh — pointed at the buyer instead of the seller.
> Same skeleton, opposite instinct.

---

## What makes a Hardy product page different

A normal product page tells you price, specs, and a star rating. A Hardy page adds four fields
nobody else surfaces:

1. **Ownership today** — family / employee-owned / charitable trust / public / conglomerate /
   private equity, with the acquisition date
2. **Trajectory** — has quality moved since the last ownership change, expressed **only as a
   cited quote**, never as Hardy's own assertion
3. **Serviceability** — repairability score, parts availability horizon, warranty terms
4. **Cost per year** — price ÷ expected service life, the honest unit of comparison

## The loop

```
browse → events batched → threshold crossed → agent wakes
      → reads behaviour → infers the real intent
      → hybrid retrieval over catalog → grades evidence
      → writes persuasive case → stores → displays
      → behaviour changes → recommendation refreshes
```

Full architecture diagram: [`HARDY.md` §8](HARDY.md#8-system-architecture).

## Architecture

```
src/
  main.py  config.py  constants.py  database.py
  auth/  catalog/  events/  recommendations/     domain modules
    router.py  schemas.py  models.py  service.py
  agent/                                          LangGraph
    graph.py  state.py  nodes.py  prompts.py  retrieval.py
  integrations/
    mesh.py          every LLM and embedding call routes through here
    vectorstore.py
  storefront/  debug/  templates/  static/
tests/
```

Domain-driven layout after [fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices),
with the agent following LangGraph's own prescribed structure.

**Every LLM/AI call goes through `src/integrations/mesh.py`.** One file to point at, and one file
that proves nothing bypasses the gateway.

## Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | Jinja2 templates + vanilla JS for tracking |
| Database | SQLite via SQLAlchemy |
| Vector DB | Qdrant |
| LLM gateway | Mesh API — chat and embeddings, `text-embedding-3-small` at 1536 dims |
| Agent | LangGraph |
| Scheduler | APScheduler |
| Tracing | LangSmith |

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your MESH_API_KEY
uvicorn src.main:app --reload
```

Verify the gateway is reachable and funded:

```bash
python -m tests.test_mesh
```

## Design

The interface follows a design system extracted from production hardware brands rather than
invented — near-black base, one high-chroma accent, expanded heavy display type.

| Document | What's in it |
|---|---|
| [`brand/BRAND.md`](brand/BRAND.md) | Brand book — colour, type, marks, spacing, voice |
| [`brand/tokens.css`](brand/tokens.css) | Design tokens. Components consume these, never raw values. |
| [`brand/cvd.py`](brand/cvd.py) | Verifies every colour pair at WCAG AA. Runnable. |
| [`HARDY.md`](HARDY.md) | The complete build document |

---

**Buy it once.**
