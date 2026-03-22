# Outline Section

Generate a structured outline for a paper section before writing full prose.

## Instructions

This is **Stage 1** of the two-stage writing process.

1. **Parse the section name** from $ARGUMENTS. If no section specified, ask the user which section to outline.
2. **Read `main.tex`** to understand the paper's current state, topic, and existing sections
3. **Read `.paper.json`** for topic context
4. **Research** the topic area using Perplexity (`mcp__perplexity__search`) or web search to gather:
   - Key concepts and terminology
   - Important references to cite (check `references.bib` for existing keys)
   - Standard structure for this type of section
5. **Generate an outline** with:
   - Subsection headings (if appropriate)
   - 3-5 key points per subsection, each with:
     - The core claim or finding
     - Supporting evidence or citation keys from `references.bib`
     - Connection to the paper's thesis
   - Suggested figures or tables
   - Transition notes between subsections
   - Target word count for each subsection
6. **Write the outline** as LaTeX comments (`%`) in the appropriate section of `main.tex`
7. **Present the outline** to the user as a summary. The user can then ask you to convert it to prose, or modify the outline first.

## Section to Outline

$ARGUMENTS
