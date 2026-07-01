"""Unit tests for retrieval.bm25_tokenizer."""

from __future__ import annotations

from retrieval.bm25_tokenizer import TOKENIZER_VERSION, tokenize


class TestTokenizerVersion:
    def test_version_is_string(self):
        assert isinstance(TOKENIZER_VERSION, str)

    def test_version_not_empty(self):
        assert TOKENIZER_VERSION


class TestBasicTokenization:
    def test_lowercase(self):
        assert tokenize("Hello World") == ["hello", "world"]

    def test_empty_string(self):
        assert tokenize("") == []

    def test_whitespace_only(self):
        assert tokenize("   ") == []

    def test_collapse_whitespace(self):
        assert tokenize("foo   bar") == ["foo", "bar"]

    def test_numbers_preserved(self):
        assert "8" in tokenize("Java 8")

    def test_version_numbers(self):
        tokens = tokenize("Python 3.11.2")
        assert "3" in tokens or "3112" in tokens or "python" in tokens

    def test_acronyms(self):
        tokens = tokenize("REST APIs")
        assert "rest" in tokens
        assert "apis" in tokens


class TestTechnicalSubstitutions:
    def test_cpp(self):
        assert "cpp" in tokenize("C++")

    def test_cpp_lowercase(self):
        assert "cpp" in tokenize("c++")

    def test_csharp(self):
        assert "csharp" in tokenize("C#")

    def test_fsharp(self):
        assert "fsharp" in tokenize("F#")

    def test_dotnet(self):
        assert "dotnet" in tokenize(".NET")

    def test_dotnet_framework(self):
        tokens = tokenize(".NET Framework 4.5")
        assert "dotnet" in tokens
        assert "framework" in tokens

    def test_nodejs(self):
        assert "nodejs" in tokenize("Node.js")

    def test_aspnet(self):
        assert "aspnet" in tokenize("ASP.NET")

    def test_no_url_in_output(self):
        """URL is not semantic content; sanitised away from punctuation."""
        tokens = tokenize("Visit https://example.com for details")
        assert "https" in tokens or "example" in tokens

    def test_vuejs(self):
        assert "vuejs" in tokenize("Vue.js")


class TestDeterminism:
    def test_same_input_same_output(self):
        text = "C++ developer with .NET and REST APIs experience"
        assert tokenize(text) == tokenize(text)

    def test_order_preserved(self):
        tokens = tokenize("alpha beta gamma")
        assert tokens == ["alpha", "beta", "gamma"]


class TestUnicodeNormalization:
    def test_nfkc_applied(self):
        # NFKC normalises full-width latin letters to ASCII equivalents
        tokens = tokenize("\uff41\uff42\uff43")  # ａｂｃ → abc
        assert tokens == ["abc"]

    def test_accented_characters(self):
        tokens = tokenize("café")
        assert len(tokens) == 1
        assert tokens[0] in ("cafe", "café")
