"""Tests for utility functions."""

from lib.utils import normalize_rfc_number


class TestNormalizeRfcNumber:
    """Tests for normalize_rfc_number function."""

    def test_normalize_with_rfc_prefix(self):
        """Test normalization with RFC prefix."""
        assert normalize_rfc_number("RFC9514") == "rfc9514"
        assert normalize_rfc_number("rfc9514") == "rfc9514"
        assert normalize_rfc_number("Rfc9514") == "rfc9514"

    def test_normalize_without_prefix(self):
        """Test normalization without RFC prefix."""
        assert normalize_rfc_number("9514") == "rfc9514"
        assert normalize_rfc_number("2119") == "rfc2119"

    def test_normalize_with_spaces(self):
        """Test normalization with spaces."""
        assert normalize_rfc_number("RFC 9514") == "rfc9514"
        assert normalize_rfc_number(" RFC9514 ") == "rfc9514"
        assert normalize_rfc_number("  9514  ") == "rfc9514"

    def test_normalize_edge_cases(self):
        """Test edge cases."""
        assert normalize_rfc_number("RFC1") == "rfc1"
        assert normalize_rfc_number("1") == "rfc1"
        assert normalize_rfc_number("RFC99999") == "rfc99999"
