# Venue Reference

Quick-reference comparison of all supported venue formats. Each venue defines LaTeX configuration, citation style, page limits, and writing conventions.

## Comparison Table

| Venue | Document Class | Citation Style | Page Limit | Abstract Limit | Blind Review | Columns |
|-|-|-|-|-|-|-|
| `generic` | `article` | natbib | None | 200-300 words | No | Single |
| `ieee` | `IEEEtran` | Numeric | 8 pages | 200 words | Double-blind | Two |
| `acm` | `acmart` (sigconf) | natbib | 12 pages | 250 words | Double-blind | Two |
| `neurips` | `neurips_2024` | natbib | 9 pages (main) | 250 words | Double-blind | Single |
| `nature` | `article` | Numeric superscript | 3000-5000 words | 150 words | No | Single |
| `arxiv` | `article` | natbib | None | 500 words | No | Single |
| `apa` | `apa7` | apacite | None | 250 words | No | Single |

## Reference Target by Depth

| Venue | Standard Mode | Deep Mode |
|-|-|-|
| All venues | 30-50 refs | 60-80 refs |

## Venue Details

### generic

Standard journal article format. Use when no specific venue is targeted.

- **Sections**: Introduction, Related Work, Methods, Results, Discussion, Conclusion
- **Citation commands**: `\citep{}` (parenthetical), `\citet{}` (narrative)
- **Special requirements**: None
- **Best for**: Draft papers, internal reports, venue-agnostic submissions

### ieee

IEEE conference and journal format. Dense two-column layout with numeric citations.

- **Sections**: Introduction, Related Work, Proposed Method, Experimental Setup, Results, Discussion, Conclusion
- **Citation commands**: `\cite{}` (numeric)
- **Special requirements**:
  - "Proposed Method" section (not "Methods")
  - Algorithm pseudocode expected
  - Comparison tables with bold best results
  - Dense, information-rich prose
- **Best for**: IEEE conferences (CVPR, ICCV, ICRA) and IEEE Transactions journals

### acm

ACM SIGCONF double-blind format. Requires CCS concepts and keywords.

- **Sections**: Introduction, Related Work, Methodology, Evaluation, Discussion, Conclusion
- **Citation commands**: `\citep{}` (parenthetical), `\citet{}` (narrative)
- **Special requirements**:
  - CCS concepts and keywords in preamble
  - Artifact evaluation discussion
  - Reproducibility emphasis
  - 30-60 references expected
- **Best for**: ACM conferences (CHI, SIGCHI, SIGMOD, KDD)

### neurips

NeurIPS/ICML/ICLR single-column format with strict page limits.

- **Sections**: Introduction, Related Work, Methods, Experiments, Discussion, Conclusion, Broader Impact
- **Citation commands**: `\citep{}` (parenthetical), `\citet{}` (narrative)
- **Special requirements**:
  - Broader Impact statement mandatory
  - Reproducibility checklist
  - Theorem statements in main text, proofs in appendix
  - Ablation studies expected
  - Statistical significance reporting mandatory
  - 9-page main content limit (references and appendix unlimited)
- **Best for**: ML conferences (NeurIPS, ICML, ICLR, AAAI)

### nature

Nature family journals. Results appear before Methods. Accessible prose for broad readership.

- **Sections**: Introduction, Results, Discussion, Methods, Data Availability
- **Citation commands**: Numeric superscript
- **Special requirements**:
  - **Results before Methods** (critical difference from other venues)
  - 150-word abstract limit (strictly enforced)
  - 3000-5000 word main text
  - Max 8 display items (figures + tables combined)
  - Accessible prose: avoid jargon, active voice, narrative clarity
  - Data Availability statement required
- **Best for**: Nature, Nature Communications, Nature-family journals

### arxiv

Extended preprint format with no page limits. Comprehensive presentation with full detail.

- **Sections**: Introduction, Related Work, Methods, Experiments, Results, Discussion, Conclusion
- **Citation commands**: `\citep{}` (parenthetical), `\citet{}` (narrative)
- **Special requirements**:
  - 500-word abstract allowed (can be detailed)
  - Supplementary material inline (not separate)
  - Readers expect completeness and negative results
  - Reproducibility details in main text
  - Extended related work expected
- **Best for**: Preprints, technical reports, papers not targeting a specific venue

### apa

APA 7th edition for psychology and social sciences.

- **Sections**: Introduction, Literature Review, Method (Participants, Materials, Procedure), Results, Discussion
- **Citation commands**: `\citep{}` (parenthetical), `\citet{}` (narrative) via apacite
- **Special requirements**:
  - Structured Method section with Participants, Materials, Procedure subsections
  - Effect sizes for every statistical test
  - Power analysis reporting
  - APA-formatted tables (no vertical lines)
  - Running head required
- **Best for**: Psychology, education, social science journals

## Selecting a Venue

```bash
# At creation time
create-paper my-paper "Topic" --venue neurips

# The venue config is copied to .venue.json in the project
# Changing venue after creation: edit .venue.json directly
```

## Creating a Custom Venue

1. Copy the closest existing venue from `template/venues/`
2. Modify the JSON fields (see [Developer Guide](DEVELOPER-GUIDE.md#adding-a-new-venue))
3. Save to `template/venues/your-venue.json`
4. Update the `create-paper` script help text

The `writing_guide` field in the JSON is the most impactful customization. It provides prose instructions that writing agents follow for tone, structure, and venue-specific conventions.
