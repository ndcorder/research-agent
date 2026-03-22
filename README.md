# research-agent

Autonomous research paper writing toolkit for Claude Code. Creates fully-structured LaTeX paper projects and writes journal-quality papers using multi-agent orchestration.

## Quick Start

```bash
# Install (symlink to PATH)
ln -s $(pwd)/create-paper ~/.local/bin/create-paper
ln -s $(pwd)/write-paper ~/.local/bin/write-paper

# Create and write a paper
create-paper my-paper "A survey on large language model reasoning" --venue arxiv
# → stamps out project, clones 177 scientific skills, asks to launch pipeline

# Or create first, write later
create-paper my-paper
cd my-paper
claude
# then type: /write-paper A survey on LLM reasoning
```

## What It Does

`create-paper` stamps out a new project with:
- LaTeX template configured for your target venue
- 177 scientific skills (literature review, citation management, statistical analysis, etc.)
- 15 slash commands for paper writing, research, review, and submission
- Pre-configured tool permissions for autonomous operation

`/write-paper` orchestrates multi-hour autonomous writing using Claude Code agents:

```
Stage 1: Deep Research         4-5 parallel agents search literature
Stage 2: Thesis & Outline      Define contribution, structure the paper
Stage 3: Section Writing        Sequential agents, 1000-2500 words each
Stage 4: Figures & Tables       Ensure adequate visual elements
Stage 5: Quality Assurance      3 parallel reviewers + revision loop (up to 5x)
Stage 6: Finalization           Polish, compile, report
```

## Venues

```bash
create-paper my-paper "topic" --venue <venue>
```

| Venue | Format | Citation Style | Page Limit |
|-|-|-|-|
| `generic` | Standard article (default) | natbib | none |
| `ieee` | IEEEtran two-column | numeric | 8 |
| `acm` | acmart sigconf | natbib | 12 |
| `neurips` | NeurIPS single-column | natbib | 9 |
| `nature` | Nature family (Results→Methods) | numeric-superscript | none |
| `arxiv` | arXiv preprint | natbib | none |
| `apa` | APA 7th edition | apacite | none |

## Commands

### Autonomous Pipeline
| Command | Description |
|-|-|
| `/write-paper <topic>` | Full autonomous pipeline (1-4 hours) |
| `/preview-pipeline` | Dry run — show what will execute |
| `/status` | Progress dashboard (word counts, refs, stage) |

### Writing
| Command | Description |
|-|-|
| `/init <topic>` | Quick single-pass generation |
| `/outline <section>` | Structured section outline |
| `/revise-section <section>` | Rewrite with feedback |

### Research & References
| Command | Description |
|-|-|
| `/search-literature <query>` | Find relevant papers |
| `/add-citation <DOI or title>` | Add BibTeX entry |
| `/ingest-papers` | Import PDFs from `attachments/` |
| `/cite-network` | Citation coverage analysis |

### Data & Figures
| Command | Description |
|-|-|
| `/analyze-data <file>` | Statistical analysis + figure generation |

### Quality & Build
| Command | Description |
|-|-|
| `/review` | Comprehensive manuscript review |
| `/compile` | Build PDF, fix errors |
| `/clean` | Remove build artifacts |

### Submission
| Command | Description |
|-|-|
| `/prepare-submission` | Anonymized version, cover letter, supplementary |

## Project Structure (generated)

```
my-paper/
├── main.tex              # LaTeX document (venue-formatted)
├── references.bib        # BibTeX references
├── .paper.json           # Topic, venue, authors, config
├── .venue.json           # Venue formatting rules
├── figures/              # Generated figures
├── attachments/          # Reference PDFs, datasets
├── research/             # Literature research outputs (auto-generated)
├── reviews/              # Review feedback (auto-generated)
├── submission/           # Submission package (via /prepare-submission)
├── .paper-state.json     # Pipeline checkpoint state
├── .paper-progress.txt   # Human-readable progress (tail from another terminal)
└── .claude/
    ├── CLAUDE.md          # Project instructions
    ├── settings.local.json # Tool permissions
    ├── commands/          # 15 slash commands
    └── skills/ → vendor/  # 177 scientific skills
```

## Configuration (.paper.json)

```json
{
  "topic": "Your paper topic",
  "venue": "generic",
  "model": "claude-sonnet-4-6",
  "target_words": 8000,
  "max_revisions": 3,
  "authors": [
    {
      "name": "First Author",
      "affiliation": "Department, University",
      "email": "author@example.com",
      "orcid": "0000-0000-0000-0000"
    }
  ],
  "keywords": ["keyword1", "keyword2"],
  "funding": "Grant details",
  "conflicts": "None declared",
  "data_availability": "Available at ...",
  "code_availability": "https://github.com/..."
}
```

## Monitoring Long Runs

While `/write-paper` runs (1-4 hours), monitor from another terminal:

```bash
# Watch progress
cat my-paper/.paper-progress.txt

# Check word count
wc -w my-paper/main.tex

# See research outputs
ls my-paper/research/

# See review feedback
ls my-paper/reviews/
```

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (CLI)
- LaTeX distribution with `pdflatex` and `latexmk`
- Python 3.10+
- Git

## Skills

177 scientific skills from [claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills) are included as a git submodule. They cover:

- Scientific writing, literature review, citation management, peer review
- Database access: PubMed, arXiv, bioRxiv, ChEMBL, UniProt, KEGG, and 30+ more
- Analysis: statistical analysis, exploratory data analysis, scikit-learn, PyTorch
- Visualization: matplotlib, seaborn, plotly, scientific schematics
- Domain tools: RDKit, BioPython, Scanpy, PyMatGen, and 100+ more

## License

MIT
