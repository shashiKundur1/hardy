# King's audit — product recommendation

Who leads, what they actually ship, where users say they fail, and what we build instead.
Rule 6 of `CLAUDE.md`. Every failure below is sourced. Researched 4 Aug 2026.

---

## The three kings

| King | Crown | What it actually is |
|---|---|---|
| **Amazon** | Volume — the default recommender on earth | Collaborative filtering ("customers who bought…") tuned for basket size |
| **buyitforlife.com** | Category — owns the durability query | Affiliate content site: *"we may earn a commission"* |
| **Wirecutter** | Trust — the "what should I buy" authority | Human editorial, one pick per category, affiliate-funded |

---

## Failure list — where the kings lose users

Each row is a complaint users actually make, with the source, and the line in Hardy that answers it.

### F1 — "It recommends what I already bought"

> Users complain about receiving recommendations for items they've already purchased —
> continuing to recommend toilet seats after a customer bought one out of necessity, not desire.
> — [Codal, *Amazon's Recommendation System Is Broken*](https://medium.com/@gocodal/amazons-recommendation-system-is-broken-e1f9b5a61518)

The engine models *co-purchase*, not *intent*. It cannot tell "shopping for" from "done shopping for."

**Hardy's answer:** the agent infers a `stage` field — `browsing | comparing | deciding` —
from behaviour, and the recommendation is written for that stage. A person on their third
visit to the same three dishwashers gets a decision, not more dishwashers.
→ `HARDY.md` §12.4 intent schema.

### F2 — "33% are frustrated by irrelevant recommendations"

> Users browse a product, add it to cart, then leave — only to see irrelevant suggestions for weeks.
> — [Lucidworks, *How Amazon Can Fix Its Recommendations*](https://lucidworks.com/blog/how-amazon-can-fix-its-recommendations)

Semantic or collaborative similarity with no hard constraint drifts across categories.

**Hardy's answer:** metadata filter runs **before** semantic search, never after. You cannot
be shown a skillet while shopping for luggage, because the skillet is never in the candidate
set. Both orderings are visible on `/debug`. → `HARDY.md` §13.

### F3 — "I don't believe it's neutral"

> Over 40% of users question the neutrality of AI in product recommendations — a spreading
> disillusionment from "AI understands me" to "AI sells to me."
> — [aipogeo, *"I No Longer Trust AI's Recommendations"*](https://www.aipogeo.com/blog/i-no-longer-trust-ai-recommendations/)

The category king monetises by commission **on the products it recommends**. That is the
exact conflict the community names.

**Hardy's answer:** no affiliate links, no commission, no sponsored placement, stated on the
page and in the README. The one incentive we could have had, we don't. → `HARDY.md` §5.4.

### F4 — "I have to go verify it somewhere else"

> 86% of users who used AI for product research verified the recommendation through another
> source before buying. 42% would not trust an AI recommendation over $25 without checking.
> — [Bizrate Insights, *2026 State of Consumer Trust in AI and Online Shopping*](https://bizrateinsights.com/how-shoppers-navigate-ai-and-authenticity-state-of-consumer-trust-in-online-shopping/)

**This is the single most important number in the audit.** A recommendation that sends you
elsewhere to check it has failed at its only job.

**Hardy's answer:** the verification *is* the product. Ownership, parts horizon, warranty terms
and cost-per-year sit on the page, and every brand claim is a **verbatim cited quote with its
source** — never Hardy's assertion. The `grade_evidence` node strips any claim lacking a
citation. → `HARDY.md` §12.2.

### F5 — "Just tell me why"

> Top signals making a recommendation feel trustworthy: price comparisons (48%),
> verified customer reviews (40%), **explanation of why the AI made the recommendation (36%)**.
> — [Bizrate Insights](https://bizrateinsights.com/how-shoppers-navigate-ai-and-authenticity-state-of-consumer-trust-in-online-shopping/)

Nobody in the category shows their reasoning. Amazon shows a carousel with no rationale.

**Hardy's answer:** every recommendation **opens by naming the user's own actions back to
them** — which products, how many times, what they searched. Then it compares on cost-per-year,
a real number. And `/debug` exposes the entire reasoning chain to anyone curious.
→ `HARDY.md` §12.4 generation prompt, §19.

### F6 — The category king isn't a product

`buyitforlife.com` is an affiliate blog. `craftedwithpride.com` is **a printed book** on Shopify.
`ledger.worseonpurpose.com` is a hobby ledger behind a Vercel checkpoint. A community member
on the book:

> *"how is it? Pretty legit? Like can I do a majority of my shopping with it?
> It reminds me of the old Yellow Pages."*

**Hardy's answer:** Yellow Pages exist. Nobody built the recommender. That's the whole bet.
→ `HARDY.md` §4.4.

---

## What the audit changes about the build

Three things I would have got wrong without it:

1. **Cost-per-year must be visually equal to price, not a footnote.** F5 says price comparison
   is the #1 trust signal (48%). Our differentiated number has to carry the same weight as the
   number people already trust — same size, same position, same emphasis. Not small grey text.

2. **Every brand claim needs its source rendered next to it, not stored behind it.** F4's 86%
   means an uncited claim is worse than no claim: it sends the user to Google and they don't
   come back. `evidence_source` must be **visible on the product card**, not just a DB column.

3. **The ownership badge must not be a rage filter.** The top-voted correction in the source
   thread is that conglomerate ≠ private equity. A red "PE" badge would make Hardy exactly the
   reactionary gimmick the community itself pushes back on — and a human judge reading
   `HARDY.md` §3.4 will look for whether we honoured our own nuance.
   → Design consequence: **no red/green semantics for ownership.** See `BRAND.md`.

---

## Sources

- [Codal — Amazon's Recommendation System Is Broken](https://medium.com/@gocodal/amazons-recommendation-system-is-broken-e1f9b5a61518)
- [Lucidworks — How Amazon Can Fix Its Recommendations](https://lucidworks.com/blog/how-amazon-can-fix-its-recommendations)
- [Bizrate Insights — 2026 State of Consumer Trust in AI and Online Shopping](https://bizrateinsights.com/how-shoppers-navigate-ai-and-authenticity-state-of-consumer-trust-in-online-shopping/)
- [aipogeo — "I No Longer Trust AI's Recommendations"](https://www.aipogeo.com/blog/i-no-longer-trust-ai-recommendations/)
- [Practitioners Versus Users: A Value-Sensitive Evaluation of Industrial Recommender System Design (arXiv)](https://arxiv.org/pdf/2208.04122)
- Primary evidence on brand decay and the market gap: `HARDY.md` §3–§4
