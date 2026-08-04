# Hardy — brand book

*Buy it once.*

Source of truth for colour, type, voice and marks. Tokens are implemented in
`brand/tokens.css`; components consume tokens, never raw values.

---

## 1. The idea in one line

**Hardy vets what you're about to buy.** It is a knowledgeable friend in a hardware shop —
plain, unhurried, specific. It gives you the number and the reason, then points at one thing.

Everything below exists to make that sentence legible before a word is read.

---

## 2. Marks

| Mark | File | Use |
|---|---|---|
| Wordmark | `logo/hardy-wordmark.png` | Header, README, video title card, social |
| Monogram | `logo/hardy-monogram.png` | Favicon, app icon, avatar, tight spaces |

Both are 3D-printed brushed steel with real scratches and a brass rim-light on every bevel,
photographed on a soft studio sweep. Generated with `logo/gen.py`, cut out with `logo/cutout.py`.

**Why steel.** The product's promise is *this will outlast you*. A flat vector logo is a
promise made in software; a scratched steel object is a promise made in a material that has
obviously already survived something. The scratches are the argument.

**Rules**
- Clear space on all sides ≥ the height of the `H`.
- Never recolour, never add a drop shadow, never place on a busy photograph.
- Minimum wordmark width `7.5rem` (120px). Below that, use the monogram.
- On dark surfaces both marks hold — the brass rim carries the edge. No inverted variant needed.

---

## 3. Colour

### 3.1 How the palette was derived

Not invented. Sampled from the mark itself (8-colour median-cut over opaque pixels):

```
#CFC1B3 15%   #6D6158 14%   #ACA29C 13%   #9F8C7D 12%
#857B74 12%   #E4DACC 11%   #4B423A 10%   #C3AC97  9%
```

**Every swatch has R > B.** The mark is *warm* steel. So Hardy's neutrals are warm neutrals —
never the cool blue-grey of every other storefront. This is the single decision that makes the
site look like the logo.

### 3.2 The scale

| Token | Hex | Role |
|---|---|---|
| `--paper` | `#F7F3EC` | Page background. Warm, low-glare, reads as paper not screen. |
| `--paper-sunk` | `#EFE9DE` | Recessed surfaces, table stripes, input fields |
| `--card` | `#FFFCF7` | Raised surfaces. Lighter than the page, warmer than white. |
| `--rule` | `#DDD4C6` | Hairlines, borders, dividers |
| `--steel-light` | `#908883` | Disabled, decorative rules. **Not placeholders** — those use `--steel`. |
| `--steel` | `#756C66` | Secondary text, metadata, captions, placeholders |
| `--steel-deep` | `#6D6158` | Tertiary headings, active icons |
| `--ink-soft` | `#4B423A` | Body text |
| `--ink` | `#211D19` | Headings, price, primary text |
| `--brass` | `#8A6420` | **The one accent.** Links, focus, primary action, cost-per-year. |
| `--brass-bright` | `#B8862F` | Hover, rim highlights, on-dark accent |
| `--brass-wash` | `#F5EEDE` | Accent backgrounds, active nav, badge fills |

One accent, as specified in `HARDY.md` §18. `--brass` is deliberately deeper than the sampled
`#C3AC97` because an accent must clear **4.5:1 on `--paper`** — the sampled value does not.
The logo can be pretty; the interface has to be readable.

### 3.3 Ownership colours — **the important one**

`HARDY.md` §3.4 records the top-voted correction in our own source thread:

> *"This sub does not know the difference between private equity and larger conglomerates…
> They are hugely different business models."*

And the King's audit's third finding: a red "PE" badge would make Hardy the reactionary gimmick
the community itself pushes back on.

**Therefore: no red, no green, anywhere in the ownership system.** Not one hue that means
"bad", not one that means "good". Instead a single **brass-fill ramp** meaning *how much
ownership continuity we can evidence* — a confidence scale, not a moral one.

| Ownership | Treatment | Reads as |
|---|---|---|
| `trust` · `family` · `employee` | Solid `--brass-wash` fill, `--brass` text, `--brass` border | "there is a durable continuity story here" |
| `public` · `conglomerate` | No fill, `--rule` border, `--steel-deep` text | "ordinary corporate ownership, no signal either way" |
| `private_equity` | No fill, `--rule` border, `--steel-deep` text, **plus the date** | "ownership changed in 2021" — a fact, not a verdict |
| `unknown` | No fill, dashed `--rule` border, `--steel-light` text | "we don't know, and we'll say so" |

`private_equity` and `conglomerate` get **identical colour treatment**. The only difference is
that PE carries its acquisition date. The date does the persuading, because the date is a fact.
`unknown` is styled to look deliberately unfinished — honesty should be visible, not hidden.

Semantic red/green is reserved for system state only: form errors, the `/debug` in-sync boolean.
Never for a brand.

### 3.4 Contrast

Every text pairing in `tokens.css` is verified ≥ 4.5:1 on its intended background by
`brand/contrast.py`, which is a runnable check, not a claim. Run it if you change a colour.

```
$ python3 brand/contrast.py
All 14 pairs pass WCAG AA.
```

It caught three failures on first run — `--steel`, `--steel-light` and `--brass-wash` were all
too light against paper and were darkened until they passed. The values in §3.2 are the
corrected ones. This is why the check exists rather than a claim in prose.

---

## 4. Type

### 4.1 Families

| Role | Family | Why |
|---|---|---|
| Display | **Archivo Black** | Wide industrial grotesque, thick even strokes, squared terminals — the closest free face to the steel wordmark. The header echoes the logo. |
| UI | **Archivo** 400/500/600 | Same superfamily as the display face, so nav and buttons sit in the same voice. One family, many weights. |
| Editorial | **Source Serif 4** | The recommendation narrative is the product. A serif reads unhurried and considered — it is the "knowledgeable friend", not a push notification. Excellent numerals. |
| Numeric | **IBM Plex Mono** | `/debug`, scores, tabular figures, cost-per-year comparison tables. Tabular by default so digits align down a column. |

All four are open-source and self-hostable. No build step, no CDN dependency.

### 4.2 Scale

Modular, ratio **1.25**, base **1rem = 16px**. `rem` everywhere — never a hardcoded `px`
for type, spacing or layout (`CLAUDE.md` Rule 5).

| Token | rem | px | Use |
|---|---|---|---|
| `--text-2xs` | 0.694 | 11 | Legal, timestamps |
| `--text-xs` | 0.8 | 13 | Badges, captions, metadata |
| `--text-sm` | 0.875 | 14 | Secondary UI, table cells |
| `--text-base` | 1 | 16 | Body — never smaller |
| `--text-lg` | 1.25 | 20 | Lead paragraph, narrative body |
| `--text-xl` | 1.563 | 25 | Card titles, price |
| `--text-2xl` | 1.953 | 31 | Section headings |
| `--text-3xl` | 2.441 | 39 | Page titles |
| `--text-4xl` | 3.052 | 49 | Hero |

Line height: `1.6` body, `1.25` headings, `1.7` for the narrative (long-form, needs air).
Measure: **60–72 characters**. The narrative is 120–180 words and must never run full-width.

### 4.3 The cost-per-year rule

From the King's audit: price comparison is the **#1 trust signal (48%)**, and cost-per-year is
Hardy's differentiated number. So it gets **the same size, weight and position as the price** —
`--text-xl`, never small grey text underneath.

```
₹42,000              ₹2,100 / year
--text-xl --ink      --text-xl --brass
```

Price in ink, cost-per-year in brass. Equal weight. The accent colour is doing the arguing.

---

## 5. Voice

Plain, unhurried, specific. Hardy sounds like a person you'd trust because it gives you the
number and the reason, then points at one thing.

**Always**
- Lead with the specific action or the specific number
- Quote evidence verbatim and show its source next to it
- End by pointing at one product to buy

**Never**
- Exclamation marks, hype, urgency, scarcity, countdowns
- Moralising about consumption — Hardy never says *don't buy*, it says *buy this one instead*
- Asserting a brand declined. Only ever quoting a cited note. (`HARDY.md` §12.2)

| Instead of | Write |
|---|---|
| "Great news! Amazing deals on durable cookware!" | "You've opened three skillets this week." |
| "This product is built to last!" | "₹2,100 a year across a 20-year service life." |
| "Bosch has gone downhill since the buyout." | "Owners report the small appliances have slipped." — r/BuyItForLife |
| "Don't waste money on cheap tools." | "Buy the Miele if you'll stay a decade. Buy the Bosch if you won't." |

Microcopy is lowercase-sentence-case, never Title Case On Buttons. Buttons are verbs.

---

## 6. Layout

- **Spacing scale** `0.25rem` base: 0.25 / 0.5 / 0.75 / 1 / 1.5 / 2 / 3 / 4 / 6 / 8rem. Nothing off-scale.
- **Radius** `--radius-sm 0.25rem`, `--radius 0.5rem`, `--radius-lg 0.75rem`. Restrained — this is a hardware shop, not a fintech app.
- **Elevation** one shadow only (`--shadow-card`), soft and warm-tinted. Depth comes from the steel photography, not from the chrome.
- **Grid** 12 column, `max-width 75rem`, gutter `1.5rem`.
- **Breakpoints** `40rem` (640) · `48rem` (768) · `64rem` (1024) · `80rem` (1280).
- Every component works **360px → 1920px**. Mobile-first: write the small layout, then add.

## 7. Accessibility floor

Non-negotiable, per `CLAUDE.md` Rule 2.

- Body text ≥ 4.5:1, large text ≥ 3:1. Verified by `contrast.py`.
- Visible focus ring on every interactive element: `2px solid --brass`, `2px` offset. Never `outline: none`.
- Ownership and repairability are never communicated by colour alone — always colour **plus** a text label.
- Hit targets ≥ `2.75rem` (44px).
- `prefers-reduced-motion` respected on every transition.
