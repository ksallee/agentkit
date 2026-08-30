# Writing style

<!-- style-check: exempt, because the tables below quote the patterns they ban. -->

Applies to every word committed here: markdown, code comments, docstrings,
commit messages, issue and PR bodies, skill files.

## Who reads this

An LLM reads it first, a person reads it second. An agent loads these files
into a context window every session, pays for every token, and cannot ask a
follow-up question when a sentence is ambiguous. A person skims past a vague
line. An agent acts on it.

The target: **maximum context in minimum tokens, with nothing that has to be
resolved from elsewhere.**

## Banned outright

| Pattern | Why | Write instead |
|---|---|---|
| Em dash `—` | Ambiguous glue. It hides whether the clause is an aside, a cause, or a new sentence. | `.` `,` `:` or `()` |
| "not X, Y" · "not just X, but Y" · "It isn't X, it's Y" | The strongest machine tell in prose. Emphasis the sentence has not earned. | Say Y. If the contrast carries weight, use two sentences. |
| "It's important to note", "It's worth noting", "Generally speaking", "In many cases", "At its core", "Simply put" | Hedging preamble. Adds tokens, adds nothing. | Delete it and start with the claim. |
| leverage, delve, utilize, robust, seamless, powerful, comprehensive, cutting-edge, best-in-class | Marketing vocabulary. | use, dig into, use. For the adjectives: delete them. |
| "studies show", "it is widely considered", "experts agree" | Vague attribution. Unfalsifiable. | Name the source, or give the measurement. |
| A closing sentence that states the moral | "And that is why grouping matters." The reader got there. | Stop at the last fact. |
| Three-item lists written for rhythm | "fast, simple, and reliable" | Say the one that is true. |

## Voice

The ban list catches spellings. These are the habits under them.

| Habit | Reads like | Write |
|---|---|---|
| Circling a word you could use | "somewhere to put a decision that is neither shipped nor personal" | "team decisions" |
| Mechanism when the consequence is the point | "the loader deduplicates by resolved file path, so both load" | "both load" |
| Contrast with what you rejected | "X rather than Y" | "X" |
| Commandment mood | `never` in every rule | what happens |
| Aphorism | "A gate that cannot fail is not a gate" | "Every gate must be able to fail" |
| Clause bolted on with "which is" | "...and that is the operator's call" | end the sentence |
| One claim, twice | "a guess", then "a guess wearing a number" | once |

Contractions are fine. Avoiding them is its own tell.

Worked example, 48 words to 27:

> A project read by two people needs somewhere to put a decision that is
> neither shipped nor personal. Skill precedence cannot serve that: the loader
> deduplicates by resolved file path and never by name, so a personal skill and
> a project skill of the same name both load and neither shadows the other.

> If two people collaborate, decisions are team decisions (not shipped, not
> personal). Skill precedence doesn't cut it: two skills of one name both load.

Per 10k words, measured against 9,660 words written by hand: `rather than` 3,
`which is`/`that is` 6, `the thing that`/`is what` 4, `never` 24. Files here
ran three to six times those.

**No checker counts them.** Whether an instance earns its place is a judgment.
`wrap-up` reads what a session added.

## Required

**Front-load.** The first sentence under a heading answers the question the
heading asks. Everything after it is detail.

**Vary sentence length.** Uniform 18 to 24 word sentences, paragraph after
paragraph, is the single most reliable sign of generated prose. Short sentences
are allowed to be very short.

**Name things, never point at them.** No "as mentioned above", no "the approach
described earlier", no bare "this" or "it" reaching across a heading. An agent
may retrieve one section without the ones around it, so every section has to
stand alone. Write `clip_to_not_afk()`, not "the helper".

**Numbers, not adjectives.** "Full recompute over 14 months, 41k sessions, 1.8s"
beats "fast". Cite the measurement or drop the claim.

**Tables for parallel facts.** Three or more things with the same shape belong
in a table. Prose that lists them costs more tokens and reads worse.

**Active voice, present tense, second person** for anything instructional.
"Run `uv sync`", not "`uv sync` should be run".

**One idea per paragraph.** Four sentences is a long paragraph here.

**Density stays, words get cut.** A shorter draft that has lost a fact is a
worse draft. Cut the phrasing, keep the coverage.

## Where a fact belongs

A fact belongs in a skill only if it is needed **while performing that skill**.
The test: would a session on day 30 need it? If yes, a first-run skill is the
wrong home, because it will not be read again.

A fact a machine can check belongs in code, not in prose anywhere. The gap
tolerance the sessionizer uses is a default in `settings`, and writing the
number into a document would create a second source. The copy is always the one
that drifts.

A fact stated in two files is a fact that will disagree with itself. If both
copies are load-bearing, test that they agree.

## Code comments

A comment explains the code. It never narrates how the code came to exist.

The test: is the comment still true and useful in a year, to a reader who
cannot see the conversation that produced it?

**Keep.** Facts about the code that are not visible from the lines around it.

- Invariants and contracts. "Every `ts_utc` sorts lexicographically, so range
  queries can use string comparison."
- Units and scales. `duration_s` is seconds, always float.
- Why an obvious alternative fails, stated as a property. "Dropping a window
  event that overlaps AFK loses the non-AFK part of it, so the sum comes out
  low. Clip instead."
- Non-local coupling. "The rule engine and the JSON schema in the project editor
  must accept the same op set."
- Anything that looks like a bug and is deliberate.

**Cut.** Anything that dates.

- Measurements of data that changes. "287 of 890 sessions were unassigned."
- Discovery narrative. "Found while looking at last Tuesday."
- Session context, and "this used to be X".
- An issue number standing in place of the reason. `# see #N` gives a reader
  nothing to act on without leaving the file, and the link outlives the context
  that made it readable.
- Restating the line below it.

**A reference appended to an explanation that already stands is fine.** Add one
when the history behind a line runs deep enough to be worth finding. Delete the
reference and nothing essential should go with it. A comment that stops making
sense without the link is unfinished.

```python
# GOOD  A browser window event and its web events describe the same seconds.
#       Counting both double-bills every focused browsing minute. (#N)

# BAD   Browser handling is subtle here, see #N.
```

Durable history already has a home: the commit, the PR, the issue. Those are
dated and stay accurate. A comment that copies them rots in place.

## An instruction carries no history

**The cut list above applies to every file an agent loads in order to act**:
the router, the guides, the skills, the rules. It has lived under a comments
heading and it was never only about comments.

An instruction says what to do. Four things say how it came to exist:

- Provenance. "Extracted from X, where every rule was used on real work."
- Current state. "Not built yet." "Until then a person checks it."
- The reasoning already settled. A finding belongs in a decision record.
- The file's editorial policy about itself.

The test: delete the sentence. When the reader still knows what to do, it was
history.

## Enforced mechanically

`bin/check-style` gates the unambiguous half: em dashes, the banned
phrase list, the "not X, Y" shapes. Run it locally, and CI runs it on every PR.

A file that has to quote a banned pattern in order to define it opts out with
`style-check: exempt` in its first 20 lines, plus the reason. Two files use it:
`bin/check-style` and this guide.

Cadence, front-loading and vocabulary are review matters. A checker that
guessed at them would produce false positives, and a gate people learn to
ignore is worse than no gate.

## Length

Long is fine when the length is content. `WORKFLOW.md` earns its by carrying
that much process. A line count is not a target in either direction.

The test, per paragraph: what does this tell a reader that the one above did
not? No answer, cut it. Two answers, it is two paragraphs.

A rewrite that came out longer than what it replaced, for a reason that was not
more coverage, is padding.
