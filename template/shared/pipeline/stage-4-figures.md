# Stage 4: Figures, Tables & Visual Elements

> **Prerequisites**: Read `pipeline/shared-protocols.md` for Provenance Logging Protocol and Codex Deliberation Protocol.

---

**Step 4a: Data-driven figures with Praxis (if available)**

If `vendor/praxis/scripts/` exists AND `attachments/` contains data files, spawn a **data analysis agent** (model: claude-sonnet-4-6[1m]):
```
You are a scientific data analyst. Read .claude/skills/praxis/SKILL.md for the Praxis toolkit API.
Read vendor/praxis/references/cookbook.md for worked examples.
Read .venue.json for the target venue — map to Praxis journal style (nature, ieee, acs, science, elsevier, springer, rsc, wiley, mdpi).

Scan attachments/ for data files. For each file:
1. Auto-detect the characterisation technique from the data structure
2. Write a Python analysis script using Praxis (sys.path.insert(0, "vendor/praxis/scripts"))
3. Apply the venue-matched journal style: apply_style("<style>")
4. Use colourblind-safe palette: set_palette("okabe_ito")
5. Run technique-specific analysis (XRD → crystallite size, DSC → Tg/Tm, mechanical → modulus, etc.)
6. Export figures as PDF to figures/
7. Save scripts to figures/scripts/ for reproducibility

After generating figures:
- Add \includegraphics{} to Results section of main.tex with descriptive captions
- Add quantitative results to the Results text
- Add methodology to the Methods section
- Write analysis summary to research/praxis_analysis.md

If no data files exist in attachments/, skip this step.
```

If Praxis is not available but data files exist, fall back to generic matplotlib (use the `matplotlib` skill from `.claude/skills/matplotlib/SKILL.md`).

**Step 4b: Structural figures and tables**

Spawn an agent (model: claude-sonnet-4-6[1m]):
```
You are a scientific visualization specialist.
Read main.tex completely.

Invoke the `scientific-visualization` skill (read .claude/skills/scientific-visualization/SKILL.md).

Ensure the paper has:
1. At least 1 overview/architecture/framework figure (use TikZ or describe in a figure environment)
2. At least 2 data/results tables with booktabs formatting
3. All figures/tables referenced in text with \ref{} BEFORE they appear
4. All captions are descriptive (2-3 sentences explaining what the figure shows and why it matters)
5. Consistent figure/table numbering and labeling
6. Float placement uses [htbp]

If Praxis already generated data figures (check figures/ directory), don't duplicate them — focus on structural/conceptual figures.
Add any new figures to main.tex with proper \includegraphics{} and \caption{}.
Edit main.tex directly.

PROVENANCE — For each figure or table added, append a provenance entry to research/provenance.jsonl:
{"ts":"[timestamp]","stage":"4","agent":"figures","action":"add","target":"figures/[filename]","reasoning":"[why this figure — what it shows and why the paper needs it]","sources":["keys"],"iteration":0}
```

**Step 4c: Codex Figure & Claims Audit**

After figures and tables are in place, call Codex to sanity-check the visual claims:

```
mcp__codex-bridge__codex_ask({
  prompt: "Audit the figures, tables, and their associated claims in this manuscript. For each figure/table: (1) Does the caption accurately describe what is shown? (2) Do the claims in the surrounding text match what the data actually shows? (3) Are there misleading axis scales, cherry-picked comparisons, or missing error bars/confidence intervals? (4) Are any figures redundant or better presented as tables (or vice versa)?",
  context: "[paste the Results and Discussion sections from main.tex, including all figure/table environments]"
})
```

Write the response to `reviews/codex_figures_audit.md`. Fix any critical mismatches between figures and claims in main.tex immediately.

**Codex Telemetry** — Append to `research/codex_telemetry.jsonl`:
```
{"ts":"[timestamp]","stage":"4","tool":"codex_ask","purpose":"figures and claims audit","outcome":"[deliberation result]","points_raised":[N],"points_accepted":[N],"points_rejected":[N],"artifact":"reviews/codex_figures_audit.md","resolution_summary":"[one-line]"}
```

**Step 4d: PRISMA Flowchart (auto-detected)**

Check if this paper is a systematic review by reading `.paper.json` and examining the `topic` field. If the topic contains any of these keywords (case-insensitive): "systematic review", "meta-analysis", "scoping review", "literature review", then generate a PRISMA flowchart:

1. Read `commands/prisma-flowchart.md` for the full procedure.
2. Execute the instructions: extract search statistics from `research/log.md`, `references.bib`, and `research/sources/`, compute the PRISMA phase numbers, generate a TikZ flowchart, and insert it into the Methods section of `main.tex`.
3. Log provenance as specified in the command file.

If the topic does **not** match any of the above keywords, skip this step silently (no output, no log entry).

---
