# Ask — Query Your Research Archive

Answer questions about the research by searching through all research artifacts, source extracts, reviews, and the manuscript itself.

## Instructions

1. **Parse the question** from $ARGUMENTS. If empty, ask the user what they want to know.

2. **Search across all research artifacts** in this priority order:
   - `research/sources/` — raw source extracts with citations and provenance (most authoritative)
   - `research/` — synthesized research notes (survey, methods, empirical, theory, gaps, thesis)
   - `reviews/` — QA feedback (technical, writing, completeness, claims audit)
   - `main.tex` — the manuscript itself
   - `references.bib` — bibliography entries
   - `research/log.md` — research provenance log (what was searched, where, when)
   - `archive/` — the full archive if it exists

   Use Grep to search for keywords from the question across all these locations. Read the most relevant files or sections.

3. **Synthesize an answer** that:
   - Directly answers the question with specific information from the research
   - Cites which file(s) the information came from (e.g., "According to research/survey.md...")
   - Includes relevant paper citations with BibTeX keys when referencing specific studies
   - Notes the provenance — which tools/databases were used to find the information (from research/log.md if available)
   - Flags if the question touches on something NOT covered in the research (a gap)

4. **If the question is about a specific paper or claim**:
   - Check `research/sources/<key>.md` for the raw source extract
   - Check `research/log.md` for when/how it was found
   - Check `main.tex` for how it's used in the manuscript
   - Provide the full trail: source → research note → manuscript

5. **If the question cannot be answered from existing research**:
   - Say so clearly
   - Suggest which databases or search tools might help find the answer
   - Offer to run a targeted search using available tools (Perplexity, domain databases, etc.)

## Example Usage

- `/ask What methods were compared for protein folding?`
- `/ask Where did the claim about 95% accuracy come from?`
- `/ask What databases were searched during research?`
- `/ask Are there any gaps in the literature coverage?`
- `/ask What did the reviewers say about the methodology?`

## Question

$ARGUMENTS
