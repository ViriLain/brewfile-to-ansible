# comments and hashes in strings should be safe
cask_args appdir: "/Applications", require_sha: true

tap "homebrew/core"
tap 'owner/tools', clone_target: 'https://github.com/owner/homebrew-tools'

brew "wget", args: ["HEAD"], restart_service: true
brew 'fd', link: false

cask "visual-studio-code"
cask 'iterm2', args: ["no-quarantine"]

vscode "ms-python.python"
mas "Xcode", 497799835
whalebrew "ghcr.io/owner/tool:latest"

# unsupported on purpose
go "golang.org/x/tools/gopls"
