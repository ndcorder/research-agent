# Lay Summary — Generate Plain-Language and Short-Form Summaries

Generate accessible summaries of the paper for different audiences and formats.

## Instructions

Read `main.tex` completely — understand the full paper before summarizing.

### Generate these summaries:

#### 1. Lay Summary (200-300 words)
For non-expert audiences. Required by many journals (Nature, PLOS, eLife, etc.).
- No jargon — explain technical terms in plain language
- Focus on: what problem, why it matters, what was found, what it means for society
- Use analogies where helpful
- Avoid: acronyms, equations, statistical terminology
- Write at a high school reading level

#### 2. Tweet Thread (3-5 tweets, 280 chars each)
For academic Twitter/social media promotion.
- Tweet 1: Hook — the key finding in one compelling sentence
- Tweet 2-3: Context and method in accessible terms
- Tweet 4: Key result with a specific number
- Tweet 5: Why it matters + link placeholder [LINK]
- Use thread numbering (1/5, 2/5, etc.)

#### 3. Press Release Paragraph (100-150 words)
For university press offices and science journalists.
- Lead with the most newsworthy finding
- Include a quotable statement from the "lead author"
- Mention the institution and journal
- End with broader significance

#### 4. Elevator Pitch (2-3 sentences)
The paper explained in 30 seconds to a non-specialist colleague.

#### 5. Technical Abstract Variant (if different from current abstract)
If the current abstract is very technical, generate an alternative that's more accessible while still being accurate. Compare with existing abstract.

### Output

Write all summaries to `research/summaries.md` with clear section headers.

Also add the lay summary to `main.tex` if the venue requires it (check `.venue.json` — Nature and medical journals typically require it). If adding to the paper, place it after the technical abstract with:
```latex
\section*{Plain Language Summary}
```

$ARGUMENTS
