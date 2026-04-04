# Developer Guide

Guide for contributors extending the Research Agent pipeline, adding venue formats, creating commands, and understanding the codebase internals.

**Key concept**: This repo is the _template_, not a paper project. Paper projects are created elsewhere via `create-paper` and symlink the selected runtime scaffold back to `template/`. Changes to `template/` propagate instantly to all paper projects.

**Related docs**: [CONTRIBUTING.md](../CONTRIBUTING.md) for PR guidelines | [ARCHITECTURE.md](ARCHITECTURE.md) for system design | [SCRIPTS-REFERENCE.md](SCRIPTS-REFERENCE.md) for script CLI reference

## Repository Structure

```
research-agent/
├── create-paper              # Bash: stamps out new paper projects
├── write-paper               # Bash: launches the configured runtime
├── sync-papers               # Bash: migrates old projects to symlinks
├── template/
│   ├── claude/
│   │   ├── CLAUDE.md         # Workspace instructions (symlinked into projects)
│   │   ├── commands/         # Claude command wrappers
│   │   └── settings.local.json
│   ├── codex/
│   │   ├── AGENTS.md         # Codex runtime instructions
│   │   ├── commands/         # Codex command wrappers
│   │   └── pipeline/         # Symlink to shared pipeline
│   ├── shared/
│   │   ├── pipeline/         # Shared stage instructions
│   │   └── runtime-contract.md
│   ├── scripts/
│   │   ├── knowledge.py         # LightRAG knowledge graph builder
│   │   ├── quality.py           # Multi-dimensional paper quality scorer
│   │   ├── reviewer-kb.py       # Reviewer defense knowledge base builder
│   │   ├── research-story.py    # Provenance narrative generator
│   │   ├── verify-references.py # LaTeX reference integrity checker
│   │   ├── format_sentences.py  # LaTeX one-sentence-per-line formatter
│   │   ├── parse-pdf.py         # Docling-based PDF → markdown converter
│   │   ├── update-manifest.py   # Rebuilds research/source-manifest.json
│   │   ├── openrouter-fallback.py # LLM fallback routing
│   │   ├── pdf-cache.sh         # Shared PDF dedup cache
│   │   ├── ensure-venv.sh       # Python venv bootstrapper
│   │   └── requirements-knowledge.txt # Pinned deps for knowledge.py
│   ├── venues/               # 7 venue JSON configs
│   ├── main.tex              # Minimal LaTeX template
│   ├── references.bib        # Empty BibTeX template
│   └── gitignore
├── vendor/
│   ├── claude-scientific-skills/  # Submodule: 177 domain skills
│   └── praxis/                    # Submodule: scientific analysis toolkit
├── tests/
│   ├── run_all.sh               # Test runner (shell + pytest)
│   ├── test_structure.sh        # Template file existence checks
│   ├── test_prompts.sh          # Command/pipeline markdown linting
│   ├── test_schema.py           # .paper-state.json schema validator
│   ├── test_venues.py           # Venue JSON required fields
│   ├── test_commands.py         # Command file existence, model specs
│   ├── test_pipeline.py         # Pipeline stage headings, orchestrator coverage
│   ├── test_quality.py          # quality.py scoring logic
│   ├── test_knowledge.py        # Knowledge graph unit tests
│   ├── test_knowledge_queue.py  # Knowledge graph queue/streaming
│   ├── test_state_completeness.py  # State file completeness
│   ├── test_format_sentences.py # LaTeX formatter tests
│   ├── test_verify_references.py   # Reference verification tests
│   ├── test_reviewer_kb.py      # Reviewer KB builder tests
│   └── conftest.py              # Pytest fixtures
└── docs/
```

## How the Pipeline Works

### Orchestration Pattern

The runtime-specific `/write-paper` wrappers are compact orchestrators. They do not contain stage logic inline. Instead, they read each stage's instructions from the shared `pipeline/*.md` files on-demand:

```
Orchestrator reads pipeline/shared-protocols.md once at start
For each stage:
    1. Check .paper-state.json — skip if stage.done == true
    2. Read pipeline/stage-N-*.md from disk (fresh read, not cached)
    3. Execute the stage instructions
    4. Update .paper-state.json with results
    5. Update .paper-progress.txt
```

**Why on-demand reads?** Claude Code conversations can run for hours. Context compression may degrade instructions loaded early. Reading each stage file fresh at execution time ensures late stages (QA, finalization) get their full instructions.

### State Management

`.paper-state.json` tracks checkpoint state for resume-on-interrupt. Schema:

```json
{
    "topic": "string",
    "venue": "string",
    "started_at": "ISO-8601",
    "current_stage": "string",
    "stages": {
        "research": {"done": false, ...},
        "snowballing": {"done": false, ...},
        "writing": {
            "done": false,
            "sections": {
                "introduction": {"done": true, "words": 1250}
            }
        }
    }
}
```

See `tests/test_schema.py` for the full schema definition and validation logic.

### Agent Spawning

The orchestrator spawns agents using Claude Code's `Agent` tool. Key conventions:

- **Parallel agents** get separate output files (e.g., `research/survey.md`, `research/methods.md`)
- **Each agent prompt** includes the full tool fallback chain, source extract format, and provenance logging instructions (from `shared-protocols.md`)
- **Model selection**: Opus for writing/reasoning, Sonnet for research/review/mechanical tasks
- **Agent names** are descriptive for tracking: `field-survey-agent`, `technical-reviewer`, etc.

## Adding a New Venue

1. Create `template/venues/your-venue.json`:

```json
{
    "name": "Your Venue",
    "documentclass": "\\documentclass{article}",
    "packages": ["\\usepackage{natbib}"],
    "bibliography_style": "plainnat",
    "citation_style": "natbib",
    "citation_commands": {
        "parenthetical": "\\citep{key}",
        "narrative": "\\citet{key}"
    },
    "page_limit": null,
    "abstract_limit": 250,
    "blind_review": false,
    "sections": [
        "Introduction",
        "Related Work",
        "Methods",
        "Results",
        "Discussion",
        "Conclusion"
    ],
    "writing_guide": "Venue-specific writing instructions..."
}
```

2. Update `create-paper` to list the new venue in the help text (line ~53-60)
3. Test with `create-paper test-paper "Test topic" --venue your-venue`

**Key fields:**

| Field | Purpose |
|-|-|
| `documentclass` | LaTeX document class declaration |
| `packages` | Required LaTeX packages |
| `bibliography_style` | BibTeX style file name |
| `citation_style` | Citation package (`natbib`, `numeric`, etc.) |
| `page_limit` | Max pages for main content (`null` = unlimited) |
| `abstract_limit` | Max words for abstract |
| `blind_review` | Whether to anonymize the manuscript |
| `sections` | Ordered list of section names |
| `writing_guide` | Prose instructions for writing agents (tone, structure, conventions) |

## Adding a New Slash Command

1. Create `template/claude/commands/your-command.md`
2. Follow the existing pattern:

```markdown
# /your-command

Brief description of what this command does.

## Arguments

- `arg1` — Description (required/optional)

## Instructions

Step-by-step instructions for Claude to follow when this command is invoked.

1. Read relevant files
2. Perform the task
3. Output results
```

3. The command is automatically available in all paper projects (via symlink)

**Conventions:**
- Commands that spawn agents should specify the model tier
- Commands that modify the manuscript should log to `research/provenance.jsonl`
- Commands that read pipeline state should check `.paper-state.json`
- Use existing shared protocols (tool fallback, source extract format) where applicable

## Adding a New Pipeline Stage

1. Create `template/claude/pipeline/stage-N-your-stage.md` with full instructions
2. Update `template/claude/CLAUDE.md` to list the new stage in the project structure and pipeline description
3. Update `template/claude/commands/write-paper.md` to read and execute the new stage at the correct point
4. Add the stage to the schema in `tests/test_schema.py`
5. Update `.paper-state.json` checkpoint handling

**Stage file conventions:**
- Start with a heading (`# Stage N: Name`) and brief description
- Reference shared protocols by name (e.g., "Follow the Provenance Logging Protocol")
- Include agent prompts as fenced code blocks (the orchestrator pastes these into `Agent` tool calls)
- Specify the model tier for each agent
- Define checkpoint fields (what to save in `.paper-state.json`)
- Handle resume: check if the stage was already partially completed

## Modifying Shared Protocols

`pipeline/shared-protocols.md` contains reusable blocks that are pasted into agent prompts:

- **Codex Deliberation Protocol** — how to handle Codex feedback
- **Provenance Logging Protocol** — JSON format for provenance entries
- **Domain Detection & Skill Routing** — maps topics to database skills
- **Tool Fallback Chain** — ordered list of research tools
- **Source Extract Format** — template for `research/sources/*.md`
- **Semantic Scholar Rate Limiting** — API pacing rules

To add a new protocol:
1. Add a new section to `shared-protocols.md`
2. Include a fenced code block with the abbreviated instruction for agent prompts
3. Reference it in the relevant stage files

## Testing

### Full test suite

```bash
bash tests/run_all.sh
```

This runs all shell-based tests and then `pytest` on all Python test files. CI runs this on Python 3.12.

### Individual tests

```bash
# Structure: template file existence, symlink targets
bash tests/test_structure.sh

# Prompt linting: command/pipeline markdown syntax
bash tests/test_prompts.sh

# Schema: .paper-state.json and venue JSON validation
python3 -m pytest tests/test_schema.py tests/test_venues.py

# Commands: file existence, model specs, CLAUDE.md cross-references
python3 -m pytest tests/test_commands.py

# Pipeline: stage headings, prerequisites, orchestrator coverage
python3 -m pytest tests/test_pipeline.py

# Scripts: quality scorer, knowledge graph, formatter, references
python3 -m pytest tests/test_quality.py tests/test_knowledge.py tests/test_format_sentences.py tests/test_verify_references.py tests/test_reviewer_kb.py

# Validate a specific paper's state file
python3 tests/test_schema.py path/to/.paper-state.json
```

### Health Check

From within a paper project:

```bash
claude "/health"
```

Checks: LaTeX installation, API keys, Codex bridge, Praxis, knowledge graph dependencies, Python packages.

### Manual pipeline testing

```bash
# Dry run — shows the plan without executing
claude "/preview-pipeline"

# Run a standard paper (fastest)
create-paper test-paper "Test topic" --venue generic
cd test-paper
write-paper
```

## Submodules

### claude-scientific-skills

177 domain-specific research skills (literature search, database queries, analysis tools). Located at `vendor/claude-scientific-skills/`, symlinked to `.claude/skills/` in paper projects.

Update:
```bash
cd vendor/claude-scientific-skills
git pull origin main
cd ../..
git add vendor/claude-scientific-skills
git commit -m "update: scientific skills submodule"
```

### Praxis

Scientific data analysis toolkit with 50+ characterization techniques and 9 journal figure styles. Located at `vendor/praxis/`.

Update:
```bash
cd vendor/praxis
git pull origin main
cd ../..
git add vendor/praxis
git commit -m "update: praxis submodule"
```

## Key Design Decisions

### Why symlinks?

Paper projects symlink back to the template repo (`template/claude/`). This means:
- Updating a command or stage in the template instantly propagates to all paper projects
- No copy drift between projects
- `sync-papers` migrates older projects that used copies

### Why on-demand stage reads?

The pipeline reads `pipeline/*.md` files from disk at execution time rather than loading them all upfront. Long-running sessions (1-8 hours) cause Claude Code to compress early context. On-demand reads ensure every stage gets its full, uncompressed instructions.

### Why provenance?

Every action (write, revise, cut, expand) is logged to `research/provenance.jsonl`. This:
- Makes every claim traceable to its source
- Enables audit of what was actually read vs. cited
- Archives cut content so nothing is silently lost
- Supports `/provenance` queries for post-hoc analysis

### Why claims-evidence matrix?

The matrix (`research/claims_matrix.md`) forces explicit warrant, qualifier, and rebuttal for every major claim. This:
- Prevents unsupported assertions from reaching the final paper
- Guides writing agents on confidence language (STRONG vs. WEAK)
- Enables automated auditing (`/audit-claims`)
- Provides reviewer-ready evidence for every claim

### Why Codex deliberation protocol?

Codex feedback is never blindly accepted. The protocol (AGREE / PARTIALLY AGREE / DISAGREE) with one rebuttal round ensures genuine collaboration between AI systems rather than rubber-stamping. Unresolved disagreements are logged for the user to decide.
