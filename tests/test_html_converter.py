"""
Tests for HTML to Markdown converter.
"""

import pytest

from lib.html_converter import HtmlToMdConverter


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

    def test_merge_split_paragraphs(self):
        """Test that paragraphs split by page breaks are merged."""
        converter = HtmlToMdConverter("dummy.html")
        
        text = """This is a sentence that continues
on the next line without proper ending
This is a new paragraph."""
        
        result = converter._remove_page_breaks(text)
        
        # Lines should be merged if they don't end with terminal punctuation
        lines = result.split("\n")
        # The first two lines should be merged
        assert any("continues on the next line" in line for line in lines)

    def test_preserve_paragraph_breaks(self):
        """Test that intentional paragraph breaks are preserved."""
        converter = HtmlToMdConverter("dummy.html")
        
        text = """First paragraph ends here.

Second paragraph starts here."""
        
        result = converter._remove_page_breaks(text)
        
        # Empty line should be preserved
        assert "\n\n" in result or result.count("\n") >= 2


class TestCodeBlockDetection:
    """Tests for code block detection heuristics."""

    def test_is_ascii_art(self):
        """Test ASCII art detection."""
        converter = HtmlToMdConverter("dummy.html")
        
        # ASCII art with box characters
        ascii_art = [
            "+---+---+",
            "| A | B |",
            "+---+---+",
            "| C | D |",
            "+---+---+"
        ]
        assert converter._is_ascii_art(ascii_art) is True
        
        # Regular text
        regular_text = [
            "This is normal text",
            "without any special characters",
            "just plain prose"
        ]
        assert converter._is_ascii_art(regular_text) is False

    def test_is_protocol_format(self):
        """Test protocol format detection."""
        converter = HtmlToMdConverter("dummy.html")
        
        # Protocol diagram with bit markers
        protocol = [
            "0 1 2 3 4 5 6 7",
            "+-+-+-+-+-+-+-+-+",
            "|  Type | Flags |",
            "+-+-+-+-+-+-+-+-+"
        ]
        assert converter._is_protocol_format(protocol) is True
        
        # Regular text
        regular_text = [
            "This is normal text",
            "without protocol markers"
        ]
        assert converter._is_protocol_format(regular_text) is False

    def test_is_ascii_table(self):
        """Test ASCII table detection."""
        converter = HtmlToMdConverter("dummy.html")
        
        # ASCII table
        table = [
            "+-------+-------+",
            "| Col 1 | Col 2 |",
            "+-------+-------+",
            "| Val 1 | Val 2 |",
            "+-------+-------+"
        ]
        assert converter._is_ascii_table(table) is True
        
        # Not a table
        not_table = [
            "Just some text",
            "with a | pipe character"
        ]
        assert converter._is_ascii_table(not_table) is False

    def test_detect_lists(self):
        """Test list detection from indentation."""
        converter = HtmlToMdConverter("dummy.html")
        
        lines = [
            "- First item",
            "- Second item",
            "1. Numbered item",
            "2. Another numbered",
            "Term",
            "  Definition of term"
        ]
        
        list_items = converter._detect_lists(lines)
        
        # Should detect unordered, ordered, and definition lists
        assert len(list_items) > 0
        assert any(item[1] == "ul" for item in list_items)
        assert any(item[1] == "ol" for item in list_items)

    def test_detect_code_blocks(self):
        """Test code block detection."""
        converter = HtmlToMdConverter("dummy.html")
        
        text = """Regular text here.

    def function():
        return True
    
More regular text.

+---+---+
| A | B |
+---+---+

Final text."""
        
        blocks = converter._detect_code_blocks(text)
        
        # Should detect at least the indented code and table
        assert len(blocks) > 0
        assert any(block[2] in ["code", "table"] for block in blocks)


class TestLinkConversion:
    """Tests for link conversion functionality."""

    def test_convert_internal_links(self):
        """Test conversion of internal section links."""
        from bs4 import BeautifulSoup
        
        converter = HtmlToMdConverter("dummy.html")
        
        html = '<a href="#section-3.2.1">Section 3.2.1</a>'
        element = BeautifulSoup(html, "html.parser")
        
        result = converter._convert_links(element)
        
        # Dots should be replaced with hyphens
        assert "#section-3-2-1" in result
        assert "Section 3.2.1" in result

    def test_convert_rfc_references(self):
        """Test conversion of RFC reference links."""
        from bs4 import BeautifulSoup
        
        converter = HtmlToMdConverter("dummy.html")
        
        html = '<a href="./rfc5305">RFC 5305</a>'
        element = BeautifulSoup(html, "html.parser")
        
        result = converter._convert_links(element)
        
        # Should convert to full URL
        assert "https://www.rfc-editor.org/rfc/rfc5305" in result
        assert "RFC 5305" in result or "RFC5305" in result

    def test_convert_external_links(self):
        """Test that external links are preserved."""
        from bs4 import BeautifulSoup
        
        converter = HtmlToMdConverter("dummy.html")
        
        html = '<a href="https://example.com">Example</a>'
        element = BeautifulSoup(html, "html.parser")
        
        result = converter._convert_links(element)
        
        # Should preserve external URL
        assert "https://example.com" in result
        assert "Example" in result


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
        assert converter.metadata == {}
        assert converter.sections == []