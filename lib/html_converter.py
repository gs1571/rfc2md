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

        # TODO: Implement remaining stages
        return text_without_links

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