# De-AI Polish — Remove AI Writing Patterns

Scan the manuscript for common AI-generated writing patterns and replace them with natural academic prose. Makes the paper read like a human domain expert wrote it.

## Instructions

1. **Read `main.tex` completely**

2. **Scan for and fix these AI writing tells:**

   ### Category 1: Filler Phrases (remove or rephrase)
   - "It is worth noting that" → state the point directly
   - "It should be noted that" → remove, state directly
   - "It is important to mention" → remove, just mention it
   - "It is evident that" → state the evidence directly
   - "It can be observed that" → state the observation
   - "In the realm of" → "in" or rephrase
   - "In the landscape of" → "in" or rephrase
   - "This serves as a testament to" → remove, state the fact

   ### Category 2: AI Vocabulary (replace with simpler words)
   - "delve" / "delves into" → "examines", "explores", "investigates"
   - "tapestry" → remove entirely or use domain-specific term
   - "multifaceted" → "complex" or be specific about the facets
   - "leverage" (as verb) → "use", "employ", "apply"
   - "utilize" → "use"
   - "facilitate" → "enable", "help", "allow"
   - "elucidate" → "explain", "clarify", "show"
   - "paradigm" (overused) → be specific about what changed

   ### Category 3: Formulaic Transitions (diversify)
   - "Furthermore," / "Moreover," / "Additionally," at sentence starts → vary: rephrase to connect ideas logically, or remove if the connection is obvious
   - "In this section, we..." openers on every section → vary openings, sometimes just start with the content
   - "As mentioned above" / "As discussed previously" → use specific references (\ref{})

   ### Category 4: Redundant Phrasing (tighten)
   - "in order to" → "to"
   - "a total of N" → "N"
   - "the fact that" → remove, rephrase
   - "due to the fact that" → "because"
   - "in the context of" → "in" or "for"
   - "a wide range of" → "many" or "various"
   - "plays a crucial role in" → "is important for" or be specific

   ### Category 5: Empty Emphasis (quantify or remove)
   - "significantly" without a significance test → remove or add p-value
   - "notably" without saying why it's notable → remove or explain
   - "remarkably" → remove unless truly remarkable, then explain why
   - "dramatically" → use numbers instead
   - "groundbreaking" → let the results speak

   ### Category 6: Structural Tells (vary for natural rhythm)
   - All paragraphs roughly same length → vary paragraph length
   - Every paragraph starts with a topic sentence of identical structure → diversify
   - Lists that were clearly expanded from bullet points → rewrite as flowing prose
   - Conclusions that start with "In conclusion" → find a more natural transition

3. **Preserve**:
   - All technical content, equations, and citations
   - Necessary hedging ("may", "might") when results are genuinely uncertain
   - Domain-specific terminology (don't oversimplify)
   - Author voice — if the paper has a distinctive analytical style, keep it

4. **Report** what was changed:
   - Count of changes per category
   - Examples of before/after for the most impactful changes
   - Any patterns you noticed but chose NOT to change (with reasoning)

## Section to Polish

$ARGUMENTS

If no arguments, polish the entire manuscript. If a section name is given (e.g., "Introduction"), only polish that section.
