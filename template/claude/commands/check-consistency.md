# Check Consistency — Find Notation, Terminology, and Abbreviation Issues

Scan the paper for internal inconsistencies that reviewers will catch.

## Instructions

Read `main.tex` completely. Check for these categories of inconsistency:

### 1. Mathematical Notation
- Same concept represented with different symbols (e.g., $x$ and $X$ for the same variable, $\theta$ and $\Theta$ for the same parameter set)
- Variables used before being defined
- Variables defined but never used
- Inconsistent subscript/superscript conventions (e.g., $x_i$ in one place, $x^{(i)}$ in another)
- Same symbol used for different things in different sections
- Inconsistent use of bold for vectors/matrices vs scalar

### 2. Terminology Drift
- Same concept referred to by different names (e.g., "model", "framework", "system", "architecture" used interchangeably for the same thing)
- Inconsistent capitalization of technical terms (e.g., "Transformer" vs "transformer", "Graph Neural Network" vs "graph neural network")
- British vs American spelling mixing (e.g., "optimise" vs "optimize", "colour" vs "color")
- Inconsistent hyphenation (e.g., "self-attention" vs "self attention", "fine-tune" vs "finetune")

### 3. Abbreviations
- Abbreviations used before being defined (first occurrence should be "Full Name (ABBR)")
- Abbreviations defined more than once
- Abbreviations defined but never used again (just use the full name)
- Inconsistent use — sometimes abbreviation, sometimes full name, after the definition

### 4. Reference Consistency
- Inconsistent citation format (mixing \citep and \citet without reason)
- "Figure X" vs "Fig. X" — pick one style and stick to it
- "Section X" vs "Sec. X" — same
- "Equation X" vs "Eq. X" — same
- "Table X" vs "Tab. X" — same
- References to sections/figures/tables that don't exist

### 5. Tense Consistency
- Methods should be past tense ("we trained") or present ("we train") — but consistent
- Results should be past tense ("achieved", "outperformed")
- Established facts should be present tense ("attention is a mechanism")
- Flag sections that mix tenses without reason

### 6. Number Formatting
- Inconsistent number formatting (e.g., "1000" vs "1,000" vs "$10^3$")
- Inconsistent decimal places in reported results
- Percentage sign inconsistency ("50%" vs "50 \%" vs "50 percent")

## Output Format

For each issue found:
```
[CATEGORY] Line X: DESCRIPTION
  Found: "text as written"
  Should be: "corrected text"
  Reason: why this is inconsistent
```

Group by category. Report total issues per category.

After reporting, **fix all issues** directly in `main.tex`. Compile to verify fixes don't break anything.

$ARGUMENTS
