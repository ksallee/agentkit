---
name: css-now
description: What CSS to reach for today, with Baseline status and the one gotcha each, checked against MDN and caniuse on 2026-08-28. Use when writing or reviewing anything that lays out, positions, transitions or themes, and when a design artboard names a CSS feature. Re-verify any line older than six months before relying on it.
---

# CSS now

Checked 2026-08-28. Baseline labels are MDN's; versions are caniuse's. Each
line is: what it is for, where support stands, the gotcha the source states.
A feature marked "enhancement only" ships behind `@supports` with a fallback.

## Ship without a fallback (Baseline widely available)

- **`<dialog>`** (widely available, March 2022). Anything modal. `showModal()`
  makes the rest inert and Esc closes by default; the `open` attribute alone is
  non-modal; `tabindex` never goes on the dialog itself.
- **`:has()`** (December 2023). A row with a selected child, a field with an
  error. Cannot nest, no pseudo-elements inside; prefer `:has(> .x)` over
  `body:has(...)`, which is slow.
- **Container queries** (`@container`, February 2023; `cqw` units Chrome 105,
  Safari 16, Firefox 110). A table that narrows with its panel instead of the
  viewport. Units fall back to small viewport units with no container.
- **`@layer`** (March 2022). Unlayered styles beat every layer; `!important`
  order inverts.
- **Nesting and `&`** (December 2023). `&` specificity is not Sass's.
- **`color-mix()`** (May 2023). Default space is oklab; sRGB gives dull mixes;
  it cannot raise opacity, relative colour syntax can.
- **`color-scheme`** (January 2022) with `<meta name="color-scheme"
  content="light dark">` to avoid a flash.
- **`linear()`** easing (December 2023). Two stops minimum, ascending.
- **Subgrid** (September 2023). No implicit tracks in a subgridded axis.
- **`:user-valid` / `:user-invalid`** (November 2023). Fire after commit (blur
  or submit), then per keystroke.

## Ship, with a fallback in mind (Baseline newly available)

- **Same-document View Transitions** (Baseline 2025, October 2025; Chrome 111,
  Safari 18, Firefox 144). Screen changes inside a single-page app. The
  framework's navigation hook returns a promise wrapping
  `document.startViewTransition`, resolves inside the callback, then awaits the
  navigation; SvelteKit's `onNavigate` is the pattern the docs give, and every
  hook needs the same feature detection and early return. The docs warn that a
  slow promise makes navigation look stalled, and to respect
  `prefers-reduced-motion`. Gotcha (MDN): reading position and focus can be
  lost while old and new DOM coexist. Name the elements that should move with
  `view-transition-name`; group shared styling with `view-transition-class`
  (also Baseline 2025).
- **Popover API** (Baseline 2025, January 2025). Menus and pickers. Always
  non-modal; use `<dialog>` when the rest must be inert.
- **`light-dark()`** (Baseline 2024, May 2024). Does nothing without
  `color-scheme: light dark` on `:root`.
- **`text-wrap: balance`** and **`pretty`** (Baseline 2024, March 2024).
  `balance` for a headline, capped at 6 lines in Chromium; `pretty` for body
  copy, slower.
- **`@starting-style`** (Baseline 2024, August 2024). Entry animation for a
  popover or dialog. Same specificity as the base rule, so it comes after it;
  fires on first render or from `display: none`; top-layer elements need
  `overlay` and `display` in the transition with `allow-discrete`.
- **`transition-behavior: allow-discrete`** (Baseline 2024, August 2024).
  Declare `transition` twice, once without the keyword, as the fallback.
- **`@property`** (Baseline 2024, July 2024). Animating a custom property.
  `syntax`, `inherits`, `initial-value` all required unless `syntax: "*"`, and
  the initial value must be computationally independent (`10px`, never `3em`).
- **Anchor positioning** (Baseline 2026, January 2026; Chrome 125, Safari 26,
  Firefox 147; spec still a Working Draft, 84% global). A menu anchored to the
  row it belongs to. Treat as an enhancement over a positioned fallback; MDN
  says parts may vary.
- **`@scope`** (Baseline 2026, March 2026). Inherited properties leak past the
  scope limit; `&` specificity differs by engine.
- **`field-sizing: content`** (Baseline 2026, June 2026; Chrome 123, Firefox
  152, Safari 26.2). An input or textarea that grows with its text. A fixed
  `width` or `height` overrides it; `rows` and `cols` are ignored.
- **Relative colour syntax** (Chrome 131, Safari 18, Firefox 133; MDN gives no
  Baseline year). Channels are numbers: `calc(l + 20)`, never `+ 20%`.

## Enhancement only (not Baseline)

- **Cross-document `@view-transition`** (Chrome 126, Safari 18.2, no Firefox).
  Same-origin only. A single-page app wants the same-document API above.
- **Scroll-driven animations** (`animation-timeline: scroll() / view()`; Chrome
  115, Safari 26, Firefox 152 still behind a flag). Where a page scrolls for
  effect, MDN's own demo wraps it in `@supports not (scroll-timeline: ...)`.
- **`interpolate-size` / `calc-size()`** (Chrome 129 only; no Firefox, no
  Safari through 27). Animating to `auto`. Opt-in by design; ship behind
  `@supports` with no motion as the fallback.

## Sources

MDN reference pages per feature, caniuse per feature, the SvelteKit blog post
on view transitions and `$app/navigation` docs, Mozilla Connect for the Firefox
scroll-timeline status. Re-check the "enhancement only" section first; it is
the one that changes.
