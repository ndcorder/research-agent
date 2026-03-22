# Check Consistency — Find Notation, Terminology, and Abbreviation Issues

Scan the paper for internal inconsistencies that reviewers will catch.

## Instructions

Read `main.tex` completely. Check for these categories of inconsistency, in priority order:

### 1. Mathematical Notation (Critical)
- Same concept with different symbols ($x$ vs $X$ for the same variable)
- Variables used before being defined
- Variables defined but never used
- Inconsistent subscript/superscript conventions
- Same symbol for different things in different sections
- Inconsistent bold for vectors/matrices vs scalar

### 2. Terminology Drift (Critical)
- Same concept called different names ("model" vs "framework" vs "system")
- Inconsistent capitalization ("Transformer" vs "transformer")
- Pick the most frequently used term and standardize to it

### 3. Abbreviations (Major)
- Used before definition (first occurrence should be "Full Name (ABBR)")
- Defined more than once
- Defined but never used again (just use full name)
- Sometimes abbreviated, sometimes spelled out after definition

### 4. Reference Format (Major)
- "Figure X" vs "Fig. X" — pick one style, use throughout
- "Section X" vs "Sec. X" — same
- "Equation X" vs "Eq. X" — same
- References to sections/figures/tables that don't exist

### 5. Tense (Minor)
- Methods: past tense consistently
- Results: past tense
- Established facts: present tense
- Flag sections that mix without reason

### 6. Spelling & Number Formatting (Minor)
- British vs American spelling — standardize to one (default: American)
- Number formatting consistency ("1000" vs "1,000")
- Percentage formatting ("50%" consistently)

## Output Format

For each issue:
```
[CATEGORY] Line X: description
  Found: "text as written"
  Fix: "corrected text"
```

Report totals per category.

After reporting, **fix all Critical and Major issues** in `main.tex`. For Minor issues, fix only clear errors — leave stylistic choices to the author. Then compile once to verify: `latexmk -pdf -interaction=nonstopmode main.tex`. If compilation fails after fixes, revert the breaking change and report it.

$ARGUMENTS
