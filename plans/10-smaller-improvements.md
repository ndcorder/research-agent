# Plan 10: Smaller High-Value Improvements

A collection of five independent improvements that don't warrant individual plans but each add significant value. These can be implemented in any order.

---

## 10a: Abstract-First Writing Option

### Problem
Some researchers (and some venues) benefit from writing the abstract first as a forcing function for clarity — if you can't summarize the contribution in 250 words, you don't understand it well enough. The current pipeline always writes the abstract last (Stage 3, Order 7).

### Design
Add an `abstract_strategy` field to `.paper.json`:
```json
{
  "abstract_strategy": "first" | "last"  // default: "last"
}
```

When `"first"`:
1. After Stage 2 (planning), write a **draft abstract** based on the thesis, outline, and claims matrix
2. Use this draft abstract as a north star for all writing agents — pass it as context with: "The abstract promises the following. Ensure your section delivers on these promises."
3. After all sections are written (Stage 3 complete), **rewrite the abstract** to match the actual content (same as the current final abstract step)

This way the abstract serves as an alignment tool during writing without being the final version.

### Files to Modify
- `template/claude/pipeline/stage-3-writing.md` — Add abstract-first logic with `.paper.json` check

---

## 10b: Response-to-Reviewers Command

### Problem
After a paper goes through human peer review (journal/conference submission), authors must write a point-by-point response addressing each reviewer comment, describing changes made, and justifying any comments not addressed. This is tedious and follows a very specific format. The pipeline has no support for this post-submission workflow.

### Design
New command: `/respond-to-reviewers`

Input: User pastes reviewer comments (or points to a file in `attachments/reviews/`)

Workflow:
1. **Parse reviewer comments** — Extract individual points from each reviewer, numbered
2. **Classify each point**: CRITICAL (must address), MAJOR (should address), MINOR (can address), PRAISE (acknowledge)
3. **Map to sections** — Identify which section(s) of main.tex each comment refers to
4. **For each CRITICAL and MAJOR point**:
   - Determine if the comment is valid (cross-reference with source extracts, claims matrix)
   - Draft a response explaining what was changed
   - Draft the actual change to main.tex (staged, not applied until user approves)
5. **Generate response document** (`response_to_reviewers.tex` or `.md`):
   ```
   We thank the reviewers for their constructive feedback. Below we address each point.

   ## Reviewer 1

   > R1.1: "The authors claim X but provide insufficient evidence..."

   **Response**: We appreciate this observation. We have strengthened the evidence for this claim by [specific change]. See Section 3.2, paragraph 3 (highlighted in blue in the revised manuscript).

   > R1.2: "The comparison with baseline Y is missing..."

   **Response**: We have added a comparison with Y in Table 2...
   ```
6. **Generate tracked-changes manuscript** — A version of main.tex with `\added{}` and `\deleted{}` commands (using the `changes` LaTeX package) showing exactly what was modified

### Files to Create
- `template/claude/commands/respond-to-reviewers.md`

### Files to Modify
- `template/claude/CLAUDE.md` — Add command to manual commands list

---

## 10c: PRISMA Flowchart for Systematic Reviews

### Problem
For systematic review or meta-analysis papers, PRISMA (Preferred Reporting Items for Systematic Reviews and Meta-Analyses) flowcharts are required by most journals. The research log (`research/log.md`) already contains the raw data (searches performed, results found, papers included/excluded), but this isn't formatted as a PRISMA diagram.

### Design
Add an option to the pipeline that generates a PRISMA flowchart from the research log.

1. **Detection**: If the paper topic contains "systematic review", "meta-analysis", "scoping review", or "literature review", auto-enable PRISMA generation
2. **Data extraction**: Parse `research/log.md` for:
   - Number of database searches and results per database
   - Number of papers after deduplication
   - Number screened (title/abstract)
   - Number assessed for eligibility (full text)
   - Number included in final review
   - Exclusion reasons at each stage
3. **Generate TikZ PRISMA flowchart**: Standard 4-phase PRISMA 2020 format
4. **Add to main.tex** as a figure in the Methods section

### Files to Create
- `template/claude/commands/prisma-flowchart.md` — Standalone command
- Add PRISMA logic to pipeline for auto-detection

### Files to Modify
- `template/claude/pipeline/stage-4-figures.md` — Auto-generate PRISMA if systematic review detected

---

## 10d: Preprint Scooping Check

### Problem
The research and writing process takes 1-8 hours. In fast-moving fields, a preprint posted during the writing process could scoop the contribution. The novelty check (Stage 2d) runs before writing, but by Stage 6 (finalization) the landscape may have changed.

### Design
Add a **pre-finalization scooping check** at the start of Stage 6:

```
Before finalizing, search for preprints posted in the last 14 days on the same topic:
1. Search arXiv (via Perplexity or API) for: [paper topic keywords] posted:last_14_days
2. Search bioRxiv/medRxiv (if biomedical) for recent preprints
3. Search Semantic Scholar for papers with publicationDate > [pipeline start date from .paper-state.json]

For each potentially conflicting preprint:
1. Read the abstract
2. Assess overlap with our contribution
3. If HIGH overlap: STOP and alert the user
4. If MEDIUM overlap: note in the finalization report — the authors should cite it and differentiate
5. If LOW overlap: note for awareness only
```

Add to the finalization report:
```markdown
## Scooping Check
- Searched arXiv and [domain] preprint servers for work posted since [pipeline start date]
- Found [N] potentially relevant preprints
- [NONE with significant overlap / One preprint with medium overlap: cite and differentiate]
```

### Files to Modify
- `template/claude/pipeline/stage-6-finalization.md` — Add scooping check before final polish

---

## 10e: Multi-Paper Shared Knowledge Base

### Problem
A researcher writing their second paper on a related topic must re-discover the same literature from scratch. The knowledge graph, source extracts, and research files are all per-paper. A shared knowledge base across papers in the same research area would avoid redundant research and ensure consistent terminology.

### Design
This is the most complex sub-improvement. Keep it simple for v1:

1. **Shared sources directory**: `~/.research-agent/shared-sources/` (outside any paper project)
2. **Export command**: `/export-sources` — copies `research/sources/*.md` and `references.bib` entries to the shared directory, tagged with the paper topic and date
3. **Import command**: `/import-sources <topic>` — searches the shared directory for sources related to a topic, copies relevant ones into the current paper's `research/sources/`
4. **Pipeline integration**: At the start of Stage 1, check the shared directory for existing sources on the topic. Present a count: "Found [N] source extracts from previous papers on related topics. Import them? (This will pre-populate your bibliography.)"

The shared knowledge base is NOT a shared knowledge graph (too complex for v1). It's just a shared pool of source extracts that can be imported to jump-start research.

### Files to Create
- `template/claude/commands/export-sources.md`
- `template/claude/commands/import-sources.md`

### Files to Modify
- `template/claude/pipeline/stage-1-research.md` — Stage 1 setup: check for shared sources
- `template/claude/CLAUDE.md` — Document shared knowledge base

---

## Acceptance Criteria (per sub-improvement)

### 10a: Abstract-First
- [ ] `.paper.json` supports `abstract_strategy` field
- [ ] Draft abstract written after Stage 2 when strategy is "first"
- [ ] Draft abstract passed to all writing agents as alignment context
- [ ] Final abstract still rewritten at the end of Stage 3

### 10b: Response-to-Reviewers
- [ ] `/respond-to-reviewers` command exists
- [ ] Parses reviewer comments into numbered points
- [ ] Classifies points by severity
- [ ] Generates point-by-point response document
- [ ] Drafts main.tex changes (not auto-applied)
- [ ] Generates tracked-changes version using `changes` package

### 10c: PRISMA Flowchart
- [ ] Auto-detected for systematic review papers
- [ ] Parses research log for search statistics
- [ ] Generates TikZ PRISMA 2020 flowchart
- [ ] Adds figure to Methods section

### 10d: Preprint Scooping Check
- [ ] Runs at start of Stage 6
- [ ] Searches arXiv and domain preprint servers for recent work
- [ ] Assesses overlap level (HIGH/MEDIUM/LOW)
- [ ] Stops pipeline for HIGH overlap
- [ ] Reports findings in finalization report

### 10e: Multi-Paper Shared Knowledge Base
- [ ] `/export-sources` copies sources to shared directory
- [ ] `/import-sources` searches and imports from shared directory
- [ ] Stage 1 checks for existing shared sources on the topic
- [ ] Source extracts maintain provenance (which paper they came from)
