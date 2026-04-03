# Score — Paper Quality Scorecard

Compute and display a multi-dimensional quality scorecard for the current paper.

## Instructions

1. Run the quality scoring engine:
   ```bash
   python scripts/quality.py score --format text --project .
   ```
2. Read the text output and display it.

3. Also run with JSON format and store the result:
   ```bash
   python scripts/quality.py score --format json --project . > .paper-quality.json
   ```

4. If `.paper-state.json` exists, update it with the latest scores under `stages.quality_scores`.

5. Save scores to cross-paper analytics:
   ```bash
   python scripts/quality.py save --project .
   ```

6. Display the text report to the user.

7. If any dimension scores below 40, highlight it with a specific recommendation:
   - **evidence < 40**: "Consider running `/audit-claims` to identify weak claims, then `/auto` to strengthen evidence."
   - **writing < 40**: "Consider running `/de-ai-polish` followed by `/auto` with writing focus."
   - **structure < 40**: "Check `/compile` for LaTeX errors and `/status` for section word counts."
   - **research < 40**: "Consider running `/audit-sources` to upgrade source access levels."
   - **provenance < 40**: "Provenance gaps suggest sections were written outside the pipeline. Run `/provenance` to investigate."

$ARGUMENTS
