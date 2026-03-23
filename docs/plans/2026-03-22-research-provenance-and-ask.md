# Research Provenance, Source Extracts & /ask Command

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Capture the full research trail (search queries, tools used, URLs, raw extracts) during the pipeline, and provide a `/ask` command to query the archive after completion.

**Architecture:** Three additions to the existing command-based system: (1) a research log that every agent appends to during Stage 1, (2) source extract files saved per-cited-paper, (3) a new `/ask` command that searches all research artifacts. All are markdown files — no new dependencies. The archive command is updated to include the new artifacts.

**Tech Stack:** Markdown command files (Claude Code slash commands), no code dependencies.

---

### Task 1: Add Research Log Infrastructure to write-paper.md

**Files:**
- Modify: `template/claude/commands/write-paper.md:14` (Setup section — add `research/log.md` creation)
- Modify: `template/claude/commands/write-paper.md:85-97` (Tool Fallback Chain — add logging instructions)

**Step 1: Add log file creation to Setup**

In `write-paper.md` line 14, the setup step creates directories:
```
4. Run: `mkdir -p research reviews figures`
```

Change to:
```
4. Run: `mkdir -p research research/sources reviews figures`
5. Initialize the research log: write a header to `research/log.md`:
   ```markdown
   # Research Log

   Provenance trail of all searches, queries, and sources consulted during the research pipeline.
   Each entry records: timestamp, agent, tool used, query, result summary, and URLs/DOIs found.

   ---
   ```
```

Renumber subsequent setup steps (5→6, 6→7).

**Step 2: Add logging instructions to the Tool Fallback Chain template**

In `write-paper.md` lines 85-97 (the TOOL FALLBACK CHAIN block that gets included in every agent prompt), append after `If ALL tools fail for a query, note the gap and move on`:

```
RESEARCH LOG — After EACH tool call (success or failure), append an entry to research/log.md:
```markdown
### [TIMESTAMP] — [YOUR AGENT NAME]
- **Tool**: [tool name, e.g., mcp__perplexity__search]
- **Query**: [exact query string]
- **Result**: [SUCCESS: N papers found / FAILURE: error message / EMPTY: no results]
- **Key finds**: [1-2 sentence summary of what was found, or "N/A"]
- **URLs/DOIs**: [list any URLs or DOIs discovered]
```
This log is critical for research provenance. Do not skip it.
```

**Step 3: Verify the edit**

Run: `grep -n "research/log.md\|RESEARCH LOG\|research/sources" template/claude/commands/write-paper.md | head -10`
Expected: matches at the lines we edited.

**Step 4: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "Add research log infrastructure to write-paper pipeline"
```

---

### Task 2: Add Logging Instructions to Each Research Agent Prompt

**Files:**
- Modify: `template/claude/commands/write-paper.md:99-209` (Agent 1-5 prompts)

Each of the 5 research agent prompts needs a logging reminder. The Tool Fallback Chain template already has the instructions, but each agent prompt must explicitly reference it since agents have no shared context.

**Step 1: Add logging reminder to Agent 1 (Field Survey) — line ~121**

After the line `Do NOT fabricate any references.`, add:

```
RESEARCH LOG: After every search or tool call, append an entry to research/log.md with: timestamp, tool name, query, result summary, and URLs/DOIs found. Use the format specified in the TOOL FALLBACK instructions above.
```

**Step 2: Add the same logging reminder to Agents 2-5**

Add the identical `RESEARCH LOG:` paragraph to each agent prompt, after their final instruction line:
- Agent 2 (Methodology) — after `Full citation details for every paper. Do NOT fabricate references.` (~line 143)
- Agent 3 (Empirical) — after `Full citation details. Do NOT fabricate references.` (~line 165)
- Agent 4 (Theory) — after `Full citation details. Do NOT fabricate references.` (~line 186)
- Agent 5 (Gap Analysis) — after `This will directly inform the paper's contribution statement.` (~line 208)

**Step 3: Add logging reminder to Bibliography Builder agent — line ~230**

After `After writing references.bib, count the entries and report the total.`, add:

```
RESEARCH LOG: For every verification search, append an entry to research/log.md recording: the paper being verified, tool used, query, and result (VERIFIED/SUSPICIOUS/FABRICATED). Include the verification URL or DOI.
```

**Step 4: Verify the edits**

Run: `grep -c "RESEARCH LOG" template/claude/commands/write-paper.md`
Expected: 7 (fallback chain + 5 agents + bibliography builder)

**Step 5: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "Add research log instructions to all Stage 1 agent prompts"
```

---

### Task 3: Add Source Extract Saving to Research Agent Prompts

**Files:**
- Modify: `template/claude/commands/write-paper.md:99-231` (Agent prompts + Bibliography Builder)

When agents find key papers, they should save raw extracts (abstract + key content) as individual files in `research/sources/`.

**Step 1: Add source extract instruction to the Tool Fallback Chain block (lines 85-97)**

After the RESEARCH LOG instructions added in Task 1, add:

```
SOURCE EXTRACTS — When you find a paper that you cite in your output:
1. Create a file: research/sources/<bibtexkey>.md (e.g., research/sources/smith2024.md)
2. Include: full citation, abstract (if available), key excerpts or findings you're using, and the URL/DOI where you found it
3. Format:
```markdown
# <Paper Title>

**Citation**: <authors>, <title>, <venue>, <year>
**DOI/URL**: <doi or url>
**BibTeX Key**: <key>

## Abstract
<paste or summarize the abstract>

## Key Findings Used
<bullet points of specific findings, data, or claims you referenced from this paper>

## Source
<where this was found: which tool, which database, what query>
```
This ensures every cited claim is traceable to a specific source document.
```

**Step 2: Verify**

Run: `grep -n "SOURCE EXTRACTS\|research/sources" template/claude/commands/write-paper.md | head -5`
Expected: matches in the fallback chain section.

**Step 3: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "Add source extract saving instructions to research agents"
```

---

### Task 4: Create the /ask Command

**Files:**
- Create: `template/claude/commands/ask.md`

**Step 1: Write the command file**

Create `template/claude/commands/ask.md`:

```markdown
# Ask — Query Your Research Archive

Answer questions about the research by searching through all research artifacts, source extracts, reviews, and the manuscript itself.

## Instructions

1. **Parse the question** from $ARGUMENTS. If empty, ask the user what they want to know.

2. **Search across all research artifacts** in this priority order:
   - `research/sources/` — raw source extracts with citations and provenance (most authoritative)
   - `research/` — synthesized research notes (survey, methods, empirical, theory, gaps, thesis)
   - `reviews/` — QA feedback (technical, writing, completeness, claims audit)
   - `main.tex` — the manuscript itself
   - `references.bib` — bibliography entries
   - `research/log.md` — research provenance log (what was searched, where, when)
   - `archive/` — the full archive if it exists

   Use Grep to search for keywords from the question across all these locations. Read the most relevant files or sections.

3. **Synthesize an answer** that:
   - Directly answers the question with specific information from the research
   - Cites which file(s) the information came from (e.g., "According to research/survey.md...")
   - Includes relevant paper citations with BibTeX keys when referencing specific studies
   - Notes the provenance — which tools/databases were used to find the information (from research/log.md if available)
   - Flags if the question touches on something NOT covered in the research (a gap)

4. **If the question is about a specific paper or claim**:
   - Check `research/sources/<key>.md` for the raw source extract
   - Check `research/log.md` for when/how it was found
   - Check `main.tex` for how it's used in the manuscript
   - Provide the full trail: source → research note → manuscript

5. **If the question cannot be answered from existing research**:
   - Say so clearly
   - Suggest which databases or search tools might help find the answer
   - Offer to run a targeted search using available tools (Perplexity, domain databases, etc.)

## Example Usage

- `/ask What methods were compared for protein folding?`
- `/ask Where did the claim about 95% accuracy come from?`
- `/ask What databases were searched during research?`
- `/ask Are there any gaps in the literature coverage?`
- `/ask What did the reviewers say about the methodology?`

## Question

$ARGUMENTS
```

**Step 2: Verify the file**

Run: `cat template/claude/commands/ask.md | head -5`
Expected: shows the header lines.

**Step 3: Commit**

```bash
git add template/claude/commands/ask.md
git commit -m "Add /ask command for querying research artifacts"
```

---

### Task 5: Update CLAUDE.md with New Commands and Directory

**Files:**
- Modify: `template/claude/CLAUDE.md:7-17` (Project Structure)
- Modify: `template/claude/CLAUDE.md:63-68` (Research & References commands section)

**Step 1: Add `research/sources/` and `research/log.md` to Project Structure**

In the project structure block (lines 7-17), change:

```
research/         # Literature research outputs (created by /write-paper)
```

to:

```
research/         # Literature research outputs (created by /write-paper)
  sources/        # Raw source extracts per cited paper (abstract, key findings, provenance)
  log.md          # Research provenance log (all searches, queries, tools, results)
```

**Step 2: Add /ask to the commands list**

In the "Research & References" section (around line 63-68), add after the `/cite-network` line:

```
- `/ask` — Query research artifacts to answer questions about the research (searches sources, notes, reviews, log)
```

**Step 3: Verify**

Run: `grep -n "sources\|log.md\|/ask" template/claude/CLAUDE.md | head -10`
Expected: matches at the lines we edited.

**Step 4: Commit**

```bash
git add template/claude/CLAUDE.md
git commit -m "Document research/sources, research/log.md, and /ask command"
```

---

### Task 6: Update /archive Command to Include New Artifacts

**Files:**
- Modify: `template/claude/commands/archive.md`

**Step 1: Add sources and log to the Research section**

In archive.md, after the line about `research/ingested/` (line 23), add:

```markdown
- Copy `research/sources/` → `archive/research/sources/` (if exists — raw source extracts per cited paper with provenance)
- Copy `research/log.md` → `archive/research/log.md` (if exists — full provenance trail of all searches)
```

**Step 2: Add a Research Provenance section to the README template**

In the README template section of archive.md, after the "## Key Findings" section (around line 103), add a new section:

```markdown
## Research Provenance

[If research/log.md exists, summarize:]
- Total number of searches conducted
- Tools/databases used (list unique tools from the log)
- Date range of research activity
- Any notable search failures or gaps

See [research/log.md](research/log.md) for the complete search trail.

## Source Extracts

[If research/sources/ has files, create a table:]

| Source | Paper | Key Finding |
|-|-|-|
| [sources/smith2024.md](research/sources/smith2024.md) | Smith et al. (2024) - [title] | [one-line key finding] |

[For each .md file in research/sources/, read the first few lines to populate the table]
```

**Step 3: Update the "How to Use This Archive" section**

Add these two lines to the usage section:

```markdown
- **Trace a claim**: Check `research/sources/` for the raw source, then `research/log.md` for how it was found
- **Answer questions**: Use `/ask <question>` to search across all artifacts
```

**Step 4: Verify**

Run: `grep -n "sources\|log.md\|Provenance" template/claude/commands/archive.md | head -10`
Expected: matches at the new sections.

**Step 5: Commit**

```bash
git add template/claude/commands/archive.md
git commit -m "Update /archive to include source extracts and research log"
```

---

### Task 7: Update /clean Command

**Files:**
- Modify: `template/claude/commands/clean.md`

**Step 1: Ensure clean handles the new subdirectories**

The existing clean command already removes `research/` which includes `sources/` and `log.md`. No changes needed to the deletion logic since `rm -rf research/` handles subdirectories.

Verify this is the case:

Run: `grep -A2 "research/" template/claude/commands/clean.md`
Expected: shows `research/` listed for removal under `all` mode.

**Step 2: Commit (skip if no changes needed)**

No commit needed — existing behavior already covers this.

---

### Task 8: Update create-paper Script

**Files:**
- Modify: `create-paper:175`

**Step 1: Add research/sources to the initial directory creation**

At line 175, change:
```bash
mkdir -p .claude/commands figures attachments
```
to:
```bash
mkdir -p .claude/commands figures attachments research/sources
```

This ensures the `research/sources/` directory exists from project creation, even before the pipeline runs. Agents can immediately write source extracts without needing `mkdir`.

**Step 2: Verify**

Run: `grep "mkdir" create-paper`
Expected: shows the updated mkdir line.

**Step 3: Commit**

```bash
git add create-paper
git commit -m "Create research/sources directory on project init"
```

---

### Task 9: Final Verification

**Step 1: Check all new/modified files exist**

Run:
```bash
ls -la template/claude/commands/ask.md template/claude/commands/archive.md template/claude/commands/write-paper.md template/claude/commands/clean.md template/claude/CLAUDE.md create-paper
```
Expected: all files listed with recent modification times.

**Step 2: Verify grep counts**

Run:
```bash
echo "=== RESEARCH LOG refs in write-paper ===" && grep -c "RESEARCH LOG" template/claude/commands/write-paper.md && echo "=== SOURCE EXTRACTS refs in write-paper ===" && grep -c "SOURCE EXTRACTS\|research/sources" template/claude/commands/write-paper.md && echo "=== /ask command exists ===" && head -1 template/claude/commands/ask.md && echo "=== archive includes sources ===" && grep -c "sources" template/claude/commands/archive.md && echo "=== CLAUDE.md references ===" && grep -c "sources\|log.md\|/ask" template/claude/CLAUDE.md
```

Expected:
- RESEARCH LOG: 7
- SOURCE EXTRACTS / sources: 2+
- /ask: shows header line
- archive sources: 3+
- CLAUDE.md: 3+

**Step 3: Commit if any stragglers**

If all checks pass, no additional commit needed. If anything was missed, fix and commit.
