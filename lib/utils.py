"""
Utility functions for RFC to Markdown converter.
"""

import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup
from lxml import etree


def setup_logging(level=logging.INFO):
    """
    Configure logging with specified level.

    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )


def normalize_rfc_number(rfc_input):
    """
    Normalize RFC number input to ensure it starts with 'rfc' prefix.

    Args:
        rfc_input: RFC number as string (e.g., "RFC9514", "9514", "rfc9514")

    Returns:
        Normalized RFC number in lowercase (e.g., "rfc9514")
    """
    # Remove all spaces and convert to lowercase
    rfc_input = rfc_input.replace(" ", "").strip().lower()
    if not rfc_input.startswith("rfc"):
        rfc_input = "rfc" + rfc_input
    return rfc_input


def extract_rfc_references_from_xml(xml_file: Path) -> set[str]:
    """
    Extract RFC references from an RFC XML file.

    Args:
        xml_file: Path to the RFC XML file

    Returns:
        Set of normalized RFC numbers (format "rfcXXXX") found in the file
    """
    rfc_refs: set[str] = set()

    try:
        # Parse the XML file
        tree = etree.parse(str(xml_file))
        root = tree.getroot()

        # Find the back section containing references
        back = root.find("back")
        if back is None:
            return rfc_refs

        # Find all reference elements in the back section
        references = back.findall(".//reference")

        for reference in references:
            # Get the anchor attribute
            anchor = reference.get("anchor", "")

            # Check if anchor starts with "RFC" (case-insensitive)
            if anchor.upper().startswith("RFC"):
                # Extract the RFC number and normalize it
                rfc_number = normalize_rfc_number(anchor)
                rfc_refs.add(rfc_number)

    except etree.XMLSyntaxError as e:
        logging.warning(f"XML syntax error in {xml_file}: {e}")
    except FileNotFoundError:
        logging.warning(f"File not found: {xml_file}")
    except Exception as e:
        logging.warning(f"Error extracting RFC references from {xml_file}: {e}")

    return rfc_refs


def extract_rfc_references_from_html(html_file: Path) -> set[str]:
    """
    Extract RFC references from an RFC HTML file.

    This function parses HTML and looks for RFC references in:
    - Links with href="/rfc/rfcXXXX" pattern
    - Text content matching "RFC XXXX" or "RFC-XXXX" patterns

    Args:
        html_file: Path to the RFC HTML file

    Returns:
        Set of normalized RFC numbers (format "rfcXXXX") found in the file
    """
    rfc_refs: set[str] = set()

    try:
        # Read and parse HTML file
        with open(html_file, encoding="utf-8") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")

        # Method 1: Extract from links with href="/rfc/rfcXXXX"
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if isinstance(href, str):
                # Match patterns like "/rfc/rfc1234" or "/rfc/rfc1234.html"
                match = re.search(r"/rfc/rfc(\d+)", href)
                if match:
                    rfc_number = f"rfc{match.group(1)}"
                    rfc_refs.add(rfc_number)

        # Method 2: Extract from text content matching "RFC XXXX" or "RFC-XXXX"
        text_content = soup.get_text()
        # Find all RFC references in text (RFC followed by number)
        rfc_pattern = re.compile(r"\bRFC[\s-]?(\d+)\b", re.IGNORECASE)
        for match in rfc_pattern.finditer(text_content):
            rfc_number = f"rfc{match.group(1)}"
            rfc_refs.add(rfc_number)

    except FileNotFoundError:
        logging.warning(f"File not found: {html_file}")
    except Exception as e:
        logging.warning(f"Error extracting RFC references from HTML {html_file}: {e}")

    return rfc_refs
