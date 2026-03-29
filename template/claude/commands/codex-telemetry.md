# Codex Telemetry — Analyze Codex Bridge Interaction Patterns

Analyze the structured Codex telemetry log to understand how the Codex bridge was used throughout the pipeline.

## Instructions

Read `research/codex_telemetry.jsonl`. If the file does not exist or is empty, report: "No Codex telemetry data found. The Codex bridge either wasn't used or telemetry logging wasn't active during this pipeline run." and stop.

Parse each line as a JSON object with fields: `ts`, `stage`, `tool`, `purpose`, `outcome`, `points_raised`, `points_accepted`, `points_rejected`, `artifact`, `resolution_summary`.

### Generate these analyses:

#### 1. Summary Statistics
- Total Codex interactions
- Breakdown by tool (codex_ask, codex_review, codex_plan, codex_risk_radar, codex_stats)
- Breakdown by stage (group by stage field)

#### 2. Agreement Analysis
- Overall agreement rate: % of interactions with outcome AGREE or PARTIALLY_AGREE (exclude N_A from denominator)
- Per-stage agreement rate
- Total points raised vs accepted vs rejected across all interactions

#### 3. Disagreement Hotspots
- List interactions where outcome was DISAGREE, sorted by points_rejected (descending)
- For each: stage, tool, purpose, points rejected, resolution summary

#### 4. Timeline
- Chronological list of all interactions with: timestamp, stage, tool, outcome (one line each)

#### 5. Patterns
- Which stages generated the most Codex feedback? (by points_raised)
- Were there clusters of disagreements in specific stages?
- Did agreement rates change over the pipeline (early stages vs late stages)?

### Output

**Default** (no arguments): Print the analysis directly to the console.

**`export` argument**: Write the full analysis to `research/codex_telemetry_report.md` and confirm.

$ARGUMENTS
