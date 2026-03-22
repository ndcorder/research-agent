# Lay Summary — Generate Plain-Language and Short-Form Summaries

Generate accessible summaries of the paper for different audiences and formats.

## Instructions

Read `main.tex` completely — understand the full paper before summarizing. If `main.tex` has no substantive content yet (only template placeholders), report that the paper needs to be written first and stop.

### Generate these summaries:

#### 1. Lay Summary (200+ words)
For non-expert audiences. Required by many journals (Nature, PLOS, eLife, etc.).
- No jargon — explain technical terms in plain language
- Focus on: what problem, why it matters, what was found, what it means
- Use analogies where helpful
- Write at a high school reading level

#### 2. Social Media Thread (3-5 posts, 280 chars each)
For academic social media promotion.
- Post 1: Hook — the key finding in one compelling sentence
- Post 2-3: Context and method in accessible terms
- Post 4: Key result with a specific number
- Post 5: Why it matters + link placeholder [LINK]
- Use thread numbering (1/5, 2/5, etc.)

#### 3. Press Release Paragraph (100+ words)
For university press offices and science journalists.
- Lead with the most newsworthy finding
- Include a quotable statement from the "lead author"
- End with broader significance

#### 4. Elevator Pitch (2-3 sentences)
The paper explained in 30 seconds to a non-specialist colleague.

### Output

Write all summaries to `research/summaries.md` with clear section headers.

Also check `.venue.json` (if it exists) — if the venue is `nature` or the `notes` field mentions "plain language summary", add the lay summary to `main.tex` after the abstract:
```latex
\section*{Plain Language Summary}
```

$ARGUMENTS
