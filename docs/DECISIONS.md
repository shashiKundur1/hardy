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

## 2026-08-04 — Still open

- [ ] Add `MESH_API_KEY` + `SUBMISSION_TOKEN` as GitHub Actions secrets (manual, Shashi)
- [ ] Confirm first CI run is green in the Actions tab
