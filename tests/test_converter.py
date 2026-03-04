"""
Unit tests for lib/converter.py module.

This module tests the XmlToMdConverter class for converting RFC XML v3 documents
to well-formatted Markdown.
"""

import pytest
from pathlib import Path
from lxml import etree

from lib.converter import XmlToMdConverter


class TestXmlToMdConverterInit:
    """Test XmlToMdConverter initialization."""

    def test_init_with_valid_path(self, tmp_path):
        """Test initialization with valid XML file path."""
        xml_file = tmp_path / "test.xml"
        xml_file.write_text('<?xml version="1.0"?><root/>', encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        
        assert converter.xml_file == xml_file
        assert converter.tree is None
        assert converter.root is None
        assert converter.markdown_lines == []
        assert converter.section_depth == 0
        assert converter.toc_entries == []
        assert converter.section_id_to_anchor == {}

    def test_init_with_string_path(self, tmp_path):
        """Test initialization with string path."""
        xml_file = tmp_path / "test.xml"
        xml_file.write_text('<?xml version="1.0"?><root/>', encoding="utf-8")
        
        converter = XmlToMdConverter(str(xml_file))
        
        assert converter.xml_file == Path(xml_file)


class TestXmlToMdConverterErrorHandling:
    """Test error handling in XmlToMdConverter."""

    def test_convert_with_invalid_xml_syntax(self, tmp_path):
        """Test conversion with invalid XML syntax."""
        xml_file = tmp_path / "invalid.xml"
        xml_file.write_text('<?xml version="1.0"?><root><unclosed>', encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        
        with pytest.raises(ValueError, match="Invalid XML syntax"):
            converter.convert()

    def test_convert_with_nonexistent_file(self, tmp_path):
        """Test conversion with nonexistent file."""
        xml_file = tmp_path / "nonexistent.xml"
        
        converter = XmlToMdConverter(xml_file)
        
        with pytest.raises(ValueError, match="Error parsing XML"):
            converter.convert()


class TestBuildSectionAnchorMapping:
    """Test section anchor mapping functionality."""

    def test_build_section_anchor_mapping_with_middle_sections(self, tmp_path):
        """Test building anchor mapping from middle sections."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <middle>
        <section pn="section-1" anchor="intro">
            <name>Introduction</name>
        </section>
        <section pn="section-2" anchor="overview">
            <name>Overview</name>
            <section pn="section-2.1" anchor="details">
                <name>Details</name>
            </section>
        </section>
    </middle>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._build_section_anchor_mapping()
        
        assert converter.section_id_to_anchor["section-1"] == "intro"
        assert converter.section_id_to_anchor["section-2"] == "overview"
        assert converter.section_id_to_anchor["section-2.1"] == "details"

    def test_build_section_anchor_mapping_with_back_sections(self, tmp_path):
        """Test building anchor mapping from back sections."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <back>
        <section pn="appendix-a" anchor="appendix-a">
            <name>Appendix A</name>
        </section>
    </back>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._build_section_anchor_mapping()
        
        assert converter.section_id_to_anchor["appendix-a"] == "appendix-a"


class TestProcessFront:
    """Test front matter processing."""

    def test_process_front_with_minimal_metadata(self, tmp_path):
        """Test processing front with minimal metadata."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <front>
        <title>Test RFC</title>
    </front>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_front()
        
        assert "# Test RFC" in converter.markdown_lines

    def test_process_front_with_title_abbrev(self, tmp_path):
        """Test processing front with title abbreviation."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <front>
        <title abbrev="Short Title">Very Long Title That Needs Abbreviation</title>
    </front>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_front()
        
        assert "# Very Long Title That Needs Abbreviation" in converter.markdown_lines
        assert "*(Short Title)*" in converter.markdown_lines

    def test_process_front_with_series_info(self, tmp_path):
        """Test processing front with series information."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <front>
        <title>Test RFC</title>
        <seriesInfo name="RFC" value="9514" stream="IETF"/>
    </front>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_front()
        
        assert "**RFC 9514**" in converter.markdown_lines
        assert "*Stream: IETF*" in converter.markdown_lines

    def test_process_front_with_root_metadata(self, tmp_path):
        """Test processing front with root element metadata."""
        xml_content = '''<?xml version="1.0"?>
<rfc category="std" obsoletes="1234" updates="5678" submissionType="IETF" 
     consensus="true" ipr="trust200902" docName="draft-test-01">
    <front>
        <title>Test RFC</title>
    </front>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_front()
        
        assert "**Category:** std" in converter.markdown_lines
        assert "**Obsoletes:** 1234" in converter.markdown_lines
        assert "**Updates:** 5678" in converter.markdown_lines
        assert "**Submission Type:** IETF" in converter.markdown_lines
        assert "**Consensus:** true" in converter.markdown_lines
        assert "**IPR:** trust200902" in converter.markdown_lines
        assert "**Doc Name:** draft-test-01" in converter.markdown_lines

    def test_process_front_with_authors(self, tmp_path):
        """Test processing front with author information."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <front>
        <title>Test RFC</title>
        <author fullname="John Doe" initials="J." surname="Doe" role="editor">
            <organization>Example Corp</organization>
            <address>
                <email>john@example.com</email>
            </address>
        </author>
    </front>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_front()
        
        assert "## Authors" in converter.markdown_lines
        assert "- John Doe *(Editor)*" in converter.markdown_lines
        assert "  - Example Corp" in converter.markdown_lines
        assert "  - Email: john@example.com" in converter.markdown_lines

    def test_process_front_with_date(self, tmp_path):
        """Test processing front with date information."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <front>
        <title>Test RFC</title>
        <date month="December" year="2023" day="5"/>
    </front>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_front()
        
        assert "**Date:** 5 December 2023" in converter.markdown_lines

    def test_process_front_with_area_and_workgroup(self, tmp_path):
        """Test processing front with area and workgroup."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <front>
        <title>Test RFC</title>
        <area>rtg</area>
        <workgroup>idr</workgroup>
    </front>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_front()
        
        assert "**Area:** rtg" in converter.markdown_lines
        assert "**Workgroup:** idr" in converter.markdown_lines

    def test_process_front_with_keywords(self, tmp_path):
        """Test processing front with keywords."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <front>
        <title>Test RFC</title>
        <keyword>BGP</keyword>
        <keyword>Segment Routing</keyword>
        <keyword>SRv6</keyword>
    </front>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_front()
        
        assert "**Keywords:** BGP, Segment Routing, SRv6" in converter.markdown_lines

    def test_process_front_with_abstract(self, tmp_path):
        """Test processing front with abstract."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <front>
        <title>Test RFC</title>
        <abstract>
            <t>This is the abstract text.</t>
            <t indent="3">This is indented text.</t>
        </abstract>
    </front>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_front()
        
        assert "## Abstract" in converter.markdown_lines
        assert "This is the abstract text." in converter.markdown_lines


class TestGenerateToc:
    """Test TOC generation."""

    def test_generate_toc_without_toc_element(self, tmp_path):
        """Test TOC generation when no TOC element exists."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <front>
        <title>Test RFC</title>
    </front>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        toc_lines = converter._generate_toc()
        
        assert "## Table of Contents" in toc_lines


class TestProcessMiddle:
    """Test middle section processing."""

    def test_process_middle_with_sections(self, tmp_path):
        """Test processing middle with sections."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <middle>
        <section anchor="intro">
            <name>Introduction</name>
            <t>Introduction text.</t>
        </section>
    </middle>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_middle()
        
        assert '<a name="intro"></a>' in converter.markdown_lines
        assert "# Introduction" in converter.markdown_lines
        assert "Introduction text." in converter.markdown_lines


class TestProcessBack:
    """Test back section processing."""

    def test_process_back_with_references(self, tmp_path):
        """Test processing back with references."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <back>
        <references>
            <name>References</name>
            <references anchor="normative">
                <name>Normative References</name>
                <reference anchor="RFC2119">
                    <front>
                        <title>Key words for use in RFCs</title>
                        <author initials="S." surname="Bradner"/>
                        <date month="March" year="1997"/>
                    </front>
                    <seriesInfo name="RFC" value="2119"/>
                </reference>
            </references>
        </references>
    </back>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_back()
        
        assert "# References" in converter.markdown_lines
        assert "## Normative References" in converter.markdown_lines


class TestProcessSection:
    """Test section processing."""

    def test_process_section_with_nested_sections(self, tmp_path):
        """Test processing section with nested subsections."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <middle>
        <section anchor="main">
            <name>Main Section</name>
            <t>Main text.</t>
            <section anchor="sub">
                <name>Subsection</name>
                <t>Sub text.</t>
            </section>
        </section>
    </middle>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_middle()
        
        assert "# Main Section" in converter.markdown_lines
        assert "## Subsection" in converter.markdown_lines


class TestProcessList:
    """Test list processing."""

    def test_process_unordered_list(self, tmp_path):
        """Test processing unordered list."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <middle>
        <section>
            <name>Test</name>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </section>
    </middle>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_middle()
        
        assert "- Item 1" in converter.markdown_lines
        assert "- Item 2" in converter.markdown_lines

    def test_process_ordered_list(self, tmp_path):
        """Test processing ordered list."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <middle>
        <section>
            <name>Test</name>
            <ol>
                <li>First</li>
                <li>Second</li>
            </ol>
        </section>
    </middle>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_middle()
        
        assert "1. First" in converter.markdown_lines
        assert "2. Second" in converter.markdown_lines


class TestGetElementText:
    """Test element text extraction with inline elements."""

    def test_get_element_text_with_xref(self, tmp_path):
        """Test extracting text with cross-reference."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <middle>
        <section>
            <name>Test</name>
            <t>See <xref target="intro">Section 1</xref> for details.</t>
        </section>
    </middle>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_middle()
        
        assert "See [Section 1](#intro) for details." in converter.markdown_lines

    def test_get_element_text_with_eref(self, tmp_path):
        """Test extracting text with external reference."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <middle>
        <section>
            <name>Test</name>
            <t>Visit <eref target="https://example.com">our site</eref>.</t>
        </section>
    </middle>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_middle()
        
        assert "Visit [our site](https://example.com)." in converter.markdown_lines

    def test_get_element_text_with_bcp14(self, tmp_path):
        """Test extracting text with BCP14 keywords."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <middle>
        <section>
            <name>Test</name>
            <t>This <bcp14>MUST</bcp14> be done.</t>
        </section>
    </middle>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_middle()
        
        assert "This **MUST** be done." in converter.markdown_lines

    def test_get_element_text_with_em(self, tmp_path):
        """Test extracting text with emphasis."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <middle>
        <section>
            <name>Test</name>
            <t>This is <em>important</em>.</t>
        </section>
    </middle>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_middle()
        
        assert "This is *important*." in converter.markdown_lines

    def test_get_element_text_with_strong(self, tmp_path):
        """Test extracting text with strong emphasis."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <middle>
        <section>
            <name>Test</name>
            <t>This is <strong>critical</strong>.</t>
        </section>
    </middle>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_middle()
        
        assert "This is **critical**." in converter.markdown_lines

    def test_get_element_text_with_tt(self, tmp_path):
        """Test extracting text with teletype (inline code)."""
        xml_content = '''<?xml version="1.0"?>
<rfc>
    <middle>
        <section>
            <name>Test</name>
            <t>Use <tt>code</tt> here.</t>
        </section>
    </middle>
</rfc>'''
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        
        converter = XmlToMdConverter(xml_file)
        converter.tree = etree.parse(str(xml_file))
        converter.root = converter.tree.getroot()
        converter._process_middle()
        
        assert "Use `code` here." in converter.markdown_lines