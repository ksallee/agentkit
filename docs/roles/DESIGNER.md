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

## Checking a design change

Look at it, then measure it. Four things a reading misses and a measurement
catches:

- A cell that clips, where the content is wider than the box holding it.
- A column out of alignment, where the left edges differ by a pixel or two.
- Labels that do not sit on one baseline.
- A font that fell back silently, so the screen you approved is not the screen
  that ships.

Record what you checked and what you saw, the same way rule 16 asks a pull
request body to.
