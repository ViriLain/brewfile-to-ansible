# CLAUDE.md

## Project Overview

**brewfile-to-ansible** converts Homebrew `Brewfile` files (Ruby DSL) into Ansible playbooks (YAML). It parses taps, formulae, casks, MAS apps, VS Code extensions, and whalebrew entries and renders them using Jinja2 templates into playbooks that use `community.general` Ansible modules.

## Tech Stack

- Python 3.9+
- Jinja2 for template rendering
- pytest for testing
- ruff for linting
- mypy for type checking
- setuptools (PEP 517/518) build system

## Project Structure

```
brewfile_converter/              # Main package
  __init__.py                    # Public API re-exports
  __main__.py                    # python -m brewfile_converter support
  models.py                      # Dataclasses: ParseIssue, BrewItem, TapItem, MasItem, BrewfileContent, ConversionOutput
  utils.py                       # Text scanning, quoting, Ruby value parsing helpers
  parser.py                      # BrewfileParser
  generator.py                   # AnsiblePlaybookGenerator (Jinja2 rendering)
  normalize.py                   # brew_bundle_list, normalize_with_brew_bundle
  cli.py                         # process_brewfile, main (CLI entry point)
  templates/
    ansible_playbook.yml.j2      # Jinja2 template for playbook output
tests/
  test_utils.py                  # Unit tests for utility functions
  test_parser.py                 # Parser unit tests
  test_generator.py              # Generator unit tests
  test_cli.py                    # CLI tests (calls main() directly)
  test_parser_variants.py        # Complex parsing scenarios
  test_normalization.py          # Brew bundle normalization tests
  fixtures/brewfiles/            # Test Brewfile fixtures
pyproject.toml                   # Project config, deps, tool configs (ruff, mypy, pytest)
```

## Common Commands

```bash
# Install in editable mode with dev deps
pip install -e .[dev]

# Run the converter
brewfile-to-ansible Brewfile -o playbook.yml

# Run tests
pytest
pytest -v  # verbose

# Lint
ruff check brewfile_converter/ tests/

# Type check
mypy brewfile_converter/
```

## CLI Usage

```
brewfile-to-ansible <brewfile> [-o OUTPUT] [-t TEMPLATE_DIR] [--strict] [--normalize-with-brew] [--dry-run]
```

- `--strict`: Fail on unsupported directives or malformed lines
- `--normalize-with-brew`: Use `brew bundle list` to normalize entries first (runs 5 calls in parallel)
- `-t`: Custom Jinja2 template directory
- `--dry-run` / `--validate`: Parse and report issues without generating a playbook

## Code Conventions

- **Dataclasses with type hints** throughout (defined in `models.py`)
- **Static parser class** (`BrewfileParser.parse()`) as single entry point for parsing
- **Generator class** (`AnsiblePlaybookGenerator`) handles Jinja2 rendering
- **`_ScanState` helper** in `utils.py` deduplicates quote/escape/bracket-depth tracking across text scanning functions
- Unsupported Brewfile options are preserved in `_brewfile_options` metadata (no silent data loss)
- Errors collected as `ParseIssue` list; strict mode raises `RuntimeError` with all issues
- CLI catches exceptions, writes to stderr, exits with code 1

## Supported Brewfile Directives

`tap`, `brew`, `cask`, `cask_args`, `vscode`, `mas`, `whalebrew`

## Testing

Tests live in `tests/` and use pytest. Fixtures are in `tests/fixtures/brewfiles/`. Run `pytest` from the project root. The pytest config is in `pyproject.toml` with `-q` as the default addopt.
