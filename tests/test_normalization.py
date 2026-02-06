import subprocess
from pathlib import Path

import pytest

from brewfile_converter import brew_bundle_list, process_brewfile


def test_normalization_warns_for_whalebrew_entries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    brewfile = tmp_path / "Brewfile"
    brewfile.write_text('whalebrew "ghcr.io/owner/tool:latest"\n')

    fake_lists = {
        "--tap": [],
        "--formula": [],
        "--cask": [],
        "--vscode": [],
        "--mas": [],
    }

    monkeypatch.setattr("brewfile_converter.normalize.brew_bundle_list", lambda _path, flag: fake_lists[flag])

    result = process_brewfile(brewfile, normalize_with_brew=True)
    assert "whalebrew install" in result.playbook
    assert any("not normalized by brew bundle list" in issue.message for issue in result.issues)


def test_brew_bundle_list_surfaces_missing_brew(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    brewfile = tmp_path / "Brewfile"
    brewfile.write_text('brew "wget"\n')

    def raise_missing(*_args: object, **_kwargs: object) -> None:
        raise FileNotFoundError("brew not found")

    monkeypatch.setattr(subprocess, "run", raise_missing)

    with pytest.raises(RuntimeError, match="brew command not found"):
        brew_bundle_list(brewfile, "--formula")
