import json

from turnbreak import install as install_module


def test_install_claude_merges_hooks_and_installs_skill(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    dest = install_module.install("claude", None)

    assert dest == tmp_path / ".claude" / "settings.json"
    settings = json.loads(dest.read_text())
    assert "UserPromptSubmit" in settings["hooks"]
    assert "Stop" in settings["hooks"]

    skill_path = tmp_path / ".claude" / "skills" / "turnbreak" / "SKILL.md"
    assert skill_path.exists()
    installed = skill_path.read_text()
    assert "{{TURNBREAK_COMMAND}}" not in installed
    assert install_module.turnbreak_command() in installed


def test_install_claude_preserves_existing_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    settings_path = tmp_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(json.dumps({"model": "claude-sonnet-5", "theme": "dark"}))

    install_module.install("claude", None)

    settings = json.loads(settings_path.read_text())
    assert settings["model"] == "claude-sonnet-5"
    assert settings["theme"] == "dark"
    assert "hooks" in settings


def test_install_claude_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    install_module.install("claude", None)
    install_module.install("claude", None)

    settings_path = tmp_path / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text())
    assert len(settings["hooks"]["UserPromptSubmit"]) == 1
    assert len(settings["hooks"]["Stop"]) == 1


def test_install_gemini_merges_hooks(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    dest = install_module.install("gemini", None)

    assert dest == tmp_path / ".gemini" / "settings.json"
    settings = json.loads(dest.read_text())
    assert "BeforeAgent" in settings["hooks"]
    assert "AfterAgent" in settings["hooks"]


def test_install_gemini_preserves_existing_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    settings_path = tmp_path / ".gemini" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(json.dumps({"theme": "dark"}))

    install_module.install("gemini", None)

    settings = json.loads(settings_path.read_text())
    assert settings["theme"] == "dark"
    assert "hooks" in settings


def test_install_gemini_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    install_module.install("gemini", None)
    install_module.install("gemini", None)

    settings_path = tmp_path / ".gemini" / "settings.json"
    settings = json.loads(settings_path.read_text())
    assert len(settings["hooks"]["BeforeAgent"]) == 1
    assert len(settings["hooks"]["AfterAgent"]) == 1


def test_install_codex_merges_hooks(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    dest = install_module.install("codex", None)

    assert dest == tmp_path / ".codex" / "hooks.json"
    hooks = json.loads(dest.read_text())
    assert "UserPromptSubmit" in hooks["hooks"]
    assert "Stop" in hooks["hooks"]


def test_install_codex_preserves_existing_unrelated_hooks(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    hooks_path = tmp_path / ".codex" / "hooks.json"
    hooks_path.parent.mkdir(parents=True)
    unrelated_hook = {
        "matcher": "*",
        "hooks": [{"type": "command", "command": "code-review-graph"}],
    }
    hooks_path.write_text(
        json.dumps({"hooks": {"PostToolUse": [unrelated_hook], "SessionStart": [unrelated_hook]}})
    )

    install_module.install("codex", None)

    hooks = json.loads(hooks_path.read_text())
    assert hooks["hooks"]["PostToolUse"][0]["hooks"][0]["command"] == "code-review-graph"
    assert hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"] == "code-review-graph"
    assert "UserPromptSubmit" in hooks["hooks"]
    assert "Stop" in hooks["hooks"]


def test_install_codex_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    install_module.install("codex", None)
    install_module.install("codex", None)

    hooks_path = tmp_path / ".codex" / "hooks.json"
    hooks = json.loads(hooks_path.read_text())
    assert len(hooks["hooks"]["UserPromptSubmit"]) == 1
    assert len(hooks["hooks"]["Stop"]) == 1


def test_install_copilot_installs_extension_and_turn_boundary_hooks(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    install_module.install("copilot", None)

    extension_dir = tmp_path / ".copilot" / "extensions" / "turnbreak"
    assert (extension_dir / "extension.mjs").exists()
    assert (extension_dir / "package.json").exists()

    hooks_path = tmp_path / ".copilot" / "hooks" / "turnbreak.json"
    assert hooks_path.exists()
    hooks = json.loads(hooks_path.read_text())
    assert hooks["version"] == 1
    assert "userPromptSubmitted" in hooks["hooks"]
    assert "agentStop" in hooks["hooks"]
    start_command = hooks["hooks"]["userPromptSubmitted"][0]["bash"]
    assert install_module.hook_command() in start_command
    assert start_command.endswith("--hint start")
    stop_command = hooks["hooks"]["agentStop"][0]["bash"]
    assert stop_command.endswith("--hint end")


def test_install_copilot_hooks_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    install_module.install("copilot", None)
    install_module.install("copilot", None)

    hooks_path = tmp_path / ".copilot" / "hooks" / "turnbreak.json"
    hooks = json.loads(hooks_path.read_text())
    assert len(hooks["hooks"]["userPromptSubmitted"]) == 1
    assert len(hooks["hooks"]["agentStop"]) == 1


def test_install_copilot_installs_skill(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    install_module.install("copilot", None)

    skill_path = tmp_path / ".copilot" / "skills" / "turnbreak" / "SKILL.md"
    assert skill_path.exists()
    installed = skill_path.read_text()
    assert "{{TURNBREAK_COMMAND}}" not in installed
    assert install_module.turnbreak_command() in installed


def test_skill_argument_hint_is_a_quoted_string():
    """Copilot's skill loader requires `argument-hint` to be a string.

    An unquoted value starting with `[` parses as a YAML flow sequence
    instead, which fails Copilot's schema check and drops the whole skill
    (it never appears in `copilot skill list`, and shows no error to the
    user). Claude Code tolerates the array form, so this only breaks
    silently on Copilot.
    """
    repo_root = install_module.adapters_dir().parents[2]
    for path in (
        install_module.skill_source_path(),
        repo_root / "SKILL.md",
    ):
        for line in path.read_text().splitlines():
            if line.startswith("argument-hint:"):
                value = line.split(":", 1)[1].strip()
                assert value.startswith('"') and value.endswith('"'), (path, line)
                break
        else:
            raise AssertionError(f"no argument-hint line in {path}")


def test_copilot_home_prefers_snap_common_dir_when_present(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "snap" / "copilot-cli" / "common").mkdir(parents=True)

    expected = tmp_path / "snap" / "copilot-cli" / "common" / ".copilot"
    assert install_module.copilot_home() == expected


def test_copilot_home_falls_back_to_plain_dotdir_without_snap(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    assert install_module.copilot_home() == tmp_path / ".copilot"


def test_install_copilot_uses_snap_path_when_snap_confined(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "snap" / "copilot-cli" / "common").mkdir(parents=True)

    dest = install_module.install("copilot", None)

    snap_copilot = tmp_path / "snap" / "copilot-cli" / "common" / ".copilot"
    assert dest == snap_copilot / "extensions" / "turnbreak"
    assert (snap_copilot / "hooks" / "turnbreak.json").exists()
    assert (snap_copilot / "skills" / "turnbreak" / "SKILL.md").exists()
    assert not (tmp_path / ".copilot" / "hooks").exists()
