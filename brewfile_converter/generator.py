"""Jinja2-based Ansible playbook renderer for parsed Brewfile content."""

import json
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader, TemplateError

from .models import BrewfileContent


class AnsiblePlaybookGenerator:
    """Render a :class:`BrewfileContent` into an Ansible playbook via Jinja2 templates."""

    def __init__(self, template_dir: Optional[Path] = None) -> None:
        self.template_dir = (
            Path(template_dir)
            if template_dir
            else Path(__file__).resolve().parent / "templates"
        )
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))

    @staticmethod
    def _install_options(options: dict[str, Any]) -> Optional[list[str]]:
        raw = options.get("args")
        if raw is None:
            raw = options.get("install_options")

        if raw is None:
            return None
        if isinstance(raw, list):
            return [str(item) for item in raw]
        return [str(raw)]

    @staticmethod
    def _options_summary(options: dict[str, Any], consumed: Optional[list[str]] = None) -> str:
        consumed = consumed or []
        visible = {k: v for k, v in options.items() if k not in consumed and not k.startswith("_")}
        if not visible:
            return ""
        pairs = [f"{k}={v!r}" for k, v in sorted(visible.items())]
        return "; ".join(pairs)

    @staticmethod
    def _yaml_quote(value: str) -> str:
        result: str = json.dumps(value)
        return result

    def generate(self, brewfile: BrewfileContent, output_file: Optional[Path] = None) -> str:
        """Render *brewfile* to an Ansible playbook string, optionally writing it to *output_file*."""
        taps = [
            {
                "name": tap.name,
                "clone_target": tap.clone_target,
                "_brewfile_options": self._options_summary(tap.options),
            }
            for tap in brewfile.taps
        ]

        brews = [
            {
                "name": brew.name,
                "install_options": self._install_options(brew.options),
                "_brewfile_options": self._options_summary(
                    brew.options,
                    consumed=["args", "install_options"],
                ),
            }
            for brew in brewfile.brews
        ]

        casks = [
            {
                "name": cask.name,
                "install_options": self._install_options(cask.options),
                "_brewfile_options": self._options_summary(
                    cask.options,
                    consumed=["args", "install_options"],
                ),
            }
            for cask in brewfile.casks
        ]

        mas_apps = [
            {
                "name": app.name,
                "id": app.app_id,
                "_brewfile_options": self._options_summary(app.options),
            }
            for app in brewfile.mas_apps
        ]

        whalebrews = [
            {
                "name": item.name,
                "_brewfile_options": self._options_summary(item.options),
            }
            for item in brewfile.whalebrews
        ]

        try:
            template = self.env.get_template("ansible_playbook.yml.j2")
            playbook: str = template.render(
                taps=taps,
                brews=brews,
                casks=casks,
                vscode=brewfile.vscode,
                mas_apps=mas_apps,
                whalebrews=whalebrews,
            )
        except TemplateError as exc:
            raise RuntimeError(f"Failed to render playbook template: {exc}") from exc

        if output_file:
            output_file.write_text(playbook)

        return playbook
