"""Unit tests for the wizard's GCP private-key sanitizer.

The wizard accepts pasted private-key values in several real-world shapes
(bare value, JSON-quoted value, JSON-quoted value with trailing comma + next
field, multi-line raw paste). The sanitizer normalizes all of these to a clean
single-line `\\n`-escaped PEM that is safe to write into the generated .env.
"""
from csfle_gen.wizard import sanitize_gcp_private_key

CLEAN_PEM = "-----BEGIN PRIVATE KEY-----\\nAAAA\\nBBBB\\n-----END PRIVATE KEY-----\\n"


def test_bare_value_with_literal_escapes_passthrough() -> None:
    assert sanitize_gcp_private_key(CLEAN_PEM) == CLEAN_PEM


def test_json_quoted_value_strips_quotes_and_keeps_escapes() -> None:
    quoted = f'"{CLEAN_PEM}"'
    assert sanitize_gcp_private_key(quoted) == CLEAN_PEM


def test_over_pasted_value_drops_trailing_json_field() -> None:
    """Reproduces the real bug report: user pasted private_key + trailing comma + client_email."""
    over_pasted = (
        f'"{CLEAN_PEM}",\n'
        '  "client_email": "dvogiatzis-test-sa@csta-emea-ai-devel.iam.gserviceaccount.com"'
    )
    assert sanitize_gcp_private_key(over_pasted) == CLEAN_PEM


def test_multiline_raw_paste_collapses_newlines_to_escapes() -> None:
    """User pasted the actual PEM with real newlines (no JSON quoting)."""
    raw_multiline = "-----BEGIN PRIVATE KEY-----\nAAAA\nBBBB\n-----END PRIVATE KEY-----\n"
    assert sanitize_gcp_private_key(raw_multiline) == CLEAN_PEM


def test_crlf_normalized() -> None:
    # No -----END marker, so trailing-newline restoration doesn't kick in;
    # the outer strip() removes the trailing CRLF and we don't add it back.
    assert sanitize_gcp_private_key("foo\r\nbar\r\n") == "foo\\nbar"


def test_blank_passes_through() -> None:
    assert sanitize_gcp_private_key("") == ""
    assert sanitize_gcp_private_key("   ") == ""


def test_leading_and_trailing_whitespace_stripped() -> None:
    assert sanitize_gcp_private_key(f"  \n{CLEAN_PEM}\n  ") == CLEAN_PEM


def test_unbalanced_quote_falls_back_to_raw() -> None:
    """If JSON parsing fails (e.g. unbalanced quote), still produce a usable value."""
    # Just one orphan double quote; JSONDecoder.raw_decode raises, so we fall through
    # to whitespace strip + newline normalization.
    assert sanitize_gcp_private_key('"oops') == '"oops'
