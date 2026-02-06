from pathlib import Path

import pytest

from brewfile_converter.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_cli_strict_failure_exit_code(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    fixture = ROOT / "tests" / "fixtures" / "brewfiles" / "strict_failure.Brewfile"
    monkeypatch.setattr("sys.argv", ["brewfile-to-ansible", str(fixture), "--strict"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Strict mode failed" in captured.err


def test_cli_non_strict_emits_warning_and_playbook(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fixture = ROOT / "tests" / "fixtures" / "brewfiles" / "strict_failure.Brewfile"
    monkeypatch.setattr("sys.argv", ["brewfile-to-ansible", str(fixture)])

    main()

    captured = capsys.readouterr()
    assert "Warning:" in captured.err
    assert "Install Homebrew packages and applications" in captured.out


def test_cli_output_file_flag(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fixture = ROOT / "tests" / "fixtures" / "brewfiles" / "complex.Brewfile"
    output = tmp_path / "playbook.yml"

    monkeypatch.setattr("sys.argv", ["brewfile-to-ansible", str(fixture), "-o", str(output)])
    main()

    assert output.exists()
    content = output.read_text()
    assert "Install Homebrew packages and applications" in content

    captured = capsys.readouterr()
    assert captured.out == ""


def test_cli_custom_template_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    template_dir = tmp_path / "custom_templates"
    template_dir.mkdir()
    custom_template = template_dir / "ansible_playbook.yml.j2"
    custom_template.write_text("---\n# Custom template\n# taps: {{ taps | length }}\n")

    fixture = ROOT / "tests" / "fixtures" / "brewfiles" / "complex.Brewfile"
    monkeypatch.setattr("sys.argv", ["brewfile-to-ansible", str(fixture), "-t", str(template_dir)])
    main()

    captured = capsys.readouterr()
    assert "Custom template" in captured.out


def test_cli_dry_run(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    fixture = ROOT / "tests" / "fixtures" / "brewfiles" / "complex.Brewfile"
    monkeypatch.setattr("sys.argv", ["brewfile-to-ansible", str(fixture), "--dry-run"])

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "Taps:" in captured.out
    assert "Formulae:" in captured.out
    assert "community.general" not in captured.out


def test_cli_dry_run_strict_with_issues(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    fixture = ROOT / "tests" / "fixtures" / "brewfiles" / "strict_failure.Brewfile"
    monkeypatch.setattr("sys.argv", ["brewfile-to-ansible", str(fixture), "--dry-run", "--strict"])

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
