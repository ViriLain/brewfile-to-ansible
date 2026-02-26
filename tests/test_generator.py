import yaml
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


def test_install_options_renders_valid_yaml(tmp_path: Path) -> None:
    brewfile = tmp_path / "Brewfile"
    brewfile.write_text('brew "git", args: ["--with-openssl", "--HEAD"]\n')

    result = process_brewfile(brewfile)
    # Must parse as valid YAML without error
    docs = list(yaml.safe_load_all(result.playbook))
    assert docs  # not empty

    # install_options must be a list, not a string like "['--with-openssl', '--HEAD']"
    tasks = docs[0][0]["tasks"]
    brew_task = next(t for t in tasks if "community.general.homebrew" in t)
    loop = brew_task["loop"]
    item = next(i for i in loop if i["name"] == "git")
    assert isinstance(item["install_options"], list)
    assert "--with-openssl" in item["install_options"]
