# Codex Review — Adversarial AI Review via Codex Bridge

Get a second-opinion review from OpenAI Codex via the codex-bridge MCP server. Codex acts as an adversarial reviewer — challenging assumptions, finding logical gaps, and stress-testing claims.

## Prerequisites

This command requires the `codex-bridge` MCP server. Check if it's available by looking for `mcp__codex-bridge__codex_review` in available tools. If not available, report: "Codex Bridge not configured. Install with: npm i -g codex-bridge && codex-bridge init" and stop.

## Instructions

1. **Read `main.tex`** completely to get the full paper content
2. **Determine review scope**:
   - If $ARGUMENTS specifies a section, extract just that section
   - If empty, review the full paper

3. **Run `codex_plan`** first to stress-test the paper's structure:
   ```
   Call mcp__codex-bridge__codex_plan with:
   - prompt: "Review this research paper's argument structure. Identify: (1) Is the thesis clearly stated and supported? (2) Does the evidence chain hold — does each section's conclusion feed logically into the next? (3) Are there circular arguments or unstated assumptions? (4) What would a skeptical reviewer attack first?"
   - context: [paste the full paper or target section]
   ```

4. **Run `codex_review`** with evidence mode for rigorous critique:
   ```
   Call mcp__codex-bridge__codex_review with:
   - prompt: "Review this scientific manuscript. Focus on: (1) Overclaims — assertions stronger than the evidence supports (2) Logical gaps — conclusions that don't follow from premises (3) Missing comparisons — baselines or prior work not addressed (4) Methodological weaknesses a peer reviewer would flag (5) Statistical claims without proper tests"
   - context: [paste the full paper or target section]
   - evidence_mode: true
   ```

5. **Run `codex_ask`** for specific concerns found:
   ```
   For each major issue identified, call mcp__codex-bridge__codex_ask with:
   - prompt: "How should the authors address this specific weakness: [describe issue]. What would strengthen the argument?"
   - context: [relevant section]
   ```

6. **Synthesize findings** into a structured review:
   - Group by severity (Critical / Major / Minor)
   - For each issue: what Codex found, where in the paper, and suggested fix
   - Note any disagreements between Claude's assessment and Codex's — present both perspectives to the user

7. **Write the review** to `reviews/codex_review.md`

8. **Show `codex_stats`** at the end to report collaboration metrics

## Disagreement Protocol

If Codex disagrees with your own assessment of the paper:
- Do NOT silently pick a side
- Present both perspectives clearly: "Claude assessment: X. Codex assessment: Y."
- Let the user decide which feedback to act on

$ARGUMENTS

Accepts an optional section name. If empty, reviews the full paper.
