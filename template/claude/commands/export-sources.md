# Export Sources to Shared Knowledge Base

Export source extracts and references from this paper to the shared knowledge base at `~/.research-agent/shared-sources/`, enabling reuse across future papers.

---

**Workflow**:

1. **Read current paper context**:
   - Read `.paper.json` for the paper topic
   - Read all source extract files from `research/sources/*.md`
   - Read `references.bib` for corresponding BibTeX entries

2. **Ensure shared directory exists**:
   - Create `~/.research-agent/shared-sources/` if it does not exist

3. **Export each source extract**:
   For each file in `research/sources/*.md`:
   - Determine the BibTeX key from the filename (e.g., `smith2024.md` -> `smith2024`)
   - Check if `~/.research-agent/shared-sources/<bibtexkey>.md` already exists:
     - **If it does not exist**: Copy the source extract to the shared directory, prepending provenance metadata (see format below)
     - **If it already exists**: Compare the two versions:
       - If the existing file has a newer export date AND the same or better access level, skip (already up-to-date)
       - If the new version has a better access level (e.g., upgrading from ABSTRACT-ONLY to FULL-TEXT), replace it with the new version (merge: keep the richer content)
       - If the new version is newer by export date and same access level, replace with the new version
   - Track counts: new, updated, already up-to-date

4. **Provenance metadata format** (prepend to each exported source extract):
   ```markdown
   <!-- Shared Knowledge Base Provenance -->
   <!-- Source Project: <current directory name> -->
   <!-- Paper Topic: <topic from .paper.json> -->
   <!-- Export Date: <YYYY-MM-DD> -->

   ```
   This block goes at the very top of the file, before the original `# <Paper Title>` heading.

5. **Export BibTeX entries**:
   - Read `references.bib` from the current project
   - Read `~/.research-agent/shared-sources/references.bib` if it exists (create if not)
   - For each BibTeX entry corresponding to an exported source extract:
     - If the key does not exist in the shared references file, append it
     - If the key already exists, keep the version with more complete metadata (more fields filled)
   - Write the merged result back to `~/.research-agent/shared-sources/references.bib`

6. **Cache PDFs for cross-project reuse**:
   For each exported source that has a corresponding PDF in `attachments/<key>.pdf`:
   - If the PDF is a **regular file** (not already a symlink to the cache):
     - Extract the paper's DOI from `references.bib` and title from `research/sources/<key>.md`
     - Run: `scripts/pdf-cache.sh store "<key>" "attachments/<key>.pdf" "<title>" "<doi>" "export" "-"`
     - Replace the local file with a cache symlink: `scripts/pdf-cache.sh link "<cache_key>" "$(pwd)" "<key>"`
   - If the PDF is already a symlink: skip (already cached)
   - Track count of PDFs newly cached
   - If `scripts/pdf-cache.sh` is not available, skip this step silently

7. **Report results**:
   ```
   Exported source extracts to ~/.research-agent/shared-sources/
   - N source extracts exported total
   - N new (did not previously exist)
   - N updated (newer version or improved access level)
   - N already up-to-date (skipped)
   - N BibTeX entries added/updated in shared references.bib
   - N PDFs added to shared cache (~/.research-agent/pdf-cache/)
   ```
