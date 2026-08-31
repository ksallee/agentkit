---
name: design-process
description: How design work is done here, from the product decision before any UI to the deliverable and the decision written where it is read next. Covers the guide read before the person, greyscale wireframes from a script, research and moodboards with sourced numbers, variants named after their reference, a rendered measurement instead of a look, and a second read against the guide. Use at the start of any design task, and when someone asks how the wireframes were made.
---

# Design process

Nine steps in the order they happen. Each names the failure it prevents,
because every one of them has happened.

## What the project supplies

This skill is the method. Six inputs are the project's.

| Input | Where it lives | Absent |
|---|---|---|
| The constraints on every screen | the design guide under `docs/` | Ask, and write the answers there |
| The person the work is delivered to, and the medium they want it in | `.agentkit/local.md` | Nobody has been asked yet (rule 0) |
| Where a finished design lands | `.agentkit/team.md`, `## Design`, `surface` | Ask. Step 8 has three answers and no default |
| Which medium in-progress design reaches a reader through | `.agentkit/team.md`, `## Design`, `review` | Take `artifact`. The row seeds with it, so an absent row is a project on the default |
| The capture, and the screens it opens | `design/capture.js` with `design/capture.py`, `design/capture.mjs` or both, seeded by `adopt`, and `design/screens.json` | Adopt the scaffolding. Step 6 says which driver to run, what the shipped capture asserts and what it leaves to you |
| The artboard generator, and the components it draws with | `design/build.py` or `design/build.mjs`, seeded by `adopt`; the components are the project's | Adopt the scaffolding. It ships the palette, the scales and one entry point, and no component |

Report an absent input and ask. A guessed constraint reads as a settled one on
the artboard, and whoever never agreed to it finds out at review.

## The loop, and the mode it runs in

Steps 3 to 7 run more than once. A set of artboards goes in front of the
operator, the direction gets confirmed or corrected, and the next pass carries
the correction. An agent that walks 1 to 9 once has made every call itself, and
the first place anybody can disagree is the deliverable.

**Ask which mode at launch. Record nothing.** An operator away from the
keyboard wants the run to finish. The same operator at the keyboard wants to
see each pass. A stored default is wrong half the time, so the question gets
asked every time a designer agent is launched on a task.

| Mode | Between passes |
|---|---|
| autonomous | Nothing. The agent runs to the deliverable and reports once |
| checkpointed | The agent publishes the review medium, asks whether the direction holds, and carries the answer into the next pass |

**Two layers hold the medium, per rule 0.** `.agentkit/team.md` carries
`review`, the medium this project's in-progress design reaches a reader
through, because a project paying for a design tool needs a committed place
saying so. `.agentkit/local.md` carries what one designer wants, because two
designers on one project can want different media and neither gets forced onto
the other's tool.

| `review` | What the operator opens mid-work |
|---|---|
| `artifact` | A published Claude artifact carrying the artboards, republished in place each pass so one link stays current |
| `paper` | The designer's own Paper canvas. Nothing here writes to it until a probe prints what its local MCP server returns, which rule 9 requires and nobody has run |
| `none` | Nothing until step 8 |

Screenshots pasted into a terminal are what a session delivers when nobody
named the medium. They arrive at whatever size the terminal gives them, drop
the live layout and the type, and cost a round of asking to see it bigger.
Favour an artifact.

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
before saving. Clipping and an overflowing column are caught this way and
neither by reading the markup. A stale capture is caught by neither, because
one artboard on its own has nothing to compare against, and the shipped capture
settles it with the `data-captured-digest` stamp on the root and the box
comparison.

**Read numbers out of the page instead of looking at it.** A claim about a
screen is `getBoundingClientRect()` and `scrollWidth` on the elements it is
about. These four are yours to run, in a console or a script. The shipped
capture runs none of them:

| Claim | The assertion |
|---|---|
| A cell clips | `scrollWidth > Math.ceil(width) + 1` |
| A column lines up | the set of its cells' left edges has one member |
| A label aligns with its values | a `Range` over each text node gives the same right edge |
| The intended font is painting | `mmmmmmmmmmlli` at 100px measures a different width in `"Name", <generic>` than in `<generic>` alone, for at least one of `monospace`, `serif`, `sans-serif` |

An eye passes the first three when they are a pixel or two out, and a pixel or
two out is what a person sees without knowing why.

**Two failures look correct.** A page whose webfont never loaded reports the
declared `font-family` in its computed style while painting the fallback at
other metrics. And a capture taken against whatever configuration sat beside it
records a misconfiguration as a design: pin the environment a capture runs in.

**`document.fonts.check` answers a different question.** It reports whether a
matching face is available to the font set. Measured in headless Chrome 152 on
2026-08-30, it returned `true` for a family declared in no `@font-face` and
installed nowhere, at every moment of the page's life, which is what a typo in
a family name and a stylesheet that never shipped both look like. It returned
`false` for a face that does paint, until something forced that face through
layout. The width probe in the table above moved at least one generic by 119px
for every family that painted, and all three by 0.00px for every family that
did not.

**Three generics, no tolerance.** One generic can sit almost on top of the
target: Courier New against `monospace` moved `mmmmmmmmmmlli` at 100px by
2.53px, and `BESbswy` at 16px by 0.22px. A fallback renders identically in both
spans, so a family that never paints measures 0.00px against all three and a
threshold has nothing to protect. Both spans measure off-screen with
`white-space: pre`, because a line break moves a width for its own reasons.

**The shipped capture asserts a fifth thing: the artboard matches the app.**
It reloads each written artboard, measures every box on it and compares that
to the live page, failing the run when one moved further than `1/64` px, the
grid Chrome lays out on. That catches a stale or wrong artboard. It catches
none of the four above, because the live page is the truth it compares to: a
clipped cell, a ragged column and a substituted font all reproduce faithfully
in an artboard that passes.

**A project is handed a capture and may replace it.** `adopt` seeds `design/`
with `capture.js`, the contract both drivers evaluate in the page, and
`screens.json` naming the screens and where the app answers. The capture points
at a URL where the app already answers and starts nothing itself. The driver
owns `<Name>.dc.html` and `<Name>.classes.html` for every name in
`screens.json`, so a project that wants different files replaces the driver. A
second one beside it writes files the driver already owns.

**Which driver is there depends on the pack, and `none` gets both.** The python
packs receive `capture.py`, `typescript` receives `capture.mjs`, and `none`
receives the pair, because a driver needs a browser rather than a language and
a gate list naming no toolchain says nothing about which runtime the machine
has.

**Run the one whose runtime is present.** `capture.py` runs under `uv run
--with playwright`; `capture.mjs` runs under node with puppeteer resolving from
the project's `node_modules`. Read the directory, then the machine:

```sh
ls design/capture.py design/capture.mjs
uv --version && node --version
```

Where both runtimes answer, take the driver written in the language the project
is written in. Both write the same bytes from the same screen, and
`tests/test_design.py` in the agentkit checkout holds them to it.

**The stamp names the driver that wrote the artboard.** Every root carries
`data-captured-driver`, reading `capture.py` or `capture.mjs`, beside the
route, the commit, the time, the viewport and the digest. Two artboards in one
directory can have come off two runtimes, and a box that differs between them
is a browser difference before it is a screen change. Say which driver produced
the artboards in the pull request.

## 7. A second read against the guide

After the build, a separate pass reads the artboards against the design guide
and against reality: totals against their tables, dates against the calendar,
the vocabulary, one meaning per grey. A first pass over a screen set that
looked finished found sixteen problems, all real.

## 8. The deliverable, as the team layer names it

`.agentkit/team.md` carries `surface` under `## Design`, and rule 0 puts the
choice there because two people open the same thing. `surface` places the
finished design. `review` beside it places the passes before this one.

| `surface` | What step 8 does |
|---|---|
| `canvas` | Publish the artboards with click-to-edit and PNG or PDF export, link them from the design guide, and put the renders in the pull request for a reviewer without the link |
| `file` | The artboards stay at the path the setting names, and the pull request carries the renders |
| `none` | Nothing is published. Steps 1 to 7 still apply to any screen |

The source stays in the repository under all three, because a surface holding
the only copy is one an account can lose.

## 9. Write the decision where it is read next

A design call goes into the design guide as a proposal with its reasoning. One
person's preference goes into `.agentkit/local.md`. A fact about motion goes
into `motion`, where those numbers live, and a CSS fact the Chrome guides leave
out goes into `design-references`. A decision that lives only in a transcript is
repeated forever.

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
