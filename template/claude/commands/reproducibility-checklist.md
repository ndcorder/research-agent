# Reproducibility Checklist — Verify Methods Are Complete and Reproducible

Generate and populate a reproducibility checklist based on the paper's content.

## Instructions

Read `main.tex` completely. Evaluate each checklist item against the paper's content.

### For each item, mark:
- **YES** — Addressed in the paper (cite the section and line)
- **NO** — Not addressed but should be
- **N/A** — Not applicable (explain why)

### General Scientific Reproducibility

1. Research question clearly stated
2. Hypotheses or research questions explicit
3. Data sources described (where does data come from, can others get it)
4. Data preprocessing documented (cleaning, filtering, normalization)
5. Sample sizes reported (train/val/test splits)
6. Evaluation metrics mathematically defined
7. Baselines described with enough detail to reproduce
8. Statistical tests identified (which tests, significance level)
9. Effect sizes reported (not just p-values)
10. Limitations acknowledged

### ML-Specific (apply if paper involves machine learning — check for keywords like "model", "training", "neural", "learning" in main.tex)

11. Model architecture fully specified (layers, sizes, activations)
12. Hyperparameters listed (learning rate, batch size, optimizer)
13. Hyperparameter search described (method, search space)
14. Training details (epochs, convergence, early stopping)
15. Compute resources (GPU type, training time, number of runs)
16. Random seeds and variance reported
17. Code availability stated
18. Dataset availability and licensing stated
19. Pre-trained models identified (which, version)

### Ethical Considerations (apply if paper involves human subjects, sensitive data, or large compute)

20. IRB/Ethics approval (for human subjects)
21. Data privacy handling
22. Bias discussion
23. Environmental impact (for large-scale compute)

## Output

1. **Write the filled checklist** to `research/reproducibility_checklist.md` with YES/NO/N/A and section references
2. **For every NO item**: suggest specific text to add and where
3. **Offer to add missing information** to `main.tex` — list what would be added and where, but only edit if the user confirms or if this command was invoked by `/write-paper` (autonomous mode)
4. Report summary: X/Y items addressed

$ARGUMENTS
