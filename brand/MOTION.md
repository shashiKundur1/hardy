# Motion

Motion in Hardy does work or it does not exist. It tells you a card is interactive, that a
panel arrived, that a menu opened. Nothing moves for decoration, and nothing moves that would
delay a person doing the thing they came to do.

Every value below is a token in `tokens.css`. No duration or easing is ever written at a call
site.

---

## 1. The numbers, and where they come from

**Durations.** Jakob Nielsen's response-time limits are the floor and ceiling. 0.1 s is the
threshold at which a system is perceived as reacting instantaneously; 1.0 s is the limit for
keeping a user's flow of thought uninterrupted.
Source: [NN/g, Response Times: The 3 Important Limits](https://www.nngroup.com/articles/response-times-3-important-limits/)

| Token | Value | Used for | Why that number |
|---|---|---|---|
| `--duration-fast` | `90ms` | Hover, focus, colour and border changes | Under Nielsen's 100 ms bar, so the change reads as instantaneous |
| `--duration` | `160ms` | Menus opening, state changes the eye must follow | Long enough to be seen, far inside the 1 s flow limit |
| `--duration-slow` | `260ms` | Something arriving that was not there before | Material's medium band; the longest Hardy uses |

**Easing.** Taken from Material Design 3's motion tokens rather than chosen by eye.
Source: [Material Design 3, Easing and duration](https://m3.material.io/styles/motion/easing-and-duration/tokens-specs)

| Token | Curve | Material equivalent |
|---|---|---|
| `--ease` | `cubic-bezier(0.2, 0, 0, 1)` | `md.sys.motion.easing.standard` |
| `--ease-enter` | `cubic-bezier(0.05, 0.7, 0.1, 1)` | `emphasized-decelerate`, for things entering |
| `--ease-exit` | `cubic-bezier(0.3, 0, 0.8, 0.15)` | `emphasized-accelerate`, for things leaving |

Entering decelerates, leaving accelerates. A thing arriving slows into place; a thing going
away gets out of the way.

**Distance.** `--lift: -2px`. Large enough to read as a lift, small enough that it never
reflows a neighbour or shifts what someone is reading.

## 2. What is allowed to animate

**`transform` and `opacity` only.** Both are composited, so neither triggers layout or paint.

Never animate `width`, `height`, `margin`, `padding`, `top`, `left`, or anything else that
forces reflow. Colour and `border-color` transitions are allowed because they paint without
reflowing, and because state changes carried by colour need a visible transition to be noticed
at all.

## 3. Where motion earns its place

| Surface | What moves | Token |
|---|---|---|
| Product card, tile, chip, pick | `translateY(var(--lift))` on hover and focus | `--duration-fast`, `--ease` |
| Account menu panel | Opacity and a small rise on open | `--duration`, `--ease-enter` |
| In-context recommendation | Opacity and a rise as it arrives | `--duration`, `--ease-enter` |
| Buttons, links, inputs | Background, border and colour | `--duration-fast`, `--ease` |

Nothing else moves. The product grid does not stagger in: a shopper came to read the grid, and
making them wait for it to assemble is the failure mode this section exists to prevent.

## 4. Reduced motion

`prefers-reduced-motion: reduce` sets every duration token to `0ms` and `--lift` to `0px` **at
the token level**, in `tokens.css`. Because no component writes its own duration, honouring the
preference is not something a component can forget to do.

The reduced path is a real design, not motion switched off leaving something broken. Every state
that motion communicates is also carried by something static: hover changes border colour as
well as lifting, the recommendation panel keeps its amber edge and its `role="status"`
announcement, and the account menu is a `<details>` element whose open state is structural.

WCAG 2.3.3 Animation from Interactions (AAA) is satisfied: every animation triggered by
interaction can be disabled, and none is essential to the function.

## 5. Checking it

```bash
grep -nE '[0-9]+ms|cubic-bezier' src/static/style.css
```

Should return nothing. Every duration and curve lives in `tokens.css`; a raw value in
`style.css` is the regression this command catches.
