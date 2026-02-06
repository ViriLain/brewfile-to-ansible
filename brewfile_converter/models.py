from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ParseIssue:
    line_no: int
    line: str
    message: str


@dataclass
class BrewItem:
    name: str
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class TapItem:
    name: str
    clone_target: Optional[str] = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class MasItem:
    name: str
    app_id: Optional[int] = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrewfileContent:
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
    playbook: str
    issues: list[ParseIssue]
