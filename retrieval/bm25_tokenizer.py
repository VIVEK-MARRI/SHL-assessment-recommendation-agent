"""Deterministic tokenizer for the BM25 lexical search index.

Design contract
---------------
* Lowercase + Unicode NFKC normalisation applied first.
* Technical symbol substitutions are applied BEFORE punctuation removal
  so that ``C++`` → ``cpp``, ``C#`` → ``csharp``, ``.NET`` → ``dotnet``.
* Punctuation is then stripped.
* Whitespace is collapsed and the string is split into tokens.
* Empty tokens are removed.
* No stemming, no lemmatisation, no stop-word removal.
  Preserving all tokens maximises recall for technical queries.

Version
-------
TOKENIZER_VERSION is embedded in every BM25 config file.  A loader that
finds a mismatching version must raise an explicit error so stale indexes
are never silently consumed.
"""

from __future__ import annotations

import re
import unicodedata

TOKENIZER_VERSION: str = "1.0"

# ---------------------------------------------------------------------------
# Technical symbol substitution table
# Applied before punctuation removal so composite tokens survive intact.
# ---------------------------------------------------------------------------

_SYMBOL_MAP: list[tuple[re.Pattern[str], str]] = [
    # More-specific compound patterns FIRST
    (re.compile(r"asp\.net", re.IGNORECASE), "aspnet"),
    (re.compile(r"node\.js", re.IGNORECASE), "nodejs"),
    (re.compile(r"vue\.js", re.IGNORECASE), "vuejs"),
    (re.compile(r"react\.js", re.IGNORECASE), "reactjs"),
    (re.compile(r"next\.js", re.IGNORECASE), "nextjs"),
    # Generic single-token substitutions
    (re.compile(r"c\+\+", re.IGNORECASE), "cpp"),
    (re.compile(r"c#", re.IGNORECASE), "csharp"),
    (re.compile(r"f#", re.IGNORECASE), "fsharp"),
    (re.compile(r"\.net", re.IGNORECASE), "dotnet"),
]

# Strip any remaining punctuation except hyphens inside words and dots
# inside version numbers (e.g. "3.2.1") — handled by the split pass.
_PUNCT_PATTERN = re.compile(r"[^\w\s]")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def tokenize(text: str) -> list[str]:
    """Tokenize a document into a deterministic list of lowercase tokens.

    Steps:
        1. Unicode NFKC normalisation.
        2. Lowercase.
        3. Apply technical symbol substitutions (C++, C#, .NET …).
        4. Strip punctuation.
        5. Collapse whitespace and split.
        6. Drop empty tokens.

    Args:
        text: Raw document string.

    Returns:
        Non-empty list of lowercase string tokens.  Returns ``[]`` only
        if the input is blank after normalisation.
    """
    if not text:
        return []

    # 1. NFKC normalise + lowercase
    normalised = unicodedata.normalize("NFKC", text).lower()

    # 2. Technical substitutions
    for pattern, replacement in _SYMBOL_MAP:
        normalised = pattern.sub(replacement, normalised)

    # 3. Remove remaining punctuation (keep alphanumerics + whitespace)
    cleaned = _PUNCT_PATTERN.sub(" ", normalised)

    # 4. Collapse whitespace, split
    tokens = _WHITESPACE_PATTERN.sub(" ", cleaned).strip().split(" ")

    # 5. Drop empties
    return [t for t in tokens if t]
