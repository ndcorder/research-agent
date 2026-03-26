# Import Sources from Shared Knowledge Base

Import relevant source extracts from the shared knowledge base (`~/.research-agent/shared-sources/`) into the current paper project.

**Usage**: `/import-sources <topic>` (or omit topic to use `.paper.json`)

---

**Workflow**:

1. **Check for shared knowledge base**:
   - Check if `~/.research-agent/shared-sources/` exists
   - If it does not exist, report: "No shared knowledge base found. Use `/export-sources` in a completed paper project to populate it." and stop

2. **Determine target topic**:
   - If `<topic>` argument was provided, use that as the relevance target
   - Otherwise, read `.paper.json` and use its `topic` field

3. **Assess relevance of each shared source**:
   For each `.md` file in `~/.research-agent/shared-sources/` (excluding `references.bib`):
   - Read the title, key findings, and content snapshot
   - Score relevance to the target topic:
     - **HIGH**: Directly relevant to the paper topic (same domain, overlapping research questions, methods, or findings that would be cited)
     - **MEDIUM**: Tangentially relevant (related field, similar methods applied to different problems, useful background)
     - **LOW**: Not relevant (different domain, no meaningful connection to the topic)

4. **Present summary to user**:
   ```
   Shared knowledge base: ~/.research-agent/shared-sources/
   Found N total sources. N highly relevant, N moderately relevant, N low relevance.

   Highly relevant sources:
   - <bibtexkey>: <paper title> (from project: <source project>)
   - ...

   Moderately relevant sources:
   - <bibtexkey>: <paper title> (from project: <source project>)
   - ...
   ```

5. **Import HIGH-relevance sources**:
   - For each HIGH-relevance source:
     - Check if `research/sources/<bibtexkey>.md` already exists in the current project
       - If it exists with the same or better access level, skip
       - If it exists with a worse access level, replace with the shared version
     - If it does not exist, copy the shared source to `research/sources/<bibtexkey>.md`
     - Add import provenance to the file: `<!-- Imported from shared knowledge base, originally from [source project name] on [date] -->`
   - Create `research/sources/` directory if it does not exist

6. **Import corresponding BibTeX entries**:
   - Read `~/.research-agent/shared-sources/references.bib`
   - For each imported source, find its BibTeX entry by key
   - Append new entries to `references.bib` (create if it does not exist)
   - Do not duplicate entries that already exist in `references.bib`

7. **Report results**:
   ```
   Import complete:
   - N sources imported (HIGH relevance)
   - N sources skipped (already existed with same or better access level)
   - N BibTeX entries added to references.bib
   - N MEDIUM-relevance sources available (run /import-sources again to review individually)
   ```
