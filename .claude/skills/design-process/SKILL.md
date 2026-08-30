---
name: design-process
description: How design work is done: decide before drawing, research before variants, sourced numbers, variants named after their reference, a measurement instead of a look, a second read against the guide, and a deliverable the team layer names. Use at the start of any design task, and when someone asks how the wireframes were made.
---

# Design process

Nine steps in the order they happen. Each names the failure it prevents,
because every one of them has happened.

## What the project supplies

This skill is the method. Five inputs are the project's.

| Input | Where it lives | Absent |
|---|---|---|
| The constraints on every screen | the design guide under `docs/` | Ask, and write the answers there |
| The person the work is delivered to | `.agentkit/local.md` | Nobody has been asked yet (rule 0) |
| Where a finished design lands | `.agentkit/team.md`, `## Design`, `surface` | Ask. Step 8 has three answers and no default |
| Which reference list is in play | `.agentkit/team.md`, `## Design`, `references` | `curated`, the `design-references` file |
| The artboard generator and the capture | the project's design directory | Steps 3 and 6 say what each needs |

Report an absent input and ask. A guessed constraint reads as a settled one on
the artboard, and whoever never agreed to it finds out at review.

## 1. Decide the product shape before the UI

Settle the questions whose answers change the shape of the work: the surface,
the unit somebody acts on, how a decision is explained back to them. That
happens in conversation, checked against a teardown of shipped tools, and rules
1 to 8 in `CLAUDE.md` hold whatever the project locked. Drawing first produces
screens shaped like the schema. Shape Up calls this breadboarding: places,
affordances and connections in words, no layout.

## 2. Read the guide, then the person

The design guide holds the constraints. `.agentkit/local.md` holds how work is
delivered and to whose taste. A design that ignores either is redone.

## 3. Wireframe greyscale, generated from one script

One generator writes every artboard, so a number or a label changes in one
place and the frames stay consistent. Greyscale on purpose: structure and
behaviour first, colour and the type pair still the designer's call, and the
frames saying so. Real numbers, scaled from a measurement, never lorem ipsum.

## 4. Research before variants, numbers from the source

For each element that decides whether the product feels good, read two or three
shipped references and take their actual sizes, radii and durations.
`design-references` is who to read. Draw the variants side by side, each named
after its reference, with what it borrows and its tradeoff in a line, then say
which one the wireframes adopt and why. A variant set where only the favourite
gets a case made for it is a rigged vote. A source publishing no numbers lends
behaviour only, and the sheet says so.

## 5. Moodboards carry facts

Two boards. What the screens do: the teardown, with the vendors' own images and
borrow or refuse per tool. How they should feel: product shots, the motion to
go and look at, and the tokens each site's CSS declares, meaning type, greys,
accent, radius, easing, duration. Marketing art, logos and phone-in-hand photos
are cut; only interfaces stay.

## 6. Render and measure, every time

Render every artboard with headless Chrome at its frame size and inspect it
before saving. Clipping, an overflowing column and a stale capture are all
caught this way and none of them by reading the markup.

**Read numbers out of the page instead of looking at it.** A claim about a
screen is `getBoundingClientRect()` and `scrollWidth` on the elements it is
about:

| Claim | The assertion |
|---|---|
| A cell clips | `scrollWidth > Math.ceil(width) + 1` |
| A column lines up | the set of its cells' left edges has one member |
| A label aligns with its values | a `Range` over each text node gives the same right edge |
| The intended font is painting | `document.fonts.check('16px "Name"')` |

An eye passes the first three when they are a pixel or two out, and a pixel or
two out is what a person sees without knowing why.

**Two failures look correct.** A page whose webfont never loaded reports the
declared `font-family` while painting the fallback at other metrics, so the
assertion asks `document.fonts`. And a capture taken against whatever
configuration sat beside it records a misconfiguration as a design: pin the
environment a capture runs in.

**The capture is a pattern each project writes for itself.** It needs a dev
server on a known port, a fixture built fresh each run so a stale one cannot
make a capture look right, and a route list of one state per screen. One page
load per route then writes the artboard and the measurements together.

## 7. A second read against the guide

After the build, a separate pass reads the artboards against the design guide
and against reality: totals against their tables, dates against the calendar,
the vocabulary, one meaning per grey. A first pass over a screen set that
looked finished found sixteen problems, all real.

## 8. The deliverable, as the team layer names it

`.agentkit/team.md` carries `surface` under `## Design`, and rule 0 puts the
choice there because two people open the same thing.

| `surface` | What step 8 does |
|---|---|
| `canvas` | Publish the artboards with click-to-edit and PNG or PDF export, link them from the design guide, and put the renders in the pull request for a reviewer without the link |
| `file` | The artboards stay at the path the setting names, and the pull request carries the renders |
| `none` | Nothing is published. Steps 1 to 7 still apply to any screen |

The source stays in the repository under all three, because a surface holding
the only copy is one an account can lose.

## 9. Write the decision where it is read next

A design call goes into the design guide as a proposal with its reasoning. One
person's preference goes into `.agentkit/local.md`. A fact about CSS or motion
goes into `css-now` or `motion`, where those numbers live. A decision that
lives only in a transcript is repeated forever.

## Tools worth reaching for

`context7` for current framework documentation. `playwright` once real screens
exist, to drive them instead of the artboards. `code-review` on the pull
request.

| Excuse | Reality |
|---|---|
| "The layout is obviously fine, I can see it." | Three of the four assertions in step 6 pass an eye and fail a measurement. |
| "There is no design guide, so there are no constraints." | Report the absence. A guessed constraint ships as an agreed one. |
| "One variant, because the other two were clearly worse." | Then the case for the winner is missing. Draw them. |
| "The artboards are the record." | An artboard shows the decision and says nothing about why. |
