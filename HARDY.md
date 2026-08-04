# Hardy — Buy It Once

**A shop that vets what you're about to buy.**

Complete build document · Written 2 Aug 2026
Target: SmartReco Build Challenge 2026 (Krish Naik × Mesh API)
Deadline: **9 Aug 2026, 12:00 IST** — submit 8 Aug

---

# Table of Contents

1. [The One-Pager](#1-the-one-pager)
2. [The Name](#2-the-name)
3. [The Problem — With Evidence](#3-the-problem--with-evidence)
4. [The Market Gap — Verified](#4-the-market-gap--verified)
5. [What Hardy Is](#5-what-hardy-is)
6. [The Catalog](#6-the-catalog)
7. [User Journeys](#7-user-journeys)
8. [System Architecture](#8-system-architecture)
9. [Data Model](#9-data-model)
10. [Behavioural Tracking](#10-behavioural-tracking)
11. [Dual-Write](#11-dual-write)
12. [The Agent](#12-the-agent)
13. [Retrieval](#13-retrieval)
14. [Trigger & Caching Policy](#14-trigger--caching-policy)
15. [Scheduled Digest](#15-scheduled-digest)
16. [Observability](#16-observability)
17. [Mesh API Integration](#17-mesh-api-integration)
18. [Pages & UI](#18-pages--ui)
19. [The Glass Box](#19-the-glass-box)
20. [Rubric Mapping](#20-rubric-mapping)
21. [Repo Structure](#21-repo-structure)
22. [CI & Submission Setup](#22-ci--submission-setup)
23. [Seven-Day Plan](#23-seven-day-plan)
24. [Submission Checklist](#24-submission-checklist)
25. [Risks & Mitigations](#25-risks--mitigations)
26. [Kill List](#26-kill-list)
27. [Open Questions](#27-open-questions)

---

# 1. The One-Pager

**Hardy is a storefront for durable goods with an AI agent that watches how you shop and recommends what will actually last.**

You browse it like any store. It quietly tracks what you view, search, and keep returning to. Once it has enough signal, an agent reasons over that behaviour, retrieves the most relevant products from a vector database, and writes you a personal, persuasive case for the one worth buying — citing who owns the brand today, whether parts will exist in 2032, what the warranty really covers, and what the thing costs **per year of use** rather than at the till.

**One word for what it does:** *vets*.

**Tagline:** *Hardy — buy it once.*

**The strategic bet:** every other entrant will build a course marketplace whose agent persuades you to buy **more**. Hardy uses the identical mandated architecture — behavioural event tracking, dual-write to SQL and a vector DB, agentic RAG, persuasive generated copy, every AI call through Mesh — pointed in the opposite direction. Same skeleton, opposite instinct.

**Critically:** the recommendation always ends in *buy this one*. Hardy redirects you to the better purchase. It never discourages purchase, because the brief requires persuasion that "motivates action."

---

# 2. The Name

**Hardy** — the English word for something built to endure. Hardy plants survive the winter; hardy gear survives the trip.

- Two syllables, warm, ends on the same friendly `-y` as the previous brands **Brolly** and **Bookie**
- Nobody has to ask how to spell it
- Sounds like a person you'd trust, which is precisely the product's job

**Alternates considered:** *Keeper* (from "it's a keeper"), *Trusty*, *Patina* (the beauty an object earns through years of use).

**Voice:** plain, unhurried, specific. Hardy sounds like a knowledgeable friend in a hardware shop — never breathless, never salesy, never moralising about consumption. It gives you the number and the reason, then points at one thing.

---

# 3. The Problem — With Evidence

All evidence below was gathered live on 2 Aug 2026 via HN Algolia, Reddit (old.reddit.com), and live Google SERPs.

## 3.1 People cannot find out what lasts

**r/BuyItForLife, top posts of the last month:**

- *"When will the enshittification end?"*
- *"Are there any good brands left not owned by private equity?!"*
- *"Before you shop at an outlet, know which of these 40 brands make cheaper, lower-quality goods for their factory stores"*
- *"We lost another good company. Rainbow Sandals"*
- *"My T-shirts keep dying. Testing 4 shirts (€20–€150) to find out whether expensive tees really last longer"* — **weeks 2 and 4 both reached top-of-month.** A person is running a multi-week longitudinal durability experiment by hand because the dataset does not exist.
- *"Reddit's quiet launch of Redditor Highlights, and astroturfing on BuyItForLife"* — even the last trusted source is being gamed.

## 3.2 The economics have a name

Hacker News, *"Quality of recent gens of Dell/Lenovo laptops worse than 10 years ago?"* (113 pts, 208 comments). Top comment:

> *"The market is splintered into high-end work laptops, low-end work laptops, gaming laptops. Only Apple has the brand value to be in the first set. Everyone else is in **a market for lemons**."*

A market for lemons is the textbook condition where information asymmetry destroys quality — and where a trustworthy information intermediary creates real value.

Related, same window: *"The emergence of print-on-demand Amazon paperback books"* (252 pts, 191 comments), full of readers describing Amazon-printed books they initially mistook for counterfeits.

## 3.3 Brand decay is real, and invisible at the point of sale

From a single r/BuyItForLife thread, structured brand-trajectory records extracted in one scrape:

| Brand | Status |
|---|---|
| Stihl | Family-owned; parts still stocked for West-German-era saws; warranty described as iron-clad |
| Lego | 75% owned by founder's family |
| Bosch | 94% owned by a charitable trust |
| Zeiss, Rolex | Charitable trusts |
| Lodge | Founder's descendants, 130+ years |
| Taylor Guitars, King Arthur Flour, Tillamook | Employee-owned |
| Birkenstock | Bought out 2021 — *"brace yourselves"* |
| Singer / Viking / Pfaff | PE umbrella, second owner — *"stay away from Singer"* |
| Tilley | Two owners post-founder; advertises Canadian, ships China-made |
| Bellroy | Recently PE |
| Tumi | Gutted by Samsonite, as Hartmann was before it |
| Patagonia | *"T-shirts are paper thin now"* since new CEO |
| Bernina | Production moved Switzerland → Thailand |
| Barbour | Family-owned, but production offshored |

**None of this is visible on a product page anywhere.**

## 3.4 The nuance that keeps us honest

The top-voted correction in that same thread:

> *"This sub does not know the difference between private equity and larger conglomerates. Just because something is owned by a larger corporation does not mean it is trash… They are hugely different business models."*

Therefore Hardy's ownership taxonomy is **graded, not a rage filter**. This single design decision separates a thoughtful product from a "PE bad" gimmick, and a human judge will notice it.

---

# 4. The Market Gap — Verified

Not assumed. Checked.

## 4.1 Hacker News has no coverage

| Query | Results |
|---|---|
| `product durability database` | **zero** |
| `private equity ruins brands` | **zero** |
| `repairability score` | 555 pts, 520 pts, 93 pts |

Loud demand, no supply.

## 4.2 The SERP is blogs

Live Google, *"how to find products that last a long time"*:

```
mentalfloss.com   :: This Website Can Help You Find Products That Will Last
reddit.com        :: how do you find a product that actually lasts online?
buymeonce.co.uk   :: How We Find the Most Durable "Buy-It-For-Life" Products
longtimelabel.com :: Directory of durable, solid and repairable products
quora.com         :: Where can you buy quality products that last...
reuters.com       :: Where to find products that last a lifetime
wisebread.com     :: How To Buy Stuff That Lasts Forever
```

**Not one working search or recommendation product on page one.** Blogs and unanswered forum questions on page one is the signature of demand with no supply.

## 4.3 All the instrumentation points at the seller

Live Google, *"how to know if a brand quality declined after private equity acquisition"*:

```
linkedin.com          :: Private Equity Has a Brand Perception Problem
collateral.com        :: Brand Perception After Acquisition: Why PE-Backed...
reddit.com            :: How to identify quality loss of previously trusted brands?
michaeltimmonsgg.com  :: Why Brands Go Stale After Private Equity Acquisitions
shiftmedia.co         :: Brand Due Diligence: What Private Equity Gets Wrong
rno1.global           :: Brand Due Diligence Assessment: What PE Firms Miss
strat7.com            :: Investor brand awareness: powerful AI tracking in 4 weeks
```

Page one is **entirely tooling sold to private equity firms**. The single consumer-side result is a Reddit thread asking the question. Buyers get a forum post; sellers get a product suite.

## 4.4 The incumbents prove the gap

| Site | What it actually is |
|---|---|
| `buyitforlife.com` | Affiliate content site — *"we may earn a commission"* |
| `craftedwithpride.com` | A **printed book**, 3rd edition, on Shopify |
| `ledger.worseonpurpose.com` | Hobby brand ledger behind a Vercel checkpoint |
| Klarna × Reddit | Published a *list* |

The category leader monetises by commission **on the products it recommends** — exactly the conflict of interest the community distrusts. Everything else is a static list.

A community member on `craftedwithpride`:

> *"how is it? Pretty legit? Like can I do a majority of my shopping with it? It reminds me of the old Yellow Pages."*

Yellow Pages exist. **Nobody has built the recommender.**

---

# 5. What Hardy Is

## 5.1 The core loop

```
browse → events batched → threshold crossed → agent wakes
      → reads behaviour → infers the real intent
      → hybrid retrieval over catalog → grades evidence
      → writes persuasive case → stores → displays
      → behaviour changes → recommendation refreshes
```

## 5.2 What makes a Hardy product page different

A normal product page tells you price, specs, and star rating. A Hardy page adds four fields nobody else surfaces:

1. **Ownership today** — family / employee-owned / charitable trust / public company / conglomerate / private equity, with the acquisition date
2. **Trajectory** — has quality moved since the last ownership change, expressed **only as a cited quote**, never as Hardy's own assertion
3. **Serviceability** — repairability score, parts availability horizon, warranty terms
4. **Cost per year** — price ÷ expected service life, the honest unit of comparison

## 5.3 What a recommendation looks like

> **You're a week into the dishwasher decision.**
>
> You've opened dishwashers on three separate days, spent longest on the spec tables, and searched "lifetime warranty" on Tuesday. You keep returning to the Bosch.
>
> Worth knowing before you decide: Bosch is 94% owned by a charitable trust, which is a large part of why the build reputation is real. Owners report the *small* appliances have slipped in recent years, but for a dishwasher the trust-ownership signal still holds.
>
> If you want the twenty-year machine rather than the ten-year one, the Miele is ₹34,000 more up front and roughly **₹1,100 a year cheaper** across its service life. Both beat the third one you looked at, which has no committed parts availability after 2029.
>
> **Buy the Miele** if you'll stay in this house a decade. **Buy the Bosch** if you won't.

Persuasive, specific, grounded in the catalog, and it names the user's own actions back to them. It ends in a purchase instruction.

## 5.4 What Hardy is not

- Not an affiliate site. No commissions, no sponsored placement.
- Not anti-consumption. It never says "don't buy." It says "buy this one instead."
- Not a review site. It surfaces ownership, serviceability, and cost-per-year — not star ratings.
- Not a price comparison engine.

---

# 6. The Catalog

## 6.1 Scope

**~130 products across 8 categories.** Enough to make retrieval meaningful, small enough to seed in a day.

| Category | Example products |
|---|---|
| Cookware | Cast iron skillets, stainless pans, Dutch ovens, kettles |
| Hand & power tools | Drills, saws, wrenches, multi-tools |
| Kitchen appliances | Dishwashers, mixers, blenders, food processors |
| Boots & footwear | Work boots, walking boots, resoleable shoes |
| Bags & luggage | Backpacks, suitcases, messenger bags |
| Outdoor gear | Tents, stoves, coolers, torches |
| Laptops & electronics | Laptops, keyboards, headphones, monitors |
| Home basics | Vacuums, fans, irons, sewing machines |

## 6.2 Product fields

| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `title` | str | "Lodge 12in Cast Iron Skillet" |
| `brand` | str | |
| `description` | text | Rich prose — this is what gets embedded |
| `category` | str | One of the eight |
| `price` | decimal | Required by the rules |
| `currency` | str | INR — single market only |
| `expected_life_years` | int | Drives cost-per-year |
| `cost_per_year` | computed | `price / expected_life_years` |
| `ownership_type` | enum | `family` / `employee` / `trust` / `public` / `conglomerate` / `private_equity` / `unknown` |
| `ownership_since` | date? | Last ownership change |
| `ownership_note` | text? | **A cited quote only.** Never Hardy's assertion. |
| `evidence_source` | str? | Where the quote came from |
| `repairability_score` | float? | 0–10, iFixit scale |
| `parts_until` | int? | Year parts are committed |
| `warranty` | str | "Lifetime", "10 years", "2 years" |
| `image_url` | str | |
| `created_at` / `updated_at` | ts | |

## 6.3 Seeding strategy — deliberately cheap

**The rubric rewards recommendations grounded in *your* catalog. It does not ask where the catalog came from, and no judge can verify our brand research.** So we do not build a scraping pipeline.

1. **Download the iFixit repairability CSV once** — real device names and real 0–10 scores for the laptops/electronics category. One download, real grounding, zero infrastructure.
2. **LLM-generate the remaining ~110 products** in a single seed script, through Mesh, using real brand names and realistic specs. Run once, commit the resulting `seed_products.json`, and load it deterministically thereafter.
3. **Ownership notes** — hand-write ~30 for the brands we know are interesting (Stihl, Lodge, Lego, Bosch, Birkenstock, Singer, Patagonia, Tilley, Tumi, Bernina, Barbour). Leave the rest `unknown`. `unknown` is honest and displays fine.

Budget: **half a day**, not three.

---

# 7. User Journeys

## 7.1 The shopper (primary)

1. Signs up with email/password
2. Lands on the storefront — categories, featured durable picks
3. Browses. Opens a product. Reads the spec table. Goes back. Searches "lifetime warranty." Opens two more.
4. After ~12 meaningful events, the agent fires
5. A recommendation card appears on the home page and at `/recommendations`, naming what they did and pointing at one product
6. They keep browsing; interests shift to camping gear; the recommendation refreshes
7. Next morning they receive a digest email recapping yesterday's research

## 7.2 The admin

1. Logs in, sees `/admin`
2. Adds a product — it lands in SQLite **and** Qdrant in the same request
3. Edits the price — the vector payload updates
4. Deletes a product — the vector is removed
5. Hits "Check consistency" — sees SQL count, vector count, and any drift

## 7.3 The judge (explicitly designed for)

1. Opens the repo, reads the README, sees the architecture and the bonus list
2. Runs it, or watches the 3-minute video
3. Opens `/debug` and watches events land, the profile compute, retrieval scores appear, the LangGraph path light up, and the LLM call counter *not* increment on every click

---

# 8. System Architecture

```
┌──────────────────────────────────────────────────────────┐
│  BROWSER                                                 │
│  Jinja2 templates + vanilla JS                           │
│  tracker.js → queue → batch → navigator.sendBeacon       │
└───────────────┬──────────────────────────────────────────┘
                │ POST /api/events (batched, fire-and-forget)
┌───────────────▼──────────────────────────────────────────┐
│  FastAPI                                                 │
│  ├── auth (session cookie, passlib bcrypt)               │
│  ├── storefront routes                                   │
│  ├── admin CRUD ──────► DUAL-WRITE ──┬──► SQLite         │
│  ├── /api/events → buffer → bulk insert └──► Qdrant      │
│  ├── /recommendations                                    │
│  └── /debug  ◄── the glass box                           │
└───────┬──────────────────────────┬───────────────────────┘
        │                          │
┌───────▼─────────┐      ┌─────────▼──────────┐
│  TRIGGER ENGINE │      │  APScheduler       │
│  count / shift  │      │  daily 08:00 IST   │
│  / scheduled    │      │  digest email      │
└───────┬─────────┘      └─────────┬──────────┘
        │                          │
┌───────▼──────────────────────────▼───────────────────────┐
│  LANGGRAPH AGENT                                         │
│  profile → retrieve → grade → refine? → generate         │
│      │                                                   │
│      ├──► Qdrant (hybrid: metadata filter + semantic)    │
│      └──► Mesh API  (embeddings + chat, ALL AI calls)     │
│                                                          │
│  traced end-to-end by LangSmith                          │
└──────────────────────────────────────────────────────────┘
```

---

# 9. Data Model

```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'user',   -- 'user' | 'admin'
    created_at    TIMESTAMP NOT NULL
);

CREATE TABLE products (
    id                  INTEGER PRIMARY KEY,
    title               TEXT NOT NULL,
    brand               TEXT NOT NULL,
    description         TEXT NOT NULL,
    category            TEXT NOT NULL,
    price               DECIMAL(10,2) NOT NULL,
    currency            TEXT NOT NULL DEFAULT 'INR',
    expected_life_years INTEGER NOT NULL,
    ownership_type      TEXT NOT NULL DEFAULT 'unknown',
    ownership_since     DATE,
    ownership_note      TEXT,      -- cited quote ONLY
    evidence_source     TEXT,
    repairability_score REAL,
    parts_until         INTEGER,
    warranty            TEXT,
    image_url           TEXT,
    vector_synced_at    TIMESTAMP, -- dual-write proof
    created_at          TIMESTAMP NOT NULL,
    updated_at          TIMESTAMP NOT NULL
);
CREATE INDEX idx_products_category ON products(category);

CREATE TABLE events (
    id         INTEGER PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    type       TEXT NOT NULL,   -- page_view|product_view|search|click|dwell
    product_id INTEGER REFERENCES products(id),
    category   TEXT,
    query      TEXT,
    dwell_ms   INTEGER,
    metadata   TEXT,            -- JSON
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX idx_events_user_time ON events(user_id, created_at DESC);

CREATE TABLE recommendations (
    id              INTEGER PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    narrative       TEXT NOT NULL,      -- the persuasive copy
    product_ids     TEXT NOT NULL,      -- JSON array
    interest_profile TEXT NOT NULL,     -- JSON, what the agent inferred
    trigger_reason  TEXT NOT NULL,      -- 'event_threshold'|'interest_shift'|'scheduled'
    profile_hash    TEXT NOT NULL,      -- cache key
    events_covered  INTEGER NOT NULL,
    model_used      TEXT NOT NULL,      -- Mesh model id
    tokens_used     INTEGER,
    latency_ms      INTEGER,
    is_active       BOOLEAN DEFAULT 1,
    created_at      TIMESTAMP NOT NULL
);
CREATE INDEX idx_recs_user ON recommendations(user_id, created_at DESC);
```

**Qdrant collection `products`:**
- Vector: embedding of `title + brand + description + category + warranty`
- Payload: `product_id`, `category`, `price`, `cost_per_year`, `ownership_type`, `repairability_score`, `expected_life_years`, `brand`
- Payload fields are what make **metadata filtering** (a starred bonus) possible

---

# 10. Behavioural Tracking

Explicitly called "a core focus" and judged on not slowing the frontend.

## 10.1 Client (`static/tracker.js`)

```js
// ponytail: queue + beacon. No dependency, no framework.
const q = [];
let flushTimer = null;

function track(type, payload = {}) {
  q.push({ type, ...payload, ts: Date.now() });
  if (q.length >= 20) return flush();          // size trigger
  if (!flushTimer) flushTimer = setTimeout(flush, 5000);  // time trigger
}

function flush() {
  if (!q.length) return;
  const batch = q.splice(0, q.length);
  clearTimeout(flushTimer); flushTimer = null;
  // sendBeacon never blocks and survives page unload
  navigator.sendBeacon('/api/events', new Blob(
    [JSON.stringify({ events: batch })], { type: 'application/json' }
  ));
}

// flush on the way out — this is why beacon matters
addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') flush();
});

// dwell: one event on leave, not a timer storm
let enter = Date.now();
addEventListener('beforeunload', () => {
  track('dwell', { dwell_ms: Date.now() - enter, path: location.pathname });
});

// search input throttled to one event per 800ms of quiet
let sT;
searchInput?.addEventListener('input', e => {
  clearTimeout(sT);
  sT = setTimeout(() => track('search', { query: e.target.value }), 800);
});
```

**Design choices that map to the rubric:**

| Requirement | Implementation |
|---|---|
| Non-blocking | `navigator.sendBeacon` — never blocks the UI thread, survives unload |
| Batched | Flush at 20 events or 5 seconds, whichever first |
| Throttled | Search debounced 800ms; dwell emitted once per page, not per tick |
| Rich signals | page_view, product_view, search, click, dwell, category |

## 10.2 Server

```python
@app.post("/api/events", status_code=202)
async def ingest(batch: EventBatch, bg: BackgroundTasks, user=Depends(current_user)):
    # 202 immediately; the write happens after the response is sent
    bg.add_task(bulk_insert_events, user.id, batch.events)
    bg.add_task(maybe_trigger_agent, user.id)
    return {"accepted": len(batch.events)}
```

Returns `202 Accepted` before touching the database. Bulk insert, single transaction.

---

# 11. Dual-Write

**This is where most entrants will lose points** — everyone implements create; many forget update and delete.

```python
class ProductService:
    """Every mutation touches SQL and Qdrant, or neither."""

    async def create(self, data: ProductIn) -> Product:
        product = await self.db.insert(data)
        await self._upsert_vector(product)
        product.vector_synced_at = utcnow()
        await self.db.update(product)
        return product

    async def update(self, pid: int, data: ProductIn) -> Product:
        product = await self.db.update(pid, data)
        await self._upsert_vector(product)          # re-embed, payload refresh
        product.vector_synced_at = utcnow()
        await self.db.update(product)
        return product

    async def delete(self, pid: int) -> None:
        await self.db.delete(pid)
        await self.qdrant.delete(collection="products", points_selector=[pid])

    async def _upsert_vector(self, p: Product):
        text = f"{p.title} by {p.brand}. {p.description} Category: {p.category}. Warranty: {p.warranty}."
        vec = await mesh_embed(text)                # through Mesh
        await self.qdrant.upsert(
            collection="products",
            points=[{"id": p.id, "vector": vec, "payload": {
                "product_id": p.id, "category": p.category, "brand": p.brand,
                "price": float(p.price), "cost_per_year": p.cost_per_year,
                "ownership_type": p.ownership_type,
                "repairability_score": p.repairability_score,
                "expected_life_years": p.expected_life_years,
            }}],
        )
```

## 11.1 Consistency endpoint — proof for the judge

```python
@app.get("/api/admin/consistency")
async def consistency():
    sql_ids    = set(await db.all_product_ids())
    vector_ids = set(await qdrant.all_point_ids("products"))
    return {
        "sql_count": len(sql_ids),
        "vector_count": len(vector_ids),
        "in_sql_only": sorted(sql_ids - vector_ids),
        "in_vector_only": sorted(vector_ids - sql_ids),
        "in_sync": sql_ids == vector_ids,
    }
```

Surfaced as a button on `/admin` and a live panel on `/debug`. It turns "kept in sync" from a claim into something a judge can click.

---

# 12. The Agent

⭐ Starred bonus: *"build the agent as an explicit reasoning workflow — nodes that analyze the query/activity, decide when to retrieve, evaluate retrieval quality, refine, and generate."*

## 12.1 Graph

```
        ┌──────────────────┐
        │  load_behaviour  │  recent events → structured summary
        └────────┬─────────┘
                 ▼
        ┌──────────────────┐
        │  infer_intent    │  LLM: what is this person solving?
        └────────┬─────────┘     → {categories, budget, priorities, stage}
                 ▼
        ┌──────────────────┐
        │  should_retrieve │  conditional edge
        └────┬────────┬────┘
      enough │        │ too thin
             ▼        └────────► END (no recommendation, no LLM spend)
        ┌──────────────────┐
        │     retrieve     │  hybrid: metadata filter → semantic → re-rank
        └────────┬─────────┘
                 ▼
        ┌──────────────────┐
        │  grade_evidence  │  is each candidate actually supported?
        └────┬────────┬────┘
     good    │        │  weak  ──► refine_query ──┐
             │        └───────────────────────────┘  (max 2 loops)
             ▼
        ┌──────────────────┐
        │     generate     │  persuasive narrative, cites user's own actions
        └────────┬─────────┘
                 ▼
        ┌──────────────────┐
        │      store       │  persist + deactivate previous
        └──────────────────┘
```

## 12.2 Why `grade_evidence` genuinely matters here

It is not decoration. Hardy makes claims about brands. The grading node enforces one rule:

> **The model may only quote `ownership_note` verbatim from the catalog. It may never assert on its own that a brand declined.**

If a retrieved product has no cited evidence, the node strips the claim rather than letting the model improvise. This is simultaneously a bonus feature, a legal safeguard, and an anti-hallucination measure — which is exactly the kind of alignment between requirement and reason that reads well to a judge.

## 12.3 State

```python
class AgentState(TypedDict):
    user_id: int
    events: list[dict]
    behaviour_summary: str
    intent: dict            # categories, budget_hint, priorities, stage
    query: str
    candidates: list[dict]
    evidence_ok: bool
    refine_count: int
    narrative: str
    product_ids: list[int]
```

## 12.4 Prompts

**Intent inference:**

```
You are analysing one shopper's browsing behaviour on a store that sells
durable goods.

Recent activity:
{behaviour_summary}

Infer what this person is actually trying to solve. Return JSON:
{
  "categories":  [...],          // what they're shopping for
  "budget_hint": "low|mid|high|unknown",
  "priorities":  [...],          // e.g. "repairability", "warranty", "longevity"
  "stage":       "browsing|comparing|deciding",
  "evidence":    "..."           // the specific actions that led you here
}

Base every field on actions actually present above. Do not speculate about
who they are — only about what they are shopping for.
```

**Generation:**

```
Write a personal recommendation for this shopper.

What they did:      {behaviour_summary}
What they want:     {intent}
Catalog candidates: {candidates_with_full_fields}

Rules:
- Open by naming what they actually did. Be specific: which products,
  how many times, what they searched.
- Compare on COST PER YEAR OF USE, not sticker price. Always show the number.
- You may mention brand ownership ONLY by quoting the `ownership_note`
  field verbatim. Never assert on your own that a brand's quality declined.
  If ownership_note is empty, say nothing about that brand's ownership.
- Recommend products ONLY from the candidates given. Never invent one.
- End with a clear instruction to buy a specific product. You may present a
  conditional ("buy X if..., buy Y if...") but you must always point at
  something to buy. Never tell them not to buy.
- Warm, plain, unhurried. A knowledgeable friend in a hardware shop.
  No exclamation marks, no hype, no lecturing about consumption.
- 120–180 words.
```

---

# 13. Retrieval

⭐ Starred bonus: *"smarter retrieval — re-ranking, metadata filtering, better chunking."*

**Hybrid, in three stages. Metadata filter first — this is mandatory, not optional.** Semantic-only search will confidently recommend a cast-iron skillet to someone shopping for luggage.

```python
async def retrieve(intent: dict, k: int = 5) -> list[dict]:
    # 1. HARD FILTER — narrow to the right universe first
    flt = Filter(must=[
        FieldCondition(key="category", match=MatchAny(any=intent["categories"]))
    ])
    if intent["budget_hint"] == "low":
        flt.must.append(FieldCondition(key="price", range=Range(lte=5000)))

    # 2. SEMANTIC — within that universe
    qvec = await mesh_embed(intent_to_query(intent))
    hits = await qdrant.search(
        collection="products", query_vector=qvec,
        query_filter=flt, limit=k * 4, with_payload=True,
    )

    # 3. RE-RANK — durability-weighted, not similarity alone
    def score(h):
        s = h.score                                          # semantic
        if h.payload.get("repairability_score"):
            s += 0.05 * h.payload["repairability_score"] / 10
        s += 0.10 * min(h.payload.get("expected_life_years", 0) / 25, 1.0)
        if "repairability" in intent["priorities"]:
            s += 0.05 * (h.payload.get("repairability_score") or 0) / 10
        return s

    return sorted(hits, key=score, reverse=True)[:k]
```

Both the pre-rank and post-rank orderings are shown on `/debug`, so the re-ranking is visibly doing something.

---

# 14. Trigger & Caching Policy

**This is an explicitly judged axis** — *"be smart about when and how often you call the AI — don't fire an LLM call on every single user action."* Almost nobody will design it deliberately. Write it down before coding it.

## 14.1 The policy

The agent fires when **any one** of these holds:

| Trigger | Condition |
|---|---|
| `event_threshold` | ≥ 12 meaningful events since the last recommendation |
| `interest_shift` | The top category in the last 10 events differs from the profile's top category |
| `scheduled` | The 08:00 IST daily digest |
| `manual` | Admin-only button on `/debug`, for the demo |

And it is **suppressed** when:

- Fewer than 5 events exist for this user (nothing to reason about)
- A recommendation was generated in the last 10 minutes (rate floor)
- `profile_hash` matches the active recommendation's hash — **the cache hit**

## 14.2 The cache key

```python
def profile_hash(user_id: int, events: list) -> str:
    cats  = sorted({e.category for e in events if e.category})
    prods = sorted({e.product_id for e in events if e.product_id})
    qs    = sorted({e.query for e in events if e.query})
    return sha256(f"{user_id}|{cats}|{prods}|{qs}|{CATALOG_VERSION}".encode()).hexdigest()[:16]
```

Same interests + same catalog = serve the stored recommendation, zero LLM calls. `CATALOG_VERSION` bumps on any product mutation, so catalog edits correctly invalidate.

## 14.3 Make it visible

`/debug` shows, live: total events, LLM calls made, **cache hit ratio**, and the reason the last trigger fired or was suppressed. A judge can watch you click twenty times and see the counter stay flat. That is worth more than a paragraph in the README — and we do both.

---

# 15. Scheduled Digest

⭐ Starred bonus: *"a real background scheduler (Celery Beat / APScheduler / cron) — not a manual button."*

**APScheduler** over Celery — no broker, one process, same credit.

```python
scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")

@scheduler.scheduled_job("cron", hour=8, minute=0, id="daily_digest")
async def daily_digest():
    for user in await db.users_active_since(hours=24):
        events = await db.events_for(user.id, since_hours=24)
        if len(events) < 5:
            continue                       # nothing worth writing about
        rec = await agent.run(user.id, trigger="scheduled")
        await send_email(user.email, subject="What you were researching yesterday",
                         html=render("email/digest.html", rec=rec, user=user))

scheduler.start()
```

**Delivery:** SMTP via `aiosmtplib`, or Resend. Telegram bot as the fallback if SMTP fights us.

**Subject line matters** — *"What you were researching yesterday"* beats *"Your recommendations."* The digest recaps the day's actual behaviour, which is the point.

---

# 16. Observability

⭐ Starred bonus. Near-zero effort with LangGraph.

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=ls__...
LANGSMITH_PROJECT=hardy
```

LangGraph auto-instruments. Every node, every Mesh call, every token, every latency — traced end to end. Add the project screenshot to the README.

Alongside it, structured logging on every agent run: `trigger_reason`, `profile_hash`, `cache_hit`, `nodes_visited`, `refine_count`, `model`, `tokens`, `latency_ms`. Those same fields render on `/debug`.

---

# 17. Mesh API Integration

**Mandatory. Every LLM/AI call must go through Mesh, or the submission is invalid.**

```python
from openai import AsyncOpenAI

mesh = AsyncOpenAI(
    base_url="https://api.meshapi.ai/v1",
    api_key=os.environ["MESH_API_KEY"],       # rsk_...
)

async def mesh_chat(messages, model="openai/gpt-4o", **kw):
    r = await mesh.chat.completions.create(model=model, messages=messages, **kw)
    return r.choices[0].message.content, r.usage

async def mesh_embed(text: str, model="openai/text-embedding-3-small"):
    r = await mesh.embeddings.create(model=model, input=text)
    return r.data[0].embedding
```

**Facts:** base URL `https://api.meshapi.ai/v1`; key prefix `rsk_`; model IDs are `provider/model`; `/v1/models` lists them (401 without a key); OpenAI-SDK compatible; pay-as-you-go, 0% markup, no minimum spend; UPI/cards accepted.

## ⚠️ Day-1 blocker

**Confirm `/v1/embeddings` works on Mesh before writing any retrieval code.** Marketing materials say embeddings are supported; the quickstart only documents chat. If embeddings are unavailable through Mesh, embedding locally or via OpenAI direct is arguably a rule violation — and the penalty is *invalid submission*, not lost points. If it turns out unsupported, document the fallback prominently in the README and in the judges' notes.

Also: **fund the key.** Their CI `checks.py` receives `MESH_API_KEY` in its environment, so assume live verification rather than a grep.

---

# 18. Pages & UI

| Route | Purpose |
|---|---|
| `/` | Storefront — categories, featured durable picks, active recommendation card |
| `/login`, `/signup` | Email/password |
| `/category/{slug}` | Category listing with filters |
| `/product/{id}` | Product page with the four Hardy fields + cost-per-year |
| `/search?q=` | Search results (tracked) |
| `/recommendations` | Recommendation history, current one highlighted |
| `/admin` | Product CRUD + consistency check (admin only) |
| `/debug` | **The glass box** |

**Design:** Jinja2 + a single hand-written stylesheet. Warm and plain — cream, ink, one accent. No design system, no CSS framework, no build step. The product's voice is "knowledgeable friend in a hardware shop," and the UI should match.

**Product card must show:** title, brand, price, **cost/year in equal weight to price**, repairability score if known, ownership badge, warranty.

---

# 19. The Glass Box

**The single highest-return thing on this list.** One page that demonstrates five rubric lines at once, refutes the "faked or stubbed" penalty, and makes the demo video shoot itself.

`/debug` shows, live, auto-refreshing:

1. **Event stream** — raw events landing as they arrive, with the batch boundaries visible
2. **Interest profile** — the JSON the agent inferred, with the actions it cited
3. **Retrieval** — candidates with **similarity scores**, shown **before and after** re-ranking, plus the metadata filter that was applied
4. **Agent path** — which LangGraph nodes ran, refine loop count, and whether `grade_evidence` passed
5. **Efficiency panel** — total events, LLM calls made, **cache hit ratio**, last trigger reason, last suppression reason
6. **Dual-write panel** — live SQL count vs vector count, in-sync boolean
7. **Mesh panel** — model used, tokens, latency for the last call

Link it from the main nav. Do not hide it. A judge finding this page unprompted is the best possible outcome.

---

# 20. Rubric Mapping

## 20.1 Hard rules (fail = invalid)

| Rule | Status |
|---|---|
| Public GitHub repo, all code in it | ✔ |
| Python Flask/FastAPI backend | ✔ FastAPI |
| Every LLM/AI call through Mesh | ✔ chat + embeddings — **verify embeddings day 1** |
| No committed secrets, `.env` gitignored | ✔ |
| One submission per participant | ✔ |
| Nothing faked or stubbed | ✔ `/debug` proves it |

## 20.2 "What a great submission looks like" — mirror this wording in the README

| Their words | Our implementation |
|---|---|
| *Tracking that captures rich behavioural signals without slowing the site down* | `sendBeacon`, 20-event/5-second batching, 800ms search debounce, single dwell event, `202` before write |
| *Products genuinely dual-written to SQL and a vector DB, kept in sync* | Create **and update and delete**, `vector_synced_at`, public consistency endpoint |
| *An agent that actually uses behaviour to drive catalog-grounded recommendations — not generic popular-product lists* | Intent inferred from real events; retrieval hard-filtered to the catalog; generation forbidden from inventing products |
| *Persuasive copy that reflects the specific user's interests* | Opens by naming their actual actions; compares on their stated priorities |
| *Production thinking: efficient triggering, caching, batched events, scheduled delivery* | Documented trigger policy, `profile_hash` cache, batched ingest, APScheduler digest — all visible on `/debug` |

## 20.3 Bonuses — do all four

*"These separate a solid submission from an exceptional one."* Most entrants will land one or two.

| Bonus | Cost | Status |
|---|---|---|
| ⭐ LangGraph structured agent | ~1 day | 6 nodes + conditional edges + refine loop |
| ⭐ Scheduled proactive delivery | ~½ day | APScheduler 08:00 IST email digest |
| ⭐ Observability | ~1 hr | LangSmith end-to-end |
| ⭐ Retrieval polish | ~½ day | Metadata filter + durability re-rank |

## 20.4 Round 1 vs round 2 — the thing to internalise

Submissions are screened by an **automated AI that reads the code**; only the top ones reach humans. **The domain concept scores zero in round 1.** Architecture completeness is priority #1; the Hardy idea is priority #2. A beautiful concept around a half-built agent loses to a plain course site where all five requirements genuinely work.

---

# 21. Repo Structure

```
hardy/
├── .github/workflows/smartreco-checks.yml   # verbatim from the organisers
├── .gitignore                               # must include .env
├── README.md                                # a scored artifact
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py                  # FastAPI app, scheduler startup
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── auth.py
│   ├── routes/
│   │   ├── storefront.py
│   │   ├── admin.py
│   │   ├── events.py
│   │   ├── recommendations.py
│   │   └── debug.py
│   ├── services/
│   │   ├── products.py          # DUAL-WRITE lives here
│   │   ├── events.py
│   │   ├── triggers.py          # the documented policy
│   │   └── mesh.py              # every AI call goes through this file
│   ├── agent/
│   │   ├── graph.py             # LangGraph definition
│   │   ├── nodes.py
│   │   ├── prompts.py
│   │   └── retrieval.py         # hybrid + re-rank
│   ├── scheduler.py             # APScheduler digest
│   ├── templates/
│   └── static/
│       ├── tracker.js
│       └── style.css
├── scripts/
│   ├── seed_catalog.py
│   └── seed_products.json       # committed, deterministic
└── tests/
    └── test_dual_write.py       # one runnable check
```

**Note:** every Mesh call routes through `app/services/mesh.py`. One file to point a judge at, and one file to prove nothing bypasses the gateway.

## `requirements.txt`

```
fastapi
uvicorn[standard]
jinja2
python-multipart
sqlalchemy
aiosqlite
passlib[bcrypt]
itsdangerous
openai
qdrant-client
langgraph
langchain-core
langsmith
apscheduler
aiosmtplib
pydantic-settings
httpx
```

`fastapi` + `openai` are the two the critical CI check looks for.

---

# 22. CI & Submission Setup

## 22.1 Workflow

Download verbatim and commit unchanged to `.github/workflows/smartreco-checks.yml`:

```
https://careerapi-production.krishnaik.in/api/ci/hackathons/smartreco-build-challenge-2026/workflow.yml
```

It requires `permissions: id-token: write` — without it the OIDC step dies. Do not edit it.

**How it works:** the runner mints a GitHub OIDC token (audience `https://career.krishnaik.in`), downloads a private `checks.py` from `careerapi-staging.krishnaik.in`, and runs it with `MESH_API_KEY` in the environment.

## 22.2 Secrets

Settings → Secrets and variables → Actions:

- `MESH_API_KEY` — the funded `rsk_...` key
- `SUBMISSION_TOKEN` — from the "My submission" tab (starts `gKb-`, ends `gt-Y`)

## 22.3 Checks

**Critical (block eligibility):** all Python files compile; `requirements.txt` lists a web framework **and** an LLM client.

**Advisory (feedback only):** no committed `.env`, README present, `.gitignore` ignores `.env`. Do all three regardless.

A failing critical check means "fix and push again" — it is not a penalty.

## 22.4 Hidden submission-form requirements

Found on the dashboard, and **they contradict the problem statement**:

- **Demo video (YouTube) is marked required** on the form, though the brief calls it optional. Treat it as required.
- **LinkedIn post link and X post link are both required.** Post on day 1, not on the 8th.
- **The GitHub URL locks permanently on submit.** One shot.
- Live URL, extra link, and notes for judges are genuinely optional.

---

# 23. Seven-Day Plan

| Day | Date | Deliverable |
|---|---|---|
| **1** | 2 Aug | Repo created. CI workflow committed, secrets added, **first green run**. Mesh key funded. **Embeddings question resolved.** FastAPI skeleton, auth, schema, migrations. LinkedIn + X posts published. |
| **2** | 3 Aug | Admin CRUD. **Dual-write incl. update and delete.** Consistency endpoint. Catalog seeded (~130 products, iFixit CSV + one generation pass). |
| **3** | 4 Aug | `tracker.js` — beacon, batching, throttling, dwell. `/api/events` bulk ingest. Storefront: home, category, product, search. Everything tracked. |
| **4** | 5 Aug | Qdrant wired. Hybrid retrieval. First working agent (plain, non-LangGraph). Recommendations stored and rendering on the site. **End-to-end loop alive.** |
| **5** | 6 Aug | Rewrite the agent as LangGraph with all six nodes + refine loop. LangSmith tracing. Re-ranking. Trigger policy + cache implemented. |
| **6** | 7 Aug | APScheduler digest + email template. **`/debug` glass box.** README written properly. Polish the storefront. |
| **7** | 8 Aug | Demo video recorded and uploaded. Deploy if cheap. Final CI green. **Submit.** |

**Submit on 8 Aug, not the 9th.** The deadline is noon IST and the repo URL locks permanently.

**Daily commits.** Not a stated rule here, but a code-screening AI can read history, and seven single-day commits look like exactly what they are.

---

# 24. Submission Checklist

- [ ] Public repo, final, all code committed
- [ ] CI green on the final commit
- [ ] `requirements.txt` lists `fastapi` and `openai`
- [ ] `.gitignore` includes `.env`; no `.env` committed; no secrets anywhere
- [ ] README: architecture diagram → **"Bonus features implemented"** → trigger/caching policy → setup and run steps
- [ ] Demo video on YouTube (**treat as required**)
- [ ] LinkedIn post link
- [ ] X post link
- [ ] Live URL (optional — finalists only)
- [ ] Notes for judges: point them at `/debug`, the dual-write service, and the trigger policy
- [ ] Double-check the GitHub URL before submitting — **it locks**

---

# 25. Risks & Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Mesh doesn't serve embeddings | **Invalidation** | Resolve day 1. Document fallback loudly if unsupported. |
| Mesh key unfunded when CI runs | **Invalidation** | Top up day 1; their `checks.py` gets the key. |
| Over-scoping the domain research | High | Ownership = one field + one quote. No scraping pipeline. Half a day, hard stop. |
| "Talks you out of buying" reads as not following the brief | High | Every recommendation ends in *buy this one*. Never "don't buy." |
| Agent half-finished because bonuses ate the week | High | Day 4 is a working end-to-end loop with a *plain* agent. LangGraph is a day-5 rewrite of something that already works. |
| Defamation-adjacent brand claims | Medium | Model may only quote `ownership_note` verbatim. `grade_evidence` enforces it. |
| Semantic-only retrieval returns nonsense | Medium | Metadata filter first, always. Shown on `/debug`. |
| Demo video doesn't land | Medium | One person, one decision, one reversal. 3 minutes. Show `/debug` mid-flow. |
| Vector/SQL drift | Low | Consistency endpoint, surfaced in two places. |

---

# 26. Kill List

**Do not build:** a cart or checkout · user reviews or ratings · multi-market or multi-currency pricing · a real ownership-research or scraping pipeline · recommendation A/B testing · social features · a custom design system or CSS framework · more than ~150 products · more than 8 categories · OAuth or social login · image uploads (use URLs) · admin analytics dashboards beyond `/debug`.

**If time runs short, cut in this order:**
1. Deployed URL
2. Re-ranking
3. LangSmith
4. Catalog size (130 → 80)
5. Email digest → Telegram (cheaper to wire)

**Never cut:** dual-write sync (incl. update/delete) · the agent loop · `/debug` · the trigger policy.

---

# 27. Open Questions

1. **Does Mesh serve `/v1/embeddings`?** — day-1 blocker, needs a funded key to answer. Everything in section 13 assumes yes.
2. **Which Mesh model for generation?** Start `openai/gpt-4o`. Compare against a cheaper one on quality of the persuasive copy; the whole product lives or dies on that copy reading like a person.
3. **SMTP or Resend or Telegram** for the digest — decide day 6, pick whichever authenticates fastest.
4. **Deploy or not?** Optional and finalists-only. Only if day 7 has slack.
5. **INR or GBP** for pricing — INR, given the judge pool and prize currency.

---

## The bet, restated

The community is running manual t-shirt durability experiments and asking each other whether brands are still good. The SERP for "products that last" is blogs and Quora. The only incumbents are an affiliate site, a printed book, and a hobby ledger. Every instrument in this market points at the seller.

Hardy points at the buyer, using the exact architecture the challenge demands.

**Buy it once.**
