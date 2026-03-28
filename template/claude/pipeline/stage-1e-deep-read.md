# Stage 1e: Deep Source Reading

> **Prerequisites**: Read `pipeline/shared-protocols.md` first.

---

**Goal**: For every source with a PDF in `attachments/`, read the full paper in a dedicated agent and rewrite the source extract with comprehensive, topic-relevant content. This replaces the thin snapshots from ingestion (which only skim pages 1-5 + last 3-5) with thorough extracts that capture everything relevant to this paper's topic.

---

## Phase 1: Identify Sources to Deep-Read

1. **List all PDFs** in `attachments/` (include symlinks to the PDF cache)
2. **Parse any unparsed PDFs** — for each PDF that lacks a corresponding `.md` file in `attachments/parsed/`, run Docling to parse and then symlink the output into the project:
   ```bash
   mkdir -p attachments/parsed
   python3 scripts/parse-pdf.py "attachments/<key>.pdf"
   ```
   This creates the `.md` and `_figures/` next to the real PDF (in the cache if symlinked). Then symlink them into the project:
   ```bash
   # If the PDF is a symlink to the cache, link the parsed outputs too
   if [ -L "attachments/<key>.pdf" ]; then
       CACHE_DIR="$HOME/.research-agent/pdf-cache"
       [ -f "$CACHE_DIR/<key>.md" ] && ln -sf "$CACHE_DIR/<key>.md" "attachments/parsed/<key>.md"
       [ -d "$CACHE_DIR/<key>_figures" ] && ln -sf "$CACHE_DIR/<key>_figures" "attachments/parsed/<key>_figures"
   fi
   ```
   If `scripts/parse-pdf.py` is not available or Docling is not installed, agents will fall back to reading the PDF directly.

   **Batch shortcut**: To parse and link all unparsed PDFs at once:
   ```bash
   mkdir -p attachments/parsed
   for pdf in attachments/*.pdf; do
       key="$(basename "$pdf" .pdf)"
       [ -f "attachments/parsed/${key}.md" ] && continue
       python3 scripts/parse-pdf.py "$pdf" 2>/dev/null || true
       if [ -L "$pdf" ]; then
           CACHE_DIR="$HOME/.research-agent/pdf-cache"
           [ -f "$CACHE_DIR/${key}.md" ] && ln -sf "$CACHE_DIR/${key}.md" "attachments/parsed/${key}.md"
           [ -d "$CACHE_DIR/${key}_figures" ] && ln -sf "$CACHE_DIR/${key}_figures" "attachments/parsed/${key}_figures"
       fi
   done
   ```
3. **Match each PDF to a BibTeX key** — filename should be `<key>.pdf`. If a PDF has no matching source extract in `research/sources/`, create a minimal one first (same as `/ingest-papers` logic)
4. **Check for prior deep reads** — read each `research/sources/<key>.md` and skip if it already has `Deep-Read: true` (for resume). Before trusting the flag, verify the Content Snapshot is non-trivial (>200 words) — if the flag is set but the snapshot is thin, re-read
5. **Build the agent list** — every PDF source that hasn't been deep-read gets an agent

Report: "Stage 1e: [N] sources to deep-read ([M] already done, [K] PDFs total)"

---

## Phase 2: Spawn Deep-Read Agents

Spawn one agent per source, **all in parallel**. Each agent writes only to its own `research/sources/<key>.md` — no shared file writes, no collision risk.

**Model**: `claude-sonnet-4-6[1m]`

**Agent prompt template** — paste the TOPIC, KEY, MD_PATH (if exists), PDF_PATH, and FIGURES_PATH (if exists), plus the Source Extract Format block from `shared-protocols.md`:

```
You are a research analyst performing a deep reading of a scientific paper.

PAPER TOPIC: [TOPIC from .paper.json]
SOURCE KEY: [KEY]
PARSED MARKDOWN: [MD_PATH, e.g., attachments/parsed/smith2024.md — if exists]
PDF FILE: [PDF_PATH, e.g., attachments/smith2024.pdf — fallback if no markdown]
FIGURES DIRECTORY: [FIGURES_PATH, e.g., attachments/parsed/smith2024_figures/ — if exists]

Your task: Read this paper thoroughly and produce a comprehensive source extract that captures everything relevant to the paper topic above.

## Reading Strategy

**If a parsed markdown file exists** (PARSED MARKDOWN path above):
1. Read the markdown file — it contains the full paper text with figure references. For very large files (>2000 lines), read in chunks using offset/limit.
2. If a figures directory exists, check its contents. Use the Read tool on any figures/charts that appear important to the paper topic — Claude can interpret images.

**If no parsed markdown exists** (fallback — Docling was unavailable):
1. Read the PDF in page ranges (max 20 pages per Read call):
   - Pages 1-20, then 21-40, etc. until you've covered the full paper
   - For very long documents (>60 pages), prioritize: abstract, introduction, methodology, results, discussion, conclusion. Skim other sections for relevant content.

**In both cases:**
1. Note everything relevant to the PAPER TOPIC — methods, findings, arguments, data, definitions, frameworks, limitations, future directions
2. Also note content that could serve as contrast, context, or counterpoint to the paper topic

## Output

Read the existing source extract at research/sources/[KEY].md. Preserve these metadata fields exactly as they are:
- Citation
- DOI/URL
- BibTeX Key
- Access Level (should already be FULL-TEXT)
- Accessed Via
- Source Type (if present)
- Enrichment / Enrichment Sources (if present)

Rewrite these sections:

### Content Snapshot

Paste the most relevant excerpts from the paper — verbatim or near-verbatim. This is a record of what was actually in the paper, not your interpretation.

- Include the abstract in full
- Include key passages from every section relevant to the paper topic
- Length should be proportional to the source's relevance and size — a foundational 50-page paper needs a longer snapshot than a 6-page methods note. No word cap.
- Organize excerpts by section (Introduction, Methods, Results, Discussion, etc.) with section headers
- For each excerpt, note the approximate page number in brackets, e.g., [p.12]

### Key Findings Used

Bullet points of specific findings, data, arguments, or claims from this paper that are relevant to the PAPER TOPIC. Be specific — include numbers, effect sizes, confidence intervals, named methods, etc. where available.

For each finding, note:
- Whether it came directly from the Content Snapshot above
- How it relates to the paper topic (supports, challenges, provides context, offers methodology)

### Add Flags

Add these lines after the Provenance section:
- **Deep-Read**: true
- **Deep-Read Date**: [current ISO-8601 timestamp]

## Provenance Logging

Append one entry to research/provenance.jsonl:
{"ts":"[ISO-8601]","stage":"1e","agent":"deep-read-[KEY]","action":"research","target":"sources/[KEY]","reasoning":"Deep-read full PDF to enrich source extract for [TOPIC]","sources":["[KEY]"],"diff_summary":"Rewrote content snapshot and key findings from full PDF reading"}
```

**Resume handling**: Track completed agents in `.paper-state.json` under `stages.deep_read.agents_completed`. After each agent completes, update the list. If the pipeline is interrupted and resumed, only spawn agents for keys NOT in `agents_completed`.

**Content filter failures**: If an agent returns a `400` error with `"Output blocked by content filtering policy"`, follow the **Content Filter Fallback Protocol** in `shared-protocols.md`. The orchestrator reads the PDF directly, constructs a self-contained prompt with embedded text, and calls `scripts/openrouter-fallback.py` to get the result from an open model. The output is then written to the source extract file as normal.

---

## Phase 3: Verification

After all agents complete:

1. **Spot-check** 2-3 source extracts — verify they have substantial Content Snapshots and the `Deep-Read: true` flag
2. **Count results**: how many sources were deep-read, any failures
3. **Rebuild knowledge graph** (if `scripts/knowledge.py` exists and `OPENROUTER_API_KEY` is set):
   ```bash
   python scripts/knowledge.py build
   ```
   Run with `run_in_background: true` — the enriched source extracts will produce a richer graph. If a knowledge graph build was already triggered by Stage 1d, run `update` instead of `build`:
   ```bash
   python scripts/knowledge.py update
   ```

---

## Checkpoint

**Update source manifest**:
```bash
python3 scripts/update-manifest.py
```

Update `.paper-state.json`:
```json
"deep_read": {
  "done": true,
  "completed_at": "...",
  "sources_read": N,
  "agents_completed": ["smith2024", "jones2023", "..."],
  "agents_pending": []
}
```

Update `.paper-progress.txt`: "Stage 1e complete: [N] sources deep-read from PDFs"
