# Make Blog Post — Generate Accessible Research Blog Post

Generate a blog post that explains the paper's contribution to a general technical audience.

## Instructions

Read `main.tex` completely. If it has no substantive content (only template placeholders or empty sections), report that the paper needs to be written first and stop.

Also read (if they exist):
- `research/summaries.md` — reuse the lay summary and elevator pitch as starting points
- `research/thesis.md` — for the core contribution statement
- `.venue.json` — for context on where the paper was submitted

### Writing guidelines

**Audience**: Technical professionals who are not specialists in your field. Think: a software engineer reading a research blog, a data scientist skimming for relevant methods, or a science journalist looking for a story.

**Tone**: Conversational but substantive. Not dumbed down, but no unexplained jargon. Every technical term gets a brief inline definition on first use (e.g., "transformer, a type of neural network architecture that processes input in parallel rather than sequentially").

**Length**: 1500-3000 words. Enough to convey the contribution meaningfully, not so much that casual readers bounce.

**Structure**:

1. **Hook** (1-2 paragraphs) — Start with the problem in concrete terms. Why should a non-specialist care? Use a specific example, statistic, or scenario.

2. **Why this matters** (1-2 paragraphs) — The gap in current approaches. What's broken, slow, missing, or unknown? Keep it grounded in real consequences.

3. **What we did** (3-5 paragraphs) — The approach, explained without jargon. Use analogies where they genuinely help (not forced). Walk through the method as a narrative, not a specification. Reference figures from the paper if they help (`![](figures/filename.pdf)`).

4. **What we found** (2-3 paragraphs) — Key results in plain terms. Lead with the most surprising or impactful finding. Use specific numbers but explain what they mean ("a 15% reduction in error rate, which translates to roughly 200 fewer misdiagnosed cases per year").

5. **What's next** (1-2 paragraphs) — Limitations (briefly, honestly), future directions, open questions.

6. **Further reading** — Link to the paper/preprint (placeholder: `[Read the full paper](LINK)`), related work worth reading, and any code/data repositories.

### Style rules

- **Active voice.** "We found" not "It was found."
- **No academic hedging.** "This suggests" is fine; "It could potentially be argued that this might suggest" is not.
- **No em dashes.** Rewrite using commas, parentheses, colons, or separate sentences.
- **No bullet point lists in the body.** Write in paragraphs. Lists are acceptable only in the "Further reading" section.
- **No abstract-style summary at the top.** The hook IS the summary.
- **Concrete over abstract.** "Processes 10,000 documents per minute" not "achieves significant throughput improvements."

### Output

Create the `deliverables/` directory if it does not exist:
```bash
mkdir -p deliverables
```

Write the blog post to `deliverables/blog-post.md`.

Report: word count and a one-line summary of the angle taken.

$ARGUMENTS
