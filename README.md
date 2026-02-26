# brewfile-to-ansible

Converts a Homebrew `Brewfile` into an Ansible playbook using `community.general` modules.

## Prerequisites

- Python 3.9+
- [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/index.html) with the `community.general` collection:

  ```bash
  ansible-galaxy collection install community.general
  ```

## Installation

```bash
git clone https://github.com/you/brewfile-to-ansible.git
cd brewfile-to-ansible
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
# Print playbook to stdout
brewfile-to-ansible Brewfile

# Write playbook to a file
brewfile-to-ansible Brewfile -o playbook.yml

# Fail on any unsupported or malformed lines
brewfile-to-ansible Brewfile --strict

# Parse and report issues without generating output
brewfile-to-ansible Brewfile --dry-run

# Normalize entries via `brew bundle list` before converting
brewfile-to-ansible Brewfile --normalize-with-brew

# Use a custom Jinja2 template directory
brewfile-to-ansible Brewfile -t ./my-templates -o playbook.yml
```

## Running the generated playbook

```bash
ansible-playbook playbook.yml
```

The playbook targets `localhost`, runs as the current user (`become: false`), and assumes Homebrew is already installed.

## Supported directives

| Directive    | Support  | Notes                                                        |
|--------------|----------|--------------------------------------------------------------|
| `tap`        | Full     | Supports optional `clone_target` URL                         |
| `brew`       | Full     | `args`/`install_options` map to `install_options` parameter  |
| `cask`       | Full     | Inherits `cask_args` options                                 |
| `cask_args`  | Full     | Applied to all following `cask` entries                      |
| `mas`        | Limited  | Parsed but app IDs lost after `--normalize-with-brew`        |
| `vscode`     | Limited  | Shell-based install, not idempotent via a native module      |
| `whalebrew`  | Limited  | Parsed but not normalized by `brew bundle list`              |

## Known limitations

- **No Ruby DSL evaluation.** Brewfile is Ruby. Loops, conditionals, variables, and method calls are not evaluated — those lines are skipped and reported as warnings.
- **MAS app IDs.** `--normalize-with-brew` cannot recover App Store app IDs from `brew bundle list`. MAS entries are preserved from the original Brewfile but will be incomplete after normalization.
- **VS Code and Whalebrew.** These use shell commands in the generated playbook and are less reliable than the native Homebrew tasks.
- **`accept_external_apps` not set.** Some casks require this flag; the generated playbook does not set it. Pass it via `install_options` if needed.
- **Homebrew must already be installed.** The generated playbook does not install Homebrew itself.

## Development

```bash
pip install -e .[dev]
pytest          # run tests
ruff check .    # lint
mypy brewfile_converter/  # type check
```

## References

- [Homebrew Bundle](https://github.com/Homebrew/homebrew-bundle)
- [community.general.homebrew](https://docs.ansible.com/ansible/latest/collections/community/general/homebrew_module.html)
- [community.general.homebrew_tap](https://docs.ansible.com/ansible/latest/collections/community/general/homebrew_tap_module.html)
- [community.general.homebrew_cask](https://docs.ansible.com/ansible/latest/collections/community/general/homebrew_cask_module.html)
