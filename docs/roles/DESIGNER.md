# Designer's guide

Owns the look, the reading order, and the words on screen. Read `CLAUDE.md`
first, then this. The numbers on every screen come out of a pipeline the
engineer owns, and nothing here computes one.

## Name the screen that decides whether the product survives

One screen usually carries the risk, and finding it is the first design job.
The shape to look for: the feature works on day one and the habit does not. A
triage screen that is unpleasant to use is a tracker that quietly stops being
accurate six weeks in, and no amount of correct arithmetic saves it. A design
problem with an engineering consequence is somebody's job, and it stops being a
coat of paint applied at the end.

Write that screen and its failure mode into this section, in this project's
terms. Everything below is craft that holds either way.

## Answer first, controls below

Every screen answers one question. That answer goes in the first line, at the
largest type on the page, before any control. A person who came to find out
whether they can ship today should not have to operate anything to learn it.

Write the question down for each screen before drawing it. A screen that
answers two questions is two screens, or one with a clear second section. A
screen answering none is a control panel, and it belongs inside the screen that
needed it.

## Reading order is a decision, and the layout carries it

Somebody's eye goes to the largest thing, then to the thing with the most
contrast, then left to right along the first line. Order the page in the order
you want it read, then check that size and contrast agree with that order. Two
elements competing for first place means neither wins.

## One meaning per colour

Pick the meanings before the palette: what is active, what is a problem, what
is done, what is neutral. Then one colour each, used nowhere else. A colour
that means "selected" in one view and "billable" in another teaches the reader
to check the legend every time, and they stop reading it.

Never carry meaning in colour alone. A shape, a position or a word carries it
too, so the screen still works in greyscale and for somebody who cannot
separate the two hues you chose.

## Density is a choice you make once

Set the spacing scale, the type scale and the row height at the start and hold
them. A screen at a different density from the one beside it reads as a
different product. Where a view genuinely needs more rows visible, make it a
setting, and let it change every view at once.

## Words are part of the design

Keep a vocabulary table: one term per concept, and what never to call it.

| Say | Never say |
|---|---|
| the term the product uses | the two synonyms somebody will reach for |

Two words for one thing is the most common way a UI gets confusing, and it
costs nothing to fix while there are four screens. Labels are sentence case,
buttons are verbs, and an error says what to do next.

## One chart, and only when a number will not do

A chart earns its place when the shape is the point: a trend, a distribution, a
comparison across many items. A single value is a number. Two values are two
numbers. Where a chart is right, one chart on the screen, and it gets a
readable axis and a stated unit.

## Handing work back

When a screen needs a number the API does not return, file it and hand it to
the engineer. A component that sums, rounds or derives is a second
implementation of the pipeline, and the two will disagree in the week that
matters.

`.agentkit/team.md` says who wins when two roles disagree.

## Where the artboards live, and what writes them

`design/` holds them, and the team layer's `surface` names that same path when
it is `file`. A screen that already runs is captured from the running app. A
screen that does not exist yet is drawn. Both land here, so the canvas and a
pull request see one set of artboards.

A capture writes two files per screen from one page load, and hand-editing
either is work the next run deletes:

| File | What it is | What it is for |
|---|---|---|
| `<Name>.dc.html` | computed styles inline, one style attribute per node, tokens written back as `var()` | what the canvas opens, because a properties panel reads and writes the element's own `style` attribute |
| `<Name>.classes.html` | the markup with the app's stylesheet carried whole | several times smaller and pixel exact, so a pull request diffs this one and reads the design change |

`design/screens.json` names the screens, the routes and where the app answers.
The capture points at that URL and starts nothing, so bring the app up first,
then run the driver this project's pack seeded:

```sh
uv run --with playwright python design/capture.py   # python
node design/capture.mjs                             # typescript
```

Every name in `screens.json` belongs to the capture. Nothing else writes those
two files: a capture that failed, or that has never run, must not be able to
move an artboard somebody drew.

**To explore, duplicate an artboard in the canvas and work on the copy.** The
copy carries the root's provenance stamp, five attributes naming the route, the
commit, the time, the frame size and a digest of the captured markup. Capture
again and compare the digest: a different one means the real screen moved while
you were working, and a commit alone cannot tell you that over a dirty tree.

A screen nobody has built is drawn by the generator, into the same directory:

```sh
python3 design/build.py   # python
node design/build.mjs     # typescript
```

One generator writes every frame, so a number or a label changes in one place
and the frames stay consistent. It ships a greyscale palette, a type scale, a
spacing scale and a frame size as defaults, and `Palette.dc.html` renders
whatever those say. Edit the constants and the artboard follows. Greyscale is
where a wireframe starts, and colour and the type pair stay your call, so
nothing checks that an artboard is grey.

Add a frame by adding a function and a row to `ARTBOARDS`, and it gets a slot in
`design/canvas.json` on the next run. The generator refuses to write a name
`screens.json` gives the capture, and it reserves a canvas slot for each one
instead. A generated artboard stamps `data-generated-by`, its frame size and a
digest, and no commit and no clock, so a rerun that changed nothing writes the
same bytes and a diff on `design/` is a design change every time.

## Checking a design change

Look at it, then measure it. A capture measures every box on the artboard
against the live app and fails on anything more than a 64th of a pixel out, so
a written artboard matches the screen it came from. Whether that screen was
right is a separate question, and nothing in the capture answers it.

Four things a reading misses and a measurement catches, on a captured artboard
and a drawn one alike:

- A cell that clips, where the content is wider than the box holding it.
- A column out of alignment, where the left edges differ by a pixel or two.
- Labels that do not sit on one baseline.
- A font that fell back silently, so the screen you approved is not the screen
  that ships.

Record what you checked and what you saw, the same way rule 16 asks a pull
request body to.
