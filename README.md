# Hardy — buy it once

**A shop that vets what you're about to buy.**

Hardy is a storefront for durable goods with an AI agent that watches how you shop and
recommends what will actually last. It tracks what you view, search, and return to; once it has
enough signal an agent reasons over that behaviour, retrieves from a vector database, and writes
you a personal case for the one worth buying — citing who owns the brand today, whether parts
will exist in 2032, what the warranty really covers, and what the thing costs **per year of use**
rather than at the till.

Built for the **SmartReco Build Challenge 2026** (Krish Naik × Mesh API).

**Running live at [hardy.shashidev.me](https://hardy.shashidev.me)** — the full stack, not a
screenshot. `GET /health` reports the database and the vector store. The agent's working is
open at [`/debug`](https://hardy.shashidev.me/debug): model calls per event recorded, the cache
hit ratio, and the reason the last trigger fired or was suppressed.

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

## The flow

```
/                 landing. What Hardy argues and why. No catalog, no tracker.
/signup → /welcome  three steps: how to read a card, categories, what you are after
/login            returns you to wherever you were headed
/shop             the storefront, behind sign-in
/category/{slug}  paged, sorted, filtered on Hardy's terms: has a source,
                  ownership continuity, expected life, cost per year
/product/{id}     the four fields nobody else surfaces
/recommendations  the agent's case, and the evidence under each pick
/footprint        every action Hardy recorded, and the control that deletes it
/profile          who you are, what you declared, what Hardy holds
/debug            the glass box: retrieval scores, node path, every AI call
/admin/login      a separate door; /admin refuses a shopper with a designed 403
/health           liveness plus vector-store reachability
```

Behavioural tracking loads on the storefront and **never on the landing page** — page
views on a marketing page are not shopping intent, and recording them poisons the signal
the agent reasons over.

## Setup

```bash
make install                  # poetry, into an in-project .venv
cp .env.example .env          # add your MESH_API_KEY and SESSION_SECRET
make seed                     # build the catalog through Mesh, idempotent
make dev                      # http://localhost:8000
```

No Poetry? `make install-pip` does the same with a plain venv.

Verify the gateway is reachable and funded:

```bash
make test-live                # the tests that need a real MESH_API_KEY
```

`make verify` is the ship gate: ruff, every offline test, and the four organiser checks.
The default test run needs no Mesh key, so a judge can run it on a fresh clone.

## Running it in containers

```bash
make docker-up                # qdrant + app + digest scheduler
make docker-seed              # seed and sync inside the container network
make docker-digest            # send one digest now
```

Four services, each with one job: `qdrant` holds the vectors, `app` serves the site,
`scheduler` is the single process that owns the daily digest, and the profile-gated
`seed` / `sync` / `digest` tasks run one-shot jobs against the same image and network.

The scheduler is a **separate service on purpose**. The web container runs multiple
workers; an in-process scheduler would fire the digest once per worker.

## Bonus features

All four of the challenge's highlighted bonuses are implemented and running:

| Bonus | Where |
|---|---|
| **Structured agent framework** | LangGraph, six nodes with conditional edges and a bounded refine loop — `src/agent/graph.py` |
| **Scheduled proactive delivery** | APScheduler cron in its own service, emailing a daily digest of the day's activity — `src/recommendations/schedule.py`, `digest.py` |
| **Observability** | LangSmith tracing over the whole graph — `src/agent/graph.py` |
| **Retrieval polish** | Metadata-filtered vector search with a durability re-rank, and the before/after of that re-rank shown on `/debug` — `src/agent/retrieval.py` |

Beyond the list, the trigger policy in `src/recommendations/triggers.py` decides when an AI
call is worth making at all: it suppresses on too-few events, a rate floor, and a profile
hash that covers the catalog version, so an unchanged profile serves cache. A scheduled
digest over unchanged behaviour costs **zero** LLM calls, and there is a test asserting it.

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
