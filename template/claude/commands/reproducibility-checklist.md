# Reproducibility Checklist — Verify Methods Are Complete and Reproducible

Generate and populate a reproducibility checklist based on the paper's content. Covers ML reproducibility (NeurIPS/ICML style) and general scientific reproducibility.

## Instructions

Read `main.tex` completely. Evaluate each checklist item against the paper's content.

### For each item, mark:
- **YES** — Addressed in the paper (cite the section/line)
- **NO** — Not addressed but should be (suggest where to add it)
- **N/A** — Not applicable to this paper type

---

### General Scientific Reproducibility

1. [ ] **Research question clearly stated** — Is the problem formulation unambiguous?
2. [ ] **Hypotheses stated** — Are the hypotheses or research questions explicit?
3. [ ] **Data sources described** — Where does the data come from? Can someone else get it?
4. [ ] **Data preprocessing documented** — Cleaning, filtering, normalization steps?
5. [ ] **Sample sizes reported** — Training/validation/test split sizes?
6. [ ] **Evaluation metrics defined** — Are all metrics mathematically defined?
7. [ ] **Baselines described** — Can someone reproduce the baseline results?
8. [ ] **Statistical tests identified** — Which tests, what significance level?
9. [ ] **Effect sizes reported** — Not just p-values?
10. [ ] **Limitations acknowledged** — Are methodological limitations discussed?

### ML-Specific Reproducibility (if applicable)

11. [ ] **Model architecture fully specified** — Layer types, sizes, activation functions?
12. [ ] **Hyperparameters listed** — Learning rate, batch size, optimizer, scheduler?
13. [ ] **Hyperparameter search described** — How were hyperparameters chosen? Search space?
14. [ ] **Training details** — Number of epochs, convergence criteria, early stopping?
15. [ ] **Compute resources** — GPU type, training time, number of runs?
16. [ ] **Random seeds** — Are experiments run with multiple seeds? Variance reported?
17. [ ] **Code availability** — Is code provided or will be released?
18. [ ] **Dataset availability** — Are datasets public? Licensing?
19. [ ] **Pre-trained models** — If used, which ones? Version/checkpoint?
20. [ ] **Data augmentation** — What augmentations, if any?

### Ethical Considerations (if applicable)

21. [ ] **IRB/Ethics approval** — For human subjects research?
22. [ ] **Informed consent** — If human participants involved?
23. [ ] **Data privacy** — Personally identifiable information handled?
24. [ ] **Bias discussion** — Potential biases in data or model?
25. [ ] **Environmental impact** — Carbon footprint of compute (for large-scale)?

---

## Output

1. **Generate the filled checklist** with YES/NO/N/A and specific references to paper sections
2. **Write to `research/reproducibility_checklist.md`**
3. **For every NO item**: Suggest specific text to add and where in `main.tex` to add it
4. **Add missing information** directly to `main.tex`:
   - Missing hyperparameters → add to Methods or Appendix
   - Missing compute details → add to Experiments
   - Missing data descriptions → add to Experiments setup
   - Missing code/data availability → add statement before References
5. **Compile** to verify additions don't break formatting

Report: how many items were YES, NO, and N/A. Flag critical gaps.

$ARGUMENTS
