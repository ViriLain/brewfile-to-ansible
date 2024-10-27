import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader


@dataclass
class BrewfileContent:
    taps: List[str] = field(default_factory=list)
    brews: List[str] = field(default_factory=list)
    casks: List[str] = field(default_factory=list)
    vscode: List[str] = field(default_factory=list)


class BrewfileParser:
    @staticmethod
    def parse(content: str) -> BrewfileContent:
        brewfile = BrewfileContent()

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith('tap'):
                tap = re.match(r'tap\s+"([^"]+)"', line)
                if tap:
                    brewfile.taps.append(tap.group(1))
            elif line.startswith('brew'):
                brew = re.match(r'brew\s+"([^"]+)"', line)
                if brew:
                    brewfile.brews.append(brew.group(1))
            elif line.startswith('cask'):
                cask = re.match(r'cask\s+"([^"]+)"', line)
                if cask:
                    brewfile.casks.append(cask.group(1))
            elif line.startswith('vscode'):
                vscode = re.match(r'vscode\s+"([^"]+)"', line)
                if vscode:
                    brewfile.vscode.append(vscode.group(1))

        return brewfile


class AnsiblePlaybookGenerator:
    def __init__(self, template_dir: str = "templates"):
        try:
            self.env = Environment(loader=FileSystemLoader(template_dir))
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Jinja environment: {e}")

    def generate(self, brewfile: BrewfileContent, output_file: Optional[Path] = None) -> str:
        try:
            template = self.env.get_template("ansible_playbook.yml.j2")
            playbook = template.render(
                taps=brewfile.taps,
                brews=brewfile.brews,
                casks=brewfile.casks,
                vscode=brewfile.vscode
            )

            if output_file:
                output_file.write_text(playbook)

            return playbook
        except Exception as e:
            raise RuntimeError(f"Failed to generate playbook: {e}")


def process_brewfile(brewfile_path: Path, output_path: Optional[Path] = None,
                     template_dir: str = "templates") -> str:
    """
    Process a Brewfile and return the generated Ansible playbook.

    Args:
        brewfile_path: Path to the Brewfile
        output_path: Optional path to write the output
        template_dir: Directory containing Jinja templates

    Returns:
        str: Generated Ansible playbook content
    """
    try:
        # Read Brewfile
        content = brewfile_path.read_text()
    except Exception as e:
        raise RuntimeError(f"Failed to read Brewfile at {brewfile_path}: {e}")

    # Parse Brewfile
    parser = BrewfileParser()
    brewfile_content = parser.parse(content)

    # Generate Ansible playbook
    generator = AnsiblePlaybookGenerator(template_dir)
    return generator.generate(brewfile_content, output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Convert Brewfile to Ansible playbook",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert Brewfile and print to stdout
  %(prog)s Brewfile

  # Convert Brewfile and save to playbook.yml
  %(prog)s Brewfile -o playbook.yml

  # Use custom template directory
  %(prog)s Brewfile -o playbook.yml -t /path/to/templates
"""
    )

    parser.add_argument(
        "brewfile",
        type=Path,
        help="Path to Brewfile"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output path for Ansible playbook (defaults to stdout)",
    )
    parser.add_argument(
        "-t", "--template-dir",
        type=str,
        default="templates",
        help="Directory containing Jinja templates (default: ./templates)"
    )

    args = parser.parse_args()

    try:
        playbook = process_brewfile(args.brewfile, args.output, args.template_dir)
        if not args.output:
            print(playbook)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()