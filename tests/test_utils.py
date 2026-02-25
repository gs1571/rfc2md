"""Tests for utility functions."""

import tempfile
from pathlib import Path

from lib.utils import (
    extract_rfc_references_from_html,
    extract_rfc_references_from_xml,
    normalize_rfc_number,
)


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
    """Tests for extract_rfc_references_from_xml function."""

    def test_extract_from_real_xml(self):
        """Test extraction from real RFC XML file."""
        xml_file = Path("examples/rfc9514.xml")
        refs = extract_rfc_references_from_xml(xml_file)

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
        refs = extract_rfc_references_from_xml(xml_file)
        assert isinstance(refs, set)

    def test_extract_normalized_format(self):
        """Test that RFC numbers are normalized."""
        xml_file = Path("examples/rfc9514.xml")
        refs = extract_rfc_references_from_xml(xml_file)

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
            refs = extract_rfc_references_from_xml(temp_file)
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
            refs = extract_rfc_references_from_xml(temp_file)
            # Should return empty set on error
            assert isinstance(refs, set)
            assert len(refs) == 0
        finally:
            temp_file.unlink()

    def test_extract_from_nonexistent_file(self):
        """Test extraction from non-existent file."""
        xml_file = Path("nonexistent_file.xml")
        refs = extract_rfc_references_from_xml(xml_file)

        # Should return empty set
        assert isinstance(refs, set)
        assert len(refs) == 0


class TestExtractRfcReferencesFromHtml:
    """Tests for extract_rfc_references_from_html function."""

    def test_extract_from_real_html(self):
        """Test extraction from real RFC HTML file."""
        html_file = Path("output/test_html_recursive/rfc1149.html")
        if not html_file.exists():
            # Skip if file doesn't exist
            return

        refs = extract_rfc_references_from_html(html_file)

        # Should return a set
        assert isinstance(refs, set)

        # Should contain expected RFCs (rfc1149 references rfc2549 and rfc6214)
        assert "rfc2549" in refs
        assert "rfc6214" in refs

        # Should have normalized format (lowercase)
        for ref in refs:
            assert ref.startswith("rfc")
            assert ref.islower()

    def test_extract_from_html_with_links(self):
        """Test extraction from HTML with RFC links."""
        html_content = """
        <html>
        <body>
            <p>Updated by: <a href="/rfc/rfc2549">RFC 2549</a>, <a href="/rfc/rfc6214.html">RFC 6214</a></p>
            <p>See also <a href="/rfc/rfc1234">1234</a></p>
        </body>
        </html>
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = Path(f.name)

        try:
            refs = extract_rfc_references_from_html(temp_file)
            assert isinstance(refs, set)
            assert "rfc2549" in refs
            assert "rfc6214" in refs
            assert "rfc1234" in refs
        finally:
            temp_file.unlink()

    def test_extract_from_html_with_text_references(self):
        """Test extraction from HTML with RFC text references."""
        html_content = """
        <html>
        <body>
            <p>This document updates RFC 1149 and RFC-2549.</p>
            <p>See RFC9514 for more details.</p>
        </body>
        </html>
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = Path(f.name)

        try:
            refs = extract_rfc_references_from_html(temp_file)
            assert isinstance(refs, set)
            assert "rfc1149" in refs
            assert "rfc2549" in refs
            assert "rfc9514" in refs
        finally:
            temp_file.unlink()

    def test_extract_returns_set(self):
        """Test that function returns a set."""
        html_content = "<html><body>RFC 1234</body></html>"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = Path(f.name)

        try:
            refs = extract_rfc_references_from_html(temp_file)
            assert isinstance(refs, set)
        finally:
            temp_file.unlink()

    def test_extract_normalized_format(self):
        """Test that RFC numbers are normalized."""
        html_content = """
        <html><body>
            <a href="/rfc/rfc1234">RFC 1234</a>
            <p>See RFC-5678 and RFC9999</p>
        </body></html>
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = Path(f.name)

        try:
            refs = extract_rfc_references_from_html(temp_file)
            # All should be in format "rfcXXXX"
            for ref in refs:
                assert ref.startswith("rfc")
                assert ref[3:].isdigit()
        finally:
            temp_file.unlink()

    def test_extract_from_empty_html(self):
        """Test extraction from HTML without references."""
        html_content = "<html><body><p>No RFC references here</p></body></html>"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = Path(f.name)

        try:
            refs = extract_rfc_references_from_html(temp_file)
            assert isinstance(refs, set)
            # May be empty or contain self-references
        finally:
            temp_file.unlink()

    def test_extract_from_nonexistent_file(self):
        """Test extraction from non-existent file."""
        html_file = Path("nonexistent_file.html")
        refs = extract_rfc_references_from_html(html_file)

        # Should return empty set
        assert isinstance(refs, set)
        assert len(refs) == 0

    def test_extract_deduplicates_references(self):
        """Test that duplicate references are deduplicated."""
        html_content = """
        <html><body>
            <a href="/rfc/rfc1234">RFC 1234</a>
            <p>See RFC 1234 and RFC-1234 again</p>
            <a href="/rfc/rfc1234.html">1234</a>
        </body></html>
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = Path(f.name)

        try:
            refs = extract_rfc_references_from_html(temp_file)
            # Should have only one rfc1234 despite multiple mentions
            assert "rfc1234" in refs
            # Count how many times rfc1234 appears (should be 1 since it's a set)
            rfc1234_count = sum(1 for ref in refs if ref == "rfc1234")
            assert rfc1234_count == 1
        finally:
            temp_file.unlink()
