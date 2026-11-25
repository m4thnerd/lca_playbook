from convergence_review.convergence import (
    BLOCKING_SEVERITIES,
    SEVERITY_ORDER,
    check_convergence,
    format_quoted_severity_list,
    format_summary,
    parse_review_json,
    parse_review_payload,
)
from convergence_review.coder import _get_coder_command, build_coder_prompt
from convergence_review.cli import (
    ROLE_CONFIGS as CLI_ROLE_CONFIGS,
    _project_root_from_git_common_dir,
    _parse_reviewers_arg,
    _resolve_role_guidelines,
    _validate_coder,
)
from convergence_review.design_doc_validation import validate_essential_requirements
from convergence_review.llm_config_loader import llm_config
from convergence_review.orchestrator import (
    _annotated_issues,
    _consolidate_reviews,
    _must_skip_coder_for_incomplete_blocking_review,
    _review_incomplete_reason,
)
from convergence_review.reviewers import (
    REVIEWER_COMMANDS,
    REVIEWER_NAMES,
    REVIEWER_ROLE_NAMES,
    ReviewResult,
    ReviewerSpec,
    build_reviewer_prompt,
    _prepare_reviewer_process,
    _repair_review_json,
    _run_single_reviewer,
    run_reviewers,
)

import argparse
import asyncio
import json
from pathlib import Path
import sys

import pytest


def test_blocking_severities_block_convergence() -> None:
    for severity in BLOCKING_SEVERITIES:
        assert not check_convergence(
            [{"severity": severity, "category": "bug", "description": "Still wrong"}]
        )


def test_nonblocking_severities_do_not_block_convergence() -> None:
    for severity in set(SEVERITY_ORDER) - set(BLOCKING_SEVERITIES):
        assert check_convergence(
            [
                {
                    "severity": severity,
                    "category": "code_quality",
                    "description": "Polish",
                }
            ]
        )


def test_summary_reports_blocking_severities() -> None:
    severity = BLOCKING_SEVERITIES[-1]
    summary = format_summary(
        [
            {
                "iteration": 1,
                "issues": [
                    {
                        "severity": severity,
                        "file": "example.py",
                        "description": "Requirement still incomplete",
                    }
                ],
                "converged": False,
            }
        ]
    )

    assert "Status: MAX ITERATIONS REACHED" in summary
    assert "legitimate implementation work remains" in summary
    assert "Essential Requirements wording is causing churn" in summary
    assert "requirements bloat is entering the implementation" in summary
    assert "read example-case-studies/requirements-risk/" in summary
    assert "1 blocking issue(s) remaining" in summary
    assert f"[{severity}] example.py: Requirement still incomplete" in summary


def test_coder_prompt_uses_blocking_severities_constant() -> None:
    prompt = build_coder_prompt("# Essential Requirements\n\n- Do the thing.", "[]")

    assert format_quoted_severity_list(BLOCKING_SEVERITIES) in prompt


def test_parse_review_json_accepts_prose_then_array() -> None:
    raw = 'Review notes:\n\n[{"severity": "high", "description": "Bug"}]'

    assert parse_review_json(raw) == [{"severity": "high", "description": "Bug"}]


def test_parse_review_json_accepts_prose_then_empty_array() -> None:
    raw = "No issues found.\n\n[]"

    assert parse_review_json(raw) == []


def test_parse_review_json_accepts_fenced_array_with_surrounding_text() -> None:
    raw = 'Findings:\n```json\n[{"severity": "low"}]\n```\nDone.'

    assert parse_review_json(raw) == [{"severity": "low"}]


def test_parse_review_payload_accepts_object_with_assessment() -> None:
    raw = '{"issues": [{"severity": "low"}], "assessment": "Ready enough."}'

    payload = parse_review_payload(raw)

    assert payload is not None
    assert payload.issues == [{"severity": "low"}]
    assert payload.assessment == "Ready enough."


def test_parse_review_payload_accepts_tool_failure_status() -> None:
    raw = json.dumps(
        {
            "infrastructure_status": "tool_failed",
            "status_detail": "repository reads were canceled",
            "issues": [],
        }
    )

    payload = parse_review_payload(raw)

    assert payload is not None
    assert payload.infrastructure_status == "tool_failed"
    assert payload.status_detail == "repository reads were canceled"
    assert payload.issues == []


def test_parse_review_payload_rejects_unrecognized_infrastructure_status() -> None:
    raw = json.dumps(
        {
            "infrastructure_status": "failed",
            "status_detail": "tooling broke",
            "issues": [],
        }
    )

    assert parse_review_payload(raw) is None


def test_parse_review_payload_rejects_unrecognized_status_in_fence() -> None:
    raw = (
        "Report:\n```json\n"
        '{"infrastructure_status": "failed", "issues": []}\n'
        "```\nDone."
    )

    assert parse_review_payload(raw) is None


def test_parse_review_payload_rejects_unrecognized_status_embedded_in_prose() -> None:
    raw = (
        "The review could not run.\n"
        '{"infrastructure_status": "failed", "status_detail": "broke", "issues": []}\n'
        "End of report."
    )

    assert parse_review_payload(raw) is None


def test_parse_review_payload_strict_mode_rejects_embedded_fragment() -> None:
    raw = "backend crashed before review ran\nretry schedule: []\n"

    permissive = parse_review_payload(raw)
    assert permissive is not None
    assert permissive.issues == []

    assert parse_review_payload(raw, allow_embedded=False) is None


def test_parse_review_payload_strict_mode_accepts_whole_output_and_fenced() -> None:
    whole = '[{"severity": "high", "description": "Bug"}]'
    fenced = 'Findings:\n```json\n[{"severity": "low"}]\n```\nDone.'

    whole_payload = parse_review_payload(whole, allow_embedded=False)
    fenced_payload = parse_review_payload(fenced, allow_embedded=False)

    assert whole_payload is not None
    assert whole_payload.issues == [{"severity": "high", "description": "Bug"}]
    assert fenced_payload is not None
    assert fenced_payload.issues == [{"severity": "low"}]


def test_review_result_status_flags_derive_from_infrastructure_status() -> None:
    parse_failed = ReviewResult("codex", "", infrastructure_status="parse_failed")
    timed_out = ReviewResult("codex", "", infrastructure_status="timed_out")
    complete = ReviewResult("codex", "[]")

    assert parse_failed.parse_error is True
    assert parse_failed.timed_out is False
    assert timed_out.timed_out is True
    assert timed_out.parse_error is False
    assert complete.parse_error is False
    assert complete.timed_out is False


def test_final_non_core_reviewer_prompt_allows_assessment_object_without_array_conflict() -> (
    None
):
    prompt = build_reviewer_prompt(
        "# Essential Requirements\n- Do the thing.",
        "Peer guidelines",
        role_name="peer",
        final_iteration=True,
    )

    assert "Respond with either a JSON array of issues or an object" in prompt
    assert "Respond with a JSON array of issues. Each issue must have:" not in prompt
    assert '"assessment": "..."' in prompt


def test_reviewer_prompt_does_not_require_shell_access() -> None:
    prompt = build_reviewer_prompt(
        "# Essential Requirements\n- Do the thing.",
        "Core guidelines",
    )

    assert "Prefer built-in read, search, and glob tools" in prompt
    assert "If your backend exposes a read-only shell" in prompt


def test_review_incomplete_reason_reports_parse_error_without_raw_output() -> None:
    reason = _review_incomplete_reason(
        [
            ReviewResult(
                "codex",
                "",
                infrastructure_status="parse_failed",
            )
        ]
    )

    assert reason == "codex:core parse_failed"


def test_blocking_reviewer_timeout_skips_coder() -> None:
    assert _must_skip_coder_for_incomplete_blocking_review(
        [
            ReviewResult(
                "codex",
                "Error: timed out",
                infrastructure_status="timed_out",
            )
        ]
    )


def test_blocking_unparseable_raw_output_is_not_sent_to_coder() -> None:
    assert _must_skip_coder_for_incomplete_blocking_review(
        [
            ReviewResult(
                "codex",
                "not json but useful context",
                infrastructure_status="parse_failed",
            )
        ]
    )


def test_summary_reports_review_incomplete() -> None:
    summary = format_summary(
        [
            {
                "iteration": 1,
                "issues": [],
                "converged": False,
                "review_incomplete": True,
            }
        ],
        review_incomplete=True,
        review_incomplete_reason="codex produced no parseable output",
    )

    assert "Status: REVIEW INCOMPLETE" in summary
    assert "codex produced no parseable output" in summary


def test_summary_distinguishes_incomplete_persona_review_from_clean() -> None:
    summary = format_summary(
        [
            {
                "iteration": 1,
                "issues": [],
                "convergence_issues": [],
                "roles_run": ["core", "peer"],
                "reviewer_statuses": [
                    {
                        "reviewer": "codex:core",
                        "role": "core",
                        "infrastructure_status": "complete",
                    },
                    {
                        "reviewer": "claude:peer",
                        "role": "peer",
                        "infrastructure_status": "parse_failed",
                        "status_detail": "output remained unparseable",
                    },
                ],
                "converged": True,
            }
        ]
    )

    assert "Status: CONVERGED" in summary
    assert "Incomplete reviews:" in summary
    assert "claude:peer: parse_failed: output remained unparseable" in summary


def test_essential_requirements_validation_accepts_valid_section() -> None:
    result = validate_essential_requirements(
        "# Title\n\n# Essential Requirements\n- One required behavior\n"
    )

    assert result.ok


def test_essential_requirements_validation_rejects_missing_section() -> None:
    result = validate_essential_requirements("# Title\n\n- Not the required heading\n")

    assert not result.ok
    assert "# Essential Requirements" in result.message


def test_essential_requirements_accepts_h2_heading() -> None:
    result = validate_essential_requirements(
        "# Title\n\n## Essential Requirements\n- One required behavior\n"
    )

    assert result.ok


def test_essential_requirements_accepts_blank_line_after_header() -> None:
    result = validate_essential_requirements(
        "# Essential Requirements\n\n- One required behavior\n"
    )

    assert result.ok


def test_essential_requirements_accepts_word_wrap_continuation() -> None:
    content = (
        "## Essential Requirements\n"
        "\n"
        "- The first requirement spans more than one line because it\n"
        "  continues here without a leading dash.\n"
        "- Second requirement\n"
        "  also wraps onto another line.\n"
        "\n"
        "## Some other section\n"
        "- not a requirement\n"
    )

    result = validate_essential_requirements(content)

    assert result.ok


def test_essential_requirements_section_ends_at_blank_line() -> None:
    content = (
        "# Essential Requirements\n"
        "- one\n"
        "- two\n"
        "\n"
        "Some prose that follows the section and is NOT a requirement.\n"
    )

    result = validate_essential_requirements(content)

    assert result.ok


def test_essential_requirements_rejects_non_bullet_before_first_bullet() -> None:
    content = "# Essential Requirements\nthis is not a bullet\n- one\n"

    result = validate_essential_requirements(content)

    assert not result.ok
    assert "non-bullet-point content" in result.message


def test_essential_requirements_caps_at_ten_with_continuations() -> None:
    bullets = "\n".join(
        f"- requirement {i}\n  continuation for {i}" for i in range(1, 12)
    )
    content = f"## Essential Requirements\n\n{bullets}\n"

    result = validate_essential_requirements(content)

    assert not result.ok
    assert "11 items" in result.message


def test_gemini_coder_alias_maps_to_opencode_model() -> None:
    assert (
        _validate_coder("gemini")
        == llm_config.CONVERGENCE_REVIEW_CODER_ALIASES["gemini"]
    )


def test_configured_llm_clis_pin_expected_model_and_effort() -> None:
    claude_coder = _get_coder_command("claude")
    codex_coder = _get_coder_command("codex")

    assert claude_coder[claude_coder.index("--model") + 1] == llm_config.CLAUDE_MODEL
    assert "--effort" in claude_coder
    assert claude_coder[claude_coder.index("--effort") + 1] == llm_config.CLAUDE_EFFORT
    assert "--model" not in codex_coder
    assert "-m" not in codex_coder
    assert (
        f'model_reasoning_effort="{llm_config.CODEX_REASONING_EFFORT}"' in codex_coder
    )

    assert (
        REVIEWER_COMMANDS["claude"][REVIEWER_COMMANDS["claude"].index("--model") + 1]
        == llm_config.CLAUDE_MODEL
    )
    assert "--effort" in REVIEWER_COMMANDS["claude"]
    assert (
        f'model_reasoning_effort="{llm_config.CODEX_REASONING_EFFORT}"'
        in REVIEWER_COMMANDS["codex"]
    )
    assert "--sandbox" in REVIEWER_COMMANDS["codex"]
    assert (
        REVIEWER_COMMANDS["codex"][REVIEWER_COMMANDS["codex"].index("--sandbox") + 1]
        == "read-only"
    )
    assert "--ephemeral" in REVIEWER_COMMANDS["codex"]
    assert "--permission-mode" in REVIEWER_COMMANDS["claude"]
    assert (
        REVIEWER_COMMANDS["claude"][
            REVIEWER_COMMANDS["claude"].index("--permission-mode") + 1
        ]
        == "plan"
    )
    assert "--disallowed-tools" in REVIEWER_COMMANDS["claude"]
    assert (
        REVIEWER_COMMANDS["claude"][
            REVIEWER_COMMANDS["claude"].index("--disallowed-tools") + 1
        ]
        == "Edit,Write,NotebookEdit,Bash"
    )
    assert "--no-session-persistence" in REVIEWER_COMMANDS["claude"]
    # Gemini reviews run through Antigravity (agy); the prompt is appended after --print.
    assert REVIEWER_COMMANDS["gemini"][0] == "agy"
    assert REVIEWER_COMMANDS["gemini"][-1] == "--print"
    assert REVIEWER_COMMANDS["gemini"][REVIEWER_COMMANDS["gemini"].index("--model") + 1] == llm_config.AGY_MODEL
    if llm_config.CODEX_MODEL:
        assert f'model="{llm_config.CODEX_MODEL}"' in REVIEWER_COMMANDS["codex"]
    else:
        assert not any(arg.startswith("model=") for arg in REVIEWER_COMMANDS["codex"])


def test_llm_config_loader_falls_back_to_example_and_prefers_local(tmp_path) -> None:
    from convergence_review.llm_config_loader import load_llm_config_from

    example_file = tmp_path / "llm_config.example.py"
    example_file.write_text('CLAUDE_MODEL = "example-model"\n', encoding="utf-8")
    loaded_fallback = load_llm_config_from(tmp_path)
    assert loaded_fallback.CLAUDE_MODEL == "example-model"

    local_file = tmp_path / "llm_config.py"
    local_file.write_text('CLAUDE_MODEL = "local-override-model"\n', encoding="utf-8")
    loaded_local = load_llm_config_from(tmp_path)
    assert loaded_local.CLAUDE_MODEL == "local-override-model"


def test_symlinked_llm_config_still_resolves_reviewer_guidelines_in_playbook_root(tmp_path) -> None:
    from convergence_review.cli import ReviewerSpec, _resolve_role_guidelines
    from convergence_review.llm_config_loader import load_llm_config_from

    synced_dir = tmp_path / "synced_cloud_folder"
    synced_dir.mkdir()
    real_config = synced_dir / "shared_llm_config.py"
    real_config.write_text('CLAUDE_MODEL = "synced-model"\n', encoding="utf-8")

    playbook_dir = tmp_path / "lca_playbook"
    (playbook_dir / "reviewers").mkdir(parents=True)
    expected_guidelines = "# Arch Critic\n\n## R1: Unjustified Scope\n"
    (playbook_dir / "reviewers" / "architecture_critic.md").write_text(expected_guidelines, encoding="utf-8")
    (playbook_dir / "llm_config.py").symlink_to(real_config)

    loaded = load_llm_config_from(playbook_dir)
    resolved = _resolve_role_guidelines(
        (ReviewerSpec(agent_name="codex", role_name="architecture"),),
        config_module=loaded,
    )
    assert resolved["architecture"] == expected_guidelines


def test_reviewer_names_and_roles_match_llm_config() -> None:
    assert set(REVIEWER_NAMES) == set(llm_config.CONVERGENCE_REVIEW_AVAILABLE_REVIEWERS)
    assert set(REVIEWER_ROLE_NAMES) == set(llm_config.CONVERGENCE_REVIEW_REVIEWER_ROLES)


def test_grok_reviewer_command_uses_grok_cli_read_only() -> None:
    cmd = REVIEWER_COMMANDS["grok"]

    assert cmd[:7] == [
        "grok",
        "-m",
        llm_config.GROK_MODEL,
        "--reasoning-effort",
        llm_config.GROK_REASONING_EFFORT,
        "--permission-mode",
        "dontAsk",
    ]
    assert "--prompt-file" not in REVIEWER_COMMANDS["grok"]
    assert "--disable-web-search" in cmd
    assert "--no-subagents" in cmd
    assert set(cmd[cmd.index("--disallowed-tools") + 1].split(",")) == {
        "run_terminal_command",
        "search_replace",
        "write",
        "spawn_subagent",
        "enter_plan_mode",
        "exit_plan_mode",
        "ask_user_question",
    }
    assert cmd[cmd.index("--output-format") + 1] == "plain"


def test_prepare_reviewer_process_grok_writes_prompt_file(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    iteration_dir = tmp_path / "iter"

    cmd, _, input_payload = _prepare_reviewer_process(
        "grok", "hello review", repo_dir, iteration_dir=iteration_dir
    )

    assert input_payload is None
    assert cmd[-2] == "--prompt-file"
    prompt_path = Path(cmd[-1])
    assert prompt_path.is_absolute()
    assert prompt_path.exists()
    assert prompt_path.parent == iteration_dir
    assert prompt_path.read_text(encoding="utf-8") == "hello review"
    assert list(repo_dir.iterdir()) == []

    second_cmd, _, _ = _prepare_reviewer_process(
        "grok", "hello review", repo_dir, iteration_dir=iteration_dir
    )
    assert Path(second_cmd[-1]) != prompt_path
    assert list(repo_dir.iterdir()) == []


def test_parse_reviewers_arg_accepts_pairs_and_same_agent_multiple_roles() -> None:
    assert _parse_reviewers_arg("codex:architecture,codex:core,grok:core") == (
        ReviewerSpec("codex", "architecture"),
        ReviewerSpec("codex", "core"),
        ReviewerSpec("grok", "core"),
    )


def test_parse_reviewers_arg_accepts_per_reviewer_claude_models() -> None:
    assert _parse_reviewers_arg(
        "codex:architecture,claude-sonnet:architecture,codex:core,"
        "claude-opus:core,grok:core"
    ) == (
        ReviewerSpec("codex", "architecture"),
        ReviewerSpec("claude-sonnet", "architecture"),
        ReviewerSpec("codex", "core"),
        ReviewerSpec("claude-opus", "core"),
        ReviewerSpec("grok", "core"),
    )


def test_essential_requirements_validation_accepts_er_sign_off_status_line() -> None:
    from convergence_review.design_doc_validation import validate_essential_requirements

    doc = (
        "# Feature\n\n"
        "# Essential Requirements\n"
        "ER Sign-Off Status: Agent-Drafted (Unreviewed)\n\n"
        "- [US-1] First requirement\n"
        "- [US-2; Data Integrity] Second requirement\n"
    )
    res = validate_essential_requirements(doc)
    assert res.ok is True, res.message


def test_claude_reviewer_model_override_only_changes_model_argument(tmp_path) -> None:
    default_cmd, _, _ = _prepare_reviewer_process("claude", "review prompt", tmp_path)
    sonnet_cmd, _, _ = _prepare_reviewer_process(
        "claude-sonnet", "review prompt", tmp_path
    )
    opus_cmd, _, _ = _prepare_reviewer_process("claude-opus", "review prompt", tmp_path)

    model_index = default_cmd.index("--model") + 1
    assert default_cmd[model_index] == llm_config.CLAUDE_MODEL
    assert sonnet_cmd[model_index] == "sonnet"
    assert opus_cmd[model_index] == "opus"
    assert sonnet_cmd[:model_index] + sonnet_cmd[model_index + 1 :] == (
        default_cmd[:model_index] + default_cmd[model_index + 1 :]
    )
    assert REVIEWER_COMMANDS["claude"][model_index] == llm_config.CLAUDE_MODEL


def test_run_reviewers_dispatches_two_architecture_reviewers(
    tmp_path, monkeypatch
) -> None:
    seen: list[ReviewerSpec] = []

    async def fake_run_single_reviewer(
        reviewer, prompt, cwd, iteration_dir=None
    ) -> ReviewResult:
        seen.append(reviewer)
        return ReviewResult(
            agent_name=reviewer.agent_name,
            role_name=reviewer.role_name,
            raw_output="[]",
        )

    monkeypatch.setattr(
        "convergence_review.reviewers._run_single_reviewer",
        fake_run_single_reviewer,
    )
    specs = (
        ReviewerSpec("codex", "architecture"),
        ReviewerSpec("claude-sonnet", "architecture"),
    )

    results = asyncio.run(
        run_reviewers(
            design_doc_content="design",
            cwd=tmp_path,
            reviewer_specs=specs,
            role_guidelines={"architecture": "guidelines"},
        )
    )

    assert seen == list(specs)
    assert [result.label for result in results] == [
        "codex:architecture",
        "claude-sonnet:architecture",
    ]


def test_agy_reviewer_uses_fake_home_and_single_prompt_channel(
    tmp_path,
    monkeypatch,
) -> None:
    record = tmp_path / "agy_invocation.json"
    fake_agy = tmp_path / "fake_agy.py"
    monkeypatch.setitem(
        REVIEWER_COMMANDS,
        "agy",
        [sys.executable, str(fake_agy), str(record)],
    )

    cmd, env, input_payload = _prepare_reviewer_process(
        "agy",
        "review prompt",
        tmp_path,
        iteration_dir=tmp_path / "iteration_01",
    )

    assert cmd == [sys.executable, str(fake_agy), str(record), "review prompt"]
    assert input_payload is None
    assert env["HOME"] == str((tmp_path / "iteration_01" / "agy_mock_home").resolve())
    assert (
        tmp_path
        / "iteration_01"
        / "agy_mock_home"
        / ".gemini"
        / "antigravity-cli"
        / "settings.json"
    ).exists()


def test_gemini_reviewer_uses_agy_fake_home_and_prompt_argument(tmp_path) -> None:
    cmd, env, input_payload = _prepare_reviewer_process(
        "gemini",
        "review prompt",
        tmp_path,
        iteration_dir=tmp_path / "iteration_01",
    )

    assert cmd[0] == "agy"
    assert cmd[-1] == "review prompt"
    assert input_payload is None
    assert env["HOME"] == str((tmp_path / "iteration_01" / "agy_mock_home").resolve())
    settings = json.loads(
        (
            tmp_path / "iteration_01" / "agy_mock_home" / ".gemini" / "antigravity-cli" / "settings.json"
        ).read_text()
    )
    assert "command(*)" in settings["permissions"]["deny"]


def test_opencode_custom_reviewer_denies_edit_shell_and_external_directory_access(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setitem(REVIEWER_COMMANDS, "opencode-custom", ["opencode", "run", "-m", "x"])
    _, env, input_payload = _prepare_reviewer_process(
        "opencode-custom",
        "review prompt",
        tmp_path,
    )

    assert input_payload == b"review prompt"
    assert json.loads(env["OPENCODE_PERMISSION"]) == {
        "edit": "deny",
        "bash": "deny",
        "external_directory": "deny",
    }


def test_agy_reviewer_result_parses_json_from_prompt_argument_subprocess(
    tmp_path,
    monkeypatch,
) -> None:
    fake_agy = tmp_path / "fake_agy.py"
    fake_agy.write_text(
        """
print('[{"severity":"low","category":"bug","file":"x.py","description":"ok"}]')
""".lstrip()
    )
    monkeypatch.setitem(REVIEWER_COMMANDS, "agy", [sys.executable, str(fake_agy)])

    result = asyncio.run(
        _run_single_reviewer(
            "agy",
            "review prompt",
            tmp_path,
            iteration_dir=tmp_path / "iteration_01",
        )
    )

    assert result.parse_error is False
    assert result.issues[0]["description"] == "ok"


def test_agy_json_repair_uses_fake_home_and_prompt_argument(
    tmp_path,
    monkeypatch,
) -> None:
    record = tmp_path / "agy_repair_invocation.json"
    fake_agy = tmp_path / "fake_agy_repair.py"
    fake_agy.write_text(
        """
import json
import os
import sys

record = sys.argv[1]
payload = {
    "argv_prompt": sys.argv[2],
    "stdin": "",
    "home": os.environ["HOME"],
    "settings_exists": os.path.exists(
        os.path.join(
            os.environ["HOME"],
            ".gemini",
            "antigravity-cli",
            "settings.json",
        )
    ),
}
open(record, "w").write(json.dumps(payload))
print('[{"severity":"medium","category":"bug","file":"x.py","description":"fixed"}]')
""".lstrip()
    )
    monkeypatch.setitem(
        REVIEWER_COMMANDS,
        "agy",
        [sys.executable, str(fake_agy), str(record)],
    )

    repaired, attempts = asyncio.run(
        _repair_review_json(
            "agy",
            "malformed reviewer output",
            tmp_path,
            iteration_dir=tmp_path / "iteration_02",
        )
    )

    payload = json.loads(record.read_text())
    assert repaired is not None
    assert repaired.infrastructure_status == "complete"
    assert repaired.issues == [
        {
            "severity": "medium",
            "category": "bug",
            "file": "x.py",
            "description": "fixed",
        }
    ]
    assert len(attempts) == 1
    assert attempts[0].parse_error is False
    assert "malformed reviewer output" in payload["argv_prompt"]
    assert payload["stdin"] == ""
    assert payload["home"] == str(
        (tmp_path / "iteration_02" / "agy_mock_home").resolve()
    )
    assert payload["settings_exists"] is True


def test_agy_internal_timeout_is_not_json_repaired(tmp_path, monkeypatch) -> None:
    fake_agy = tmp_path / "fake_agy_timeout.py"
    fake_agy.write_text(
        """
print("Error: timed out waiting for response")
""".lstrip()
    )
    monkeypatch.setitem(REVIEWER_COMMANDS, "agy", [sys.executable, str(fake_agy)])

    result = asyncio.run(
        _run_single_reviewer(
            "agy",
            "review prompt",
            tmp_path,
            iteration_dir=tmp_path / "iteration_03",
        )
    )

    assert result.timed_out is True
    assert result.parse_error is False
    assert result.repair_attempts == []
    assert result.raw_output.strip() == "Error: timed out waiting for response"


def test_persona_parse_failure_uses_same_json_repair_as_blocking_roles(
    tmp_path, monkeypatch
) -> None:
    fake_reviewer = tmp_path / "fake_persona_parse_failure.py"
    fake_reviewer.write_text(
        """
import sys

prompt = sys.argv[-1]
if "Convert the reviewer output" in prompt:
    print('[{"severity":"low","category":"other","file":"general","description":"recovered"}]')
else:
    print("this is not json")
""".lstrip()
    )
    monkeypatch.setitem(
        REVIEWER_COMMANDS,
        "agy",
        [sys.executable, str(fake_reviewer)],
    )

    result = asyncio.run(
        _run_single_reviewer(
            ReviewerSpec("agy", "peer"),
            "review prompt",
            tmp_path,
            iteration_dir=tmp_path / "iteration_04",
        )
    )

    assert result.label == "agy:peer"
    assert result.parse_error is False
    assert result.parse_repaired is True
    assert len(result.repair_attempts) == 1
    assert result.issues[0]["description"] == "recovered"
    assert result.raw_output.strip() == "this is not json"


def test_tool_failed_reviewer_is_retried_independently(tmp_path, monkeypatch) -> None:
    counter = tmp_path / "attempt_count.txt"
    fake_reviewer = tmp_path / "fake_tool_failure_then_success.py"
    fake_reviewer.write_text(
        f"""
from pathlib import Path

counter = Path({str(counter)!r})
attempt = int(counter.read_text()) + 1 if counter.exists() else 1
counter.write_text(str(attempt))
if attempt == 1:
    print('{{"infrastructure_status":"tool_failed","status_detail":"read canceled","issues":[]}}')
else:
    print('[]')
""".lstrip()
    )
    monkeypatch.setitem(REVIEWER_COMMANDS, "agy", [sys.executable, str(fake_reviewer)])

    result = asyncio.run(
        _run_single_reviewer(
            ReviewerSpec("agy", "architecture"),
            "review prompt",
            tmp_path,
        )
    )

    assert result.infrastructure_status == "complete"
    assert result.retry_count == 1
    assert len(result.prior_attempts) == 1
    assert result.prior_attempts[0].infrastructure_status == "tool_failed"
    assert result.prior_attempts[0].status_detail == "read canceled"


def test_nonzero_reviewer_exit_with_valid_payload_preserves_findings(
    tmp_path, monkeypatch
) -> None:
    fake_reviewer = tmp_path / "fake_nonzero_reviewer.py"
    fake_reviewer.write_text(
        """
import sys

print('[{"severity": "high", "category": "bug", "description": "Real finding"}]')
print('usage limit warning', file=sys.stderr)
raise SystemExit(7)
""".lstrip()
    )
    monkeypatch.setitem(REVIEWER_COMMANDS, "agy", [sys.executable, str(fake_reviewer)])

    result = asyncio.run(
        _run_single_reviewer(
            ReviewerSpec("agy", "core"),
            "review prompt",
            tmp_path,
        )
    )

    assert result.infrastructure_status == "complete"
    assert result.retry_count == 0
    assert result.issues == [
        {"severity": "high", "category": "bug", "description": "Real finding"}
    ]
    assert result.returncode == 7
    assert "usage limit warning" in result.stderr_output


def test_nonzero_reviewer_exit_without_parseable_output_is_tool_failure(
    tmp_path, monkeypatch
) -> None:
    fake_reviewer = tmp_path / "fake_nonzero_unparseable_reviewer.py"
    fake_reviewer.write_text(
        """
import sys

print('backend crashed mid-review')
print('backend unavailable', file=sys.stderr)
raise SystemExit(7)
""".lstrip()
    )
    monkeypatch.setitem(REVIEWER_COMMANDS, "agy", [sys.executable, str(fake_reviewer)])

    result = asyncio.run(
        _run_single_reviewer(
            ReviewerSpec("agy", "core"),
            "review prompt",
            tmp_path,
        )
    )

    assert result.infrastructure_status == "tool_failed"
    assert result.retry_count == 1
    assert result.issues == []
    assert result.status_detail == (
        "reviewer exited with code 7 without a parseable review"
    )
    assert len(result.repair_attempts) > 0
    assert all(attempt.parse_error for attempt in result.repair_attempts)
    assert "backend unavailable" in result.stderr_output


def test_nonzero_reviewer_exit_with_repairable_output_recovers_via_repair(
    tmp_path, monkeypatch
) -> None:
    fake_reviewer = tmp_path / "fake_nonzero_repairable_reviewer.py"
    fake_reviewer.write_text(
        """
import sys

prompt = sys.argv[-1]
if "Convert the reviewer output" in prompt:
    print('[{"severity":"high","category":"bug","file":"x.py","description":"recovered"}]')
else:
    print("Found one issue: high bug in x.py (recovered)")
    print("usage limit warning", file=sys.stderr)
    raise SystemExit(7)
""".lstrip()
    )
    monkeypatch.setitem(REVIEWER_COMMANDS, "agy", [sys.executable, str(fake_reviewer)])

    result = asyncio.run(
        _run_single_reviewer(
            ReviewerSpec("agy", "core"),
            "review prompt",
            tmp_path,
        )
    )

    assert result.infrastructure_status == "complete"
    assert result.retry_count == 0
    assert result.parse_repaired is True
    assert len(result.repair_attempts) == 1
    assert result.issues == [
        {
            "severity": "high",
            "category": "bug",
            "file": "x.py",
            "description": "recovered",
        }
    ]
    assert result.returncode == 7
    assert "usage limit warning" in result.stderr_output


def test_nonzero_reviewer_exit_with_incidental_fragment_is_not_complete(
    tmp_path, monkeypatch
) -> None:
    fake_reviewer = tmp_path / "fake_nonzero_incidental_fragment_reviewer.py"
    fake_reviewer.write_text(
        """
import sys

prompt = sys.argv[-1]
if "Convert the reviewer output" in prompt:
    print("null")
else:
    print("backend crashed before review ran")
    print("retry schedule: []")
    print("backend unavailable", file=sys.stderr)
    raise SystemExit(7)
""".lstrip()
    )
    monkeypatch.setitem(REVIEWER_COMMANDS, "agy", [sys.executable, str(fake_reviewer)])

    result = asyncio.run(
        _run_single_reviewer(
            ReviewerSpec("agy", "core"),
            "review prompt",
            tmp_path,
        )
    )

    assert result.infrastructure_status == "tool_failed"
    assert result.issues == []
    assert result.retry_count == 1
    assert len(result.repair_attempts) > 0
    assert all(attempt.parse_error for attempt in result.repair_attempts)
    assert "backend unavailable" in result.stderr_output


def test_nonzero_reviewer_exit_with_fenced_payload_preserves_findings(
    tmp_path, monkeypatch
) -> None:
    fake_reviewer = tmp_path / "fake_nonzero_fenced_reviewer.py"
    fake_reviewer.write_text(
        """
import sys

print("Findings below:")
print("```json")
print('[{"severity": "high", "category": "bug", "description": "Fenced finding"}]')
print("```")
print("usage limit warning", file=sys.stderr)
raise SystemExit(7)
""".lstrip()
    )
    monkeypatch.setitem(REVIEWER_COMMANDS, "agy", [sys.executable, str(fake_reviewer)])

    result = asyncio.run(
        _run_single_reviewer(
            ReviewerSpec("agy", "core"),
            "review prompt",
            tmp_path,
        )
    )

    assert result.infrastructure_status == "complete"
    assert result.retry_count == 0
    assert result.parse_repaired is False
    assert result.issues == [
        {"severity": "high", "category": "bug", "description": "Fenced finding"}
    ]
    assert result.returncode == 7


def test_zero_exit_reviewer_keeps_embedded_fragment_extraction(
    tmp_path, monkeypatch
) -> None:
    fake_reviewer = tmp_path / "fake_zero_exit_embedded_reviewer.py"
    fake_reviewer.write_text(
        """
print("Review notes:")
print('[{"severity": "high", "category": "bug", "description": "Embedded finding"}]')
print("Done.")
""".lstrip()
    )
    monkeypatch.setitem(REVIEWER_COMMANDS, "agy", [sys.executable, str(fake_reviewer)])

    result = asyncio.run(
        _run_single_reviewer(
            ReviewerSpec("agy", "core"),
            "review prompt",
            tmp_path,
        )
    )

    assert result.infrastructure_status == "complete"
    assert result.retry_count == 0
    assert result.parse_repaired is False
    assert result.issues == [
        {"severity": "high", "category": "bug", "description": "Embedded finding"}
    ]
    assert result.returncode == 0


def test_repair_output_self_reporting_tool_failed_stays_incomplete(
    tmp_path, monkeypatch
) -> None:
    fake_reviewer = tmp_path / "fake_repair_reports_failure.py"
    fake_reviewer.write_text(
        """
import sys

prompt = sys.argv[-1]
if "Convert the reviewer output" in prompt:
    print(
        '{"infrastructure_status":"tool_failed",'
        '"status_detail":"backend degraded","issues":[]}'
    )
else:
    print("this is not json")
""".lstrip()
    )
    monkeypatch.setitem(REVIEWER_COMMANDS, "agy", [sys.executable, str(fake_reviewer)])

    result = asyncio.run(
        _run_single_reviewer(
            ReviewerSpec("agy", "core"),
            "review prompt",
            tmp_path,
        )
    )

    assert result.infrastructure_status == "tool_failed"
    assert result.status_detail == "backend degraded"
    assert result.issues == []
    assert result.parse_repaired is False
    assert result.retry_count == 1
    assert result.prior_attempts[0].infrastructure_status == "tool_failed"


def test_nonzero_repair_exit_with_incidental_fragment_is_not_complete(
    tmp_path, monkeypatch
) -> None:
    fake_reviewer = tmp_path / "fake_nonzero_repair_crash.py"
    fake_reviewer.write_text(
        """
import sys

print("backend crashed before running")
print("retry schedule: []")
print("backend unavailable", file=sys.stderr)
raise SystemExit(7)
""".lstrip()
    )
    monkeypatch.setitem(REVIEWER_COMMANDS, "agy", [sys.executable, str(fake_reviewer)])

    result = asyncio.run(
        _run_single_reviewer(
            ReviewerSpec("agy", "core"),
            "review prompt",
            tmp_path,
        )
    )

    assert result.infrastructure_status == "tool_failed"
    assert result.issues == []
    assert result.parse_repaired is False
    assert result.retry_count == 1
    assert len(result.repair_attempts) > 0
    assert all(attempt.parse_error for attempt in result.repair_attempts)


def test_zero_exit_repair_keeps_embedded_fragment_extraction(
    tmp_path, monkeypatch
) -> None:
    fake_reviewer = tmp_path / "fake_zero_exit_embedded_repair.py"
    fake_reviewer.write_text(
        """
import sys

prompt = sys.argv[-1]
if "Convert the reviewer output" in prompt:
    print("Here is the converted output:")
    print('[{"severity":"high","category":"bug","file":"x.py","description":"recovered"}]')
else:
    print("prose review that is not json")
""".lstrip()
    )
    monkeypatch.setitem(REVIEWER_COMMANDS, "agy", [sys.executable, str(fake_reviewer)])

    result = asyncio.run(
        _run_single_reviewer(
            ReviewerSpec("agy", "core"),
            "review prompt",
            tmp_path,
        )
    )

    assert result.infrastructure_status == "complete"
    assert result.parse_repaired is True
    assert result.retry_count == 0
    assert result.issues == [
        {
            "severity": "high",
            "category": "bug",
            "file": "x.py",
            "description": "recovered",
        }
    ]


def test_incomplete_persona_review_is_not_rendered_as_clean() -> None:
    consolidated = _consolidate_reviews(
        [
            ReviewResult(
                "claude",
                "malformed",
                role_name="peer",
                infrastructure_status="parse_failed",
                status_detail="output remained unparseable",
            )
        ]
    )

    assert "Reviewer infrastructure status: parse_failed" in consolidated
    assert "must not be treated as a clean review" in consolidated
    assert "--- claude:peer reviewer ---\n[]" not in consolidated


def test_run_reviewers_returns_empty_blocking_output_for_orchestrator_handling(
    tmp_path,
    monkeypatch,
) -> None:
    fake_reviewer = tmp_path / "fake_empty_reviewer.py"
    fake_reviewer.write_text("")
    monkeypatch.setitem(
        REVIEWER_COMMANDS,
        "agy",
        [sys.executable, str(fake_reviewer)],
    )

    results = asyncio.run(
        run_reviewers(
            "# Essential Requirements\n- Do the thing.",
            tmp_path,
            reviewer_specs=(ReviewerSpec("agy", "core"),),
            role_guidelines={"core": "Core review guidelines"},
            iteration_dir=tmp_path / "iteration_05",
        )
    )

    assert len(results) == 1
    assert results[0].label == "agy:core"
    assert results[0].parse_error is True
    assert results[0].raw_output == ""


def test_parse_reviewers_arg_dedupes_and_preserves_input_order() -> None:
    assert _parse_reviewers_arg("codex:core,claude:core,codex:core") == (
        ReviewerSpec("codex", "core"),
        ReviewerSpec("claude", "core"),
    )


def test_parse_reviewers_arg_rejects_unknown() -> None:
    with pytest.raises(argparse.ArgumentTypeError) as exc:
        _parse_reviewers_arg("claude:core,bogus:core")

    assert "<agent>:<role>" in str(exc.value)
    assert "Accepted agents" in str(exc.value)
    assert "Accepted roles" in str(exc.value)


def test_parse_reviewers_arg_rejects_bare_name() -> None:
    with pytest.raises(argparse.ArgumentTypeError) as exc:
        _parse_reviewers_arg("claude")

    assert "<agent>:<role>" in str(exc.value)


@pytest.mark.parametrize("agent", ["claude-", "claude-/opus", "claude--opus"])
def test_parse_reviewers_arg_rejects_invalid_claude_model_selector(agent) -> None:
    with pytest.raises(argparse.ArgumentTypeError) as exc:
        _parse_reviewers_arg(f"{agent}:core")

    assert "claude-<model>" in str(exc.value)


def test_parse_reviewers_arg_rejects_empty() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        _parse_reviewers_arg(",")


def test_resolve_role_guidelines_loads_registered_repo_files() -> None:
    guidelines = _resolve_role_guidelines(
        (ReviewerSpec("codex", "architecture"), ReviewerSpec("codex", "core"))
    )

    assert set(guidelines) == {"architecture", "core"}
    assert "## R1:" in guidelines["architecture"]
    assert "## R1:" in guidelines["core"]


def test_resolve_role_guidelines_fails_for_missing_registered_file(monkeypatch) -> None:
    monkeypatch.setitem(
        CLI_ROLE_CONFIGS["core"],
        "guidelines",
        "reviewers/missing_role_guidelines.md",
    )

    with pytest.raises(SystemExit):
        _resolve_role_guidelines((ReviewerSpec("codex", "core"),))


def test_project_root_from_git_common_dir_handles_linked_worktree() -> None:
    common_dir = Path("/repo/.git/worktrees/example-worktree")

    assert _project_root_from_git_common_dir(common_dir) == Path("/repo")


def test_consolidate_reviews_groups_by_influence_tier() -> None:
    consolidated = _consolidate_reviews(
        [
            ReviewResult(
                "codex",
                "[]",
                role_name="peer",
                issues=[
                    {
                        "severity": "medium",
                        "file": "peer.py",
                        "description": "Peer note",
                    }
                ],
            ),
            ReviewResult(
                "codex",
                "[]",
                role_name="architecture",
                issues=[
                    {"severity": "high", "file": "arch.py", "description": "Arch note"}
                ],
            ),
            ReviewResult(
                "claude",
                "[]",
                role_name="core",
                issues=[
                    {
                        "severity": "medium",
                        "file": "core.py",
                        "description": "Core note",
                    }
                ],
            ),
        ]
    )

    assert consolidated.index("ARCHITECTURE TIER") < consolidated.index("CORE TIER")
    assert consolidated.index("CORE TIER") < consolidated.index("PERSONA TIER")
    assert "Act on each finding or explicitly defer" in consolidated
    assert "Persona findings are advisory" in consolidated
    assert '"reviewer_role": "architecture"' in consolidated


def test_annotated_issues_use_selected_reviewer_role_metadata() -> None:
    issues = _annotated_issues(
        ReviewResult(
            "codex",
            "[]",
            role_name="client",
            issues=[
                {
                    "severity": "high",
                    "reviewer": "codex:core",
                    "reviewer_agent": "codex",
                    "reviewer_role": "core",
                    "file": "client.py",
                    "description": "Persona concern must stay advisory",
                }
            ],
        )
    )

    assert issues[0]["reviewer"] == "codex:client"
    assert issues[0]["reviewer_agent"] == "codex"
    assert issues[0]["reviewer_role"] == "client"


def test_summary_renders_tier_sections_and_filters_persona_blockers() -> None:
    summary = format_summary(
        [
            {
                "iteration": 1,
                "issues": [
                    {
                        "severity": "high",
                        "reviewer": "codex:client",
                        "reviewer_role": "client",
                        "file": "client.py",
                        "description": "Client concern",
                    }
                ],
                "convergence_issues": [],
                "roles_run": ["architecture", "core", "client"],
                "assessments": [
                    {
                        "reviewer": "codex:client",
                        "role": "client",
                        "assessment": "Client is comfortable.",
                    }
                ],
                "converged": True,
            }
        ],
        deferred_issues=[
            {
                "iteration": 1,
                "severity": "medium",
                "reviewer": "codex:architecture",
                "role": "architecture",
                "summary": "Deliberate deferral",
                "rationale": "Needs product input",
            }
        ],
    )

    assert "Status: CONVERGED" in summary
    assert "Architecture Tier:" in summary
    assert "Core Tier:" in summary
    assert "Persona Tier:" in summary
    assert "codex:client client.py: Client concern" in summary
    assert "codex:client: Client is comfortable." in summary
    assert "blocking issue(s) remaining" not in summary
