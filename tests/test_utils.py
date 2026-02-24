"""Tests for utility functions."""

import tempfile
from pathlib import Path

from lib.utils import extract_rfc_references, normalize_rfc_number


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


class TestExtractRfcReferences:
    """Tests for extract_rfc_references function."""

    def test_extract_from_real_xml(self):
        """Test extraction from real RFC XML file."""
        xml_file = Path("examples/rfc9514.xml")
        refs = extract_rfc_references(xml_file)

        # Should return a set
        assert isinstance(refs, set)

        # Should contain expected RFCs
        assert "rfc2119" in refs
        assert "rfc7752" in refs
        assert "rfc8402" in refs
        assert "rfc9085" in refs

        # Should have normalized format (lowercase)
        for ref in refs:
            assert ref.startswith("rfc")
            assert ref.islower()

    def test_extract_returns_set(self):
        """Test that function returns a set."""
        xml_file = Path("examples/rfc9514.xml")
        refs = extract_rfc_references(xml_file)
        assert isinstance(refs, set)

    def test_extract_normalized_format(self):
        """Test that RFC numbers are normalized."""
        xml_file = Path("examples/rfc9514.xml")
        refs = extract_rfc_references(xml_file)

        # All should be in format "rfcXXXX"
        for ref in refs:
            assert ref.startswith("rfc")
            assert ref[3:].isdigit()

    def test_extract_from_empty_xml(self):
        """Test extraction from XML without references."""
        # Create a minimal XML without references
        xml_content = """<?xml version='1.0' encoding='utf-8'?>
<rfc>
  <front>
    <title>Test RFC</title>
  </front>
  <middle>
    <section>
      <name>Test</name>
    </section>
  </middle>
</rfc>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            temp_file = Path(f.name)

        try:
            refs = extract_rfc_references(temp_file)
            assert isinstance(refs, set)
            assert len(refs) == 0
        finally:
            temp_file.unlink()

    def test_extract_from_invalid_xml(self):
        """Test extraction from invalid XML."""
        # Create an invalid XML file
        xml_content = "This is not valid XML"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            temp_file = Path(f.name)

        try:
            refs = extract_rfc_references(temp_file)
            # Should return empty set on error
            assert isinstance(refs, set)
            assert len(refs) == 0
        finally:
            temp_file.unlink()

    def test_extract_from_nonexistent_file(self):
        """Test extraction from non-existent file."""
        xml_file = Path("nonexistent_file.xml")
        refs = extract_rfc_references(xml_file)

        # Should return empty set
        assert isinstance(refs, set)
        assert len(refs) == 0
