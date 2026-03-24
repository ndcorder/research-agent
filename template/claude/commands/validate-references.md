# Validate References — Verify Every Citation is Real

Cross-check every BibTeX entry in `references.bib` against real sources to catch fabricated, hallucinated, or incorrectly formatted references.

## Instructions

This is a CRITICAL quality gate. Fabricated references are the single biggest risk in AI-assisted paper writing.

1. **Parse `references.bib`** — extract every entry with its key, type, title, authors, year, DOI, journal/venue
2. **For each entry, verify it exists** using this verification chain (try in order):
   - **If DOI present**: use WebFetch on `https://api.crossref.org/works/DOI` and compare title/authors/year against the response
   - **If arXiv ID present**: use WebFetch on `https://export.arxiv.org/api/query?id_list=ID`
   - **If no DOI/arXiv**: search for the exact title using Perplexity or web search with the title in quotes
   - **Note**: CrossRef may rate-limit unauthenticated requests. If you get rate-limited, add a brief pause between requests or switch to search-based verification.

3. **For each entry, classify as**:
   - **VERIFIED** — Found in at least one authoritative source, metadata matches
   - **METADATA MISMATCH** — Paper exists but some fields are wrong (wrong year, misspelled author, wrong venue). List corrections.
   - **SUSPICIOUS** — Cannot find this exact paper. Flag for manual review. **Do NOT remove** — preprints, workshop papers, and technical reports may be hard to find online.
   - **FABRICATED** — Strong evidence this paper does not exist: no search results across multiple tools AND implausible author/venue combination AND DOI returns 404. Only classify as FABRICATED when confident.

4. **For VERIFIED entries, check metadata completeness**:
   - All authors present (not truncated to "et al.")
   - Correct entry type (@article vs @inproceedings vs @misc)
   - Volume, number, pages filled in (for journal articles)
   - DOI present (add if found during verification)

5. **For VERIFIED entries, attempt OA resolution** (if no source extract with FULL-TEXT exists):
   - **If DOI present**: check Semantic Scholar `openAccessPdf` field via `https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=openAccessPdf,abstract`
   - **If open-access PDF found**: fetch it with WebFetch, create or update `research/sources/<key>.md` with `Access Level: FULL-TEXT` and a content snapshot of key sections
   - **If no OA PDF but abstract available**: create or update `research/sources/<key>.md` with `Access Level: ABSTRACT-ONLY` and the abstract as the content snapshot
   - **If abstract available from Semantic Scholar response**: always save it to the source extract even if full text isn't available
   - This step is best-effort — don't let OA failures block the validation. Log attempts in `research/log.md`.

6. **Fix directly**:
   - Correct metadata mismatches in `references.bib`
   - Remove FABRICATED entries from `references.bib` AND their `\citep{}`/`\citet{}` from `main.tex`
   - Add missing DOIs discovered during verification

7. **Write validation report** to `research/reference_validation.md`:
   ```
   Reference Validation Report
   Total entries:     45
   Verified:          38
   Metadata fixed:     4 (corrected in references.bib)
   Suspicious:         2 (flagged for manual review)
   Fabricated:         1 (removed)

   SUSPICIOUS - manual review needed:
   - [key] "Title..." - no exact match found, closest: "Similar Title..."

   REMOVED (fabricated):
   - [key] "Title..." - no evidence this paper exists

   METADATA CORRECTIONS:
   - [key] year: 2021->2022, venue: "ICML"->"NeurIPS"

   Source Access Levels:
   - Full-text:      N (via OA resolution or attachments/)
   - Abstract-only:  N
   - Metadata-only:  N
   - No source file: N
   ```

8. **After all fixes**, compile: `latexmk -pdf -interaction=nonstopmode main.tex`

$ARGUMENTS
