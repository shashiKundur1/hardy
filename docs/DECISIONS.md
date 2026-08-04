# Decisions & verified facts

Append-only. Each entry is dated and says how it was verified.

---

## 2026-08-04 — Deadline corrected: **11 Aug**, not 9 Aug

`HARDY.md` states "Deadline: 9 Aug 2026, 12:00 IST — submit 8 Aug". **This is wrong.**

Verified live on the dashboard (`career.krishnaik.in/dashboard/hackathons?h=smartreco-build-challenge-2026`):

| Phase | Window |
|---|---|
| Registration | 31 Jul 12:00 IST → **7 Aug 12:00 IST** (already registered ✔) |
| Submission | 2 Aug 12:00 IST → **11 Aug 12:00 IST** |
| Results | 14 Aug 12:00 IST |

**Impact:** 7 full days from 4 Aug, not 4. Target submission **10 Aug**, one day of buffer,
because the repo URL locks permanently on submit.

## 2026-08-04 — ⚠️ BLOCKER RESOLVED: Mesh serves embeddings

`HARDY.md` §27 Q1 flagged this as the day-1 invalidation risk. **Answered: yes.**

Verified with the funded key against `https://api.meshapi.ai/v1`:

```
GET  /v1/models       → 200 · 999 models · 44 with supports_embeddings=true
POST /v1/embeddings   → 200 · openai/text-embedding-3-small · dim=1536
POST /v1/chat/completions → 200 · openai/gpt-4o
```

Section 13 (retrieval) proceeds as written. No fallback needed, no README caveat needed.
Embedding models available include `openai/*`, `cohere/embed-v4`, `baai/bge-m3`,
`amazon/titan-embed-text-v2`, `google/embeddinggemma-300m`.

**Qdrant collection must be created with `size=1536`, `distance=Cosine`.**

## 2026-08-04 — Submission form: video and social posts ARE required

The problem statement says *"A demo video and deployed URL are optional, and are reviewed
only for finalists."* The actual form contradicts it. Fields marked `*`:

| Field | Required |
|---|---|
| GitHub URL | ✔ **locks permanently on submit** |
| LinkedIn post link | ✔ |
| X (Twitter) post link | ✔ |
| Demo video (YouTube) | ✔ |
| Live / deployed URL | optional |
| Extra link | optional |
| Notes for judges | optional |

**Action:** post to LinkedIn and X early — they gate submission and cost nothing to do now.
Treat the demo video as required, not a finalist-only nicety.

## 2026-08-04 — Rules confirmed verbatim from the dashboard

- One submission per participant/team. Public GitHub repo is the submission.
- Backend **must** be Python (Flask or FastAPI). Any vector DB.
- **Every LLM/AI call through Mesh, or the submission is invalid.** Stated twice.
- No hardcoded secrets. `.env` gitignored.
- *"Faked or stubbed features (hardcoded recommendations, a vector database that is never
  queried, an LLM client that is never called) will score poorly."* — the `/debug` page
  exists to refute exactly this.
- Screening: **automated AI reads the code first**, top submissions go to human judges.

Prizes: 1st ₹20,000 · 2nd ₹10,000 · 3rd ₹5,000 · 4th–10th quarterly Projects subscription.

## 2026-08-04 — Credentials in place

`MESH_API_KEY` and `SUBMISSION_TOKEN` are set as GitHub Actions secrets. `LANGSMITH_API_KEY`
verified (`/api/v1/sessions` → 200), so the observability bonus is unblocked.
All three live in the gitignored, `chmod 600` `.env`. Nothing secret is tracked —
`git check-ignore` confirms `.env` is caught by line 2 of `.gitignore`.

First CI run failed with `token_missing` because the secrets did not exist yet. That was the
expected bootstrap failure, not a code problem.

## 2026-08-04 — ⚠️ CI has **four** critical checks, not two

`HARDY.md` §22.3 lists two critical checks (compiles, requirements). The real run shows **four**:

| Check | What it does |
|---|---|
| `compiles` | All Python files free of syntax errors |
| `requirements` | Web framework **and** LLM client present |
| **`mesh_used`** | **Greps the repo for actual Mesh API usage.** Undocumented anywhere. |
| **`mesh_key`** | **Calls the Mesh API with your key to prove it is valid and funded.** |

`mesh_used` is the one that matters: **a repo with no Mesh call in it fails a critical check**,
so CI cannot be green on scaffolding alone. It was the sole failure once the secrets landed.
Closed by writing the real `app/services/mesh.py` rather than a placeholder.

`mesh_key` confirms §22.1's warning was right — the organisers make a **live billed call** with
the key. It must stay funded through 11 Aug, not just at submission time.

A trailing `403 Result not recorded — You have not submitted your entry yet` is expected and
harmless: check results only get recorded once the dashboard form is submitted.

## 2026-08-04 — Revised day plan

`HARDY.md` §23 is built around a 2 Aug start and a 9 Aug deadline. Both are wrong. Actual
plan, anchored to the real 11 Aug deadline with 10 Aug as the target submission date:

| Day | Date | Deliverable |
|---|---|---|
| 1 | **4 Aug** | Repo, CI green, Mesh + embeddings verified, brand book, tokens, King's audit, process map |
| 2 | 5 Aug | FastAPI skeleton, auth, schema. Admin CRUD. **Dual-write incl. update + delete.** Consistency endpoint. |
| 3 | 6 Aug | Catalog seeded (~130 products). `tracker.js` + `/api/events` bulk ingest. Storefront pages, all tracked. |
| 4 | 7 Aug | Qdrant wired, hybrid retrieval, plain agent. **End-to-end loop alive.** LinkedIn + X posts published. |
| 5 | 8 Aug | LangGraph rewrite, six nodes + refine loop. LangSmith tracing. Re-rank. Trigger policy + cache. |
| 6 | 9 Aug | APScheduler digest. **`/debug` glass box.** README. Storefront polish against the brand book. |
| 7 | 10 Aug | Demo video. Final CI green. **Submit.** |
| — | 11 Aug | Buffer only. The repo URL locks on submit; do not spend this day. |

Registration closes **7 Aug 12:00 IST** — already registered, no action.

## 2026-08-04 — CI is green on checks, red on the badge, and that is expected

Run 30928964660: **4/4 critical, 3/3 advisory passed.**

```
[PASS] compiles: all 9 files compile cleanly
[PASS] requirements: web framework + LLM client present
[PASS] mesh_used: Mesh API referenced in: test_mesh.py, config.py, mesh.py
[PASS] mesh_key: Mesh API key is valid
[PASS] no committed .env file   [PASS] README found   [PASS] .gitignore ignores .env
```

The workflow still exits 1 on:

> `Result not recorded (403): You have not submitted your entry yet.`

**This cannot be fixed by code.** Results only record once the dashboard form is submitted, and
the form requires the YouTube video plus LinkedIn and X links, which do not exist yet.

**Do not submit early to clear it** — the GitHub URL locks permanently on submit. Expect a red
badge in the Actions tab until submission day and read the check lines, not the badge.
