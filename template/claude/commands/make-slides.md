# Make Slides — Generate Presentation Deck from Paper

Generate a structured slide deck from the completed paper, ready to adapt into any presentation tool.

## Instructions

Read `main.tex` completely. If it has no substantive content (only template placeholders or empty sections), report that the paper needs to be written first and stop.

Also read (if they exist):
- `.venue.json` — for talk length calibration
- `research/thesis.md` — for the core contribution statement
- `research/summaries.md` — for the elevator pitch (reuse as a starting point for the talk narrative)

### Talk length calibration

Check `.venue.json` for the venue type:
- **Conference paper** (NeurIPS, ICML, ACL, CHI, etc.): Target **15-20 minutes** (12-15 slides)
- **Journal article** or **seminar**: Target **45 minutes** (25-30 slides)
- **Short/workshop paper**: Target **8-10 minutes** (8-10 slides)
- **No venue info**: Default to 15-20 minutes

### Slide structure

Generate markdown slides following this academic talk structure:

```markdown
# [Paper Title]
**[Authors]** — [Venue/Year if known]

---

## Slide 1: The Problem
[What gap or question motivates this work? One clear statement + visual hook]

> Speaker notes: Open with the problem, not the solution. Make the audience care before explaining the approach.

---

## Slide 2: Why It Matters
[Real-world impact, practical consequences, or scientific importance]

> Speaker notes: ...
```

Follow this arc:
1. **Title slide** (1 slide) — paper title, authors, affiliation, venue
2. **The Problem** (1-2 slides) — what gap exists, why it matters
3. **Background** (1-2 slides) — key prior work, just enough context (not a full lit review)
4. **Our Approach** (2-3 slides) — method/framework/contribution, with a diagram placeholder if the paper has one in `figures/`
5. **Key Results** (2-3 slides) — most impactful findings, reference figures from the paper where possible (`![](figures/filename.pdf)`)
6. **Discussion** (1 slide) — what the results mean, limitations (briefly)
7. **Takeaway** (1 slide) — single memorable conclusion, future directions
8. **Backup slides** (2-3 slides) — detailed methods, additional results, anticipated Q&A answers

### Slide guidelines

- **One idea per slide.** If a slide has more than 3 bullet points, split it.
- **Use figures from the paper.** Reference existing files in `figures/` as image placeholders. Do not invent figures that don't exist.
- **Speaker notes are mandatory.** Every slide gets a `> Speaker notes:` block with what to say, transitions, and timing hints.
- **No em dashes.** Rewrite using commas, colons, or separate sentences.
- **Minimize text on slides.** Slides are visual anchors, not scripts. The speaker notes carry the detail.
- **Include transition cues.** Speaker notes should indicate how to bridge to the next slide.

### Output

Create the `deliverables/` directory if it does not exist:
```bash
mkdir -p deliverables
```

Write the slide deck to `deliverables/slides.md`.

Report: number of slides generated, estimated talk duration, and any figures referenced.

$ARGUMENTS
