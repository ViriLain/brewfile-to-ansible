# Brewfile to Ansible Converter

Convert a Homebrew `Brewfile` into an Ansible playbook.

The converter now supports common Brewfile directives and option styles, including quoted and unquoted values, inline option hashes, arrays, comments, and strict-mode validation.

## Features

- Parses directives:
  - `tap`
  - `brew`
  - `cask`
  - `cask_args` (applied to following `cask` entries)
  - `vscode`
  - `mas`
  - `whalebrew`
- Supports both single and double quotes.
- Parses Ruby-style values:
  - booleans (`true` / `false`)
  - integers
  - arrays (`[...]`)
  - inline hashes (`{...}`)
  - symbols (`:something`)
- Preserves unsupported options in generated loop metadata (`_brewfile_options`) to avoid silent data loss.
- Emits warnings for unsupported directives or malformed lines.
- Supports `--strict` mode to fail conversion when unsupported lines are encountered.
- Supports `--normalize-with-brew` mode to normalize entries via `brew bundle list`.

## Installation

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Usage

Convert and print to stdout:

```bash
brewfile-to-ansible Brewfile
```

Convert and write to a file:

```bash
brewfile-to-ansible Brewfile -o playbook.yml
```

Fail if the parser encounters unsupported lines:

```bash
brewfile-to-ansible Brewfile --strict
```

Normalize entries using Homebrew Bundle's parser before conversion:

```bash
brewfile-to-ansible Brewfile --normalize-with-brew
```

Use a custom template directory:

```bash
brewfile-to-ansible Brewfile -t ./templates -o playbook.yml
```

## Generated playbook behavior

- Uses Homebrew modules where available:
  - `community.general.homebrew_tap`
  - `community.general.homebrew`
  - `community.general.homebrew_cask`
  - `community.general.mas`
- Installs VS Code extensions only when missing by checking `code --list-extensions` first.
- Installs whalebrew images only when missing by checking `whalebrew list` first.

## Support matrix and caveats

- The parser aims to be permissive for many Brewfile formats, but Brewfile is Ruby DSL and can contain arbitrary Ruby.
- Fully dynamic Ruby constructs (conditionals, loops, variables, method calls) are not evaluated.
- Unsupported directives are reported as warnings and can fail conversion under `--strict`.
- Some directive options may not map directly to Ansible module parameters; those options are preserved in metadata for manual follow-up.
- `--normalize-with-brew` requires `brew` and may drop some option-level details that `brew bundle list` does not emit (for example, `mas` app IDs for some entries); these are reported as warnings.

## Development

Run tests:

```bash
pytest
```

## Brewfile reference

- [Homebrew Bundle documentation](https://github.com/Homebrew/homebrew-bundle)
