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

    def test_convert_with_toc(self, tmp_path):
        """Test conversion of RFC with Table of Contents (baseline test)."""
        html_content = """<!DOCTYPE html>
<html>
<body>
<pre>
Internet Engineering Task Force (IETF)                       J. Harrison
Request for Comments: 7752                                     J. Berger
Category: Standards Track                                    M. Bartlett
ISSN: 2070-1721                                      Metaswitch Networks
                                                              March 2016


                   BGP Link-State Information

Abstract

   This document specifies a method for exchanging link-state
   information using the BGP routing protocol.

Status of This Memo

   This is an Internet Standards Track document.

Table of Contents

   1. Introduction ....................................................3
   2. Terminology .....................................................6
   3. Protocol Extensions .............................................8

1. Introduction

   This is the introduction text.

2. Terminology

   This section defines terminology.

3. Protocol Extensions

   This section describes protocol extensions.
</pre>
</body>
</html>
"""

        html_file = tmp_path / "test_with_toc.html"
        html_file.write_text(html_content)

        converter = HtmlToMdConverter(html_file)
        result = converter.convert()

        # Check that pre-TOC content is wrapped
        assert "```text" in result
        assert "Abstract" in result
        assert "Status of This Memo" in result
        assert "Internet Engineering Task Force" in result

        # Check that TOC is formatted with links
        assert "Table of Contents" in result or "`Table of Contents`" in result
        assert "[`1`](#section-1)" in result or "section-1" in result
        assert "[`2`](#section-2)" in result or "section-2" in result
        assert "[`3`](#section-3)" in result or "section-3" in result

        # Check that sections are properly formatted
        assert '<a id="section-1"></a> **`1. Introduction`**' in result
        assert '<a id="section-2"></a> **`2. Terminology`**' in result
        assert '<a id="section-3"></a> **`3. Protocol Extensions`**' in result

        # Check that section content is wrapped
        assert "This is the introduction text." in result
        assert "This section defines terminology." in result
        assert "This section describes protocol extensions." in result


class TestConvertWithoutToc:
    """Tests for converting RFC documents without Table of Contents."""

    def test_convert_without_toc(self, tmp_path):
        """Test conversion of RFC without Table of Contents."""
        # Create minimal HTML without TOC
        html_content = """<!DOCTYPE html>
<html>
<body>
<pre>
Internet Engineering Task Force (IETF)                       J. Harrison
Request for Comments: 6119                                     J. Berger
Category: Standards Track                                    M. Bartlett
ISSN: 2070-1721                                      Metaswitch Networks
                                                           February 2011


                   IPv6 Traffic Engineering in IS-IS

Abstract

   This document specifies a method for exchanging IPv6 traffic
   engineering information using the IS-IS routing protocol.

Status of This Memo

   This is an Internet Standards Track document.

Copyright Notice

   Copyright (c) 2011 IETF Trust and the persons identified as the
   document authors.  All rights reserved.

1. Introduction

   This is the introduction text.

2. Requirements

   These are the requirements.
</pre>
</body>
</html>
"""

        html_file = tmp_path / "test_no_toc.html"
        html_file.write_text(html_content)

        converter = HtmlToMdConverter(html_file)
        result = converter.convert()

        # Check that pre-section content is wrapped
        assert "```text" in result
        assert "Abstract" in result
        assert "Status of This Memo" in result
        assert "Copyright Notice" in result
        assert "Internet Engineering Task Force" in result

        # Check that sections are properly formatted
        assert '<a id="section-1"></a> **`1. Introduction`**' in result
        assert '<a id="section-2"></a> **`2. Requirements`**' in result

        # Check that section content is wrapped
        assert "This is the introduction text." in result
        assert "These are the requirements." in result

    def test_convert_without_toc_no_sections(self, tmp_path):
        """Test conversion of RFC without TOC and without sections."""
        html_content = """<!DOCTYPE html>
<html>
<body>
<pre>
Abstract

   This is the abstract.

Status of This Memo

   This is the status.
</pre>
</body>
</html>
"""

        html_file = tmp_path / "test_no_toc_no_sections.html"
        html_file.write_text(html_content)

        converter = HtmlToMdConverter(html_file)
        result = converter.convert()

        # All content should be wrapped in a single pre block
        assert "```text" in result
        assert "Abstract" in result
        assert "Status of This Memo" in result
        assert "This is the abstract." in result
        assert "This is the status." in result


class TestTocWithContentsHeader:
    """Tests for TOC extraction with 'Contents' header (RFC3209 format)."""

    def test_extract_toc_with_contents_header(self):
        """Test TOC extraction when header is 'Contents' instead of 'Table of Contents'."""
        converter = HtmlToMdConverter("dummy.html")
        text = """Some text before

Contents

   1      Introduction   ..........................................   3
   1.1    Background  .............................................   4

1. Introduction
"""
        result, formatted_toc, toc_start = converter._extract_toc(text)

        assert toc_start == 2  # Line where "Contents" appears
        assert "`Contents`" in formatted_toc
        assert "[`1`](#section-1)`. Introduction`" in formatted_toc
        assert "[`1.1`](#section-1-1)`. Background`" in formatted_toc

    def test_extract_toc_with_table_of_contents_header(self):
        """Test TOC extraction with standard 'Table of Contents' header (regression test)."""
        converter = HtmlToMdConverter("dummy.html")
        text = """Some text before

Table of Contents

   1      Introduction   ..........................................   3
   1.1    Background  .............................................   4

1. Introduction
"""
        result, formatted_toc, toc_start = converter._extract_toc(text)

        assert toc_start == 2
        assert "`Table of Contents`" in formatted_toc
        assert "[`1`](#section-1)`. Introduction`" in formatted_toc


class TestPageBreakRemovalExtended:
    """Extended tests for page break removal with various RFC formats."""

    def test_remove_page_breaks_best_current_practice(self):
        """Test removal of Best Current Practice page break format."""
        converter = HtmlToMdConverter("dummy.html")
        text = """Some text before

Narten & Alvestrand      Best Current Practice                  [Page 1]

Some text after"""

        result = converter._remove_page_breaks(text)

        # Page break should be completely removed
        assert "[Page 1]" not in result
        assert "Best Current Practice" not in result
        # Text should be continuous
        assert "Some text before" in result
        assert "Some text after" in result

    def test_remove_page_breaks_informational_format(self):
        """Test removal of informational RFC page break format."""
        converter = HtmlToMdConverter("dummy.html")
        text = """Content before

Seedorf & Burger             Informational                      [Page 2]

Content after"""

        result = converter._remove_page_breaks(text)

        assert "[Page 2]" not in result
        assert "Informational" not in result
        assert "Content before" in result
        assert "Content after" in result

    def test_remove_page_breaks_multiple(self):
        """Test removal of multiple page breaks."""
        converter = HtmlToMdConverter("dummy.html")
        text = """Section 1

Author Name              Category                               [Page 1]

Section 2

Author Name              Category                               [Page 2]

Section 3"""

        result = converter._remove_page_breaks(text)

        assert "[Page 1]" not in result
        assert "[Page 2]" not in result
        assert "Category" not in result
        # All sections should be present
        assert "Section 1" in result
        assert "Section 2" in result
        assert "Section 3" in result

    def test_remove_page_breaks_with_varying_spacing(self):
        """Test removal of page breaks with different spacing patterns."""
        converter = HtmlToMdConverter("dummy.html")
        text = """Text 1

Smith & Jones            Standards Track                        [Page 10]

Text 2

Brown                    Experimental                           [Page 100]

Text 3"""

        result = converter._remove_page_breaks(text)

        assert "[Page 10]" not in result
        assert "[Page 100]" not in result
        assert "Standards Track" not in result
        assert "Experimental" not in result

    def test_remove_page_breaks_preserves_content(self):
        """Test that page break removal doesn't affect actual content."""
        converter = HtmlToMdConverter("dummy.html")
        text = """This is important content about [Page numbers] in documents.

Author                   Status                                 [Page 5]

More content that mentions Page 5 in the text."""

        result = converter._remove_page_breaks(text)

        # Page break line should be removed
        assert "Author                   Status" not in result
        # But content mentioning pages should remain
        assert "[Page numbers]" in result
        assert "Page 5 in the text" in result

    def test_remove_page_breaks_empty_text(self):
        """Test page break removal with empty text."""
        converter = HtmlToMdConverter("dummy.html")
        text = ""

        result = converter._remove_page_breaks(text)

        assert result == ""

    def test_remove_page_breaks_no_breaks(self):
        """Test text without page breaks remains unchanged."""
        converter = HtmlToMdConverter("dummy.html")
        text = """This is a document
with multiple lines
but no page breaks."""

        result = converter._remove_page_breaks(text)

        assert result == text

    def test_remove_page_breaks_in_toc(self):
        """Test removal of page breaks that appear inside TOC (RFC4655/RFC7938 case)."""
        converter = HtmlToMdConverter("dummy.html")
        text = """Table of Contents

   1. Introduction . . . . . . . . . . . . . . . . . . . . . . . .   3
   2. Terminology  . . . . . . . . . . . . . . . . . . . . . . . .   4

Farrel, et al.               Informational                      [Page 1]

      4.5. Network Element Lacks Control Plane  . . . . . . . . . .   8
      4.6. Backup Path Computation  . . . . . . . . . . . . . . . .   8

1. Introduction"""

        result = converter._remove_page_breaks(text)

        # Page break should be removed
        assert "[Page 1]" not in result
        assert "Farrel, et al." not in result
        # TOC entries should be preserved and continuous
        assert "1. Introduction" in result
        assert "2. Terminology" in result
        assert "4.5. Network Element" in result
        assert "4.6. Backup Path" in result

    def test_remove_page_breaks_et_al_format(self):
        """Test removal of page breaks with 'et al.' in author names."""
        converter = HtmlToMdConverter("dummy.html")
        text = """Content before

Farrel, et al.               Informational                      [Page 1]

Content after"""

        result = converter._remove_page_breaks(text)

        assert "[Page 1]" not in result
        assert "Farrel, et al." not in result
        assert "Informational" not in result
        assert "Content before" in result
        assert "Content after" in result

    def test_remove_page_breaks_various_categories(self):
        """Test removal of page breaks with various RFC categories."""
        converter = HtmlToMdConverter("dummy.html")
        categories = [
            "Standards Track",
            "Informational",
            "Best Current Practice",
            "Experimental",
            "Historic",
        ]

        for i, category in enumerate(categories, 1):
            text = f"""Text before

Author Name              {category:40}[Page {i}]

Text after"""

            result = converter._remove_page_breaks(text)

            assert f"[Page {i}]" not in result
            assert category not in result
            assert "Text before" in result
            assert "Text after" in result
