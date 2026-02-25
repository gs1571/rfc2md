"""
Tests for HTML to Markdown converter.
"""

from lib.html_converter import HtmlToMdConverter


class TestHtmlConverter:
    """Tests for HTML converter basic functionality."""

    def test_import(self):
        """Test that the module can be imported."""
        assert HtmlToMdConverter is not None

    def test_initialization(self):
        """Test converter initialization."""
        converter = HtmlToMdConverter("test.html")
        assert converter.html_file.name == "test.html"
        assert converter.soup is None
        assert converter.markdown_lines == []


class TestPageBreakRemoval:
    """Tests for page break removal functionality."""

    def test_remove_page_breaks(self):
        """Test that page headers and footers are removed."""
        converter = HtmlToMdConverter("dummy.html")

        text = """Some content here
Gredler, et al.              Standards Track                    [Page 1]
More content
RFC 7752                  BGP-LS                        March 2016
Final content"""

        result = converter._remove_page_breaks(text)

        # Page header and footer should be removed
        assert "Standards Track" not in result
        assert "[Page 1]" not in result
        assert "March 2016" not in result or "RFC 7752" not in result

        # Content should remain
        assert "Some content here" in result
        assert "More content" in result
        assert "Final content" in result

    def test_preserve_paragraph_breaks(self):
        """Test that intentional paragraph breaks are preserved."""
        converter = HtmlToMdConverter("dummy.html")

        text = """First paragraph ends here.

Second paragraph starts here."""

        result = converter._remove_page_breaks(text)

        # Empty line should be preserved
        assert "\n\n" in result or result.count("\n") >= 2


class TestLinkRemoval:
    """Tests for HTML link removal."""

    def test_remove_links(self):
        """Test that HTML links are removed while preserving text."""
        converter = HtmlToMdConverter("dummy.html")

        text = 'This is <a href="#section-1">Section 1</a> and <a href="http://example.com">example</a>.'

        result = converter._remove_links(text)

        # Links should be removed
        assert "<a" not in result
        assert "</a>" not in result
        assert "href" not in result

        # Text should be preserved
        assert "Section 1" in result
        assert "example" in result


class TestEmptyLineCollapse:
    """Tests for empty line collapsing."""

    def test_collapse_empty_lines(self):
        """Test that multiple empty lines are collapsed to single empty line."""
        converter = HtmlToMdConverter("dummy.html")

        text = """First paragraph.



Second paragraph.




Third paragraph."""

        result = converter._collapse_empty_lines(text)

        # Should not have triple newlines
        assert "\n\n\n" not in result

        # Should still have double newlines (single empty line)
        assert "\n\n" in result


class TestTocExtraction:
    """Tests for Table of Contents extraction and formatting."""

    def test_extract_toc(self):
        """Test TOC extraction from text."""
        converter = HtmlToMdConverter("dummy.html")

        text = """Some content before TOC

Table of Contents

   1. Introduction ....................................................3
      1.1. Requirements Language ......................................5
   2. Motivation and Applicability ....................................5

1. Introduction

   This is the introduction text."""

        result, formatted_toc, toc_start = converter._extract_toc(text)

        # TOC should be found
        assert toc_start >= 0

        # Formatted TOC should contain markdown links
        assert "[`1`](#section-1)" in result or "`1`" in result

    def test_format_toc_entry(self):
        """Test formatting of individual TOC entries."""
        converter = HtmlToMdConverter("dummy.html")

        # Test entry with leading spaces
        line = "   1. Introduction ....................................................3"
        result = converter._format_toc_entry(line)

        # Should preserve leading spaces and create link
        assert result is not None
        assert "Introduction" in result
        assert "`" in result  # Should be monospace


class TestSectionProcessing:
    """Tests for section header processing."""

    def test_create_section_anchor(self):
        """Test section anchor ID creation."""
        converter = HtmlToMdConverter("dummy.html")

        # Test simple section number
        assert converter._create_section_anchor("1") == "section-1"

        # Test nested section number
        assert converter._create_section_anchor("1.2.3") == "section-1-2-3"

    def test_process_sections(self):
        """Test section processing and wrapping."""
        converter = HtmlToMdConverter("dummy.html")

        text = """Pre-TOC content

`Table of Contents`

1. Introduction

   This is introduction text.

2. Background

   This is background text."""

        result = converter._process_sections(text, 2)

        # Should contain section anchors
        assert "section-1" in result or "<a id=" in result

        # Should contain pre blocks
        assert "```text" in result


class TestTocFormatting:
    """Tests for TOC entry formatting."""

    def test_format_toc_entry_rfc7752_format(self):
        """Test TOC entry formatting for RFC7752 format (continuous dots)."""
        converter = HtmlToMdConverter("dummy.html")

        # Test format: "   1. Introduction....3"
        line = "   1. Introduction....................................................3"
        result = converter._format_toc_entry(line)
        expected = "`   `[`1`](#section-1)`. Introduction`"
        assert result == expected

    def test_format_toc_entry_rfc8402_format(self):
        """Test TOC entry formatting for RFC8402 format (spaced dots)."""
        converter = HtmlToMdConverter("dummy.html")

        # Test format: "   1. Introduction  . . . . . . . . . . . . . . . . . . . . . . .  6"
        line = "   1. Introduction  . . . . . . . . . . . . . . . . . . . . . . .  6"
        result = converter._format_toc_entry(line)
        expected = "`   `[`1`](#section-1)`. Introduction`"
        assert result == expected

    def test_format_toc_entry_with_subsection(self):
        """Test TOC entry with subsection number."""
        converter = HtmlToMdConverter("dummy.html")

        # RFC7752 format
        line = "      1.1. Requirements Language ......................................5"
        result = converter._format_toc_entry(line)
        expected = "`      `[`1.1`](#section-1-1)`. Requirements Language`"
        assert result == expected

        # RFC8402 format
        line = "     3.1. IGP-Prefix Segment (Prefix-SID) . . . . . . . . . . . .  9"
        result = converter._format_toc_entry(line)
        expected = "`     `[`3.1`](#section-3-1)`. IGP-Prefix Segment (Prefix-SID)`"
        assert result == expected

    def test_format_toc_entry_with_deep_subsection(self):
        """Test TOC entry with deep subsection number."""
        converter = HtmlToMdConverter("dummy.html")

        line = "           3.2.1. Node Descriptors...................................12"
        result = converter._format_toc_entry(line)
        expected = "`           `[`3.2.1`](#section-3-2-1)`. Node Descriptors`"
        assert result == expected

    def test_format_toc_entry_continuation_line(self):
        """Test TOC entry continuation line (no section number)."""
        converter = HtmlToMdConverter("dummy.html")

        line = "                  Functional Components"
        result = converter._format_toc_entry(line)
        expected = "`                  Functional Components`"
        assert result == expected

    def test_format_toc_entry_with_page_number_rfc7752(self):
        """Test TOC entry with page number at the end (RFC7752 format)."""
        converter = HtmlToMdConverter("dummy.html")

        # RFC7752 format with page number
        line = "   1. Introduction.....................................3"
        result = converter._format_toc_entry(line)
        expected = "`   `[`1`](#section-1)`. Introduction`"
        assert result == expected

    def test_format_toc_entry_with_page_number_rfc8402(self):
        """Test TOC entry with page number at the end (RFC8402 format)."""
        converter = HtmlToMdConverter("dummy.html")

        # RFC8402 format with page number
        line = "   1. Introduction  . . . . . . . . . . . . . . . . . . . . . . .  5"
        result = converter._format_toc_entry(line)
        expected = "`   `[`1`](#section-1)`. Introduction`"
        assert result == expected

    def test_format_toc_entry_empty_line(self):
        """Test TOC entry with empty line."""
        converter = HtmlToMdConverter("dummy.html")

        line = "   "
        result = converter._format_toc_entry(line)
        assert result is None

    def test_format_toc_entry_special_characters(self):
        """Test TOC entry with special characters in title."""
        converter = HtmlToMdConverter("dummy.html")

        line = "   3. Link-State IGP Segments . . . . . . . . . . . . . . . . .  9"
        result = converter._format_toc_entry(line)
        expected = "`   `[`3`](#section-3)`. Link-State IGP Segments`"
        assert result == expected

    def test_format_toc_entry_mixed_formats(self):
        """Test that both RFC formats work correctly in same document."""
        converter = HtmlToMdConverter("dummy.html")

        # RFC7752 style
        line1 = "   1. Introduction....................................................3"
        result1 = converter._format_toc_entry(line1)
        assert result1 is not None
        assert "Introduction`" in result1
        assert ". . ." not in result1
        assert "..." not in result1

        # RFC8402 style
        line2 = "   2. Terminology . . . . . . . . . . . . . . . . . . . . . . . .  6"
        result2 = converter._format_toc_entry(line2)
        assert result2 is not None
        assert "Terminology`" in result2
        assert ". . ." not in result2
