# Validate References — Verify Every Citation is Real

Cross-check every BibTeX entry in `references.bib` against real sources to catch fabricated, hallucinated, or incorrectly formatted references.

## Instructions

This is a CRITICAL quality gate. Fabricated references are the single biggest risk in AI-assisted paper writing.

1. **Parse `references.bib`** — extract every entry with its key, type, title, authors, year, DOI, journal/venue
2. **For each entry, verify it exists** using this verification chain:
   - **If DOI present**: Fetch metadata from CrossRef (`curl -s "https://api.crossref.org/works/DOI"`) and compare title/authors/year
   - **If arXiv ID present**: Check against arXiv API
   - **If no DOI/arXiv**: Search for the exact title using Perplexity or web search
   - **Fallback**: Search Google Scholar via web search with `"exact title"` in quotes

3. **For each entry, classify as**:
   - **VERIFIED** — Found in at least one authoritative source, metadata matches
   - **METADATA MISMATCH** — Paper exists but some fields are wrong (wrong year, misspelled author, wrong venue). List the corrections needed.
   - **SUSPICIOUS** — Cannot find this exact paper. Title/author combination returns no results. Flag for manual review.
   - **FABRICATED** — Strong evidence this paper does not exist (no search results, implausible author/venue combination, DOI returns 404). **Remove immediately.**

4. **For VERIFIED entries, check metadata completeness**:
   - All authors present (not truncated with "et al." in BibTeX)
   - Correct entry type (@article vs @inproceedings vs @misc)
   - Volume, number, pages filled in (for journal articles)
   - DOI present (add if found during verification)
   - Year is correct
   - Journal/conference name is not abbreviated incorrectly

5. **Fix all issues directly**:
   - Correct metadata mismatches in `references.bib`
   - Remove fabricated entries from `references.bib`
   - Remove corresponding `\citep{}`/`\citet{}` from `main.tex` for deleted entries
   - Add missing DOIs discovered during verification

6. **Output a validation report** to `research/reference_validation.md`:
   ```
   Reference Validation Report
   ══════════════════════════════
   Total entries:     45
   Verified:          38 ✓
   Metadata fixed:     4 (corrected in references.bib)
   Suspicious:         2 (flagged for manual review)
   Fabricated:         1 (removed)

   SUSPICIOUS — manual review needed:
   - [smith2024] "Title..." — no exact match found, closest result: "Similar Title..."
   - [jones2023] "Title..." — DOI returns different paper

   REMOVED (fabricated):
   - [fake2025] "Title..." — no evidence this paper exists

   METADATA CORRECTIONS APPLIED:
   - [doe2022] year: 2021→2022, venue: "ICML"→"NeurIPS"
   - [chen2023] added DOI: 10.xxxx/xxxxx
   ```

7. **After all fixes, compile**: `latexmk -pdf -interaction=nonstopmode main.tex` to ensure no broken citations

## Important Notes

- This command should be run BEFORE final submission
- Be thorough — check EVERY entry, not just a sample
- When in doubt, mark as SUSPICIOUS rather than removing (let the human decide)
- Some preprints and working papers may not appear in databases — mark as SUSPICIOUS, not FABRICATED
- Conference workshop papers and technical reports may be harder to verify — search more broadly

$ARGUMENTS
