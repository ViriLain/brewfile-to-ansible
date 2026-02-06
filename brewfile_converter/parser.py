import re
from typing import Optional

from .models import BrewfileContent, BrewItem, MasItem, ParseIssue, TapItem
from .utils import (
    extract_first_argument,
    parse_options_and_positional,
    sanitize_options,
    strip_inline_comment,
)


class BrewfileParser:
    SUPPORTED_DIRECTIVES = {"tap", "brew", "cask", "vscode", "mas", "whalebrew", "cask_args"}

    @staticmethod
    def parse(content: str) -> BrewfileContent:
        brewfile = BrewfileContent()

        for line_no, raw_line in enumerate(content.splitlines(), start=1):
            stripped = strip_inline_comment(raw_line).strip()
            if not stripped:
                continue

            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(.*)$", stripped)
            if not match:
                brewfile.unsupported.append(
                    ParseIssue(line_no=line_no, line=raw_line, message="Could not parse line format")
                )
                continue

            directive = match.group(1).lower()
            rest = match.group(2).strip()

            if directive not in BrewfileParser.SUPPORTED_DIRECTIVES:
                brewfile.unsupported.append(
                    ParseIssue(
                        line_no=line_no,
                        line=raw_line,
                        message=f"Unsupported Brewfile directive: {directive}",
                    )
                )
                continue

            if directive == "cask_args":
                options, positional = parse_options_and_positional(rest)
                if positional:
                    brewfile.unsupported.append(
                        ParseIssue(
                            line_no=line_no,
                            line=raw_line,
                            message="cask_args positional arguments were ignored",
                        )
                    )
                brewfile.cask_args.update(options)
                continue

            name, remainder = extract_first_argument(rest)
            if not name:
                brewfile.unsupported.append(
                    ParseIssue(
                        line_no=line_no,
                        line=raw_line,
                        message=f"{directive} entry has no package/application name",
                    )
                )
                continue

            remainder = remainder.strip()
            if remainder.startswith(","):
                remainder = remainder[1:].strip()
            options, positional = parse_options_and_positional(remainder)

            if directive == "tap":
                clone_target = options.get("clone_target")
                if clone_target is None and positional:
                    first = positional[0]
                    clone_target = first if isinstance(first, str) else None
                tap_opts = sanitize_options(options, ignore_keys=["clone_target"])
                brewfile.taps.append(TapItem(name=name, clone_target=clone_target, options=tap_opts))
                continue

            if directive == "brew":
                brewfile.brews.append(BrewItem(name=name, options=options))
                continue

            if directive == "cask":
                cask_options = dict(brewfile.cask_args)
                cask_options.update(options)
                brewfile.casks.append(BrewItem(name=name, options=cask_options))
                continue

            if directive == "vscode":
                brewfile.vscode.append(name)
                continue

            if directive == "whalebrew":
                brewfile.whalebrews.append(BrewItem(name=name, options=options))
                continue

            if directive == "mas":
                app_id_raw = options.pop("id", None)
                if app_id_raw is None and positional:
                    app_id_raw = positional[0]

                app_id: Optional[int] = None
                if isinstance(app_id_raw, int):
                    app_id = app_id_raw
                elif isinstance(app_id_raw, str) and app_id_raw.isdigit():
                    app_id = int(app_id_raw)

                if app_id is None:
                    brewfile.unsupported.append(
                        ParseIssue(
                            line_no=line_no,
                            line=raw_line,
                            message="mas entry missing numeric id",
                        )
                    )

                brewfile.mas_apps.append(MasItem(name=name, app_id=app_id, options=options))

        return brewfile
