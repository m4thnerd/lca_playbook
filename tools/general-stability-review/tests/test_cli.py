import json
import re
from pathlib import Path

from general_stability_review.cli import (
    GitContext,
    _classify_failure,
    _command_for_reviewer,
    _prepare_reviewer_process,
    _write_artifacts,
    DEFAULT_REVIEWER_BY_MODE,
    _format_summary,
    _normalized_result,
    _parse_json_object,
    _print_playbook_reminder,
    _resolve_artifacts_dir,
    build_review_prompt,
    build_staff_review_prompt,
    REVIEWER_TIMEOUT,
    STAFF_REVIEWER_TIMEOUT,
    ReviewRun,
)
from general_stability_review.llm_config_loader import llm_config


def _git_context() -> GitContext:
    return GitContext(
        repo_root=Path("/repo"),
        base_ref="origin/main",
        branch="feature",
        head="abc123",
        merge_base="def456",
        shortstat="2 files changed, 10 insertions(+), 1 deletion(-)",
        name_status="M\tapp.py",
        worktree_status=" M app.py",
    )


def test_playbook_reminder_is_printed(capsys) -> None:
    _print_playbook_reminder()

    output = capsys.readouterr().out
    assert "You just initiated a GSR" in output
    assert "reviews/general_stability_review_playbook.md" in output
    assert "interpreting GSR results proportionately" in output


def test_codex_reviewer_pins_model_with_high_effort_read_only() -> None:
    command = _command_for_reviewer("codex")

    if llm_config.CODEX_MODEL:
        assert f'model="{llm_config.CODEX_MODEL}"' in command
    else:
        assert not any(arg.startswith("model=") for arg in command)
    assert f'model_reasoning_effort="{llm_config.CODEX_REASONING_EFFORT}"' in command
    assert "--sandbox" in command
    assert command[command.index("--sandbox") + 1] == "read-only"
    assert "--ephemeral" in command


def test_llm_config_loader_falls_back_to_example_and_prefers_local(tmp_path) -> None:
    from general_stability_review.llm_config_loader import load_llm_config_from

    example_file = tmp_path / "llm_config.example.py"
    example_file.write_text('CLAUDE_MODEL = "example-model"\n', encoding="utf-8")
    loaded_fallback = load_llm_config_from(tmp_path)
    assert loaded_fallback.CLAUDE_MODEL == "example-model"

    local_file = tmp_path / "llm_config.py"
    local_file.write_text('CLAUDE_MODEL = "local-override-model"\n', encoding="utf-8")
    loaded_local = load_llm_config_from(tmp_path)
    assert loaded_local.CLAUDE_MODEL == "local-override-model"


def test_claude_reviewer_uses_configured_model_and_effort() -> None:
    command = _command_for_reviewer("claude")

    assert command[command.index("--model") + 1] == llm_config.CLAUDE_MODEL
    assert command[command.index("--effort") + 1] == llm_config.CLAUDE_EFFORT


def test_opencode_custom_reviewer_maps_model() -> None:
    assert _command_for_reviewer("opencode:google/example") == [
        "opencode",
        "run",
        "-m",
        "google/example",
        "--variant",
        llm_config.OPENCODE_VARIANT,
    ]


def test_review_prompt_includes_gsr_scope_and_json_contract() -> None:
    prompt = build_review_prompt(_git_context(), "Pay attention to migrations.")

    assert "General Stability Review" in prompt
    assert "Do not edit files" in prompt
    assert "Treat rare theoretical edge cases as" in prompt
    assert "Treat explicit settled implementation decisions" in prompt
    assert "settled decision merely because another architecture is plausible" in prompt
    assert "Anti-Ratchet Rule:" in prompt
    assert "does not add more complexity than the risk justifies" in prompt
    assert "git diff origin/main...HEAD" in prompt
    assert '"overall": "clean" | "findings" | "incomplete"' in prompt
    assert "Pay attention to migrations." in prompt


def test_parse_json_object_accepts_fenced_json_with_text() -> None:
    raw = 'Done.\n```json\n{"overall": "clean", "findings": []}\n```'

    assert _parse_json_object(raw) == {"overall": "clean", "findings": []}


def test_normalized_result_promotes_clean_with_findings_to_findings() -> None:
    run = ReviewRun(
        reviewer="codex",
        command=["codex"],
        raw_output="",
        stderr="",
        elapsed_s=1.0,
        returncode=0,
    )

    result = _normalized_result(
        {
            "overall": "clean",
            "summary": "Found one.",
            "findings": [{"severity": "medium", "file": "app.py"}],
        },
        run,
    )

    assert result["overall"] == "findings"
    assert not result["parse_error"]


def test_normalized_result_marks_unparseable_output_incomplete() -> None:
    run = ReviewRun(
        reviewer="codex",
        command=["codex"],
        raw_output="not json",
        stderr="",
        elapsed_s=1.0,
        returncode=0,
    )

    result = _normalized_result(None, run)

    assert result["overall"] == "incomplete"
    assert result["parse_error"]
    assert result["failure_classification"] == "unparseable_reviewer_output"


def test_classify_claude_quota_or_billing_failure() -> None:
    run = ReviewRun(
        reviewer="claude",
        command=["claude"],
        raw_output="",
        stderr="API Error: quota exceeded for current subscription",
        elapsed_s=1.0,
        returncode=1,
    )

    assert _classify_failure(run) == "quota_or_billing"


def test_classify_claude_network_failure() -> None:
    run = ReviewRun(
        reviewer="claude",
        command=["claude"],
        raw_output="",
        stderr="API Error: Unable to connect to API (ConnectionRefused)",
        elapsed_s=1.0,
        returncode=1,
    )

    assert _classify_failure(run) == "network"


def test_classify_auth_failure() -> None:
    run = ReviewRun(
        reviewer="claude",
        command=["claude"],
        raw_output="",
        stderr="API key is invalid: 401 unauthorized",
        elapsed_s=1.0,
        returncode=1,
    )

    assert _classify_failure(run) == "auth"


def test_classify_codex_local_state_failure() -> None:
    run = ReviewRun(
        reviewer="codex",
        command=["codex"],
        raw_output="",
        stderr="/Users/dev/.codex/state_5.sqlite: Read-only file system (os error 30)",
        elapsed_s=1.0,
        returncode=1,
    )

    assert _classify_failure(run) == "local_state_or_sandbox"


def test_normalized_result_records_worktree_mutation() -> None:
    run = ReviewRun(
        reviewer="codex",
        command=["codex"],
        raw_output='{"overall": "clean", "summary": "Clean.", "findings": []}',
        stderr="",
        elapsed_s=1.0,
        returncode=0,
        worktree_status_before="",
        worktree_status_after=" M app.py",
    )

    result = _normalized_result({"overall": "clean", "summary": "Clean.", "findings": []}, run)

    assert result["worktree_mutated"]


def test_staff_playbook_reminder_is_printed(capsys) -> None:
    _print_playbook_reminder("staff-engineer")

    output = capsys.readouterr().out
    assert "You just initiated a Staff Engineer Review" in output
    assert "reviewers/staff_engineer_reviewer.md" in output
    assert "reviews/general_stability_review_playbook.md" in output


def test_staff_review_prompt_loads_guidelines_and_context() -> None:
    prompt = build_staff_review_prompt(
        _git_context(), "Deletion of deprecated cache mechanism."
    )

    assert "Staff Engineer Reviewer Guidelines" in prompt
    assert "Silence Discipline" in prompt
    assert "Churn & Anti-Ratchet Discipline" in prompt
    assert "Playbook root:" in prompt
    assert "Deletion of deprecated cache mechanism." in prompt
    assert "git diff --stat origin/main...HEAD" in prompt


def test_resolve_artifacts_dir_separates_gsr_and_staff_runs() -> None:
    gsr_dir = _resolve_artifacts_dir(Path("/repo"), None, mode="gsr")
    staff_dir = _resolve_artifacts_dir(Path("/repo"), None, mode="staff-engineer")

    assert gsr_dir.parent == Path("/repo/tmp/gsr-reviews")
    assert staff_dir.parent == Path("/repo/tmp/staff-engineer-reviews")


def test_format_summary_includes_staff_mode() -> None:
    run = ReviewRun(
        reviewer="claude",
        command=["claude"],
        raw_output="",
        stderr="",
        elapsed_s=2.5,
        returncode=0,
    )
    result = {
        "overall": "findings",
        "summary": "Excessive test and helper bloat.",
        "findings": [
            {
                "severity": "medium",
                "confidence": "high",
                "file": "service.py",
                "line": 42,
                "title": "Unnecessary retry framework",
                "description": "Adds 200 lines where a direct call suffices.",
                "recommendation": "Use request_with_backoff().",
            }
        ],
        "non_actionable_notes": ["Deletion completeness verified."],
        "parse_error": False,
        "failure_classification": None,
    }

    summary = _format_summary(run, result, Path("/repo/tmp/staff"), mode="staff-engineer")

    assert "# Staff Engineer Review Result" in summary
    assert "- Mode: staff-engineer" in summary
    assert "[medium] service.py:42 - Unnecessary retry framework" in summary



def test_staff_mode_gets_longer_default_timeout() -> None:
    assert STAFF_REVIEWER_TIMEOUT > REVIEWER_TIMEOUT
    assert STAFF_REVIEWER_TIMEOUT == 30 * 60


def test_staff_mode_uses_staff_pins_and_enforces_read_only_sandboxes() -> None:
    staff_claude = _command_for_reviewer("claude", mode="staff-engineer")
    assert staff_claude[staff_claude.index("--model") + 1] == llm_config.STAFF_ENGINEER_CLAUDE_MODEL
    assert staff_claude[staff_claude.index("--effort") + 1] == llm_config.STAFF_ENGINEER_CLAUDE_EFFORT
    assert "plan" in staff_claude
    staff_codex = _command_for_reviewer("codex", mode="staff-engineer")
    if llm_config.STAFF_ENGINEER_CODEX_MODEL:
        assert f'model="{llm_config.STAFF_ENGINEER_CODEX_MODEL}"' in staff_codex
    assert "read-only" in staff_codex and "--ephemeral" in staff_codex
    staff_gemini = _command_for_reviewer("gemini", mode="staff-engineer")
    assert staff_gemini[0] == "agy" and staff_gemini[-1] == "--print"
    assert staff_gemini[staff_gemini.index("--model") + 1] == llm_config.STAFF_ENGINEER_AGY_MODEL
    assert "--dangerously-skip-permissions" not in staff_gemini
    assert DEFAULT_REVIEWER_BY_MODE == {
        "gsr": llm_config.GENERAL_STABILITY_REVIEW_DEFAULT_REVIEWER,
        "staff-engineer": llm_config.STAFF_ENGINEER_DEFAULT_REVIEWER,
    }


def test_llm_config_loader_prefers_local_override_and_falls_back_to_example(tmp_path) -> None:
    from general_stability_review.llm_config_loader import load_llm_config_from

    sub = tmp_path / "tools" / "pkg"
    sub.mkdir(parents=True)
    (tmp_path / "llm_config.example.py").write_text('CLAUDE_MODEL = "sonnet"\n', encoding="utf-8")

    fallback_mod = load_llm_config_from(sub)
    assert fallback_mod.CLAUDE_MODEL == "sonnet"

    (tmp_path / "llm_config.py").write_text('CLAUDE_MODEL = "opus"\n', encoding="utf-8")
    override_mod = load_llm_config_from(sub)
    assert override_mod.CLAUDE_MODEL == "opus"


def test_prepare_reviewer_process_agy_uses_fake_home_and_prompt_argument(tmp_path) -> None:
    argv, env, stdin_payload = _prepare_reviewer_process(
        ["agy", "--model", "m", "--print"], "review prompt", tmp_path / "run"
    )
    assert argv == ["agy", "--model", "m", "--print", "review prompt"]
    assert stdin_payload is None
    assert env["HOME"] == str((tmp_path / "run" / "agy_home").resolve())
    settings = json.loads(
        (tmp_path / "run" / "agy_home" / ".gemini" / "antigravity-cli" / "settings.json").read_text()
    )
    assert "command(git)" in settings["permissions"]["allow"]
    assert "write_file(*)" in settings["permissions"]["deny"]
    assert "search_web(*)" in settings["permissions"]["deny"]


def test_prepare_reviewer_process_grok_writes_prompt_file(tmp_path) -> None:
    argv, _, stdin_payload = _prepare_reviewer_process(
        ["grok", "-m", "grok-4.7"], "review prompt", tmp_path / "run"
    )
    assert stdin_payload is None
    assert argv[-2] == "--prompt-file"
    assert Path(argv[-1]).read_text() == "review prompt"


def test_prepare_reviewer_process_default_is_stdin(tmp_path) -> None:
    argv, _, stdin_payload = _prepare_reviewer_process(["codex", "exec", "-"], "p", tmp_path)
    assert argv == ["codex", "exec", "-"]
    assert stdin_payload == "p"


def test_write_artifacts_accepts_run_dir_created_by_launcher(tmp_path) -> None:
    run_dir = tmp_path / "run_x"
    _prepare_reviewer_process(["agy", "--model", "m", "--print"], "p", run_dir)
    run = ReviewRun(
        reviewer="gemini", command=["agy"], raw_output="{}", stderr="", elapsed_s=1.0, returncode=0
    )
    _write_artifacts(run_dir, _git_context(), "p", run, {}, {"overall": "clean"}, mode="staff-engineer")
    assert (run_dir / "result.json").exists()
