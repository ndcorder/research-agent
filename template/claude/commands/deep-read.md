# Deep Read — Read Sources and Enrich Extracts

Read the full text of cited papers and rewrite their source extracts with comprehensive, topic-relevant content. Optionally updates research files where these sources are mentioned.

This is the standalone version of Stage 1e from `/write-paper`. Use it on existing papers to retroactively enrich source extracts after acquiring PDFs.

## Instructions

**Read `pipeline/stage-1e-deep-read.md` now.** This command executes the same core logic defined there (Phases 1-3). The stage file is the authoritative reference for agent prompts, reading strategy, and output format.

### Execute Stage 1e

Run Phases 1-3 from `stage-1e-deep-read.md`:

1. **Phase 1: Identify** — find all sources with PDFs in `attachments/`, check for prior deep reads
2. **Phase 2: Spawn agents** — one Sonnet 1M agent per source, all in parallel, each rewrites its source extract
3. **Phase 3: Verification** — spot-check results, rebuild knowledge graph if available

### Additional Steps (standalone-only)

These steps run AFTER all deep-read agents have completed. They are specific to `/deep-read` and not part of the `/write-paper` pipeline.

**Update Research Files**

For each source that was deep-read, search the research files for mentions of that source and patch them with richer detail:

1. Read all `.md` files in `research/` (excluding `research/sources/`, `research/knowledge/`, `research/provenance.jsonl`, and `research/log.md`)
2. For each deep-read source, search these files for mentions by:
   - BibTeX key (e.g., `smith2024`)
   - First author surname
   - Paper title (or significant substring)
3. Where a mention is found, check if the surrounding text is thin or inaccurate compared to what the deep read revealed. If so, patch the text with richer detail — add specific findings, correct inaccuracies, flesh out vague references
4. Do NOT restructure or rewrite the research files wholesale — make targeted, surgical patches only

**Important**: Process research file updates **sequentially** (not in parallel) to avoid write collisions on shared files. Multiple sources may be mentioned in the same paragraph.

**Update Claims Matrix** (if `research/claims_matrix.md` exists)

1. For each deep-read source, find claims in the matrix that cite this source
2. Check whether the deep read revealed stronger or weaker evidence than originally recorded
3. Update evidence notes, warrant quality assessments, and rebuttal references as needed
4. Recompute evidence density scores for affected claims using the scoring model from `/write-paper` Stage 2 step 5

**Provenance Logging**

For each research file or claims matrix update, append to `research/provenance.jsonl`:
```json
{"ts":"[ISO-8601]","stage":"deep-read","agent":"deep-read-consolidation","action":"revise","target":"[file path]","reasoning":"Updated with richer detail from deep-read of [KEY]","sources":["[KEY]"],"diff_summary":"[one-line description of change]"}
```

**Update Source Manifest**

After all work is complete (deep-read agents + research file patches + claims matrix updates), rebuild the manifest:
```bash
python3 scripts/update-manifest.py
```

## Arguments

$ARGUMENTS

If no arguments given, deep-read ALL sources with PDFs in `attachments/`.
If one or more BibTeX keys are given (space-separated), deep-read only those sources. Each must have a PDF in `attachments/<key>.pdf`.
If `--force` is passed, re-read ALL sources even if they already have `Deep-Read: true`. Also pass `--force` to `parse-pdf.py` to regenerate markdown files.
