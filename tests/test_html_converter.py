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
        assert "```" in result
