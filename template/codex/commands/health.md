# Health Check — Codex Runtime

Diagnose Codex pipeline prerequisites and optional integrations.

## Instructions

Run shell checks and report a concise table with status, detail, and impact.

### Required

1. LaTeX: `which pdflatex` and `which latexmk`
2. Python: `python3 --version`
3. Git: `git --version`
4. Codex CLI: `codex --version`

### Optional

5. Knowledge Graph: `OPENROUTER_API_KEY` and `python3 -c "import lightrag" 2>/dev/null`
6. Codex Bridge: `which codex-bridge`
7. Praxis: check `vendor/praxis/scripts/`
8. CORE API key: `CORE_API_KEY`
9. NCBI API key: `NCBI_API_KEY`
10. Scientific skills: `.codex/skills/` exists and contains `SKILL.md` files

### Project State

11. `.paper.json`: show topic, venue, depth, runtime
12. `.paper-state.json`: show current stage if present
13. `research/source_coverage.md`: summarize counts if present
14. `research/knowledge/`: verify directory state if present

Warn prominently if any required check fails.
