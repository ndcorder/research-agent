# Stage 2: Thesis, Contribution & Outline

> **Prerequisites**: Read `pipeline/shared-protocols.md` for Provenance Logging Protocol and Codex Deliberation Protocol.

---

Read ALL files in `research/`, especially `research/gaps.md`. Then:

1. **Define the paper's thesis and contribution** based on the gap analysis:
   - What specific problem does this paper address?
   - What is the novel contribution?
   - What are the key claims this paper will make?
   - Write these to `research/thesis.md`

   **Knowledge graph validation** (run if `research/knowledge/` exists — if not, log `"⚠ Knowledge graph not available — applying compensating checks per Knowledge Graph Availability Protocol"` and follow the compensation steps below):
   ```bash
   python scripts/knowledge.py query "What approaches have been proposed for [thesis topic]?"
   python scripts/knowledge.py evidence-against "[proposed contribution statement]"
   python scripts/knowledge.py contradictions
   python scripts/knowledge.py entities
   ```
   - If the graph reveals existing work that closely matches the proposed contribution, flag this as a **novelty red flag** and surface it before Stage 2d (novelty check).
   - Use the entity list to identify key concepts the paper MUST discuss. If an entity with many relationships isn't mentioned in the outline, it's likely a gap.
   - Run `python scripts/knowledge.py coverage research/thesis.md` to check which important entities are missing from the thesis statement.

   **If the knowledge graph is NOT available**, compensate:
   - Manually scan `research/sources/` for existing work that overlaps with the proposed contribution. Read at least the top 5 most-cited sources and compare their findings against the thesis.
   - Compile a list of key concepts mentioned across 3+ source extracts — these are the entities the paper must discuss. Check the outline against this list.
   - Note in `research/thesis.md`: `"Note: Thesis validated against source extracts only (knowledge graph unavailable). Cross-source entity coverage may be incomplete."`

2. **Determine paper structure** based on topic type AND venue:
   - Read `.venue.json` for venue-specific section order (e.g., Nature puts Results before Methods)
   - Read `.venue.json` for citation style (natbib vs numeric vs APA), page limits, abstract limits
   - Survey → taxonomy-based Related Work, no Methods/Results; instead use thematic analysis sections
   - Empirical → standard IMRAD with heavy Methods and Results
   - Theoretical → formal framework section, proofs, theoretical analysis
   - Methods → proposed approach, evaluation against baselines
   - **Adapt section word targets** if venue has page limits (e.g., 8-page IEEE = shorter sections)

3. **Create detailed outline** in `main.tex`:
   - Replace all placeholder content
   - Add `\maketitle`, abstract placeholder, all sections/subsections
   - Under each subsection, add `% OUTLINE:` comments with key arguments, citation keys, figure/table plans, word targets
   - Add `\bibliographystyle{plainnat}` and `\bibliography{references}`
   - Update title and authors — derive an appropriate academic title from the topic

4. **Build a Claims-Evidence Matrix** — create `research/claims_matrix.md`:
   - List every major claim the paper will make (from thesis.md)
   - For each claim, identify: what evidence supports it (experiment, citation, formal proof, data)
   - For each claim, note: which section will present this evidence
   - Flag any claims that lack evidence — these must be either supported or removed before writing begins
   - Format as a markdown table:
     ```
     | # | Claim | Evidence Type | Evidence Sources | Warrant | Qualifier | Rebuttal | Counter-Evidence | Score | Strength | Section | Status |
     |-|-|-|-|-|-|-|-|-|-|-|
     | 1 | Our method improves X by Y% | Experiment | Own experiments (N/A, direct) = 3 | Standard benchmark, exceeds typical gains | English data, default params | May not generalize to low-resource (Sec 6.2) | 3.0 | WEAK | Results | Planned |
     | 2 | Prior approaches fail because... | Citation | smith2024 (FULL-TEXT, direct) = 4, jones2025 (ABSTRACT-ONLY, tangential) = 1 | [MISSING] | | | 5.0 | MODERATE | Related Work | ⚠ Weak warrant |
     ```
     Each evidence source entry uses compact notation: `key (access_level, relevance) = N pts`
     - **Warrant**: One sentence explaining WHY the evidence supports the claim (the logical bridge). A claim with empty Warrant is a structural red flag — the pipeline knows WHAT evidence exists but hasn't articulated WHY it's sufficient.
     - **Qualifier**: Scope limitations or conditions under which the claim holds.
     - **Rebuttal**: Anticipated counterarguments and where they're addressed.
   - This matrix becomes a quality gate in Stage 5 — every claim must have status "Supported" before the paper passes QA, and no CRITICAL-strength claims may survive to finalization. Additionally, no claim may pass QA with a "Missing" warrant.
   - **Source access warning**: Any claim supported ONLY by ABSTRACT-ONLY sources should be flagged with ⚠ — the pipeline may be inferring beyond what was actually read. In Stage 5 QA, reviewers must verify these claims are conservative and well-hedged.
   - **Knowledge graph evidence verification** (run if `research/knowledge/` exists):
     ```bash
     python scripts/knowledge.py evidence-for "claim text here"
     python scripts/knowledge.py evidence-against "claim text here"
     ```
     Run these for EVERY claim in the matrix. Update the matrix with any additional evidence or contradictions the graph surfaces. This is mandatory when the graph is available, not optional.

   - **If the knowledge graph is NOT available**: For every claim in the matrix, manually verify evidence by re-reading the cited source extracts in `research/sources/`. For each WEAK or MODERATE claim, also search other source extracts for contradictory findings. Apply a **-0.5 score penalty** to any claim whose evidence relies on cross-source inference (i.e., combining findings from multiple sources to support a single claim) — the graph would have validated these cross-references. Flag any claim that drops strength category due to this penalty with `⚠ KG-unverified`.

   **Warrant Development** — after building the claims-evidence matrix, develop the Warrant and Rebuttal for each claim:

   For each claim in the matrix:
   1. **Warrant**: Articulate WHY the evidence supports the claim. If the warrant is obvious (direct experimental result supporting an empirical claim), state it briefly. If the warrant requires reasoning (e.g., "this theoretical framework applies because..."), develop it fully. If no clear warrant exists, the claim is unsupported even with citations — flag it with `[MISSING]` in the Warrant column.
   2. **Qualifier**: State the scope limitations or conditions under which the claim holds. Omit only if the claim is truly universal.
   3. **Rebuttal**: For each claim, identify the most likely reviewer objection. Determine whether the rebuttal is addressed in the paper (and where) or needs to be added. Use the knowledge graph (if available) to find counterevidence:
      ```bash
      python scripts/knowledge.py evidence-against "[claim text]"
      ```

   4. **Counter-Evidence**: For each claim, check `research/disagreements.json`. If the claim maps to a registered disagreement:
      - Reference the disagreement ID (e.g., "See D1")
      - Record the opposing position and its source keys
      - Copy the `resolution_strategy` from the registry
      - If no disagreement applies, leave blank

      A claim with Counter-Evidence and resolution_strategy `comparative_analysis` MUST have its Warrant explain why the paper favors its position over the counter-evidence. A claim with `hedge` strategy MUST have a Qualifier that reflects the uncertainty. A claim with `scope_limit` MUST have a Qualifier restricting scope to uncontested territory.

   5. **Update disagreement registry**: After building the claims matrix, update `research/disagreements.json`:
      - Set `addressed_in_sections` based on which sections the disputed claims appear in
      - If a disagreement led to `remove_claim`, set its status to `"resolved"` and note the removal
      - If a disagreement is addressed via `comparative_analysis` or `hedge`, keep status as `"identified"` — it becomes `"resolved"` only after Stage 3 writing confirms the text handles it

   **Warrant quality categories** — assess each warrant:
   | Quality | Description | Action |
   |-|-|-|
   | **Sound** | Evidence logically necessitates the claim | None needed |
   | **Reasonable** | Evidence supports the claim given stated assumptions | State assumptions explicitly |
   | **Weak** | Evidence is consistent with the claim but doesn't strongly support it | Hedge the claim or find stronger evidence |
   | **Missing** | No warrant articulated — claim and evidence are just juxtaposed | Develop warrant or remove claim |
   | **Invalid** | The warrant contains a logical fallacy or factual error | Fix immediately |

   Claims with Missing or Invalid warrants are structural defects — they must be resolved before writing begins, regardless of evidence density score.

   **Automated Warrant Resolution** — after initial warrant assessment, resolve all Missing or Invalid warrants before scoring:

   1. Collect all claims where Warrant is `[MISSING]` or rated `Invalid`.
   2. For each unresolved claim, spawn a targeted research agent (`model: "claude-sonnet-4-6[1m]"`) that:
      - Reads the claim text, its evidence sources (from `research/sources/<key>.md`), and the paper's thesis (`research/thesis.md`)
      - Searches for mechanistic, causal, or theoretical evidence that bridges the gap between evidence and claim:
        - Knowledge graph (if available): `python scripts/knowledge.py query "Why does [evidence] support [claim]?"`
        - Knowledge graph: `python scripts/knowledge.py evidence-for "[claim text]"` (may surface bridging sources missed earlier)
        - Semantic Scholar / literature search: look for mechanistic explanations, causal pathways, or theoretical frameworks that connect the evidence type to the claim type
      - Outputs one of:
        - **Warrant found**: a one-sentence warrant with the reasoning chain and any new sources discovered. Include source keys for any new evidence.
        - **Warrant not found**: the evidence genuinely does not support this claim through any articulable reasoning. Recommend: hedge the claim, downgrade it to a weaker form, or remove it.
   3. Run agents in parallel (one per unresolved claim). Each agent writes its result to a temporary file `research/warrant_resolution_C[N].md`.
   4. Read all resolution files and update the claims matrix:
      - For resolved warrants: fill in the Warrant column, rate quality, add any new sources to the Evidence Sources column and create source extracts in `research/sources/` if new papers were found.
      - For unresolvable claims: either rewrite the claim to a weaker form that the evidence does support (and write the warrant for the weaker claim), or mark the claim for removal with `[REMOVE — no warrant]` in the Status column.
   5. Delete the temporary `research/warrant_resolution_C*.md` files after merging results.
   6. Log each resolution to `research/provenance.jsonl`: action `warrant_resolution`, target `claims/C[N]`, reasoning explaining the outcome.

   After warrant resolution, re-assess: if any claims still have Missing warrants, they must be removed before proceeding. Zero Missing or Invalid warrants is a hard gate for Stage 2 completion.

5. **Score the Claims-Evidence Matrix** — compute evidence density scores for every claim:

   **Base score per source** (by access level):
   | Access Level | Score | Rationale |
   |-|-|-|
   | FULL-TEXT, primary data | 3 | Actual results read |
   | FULL-TEXT, secondary/review | 2 | Full argument read but not primary evidence |
   | ABSTRACT-ONLY | 1 | Summary only, not the real content |
   | METADATA-ONLY | 0 | Paper exists, nothing more |

   **Modifiers** (per source, cumulative):
   - Highly cited (>100 citations): +0.5
   - Recent (2024-2026): +0.5
   - Finding directly matches the claim (not tangential): +1
   - Same domain/methodology as the paper: +0.5

   **Claim score** = sum of all supporting source scores. **Thresholds**:
   | Score | Strength | Meaning |
   |-|-|-|
   | >= 6 | STRONG | Well-supported, multiple strong sources |
   | 3-5.9 | MODERATE | Adequately supported but could be stronger |
   | 1-2.9 | WEAK | Under-supported, needs more evidence or hedging |
   | 0-0.9 | CRITICAL | Essentially unsupported, must be addressed |

   Compute the score for each claim, fill in the Score and Strength columns, then:
   - Flag WEAK claims with ⚠ and note whether they need additional evidence or hedged language
   - Flag CRITICAL claims with ⛔ — these must be either supported with new evidence, hedged heavily, or removed before writing begins
   - The scored matrix drives downstream behavior: writing confidence (Stage 3), QA focus (Stage 5), and `/auto` prioritization

6. **Codex reviews the Claims-Evidence Matrix**:
   ```
   mcp__codex-bridge__codex_ask({
     prompt: "Review this claims-evidence matrix for a research paper. For each claim, assess: (1) Is the proposed evidence actually sufficient to support this claim? (2) Are there claims that are too strong for the evidence type? (e.g., claiming 'proves' based on empirical results) (3) Are there obvious missing claims that the paper should make but doesn't? (4) Are any claims redundant or overlapping?",
     context: "[paste content of research/claims_matrix.md]"
   })
   ```
   Apply the **Codex Deliberation Protocol**. Update the matrix based on agreed feedback. Log deliberation.

   **Codex Telemetry** — Append to `research/codex_telemetry.jsonl`:
   ```
   {"ts":"[timestamp]","stage":"2","tool":"codex_ask","purpose":"claims-evidence matrix review","outcome":"[deliberation result]","points_raised":[N],"points_accepted":[N],"points_rejected":[N],"artifact":"research/claims_matrix.md","resolution_summary":"[one-line]"}
   ```

7. Use the `scientific-writing` skill for IMRAD structure guidance.
8. Use the `venue-templates` skill if targeting a specific venue.
9. **Log planning provenance** — append entries to `research/provenance.jsonl` for key planning decisions:
   - Thesis selection: action `plan`, target `thesis`, reasoning explaining why this contribution was chosen over alternatives from gaps.md
   - Section structure: action `plan`, target `outline`, reasoning explaining structural decisions (why these sections, why this order)
   - Each claim in the claims matrix: action `plan`, target `claims/C[N]`, reasoning explaining the evidence strategy for this claim

**Checkpoint**: Verify outline has 5+ major sections, subsections under each, and planning notes.

Update `.paper-state.json`: mark `outline` as done.

## Evidence Density Scoring Gate

After completing the claims-evidence matrix with warrants, qualifiers, and rebuttals, run the evidence density scorer:

```bash
python scripts/quality.py heatmap --project .
```

This produces `research/evidence_heatmap.md` — a per-claim breakdown that Stage 3 writing agents will consume.

**Review the heatmap before proceeding to writing:**

1. If ANY claim has `CRITICAL` strength (score < 1):
   - STOP. Either run `/targeted-research` to find supporting evidence, hedge the claim to hypothesis-level, or remove it from the outline.
   - Do NOT proceed to Stage 3 with CRITICAL claims unless they are explicitly framed as hypotheses.

2. If more than 30% of claims are `WEAK`:
   - Consider running Stage 2c (targeted research in deep mode) to strengthen evidence before writing.
   - Log the decision in `.paper-state.json` under `stages.planning.evidence_gate`.

3. Update `.paper-state.json`:
   ```json
   {
     "stages": {
       "planning": {
         "evidence_gate": {
           "total_claims": N,
           "strong": N,
           "moderate": N,
           "weak": N,
           "critical": N,
           "gate_passed": true
         }
       }
     }
   }
   ```

Checkpoint: `stages.planning.evidence_gate` must exist before Stage 3 starts.

> **Next**: After novelty verification (Stage 2d), proceed to **Stage 2e: Assumptions Analysis** (`pipeline/stage-2e-assumptions.md`) which systematically enumerates and categorizes methodological assumptions before writing begins.
