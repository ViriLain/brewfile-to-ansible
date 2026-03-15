"""Data models for parsed Brewfile content and conversion results."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ParseIssue:
    """A warning or error encountered while parsing a single Brewfile line."""

    line_no: int
    line: str
    message: str


@dataclass
class BrewItem:
    """A Homebrew formula, cask, or whalebrew entry with optional install options."""

    name: str
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class TapItem:
    """A Homebrew tap, optionally pointing at a custom clone URL."""

    name: str
    clone_target: Optional[str] = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class MasItem:
    """A Mac App Store entry identified by name and numeric app ID."""

    name: str
    app_id: Optional[int] = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrewfileContent:
    """Aggregated result of parsing a Brewfile, grouped by directive type."""

    taps: list[TapItem] = field(default_factory=list)
    brews: list[BrewItem] = field(default_factory=list)
    casks: list[BrewItem] = field(default_factory=list)
    vscode: list[str] = field(default_factory=list)
    mas_apps: list[MasItem] = field(default_factory=list)
    whalebrews: list[BrewItem] = field(default_factory=list)
    cask_args: dict[str, Any] = field(default_factory=dict)
    unsupported: list[ParseIssue] = field(default_factory=list)


@dataclass
class ConversionOutput:
    """Final output of a Brewfile-to-Ansible conversion: the rendered playbook and any issues."""

    playbook: str
    issues: list[ParseIssue]
