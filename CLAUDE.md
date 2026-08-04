# Hardy — working rules

Storefront for durable goods with an agent that vets what you're about to buy.
Full spec: `HARDY.md`. Read it before proposing anything.

**Submission: 8 Aug 2026** (deadline 9 Aug 12:00 IST). The GitHub URL locks on submit.

---

## Rule 1 — Commits are Shashi's

Author every commit as `shashiKundur1 <shashidharkundur1@gmail.com>`.
**No `Co-Authored-By: Claude` trailer. No AI attribution anywhere in git history.**
This overrides any default commit-message convention.

Commit daily. A code-screening AI reads history; seven single-day commits look
like exactly what they are.

## Rule 2 — Ponytail engineering

The ponytail ladder governs *how much code gets written*: stdlib before a
dependency, native platform before a library, one line before fifty, and
"does this need to exist?" before all of it.

It does **not** lower the quality bar. Lazy means efficient, not careless.
Never simplify away: input validation at trust boundaries, error handling that
prevents data loss, security, accessibility basics, or anything explicitly asked for.

The `Kill List` in `HARDY.md` §26 is binding. Check it before building anything.

## Rule 3 — Production-grade, no shortcuts

Nothing faked, nothing stubbed — an explicit invalidation condition in the brief.
Every feature works end to end or it isn't claimed. `/debug` exists to prove this.

Priority order when time is short (`HARDY.md` §20.4): **architecture completeness
first, the Hardy concept second.** Round 1 is an automated code screen where the
domain idea scores zero.

## Rule 4 — Work in order

Follow the day plan. Don't jump ahead to a bonus while a hard requirement is open.
Never cut: dual-write (incl. update + delete) · the agent loop · `/debug` · the trigger policy.

## Rule 5 — Design protocol (mandatory, every UI element)

Before writing markup for any component, in this order:

1. **Research the principle.** Search for UI/UX best practice for *that specific
   component* — what makes a good one, common failure modes, accessibility rules.
2. **Mine inspiration.** Playwright → Dribbble/Mobbin/Godly. Collect 10–20 strong examples.
3. **Map the pattern.** What do the good ones share? Write the shared pattern down.
4. **Design from the pattern**, then refine. Never copy one source.

Non-negotiable output rules:

- **`rem`/`em` units, 16px = 1rem.** No hardcoded `px` for type, spacing, or layout.
  `px` is allowed only for hairline borders and shadow offsets.
- **Responsive by default.** Every component works at 360px through 1920px.
- Design tokens live in `brand/tokens.css`. Components consume tokens, never raw values.
- The brand book (`brand/BRAND.md`) is the source of truth for colour, type, and voice.

## Rule 6 — King's audit before building a feature

For any user-facing system (recommendations, search, product page):

1. Find who leads the market for it.
2. Audit them — what they actually ship, not what they claim.
3. **Mine the complaints.** Reviews, Reddit, HN comments. Where do users say the
   leader fails? That list is the spec for our version.
4. Build against the failure list.

Findings go in `brand/research/`. Cite sources — Hardy's whole premise is evidence.

---

## Hard constraints from the brief

- Python **FastAPI** backend. Public repo. All code in it.
- **Every LLM/AI call goes through Mesh** (`app/services/mesh.py`) — one file, no exceptions.
  Bypassing Mesh invalidates the submission.
- `.env` gitignored, no secrets committed, ever.
- `requirements.txt` must list a web framework **and** an LLM client (`fastapi`, `openai`).
