#!/usr/bin/env python3
"""Generate a narrative markdown 'story' of the research process from provenance logs.

Reads research/provenance.jsonl and research/log.md, synthesizes them into a
chronological narrative showing how the paper evolved from idea to manuscript.

Usage:
    python scripts/research-story.py                    # full story
    python scripts/research-story.py --stage 3          # just the writing stage
    python scripts/research-story.py --compact          # condensed version
    python scripts/research-story.py -o story.md        # write to file
"""

import json
import sys
import re
import argparse
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

PROJECT = Path.cwd()
PROVENANCE = PROJECT / "research" / "provenance.jsonl"
LOG = PROJECT / "research" / "log.md"

# Stage metadata for narrative framing
STAGE_META = {
    "2": {
        "title": "Planning the Argument",
        "subtitle": "Thesis, outline, and claims-evidence matrix",
        "icon": "compass",
    },
    "2e": {
        "title": "Stress-Testing Assumptions",
        "subtitle": "Methodological assumptions analysis",
        "icon": "microscope",
    },
    "3": {
        "title": "Writing the Manuscript",
        "subtitle": "Section-by-section drafting",
        "icon": "pen",
    },
    "5": {
        "title": "Quality Assurance",
        "subtitle": "Peer review and revision",
        "icon": "magnifying-glass",
    },
    "1e": {
        "title": "Deep Reading",
        "subtitle": "Full-text source analysis",
        "icon": "book",
    },
    "deep-read": {
        "title": "Consolidating Deep Reads",
        "subtitle": "Updating research files with enriched evidence",
        "icon": "layers",
    },
    "auto": {
        "title": "Autonomous Improvement",
        "subtitle": "Iterative refinement cycles",
        "icon": "cycle",
    },
    "auto-1": {
        "title": "Auto-Iteration 1: Tightening",
        "subtitle": "Cutting redundancy and hedging confidence",
        "icon": "scissors",
    },
    "auto-2": {
        "title": "Auto-Iteration 2: Deepening",
        "subtitle": "Strengthening warrants and sharpening novelty",
        "icon": "arrow-down",
    },
    "auto-3": {
        "title": "Auto-Iteration 3: Polishing",
        "subtitle": "Final consistency fixes",
        "icon": "sparkle",
    },
    "1d": {
        "title": "Source Acquisition",
        "subtitle": "Obtaining full-text PDFs via the 14-resolver cascade",
        "icon": "download",
    },
}


def parse_ts(entry):
    """Extract a datetime from an entry's timestamp field."""
    raw = entry.get("ts") or entry.get("timestamp") or ""
    raw = raw.rstrip("Z")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def infer_stage(entry):
    """Infer stage for entries that lack an explicit stage field."""
    action = entry.get("action", "")
    agent = entry.get("agent", "")

    # Source acquisition / upgrade entries
    if action in ("source_acquisition", "source_upgrade", "source_create", "source_update"):
        return "1d"

    # Writing entries with section field instead of stage
    if action == "write" and entry.get("section"):
        return "3"

    # Deep-read entries
    if action == "deep_read":
        return "1e"

    # Agent name hints
    if "deep-read" in agent.lower():
        return "1e"
    if "writing" in agent.lower():
        return "3"
    if "pdf-ingestion" in agent.lower():
        return "1d"

    return "unknown"


def load_provenance():
    """Load and parse provenance.jsonl entries."""
    entries = []
    with open(PROVENANCE) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entry["_line"] = i
                entry["_dt"] = parse_ts(entry)
                # Normalize missing stage
                if not entry.get("stage"):
                    entry["stage"] = infer_stage(entry)
                # Normalize target from section field
                if not entry.get("target") and entry.get("section"):
                    subsec = entry.get("subsection", "")
                    entry["target"] = f"sec{entry['section']}" + (f"/{subsec}" if subsec else "")
                # Use description as reasoning fallback
                if not entry.get("reasoning") and entry.get("description"):
                    entry["reasoning"] = entry["description"]
                entries.append(entry)
            except json.JSONDecodeError:
                pass
    return entries


def load_log_searches():
    """Parse research/log.md for search query entries."""
    if not LOG.exists():
        return []
    searches = []
    current = {}
    with open(LOG) as f:
        for line in f:
            m = re.match(r"^### (\S+)\s*—\s*(.+)", line)
            if m:
                if current:
                    searches.append(current)
                current = {"ts": m.group(1), "agent": m.group(2).strip()}
            elif line.startswith("- **Tool**:") and current:
                current["tool"] = line.split(":", 1)[1].strip()
            elif line.startswith("- **Query**:") and current:
                current["query"] = line.split(":", 1)[1].strip()
            elif line.startswith("- **Result**:") and current:
                current["result"] = line.split(":", 1)[1].strip()
            elif line.startswith("- **Key finds**:") and current:
                current["finds"] = line.split(":", 1)[1].strip()
            elif line.startswith("- **Task**:") and current:
                current["task"] = line.split(":", 1)[1].strip()
            elif line.startswith("- **Summary**:") and current:
                current["summary"] = line.split(":", 1)[1].strip()
    if current:
        searches.append(current)
    return searches


def group_by_stage(entries):
    """Group entries by stage, preserving order."""
    groups = defaultdict(list)
    stage_order = []
    for e in entries:
        stage = e.get("stage", "unknown")
        if stage not in stage_order:
            stage_order.append(stage)
        groups[stage].append(e)
    return groups, stage_order


def summarize_actions(entries):
    """Count action types in a group of entries."""
    return Counter(e.get("action", "unknown") for e in entries)


def unique_sources(entries):
    """Collect unique sources referenced across entries."""
    sources = set()
    for e in entries:
        for s in e.get("sources", []):
            sources.add(s)
    return sorted(sources)


def unique_claims(entries):
    """Collect unique claims referenced across entries."""
    claims = set()
    for e in entries:
        for c in e.get("claims", []):
            claims.add(c)
    return sorted(claims)


def format_reasoning_quote(reasoning, max_len=0):
    """Format reasoning as a quote. If max_len > 0, truncate."""
    if not reasoning:
        return ""
    if max_len > 0 and len(reasoning) > max_len:
        return reasoning[:max_len].rsplit(" ", 1)[0] + "..."
    return reasoning


def section_target_to_label(target):
    """Convert target like 'introduction/p3' to a readable label."""
    parts = target.replace("sec:", "").replace("_", " ").replace("/", " > ")
    return parts


def render_writing_stage(entries, compact=False):
    """Render Stage 3 writing entries as a narrative."""
    lines = []
    # Group by agent
    by_agent = defaultdict(list)
    for e in entries:
        by_agent[e.get("agent", "unknown")].append(e)

    for agent, agent_entries in by_agent.items():
        agent_label = agent.replace("write-", "").replace("-", " ").title()
        if agent == "discussion-writer":
            agent_label = "Discussion"
        elif agent == "evidence-synthesis-writer":
            agent_label = "Evidence Synthesis"
        elif agent == "write-abstract":
            agent_label = "Abstract"
        elif agent == "write-conclusion":
            agent_label = "Conclusion"

        targets = [section_target_to_label(e.get("target", "")) for e in agent_entries]
        sources_used = unique_sources(agent_entries)
        claims_addressed = unique_claims(agent_entries)

        lines.append(f"**{agent_label}** ({len(agent_entries)} paragraphs)")
        if not compact:
            # Show the first entry's reasoning as the hook
            first_reasoning = agent_entries[0].get("reasoning", "")
            if first_reasoning:
                lines.append(f"> {format_reasoning_quote(first_reasoning)}")
            lines.append("")
            if sources_used:
                lines.append(f"  Sources drawn on: {', '.join(sources_used)}")
            if claims_addressed:
                lines.append(f"  Claims addressed: {', '.join(claims_addressed)}")
        lines.append("")

    return "\n".join(lines)


def render_revision_stage(entries, compact=False):
    """Render revision/auto entries as a narrative."""
    lines = []
    actions = summarize_actions(entries)

    # Group by iteration
    by_iter = defaultdict(list)
    for e in entries:
        it = e.get("iteration", e.get("qa_iteration", "?"))
        by_iter[it].append(e)

    for it, iter_entries in sorted(by_iter.items(), key=lambda x: str(x[0])):
        if it not in ("?", 0):
            lines.append(f"**Iteration {it}**")
        for e in iter_entries:
            action = e.get("action", "?")
            target = section_target_to_label(e.get("target", "?"))
            reasoning = e.get("reasoning", "")
            diff = e.get("diff_summary", "")

            action_verb = {
                "revise": "Revised",
                "cut": "Cut",
                "add": "Added",
                "reorder": "Restructured",
            }.get(action, action.title())

            if compact:
                lines.append(f"- {action_verb} **{target}**" +
                           (f": {diff}" if diff else ""))
            else:
                lines.append(f"- {action_verb} **{target}**")
                if reasoning:
                    lines.append(f"  > {format_reasoning_quote(reasoning)}")
                if diff:
                    lines.append(f"  *Change*: {diff}")
            lines.append("")

    return "\n".join(lines)


def render_deep_read_stage(entries, compact=False):
    """Render deep-read entries as a narrative."""
    lines = []
    sources_read = []
    for e in entries:
        src = (e.get("sources") or ["?"])[0]
        sources_read.append(src)
        if not compact:
            diff = e.get("diff_summary", "")
            if diff and len(diff) > 40:
                lines.append(f"- **{src}**: {diff}")
            else:
                lines.append(f"- **{src}**")

    if compact:
        lines.append(f"Read {len(sources_read)} sources in full: {', '.join(sources_read)}")

    return "\n".join(lines)


def render_source_acquisition(entries, compact=False):
    """Render source acquisition entries."""
    lines = []
    upgrades = [e for e in entries if e.get("action") in ("source_acquisition", "source_upgrade", "source_create", "source_update")]

    by_result = defaultdict(list)
    for e in upgrades:
        result = e.get("result") or e.get("to_level", "?")
        by_result[result].append(e)

    for result, result_entries in by_result.items():
        keys = [e.get("key") or e.get("target", "").split("/")[-1].replace(".md", "") for e in result_entries]
        lines.append(f"**{result}** ({len(result_entries)}): {', '.join(keys)}")
        if not compact:
            for e in result_entries:
                note = e.get("note", "")
                if note:
                    key = e.get("key", "?")
                    lines.append(f"  - {key}: {note}")
            lines.append("")

    return "\n".join(lines)


def render_planning_stage(entries, compact=False):
    """Render planning entries as a narrative."""
    lines = []
    for e in entries:
        target = e.get("target", "?")
        reasoning = e.get("reasoning", "")
        lines.append(f"**{target.title()}**")
        if reasoning:
            lines.append(f"> {format_reasoning_quote(reasoning)}")
        sources_used = e.get("sources", [])
        if sources_used:
            lines.append(f"  Informed by: {', '.join(sources_used)}")
        lines.append("")
    return "\n".join(lines)


def render_log_searches(searches, compact=False):
    """Render log.md search entries."""
    lines = []
    # Group by agent
    by_agent = defaultdict(list)
    for s in searches:
        by_agent[s.get("agent", "Unknown")].append(s)

    for agent, agent_searches in by_agent.items():
        queries = [s.get("query", s.get("task", "")) for s in agent_searches if s.get("query") or s.get("task")]
        if compact:
            lines.append(f"- **{agent}**: {len(agent_searches)} searches")
        else:
            lines.append(f"### {agent}")
            lines.append(f"{len(agent_searches)} searches conducted.")
            lines.append("")
            for s in agent_searches:
                q = s.get("query", s.get("task", ""))
                tool = s.get("tool", "")
                finds = s.get("finds", s.get("summary", ""))
                if q:
                    lines.append(f'- `{q}`' + (f" via {tool}" if tool else ""))
                    if finds and not compact:
                        lines.append(f"  Found: {finds}")
            lines.append("")

    return "\n".join(lines)


def compute_stats(entries, searches):
    """Compute summary statistics."""
    actions = summarize_actions(entries)
    all_sources = set()
    all_claims = set()
    for e in entries:
        for s in e.get("sources", []):
            all_sources.add(s)
        for c in e.get("claims", []):
            all_claims.add(c)

    stages = set(e.get("stage", "?") for e in entries)
    iterations = set()
    for e in entries:
        it = e.get("iteration")
        if it is not None and it > 0:
            iterations.add(it)

    dates = [e["_dt"] for e in entries if e.get("_dt")]
    span = ""
    if dates:
        earliest = min(dates)
        latest = max(dates)
        delta = (latest - earliest).days
        span = f"{earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')} ({delta} days)"

    return {
        "total_entries": len(entries),
        "total_searches": len(searches),
        "actions": dict(actions),
        "unique_sources": len(all_sources),
        "unique_claims": len(all_claims),
        "stages": len(stages),
        "iterations": len(iterations),
        "timespan": span,
    }


def generate_story(entries, searches, stage_filter=None, compact=False):
    """Generate the full narrative markdown."""
    lines = []

    # Title
    lines.append("# The Research Story")
    lines.append("")
    lines.append("*How this paper was built, decision by decision.*")
    lines.append("")

    # Stats overview
    stats = compute_stats(entries, searches)
    lines.append("## At a Glance")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|-|-|")
    lines.append(f"| Timespan | {stats['timespan']} |")
    lines.append(f"| Provenance entries | {stats['total_entries']} |")
    lines.append(f"| Literature searches | {stats['total_searches']} |")
    lines.append(f"| Unique sources cited | {stats['unique_sources']} |")
    lines.append(f"| Claims tracked | {stats['unique_claims']} |")
    lines.append(f"| Auto-improvement iterations | {stats['iterations']} |")
    lines.append(f"| Actions | {', '.join(f'{v} {k}' for k, v in sorted(stats['actions'].items(), key=lambda x: -x[1]))} |")
    lines.append("")

    # Group provenance by stage
    groups, stage_order = group_by_stage(entries)

    if stage_filter:
        stage_order = [s for s in stage_order if s == stage_filter]

    # Literature research (from log.md)
    if not stage_filter or stage_filter == "1":
        lines.append("---")
        lines.append("")
        lines.append("## Chapter 1: Literature Research")
        lines.append("")
        if searches:
            lines.append(f"The research began with {len(searches)} systematic searches across multiple databases.")
            lines.append("")
            lines.append(render_log_searches(searches, compact))
        else:
            lines.append("*(Search log not available)*")
        lines.append("")

    # Source acquisition (all 1d-stage entries)
    acq_entries = groups.get("1d", [])
    if acq_entries and (not stage_filter or stage_filter in ("1d", "acq")):
        lines.append("---")
        lines.append("")
        lines.append("## Chapter 2: Acquiring the Sources")
        lines.append("")
        lines.append(f"The pipeline attempted to obtain full text for every cited source, "
                     f"running a 14-resolver cascade across open-access repositories.")
        lines.append("")
        lines.append(render_source_acquisition(acq_entries, compact))
        lines.append("")

    # Render each stage
    chapter_num = 3
    for stage in stage_order:
        # Skip 1d (already rendered as Chapter 2)
        if stage == "1d":
            continue
        stage_entries = groups[stage]
        if not stage_entries:
            continue

        meta = STAGE_META.get(stage, {})
        title = meta.get("title", f"Stage {stage}")
        subtitle = meta.get("subtitle", "")

        lines.append("---")
        lines.append("")
        lines.append(f"## Chapter {chapter_num}: {title}")
        if subtitle:
            lines.append(f"*{subtitle}*")
        lines.append("")

        # Date range for this stage
        dates = [e["_dt"] for e in stage_entries if e.get("_dt")]
        if dates:
            earliest = min(dates).strftime("%Y-%m-%d %H:%M")
            latest = max(dates).strftime("%Y-%m-%d %H:%M")
            if earliest[:10] == latest[:10]:
                lines.append(f"*{earliest}*")
            else:
                lines.append(f"*{earliest} to {latest}*")
            lines.append("")

        actions = summarize_actions(stage_entries)
        lines.append(f"{len(stage_entries)} actions: {', '.join(f'{v} {k}' for k, v in sorted(actions.items(), key=lambda x: -x[1]))}")
        lines.append("")

        # Dispatch to stage-specific renderer
        if stage == "2" or stage == "2e":
            lines.append(render_planning_stage(stage_entries, compact))
        elif stage == "3":
            lines.append(render_writing_stage(stage_entries, compact))
        elif stage in ("5",):
            lines.append(render_revision_stage(stage_entries, compact))
        elif stage == "1e":
            lines.append(render_deep_read_stage(stage_entries, compact))
        elif stage == "deep-read":
            lines.append(render_revision_stage(stage_entries, compact))
        elif stage.startswith("auto"):
            lines.append(render_revision_stage(stage_entries, compact))
        else:
            # Generic rendering
            for e in stage_entries:
                action = e.get("action", "?")
                target = e.get("target", "?")
                reasoning = e.get("reasoning", "")
                lines.append(f"- **{action}** {target}")
                if reasoning and not compact:
                    lines.append(f"  > {format_reasoning_quote(reasoning)}")
            lines.append("")

        chapter_num += 1

    # Epilogue
    lines.append("---")
    lines.append("")
    lines.append("## Epilogue")
    lines.append("")
    lines.append(f"This paper went through {stats['iterations']} autonomous improvement iterations, "
                 f"drew on {stats['unique_sources']} unique sources, and tracked {stats['unique_claims']} "
                 f"claims from conception through every revision. Every paragraph can be traced back "
                 f"to the evidence and reasoning that produced it.")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate research story from provenance logs")
    parser.add_argument("--stage", help="Filter to a specific stage")
    parser.add_argument("--compact", action="store_true", help="Condensed output")
    parser.add_argument("-o", "--output", help="Write to file instead of stdout")
    args = parser.parse_args()

    if not PROVENANCE.exists():
        print(f"Error: {PROVENANCE} not found", file=sys.stderr)
        sys.exit(1)

    entries = load_provenance()
    searches = load_log_searches()
    story = generate_story(entries, searches, stage_filter=args.stage, compact=args.compact)

    if args.output:
        Path(args.output).write_text(story)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(story)


if __name__ == "__main__":
    main()
