---
name: motion
description: A motion budget with the numbers and the sources: durations, easings, what never moves, reduced motion. The numbers are defaults a project edits in place. Use when an artboard, a component or a screen change involves a transition, an animation, a hover state, or a keyboard-triggered surface. Sources checked 2026-08-28.
---

# Motion

**Every number here is a default, and every one carries the source it came
from, checked 2026-08-28.** The sources publish these for interfaces in
general. A budget is a decision about one product, so a project that wants a
different figure edits the line here and writes the reason beside it, keeping
the source of whatever it replaced. This file is the one place the numbers
live; a second copy in a design guide is the copy that drifts.

## Frequency decides whether anything moves at all

Emil Kowalski's standards, which Raycast and Linear follow in practice:

| How often the person meets it | What to do |
|---|---|
| 100+ times a day: keyboard shortcuts, the command palette, row selection | No animation. The surface appears instantly. |
| Tens of times a day: hover, list navigation, expanding a row | Remove, or reduce to a colour change. |
| Occasionally: a dialog, a toast, a destructive confirmation | Standard timing below. |
| Rarely: onboarding, a first empty state | May delight. Once. |

Rauno Freiberg says the same from the other side: high-frequency surfaces
(command and context menus) appear instantly; keyboard needs no animated
affordance, touch does; every gesture is cancellable mid-way.

## Durations and easings

- Button press 100 to 160 ms; tooltip and small popover 125 to 200 ms (and
  0 ms for the next tooltip while one is showing); dropdown and select 150 to
  250 ms; dialog and drawer 200 to 500 ms. Everything under 300 ms.
- Ease-out for enter and exit, `cubic-bezier(0.23, 1, 0.32, 1)`; ease-in-out
  for a move or morph, `cubic-bezier(0.77, 0, 0.175, 1)`; drawers
  `cubic-bezier(0.32, 0.72, 0, 1)`; ease-in belongs in no UI; `linear` only for
  constant motion.
- Springs when something is dragged: duration 0.5, bounce 0.1 to 0.3.
- Press feedback `scale(0.97)`; an entrance from below `scale(0.95)` reads as a
  bounce nobody asked for.
- Stagger 30 to 80 ms, and only for a list that is new, never for a list the
  person already knows.
- Animate `transform` and `opacity` only; blur under 20 px.
- Material 3's token ladder for reference: 50 to 200 ms short, 250 to 400 ms
  medium, 450 to 600 ms long; its standard easing is `cubic-bezier(0.2, 0, 0,
  1)`.

## Reduced motion

`prefers-reduced-motion: reduce` means fewer and gentler, and zero is a
different setting. Keep opacity changes, drop anything that scales, pans or
slides. Apple's guidance is the same: minimise, replace with a cross-fade or a
static change, and let motion be one channel for information and never the
only one. A view transition checks the media query before starting.

Hover motion goes behind `@media (hover: hover) and (pointer: fine)`, so a
touch device is not animating on a hover it cannot express.

## Six calls the numbers above do not make

Each one is a sentence added to this file the first time it comes up, because
an engineer asks about all six while building:

| Call | What the sentence settles |
|---|---|
| Load | Whether a screen may settle in the first time it appears, and whether it repeats on a data change |
| The primary list action | What moves when a row is acted on, and for how long |
| Screen change | Which elements carry a `view-transition-name`, and at what duration |
| A charted number | Whether bars and lines move at all, and on which interactions |
| Copy and other confirmations | A label change, a toast, or neither, and how long it stands |
| Hover | A colour change, or something that moves |

A call recorded nowhere gets answered differently by each screen.
`design-references` names the guides carrying browser support for the features
these need.

## Sources

Emil Kowalski, `STANDARDS.md` in `github.com/emilkowalski/skills` and the
articles "7 practical animation tips" and "Great animations" at
`emilkowal.ski`; Rauno Freiberg, "Invisible details of interaction design" at
`rauno.me/craft`; Apple Human Interface Guidelines, Motion; Material 3 motion
tokens at `m3.material.io`; MDN, `prefers-reduced-motion`; Marcin Wichary, "A
few small details" at `unsung.aresluna.org` (interruptible animations, exits
quieter than entrances).
