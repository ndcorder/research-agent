# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2026-03-25

### Added
- Autonomous paper writing pipeline (`/write-paper`) producing journal-quality research papers in 1-8 hours with parallel multi-agent orchestration
- 30 slash commands for research, writing, quality assurance, data analysis, and submission
- Iterative improvement command (`/auto`) for autonomously assessing and improving finished papers, including content cuts as first-class improvements
- Provenance ledger system tracing every word in the paper back to its origin via `research/provenance.jsonl`
- Provenance query command (`/provenance`) with 7 modes: summary, section, trace, history, sources, gaps, timeline
- Knowledge graph (`scripts/knowledge.py`) built from source extracts using LightRAG with semantic search, contradiction detection, and evidence queries
- Source coverage audit (`/audit-sources`) classifying references by access level with automated open-access resolution and human-in-the-loop for paywalled papers
- Codex Bridge integration for optional adversarial AI review with deliberation protocol across 10 pipeline stages
- Praxis integration for domain-specific scientific data analysis (50+ characterisation techniques, 9 journal figure styles)
- 177 scientific skills with automatic domain detection and skill routing
- Deep research mode (`--deep`) with 12 specialized agents, 60-80 references, thesis-informed second pass, and per-section literature searches
- 7 venue templates (generic, IEEE, ACM, NeurIPS, Nature, arXiv, APA) with automatic formatting
- De-AI polish removing AI writing patterns including em dashes, filler phrases, and formulaic transitions
- Claims-evidence matrix mapping every claim to specific evidence with source access level tracking
- Symlinked project architecture so template updates propagate instantly to all paper projects
- Project scaffolding (`create-paper`) with venue selection, depth mode, and optional auto-launch
- Migration tool (`sync-papers`) to convert existing projects from file copies to symlinks
- Checkpoint and resume system (`.paper-state.json`) allowing interrupted pipelines to continue

### Security
- Sanitized shell variable interpolation in `create-paper` and `write-paper` to prevent injection via topic strings or venue paths
