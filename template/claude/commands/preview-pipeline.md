# Preview Pipeline — Dry Run of /write-paper

Show exactly what the autonomous pipeline will do without executing it.

## Instructions

1. **Read `.paper.json`** for topic, venue, target words, model
2. **Detect domain** from topic (same logic as /write-paper)
3. **Check current state**:
   - Does `research/` exist with files? (research already done)
   - Does `main.tex` have section content? (writing already started)
   - Does `reviews/` exist? (reviews already done)
   - What's the current word count per section?
   - How many references in `references.bib`?
4. **Generate execution plan**:

```
Pipeline Preview for: "[topic]"
Domain detected: [domain]
Venue: [venue or "generic"]
Model: writing=opus, research/review=sonnet

STAGE 1: DEEP RESEARCH
  ├── Agent: Field Survey          [SKIP — research/survey.md exists]
  ├── Agent: Methodology Dive      [RUN — no research/methods.md]
  ├── Agent: Empirical Evidence    [RUN — no research/empirical.md]
  ├── Agent: Theoretical Found.    [RUN — no research/theory.md]
  ├── Agent: Gap Analysis          [BLOCKED — waiting on above]
  └── Agent: Bibliography Builder  [RUN — only 5 refs in .bib]
  Skills: literature-review, pubmed-database, arxiv-database, ...

STAGE 2: THESIS & OUTLINE          [RUN — no outline in main.tex]
  Skills: scientific-writing, venue-templates

STAGE 3: WRITING
  ├── Introduction    (0/1200 words) [RUN]
  ├── Related Work    (0/2000 words) [RUN]
  ├── Methods         (0/2500 words) [RUN]
  ├── Results         (0/2000 words) [RUN]
  ├── Discussion      (0/1500 words) [RUN]
  ├── Conclusion      (0/600 words)  [RUN]
  └── Abstract        (0/300 words)  [RUN — after all sections]
  Skills: scientific-writing, statistical-analysis

STAGE 4: FIGURES & TABLES          [RUN]
  Skills: scientific-visualization, matplotlib

STAGE 5: QUALITY ASSURANCE (up to 5 iterations)
  ├── Technical Review              [RUN]
  ├── Writing Review                [RUN]
  └── Citation Review               [RUN]
  → Revision after each round
  Skills: peer-review, citation-management

STAGE 6: FINALIZATION             [RUN]

Estimated agents: ~18-25
Estimated duration: 2-4 hours
```

5. **Do NOT execute anything.** This is preview only.

$ARGUMENTS
