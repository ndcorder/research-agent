# Stage 1c: Codex Research Cross-Check

> **Prerequisites**: Read `pipeline/shared-protocols.md` for the Codex Deliberation Protocol.

---

**This is a standalone stage. Do NOT skip it. Do NOT merge it into another stage.**

After all research agents and bibliography building are complete, use Codex to cross-check the key findings.

1. Read ALL research files: `research/survey.md`, `research/methods.md`, `research/empirical.md`, `research/theory.md`, `research/gaps.md` (and in deep mode, also the 7 additional files).
2. For EACH research file, call Codex to cross-check its claims:

```
mcp__codex-bridge__codex_ask({
  prompt: "Cross-check these research findings from [FILENAME]. For each major claim: (1) Is it accurately represented? (2) Are there contradicting studies or nuances missing? (3) Are key papers overlooked? (4) Are any claims exaggerated or out of context? Be specific — cite papers by name if you know of contradictions.",
  context: "[paste content of the research file being checked]"
})
```

3. Write all Codex responses to `research/codex_cross_check.md` (append each file's review as a section)
4. Apply the **Codex Deliberation Protocol**: evaluate each point, push back where you disagree, log the deliberation
5. **Codex Telemetry** — After each per-file cross-check and deliberation, append to `research/codex_telemetry.jsonl`:
   ```
   {"ts":"[timestamp]","stage":"1c","tool":"codex_ask","purpose":"cross-check [FILENAME]","outcome":"[deliberation result]","points_raised":[N],"points_accepted":[N],"points_rejected":[N],"artifact":"research/codex_cross_check.md","resolution_summary":"[one-line]"}
   ```
6. If Codex identifies missing perspectives or inaccurate claims, spawn a **targeted follow-up research agent** (model: claude-sonnet-4-6[1m]) to investigate those specific gaps. The agent should update the relevant research files and add any new references to `references.bib`.

**Checkpoint**: Verify `research/codex_cross_check.md` exists. If it does not exist, you skipped this stage — go back and do it.

Update `.paper-state.json`: mark `codex_cross_check` as done.
