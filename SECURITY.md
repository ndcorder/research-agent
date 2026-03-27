# Security

## Threat Model

Research Agent runs Claude Code autonomously for 1-8 hours with network access. The primary trust boundaries are:

1. **Permission allowlist** (`.claude/settings.local.json`) — controls which tools Claude can use without prompting. Only tools on this list auto-approve. Anything else (e.g., `git push`, arbitrary shell commands) prompts the user.
2. **Template integrity** — pipeline instructions and commands are symlinked from the template directory. If an attacker modifies these files, they control what Claude executes.
3. **Submodule integrity** — 177 scientific skills are cloned from an external repository. A supply chain compromise would give an attacker code execution within the pipeline.

### What the pipeline can do (by design)

- Read and write files in the paper project directory
- Make HTTP requests to academic APIs (CrossRef, Semantic Scholar, Unpaywall, OpenAlex, CORE, PubMed)
- Download PDFs to `attachments/`
- Run `latexmk`/`pdflatex` for compilation
- Run `python3` for knowledge graph building, data analysis, and figure generation
- Spawn subagents with the same permissions

### What the pipeline cannot do (blocked by allowlist)

- Push to git remotes
- Run arbitrary shell commands outside the scoped patterns
- Install system packages (only `pip install` is allowed)
- Access files outside the project directory (Claude Code sandbox)
- Send emails, post to Slack, or interact with services not on the MCP allowlist

## Permission Allowlist

The allowlist in `.claude/settings.local.json` is scoped to the minimum tools the pipeline needs:

- **Python**: Limited to `python3 -c` (one-liners), `python3 scripts/` (knowledge graph), `python3 figures/` (generated analysis scripts), `python3 -m pip` (dependency installs), and `python3 --version` (health check). Arbitrary `python3 malicious.py` is not auto-approved.
- **curl**: Limited to `curl -L -o` (PDF downloads to local files) and `curl -s https://api.crossref.org/` (reference validation). Arbitrary curl to external URLs is not auto-approved.
- **rm**: Limited to `rm -f reviews/` (clearing stale reviews between QA iterations), `rm -rf archive/` (rebuilding the archive), and `rm -f *.aux` (LaTeX cleanup). Deleting research files or other directories prompts the user.
- **MCP tools**: Perplexity (search, reasoning), Context7 (docs), Firecrawl (scraping), and Codex Bridge (adversarial review). All are read-oriented tools used for research.

If you encounter an unexpected prompt during a pipeline run, it means the pipeline tried to use a tool not on the allowlist. You can approve it once, and if it's a legitimate pipeline operation, add the pattern to `settings.local.json`.

## Submodule Policy

The `vendor/claude-scientific-skills` submodule is pinned to a specific tag in `.gitmodules`. To update:

1. Review the changelog and diff of the new release
2. Update the `branch` field in `.gitmodules` to the new tag
3. Run `git submodule update --remote vendor/claude-scientific-skills`
4. Verify with `git -C vendor/claude-scientific-skills describe --tags`
5. Commit the submodule update

Do not run `git submodule update --remote` without first verifying the target release. The submodule contains Python scripts that execute during the pipeline.

## API Keys

All API keys are sourced from environment variables, never hardcoded:

| Variable | Service | Required |
|-|-|-|
| `OPENROUTER_API_KEY` | LightRAG knowledge graph (Gemini Flash + Qwen3 8B) | Optional |
| `CORE_API_KEY` | CORE institutional repository (200M+ papers) | Optional |
| `NCBI_API_KEY` | PubMed Central (increases rate limit) | Optional |
| `UNPAYWALL_EMAIL` | Unpaywall OA resolution | Optional |

Store these in your shell profile or a `.env` file (gitignored by default).

## Reporting

If you find a security issue, please open an issue on the repository or contact the maintainers directly.
