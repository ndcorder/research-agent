# Stage 2b: Codex Thesis Stress-Test

> **Prerequisites**: Read `pipeline/shared-protocols.md` for the Codex Deliberation Protocol.

---

**This is a standalone stage. Do NOT skip it. Do NOT merge it into another stage.**

1. Read `research/thesis.md` for the thesis/contribution statement
2. Read `main.tex` for the outline structure
3. Call the Codex MCP tool directly:

```
mcp__codex-bridge__codex_plan({
  prompt: "Stress-test this research paper plan. The thesis is: [paste thesis]. The sections are: [list sections]. Challenge: (1) Is the contribution genuinely novel given the related work? (2) Is the argument structure sound — does evidence flow logically? (3) What will reviewers attack? (4) Are there missing sections or weak links?",
  context: "[paste content of research/thesis.md and the outline sections from main.tex]"
})
```

4. Write the Codex response to `research/codex_thesis_review.md`
5. **Assumptions context (resume only)**: If `research/assumptions.md` exists (from a prior partial run), also call Codex to review the assumptions:
   ```
   mcp__codex-bridge__codex_ask({
     prompt: "Review these methodological assumptions. Are any miscategorized (e.g., marked STANDARD but actually RISKY)? Are any assumptions MISSING that a reviewer would flag? Are the proposed mitigations adequate?",
     context: "[paste content of research/assumptions.md]"
   })
   ```
   Append the response to `research/codex_thesis_review.md`. Skip this step if `research/assumptions.md` does not exist (it will be created later in Stage 2e).
6. If Codex identifies structural problems, fix them in the outline in `main.tex` before proceeding
7. Surface any disagreements between your assessment and Codex's to the user

**Checkpoint**: Verify `research/codex_thesis_review.md` exists. If it does not exist, you skipped this stage — go back and do it.

Update `.paper-state.json`: mark `codex_thesis` as done.
