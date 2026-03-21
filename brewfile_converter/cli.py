import argparse
import sys
from pathlib import Path
from typing import Optional

from .generator import AnsiblePlaybookGenerator
from .models import ConversionOutput, ParseIssue
from .normalize import normalize_with_brew_bundle
from .parser import BrewfileParser


def process_brewfile(
    brewfile_path: Path,
    output_path: Optional[Path] = None,
    template_dir: Optional[Path] = None,
    strict: bool = False,
    normalize_with_brew: bool = False,
) -> ConversionOutput:
    try:
        content = brewfile_path.read_text()
    except Exception as exc:
        raise RuntimeError(f"Failed to read Brewfile at {brewfile_path}: {exc}") from exc

    brewfile_content = BrewfileParser.parse(content)
    if normalize_with_brew:
        brewfile_content = normalize_with_brew_bundle(brewfile_path, brewfile_content)

    has_supported_entries = any(
        [
            brewfile_content.taps,
            brewfile_content.brews,
            brewfile_content.casks,
            brewfile_content.vscode,
            brewfile_content.mas_apps,
            brewfile_content.whalebrews,
        ]
    )
    if not has_supported_entries:
        brewfile_content.unsupported.append(
            ParseIssue(
                line_no=0,
                line="",
                message="No supported Brewfile entries were detected",
            )
        )

    if strict and brewfile_content.unsupported:
        details = "\n".join(
            f"line {issue.line_no}: {issue.message} -> {issue.line.strip()}" for issue in brewfile_content.unsupported
        )
        raise RuntimeError(f"Strict mode failed due to unsupported lines:\n{details}")

    generator = AnsiblePlaybookGenerator(template_dir)
    playbook = generator.generate(brewfile_content, output_path)

    return ConversionOutput(playbook=playbook, issues=brewfile_content.unsupported)


def _print_issues(issues: list[ParseIssue]) -> None:
    for issue in issues:
        location = f"line {issue.line_no}" if issue.line_no > 0 else "input"
        detail = f" [{issue.line.strip()}]" if issue.line.strip() else ""
        print(f"Warning: {location}: {issue.message}{detail}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Brewfile to Ansible playbook",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert Brewfile and print to stdout
  %(prog)s Brewfile

  # Convert Brewfile and save to playbook.yml
  %(prog)s Brewfile -o playbook.yml

  # Fail when unsupported directives/lines are encountered
  %(prog)s Brewfile --strict

  # Normalize directives via brew bundle parser before conversion
  %(prog)s Brewfile --normalize-with-brew

  # Use custom template directory
  %(prog)s Brewfile -o playbook.yml -t /path/to/templates

  # Validate a Brewfile without generating output
  %(prog)s Brewfile --dry-run
""",
    )

    parser.add_argument("brewfile", type=Path, help="Path to Brewfile")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output path for Ansible playbook (defaults to stdout)",
    )
    parser.add_argument(
        "-t",
        "--template-dir",
        type=Path,
        default=None,
        help="Directory containing Jinja templates (default: script-local templates)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if unsupported directives or malformed lines are present",
    )
    parser.add_argument(
        "--normalize-with-brew",
        action="store_true",
        help=("Use `brew bundle list` to normalize taps/formulae/casks/vscode/mas entries. Requires Homebrew."),
    )
    parser.add_argument(
        "--dry-run",
        "--validate",
        action="store_true",
        dest="dry_run",
        help="Parse the Brewfile and report issues without generating a playbook",
    )

    args = parser.parse_args()

    try:
        if args.dry_run:
            content = args.brewfile.read_text()
            brewfile_content = BrewfileParser.parse(content)
            if args.normalize_with_brew:
                brewfile_content = normalize_with_brew_bundle(args.brewfile, brewfile_content)

            print(f"Taps: {len(brewfile_content.taps)}")
            print(f"Formulae: {len(brewfile_content.brews)}")
            print(f"Casks: {len(brewfile_content.casks)}")
            print(f"VS Code extensions: {len(brewfile_content.vscode)}")
            print(f"Mac App Store apps: {len(brewfile_content.mas_apps)}")
            print(f"Whalebrew images: {len(brewfile_content.whalebrews)}")

            if brewfile_content.unsupported:
                print(f"\nIssues ({len(brewfile_content.unsupported)}):", file=sys.stderr)
                _print_issues(brewfile_content.unsupported)

            if args.strict and brewfile_content.unsupported:
                sys.exit(1)
            sys.exit(0)

        result = process_brewfile(
            brewfile_path=args.brewfile,
            output_path=args.output,
            template_dir=args.template_dir,
            strict=args.strict,
            normalize_with_brew=args.normalize_with_brew,
        )

        _print_issues(result.issues)

        if not args.output:
            print(result.playbook)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
