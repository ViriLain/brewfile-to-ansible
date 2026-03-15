"""Public API surface for the brewfile_converter package.

Re-exports the parser, generator, CLI entry points, normalization helpers,
and utility functions so consumers can ``import brewfile_converter`` directly.
"""

from .cli import main, process_brewfile
from .generator import AnsiblePlaybookGenerator
from .models import (
    BrewfileContent,
    BrewItem,
    ConversionOutput,
    MasItem,
    ParseIssue,
    TapItem,
)
from .normalize import brew_bundle_list, normalize_with_brew_bundle
from .parser import BrewfileParser
from .utils import (
    extract_first_argument,
    normalize_key,
    parse_options_and_positional,
    parse_rubyish_value,
    sanitize_options,
    split_key_value,
    split_top_level,
    strip_inline_comment,
    unquote,
)

__all__ = [
    "AnsiblePlaybookGenerator",
    "BrewItem",
    "BrewfileContent",
    "BrewfileParser",
    "ConversionOutput",
    "MasItem",
    "ParseIssue",
    "TapItem",
    "brew_bundle_list",
    "extract_first_argument",
    "main",
    "normalize_key",
    "normalize_with_brew_bundle",
    "parse_options_and_positional",
    "parse_rubyish_value",
    "process_brewfile",
    "sanitize_options",
    "split_key_value",
    "split_top_level",
    "strip_inline_comment",
    "unquote",
]
