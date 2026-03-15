from pathlib import Path

import yaml

from brewfile_converter import process_brewfile


def test_generation_includes_extended_sections(tmp_path: Path) -> None:
    brewfile = tmp_path / "Brewfile"
    brewfile.write_text(
        "\n".join(
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
    brew_task = next(
        t
        for t in tasks
        if "community.general.homebrew" in t
        and "community.general.homebrew_tap" not in t
        and "community.general.homebrew_cask" not in t
    )
    loop = brew_task["loop"]
    item = next(i for i in loop if i["name"] == "git")
    assert isinstance(item["install_options"], list)
    assert "--with-openssl" in item["install_options"]


def test_playbook_sets_gather_facts_false(tmp_path: Path) -> None:
    brewfile = tmp_path / "Brewfile"
    brewfile.write_text('brew "wget"\n')

    result = process_brewfile(brewfile)
    docs = list(yaml.safe_load_all(result.playbook))
    play = docs[0][0]
    assert play.get("gather_facts") is False


def test_generated_playbook_is_valid_yaml(tmp_path: Path) -> None:
    """Generated playbook must always be parseable YAML — no Python repr leakage."""
    brewfile = tmp_path / "Brewfile"
    brewfile.write_text(
        "\n".join(
            [
                'tap "homebrew/cask-fonts"',
                'brew "git", args: ["--with-openssl"]',
                'brew "python@3.12", link: false, restart_service: true',
                'cask_args appdir: "/Applications"',
                'cask "font-fira-code"',
                'cask "iterm2"',
            ]
        )
    )

    result = process_brewfile(brewfile)
    # Must not raise
    docs = list(yaml.safe_load_all(result.playbook))
    assert docs
    assert isinstance(docs[0], list)  # list of plays


def test_unsupported_brew_options_appear_in_brewfile_options_comment(tmp_path: Path) -> None:
    brewfile = tmp_path / "Brewfile"
    brewfile.write_text('brew "wget", restart_service: true, link: false\n')

    result = process_brewfile(brewfile)

    # restart_service and link are not Ansible module params — must appear as metadata
    assert "restart_service" in result.playbook
    assert "link" in result.playbook
    assert "_brewfile_options" in result.playbook


def test_unsupported_cask_options_appear_in_brewfile_options_comment(tmp_path: Path) -> None:
    brewfile = tmp_path / "Brewfile"
    brewfile.write_text('cask "iterm2", quit_application: true\n')

    result = process_brewfile(brewfile)
    assert "quit_application" in result.playbook
    assert "_brewfile_options" in result.playbook


def test_playbook_renders_with_taps_only(tmp_path: Path) -> None:
    brewfile = tmp_path / "Brewfile"
    brewfile.write_text('tap "homebrew/core"\n')

    result = process_brewfile(brewfile)
    docs = list(yaml.safe_load_all(result.playbook))
    assert docs
    tasks = docs[0][0]["tasks"]
    assert len(tasks) == 1
    assert "community.general.homebrew_tap" in tasks[0]


def test_playbook_renders_with_casks_only(tmp_path: Path) -> None:
    brewfile = tmp_path / "Brewfile"
    brewfile.write_text('cask "iterm2"\n')

    result = process_brewfile(brewfile)
    docs = list(yaml.safe_load_all(result.playbook))
    assert docs
    tasks = docs[0][0]["tasks"]
    assert len(tasks) == 1
    assert "community.general.homebrew_cask" in tasks[0]


def test_playbook_renders_with_brews_only(tmp_path: Path) -> None:
    brewfile = tmp_path / "Brewfile"
    brewfile.write_text('brew "wget"\n')

    result = process_brewfile(brewfile)
    docs = list(yaml.safe_load_all(result.playbook))
    assert docs
    tasks = docs[0][0]["tasks"]
    assert len(tasks) == 1
    assert "community.general.homebrew" in tasks[0]
    assert "community.general.homebrew_tap" not in tasks[0]
    assert "community.general.homebrew_cask" not in tasks[0]
