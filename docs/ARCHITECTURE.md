# Architecture

Visual guide to the Research Agent system architecture, pipeline flow, data model, and agent orchestration.

## System Overview

```mermaid
graph TB
    subgraph "User Interface"
        CLI["create-paper / write-paper CLI"]
        Claude["Claude Code CLI"]
    end

    subgraph "Orchestration Layer"
        WP["/write-paper Orchestrator"]
        Auto["/auto Improvement Loop"]
        Manual["42 Slash Commands"]
    end

    subgraph "Pipeline Stages"
        S1["Stage 1: Research"]
        S1b["Stage 1b: Snowballing"]
        S1b2["Stage 1b-ii: Co-Citation"]
        S1c["Stage 1c: Codex Cross-Check"]
        S1d["Stage 1d: Source Acquisition"]
        S1e["Stage 1e: Deep Read"]
        S1f["Stage 1f: Synthesis"]
        S2["Stage 2: Planning"]
        S2b["Stage 2b: Codex Thesis"]
        S2c["Stage 2c: Targeted Research"]
        S2d["Stage 2d: Novelty Check"]
        S2e["Stage 2e: Assumptions"]
        S3["Stage 3: Writing"]
        S4["Stage 4: Figures"]
        S5["Stage 5: QA Loop"]
        S5p["Stage 5+: Post-QA"]
        S6["Stage 6: Finalization"]
    end

    subgraph "External Services"
        SS["Semantic Scholar API"]
        CR["CrossRef API"]
        UP["Unpaywall API"]
        OA["OpenAlex API"]
        PMC["PubMed Central"]
        CORE["CORE API"]
        Perp["Perplexity"]
        Web["Web Search"]
        FC["Firecrawl"]
    end

    subgraph "Optional Integrations"
        Codex["Codex Bridge"]
        LightRAG["LightRAG Knowledge Graph"]
        Praxis["Praxis Scientific Toolkit"]
    end

    subgraph "Output Artifacts"
        PDF["main.pdf"]
        Prov["provenance.jsonl"]
        Archive["archive/"]
    end

    CLI --> WP
    Claude --> Manual
    Claude --> Auto
    WP --> S1 --> S1b --> S1b2 --> S1c --> S1d
    S1d --> S2 --> S2b --> S2c --> S2d --> S2e
    S2e --> S3 --> S4 --> S5 --> S5p --> S6
    S6 --> PDF
    S6 --> Prov
    S6 --> Archive
    Auto --> S5

    S1 --> Perp & Web & FC & SS
    S1b --> SS
    S1b2 --> SS
    S1d --> S1e --> S1f --> S2
    S1d --> UP & OA & PMC & CORE
    S5p --> CR

    S1c -.-> Codex
    S2b -.-> Codex
    S5 -.-> Codex
    S1d -.-> LightRAG
    S4 -.-> Praxis
```

## Pipeline Flow

The `/write-paper` orchestrator reads stage instructions from `pipeline/*.md` files on-demand. Each file is read fresh from disk before execution, preventing context compression from degrading late-stage instructions.

```mermaid
flowchart TD
    Start(["/write-paper topic"]) --> ReadConfig["Read .paper.json\n+ .venue.json"]
    ReadConfig --> ReadProto["Read shared-protocols.md"]
    ReadProto --> DetectDomain["Detect domain\n→ select skills"]

    DetectDomain --> S1["Stage 1: Deep Research"]
    S1 --> |"Read stage-1-research.md"| ResearchAgents

    subgraph ResearchAgents ["Parallel Research Agents"]
        direction LR
        A1["Field Survey"]
        A2["Methodology"]
        A3["Empirical"]
        A4["Theory"]
        A5["Gap Analysis"]
        A6["+ 7 more\n(deep mode)"]
    end

    ResearchAgents --> BibBuild["Bibliography Builder\n→ references.bib"]
    BibBuild --> S1b["Stage 1b: Snowballing\n(backward + forward)"]
    S1b --> S1b2["Stage 1b-ii: Co-Citation\nAnalysis"]
    S1b2 --> S1c{"Codex\ninstalled?"}
    S1c --> |yes| CrossCheck["Codex Cross-Check"]
    S1c --> |no| S1d
    CrossCheck --> S1d["Stage 1d: Source Acquisition"]

    S1d --> AuditSrc["Audit access levels\nFULL-TEXT / ABSTRACT / METADATA"]
    AuditSrc --> OAResolve["OA Resolution\n(7 APIs)"]
    OAResolve --> UserPause{"Paywalled\nPDFs remain?"}
    UserPause --> |yes| WaitUser["Pause for user\nto add PDFs"]
    UserPause --> |no| S1eFlow
    WaitUser --> S1eFlow["Stage 1e: Deep Read\n(parallel PDF agents)"]
    S1eFlow --> KG{"Knowledge\ngraph enabled?"}
    KG --> |yes| BuildKG["Build LightRAG"]
    KG --> |no| S1fFlow
    BuildKG --> S1fFlow["Stage 1f: Synthesis\n(cross-source analysis)"]
    S1fFlow --> S2

    S2["Stage 2: Planning"] --> Thesis["Thesis + Contribution"]
    Thesis --> Outline["Detailed Outline\nwith word targets"]
    Outline --> ClaimsMatrix["Claims-Evidence Matrix\n(warrant, qualifier, rebuttal)"]
    ClaimsMatrix --> S2b2{"Codex?"}
    S2b2 --> |yes| ThesisStress["Codex Thesis\nStress-Test"]
    S2b2 --> |no| Deep1
    ThesisStress --> Deep1{"Deep\nmode?"}
    Deep1 --> |yes| S2c["Targeted Research\n(3 agents)"]
    Deep1 --> |no| S2d
    S2c --> S2d["Novelty Check\n(arXiv, Scholar, DBLP)"]
    S2d --> NovelDecision{"Novel?"}
    NovelDecision --> |no| STOP([Stop Pipeline])
    NovelDecision --> |yes| S2e["Assumptions Analysis"]

    S2e --> S3["Stage 3: Sequential Writing"]
    S3 --> WriteLoop

    subgraph WriteLoop ["Per-Section Agents (Opus)"]
        direction TB
        W1["Introduction"] --> W2["Related Work"]
        W2 --> W3["Methods"]
        W3 --> W4["Results"]
        W4 --> W5["Discussion"]
        W5 --> W6["Conclusion"]
        W6 --> W7["Abstract"]
    end

    WriteLoop --> EvidCheck["Evidence Check\n→ micro-research if gaps"]
    EvidCheck --> S3b["Stage 3b: Coherence\nCheck"]
    S3b --> S3c["Stage 3c: Reference\nIntegrity"]
    S3c --> S4["Stage 4: Figures & Tables"]

    S4 --> PraxisCheck{"Praxis\ndata?"}
    PraxisCheck --> |yes| PraxisFig["Praxis venue-matched\nfigures"]
    PraxisCheck --> |no| MatplotFig["matplotlib figures"]
    PraxisFig --> S5
    MatplotFig --> S5

    S5["Stage 5: QA Loop"] --> QAAgents

    subgraph QAAgents ["Parallel Review (up to 5-8 iterations)"]
        direction LR
        R1["Technical\nReviewer"]
        R2["Writing Quality\nReviewer"]
        R3["Completeness\nReviewer"]
        R4["Codex Adversarial\n(optional)"]
    end

    QAAgents --> Synthesize["Synthesize issues\n→ prioritized fix list"]
    Synthesize --> RevisionAgent["Revision Agent\n(Opus)"]
    RevisionAgent --> QAGates{"Quality\ngates pass?"}
    QAGates --> |no| QAAgents
    QAGates --> |yes| PostQA

    subgraph PostQA ["Post-QA Audits"]
        direction LR
        PQ1["Consistency\nChecker"]
        PQ2["Claims\nAuditor"]
        PQ3["Reproducibility\nChecker"]
        PQ4["Reference\nValidator"]
        PQ5["Codex Risk\nRadar"]
    end

    PostQA --> S6["Stage 6: Finalization"]
    S6 --> ScoopCheck["Scooping Check\n(recent preprints)"]
    ScoopCheck --> DeAI["De-AI Polish"]
    DeAI --> Compile["Compile PDF"]
    Compile --> ArchiveStep["Archive Artifacts"]
    ArchiveStep --> Done(["main.pdf + provenance"])
```

## Agent Model Tiers

```mermaid
graph LR
    subgraph "Opus 4.6 (1M context)"
        Writing["Section Writing"]
        Revision["Revision Agent"]
        Expansion["Expansion Agent"]
        DeAI2["De-AI Polish"]
        GapAgent["Gap Analysis"]
    end

    subgraph "Sonnet 4.6 (1M context)"
        Research["Research Agents"]
        Review["Review Agents"]
        BibBuild2["Bibliography Builder"]
        RefVal["Reference Validator"]
        LaySummary["Lay Summary"]
        Repro["Reproducibility"]
        SectionLit["Section Lit Searches"]
    end

    subgraph "External (Optional)"
        CodexExt["Codex (codex-bridge)"]
        LightRAGIngest["LightRAG Ingestion\n(Gemini Flash)"]
        LightRAGQuery["LightRAG Query\n(configurable)"]
        LightRAGEmbed["LightRAG Embedding\n(Qwen3 8B)"]
    end
```

## Data Flow

```mermaid
graph LR
    subgraph "Input"
        Topic[".paper.json\n(topic, venue, depth)"]
        Venue[".venue.json\n(LaTeX config)"]
        Data["attachments/\n(PDFs, data files)"]
    end

    subgraph "Research Artifacts"
        Sources["research/sources/*.md\n(per-paper extracts)"]
        Log["research/log.md\n(tool call log)"]
        KGraph["research/knowledge/\n(LightRAG graph)"]
        Claims["research/claims_matrix.md"]
        Assumptions["research/assumptions.md"]
    end

    subgraph "Manuscript"
        TeX["main.tex"]
        Bib["references.bib"]
        Figs["figures/*.pdf"]
    end

    subgraph "Quality Records"
        Reviews["reviews/*.md"]
        CodexLog["reviews/codex_deliberation_log.md"]
        ProvLog["research/provenance.jsonl"]
        Cuts["provenance/cuts/*.tex"]
    end

    subgraph "Output"
        PDF2["main.pdf"]
        Archive2["archive/\n(browsable bundle)"]
        Progress[".paper-progress.txt"]
        State[".paper-state.json"]
    end

    Topic --> Sources
    Data --> Sources
    Sources --> Claims
    Sources --> KGraph
    Claims --> TeX
    Assumptions --> TeX
    TeX --> PDF2
    Bib --> PDF2
    Figs --> PDF2
    Reviews --> TeX
    TeX --> ProvLog
    TeX --> Archive2
```

## Checkpoint & Resume

The pipeline tracks progress in `.paper-state.json`, enabling resume-on-interrupt:

```mermaid
stateDiagram-v2
    [*] --> research
    research --> snowballing
    snowballing --> cocitation
    cocitation --> codex_cross_check
    codex_cross_check --> source_acquisition
    source_acquisition --> deep_read
    deep_read --> synthesis
    synthesis --> outline
    outline --> codex_thesis
    codex_thesis --> targeted_research : deep mode
    targeted_research --> novelty_check
    codex_thesis --> novelty_check : standard mode
    novelty_check --> assumptions
    assumptions --> writing
    writing --> coherence
    coherence --> reference_integrity
    reference_integrity --> figures
    figures --> qa
    qa --> qa : iteration loop
    qa --> post_qa
    post_qa --> finalization
    finalization --> [*]

    note right of writing
        Per-section tracking:
        introduction.done, related_work.done,
        methods.done, results.done, etc.
    end note

    note right of qa
        qa_iteration counter
        tracks loop progress
    end note
```

## `/auto` Improvement Loop

```mermaid
flowchart TD
    Start(["/auto N"]) --> Iter["Iteration i = 1"]

    Iter --> P1["Phase 1: Assessment"]

    subgraph P1Detail ["5 Parallel Assessment Agents"]
        direction LR
        AD["Depth &\nEvidence"]
        AS["Structure &\nFlow"]
        AC["Competitive\nPositioning"]
        AW["Writing\nQuality"]
        AX["Codex Review\n(optional)"]
    end

    P1 --> P1Detail
    P1Detail --> Regress{"Iteration > 1?"}
    Regress --> |yes| RegCheck["Regression\nDetector"]
    Regress --> |no| P2
    RegCheck --> P2

    P2["Phase 2: Prioritization"] --> ActionPlan["Top-5 Action Plan\n(regressions first)"]
    ActionPlan --> EarlyStop1{"< 3 actions?"}
    EarlyStop1 --> |yes| Done(["Early stop:\npaper is good"])
    EarlyStop1 --> |no| P3

    P3["Phase 3: Execution"] --> Research3["Targeted Research\n(max 3 queries)"]
    Research3 --> Revise3["Revision Agent\nexecutes action plan"]
    Revise3 --> P4

    P4["Phase 4: Verification"] --> Compile4["Compile + check"]
    Compile4 --> Scores["Recompute\nevidence scores"]
    Scores --> NextIter{"i < N?"}
    NextIter --> |yes| Iter
    NextIter --> |no| Done2(["Done: N iterations complete"])
```

## Project Directory Layout

```
paper-project/                     # Created by create-paper
├── main.tex                       # Primary LaTeX document
├── references.bib                 # BibTeX references
├── .paper.json                    # Topic, venue, depth, authors
├── .venue.json                    # Venue template (copy from venues/)
├── .paper-state.json              # Checkpoint state (auto-managed)
├── .paper-progress.txt            # Human-readable progress
├── figures/                       # Generated and imported figures
├── attachments/                   # Reference PDFs, data files
├── research/
│   ├── sources/                   # Per-paper source extracts
│   │   ├── smith2024.md
│   │   └── jones2023.md
│   ├── knowledge/                 # LightRAG graph (gitignored)
│   ├── log.md                     # Research provenance log
│   ├── provenance.jsonl           # Machine-readable provenance
│   ├── claims_matrix.md           # Claims-evidence mapping
│   └── assumptions.md             # Methodological assumptions
├── reviews/                       # Review feedback
│   ├── technical_review.md
│   ├── writing_review.md
│   └── codex_deliberation_log.md
├── provenance/
│   └── cuts/                      # Archived cut content
├── archive/                       # Browsable bundle (end of pipeline)
└── .claude/
    ├── CLAUDE.md                  # Workspace instructions (symlink)
    ├── commands/                  # 35 slash commands (symlinks)
    ├── pipeline/                  # Stage instructions (symlinks)
    │   ├── shared-protocols.md
    │   ├── stage-1-research.md
    │   ├── ...
    │   └── auto-phase-4-verification.md
    └── skills/                    # → vendor/claude-scientific-skills
```

## Symlink Architecture

Paper projects use symlinks back to the Research Agent template, enabling instant updates across all papers:

```mermaid
graph LR
    subgraph "research-agent/ (template repo)"
        T_CLAUDE["template/claude/CLAUDE.md"]
        T_CMD["template/claude/commands/*.md"]
        T_PIPE["template/claude/pipeline/*.md"]
        T_SKILLS["vendor/claude-scientific-skills/"]
    end

    subgraph "my-paper/ (paper project)"
        P_CLAUDE[".claude/CLAUDE.md"]
        P_CMD[".claude/commands/"]
        P_PIPE[".claude/pipeline/"]
        P_SKILLS[".claude/skills/"]
    end

    P_CLAUDE -->|symlink| T_CLAUDE
    P_CMD -->|symlink| T_CMD
    P_PIPE -->|symlink| T_PIPE
    P_SKILLS -->|symlink| T_SKILLS
```

The `sync-papers` script migrates older paper projects to use symlinks.

## Provenance Chain

Every paragraph in the final PDF traces back through:

```mermaid
graph BT
    PDF3["Final PDF paragraph"] --> Prov["provenance.jsonl entry"]
    Prov --> Sources2["research/sources/key.md\n(content snapshot)"]
    Sources2 --> Tool["Tool call\n(Perplexity, Scholar, etc.)"]
    Tool --> Paper["Original paper\n(DOI / URL)"]

    Prov --> Claims2["claims_matrix.md\n(claim ID, warrant, evidence score)"]
    Prov --> Feedback["reviews/*.md\n(revision feedback)"]
    Prov --> CutRef["provenance/cuts/\n(archived removed text)"]
```

## Claims-Evidence Matrix

```mermaid
graph TD
    Claim["Claim C1:\nOur method outperforms X"] --> Evidence

    subgraph Evidence ["Evidence Sources"]
        E1["smith2024 (FULL-TEXT)\nScore: 2.5"]
        E2["jones2023 (ABSTRACT)\nScore: 1.8"]
        E3["Our experiments\nScore: 3.0"]
    end

    Evidence --> Score["Total: 7.3 → STRONG"]

    Claim --> Warrant["Warrant:\nControlled comparison on\nsame benchmark"]
    Claim --> Qualifier["Qualifier:\nOn English-only datasets"]
    Claim --> Rebuttal["Rebuttal:\nSection 5.2 discusses\nlimitations on multilingual"]
```

Evidence density scoring:

| Rating | Score | Writing guidance |
|-|-|-|
| STRONG | >= 6.0 | Confident language |
| MODERATE | 3.0 - 5.9 | Standard academic hedging |
| WEAK | 1.0 - 2.9 | Hedged language required |
| CRITICAL | < 1.0 | Must resolve before finalization |

## Tool Fallback Chain

```mermaid
flowchart LR
    Q["Research Query"] --> D["Domain Skills\n(pubmed, arxiv, etc.)"]
    D --> |fail| P["Perplexity Search"]
    P --> |fail| W["WebSearch"]
    W --> |fail| F["Firecrawl Search"]
    F --> |fail| WF["WebFetch\n(known URLs)"]
    WF --> |fail| RL["research-lookup\nskill (fallback)"]
    RL --> |fail| Gap["Log gap,\nmove on"]

    D --> |success| Log["Log to research/log.md\n+ create source extract"]
    P --> |success| Log
    W --> |success| Log
    F --> |success| Log
    WF --> |success| Log
    RL --> |success| Log
```
