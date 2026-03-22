# Preview Pipeline — Dry Run of /write-paper

Show exactly what the autonomous pipeline will do without executing it.

## Instructions

1. **Read `.paper.json`** for topic, venue, target_words
2. **Read `.venue.json`** if present for section structure
3. **Detect domain** from topic (use the same domain keyword matching as `/write-paper`)
4. **Check current state**:
   - List files in `research/` (if any)
   - Count words per section in `main.tex` (strip LaTeX commands for approximation)
   - Count references in `references.bib`
   - Check if `.paper-state.json` exists and read completed stages
5. **Generate execution plan** showing:
   - Each stage and its sub-steps
   - For each: whether it will RUN (needs doing) or SKIP (already done)
   - Which skills will be invoked (verify they exist in `.claude/skills/`)
   - Model selection per agent (opus for writing, sonnet for research/review)
   - Current vs target word counts per section
   - **Compute estimates dynamically** based on how many stages need to run:
     - Research stage: ~15-20 min (5 agents)
     - Outline: ~5 min
     - Per section writing: ~5-10 min each
     - QA loop iteration: ~15 min
     - Total: sum of stages that will RUN

6. **Do NOT execute anything.** This is preview only.

$ARGUMENTS
