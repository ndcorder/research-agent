# Health Check — Diagnose Pipeline Prerequisites

Run a diagnostic check of all pipeline prerequisites and optional integrations. Reports what's available, what's missing, and what impact each missing component has.

## Instructions

Run the following checks and report results in a table. For each check, report: status (OK / MISSING / WARN), detail, and impact if missing.

### Required Prerequisites

1. **LaTeX**: Run `which pdflatex` and `which latexmk`. Both must exist.
   - MISSING impact: Pipeline cannot compile the paper. Fatal.

2. **Python**: Run `python3 --version`. Must be 3.10+.
   - MISSING impact: Knowledge graph and data analysis unavailable. Fatal for those features.

3. **Git**: Run `git --version`.
   - MISSING impact: No version control. Not fatal but strongly recommended.

4. **Claude Code**: Already running if you see this. Always OK.

### Optional Integrations

5. **Knowledge Graph (LightRAG)**:
   - Check: `OPENROUTER_API_KEY` env var set? Run `python3 -c "import lightrag" 2>/dev/null`.
   - OK: Key set AND lightrag importable
   - WARN: Key set but lightrag not installed (run `pip install lightrag-hku`)
   - MISSING: Key not set
   - Impact: Without this, the pipeline skips all knowledge graph queries at every stage. This removes ~40% of the evidence verification, contradiction detection, and entity coverage checks. The pipeline still works but produces weaker papers.

6. **Codex Bridge**:
   - Check: Run `which codex-bridge` or `npm list -g codex-bridge 2>/dev/null`.
   - MISSING impact: No adversarial AI review. The pipeline skips ~10 Codex integration points (research cross-check, thesis stress-test, section spot-checks, adversarial QA review, risk radar). Papers lose the second-opinion perspective.

7. **Praxis Scientific Analysis**:
   - Check: Does `vendor/praxis/scripts/` exist?
   - MISSING impact: No technique-specific data analysis or venue-matched publication figures. Falls back to generic matplotlib. Only matters if you have data files in `attachments/`.

8. **CORE API Key**:
   - Check: `CORE_API_KEY` env var set?
   - MISSING impact: One fewer source for OA resolution. Loses access to 200M+ institutional repository papers. Other OA sources (Unpaywall, OpenAlex, PubMed Central) still work.

9. **NCBI API Key**:
   - Check: `NCBI_API_KEY` env var set?
   - MISSING impact: PubMed rate limit stays at 3 requests/second instead of 10. Only relevant for biomedical/clinical papers.

10. **Scientific Skills**:
    - Check: Does `.claude/skills/` exist and contain SKILL.md files? Count them.
    - MISSING impact: Writing and review agents lose access to 177 domain-specific scientific skills. Prose quality and domain accuracy decrease.

### Project State (if inside a paper project)

11. **Paper config**: Does `.paper.json` exist? If so, show topic, depth, venue.
12. **Pipeline state**: Does `.paper-state.json` exist? If so, show current stage and completion %.
13. **Source coverage**: Does `research/source_coverage.md` exist? If so, show full-text/abstract/metadata counts.
14. **Knowledge graph**: Does `research/knowledge/` exist? If so, run `python scripts/knowledge.py entities 2>/dev/null | head -5` to verify it works.

### Output Format

```
Pipeline Health Check
=====================

Required
  [OK]      LaTeX          pdflatex 3.14159, latexmk 4.83
  [OK]      Python         3.12.1
  [OK]      Git            2.43.0
  [OK]      Claude Code    Running

Optional Integrations
  [OK]      Knowledge Graph   OPENROUTER_API_KEY set, lightrag installed
  [MISSING] Codex Bridge      Not installed — no adversarial review (~10 checkpoints skipped)
  [OK]      Praxis            vendor/praxis/ present
  [MISSING] CORE API Key      OA resolution reduced (Unpaywall/OpenAlex still active)
  [MISSING] NCBI API Key      PubMed rate-limited to 3 req/s (only matters for biomedical)
  [OK]      Scientific Skills 177 skills available

Project State
  Topic:    "LLM reasoning capabilities"
  Depth:    deep
  Stage:    Stage 3 (Writing) — 60% complete
  Sources:  42 refs — 18 full-text, 20 abstract-only, 4 metadata-only
  KG:       Built, 847 entities
```

Run all checks using Bash commands. Report the table to the user. If any REQUIRED check fails, warn prominently.
