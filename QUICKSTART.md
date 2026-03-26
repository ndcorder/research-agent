# Quick Start

Three commands from zero to paper.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI (`claude`)
- LaTeX (`pdflatex` + `latexmk`)
- Python 3.10+

## Install

```bash
git clone https://github.com/your-org/research-agent
cd research-agent
ln -s $(pwd)/create-paper ~/.local/bin/create-paper
ln -s $(pwd)/write-paper ~/.local/bin/write-paper
```

## Your First Paper

```bash
create-paper my-paper "A survey on LLM reasoning" --venue arxiv
cd my-paper
write-paper
```

## What Happens Next

The pipeline runs autonomously for 1-4 hours. It will:

- Launch 5+ parallel research agents across academic databases
- Build a thesis, contribution statement, and claims-evidence matrix
- Write each section with dedicated Opus-tier agents
- Run parallel QA review (3 agents) in iterative loops
- Compile a finalized, citation-traced LaTeX PDF

Output: `main.pdf` with full provenance (every paragraph traced to sources).

## Optional: Improve the Paper

```bash
# Inside the paper directory, launch iterative refinement
claude "/auto"
```

## Optional: Better Results

```bash
# Knowledge graph (richer synthesis) -- requires OpenRouter
export OPENROUTER_API_KEY=your-key

# Adversarial AI review from OpenAI Codex
npm i -g codex-bridge

# 200M+ institutional repository papers (free)
export CORE_API_KEY=your-key   # Register at https://core.ac.uk/services/api
```

## Need More?

- Full docs: [README.md](README.md)
- Diagnostics: `claude "/health"` inside a paper project
