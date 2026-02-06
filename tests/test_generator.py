from pathlib import Path

from brewfile_converter import process_brewfile


def test_generation_includes_extended_sections(tmp_path: Path) -> None:
    brewfile = tmp_path / "Brewfile"
    brewfile.write_text(
        '\n'.join(
            [
                'tap "homebrew/core"',
                'brew "wget", args: ["HEAD"]',
                'cask "visual-studio-code"',
                'mas "Xcode", id: 497799835',
                'vscode "ms-python.python"',
                'whalebrew "ghcr.io/owner/tool:latest"',
            ]
        )
    )

    result = process_brewfile(brewfile)

    assert "community.general.homebrew_tap" in result.playbook
    assert "community.general.homebrew:" in result.playbook
    assert "community.general.homebrew_cask" in result.playbook
    assert "community.general.mas" in result.playbook
    assert "whalebrew install" in result.playbook
    assert "code --list-extensions" in result.playbook
    assert "install_options" in result.playbook
