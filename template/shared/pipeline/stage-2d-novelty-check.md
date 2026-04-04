# Stage 2d: Novelty Verification

> **Prerequisites**: Read `pipeline/shared-protocols.md` for the Codex Deliberation Protocol.

---

**This is a standalone stage. Do NOT skip it. Do NOT merge it into another stage.**

Before investing hours in writing, verify the contribution hasn't already been published. This catches the worst-case scenario: writing a complete paper about something that already exists.

1. Read `research/thesis.md` for the contribution statement and key claims
2. Search for existing work that makes the SAME contribution:

**Search strategy** — use ALL available tools in parallel:
- Search arXiv for papers with similar titles and abstracts (use `mcp__perplexity__search` or domain database skills)
- Search Semantic Scholar / Google Scholar for the specific method or approach name
- Search DBLP for the exact technique combination
- If Codex is available, also ask:
  ```
  mcp__codex-bridge__codex_ask({
    prompt: "Has this specific contribution already been published? The claimed contribution is: [paste thesis]. Search your knowledge for any existing work that makes the same or very similar claims. Be thorough — check not just the exact method name but also equivalent approaches under different names.",
    context: "[paste content of research/thesis.md]"
  })
  ```

3. Write the results to `research/novelty_check.md`:
   - **NOVEL**: No existing work makes the same contribution → proceed
   - **PARTIALLY NOVEL**: Similar work exists but our angle/approach differs → document how we differentiate, update thesis.md to clarify the distinction
   - **NOT NOVEL**: Existing work already covers this → STOP. Report to user with the conflicting papers. Do NOT proceed to writing.

4. If partially novel, update `research/thesis.md` and the outline in `main.tex` to explicitly differentiate from the similar work. Add the similar papers to `references.bib` and plan to discuss them in Related Work.

**Checkpoint**: Verify `research/novelty_check.md` exists and status is NOVEL or PARTIALLY NOVEL. If NOT NOVEL, halt the pipeline and report to the user.

Update `.paper-state.json`: mark `novelty_check` as done.
