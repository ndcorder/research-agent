"""Runtime-aware structural checks for Claude and Codex support."""

from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent


def test_shared_pipeline_exists():
    pipeline_dir = REPO_ROOT / "template" / "shared" / "pipeline"
    assert pipeline_dir.is_dir()
    assert (pipeline_dir / "shared-protocols.md").exists()


def test_runtime_pipeline_wrappers_point_to_shared_pipeline():
    for runtime in ("claude", "codex"):
        pipeline_path = REPO_ROOT / "template" / runtime / "pipeline"
        assert pipeline_path.exists(), f"missing {pipeline_path}"
        assert pipeline_path.resolve() == (REPO_ROOT / "template" / "shared" / "pipeline").resolve()


def test_codex_runtime_scaffold_exists():
    codex_dir = REPO_ROOT / "template" / "codex"
    assert (codex_dir / "AGENTS.md").exists()
    assert (codex_dir / "runtime-contract.md").exists()
    for name in ("write-paper", "preview-pipeline", "health", "targeted-research"):
        assert (codex_dir / "commands" / f"{name}.md").exists()


def test_codex_command_surface_matches_claude():
    claude = {p.name for p in (REPO_ROOT / "template" / "claude" / "commands").glob("*.md")}
    codex = {p.name for p in (REPO_ROOT / "template" / "codex" / "commands").glob("*.md")}
    assert claude == codex


def test_codex_command_wrappers_are_all_present_and_resolved():
    codex_dir = REPO_ROOT / "template" / "codex" / "commands"
    claude_dir = REPO_ROOT / "template" / "claude" / "commands"

    special_files = {
        "write-paper.md",
        "preview-pipeline.md",
        "health.md",
        "targeted-research.md",
    }

    for claude_file in claude_dir.glob("*.md"):
        codex_file = codex_dir / claude_file.name
        assert codex_file.exists()
        if claude_file.name in special_files:
            assert codex_file.is_file()
        else:
            assert codex_file.is_symlink()
            assert codex_file.resolve() == claude_file.resolve()


def test_codex_scaffold_contract_files_exist():
    codex_dir = REPO_ROOT / "template" / "codex"
    assert (codex_dir / "AGENTS.md").exists()
    assert (codex_dir / "runtime-contract.md").exists()
    assert (codex_dir / "runtime-contract.md").resolve() == (
        REPO_ROOT / "template" / "shared" / "runtime-contract.md"
    ).resolve()


def test_runtime_launcher_scripts_exist():
    for name in ("runtime.sh", "run-paper-command"):
        assert (REPO_ROOT / "template" / "scripts" / name).exists()


def test_create_paper_supports_runtime_flag():
    text = (REPO_ROOT / "create-paper").read_text(encoding="utf-8")
    assert "--runtime" in text
    assert '"runtime": runtime' in text
    assert ".codex/skills" in text
    assert ".codex/AGENTS.md" in text
    assert 'AGENTS.md' in text
    assert ".codex/commands" in text
    assert ".codex/pipeline" in text


def test_write_paper_dispatches_via_runtime_runner():
    text = (REPO_ROOT / "write-paper").read_text(encoding="utf-8")
    assert "runtime" in text.lower()
    assert "run-paper-command" in text


def test_gui_runtime_field_wired_through():
    rust = (REPO_ROOT / "gui" / "src-tauri" / "src" / "commands" / "state.rs").read_text(
        encoding="utf-8"
    )
    svelte = (
        REPO_ROOT / "gui" / "src" / "lib" / "components" / "layout" / "CreatePaperDialog.svelte"
    ).read_text(encoding="utf-8")
    assert "runtime: Option<String>" in rust
    assert 'runtime = $state("claude")' in svelte
