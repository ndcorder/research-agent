# Audit Claims — Flag Overclaims, Unsupported Statements, and Hedging Issues

Identify claims that are too strong, unsupported, or likely to trigger reviewer pushback.

## Instructions

Read `main.tex` completely. For every claim or assertion, evaluate its strength against the evidence provided.

### 1. Overclaims (HIGH priority — rejection risk)

Flag statements that claim more than the evidence supports:

- **"novel" / "first" / "unique"** — Is it actually? Check Related Work for similar approaches. If prior work exists, suggest "We propose an alternative approach" instead.
- **"prove" / "demonstrate conclusively"** — Is there a formal proof? If only experimental evidence, use "provide evidence that" or "show empirically".
- **"significantly better/outperforms"** — Is there a statistical significance test? If not, flag immediately. Suggest adding one or softening to "achieves higher scores".
- **"state-of-the-art"** — Is it compared against ALL recent baselines? If missing key competitors, flag.
- **"optimal" / "best"** — Can you actually prove optimality? Usually not. Suggest "competitive" or "strong performance".
- **"always" / "never"** — Absolute claims require absolute proof. Almost always wrong.
- **"clearly" / "obviously"** — If it were obvious, you wouldn't need to say it. Remove.

### 2. Unsupported Claims (HIGH priority)

Flag assertions without evidence or citation:
- Factual claims about the world without a citation
- Claims about other methods' limitations without citation or evidence
- Performance claims without corresponding data in the paper
- Causal claims from correlational evidence ("X causes Y" when you only showed correlation)
- Generalization claims from limited experiments ("works for all domains" tested on one)

### 3. Hedge Appropriateness (MEDIUM priority)

Check that hedging matches evidence strength:
- **Under-hedged**: Strong claim, weak evidence → add hedging ("may", "suggests", "in our experiments")
- **Over-hedged**: Strong evidence but wimpy language → strengthen ("Our results consistently show" instead of "It might perhaps be the case")
- Missing confidence intervals or error bars on quantitative claims

### 4. Scope Mismatch (MEDIUM priority)

- Abstract claims something the paper doesn't actually deliver
- Introduction promises something the conclusion doesn't address
- Title implies broader scope than the paper covers

### 5. Limitation Honesty (LOW priority but important)

- Are limitations discussed honestly or hand-waved?
- Are obvious limitations missing? (e.g., "tested on English only" but no mention of language limitation)
- Is future work specific or vague?

## Output Format

```
OVERCLAIM (Critical) — Line X
  Claim: "Our method significantly outperforms all baselines"
  Issue: No statistical significance test reported
  Fix: "Our method achieves higher scores than tested baselines (Table 2)"

UNSUPPORTED (Critical) — Line X
  Claim: "Transformers are known to struggle with long sequences"
  Issue: No citation provided
  Fix: Add citation or rephrase: "Prior work has identified challenges with long sequences \citep{...}"

UNDER-HEDGED (Major) — Line X
  Claim: "This proves the approach generalizes"
  Issue: Tested on 2 datasets only
  Fix: "These results suggest the approach may generalize, though broader evaluation is needed"
```

After reporting, **fix all Critical and Major issues** in `main.tex`. Keep the author's voice — don't make everything timid, just make claims proportional to evidence.

$ARGUMENTS
