from pathlib import Path

from brewfile_converter import BrewfileParser


def test_complex_fixture_parses_expected_shapes() -> None:
    fixture = Path(__file__).parent / "fixtures" / "brewfiles" / "complex.Brewfile"
    parsed = BrewfileParser.parse(fixture.read_text())

    assert [tap.name for tap in parsed.taps] == ["homebrew/core", "owner/tools"]
    assert parsed.taps[1].clone_target == "https://github.com/owner/homebrew-tools"

    assert [brew.name for brew in parsed.brews] == ["wget", "fd"]
    assert parsed.brews[0].options["args"] == ["HEAD"]
    assert parsed.brews[1].options["link"] is False

    assert [cask.name for cask in parsed.casks] == ["visual-studio-code", "iterm2"]
    assert parsed.casks[0].options["appdir"] == "/Applications"
    assert parsed.casks[1].options["args"] == ["no-quarantine"]

    assert parsed.vscode == ["ms-python.python"]
    assert parsed.mas_apps[0].name == "Xcode"
    assert parsed.mas_apps[0].app_id == 497799835

    assert parsed.whalebrews[0].name == "ghcr.io/owner/tool:latest"
    assert any("Unsupported Brewfile directive: go" in issue.message for issue in parsed.unsupported)


def test_comment_stripping_keeps_hashes_in_strings() -> None:
    content = 'brew "ripgrep#stable" # comment to ignore\n'
    parsed = BrewfileParser.parse(content)

    assert len(parsed.brews) == 1
    assert parsed.brews[0].name == "ripgrep#stable"
