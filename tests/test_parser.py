from pathlib import Path

import pytest

from brewfile_converter import BrewfileParser, process_brewfile


def test_parse_common_and_extended_directives() -> None:
    content = """
# comment
tap "homebrew/cask", "https://github.com/Homebrew/homebrew-cask"
tap 'user/tools', clone_target: 'https://github.com/user/homebrew-tools'
brew "wget"
brew "python@3.12", args: ["HEAD"], link: false
cask_args appdir: "/Applications", require_sha: true
cask "iterm2"
vscode "ms-python.python"
mas "Xcode", id: 497799835
whalebrew "ghcr.io/owner/tool:latest"
"""

    parsed = BrewfileParser.parse(content)

    assert len(parsed.taps) == 2
    assert parsed.taps[0].name == "homebrew/cask"
    assert parsed.taps[0].clone_target == "https://github.com/Homebrew/homebrew-cask"

    assert len(parsed.brews) == 2
    assert parsed.brews[1].options["args"] == ["HEAD"]
    assert parsed.brews[1].options["link"] is False

    assert len(parsed.casks) == 1
    assert parsed.casks[0].options["appdir"] == "/Applications"
    assert parsed.casks[0].options["require_sha"] is True

    assert parsed.vscode == ["ms-python.python"]
    assert len(parsed.mas_apps) == 1
    assert parsed.mas_apps[0].app_id == 497799835

    assert len(parsed.whalebrews) == 1
    assert parsed.whalebrews[0].name == "ghcr.io/owner/tool:latest"


def test_unsupported_and_strict_mode(tmp_path: Path) -> None:
    brewfile = tmp_path / "Brewfile"
    brewfile.write_text('brew "wget"\nmas "Xcode"\nunknown "x"\n')

    result = process_brewfile(brewfile)
    assert len(result.issues) == 2

    with pytest.raises(RuntimeError):
        process_brewfile(brewfile, strict=True)


def test_warns_when_no_supported_entries(tmp_path: Path) -> None:
    brewfile = tmp_path / "Brewfile"
    brewfile.write_text("# comments only\n# still comments\n")

    result = process_brewfile(brewfile)
    assert any("No supported Brewfile entries were detected" in issue.message for issue in result.issues)


def test_normalize_with_brew_uses_brew_bundle_lists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    brewfile = tmp_path / "Brewfile"
    brewfile.write_text(
        "\n".join(
            [
                'tap "homebrew/cask"',
                'brew "wget", restart_service: true',
                'cask "visual-studio-code"',
                'vscode "ms-python.python"',
                'mas "Xcode", id: 497799835',
            ]
        )
    )

    fake_lists = {
        "--tap": ["homebrew/cask"],
        "--formula": ["wget", "jq"],
        "--cask": ["visual-studio-code"],
        "--vscode": ["ms-python.python"],
        "--mas": ["Xcode", "GarageBand"],
    }

    def fake_brew_bundle_list(_: Path, flag: str) -> list[str]:
        return fake_lists[flag]

    monkeypatch.setattr("brewfile_converter.normalize.brew_bundle_list", fake_brew_bundle_list)

    result = process_brewfile(brewfile, normalize_with_brew=True)
    assert 'name: "jq"' in result.playbook
    assert any("mas app id unavailable" in issue.message for issue in result.issues)


def test_cask_args_does_not_bleed_into_brew_entries() -> None:
    content = """\
cask_args appdir: "/Applications", require_sha: true
brew "wget"
brew "git"
cask "iterm2"
"""
    parsed = BrewfileParser.parse(content)

    # brew entries must have no cask_args options
    for brew in parsed.brews:
        assert "appdir" not in brew.options, f"cask_args bled into brew '{brew.name}'"
        assert "require_sha" not in brew.options, f"cask_args bled into brew '{brew.name}'"

    # cask entries must have cask_args options
    assert parsed.casks[0].options.get("appdir") == "/Applications"
    assert parsed.casks[0].options.get("require_sha") is True


def test_names_with_special_characters_parse_correctly() -> None:
    content = """\
tap "homebrew/cask-fonts"
brew "python@3.12"
cask "font-fira-code"
cask "visual-studio-code"
"""
    parsed = BrewfileParser.parse(content)

    assert parsed.taps[0].name == "homebrew/cask-fonts"
    assert parsed.brews[0].name == "python@3.12"
    assert parsed.casks[0].name == "font-fira-code"
    assert parsed.casks[1].name == "visual-studio-code"
    assert not parsed.unsupported


def test_blank_and_comment_lines_are_silently_ignored() -> None:
    content = """\
# This is a comment
tap "homebrew/core"

# Another comment
brew "wget"

"""
    parsed = BrewfileParser.parse(content)

    assert len(parsed.taps) == 1
    assert len(parsed.brews) == 1
    assert not parsed.unsupported
