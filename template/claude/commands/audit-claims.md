# Audit Claims — Flag Overclaims, Unsupported Statements, and Hedging Issues

Identify claims that are too strong, unsupported, or likely to trigger reviewer pushback.

## Instructions

Read `main.tex` completely. For every claim or assertion, evaluate its strength against the evidence provided.

### 1. Overclaims (Critical — rejection risk)

Flag statements that claim more than the evidence supports:

- **"novel" / "first" / "unique"** — Is it actually? Check Related Work. If prior work exists, suggest "We propose an alternative approach" instead.
- **"prove" / "demonstrate conclusively"** — Is there a formal proof? If only experimental, use "provide evidence that" or "show empirically".
- **"significantly better/outperforms"** — Is there a statistical significance test? If not, flag immediately.
- **"state-of-the-art"** — Compared against ALL recent baselines? If missing key competitors, flag.
- **"optimal" / "best"** — Can you prove optimality? Suggest "competitive" or "strong performance".
- **"always" / "never"** — Absolute claims require absolute proof.
- **"clearly" / "obviously"** — If it were obvious, you wouldn't say it. Remove.

### 2. Unsupported Claims (Critical)

- Factual claims without a citation
- Claims about other methods' limitations without evidence
- Performance claims without corresponding data in the paper
- Causal claims from correlational evidence
- Generalization claims from limited experiments

### 3. Hedge Appropriateness (Major)

- **Under-hedged**: Strong claim, weak evidence — add hedging
- **Over-hedged**: Strong evidence, wimpy language — strengthen

### 4. Scope Mismatch (Major)

- Abstract promises something the paper doesn't deliver
- Title implies broader scope than content covers
- Introduction claims not addressed in conclusion

### Output Format

```
OVERCLAIM (Critical) - Line X
  Claim: "Our method significantly outperforms all baselines"
  Issue: No statistical significance test reported
  Fix: "Our method achieves higher scores than tested baselines (Table 2)"
```

Group by severity. Count totals per category.

After reporting, **fix all Critical and Major issues** in `main.tex`. Keep the author's intent — soften language proportionally, don't make everything timid. Then compile: `latexmk -pdf -interaction=nonstopmode main.tex`

## Arguments

$ARGUMENTS

Accepts an optional section name to audit only that section. If empty, audit the entire paper.
