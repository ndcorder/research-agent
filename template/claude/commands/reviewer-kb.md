---
description: "Build and query the reviewer defense knowledge base"
model: sonnet
---

# Reviewer Defense Knowledge Base

Build, refresh, or query the reviewer defense knowledge base for `/respond-to-reviewers`.

## Subcommands

- **prepare** — Parse `research/claims_matrix.md`, `research/assumptions.md`, and
  `research/methodology-notes.md` into structured narrative documents under
  `research/prepared/`. If `methodology-notes.md` does not exist, a template is
  generated for the author to fill in. Must be run before `build`.

- **build** — Run `prepare` then call `python scripts/knowledge.py build` to ingest
  all prepared documents alongside source extracts and parsed PDFs. Use this for a
  full (re)build of the knowledge graph including reviewer-defense material.

- **refresh** — Incremental update. Re-prepares only files whose source has changed
  (checked by mtime), then calls `python scripts/knowledge.py update` to ingest new
  documents without a full rebuild. Use after editing the claims matrix or assumptions.

- **defense-brief** — Pre-compute a structured defense for every claim in the claims
  matrix. Runs `evidence-for`, `evidence-against`, and targeted queries against the
  knowledge graph for each claim, then assembles the results into:
  - `research/prepared/defense/defense-brief.md` — full brief
  - `research/prepared/defense/claim-C{N}.md` — one sheet per claim
  Requires a built knowledge graph (`build` must have run first).

- **status** — Report the current state of the knowledge graph and prepared documents:
  entity/relationship counts, last build timestamp, document counts by stream, and
  whether the defense brief exists and how old it is.

## Instructions

Run the command the user requested:

```bash
python scripts/reviewer-kb.py $ARGUMENTS
```

Stream the output to the user as it runs. When the command finishes, summarize:

- For **prepare**: how many files were written to each `research/prepared/` subdirectory
- For **build**: entity count and relationship count from the graph summary
- For **refresh**: which source files were re-prepared and the graph update summary
- For **defense-brief**: how many claim sheets were generated and the path to the full brief
- For **status**: print the full status report as-is

If the script exits with a non-zero code, report the error and suggest the likely fix
(e.g., "Run `build` before `defense-brief`", or "Set `OPENROUTER_API_KEY` to enable
knowledge graph construction").

## Arguments

$ARGUMENTS
