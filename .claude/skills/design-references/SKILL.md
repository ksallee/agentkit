---
name: design-references
description: Who to learn from for a dense, keyboard-first, quiet interface: designers, design engineers and products, with what each is known for and where to look. Use when a design task needs a reference for a component, a motion, a layout or a tone, before drawing from memory. Links checked 2026-08-28.
---

# Design references

Look before drawing. Every reference below publishes, so a fact can be read at
the source rather than remembered. When one is used, the artboard names it.

The list serves one genre: dense, keyboard-first, quiet. A project in another
genre keeps the people, who write about craft, and builds its own product list.

## People

- **Rauno Freiberg**, `rauno.me/craft`. Interaction essays, the Command Menu
  and Combobox pieces, Vercel and Next.js work. The reference for why
  high-frequency surfaces do not animate.
- **Emil Kowalski**, `emilkowal.ski`. Sonner and Vaul, the animations.dev
  course, ex-Vercel and Linear. The numbers in the `motion` skill are his.
- **Paco Coursey**, `paco.me`. Author of `cmdk` and next-themes; Linear.
- **Jhey Tompkins**, `jhey.dev`. UI demos and interaction patterns, CSS tricks
  that hold up; ex-Chrome DevRel, ex-Vercel.
- **Adam Argyle**, `nerdy.dev`. CSS notebook, Open Props; the first place a new
  CSS feature gets a working demo.
- **Una Kravets**, `una.im`. CSS writing, The CSS Podcast, one-line layouts.
- **Josh Comeau**, `joshwcomeau.com`. Interactive tutorials on CSS and
  animation; the scroll-driven animations guide.
- **Amelia Wattenberger**, `wattenberger.com`. Novel interfaces and data
  visualisation. For when a chart has to be better than a chart.
- **Maggie Appleton**, `maggieappleton.com`. Visual essays on tools for
  thought. For how a screen explains itself.
- **Karri Saarinen**, `karrisaarinen.com`. Linear's CEO; his ten craft rules
  are on the Figma blog. Density and hierarchy over decoration.
- **Sam Selikoff**, `samselikoff.com`. Build UI, Frontend First. Component
  behaviour explained in code.
- **Jakub Krehel**, `jakub.kr`. "Details that make interfaces feel better",
  "Drag gestures on the web".
- **Marcin Wichary**, `unsung.aresluna.org`. Small details: interruptible
  animation, quieter exits.
- **Benji Taylor**, `benji.org`. The Family write-up ("family values"): delight
  intensity inversely proportional to feature frequency.
- **Flo Guo**, `floguo.com/notes/design-engineering`. Curates design engineers;
  a good index when this list goes stale.

## Products and systems

- **Linear**, `linear.app/now`, `linear.app/method`. Density, one accent, the
  redesign post on reducing visual noise.
- **Raycast**, `raycast.com/blog/category/craft`. Instant palette, recently
  used at the top, favourites on ⌘1 to 9, no shadows, a surface ladder.
- **Superhuman**, `blog.superhuman.com`. The command palette post (one shortcut
  exposes and teaches every command; fuzzy matching with aliases) and the inbox
  zero images post.
- **Vercel Geist**, `vercel.com/geist`. Menu, Table, Button conventions; Geist
  and Geist Mono; the design engineering post on weighing cost against
  experience impact.
- **shadcn/ui**, `ui.shadcn.com`. Command, Table, Button, Kbd, Toggle Group
  sources, with exact sizes an artboard can quote.
- **cmdk**, `github.com/pacocoursey/cmdk`. The Vercel, Linear and Raycast
  themes in its demo carry the palette dimensions.
- **Amie**, `amie.so`. An interface that feels physical; the drag reference,
  and one bouncy easing used deliberately.
- **Notion Calendar**, `notion.com/product/calendar`. Time as columns, one
  weight of grey, colour only on events.
- **Family**, `family.co`. The most animated of the set; study, do not copy.

## The project's own references

Two or three products in the same genre, added here as the project finds them.
One line each: what it is known for, and whether it publishes numbers. Where a
competitor is being studied for what to refuse, say so, because an artboard
naming it otherwise reads as an endorsement.

## One catalogue, if the project asked for it

`.agentkit/team.md` carries a `references` setting: `curated` or `refero`.
Curated is the list above, it needs no account and no service, and it is what
runs when the setting is absent.

`refero` adds `styles.refero.design`, which extracts a design system from a
product's website and publishes it as a `DESIGN.md`. It arrives through the
Refero MCP server offered at `refero.design/mcp`, and rule 9 wants a probe of
what its tools return before anything parses them.
`probes/refero_styles.py` measured the site on 2026-08-30: a style page is
270 KB of HTML carrying colours, typography, spacing, shapes, elevation and
components, and no path serves the `DESIGN.md` as a file.

It answers one question: a product this list does not cover, whose numbers are
wanted for one component.

## How to use a reference

Open the source, take the number or the behaviour, name the source on the
artboard, and write the tradeoff in a line. A reference that publishes no
numbers lends behaviour only; say so.

**Importing a whole design system is a decision about what the product is.**
Three projects that each take one from the same catalogue come out looking like
each other. Take the radius, the duration, the type scale. Adopt a system
whole once, deliberately, with the project's name on it.
