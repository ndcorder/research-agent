# Prepare Submission — Generate Submission-Ready Package

Prepare the paper for journal/conference submission with all required materials.

## Instructions

1. **Read `.paper.json`** for venue and author information
2. **Create submission directory**: `mkdir -p submission/`
3. **Generate the following**:

### Anonymized Version (if venue requires double-blind)
- Copy `main.tex` to `submission/main-anonymous.tex`
- Remove all author names, affiliations, emails
- Replace self-citations with "Anonymous" or "[removed for review]"
- Remove acknowledgments section
- Remove any identifying information in text (e.g., "our lab at Stanford")
- Compile the anonymous version

### Camera-Ready Version
- Copy `main.tex` to `submission/main-camera-ready.tex`
- Ensure all metadata is complete (authors, affiliations, ORCIDs)
- Apply venue-specific formatting if `venue` is set in `.paper.json`
- Compile the camera-ready version

### Supplementary Materials
- Create `submission/supplementary.tex` with:
  - Extended results tables
  - Additional figures
  - Detailed proofs (if applicable)
  - Hyperparameter details
  - Dataset descriptions
  - Compute resources used
- Compile to `submission/supplementary.pdf`

### Cover Letter
- Create `submission/cover-letter.tex` with:
  - Dear Editor/Program Chair salutation
  - Paper title and brief summary (2-3 sentences)
  - Key contribution and significance (1 paragraph)
  - Why this venue is appropriate (1 paragraph)
  - Statement of originality and no concurrent submission
  - Author contact information
- Compile to `submission/cover-letter.pdf`

### Response to Reviewers (if revising)
- If `reviews/` directory has review files, create `submission/response-to-reviewers.tex`:
  - Quote each reviewer comment
  - Provide point-by-point response
  - Reference specific changes made (page, section)
- Compile to `submission/response-to-reviewers.pdf`

### Checklist
- Create `submission/checklist.md`:
  - [ ] All figures are high-resolution (300+ DPI for raster, vector preferred)
  - [ ] References formatted per venue style
  - [ ] Page limit met
  - [ ] Abstract within word limit
  - [ ] Author information complete
  - [ ] Acknowledgments included (or removed for blind review)
  - [ ] Data availability statement
  - [ ] Code availability statement
  - [ ] Ethics statement (if applicable)
  - [ ] Conflict of interest declaration

4. **Final compilation** of all documents
5. **Report** contents of `submission/` directory

## Target Venue

$ARGUMENTS
