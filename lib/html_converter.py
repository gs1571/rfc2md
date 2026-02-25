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

        # Stage 1: Extract raw text and remove links
        raw_text = self._extract_raw_text()
        text_without_links = self._remove_links(raw_text)

        # Stage 2: Remove page breaks
        text_without_page_breaks = self._remove_page_breaks(text_without_links)

        # Stage 3: Collapse multiple empty lines
        text_collapsed = self._collapse_empty_lines(text_without_page_breaks)

        # Stage 4: Extract and format Table of Contents
        text_with_formatted_toc, formatted_toc = self._extract_toc(text_collapsed)

        # TODO: Implement remaining stages
        return text_with_formatted_toc

    def _extract_raw_text(self):
        """
        Extract all text from <pre> blocks in the HTML.

        This method finds all <pre> blocks in the HTML document and extracts
        their text content, combining them into a single text document.

        Returns:
            String containing all extracted text from pre blocks
        """
        self.logger.debug("Extracting raw text from pre blocks")

        # Find all pre blocks
        pre_blocks = self.soup.find_all("pre")
        self.logger.debug(f"Found {len(pre_blocks)} pre blocks")

        # Extract text from each pre block
        text_parts = []
        for pre in pre_blocks:
            text = pre.get_text()
            text_parts.append(text)

        # Combine all text parts
        full_text = "\n".join(text_parts)
        self.logger.debug(f"Extracted {len(full_text)} characters of text")

        return full_text

    def _remove_links(self, text):
        """
        Remove all HTML link tags from text while preserving link text.

        This method removes <a> tags but keeps the text content of the links.
        It handles both opening and closing tags.

        Args:
            text: Input text containing HTML link tags

        Returns:
            String with HTML link tags removed but text preserved
        """
        self.logger.debug("Removing HTML links from text")

        # Remove opening <a> tags with any attributes
        text = re.sub(r'<a[^>]*>', '', text)

        # Remove closing </a> tags
        text = re.sub(r'</a>', '', text)

        self.logger.debug("HTML links removed")
        return text

    def _remove_page_breaks(self, text):
        """
        Remove RFC page break patterns from text.

        This method removes pagination artifacts including:
        - Author/page number headers (e.g., "Author, et al.  Standards Track  [Page N]")
        - RFC title headers (e.g., "RFC NNNN  Title  Month YYYY")
        - Page separator lines (lines with only dashes)

        Args:
            text: Input text containing page breaks

        Returns:
            String with page breaks removed
        """
        self.logger.debug("Removing page breaks from text")

        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Skip lines with "Standards Track" and "[Page N]" pattern
            if re.search(r'Standards Track\s+\[Page \d+\]', line):
                continue

            # Skip lines with "RFC NNNN" and date pattern
            if re.search(r'^RFC \d+\s+.+\s+\w+ \d{4}$', line):
                continue

            # Skip lines that are only dashes or form feed characters
            if re.match(r'^[\s\-\f]+$', line) and len(line.strip('-').strip()) == 0:
                continue

            cleaned_lines.append(line)

        result = '\n'.join(cleaned_lines)
        self.logger.debug(f"Removed {len(lines) - len(cleaned_lines)} page break lines")

        return result

    def _collapse_empty_lines(self, text):
        """
        Collapse multiple consecutive empty lines into a single empty line.

        This method finds sequences of three or more newlines and replaces them
        with exactly two newlines (one empty line), preserving document structure
        while removing excessive whitespace.

        Args:
            text: Input text with potential multiple empty lines

        Returns:
            String with multiple empty lines collapsed to single empty lines
        """
        self.logger.debug("Collapsing multiple empty lines")

        # Replace three or more consecutive newlines with exactly two
        # This preserves single empty lines while removing multiple ones
        result = re.sub(r'\n\n\n+', '\n\n', text)

        self.logger.debug("Empty lines collapsed")
        return result

    def _extract_toc(self, text):
        """
        Extract and format the Table of Contents from text.

        This method finds the TOC section, extracts it from the main text,
        and formats each entry as a monospace markdown link with preserved indentation.

        Args:
            text: Input text containing the Table of Contents

        Returns:
            Tuple of (text_with_formatted_toc, formatted_toc) where:
            - text_with_formatted_toc: Text with old TOC replaced by formatted TOC
            - formatted_toc: Formatted TOC as markdown string (for reference)
        """
        self.logger.debug("Extracting Table of Contents")

        lines = text.split('\n')
        toc_start = -1
        toc_end = -1

        # Find TOC start
        for i, line in enumerate(lines):
            if line.strip().startswith('Table of Contents'):
                toc_start = i
                break

        if toc_start == -1:
            self.logger.debug("No Table of Contents found")
            return text, ""

        # Find TOC end - next line that starts without leading spaces (next section)
        for i in range(toc_start + 1, len(lines)):
            line = lines[i]
            # TOC ends when we hit a line that starts without spaces and is not empty
            # and is not a TOC entry (doesn't have dots and page numbers)
            if line and not line[0].isspace() and not re.search(r'\.+\s*\d+$', line):
                toc_end = i
                break

        if toc_end == -1:
            toc_end = len(lines)

        # Extract TOC lines
        toc_lines = lines[toc_start:toc_end]

        # Format TOC entries
        formatted_entries = ['`Table of Contents`', '']
        for line in toc_lines[1:]:  # Skip "Table of Contents" header
            if line.strip():  # Skip empty lines
                formatted_entry = self._format_toc_entry(line)
                if formatted_entry:
                    formatted_entries.append(formatted_entry)
                    formatted_entries.append('')  # Add empty line between entries

        formatted_toc = '\n'.join(formatted_entries)
        
        # Replace old TOC with formatted TOC in the text
        text_with_formatted_toc = '\n'.join(lines[:toc_start] + [formatted_toc] + lines[toc_end:])

        self.logger.debug(f"Extracted TOC with {len(formatted_entries)} entries")

        return text_with_formatted_toc, formatted_toc

    def _format_toc_entry(self, line):
        """
        Format a single TOC entry as monospace markdown with clickable section link.

        This method:
        1. Preserves leading spaces from the original line
        2. Removes trailing dots and page numbers from anywhere in the line
        3. Finds section number pattern anywhere in the line and creates anchor
        4. Handles multi-line entries (continuation lines without section numbers)

        Args:
            line: A single TOC entry line (may be continuation line)

        Returns:
            Formatted markdown string or None if line is empty after cleaning
        """
        # Extract leading spaces
        leading_spaces = ''
        for char in line:
            if char == ' ':
                leading_spaces += char
            else:
                break

        # Remove trailing dots and page numbers from the end: \.+\s*\d*$
        line_cleaned = re.sub(r'\.+\s*\d*$', '', line).strip()

        if not line_cleaned:
            return None

        # Try to find section number pattern ANYWHERE in the line
        # Pattern: digits separated by dots, followed by dot and space
        match = re.search(r'(\d+(?:\.\d+)*)\.\s+', line_cleaned)

        if match:
            # This line has a section number - create anchor link
            section_num = match.group(1)
            # Get text after the section number
            section_title = line_cleaned[match.end():]
            
            # Create anchor ID: section-1-1 (replace dots with dashes)
            anchor_id = f"section-{section_num.replace('.', '-')}"

            # Format as: `   `[`1`](#section-1)`. Title text`
            formatted = f"`{leading_spaces}`[`{section_num}`](#{anchor_id})`. {section_title}`"
        else:
            # This is a continuation line without section number
            # Just format it as monospace with preserved indentation
            formatted = f"`{leading_spaces}{line_cleaned}`"

        return formatted