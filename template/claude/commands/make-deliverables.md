# Make Deliverables — Generate All Output Formats in Parallel

Generate all downstream deliverables from the completed paper simultaneously.

## Instructions

Read `main.tex` completely. If it has no substantive content (only template placeholders or empty sections), report that the paper needs to be written first and stop.

Create the `deliverables/` directory if it does not exist:
```bash
mkdir -p deliverables
```

### Spawn 3 agents in parallel

Launch all three agents simultaneously. Each agent prompt below must include the full content of `main.tex` (paste it into the prompt). Also paste the content of `.venue.json`, `research/thesis.md`, and `research/summaries.md` if they exist.

**CRITICAL**: Each agent prompt must contain ALL the information the agent needs — agents have no shared context. Paste the file contents directly into the prompt, do not tell agents to read files themselves.

**Agent 1 — Lay Summary** (model: claude-sonnet-4-6[1m])
```
You are a science communicator. Generate accessible summaries of this research paper for different audiences.

Here is the paper:
[PASTE FULL main.tex CONTENT]

[IF .venue.json EXISTS: Here is the venue config: PASTE CONTENT]

Generate these four formats:

1. LAY SUMMARY (200+ words): For non-expert audiences. No jargon — explain technical terms in plain language. Focus on: what problem, why it matters, what was found, what it means. Use analogies where helpful. Write at a high school reading level.

2. SOCIAL MEDIA THREAD (3-5 posts, 280 chars each): Post 1: Hook — the key finding in one compelling sentence. Post 2-3: Context and method in accessible terms. Post 4: Key result with a specific number. Post 5: Why it matters + link placeholder [LINK]. Use thread numbering (1/5, 2/5, etc.).

3. PRESS RELEASE PARAGRAPH (100+ words): Lead with the most newsworthy finding. Include a quotable statement from the "lead author". End with broader significance.

4. ELEVATOR PITCH (2-3 sentences): The paper explained in 30 seconds to a non-specialist colleague.

RULES: Never use em dashes (—) or en dashes (–). Rewrite using commas, parentheses, colons, or separate sentences.

YOU MUST use the Write tool to write all summaries to research/summaries.md with clear section headers (# Lay Summary, # Social Media Thread, # Press Release, # Elevator Pitch).

If the venue is "nature" or the venue notes mention "plain language summary", also use the Edit tool to add the lay summary to main.tex after the abstract as: \section*{Plain Language Summary}
```

**Agent 2 — Slide Deck** (model: claude-sonnet-4-6[1m])
```
You are an academic presentation designer. Generate a structured markdown slide deck from this research paper.

Here is the paper:
[PASTE FULL main.tex CONTENT]

[IF .venue.json EXISTS: Here is the venue config: PASTE CONTENT]
[IF research/thesis.md EXISTS: Here is the thesis: PASTE CONTENT]

TALK LENGTH: Conference paper → 15-20 min (12-15 slides). Journal/seminar → 45 min (25-30 slides). Workshop/short paper → 8-10 min (8-10 slides). No venue info → default 15-20 min.

Generate markdown slides following this structure:
1. Title slide (1) — paper title, authors, affiliation, venue
2. The Problem (1-2) — what gap exists, why it matters
3. Background (1-2) — key prior work, just enough context
4. Our Approach (2-3) — method/contribution, reference figures from figures/ if they exist
5. Key Results (2-3) — most impactful findings, reference paper figures
6. Discussion (1) — what results mean, limitations briefly
7. Takeaway (1) — single memorable conclusion, future directions
8. Backup slides (2-3) — detailed methods, additional results, Q&A prep

Format each slide as:
---
## Slide N: Title
[Content — bullets or short text, minimal]

> Speaker notes: [What to say, transitions, timing hints]
---

RULES:
- One idea per slide. If more than 3 bullet points, split it.
- Reference existing figures from figures/ as ![](figures/filename.pdf). Do NOT invent figures.
- Every slide MUST have a Speaker Notes block.
- Never use em dashes (—) or en dashes (–).
- Slides are visual anchors, not scripts. Speaker notes carry the detail.

YOU MUST use the Write tool to write the complete slide deck to deliverables/slides.md.
```

**Agent 3 — Blog Post** (model: claude-sonnet-4-6[1m])
```
You are a science writer. Generate an accessible blog post from this research paper for a general technical audience.

Here is the paper:
[PASTE FULL main.tex CONTENT]

[IF research/thesis.md EXISTS: Here is the thesis: PASTE CONTENT]

TARGET: 1500-3000 words. Audience: technical professionals who are not specialists in this field.

STRUCTURE:
1. Hook (1-2 paragraphs) — Start with the problem in concrete terms. Use a specific example, statistic, or scenario.
2. Why this matters (1-2 paragraphs) — The gap in current approaches. Real consequences.
3. What we did (3-5 paragraphs) — The approach without jargon. Use analogies. Walk through the method as narrative.
4. What we found (2-3 paragraphs) — Lead with the most surprising finding. Use specific numbers and explain what they mean.
5. What's next (1-2 paragraphs) — Limitations honestly, future directions, open questions.
6. Further reading — [Read the full paper](LINK), related work, code/data repos.

RULES:
- Active voice. "We found" not "It was found."
- No academic hedging. "This suggests" is fine; "It could potentially be argued" is not.
- Never use em dashes (—) or en dashes (–). Rewrite with commas, parentheses, colons, or separate sentences.
- No bullet lists in the body. Write in paragraphs. Lists only in Further Reading.
- Every technical term gets a brief inline definition on first use.
- Concrete over abstract. "Processes 10,000 documents per minute" not "achieves significant throughput improvements."

YOU MUST use the Write tool to write the blog post to deliverables/blog-post.md.
```

### After all agents complete

Verify that all three output files exist:
- `research/summaries.md`
- `deliverables/slides.md`
- `deliverables/blog-post.md`

If any file is missing, report which agent failed to write its output.

Report a summary:
```
Deliverables generated:
- research/summaries.md — lay summary, social media thread, press release, elevator pitch
- deliverables/slides.md — [N] slides, ~[M] min talk
- deliverables/blog-post.md — [N] words
```

$ARGUMENTS
