# Prepare Submission — Generate Submission-Ready Package

Prepare the paper for journal/conference submission with all required materials.

## Instructions

1. **Read `.paper.json`** for author and venue information
2. **Read `.venue.json`** if it exists — check the `blind_review` field to determine if anonymization is needed
3. **Create submission directory**: `mkdir -p submission/`
4. **Generate the following**:

### Anonymized Version (if `blind_review` is true in `.venue.json`)
- Copy `main.tex` to `submission/main-anonymous.tex`
- Remove all author names, affiliations, emails from the author block
- Replace `\author{...}` with `\author{Anonymous}`
- Comment out acknowledgments section
- Scan text for institution names, lab names, or other identifying info — flag them for manual review (do NOT auto-remove from body text as this is error-prone)
- Compile the anonymous version

### Camera-Ready Version
- Copy `main.tex` to `submission/main-camera-ready.tex`
- Ensure all metadata is complete (authors, affiliations from `.paper.json`)
- Compile the camera-ready version

### Supplementary Materials (if applicable)
- Only generate if the paper has content that belongs in supplementary (extended proofs, extra experiments, detailed hyperparameters)
- Read `main.tex` to identify candidates for supplementary material
- If nothing qualifies, skip this step
- If content exists: create `submission/supplementary.tex`, compile to PDF

### Cover Letter
- Create `submission/cover-letter.tex` with:
  - Paper title and brief summary (2-3 sentences)
  - Key contribution and significance (1 paragraph)
  - Why this venue is appropriate (1 paragraph)
  - Statement of originality and no concurrent submission
  - Author contact information from `.paper.json`
- Compile to `submission/cover-letter.pdf`

### Response to Reviewers (only if `reviews/` directory has review files)
- Create `submission/response-to-reviewers.tex`:
  - Quote each reviewer comment
  - Provide point-by-point response
  - Reference specific changes made (page, section)
- Compile to PDF

### Checklist
- Create `submission/checklist.md` with all items checked against the actual paper state

5. **Final compilation** of all documents
6. **Report** contents of `submission/` directory with file sizes

## Target Venue

$ARGUMENTS

If no arguments, use venue from `.paper.json`.
