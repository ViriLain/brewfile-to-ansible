from brewfile_converter.utils import (
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


class TestStripInlineComment:
    def test_no_comment(self) -> None:
        assert strip_inline_comment('brew "wget"') == 'brew "wget"'

    def test_simple_comment(self) -> None:
        result = strip_inline_comment('brew "wget" # install wget')
        assert result == 'brew "wget" '

    def test_hash_inside_double_quotes(self) -> None:
        assert strip_inline_comment('brew "foo#bar"') == 'brew "foo#bar"'

    def test_hash_inside_single_quotes(self) -> None:
        assert strip_inline_comment("brew 'foo#bar'") == "brew 'foo#bar'"

    def test_comment_after_quoted_hash(self) -> None:
        result = strip_inline_comment('brew "foo#bar" # comment')
        assert result == 'brew "foo#bar" '

    def test_empty_string(self) -> None:
        assert strip_inline_comment("") == ""

    def test_only_comment(self) -> None:
        assert strip_inline_comment("# just a comment") == ""

    def test_escaped_quote(self) -> None:
        result = strip_inline_comment(r'brew "foo\"bar" # comment')
        assert result == r'brew "foo\"bar" '


class TestSplitTopLevel:
    def test_simple_split(self) -> None:
        assert split_top_level("a, b, c") == ["a", "b", "c"]

    def test_quoted_comma(self) -> None:
        assert split_top_level('"a,b", c') == ['"a,b"', "c"]

    def test_bracketed_comma(self) -> None:
        assert split_top_level("[a, b], c") == ["[a, b]", "c"]

    def test_nested_brackets(self) -> None:
        assert split_top_level("{a: [1, 2]}, b") == ["{a: [1, 2]}", "b"]

    def test_empty_string(self) -> None:
        assert split_top_level("") == []

    def test_no_separator(self) -> None:
        assert split_top_level("abc") == ["abc"]

    def test_custom_separator(self) -> None:
        assert split_top_level("a;b;c", sep=";") == ["a", "b", "c"]

    def test_strips_whitespace(self) -> None:
        assert split_top_level("  a ,  b  ") == ["a", "b"]


class TestUnquote:
    def test_double_quoted(self) -> None:
        assert unquote('"hello"') == "hello"

    def test_single_quoted(self) -> None:
        assert unquote("'hello'") == "hello"

    def test_unquoted(self) -> None:
        assert unquote("hello") == "hello"

    def test_escaped_newline(self) -> None:
        assert unquote('"hello\\nworld"') == "hello\nworld"

    def test_escaped_tab(self) -> None:
        assert unquote('"hello\\tworld"') == "hello\tworld"

    def test_escaped_backslash(self) -> None:
        assert unquote('"hello\\\\world"') == "hello\\world"

    def test_escaped_quote(self) -> None:
        assert unquote('"hello\\"world"') == 'hello"world'

    def test_empty_quoted(self) -> None:
        assert unquote('""') == ""

    def test_whitespace_stripped(self) -> None:
        assert unquote('  "hello"  ') == "hello"

    def test_mismatched_quotes(self) -> None:
        assert unquote("\"hello'") == "\"hello'"

    def test_unknown_escape_preserved(self) -> None:
        assert unquote('"hello\\xworld"') == "hello\\xworld"

    def test_single_char(self) -> None:
        assert unquote("x") == "x"


class TestSplitKeyValue:
    def test_simple_kv(self) -> None:
        assert split_key_value("key: value") == ("key", "value")

    def test_quoted_value_with_colon(self) -> None:
        assert split_key_value('key: "http://example.com"') == ("key", '"http://example.com"')

    def test_no_colon(self) -> None:
        assert split_key_value("just_a_value") is None

    def test_nested_brackets(self) -> None:
        assert split_key_value("key: [a, b: c]") == ("key", "[a, b: c]")

    def test_empty_value(self) -> None:
        assert split_key_value("key:") is None

    def test_empty_key(self) -> None:
        assert split_key_value(": value") is None


class TestParseRubyishValue:
    def test_true(self) -> None:
        assert parse_rubyish_value("true") is True

    def test_false(self) -> None:
        assert parse_rubyish_value("false") is False

    def test_nil(self) -> None:
        assert parse_rubyish_value("nil") is None

    def test_integer(self) -> None:
        assert parse_rubyish_value("42") == 42

    def test_negative_integer(self) -> None:
        assert parse_rubyish_value("-7") == -7

    def test_symbol(self) -> None:
        assert parse_rubyish_value(":homebrew") == "homebrew"

    def test_quoted_string(self) -> None:
        assert parse_rubyish_value('"hello"') == "hello"

    def test_array(self) -> None:
        assert parse_rubyish_value('["a", "b"]') == ["a", "b"]

    def test_empty_array(self) -> None:
        assert parse_rubyish_value("[]") == []

    def test_hash(self) -> None:
        result = parse_rubyish_value('{key: "value"}')
        assert result == {"key": "value"}

    def test_case_insensitive_booleans(self) -> None:
        assert parse_rubyish_value("TRUE") is True
        assert parse_rubyish_value("False") is False

    def test_unquoted_string(self) -> None:
        assert parse_rubyish_value("plain") == "plain"


class TestExtractFirstArgument:
    def test_quoted_first(self) -> None:
        name, rest = extract_first_argument('"wget", args: ["HEAD"]')
        assert name == "wget"
        assert "args" in rest

    def test_single_quoted(self) -> None:
        name, rest = extract_first_argument("'wget'")
        assert name == "wget"
        assert rest == ""

    def test_unquoted(self) -> None:
        name, rest = extract_first_argument("wget, args: true")
        assert name == "wget"

    def test_empty(self) -> None:
        name, rest = extract_first_argument("")
        assert name is None
        assert rest == ""


class TestNormalizeKey:
    def test_symbol_key(self) -> None:
        assert normalize_key(":restart_service") == "restart_service"

    def test_hyphenated(self) -> None:
        assert normalize_key("no-quarantine") == "no_quarantine"

    def test_quoted_key(self) -> None:
        assert normalize_key('"my-key"') == "my_key"

    def test_plain(self) -> None:
        assert normalize_key("simple") == "simple"


class TestSanitizeOptions:
    def test_removes_ignored(self) -> None:
        result = sanitize_options({"a": 1, "b": 2}, ignore_keys=["b"])
        assert result == {"a": 1}

    def test_removes_underscore_prefix(self) -> None:
        result = sanitize_options({"a": 1, "_private": 2})
        assert result == {"a": 1}

    def test_no_ignore_keys(self) -> None:
        result = sanitize_options({"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}


class TestParseOptionsAndPositional:
    def test_key_value_pairs(self) -> None:
        options, positional = parse_options_and_positional('key: "value", other: true')
        assert options == {"key": "value", "other": True}
        assert positional == []

    def test_positional_args(self) -> None:
        options, positional = parse_options_and_positional('"foo", "bar"')
        assert options == {}
        assert positional == ["foo", "bar"]

    def test_mixed(self) -> None:
        options, positional = parse_options_and_positional('"foo", key: "value"')
        assert options == {"key": "value"}
        assert positional == ["foo"]

    def test_empty(self) -> None:
        options, positional = parse_options_and_positional("")
        assert options == {}
        assert positional == []
