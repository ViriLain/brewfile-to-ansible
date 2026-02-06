import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .models import BrewfileContent, BrewItem, MasItem, ParseIssue, TapItem


def brew_bundle_list(brewfile_path: Path, bundle_flag: str) -> list[str]:
    env = os.environ.copy()
    env.setdefault("HOMEBREW_NO_AUTO_UPDATE", "1")
    env.setdefault("HOMEBREW_NO_INSTALL_CLEANUP", "1")

    cmd = ["brew", "bundle", "list", bundle_flag, "--file", str(brewfile_path)]
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("brew command not found; install Homebrew to use --normalize-with-brew") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to run {' '.join(cmd)}: {exc}") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(
            f"brew bundle list failed for {bundle_flag} with exit code {result.returncode}: {stderr or 'no stderr'}"
        )

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def normalize_with_brew_bundle(brewfile_path: Path, brewfile: BrewfileContent) -> BrewfileContent:
    normalized = BrewfileContent(
        taps=list(brewfile.taps),
        brews=list(brewfile.brews),
        casks=list(brewfile.casks),
        vscode=list(brewfile.vscode),
        mas_apps=list(brewfile.mas_apps),
        whalebrews=list(brewfile.whalebrews),
        cask_args=dict(brewfile.cask_args),
        unsupported=list(brewfile.unsupported),
    )

    tap_by_name = {item.name: item for item in brewfile.taps}
    brew_by_name = {item.name: item for item in brewfile.brews}
    cask_by_name = {item.name: item for item in brewfile.casks}
    mas_by_name = {item.name: item for item in brewfile.mas_apps}

    flags = ["--tap", "--formula", "--cask", "--vscode", "--mas"]
    results: dict[str, list[str]] = {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_flag = {
            executor.submit(brew_bundle_list, brewfile_path, flag): flag
            for flag in flags
        }
        for future in as_completed(future_to_flag):
            flag = future_to_flag[future]
            results[flag] = future.result()

    tap_names = results["--tap"]
    brew_names = results["--formula"]
    cask_names = results["--cask"]
    vscode_names = results["--vscode"]
    mas_names = results["--mas"]

    normalized.taps = [
        tap_by_name.get(name, TapItem(name=name))
        for name in tap_names
    ]
    normalized.brews = [
        brew_by_name.get(name, BrewItem(name=name))
        for name in brew_names
    ]
    normalized.casks = [
        cask_by_name.get(name, BrewItem(name=name))
        for name in cask_names
    ]
    normalized.vscode = vscode_names

    normalized.mas_apps = []
    for name in mas_names:
        existing = mas_by_name.get(name)
        if existing is not None:
            normalized.mas_apps.append(existing)
            continue

        normalized.mas_apps.append(MasItem(name=name, app_id=None))
        normalized.unsupported.append(
            ParseIssue(
                line_no=0,
                line=name,
                message="mas app id unavailable after brew normalization; add id manually",
            )
        )

    if brewfile.whalebrews:
        normalized.unsupported.append(
            ParseIssue(
                line_no=0,
                line="",
                message="whalebrew entries are not normalized by brew bundle list and were parsed directly",
            )
        )

    return normalized
