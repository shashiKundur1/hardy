# Hardy — buy it once

**A shop that vets what you're about to buy.**

Hardy is a storefront for durable goods with an AI agent that watches how you shop
and recommends what will actually last. It tracks what you view, search, and return
to; once it has enough signal an agent reasons over that behaviour, retrieves from a
vector database, and writes you a personal case for the one worth buying — citing who
owns the brand today, whether parts will exist in 2032, what the warranty really
covers, and what the thing costs **per year of use** rather than at the till.

Built for the **SmartReco Build Challenge 2026** (Krish Naik × Mesh API).

> Every other entrant builds an agent that persuades you to buy *more*. Hardy uses the
> identical mandated architecture — behavioural tracking, dual-write to SQL and a vector
> DB, agentic RAG, persuasive copy, every AI call through Mesh — pointed at the buyer
> instead of the seller. Same skeleton, opposite instinct.

---

## Status

Day 1 of 5. Repo, CI, and brand foundation in place. Architecture in progress.

See [`HARDY.md`](HARDY.md) for the complete build document — problem evidence,
market gap analysis, architecture, data model, agent design, and rubric mapping.

## Architecture

```
browse → events batched → threshold crossed → agent wakes
      → reads behaviour → infers the real intent
      → hybrid retrieval over catalog → grades evidence
      → writes persuasive case → stores → displays
```

Full diagram: [`HARDY.md` §8](HARDY.md#8-system-architecture).

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your MESH_API_KEY
uvicorn app.main:app --reload
```

## Documentation

| Document | What's in it |
|---|---|
| [`HARDY.md`](HARDY.md) | The complete build document |
| [`brand/BRAND.md`](brand/BRAND.md) | Brand book — colour, type, voice, logo |
| [`brand/research/`](brand/research/) | Market research and competitor audits |
| [`CLAUDE.md`](CLAUDE.md) | Engineering and design rules |

---

**Buy it once.**
