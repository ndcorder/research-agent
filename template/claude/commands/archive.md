# Archive — Bundle All Research Artifacts for Browsing

Create a self-contained `archive/` directory with all research artifacts organized for easy browsing. This is automatically run at the end of `/write-paper` but can also be invoked manually at any time.

## Instructions

1. **Create the archive directory structure**:

```bash
mkdir -p archive/{paper,research,reviews,figures,data,metadata}
```

2. **Copy artifacts into organized subdirectories**:

### Paper (final outputs)
- Copy `main.tex` → `archive/paper/`
- Copy `main.pdf` → `archive/paper/` (if it exists — compile first if needed)
- Copy `references.bib` → `archive/paper/`

### Research (literature & analysis)
- Copy all files from `research/` → `archive/research/` (if directory exists)
  - This includes: survey.md, methods.md, empirical.md, theory.md, gaps.md, thesis.md, summaries.md, codex_thesis_review.md, praxis_analysis.md, data_analysis.md, reference_validation.md, reproducibility_checklist.md, and any other files
- Copy all files from `research/ingested/` → `archive/research/ingested/` (if exists — these are ingested paper summaries)
- Copy `research/sources/` → `archive/research/sources/` (if exists — raw source extracts per cited paper with provenance)
- Copy `research/log.md` → `archive/research/log.md` (if exists — full provenance trail of all searches)

### Reviews (QA feedback)
- Copy all files from `reviews/` → `archive/reviews/` (if directory exists)
  - This includes: technical.md, writing.md, completeness.md, codex_adversarial.md, consistency.md, claims_audit.md, and any other review files

### Figures (visual elements)
- Copy all files from `figures/` → `archive/figures/` (PDFs, PNGs, SVGs)
- Copy `figures/scripts/` → `archive/figures/scripts/` (if exists — reproducible figure generation code)

### Data (source materials)
- Copy all files from `attachments/` → `archive/data/` (if directory exists — user-provided PDFs, datasets, supplementary materials)

### Metadata (configuration & state)
- Copy `.paper.json` → `archive/metadata/`
- Copy `.venue.json` → `archive/metadata/` (if exists)
- Copy `.paper-state.json` → `archive/metadata/` (if exists)
- Copy `.paper-progress.txt` → `archive/metadata/` (if exists)

### Submission (if already prepared)
- Copy `submission/` → `archive/submission/` (if directory exists)

3. **Generate the browsable index** — create `archive/README.md`:

Write a comprehensive index file structured as follows:

```markdown
# Research Archive: [Paper Title]

> [One-line description from .paper.json topic field]

**Generated**: [current date]
**Venue**: [venue from .paper.json or .venue.json]
**Authors**: [from .paper.json]

---

## Paper

| File | Description |
|-|-|
| [paper/main.pdf](paper/main.pdf) | Final compiled manuscript |
| [paper/main.tex](paper/main.tex) | LaTeX source |
| [paper/references.bib](paper/references.bib) | Bibliography ([N] references) |

## Research Notes

[For each file in archive/research/, create a table row with:]
- Filename linked to path
- One-line description based on the file's content (read the first few lines to summarize)

## Review Feedback

[For each file in archive/reviews/, create a table row with:]
- Filename linked to path
- One-line summary of what the review covers

## Figures

[For each figure file, create a table row with:]
- Filename linked to path
- Caption or description (if determinable from main.tex \caption{} commands)

## Source Data

[For each file in archive/data/, create a table row with:]
- Filename linked to path
- File size and type

## Metadata

| File | Description |
|-|-|
| [metadata/.paper.json](metadata/.paper.json) | Paper configuration (topic, venue, authors) |
| [metadata/.venue.json](metadata/.venue.json) | Venue formatting requirements |
| [metadata/.paper-state.json](metadata/.paper-state.json) | Pipeline execution state & checkpoints |
| [metadata/.paper-progress.txt](metadata/.paper-progress.txt) | Human-readable progress log |

[Only include rows for files that actually exist]

## Key Findings

[Read research/survey.md and research/thesis.md. Write 3-5 bullet points summarizing:]
- The main research question
- The key contribution/thesis
- The most important findings or conclusions
- Any notable gaps or limitations identified

## Research Provenance

[If research/log.md exists, summarize:]
- Total number of searches conducted
- Tools/databases used (list unique tools from the log)
- Date range of research activity
- Any notable search failures or gaps

See [research/log.md](research/log.md) for the complete search trail.

## Source Extracts

[If research/sources/ has files, create a table:]

| Source | Paper | Key Finding |
|-|-|-|
| [sources/smith2024.md](research/sources/smith2024.md) | Smith et al. (2024) - [title] | [one-line key finding] |

[For each .md file in research/sources/, read the first few lines to populate the table]

## How to Use This Archive

- **Quick overview**: Read this README and the Key Findings above
- **Full paper**: Open `paper/main.pdf`
- **Deep dive into literature**: Browse `research/` — each file covers a different angle
- **Quality feedback**: Check `reviews/` — technical, writing, and completeness reviews
- **Reproduce figures**: See `figures/scripts/` for generation code
- **Raw data**: Source materials are in `data/`
- **Trace a claim**: Check `research/sources/` for the raw source, then `research/log.md` for how it was found
- **Answer questions**: Use `/ask <question>` to search across all artifacts
```

4. **Report** the archive contents:
   - Total number of files archived
   - Total size of archive directory
   - Path: `archive/`

## Important

- **Do not move or delete originals** — the archive is a copy, not a move
- **Overwrite if archive/ already exists** — `rm -rf archive/` first to ensure a clean archive
- **Skip missing directories gracefully** — only archive what actually exists
- **Read .paper.json** for title, authors, and venue to populate the README
- **Read main.tex** to extract figure captions for the index

## Arguments

$ARGUMENTS

Usage: `/archive` (archive current project)
