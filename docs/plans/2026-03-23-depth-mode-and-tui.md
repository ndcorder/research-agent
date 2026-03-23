# Depth Mode & Configuration TUI

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `depth` parameter (standard/deep) that scales research effort across the pipeline, with a bash TUI in create-paper for reviewing and customizing settings before launch.

**Architecture:** Three changes: (1) bash TUI using tput in create-paper that shows editable settings and writes them to .paper.json, (2) write-paper.md reads depth from .paper.json and conditionally scales research agents, adds Stage 2c targeted research, per-section lit searches, Codex-assisted expansion, and more QA iterations, (3) remove hard word count targets throughout — let content dictate length.

**Tech Stack:** Bash (tput for TUI), markdown command files.

---

### Task 1: Build the configuration TUI in create-paper

**Files:**
- Modify: `create-paper:263-321` (replace the Summary + Launch sections)

**Step 1: Replace the Summary and Launch sections with the TUI**

Replace everything from `# ── Summary ──` (line 263) through end of file (line 322) with a TUI that:

1. Defines the configuration variables with defaults:
```bash
# ── Configuration TUI ────────────────────────────────────────
CFG_TOPIC="$TOPIC"
CFG_VENUE="$VENUE"
CFG_VENUE_NAME="$VENUE_NAME"
CFG_DEPTH="standard"
VENUES=("generic" "ieee" "acm" "neurips" "nature" "arxiv" "apa")
VENUE_NAMES=("Standard journal article" "IEEE conference/journal" "ACM conference" "NeurIPS/ICML/ICLR" "Nature family" "arXiv preprint" "APA 7th edition")
DEPTHS=("standard" "deep")

# Depth descriptions (read-only display)
declare -A DEPTH_INFO
DEPTH_INFO[standard_agents]="5"
DEPTH_INFO[standard_refs]="30-50"
DEPTH_INFO[standard_second_pass]="no"
DEPTH_INFO[standard_section_lit]="no"
DEPTH_INFO[standard_qa_iter]="5"
DEPTH_INFO[standard_codex]="1× per checkpoint"
DEPTH_INFO[deep_agents]="12 (specialized)"
DEPTH_INFO[deep_refs]="60-80"
DEPTH_INFO[deep_second_pass]="yes — thesis-informed"
DEPTH_INFO[deep_section_lit]="yes — per-section deep-dives"
DEPTH_INFO[deep_qa_iter]="8"
DEPTH_INFO[deep_codex]="2× at key checkpoints"
```

2. Implements a draw function that renders the TUI box:
```bash
SELECTED=0  # 0=topic, 1=venue, 2=depth
FIELDS=3

draw_tui() {
    local d="$CFG_DEPTH"
    tput clear
    tput cup 0 0

    # Find current venue index for display
    local vi=0
    for i in "${!VENUES[@]}"; do
        [[ "${VENUES[$i]}" == "$CFG_VENUE" ]] && vi=$i
    done

    echo -e "${bold}┌─ Paper Configuration ─────────────────────────────────┐${reset}"
    echo -e "${bold}│${reset}                                                       ${bold}│${reset}"

    # Topic row
    if [[ $SELECTED -eq 0 ]]; then
        echo -e "${bold}│${reset}  ${green}▸ Topic${reset}       ${bold}$CFG_TOPIC${reset}"
    else
        echo -e "${bold}│${reset}    Topic       $CFG_TOPIC"
    fi
    printf "${bold}│${reset}\n"

    # Venue row
    if [[ $SELECTED -eq 1 ]]; then
        echo -e "${bold}│${reset}  ${green}▸ Venue${reset}       ${bold}$CFG_VENUE${reset}  ·  ${VENUE_NAMES[$vi]}"
    else
        echo -e "${bold}│${reset}    Venue       $CFG_VENUE  ·  ${VENUE_NAMES[$vi]}"
    fi
    printf "${bold}│${reset}\n"

    # Depth row
    local std_style=""
    local deep_style=""
    if [[ "$d" == "standard" ]]; then
        std_style="${bold}${green}● standard${reset}"
        deep_style="○ deep"
    else
        std_style="○ standard"
        deep_style="${bold}${green}● deep${reset}"
    fi
    if [[ $SELECTED -eq 2 ]]; then
        echo -e "${bold}│${reset}  ${green}▸ Depth${reset}       $std_style        $deep_style"
    else
        echo -e "${bold}│${reset}    Depth       $std_style        $deep_style"
    fi
    printf "${bold}│${reset}\n"

    echo -e "${bold}│${reset}                                                       ${bold}│${reset}"
    echo -e "${bold}│${reset}  ── What ${bold}${d}${reset} means ──────────────────────────────   ${bold}│${reset}"
    echo -e "${bold}│${reset}  Research agents:       ${DEPTH_INFO[${d}_agents]}                          ${bold}│${reset}"
    echo -e "${bold}│${reset}  Reference target:      ${DEPTH_INFO[${d}_refs]}                          ${bold}│${reset}"
    echo -e "${bold}│${reset}  Second research pass:  ${DEPTH_INFO[${d}_second_pass]}                          ${bold}│${reset}"
    echo -e "${bold}│${reset}  Section lit searches:  ${DEPTH_INFO[${d}_section_lit]}                          ${bold}│${reset}"
    echo -e "${bold}│${reset}  Max QA iterations:     ${DEPTH_INFO[${d}_qa_iter]}                          ${bold}│${reset}"
    echo -e "${bold}│${reset}  Codex rounds:          ${DEPTH_INFO[${d}_codex]}                          ${bold}│${reset}"
    echo -e "${bold}│${reset}                                                       ${bold}│${reset}"
    echo -e "${bold}│${reset}  ${blue}[↑↓]${reset} Navigate  ${blue}[←→]${reset} Change  ${blue}[Enter]${reset} Launch       ${bold}│${reset}"
    echo -e "${bold}│${reset}  ${blue}[e]${reset} Edit topic  ${blue}[q]${reset} Quit                         ${bold}│${reset}"
    echo -e "${bold}└───────────────────────────────────────────────────────┘${reset}"
}
```

3. Implements the input loop:
```bash
run_tui() {
    # Hide cursor
    tput civis
    trap 'tput cnorm; tput clear' EXIT

    draw_tui

    while true; do
        # Read single keypress
        IFS= read -rsn1 key

        case "$key" in
            $'\x1b')  # Escape sequence
                read -rsn2 -t 0.1 seq
                case "$seq" in
                    '[A')  # Up arrow
                        ((SELECTED = SELECTED > 0 ? SELECTED - 1 : FIELDS - 1))
                        ;;
                    '[B')  # Down arrow
                        ((SELECTED = SELECTED < FIELDS - 1 ? SELECTED + 1 : 0))
                        ;;
                    '[C')  # Right arrow — cycle forward
                        cycle_field 1
                        ;;
                    '[D')  # Left arrow — cycle backward
                        cycle_field -1
                        ;;
                esac
                ;;
            '')  # Enter
                tput cnorm
                tput clear
                return 0
                ;;
            'q'|'Q')
                tput cnorm
                tput clear
                echo "Aborted."
                exit 0
                ;;
            'e'|'E')
                if [[ $SELECTED -eq 0 ]]; then
                    # Edit topic inline
                    tput cnorm
                    tput cup 22 0
                    read -rp "New topic: " new_topic
                    if [[ -n "$new_topic" ]]; then
                        CFG_TOPIC="$new_topic"
                    fi
                    tput civis
                fi
                ;;
        esac

        draw_tui
    done
}

cycle_field() {
    local dir=$1
    case $SELECTED in
        1)  # Venue
            local vi=0
            for i in "${!VENUES[@]}"; do
                [[ "${VENUES[$i]}" == "$CFG_VENUE" ]] && vi=$i
            done
            local len=${#VENUES[@]}
            vi=$(( (vi + dir + len) % len ))
            CFG_VENUE="${VENUES[$vi]}"
            CFG_VENUE_NAME="${VENUE_NAMES[$vi]}"
            ;;
        2)  # Depth
            if [[ "$CFG_DEPTH" == "standard" ]]; then
                CFG_DEPTH="deep"
            else
                CFG_DEPTH="standard"
            fi
            ;;
    esac
}
```

4. Runs the TUI and then writes config + launches:
```bash
# Show TUI if interactive terminal
if [[ -t 0 ]]; then
    run_tui
fi

# Update .paper.json with TUI selections
python3 -c "
import json, os
config = json.load(open('.paper.json')) if os.path.exists('.paper.json') else {}
config['topic'] = '''${CFG_TOPIC}'''
config['venue'] = '$CFG_VENUE'
config['depth'] = '$CFG_DEPTH'
json.dump(config, open('.paper.json', 'w'), indent=2)
"

# Update .venue.json if venue changed
if [[ "$CFG_VENUE" != "$VENUE" ]]; then
    cp "$VENUES_DIR/$CFG_VENUE.json" .venue.json
fi

TOPIC="$CFG_TOPIC"

echo -e "${bold}Paper project ready!${reset}"
echo ""
echo "  Project:  $(pwd)"
echo "  Venue:    $CFG_VENUE_NAME"
echo "  Depth:    $CFG_DEPTH"
echo ""

if [[ -n "$TOPIC" ]]; then
    read -p "Launch autonomous pipeline now? [Y/n] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        exec "$SCRIPT_DIR/write-paper"
    fi
else
    info "Launch when ready:"
    echo ""
    echo "  ${bold}Autonomous:${reset}  cd $(pwd) && write-paper \"your topic\""
    echo "  ${bold}Interactive:${reset} cd $(pwd) && claude"
fi
```

**Step 2: Remove the old .paper.json generation** (lines 184-209)

Since the TUI now writes .paper.json at the end (with depth included), the earlier .paper.json generation (lines 184-209) should be simplified to just create a minimal initial config that the TUI will overwrite:

```bash
# Minimal initial config (TUI will finalize)
python3 -c "
import json
config = {
    'topic': '''${TOPIC}''' if '''${TOPIC}''' else '',
    'venue': '$VENUE',
    'depth': 'standard',
    'authors': [
        {
            'name': 'First Author',
            'affiliation': 'Department, University',
            'email': 'author@example.com',
            'orcid': ''
        }
    ],
    'keywords': [],
    'funding': '',
    'conflicts': '',
    'data_availability': '',
    'code_availability': ''
}
json.dump(config, open('.paper.json', 'w'), indent=2)
"
```

**Step 3: Verify**

Run: `bash -n create-paper` (syntax check)
Expected: no errors.

Run TUI manually: `cd /tmp && create-paper tui-test "test topic"`, verify TUI renders, arrow keys work, q quits. Clean up after.

**Step 4: Commit**

```bash
git add create-paper
git commit -m "Add configuration TUI with depth mode to create-paper"
```

---

### Task 2: Add depth to .paper.json and write-paper.md setup

**Files:**
- Modify: `template/claude/commands/write-paper.md:11-25` (Setup section)

**Step 1: Add depth reading to setup**

Find the setup step that reads .paper.json (line 11):
```
1. Read `.paper.json` for topic, venue, model, and config. If it doesn't exist, create it from the topic in $ARGUMENTS.
```

Replace with:
```
1. Read `.paper.json` for topic, venue, depth, and config. If it doesn't exist, create it from the topic in $ARGUMENTS with `depth: "standard"`.
   - **depth** controls research intensity: `"standard"` (default) or `"deep"` (3× research effort).
   - Store the depth value — it determines behavior at every stage below.
```

**Step 2: Add depth-aware defaults section**

After the Checkpoint Persistence section (after the JSON example block that ends around line 55), add a new section:

```markdown
## Depth Mode

Read `depth` from `.paper.json` (default: `"standard"`). This controls research intensity across all stages.

| Setting | standard | deep |
|-|-|-|
| Stage 1 research agents | 5 | 12 (7 additional specialized agents) |
| Reference target | 30-50 | 60-80 |
| Stage 2c targeted research | skip | thesis-informed second pass (3-4 agents) |
| Stage 3 per-section lit search | skip | research agent before each writing agent |
| Stage 3 Codex expansion | fix critical issues only | also ask "what's missing?" and expand |
| Max QA iterations | 5 | 8 |
| Codex rounds per checkpoint | 1 | 2 (early + late in QA loop) |

When `depth` is `"deep"`, follow ALL deep-mode instructions marked with **[DEEP]** below. When `depth` is `"standard"`, skip them.
```

**Step 3: Verify**

Run: `grep -n "depth\|DEEP" template/claude/commands/write-paper.md | head -15`
Expected: matches in setup and depth mode sections.

**Step 4: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "Add depth mode documentation to write-paper.md setup"
```

---

### Task 3: Add 7 deep-mode research agents to Stage 1

**Files:**
- Modify: `template/claude/commands/write-paper.md` — Stage 1, after Agent 5 and before the "Note: Run agents 1-4 in parallel" line

**Step 1: Add deep-mode agents**

Find the line:
```
**Note:** Run agents 1-4 in parallel (they're independent). Run agent 5 AFTER 1-4 complete (it reads their outputs).
```

Replace with:
```
**[DEEP] Agents 6-12 — Additional Specialized Research** (model: sonnet)

If `depth` is `"deep"`, spawn 7 additional research agents IN PARALLEL alongside agents 1-4. Each gets the same TOOL FALLBACK and RESEARCH LOG instructions as agents 1-5.

**Agent 6 — "Recent Frontiers (2024-2026)"**
```
You are a research scientist focused exclusively on the MOST RECENT work.
TOPIC: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]

TOOL FALLBACK: [same chain as above]

Your task:
1. Search ONLY for papers published 2024-2026
2. Identify emerging trends, new methods, and paradigm shifts in the last 2 years
3. Note any papers that challenge established findings from earlier work
4. Identify preprints and work-in-progress that hasn't been peer-reviewed yet

Write a 1500+ word analysis to research/recent_frontiers.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same as above]
```

**Agent 7 — "Negative Results & Failed Approaches"**
```
You are a research scientist studying what DIDN'T work.
TOPIC: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]

TOOL FALLBACK: [same chain as above]

Your task:
1. Find papers reporting negative results, null findings, or failed approaches
2. Document approaches that were tried and abandoned — and WHY
3. Identify common pitfalls and known failure modes
4. Note any replication failures or controversial findings

Write a 1200+ word analysis to research/negative_results.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same as above]
```

**Agent 8 — "Cross-Disciplinary Insights"**
```
You are a cross-disciplinary researcher looking for insights from ADJACENT fields.
TOPIC: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]

TOOL FALLBACK: [same chain as above]

Your task:
1. Identify related techniques or approaches from other fields that could apply
2. Find analogous problems solved in different domains
3. Note any interdisciplinary collaborations or hybrid methods
4. Look for theoretical frameworks from other fields that might provide insight

Write a 1200+ word analysis to research/cross_disciplinary.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same as above]
```

**Agent 9 — "Datasets, Benchmarks & Reproducibility"**
```
You are a research engineer focused on data and reproducibility.
TOPIC: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]

TOOL FALLBACK: [same chain as above]

Your task:
1. Catalog ALL standard datasets and benchmarks used in this field
2. Document data availability, licensing, and access methods
3. Find open-source implementations and code repositories
4. Note reproducibility studies — which results have been independently verified?
5. Identify gaps in available data or benchmarks

Write a 1500+ word analysis to research/datasets_reproducibility.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same as above]
```

**Agent 10 — "Industry & Applied Work"**
```
You are a research analyst tracking industry and applied implementations.
TOPIC: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]

TOOL FALLBACK: [same chain as above]

Your task:
1. Find industry applications, deployed systems, and commercial use of these methods
2. Identify patents, technical reports, and white papers from companies
3. Note the gap between academic benchmarks and real-world performance
4. Document any industry-specific constraints or requirements

Write a 1200+ word analysis to research/industry_applied.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same as above]
```

**Agent 11 — "Competing Hypotheses & Debates"**
```
You are a research scientist mapping the intellectual landscape of active debates.
TOPIC: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]

TOOL FALLBACK: [same chain as above]

Your task:
1. Identify active scientific debates and competing hypotheses
2. Map the different "camps" or schools of thought and their key proponents
3. Document the strongest arguments on each side
4. Note any emerging consensus or unresolved tensions

Write a 1200+ word analysis to research/competing_hypotheses.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same as above]
```

**Agent 12 — "Intellectual Lineage"**
```
You are a research historian tracing the intellectual roots of this field.
TOPIC: [TOPIC]
DOMAIN: [DETECTED_DOMAIN]

TOOL FALLBACK: [same chain as above]

Your task:
1. Identify the 5-10 most foundational papers that shaped this field
2. Trace how ideas evolved from those seminal works to current approaches
3. Map the citation lineage — which breakthroughs enabled which subsequent work?
4. Identify any paradigm shifts and what caused them

Write a 1200+ word analysis to research/intellectual_lineage.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same as above]
```

**Note:** In deep mode, run agents 1-4 AND 6-12 in parallel (they're all independent). Run agent 5 AFTER ALL complete (it reads their outputs — including the 7 deep-mode files). The bibliography builder then processes ALL research files.
```

If depth is standard, the existing note stays:
```
**Note:** Run agents 1-4 in parallel (they're independent). Run agent 5 AFTER 1-4 complete (it reads their outputs).
```

**Step 2: Update the bibliography builder reference target**

Find in the bibliography checkpoint:
```
**Checkpoint**: Count entries in `references.bib`. If fewer than 25, report which research areas are underrepresented and spawn additional targeted research agents for those areas.
```

Replace with:
```
**Checkpoint**: Count entries in `references.bib`. If depth is `"standard"` and fewer than 25, or if depth is `"deep"` and fewer than 50, report which research areas are underrepresented and spawn additional targeted research agents for those areas.
```

**Step 3: Verify**

Run: `grep -c "Agent [0-9]" template/claude/commands/write-paper.md` → expect 12+
Run: `grep -c "\[DEEP\]" template/claude/commands/write-paper.md` → expect 1+

**Step 4: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "Add 7 deep-mode specialized research agents to Stage 1"
```

---

### Task 4: Add Stage 2c — Thesis-Informed Targeted Research

**Files:**
- Modify: `template/claude/commands/write-paper.md` — insert after Stage 2b (Codex Thesis Stress-Test), before Stage 3

**Step 1: Add Stage 2c**

Find:
```
Update `.paper-state.json`: mark `codex_thesis` as done.

---

### Stage 3: Section-by-Section Writing
```

Replace with:
```
Update `.paper-state.json`: mark `codex_thesis` as done.

---

### Stage 2c: Thesis-Informed Targeted Research [DEEP]

**Skip this stage if depth is `"standard"`.** This stage only runs in deep mode.

Now that the thesis, contribution statement, and outline are finalized, run a SECOND targeted research pass. The first pass (Stage 1) was broad. This pass is surgical — searching for literature that directly supports, challenges, or contextualizes the specific claims this paper will make.

Read `research/thesis.md` and the outline in `main.tex`. For each major claim or section, spawn a targeted research agent.

Spawn **3-4 agents in parallel** (model: sonnet):

**Agent A — "Supporting Evidence"**
```
You are a research scientist gathering evidence to SUPPORT a specific thesis.
THESIS: [paste from research/thesis.md]
KEY CLAIMS: [list the 3-5 main claims from the thesis]

TOOL FALLBACK: [same chain as Stage 1]

Your task:
1. For EACH key claim, find 3-5 papers that provide direct supporting evidence
2. Find experimental results, datasets, or case studies that validate the approach
3. Look for meta-analyses or systematic reviews that corroborate the position
4. Ensure the evidence is strong enough to withstand peer review scrutiny

Write findings to research/targeted_support.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same format]
```

**Agent B — "Counterarguments & Rebuttals"**
```
You are a devil's advocate researcher looking for evidence AGAINST a thesis.
THESIS: [paste from research/thesis.md]
KEY CLAIMS: [list the 3-5 main claims]

TOOL FALLBACK: [same chain as Stage 1]

Your task:
1. Find papers that contradict or challenge each key claim
2. Identify the strongest counterarguments a reviewer would raise
3. Search for alternative explanations for any claimed results
4. Find evidence for competing approaches that might outperform this one

Write findings to research/targeted_counter.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same format]
```

**Agent C — "Methodological Precedents"**
```
You are a methods specialist finding precedents for the proposed approach.
PROPOSED METHOD: [paste Methods outline from main.tex]

TOOL FALLBACK: [same chain as Stage 1]

Your task:
1. Find papers that used similar methods — especially in different contexts
2. Document known limitations and failure modes of the proposed techniques
3. Find best practices, recommended parameters, and implementation guidance
4. Identify any methodological innovations that should be incorporated

Write findings to research/targeted_methods.md.
Full citation details. Do NOT fabricate references.
RESEARCH LOG: [same format]
```

After all agents complete, run the bibliography builder again to add new references to `references.bib`.

**Checkpoint**: Verify targeted research files exist. Update `.paper-state.json`: mark `targeted_research` as done.

---

### Stage 3: Section-by-Section Writing
```

**Step 2: Verify**

Run: `grep -n "Stage 2c\|targeted_research\|DEEP.*stage\|Thesis-Informed" template/claude/commands/write-paper.md | head -10`

**Step 3: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "Add Stage 2c: thesis-informed targeted research (deep mode)"
```

---

### Task 5: Add per-section literature deep-dives and Codex expansion to Stage 3

**Files:**
- Modify: `template/claude/commands/write-paper.md` — Stage 3, before the writing agent prompts

**Step 1: Add deep-mode per-section research instruction**

Find the line:
```
**Every writing agent prompt MUST include:**
```

Before it, add:
```
**[DEEP] Per-Section Literature Deep-Dives**

If depth is `"deep"`, BEFORE each writing agent starts, spawn a quick **section research agent** (model: sonnet) to find literature specific to that section's topic:

```
You are a focused research assistant. You have 1 task: find papers relevant to the [SECTION] section of a paper about [TOPIC].

The section outline says: [paste the % OUTLINE: comments for this section from main.tex]

TOOL FALLBACK: [same chain as Stage 1]

Search for:
1. Papers directly relevant to what this section will discuss
2. Specific data points, statistics, or results this section should cite
3. Recent work (2024-2026) on this specific subtopic

Write a concise list of 5-10 relevant papers with key findings to research/section_lit_[SECTION].md.
Full citation details. Add new references to references.bib.
RESEARCH LOG: [same format]
```

The writing agent for that section should then ALSO read `research/section_lit_[SECTION].md` for fresh, section-specific references.

```

**Step 2: Add deep-mode Codex expansion instruction**

Find the existing Stage 3 Codex spot-check block (the one we added in the previous plan that starts with "After each major section completes"). After that entire block, add:

```
**[DEEP] Codex-Assisted Expansion**

If depth is `"deep"`, after the spot-check, also call Codex to identify gaps:

```
mcp__codex-bridge__codex_ask({
  prompt: "You are a domain expert reviewing the [SECTION] section. What substantive content is MISSING that a knowledgeable reviewer would expect to see? Don't focus on writing quality — focus on intellectual completeness. What arguments, evidence, comparisons, or nuances are absent? Be specific.",
  context: "[paste the section content from main.tex]"
})
```

If Codex identifies substantive gaps, spawn an **expansion agent** (model: opus) to address them:
```
Read main.tex. The [SECTION] section has been reviewed and these content gaps were identified:
[paste Codex response]

Address each gap by adding substantive content — new paragraphs, additional citations from references.bib, deeper analysis. Do NOT pad with filler. Only add content that addresses the identified gaps.
Invoke the `scientific-writing` skill.
Edit main.tex directly.
```
```

**Step 3: Verify**

Run: `grep -c "\[DEEP\]" template/claude/commands/write-paper.md` → should be 3+ (Stage 1 agents, per-section lit, Codex expansion)

**Step 4: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "Add per-section lit searches and Codex expansion for deep mode"
```

---

### Task 6: Scale QA and Codex rounds for deep mode

**Files:**
- Modify: `template/claude/commands/write-paper.md` — Stage 5

**Step 1: Update QA loop iteration limit**

Find:
```
**This stage LOOPS until all quality criteria pass.** Maximum 5 iterations.
```

Replace with:
```
**This stage LOOPS until all quality criteria pass.** Maximum 5 iterations (or 8 if depth is `"deep"`).
```

**Step 2: Add second Codex round for deep mode**

Find the Step 5d Quality Gate Check section:
```
#### Step 5d: Quality Gate Check

After revision, check ALL criteria from the table below. If any fail, loop back to Step 5a with fresh reviewers. If all pass, proceed to Stage 6.
```

Replace with:
```
#### Step 5d: Quality Gate Check

After revision, check ALL criteria from the table below. If any fail, loop back to Step 5a with fresh reviewers. If all pass, proceed to Stage 6.

**[DEEP]** If depth is `"deep"` and this is the FINAL QA iteration (all criteria pass), run one additional Codex review before exiting:

```
mcp__codex-bridge__codex_review({
  prompt: "Final deep review of this manuscript. This paper has already passed multiple rounds of QA. Look for subtle issues that earlier reviews missed: (1) Implicit assumptions never made explicit (2) Logical leaps that seem fine on first read but don't hold up (3) Claims that are technically true but misleading (4) Missing qualifications or edge cases (5) Opportunities to strengthen the argument that were overlooked.",
  context: "[paste the full content of main.tex]",
  evidence_mode: true
})
```

Write to `reviews/codex_final_deep.md`. If this surfaces CRITICAL issues, do one more fix-and-review cycle. Otherwise, proceed.
```

**Step 3: Verify**

Run: `grep -n "codex_final_deep\|8 if depth" template/claude/commands/write-paper.md | head -5`

**Step 4: Commit**

```bash
git add template/claude/commands/write-paper.md
git commit -m "Scale QA iterations and add final Codex review for deep mode"
```

---

### Task 7: Remove hard word count targets from pipeline

**Files:**
- Modify: `template/claude/commands/write-paper.md` — Stage 3 writing table and expansion logic

**Step 1: Replace the section writing order table**

Find the table:
```
| Order | Section | Target Words | Key instruction |
|-|-|-|-|
| 1 | Introduction | 1200+ | Broad context → specific problem → contribution → findings preview → paper organization. Cite 8-12 works. |
| 2 | Related Work | 2000+ | Organize THEMATICALLY in 3-5 subsections. Discuss 3-5 papers per theme. Position this work explicitly. Cite 15-20 works. |
| 3 | Methods/Approach | 2500+ | Full detail for reproduction. Math in equation/align environments. Pseudocode if applicable. Design rationale. Use `sympy` skill for formulations if appropriate. |
| 4 | Results/Experiments | 2000+ | Setup → quantitative results (tables) → ablations → qualitative analysis. At least 2 booktabs tables. Use `statistical-analysis` skill, `matplotlib` or `scientific-visualization` skill for figures. |
| 5 | Discussion | 1500+ | Interpret findings → compare with prior work → limitations (be honest) → broader implications → future work. Use `scientific-critical-thinking` skill. |
| 6 | Conclusion | 600+ | Restate problem → summarize approach → highlight key results (with numbers) → impact statement. No new information. |
| 7 | Abstract | 250+ | Written LAST. Self-contained. Specific quantitative claims. Read the ENTIRE paper first. |
```

Replace with:
```
| Order | Section | Guidance | Key instruction |
|-|-|-|-|
| 1 | Introduction | Comprehensive | Broad context → specific problem → contribution → findings preview → paper organization. Cite 8-12 works. Write until the reader fully understands the problem and why this work matters. |
| 2 | Related Work | Thorough | Organize THEMATICALLY in 3-5 subsections. Discuss 3-5 papers per theme. Position this work explicitly. Cite 15-20 works. Cover the field completely — don't leave gaps a reviewer would notice. |
| 3 | Methods/Approach | Exhaustive | Full detail for reproduction. Math in equation/align environments. Pseudocode if applicable. Design rationale. Use `sympy` skill for formulations if appropriate. Another researcher should be able to reproduce this from your description alone. |
| 4 | Results/Experiments | Data-driven | Setup → quantitative results (tables) → ablations → qualitative analysis. At least 2 booktabs tables. Use `statistical-analysis` skill, `matplotlib` or `scientific-visualization` skill for figures. Present all results needed to support your claims. |
| 5 | Discussion | Reflective | Interpret findings → compare with prior work → limitations (be honest) → broader implications → future work. Use `scientific-critical-thinking` skill. Be thorough on limitations — reviewers respect honesty. |
| 6 | Conclusion | Concise | Restate problem → summarize approach → highlight key results (with numbers) → impact statement. No new information. Brief and impactful. |
| 7 | Abstract | Self-contained | Written LAST. Specific quantitative claims. Read the ENTIRE paper first. Must stand alone — a reader should understand the full contribution from the abstract. |
```

**Step 2: Replace the expansion trigger**

Find:
```
**After each writing agent completes**, check the word count of that section inline. If under 70% of target, immediately spawn an expansion agent:
```

Replace with:
```
**After each writing agent completes**, assess whether the section is substantively complete. If the section feels thin — missing depth, lacking citations, skipping over important points, or leaving obvious gaps — spawn an expansion agent:
```

**Step 3: Update the expansion agent prompt**

Find:
```
The [SECTION] section in main.tex is currently [N] words. Target: [TARGET]+.
Read main.tex. Invoke the `scientific-writing` skill.
EXPAND the section by adding depth, subsections, citations, analysis, and formal detail.
Do NOT delete existing content. Only ADD.
Target: [TARGET]+ words total for this section.
Edit main.tex directly.
```

Replace with:
```
The [SECTION] section in main.tex needs more depth.
Read main.tex. Invoke the `scientific-writing` skill.
EXPAND the section by adding depth, subsections, citations, analysis, and formal detail.
Do NOT delete existing content. Only ADD substantive content — not filler.
Write until the section is comprehensive. A domain expert should not feel anything important was left unsaid.
Edit main.tex directly.
```

**Step 4: Update the Quality Criteria table**

Find the quality criteria table and replace hard word count rows. Find:
```
| Total word count | 8000+ (or .paper.json target_words) |
| Introduction | 1000+ words |
| Related Work / Background | 1500+ words |
| Methods / Approach | 2000+ words |
| Results / Experiments | 1500+ words |
| Discussion | 1200+ words |
| Conclusion | 500+ words |
| Abstract | 200+ words |
```

Replace with:
```
| Sections substantively complete | No obvious gaps, thin arguments, or missing depth |
| Introduction | Sets up the problem, contribution, and paper structure clearly |
| Related Work / Background | Covers the field thoroughly — no major omissions a reviewer would flag |
| Methods / Approach | Detailed enough for reproduction by an independent researcher |
| Results / Experiments | All claims supported by presented evidence |
| Discussion | Honest limitations, meaningful comparisons with prior work |
| Conclusion | Concise summary with specific results |
| Abstract | Self-contained, specific, quantitative where possible |
```

**Step 5: Remove target_words from .paper.json generation in create-paper**

In `create-paper`, find the line in the .paper.json generation:
```
    'target_words': 8000,
```

Remove this line entirely.

**Step 6: Update Rule 6 about word counts**

Find:
```
6. **Check word counts after every writing agent.** Expand immediately if under 70% of target. The expansion agent should use `model: "opus"`.
```

Replace with:
```
6. **Assess completeness after every writing agent.** If the section lacks depth, is missing citations, or leaves obvious gaps, expand immediately. The expansion agent should use `model: "opus"`.
```

**Step 7: Update Rule 12 about venue word targets**

Find:
```
12. **Venue-aware word targets.** If `.venue.json` has a `page_limit`, scale section word targets proportionally. An 8-page IEEE paper needs ~6000 words total, not 8000+. Read the venue config and adjust.
```

Replace with:
```
12. **Venue-aware length.** If `.venue.json` has a `page_limit`, respect it. An 8-page IEEE paper must be concise — prioritize depth over breadth and cut less critical content. Read the venue config and adjust scope accordingly.
```

**Step 8: Verify**

Run: `grep -c "Target Words\|target_words\|1200+\|2000+\|2500+" template/claude/commands/write-paper.md` → expect 0 (all removed from the table and criteria, though deep-mode agent prompts in Task 3 still say "1200+ word analysis" which is fine — that's research notes, not manuscript sections)
Run: `grep "substantive\|comprehensive\|obvious gaps" template/claude/commands/write-paper.md | head -5` → expect matches

**Step 9: Commit**

```bash
git add template/claude/commands/write-paper.md create-paper
git commit -m "Remove hard word targets — let content dictate length"
```

---

### Task 8: Update CLAUDE.md and write-paper launcher

**Files:**
- Modify: `template/claude/CLAUDE.md`
- Modify: `write-paper:55-57`

**Step 1: Add depth to CLAUDE.md pipeline description**

Find:
```
This runs for 1-4 hours. Agents use `model: "opus"` for writing, `model: "sonnet"` for research/review.
```

Replace with:
```
This runs for 1-4 hours (standard) or 3-8 hours (deep). Agents use `model: "opus"` for writing, `model: "sonnet"` for research/review. Set `depth` in `.paper.json` to `"deep"` for 3× research effort — more agents, targeted second pass, per-section literature searches, and additional Codex rounds.
```

**Step 2: Update write-paper launcher to show depth**

In `write-paper`, find:
```
echo -e "${blue}→${reset} Launching autonomous paper writing pipeline"
echo -e "  Topic: ${bold}$TOPIC${reset}"
echo -e "  This will take 1-4 hours for a journal-quality paper."
```

Replace with:
```
DEPTH=$(python3 -c "import json; print(json.load(open('.paper.json')).get('depth', 'standard'))" 2>/dev/null || echo "standard")
echo -e "${blue}→${reset} Launching autonomous paper writing pipeline"
echo -e "  Topic: ${bold}$TOPIC${reset}"
echo -e "  Depth: ${bold}$DEPTH${reset}"
if [[ "$DEPTH" == "deep" ]]; then
    echo -e "  This will take 3-8 hours for a deeply researched paper."
else
    echo -e "  This will take 1-4 hours for a journal-quality paper."
fi
```

**Step 3: Verify**

Run: `grep "depth\|DEPTH\|deep" write-paper | head -5`
Run: `grep "depth\|deep" template/claude/CLAUDE.md | head -5`

**Step 4: Commit**

```bash
git add template/claude/CLAUDE.md write-paper
git commit -m "Document depth mode in CLAUDE.md and show depth in write-paper launcher"
```

---

### Task 9: Final verification

**Step 1: Syntax check create-paper**

Run: `bash -n create-paper`
Expected: no errors.

**Step 2: Count deep-mode markers**

Run: `grep -c "\[DEEP\]" template/claude/commands/write-paper.md`
Expected: 4+ (Stage 1 agents, Stage 2c, per-section lit, Codex expansion, QA scaling)

**Step 3: Verify no hard word targets in manuscript sections**

Run: `grep -n "1000+\|1200+\|1500+\|2000+\|2500+" template/claude/commands/write-paper.md | grep -v "research agent\|analysis to\|word analysis\|word survey\|word comprehensive\|word gap"`
Expected: no matches from the section writing table or quality criteria (research agent targets are fine).

**Step 4: Verify depth flows end-to-end**

Run: `grep -n "depth" create-paper write-paper template/claude/commands/write-paper.md template/claude/CLAUDE.md | head -20`
Expected: matches in all 4 files.
