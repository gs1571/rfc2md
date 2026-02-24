"""
HTML to Markdown converter module.

This module contains the HtmlToMdConverter class for converting old RFC HTML files
to well-formatted Markdown when XML versions are not available.
"""

import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup


class HtmlToMdConverter:
    """
    Converter class for transforming RFC HTML documents to Markdown format.

    This class handles parsing of old RFC HTML files and conversion to well-formatted
    Markdown, including metadata extraction, page break removal, code block detection,
    and link preservation.
    """

    def __init__(self, html_file):
        """
        Initialize the converter with an HTML file.

        Args:
            html_file: Path to the RFC HTML file
        """
        self.html_file = Path(html_file)
        self.logger = logging.getLogger(__name__)
        self.soup = None
        self.markdown_lines = []
        self.metadata = {}
        self.sections = []

    def convert(self):
        """
        Convert the RFC HTML to Markdown format.

        Returns:
            String containing the complete Markdown document
        """
        self.logger.info(f"Parsing HTML file: {self.html_file}")

        # Parse HTML
        try:
            with open(self.html_file, "r", encoding="utf-8") as f:
                html_content = f.read()
            self.soup = BeautifulSoup(html_content, "html.parser")
        except Exception as e:
            raise ValueError(f"Error parsing HTML: {e}") from e

        # Extract metadata from HTML meta tags and header section
        self._extract_metadata()

        # Build section hierarchy from span elements
        self._extract_sections()

        # Process document sections
        self._process_document()

        return "\n".join(self.markdown_lines)

    def _extract_metadata(self):
        """
        Extract metadata from HTML meta tags and header section.

        Populates self.metadata with RFC number, title, authors, date, etc.
        """
        # Extract from meta tags
        meta_tags = self.soup.find_all("meta")
        for meta in meta_tags:
            name = meta.get("name", "")
            content = meta.get("content", "")
            if name and content:
                self.metadata[name] = content

        # Extract title from <title> tag
        title_tag = self.soup.find("title")
        if title_tag and title_tag.string:
            self.metadata["title"] = title_tag.string.strip()

        # Extract RFC number and other info from initial pre block
        pre_blocks = self.soup.find_all("pre")
        if pre_blocks:
            first_pre = pre_blocks[0]
            text = first_pre.get_text()
            
            # Try to extract RFC number
            rfc_match = re.search(r"RFC\s+(\d+)", text, re.IGNORECASE)
            if rfc_match:
                self.metadata["rfc_number"] = rfc_match.group(1)
            
            # Try to extract category (Standards Track, Informational, etc.)
            category_match = re.search(
                r"(Standards Track|Informational|Best Current Practice|Experimental|Historic)",
                text
            )
            if category_match:
                self.metadata["category"] = category_match.group(1)
            
            # Try to extract date
            date_match = re.search(
                r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
                text
            )
            if date_match:
                self.metadata["date"] = f"{date_match.group(1)} {date_match.group(2)}"

    def _extract_sections(self):
        """
        Build section hierarchy from span class="h1", "h2", etc. elements.

        Populates self.sections with section information including number, title, and anchor.
        """
        # Find all section headers (h1, h2, h3, etc.)
        for level in range(1, 7):
            headers = self.soup.find_all("span", class_=f"h{level}")
            for header in headers:
                # Extract section number and title
                text = header.get_text().strip()
                
                # Find associated anchor
                anchor_elem = header.find("a", class_="selflink")
                anchor = ""
                if anchor_elem:
                    anchor = anchor_elem.get("id", "") or anchor_elem.get("name", "")
                
                # Parse section number and title
                # Format is typically: "3.2.1  Section Title" or "Appendix A.  Title"
                section_info = {
                    "level": level,
                    "text": text,
                    "anchor": anchor,
                    "element": header
                }
                
                self.sections.append(section_info)

    def _remove_page_breaks(self, text):
        """
        Remove page headers, footers, and page break markers from text.

        Args:
            text: Text content with page breaks

        Returns:
            Text with page breaks removed and paragraphs merged
        """
        lines = text.split("\n")
        cleaned_lines = []
        
        # Regex patterns for page break detection
        page_header_pattern = re.compile(
            r"^[A-Za-z,\s\.]+\s+(Standards Track|Informational|Best Current Practice|Experimental|Historic)\s+\[Page \d+\]$"
        )
        page_footer_pattern = re.compile(
            r"^RFC \d+\s+.*\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}$"
        )
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a page header
            if page_header_pattern.match(line.strip()):
                i += 1
                continue
            
            # Check if this is a page footer
            if page_footer_pattern.match(line.strip()):
                i += 1
                continue
            
            # Check for form feed or page break markers
            if line.strip() in ["", "\f", "\x0c"]:
                # Skip empty lines that are likely page breaks
                # But preserve intentional paragraph breaks
                if i > 0 and i < len(lines) - 1:
                    # Check if previous and next lines are content
                    prev_line = cleaned_lines[-1] if cleaned_lines else ""
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        # If both prev and next have content, this might be a paragraph break
                        if prev_line.strip() and next_line and not page_header_pattern.match(next_line):
                            cleaned_lines.append("")
                i += 1
                continue
            
            cleaned_lines.append(line)
            i += 1
        
        # Merge split paragraphs that were broken by page breaks
        merged_lines = []
        i = 0
        while i < len(cleaned_lines):
            line = cleaned_lines[i]
            
            # Check if line ends mid-sentence (no period, comma, colon, or other terminal punctuation)
            if line.strip() and i + 1 < len(cleaned_lines):
                next_line = cleaned_lines[i + 1].strip()
                
                # If current line doesn't end with terminal punctuation and next line exists
                # and is not empty, and doesn't start a new section, merge them
                if (not re.search(r"[.,:;!?)\]]$", line.strip()) and
                    next_line and
                    not next_line.startswith("#") and
                    not re.match(r"^\d+\.?\s", next_line)):  # Not a numbered item
                    
                    # Merge with next line
                    merged_lines.append(line.rstrip() + " " + next_line)
                    i += 2
                    continue
            
            merged_lines.append(line)
            i += 1
        
        return "\n".join(merged_lines)

    def _is_ascii_art(self, lines):
        """
        Detect if lines contain ASCII art diagrams.

        Args:
            lines: List of text lines

        Returns:
            True if lines appear to be ASCII art
        """
        if not lines or len(lines) < 2:
            return False
        
        # Count lines with box drawing characters
        box_char_count = 0
        for line in lines:
            if re.search(r"[+\-|=]{3,}", line):
                box_char_count += 1
        
        # If more than 30% of lines have box characters, likely ASCII art
        return box_char_count / len(lines) > 0.3

    def _is_protocol_format(self, lines):
        """
        Detect if lines contain protocol field definitions (bit diagrams).

        Args:
            lines: List of text lines

        Returns:
            True if lines appear to be protocol format diagrams
        """
        if not lines or len(lines) < 2:
            return False
        
        # Look for bit field markers like "0 1 2 3" followed by "+-+-+-+"
        for i in range(len(lines) - 1):
            line = lines[i]
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            
            # Check for bit position markers
            if re.search(r"\b0\s+1\s+2\s+3\b", line):
                return True
            
            # Check for bit field separators
            if re.search(r"\+-\+-\+-\+", line) or re.search(r"\+-\+-\+-\+", next_line):
                return True
        
        return False

    def _is_ascii_table(self, lines):
        """
        Detect if lines contain ASCII art tables.

        Args:
            lines: List of text lines

        Returns:
            True if lines appear to be ASCII tables
        """
        if not lines or len(lines) < 3:
            return False
        
        # Look for table borders with +---+ pattern
        border_count = 0
        pipe_count = 0
        
        for line in lines:
            if re.search(r"\+[-=]+\+", line):
                border_count += 1
            if line.count("|") >= 2:
                pipe_count += 1
        
        # Tables typically have borders and multiple lines with pipes
        return border_count >= 2 and pipe_count >= 2

    def _detect_lists(self, lines):
        """
        Identify list structures from indentation patterns.

        Args:
            lines: List of text lines

        Returns:
            List of tuples (line_index, list_type, indent_level)
            where list_type is 'ul' (unordered), 'ol' (ordered), or 'dl' (definition)
        """
        list_items = []
        
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            
            # Detect unordered lists (-, *, o)
            if re.match(r"^[-*o]\s+", stripped):
                list_items.append((i, "ul", indent))
            
            # Detect ordered lists (1., 1), etc.)
            elif re.match(r"^\d+[.)]\s+", stripped):
                list_items.append((i, "ol", indent))
            
            # Detect definition lists (term followed by indented description)
            elif i + 1 < len(lines):
                next_line = lines[i + 1]
                next_stripped = next_line.lstrip()
                next_indent = len(next_line) - len(next_stripped)
                
                # If current line is not indented but next is, might be definition
                if indent == 0 and next_indent > 0 and stripped and not re.match(r"^[-*o\d]", stripped):
                    list_items.append((i, "dl", 0))
        
        return list_items

    def _detect_code_blocks(self, text):
        """
        Identify code blocks vs. prose using heuristics.

        Args:
            text: Text content to analyze

        Returns:
            List of tuples (start_line, end_line, block_type)
            where block_type is 'code', 'table', 'diagram', or 'prose'
        """
        lines = text.split("\n")
        blocks = []
        i = 0
        
        while i < len(lines):
            if i >= len(lines):
                break
                
            line = lines[i]
            matched = False
            
            # Check for line-numbered code (e.g., "1 | code")
            if re.match(r"^\s*\d+\s*\|", line):
                start = i
                i += 1
                while i < len(lines) and re.match(r"^\s*\d+\s*\|", lines[i]):
                    i += 1
                blocks.append((start, i - 1, "code"))
                matched = True
            
            # Check for ASCII tables (simple detection)
            elif re.search(r"\+[-=]+\+", line):
                start = i
                i += 1
                # Look ahead up to 20 lines for table content
                end = min(i + 20, len(lines))
                while i < end and re.search(r"[+|]", lines[i]):
                    i += 1
                if i > start + 2:  # At least 3 lines for a table
                    blocks.append((start, i - 1, "table"))
                    matched = True
            
            # Check for consistent indentation (code blocks)
            elif line.startswith("    ") or line.startswith("\t"):
                start = i
                indent_count = 1
                i += 1
                # Look ahead up to 50 lines
                end = min(i + 50, len(lines))
                while i < end:
                    if lines[i].startswith("    ") or lines[i].startswith("\t"):
                        indent_count += 1
                        i += 1
                    elif not lines[i].strip():
                        # Empty line, continue
                        i += 1
                    else:
                        # Non-indented, non-empty line - end of block
                        break
                
                # If we have 3+ consistently indented lines, it's likely code
                if indent_count >= 3:
                    blocks.append((start, i - 1, "code"))
                    matched = True
            
            if not matched:
                i += 1
        
        return blocks

    def _convert_links(self, element):
        """
        Transform HTML links to Markdown format.

        Args:
            element: BeautifulSoup element to process for links

        Returns:
            Text with converted links
        """
        # Find all links in the element
        links = element.find_all("a") if element else []
        
        for link in links:
            href = link.get("href", "")
            text = link.get_text().strip()
            
            if not href:
                continue
            
            # Handle internal section links: #section-3.2.1 → #section-3-2-1
            if href.startswith("#"):
                # Replace dots with hyphens in anchor
                anchor = href[1:].replace(".", "-")
                markdown_link = f"[{text}](#{anchor})"
                link.replace_with(markdown_link)
            
            # Handle RFC references: ./rfc5305 → full URL
            elif href.startswith("./rfc") or href.startswith("rfc"):
                rfc_num = re.search(r"rfc(\d+)", href, re.IGNORECASE)
                if rfc_num:
                    rfc_number = rfc_num.group(1)
                    full_url = f"https://www.rfc-editor.org/rfc/rfc{rfc_number}"
                    markdown_link = f"[{text or f'RFC{rfc_number}'}]({full_url})"
                    link.replace_with(markdown_link)
            
            # Handle external links: preserve as-is
            elif href.startswith("http://") or href.startswith("https://"):
                markdown_link = f"[{text}]({href})"
                link.replace_with(markdown_link)
            
            # Handle relative links
            else:
                markdown_link = f"[{text}]({href})"
                link.replace_with(markdown_link)
        
        return element.get_text() if element else ""

    def _normalize_text(self, text, preserve_code_blocks=False):
        """
        Clean up text content while preserving intentional formatting.

        Args:
            text: Text content to normalize
            preserve_code_blocks: If True, preserve line breaks in code blocks

        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = text.split("\n")
        normalized_lines = []
        
        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()
            
            # Preserve empty lines (paragraph breaks)
            if not line.strip():
                normalized_lines.append("")
                continue
            
            normalized_lines.append(line)
        
        # Remove multiple consecutive empty lines
        result_lines = []
        prev_empty = False
        for line in normalized_lines:
            if not line.strip():
                if not prev_empty:
                    result_lines.append(line)
                prev_empty = True
            else:
                result_lines.append(line)
                prev_empty = False
        
        return "\n".join(result_lines)

    def _process_document(self):
        """
        Process the entire document and generate Markdown output.

        This orchestrates all conversion steps in the correct order.
        """
        # Add title and metadata
        if "title" in self.metadata:
            self.markdown_lines.append(f"# {self.metadata['title']}")
            self.markdown_lines.append("")
        
        if "rfc_number" in self.metadata:
            rfc_info = f"**RFC {self.metadata['rfc_number']}**"
            if "category" in self.metadata:
                rfc_info += f" - {self.metadata['category']}"
            self.markdown_lines.append(rfc_info)
            self.markdown_lines.append("")
        
        if "date" in self.metadata:
            self.markdown_lines.append(f"**Date:** {self.metadata['date']}")
            self.markdown_lines.append("")
        
        # For HTML RFCs, just extract and clean the text from pre blocks
        # This is a simplified approach - full implementation would need
        # more sophisticated parsing
        pre_blocks = self.soup.find_all("pre") if self.soup else []
        
        if pre_blocks:
            # Get all text from first pre block (main content)
            main_pre = pre_blocks[0]
            text = main_pre.get_text()
            
            # Remove page breaks
            text = self._remove_page_breaks(text)
            
            # Simple approach: just output the cleaned text
            # A full implementation would parse sections, detect code blocks, etc.
            self.markdown_lines.append(text)