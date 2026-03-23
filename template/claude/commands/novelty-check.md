# Novelty Check — Verify Your Contribution Hasn't Been Published

Search across academic databases to verify that the paper's claimed contribution is genuinely novel. This runs automatically as Stage 2d in `/write-paper` but can also be invoked manually at any time.

## Instructions

1. **Identify the contribution** to check:
   - If $ARGUMENTS is provided, use it as the contribution description
   - Otherwise, read `research/thesis.md` for the contribution statement
   - If neither exists, ask the user what contribution to check

2. **Extract searchable claims** from the contribution:
   - The specific method or approach name
   - The problem being solved
   - The key technical innovation
   - The claimed improvement or result

3. **Search comprehensively** — use ALL available tools:

   **Academic databases** (try in this order):
   - Perplexity search (`mcp__perplexity__search` or `mcp__perplexity__reason`) — broad academic search
   - arXiv search — for preprints in CS/physics/math/biology
   - Semantic Scholar — for citation-aware search
   - Domain-specific databases (PubMed for biomedical, ChEMBL for chemistry, etc.)
   - Web search as fallback

   **For each search, try multiple query formulations:**
   - Exact method/approach name
   - Key technique combination (e.g., "transformer + protein folding")
   - Problem statement (e.g., "improving discrete diffusion language models")
   - Alternative names for the same approach

   **Cross-model verification** (if Codex Bridge is available):
   ```
   mcp__codex-bridge__codex_ask({
     prompt: "Has this specific contribution already been published? The claimed contribution is: [CONTRIBUTION]. Search your knowledge for any existing work that makes the same or very similar claims. Check not just the exact method name but also equivalent approaches under different names. List any papers you find.",
     context: "[contribution details]"
   })
   ```

4. **Assess novelty** based on findings:

   - **NOVEL** — No existing work makes the same contribution. Minor overlaps with prior work exist but the core innovation is new.
   - **PARTIALLY NOVEL** — Similar work exists but the approach, application, or angle differs meaningfully. Document the differences.
   - **NOT NOVEL** — Existing work already covers this contribution substantially. List the conflicting papers.

5. **Write the report** to `research/novelty_check.md`:
   ```markdown
   # Novelty Check Report

   **Contribution checked**: [the contribution statement]
   **Date**: [current date]
   **Status**: NOVEL / PARTIALLY NOVEL / NOT NOVEL

   ## Search Queries Used
   [List every query and which tool was used]

   ## Existing Related Work Found
   [For each paper found:]
   - **Title**: ...
   - **Authors**: ...
   - **Year**: ...
   - **DOI/URL**: ...
   - **Overlap**: [what's similar to our contribution]
   - **Distinction**: [how our contribution differs]

   ## Assessment
   [Detailed explanation of why the contribution is/isn't novel]

   ## Recommendations
   [If PARTIALLY NOVEL: how to differentiate more clearly]
   [If NOT NOVEL: alternative angles or pivot suggestions]
   ```

6. **Report the verdict** clearly to the user with the key evidence.

## Example Usage

- `/novelty-check "Using graph attention networks for protein-protein interaction prediction"`
- `/novelty-check "A factorized gap approach to discrete diffusion language models"`
- `/novelty-check` (reads from research/thesis.md)

## Contribution to Check

$ARGUMENTS
