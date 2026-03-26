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
5. If Codex identifies structural problems, fix them in the outline in `main.tex` before proceeding
6. Surface any disagreements between your assessment and Codex's to the user

**Checkpoint**: Verify `research/codex_thesis_review.md` exists. If it does not exist, you skipped this stage — go back and do it.

Update `.paper-state.json`: mark `codex_thesis` as done.
