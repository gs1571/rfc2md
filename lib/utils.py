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


def extract_rfc_numbers_from_markdown(md_file: Path) -> set[str]:
    """
    Extract RFC numbers from a Markdown file.

    This function parses Markdown content and looks for RFC references in various formats:
    - RFC 9514 or RFC9514 (with/without space, case-insensitive)
    - [RFC 9514](...) (in markdown links)
    - rfc9514.md or rfc9514.xml (as filenames)
    - RFC-9514 (with hyphen)
    - rfc9514. (with trailing dot)

    Args:
        md_file: Path to the Markdown file

    Returns:
        Set of normalized RFC numbers (format "rfcXXXX") found in the file
    """
    rfc_refs: set[str] = set()

    try:
        # Read markdown file
        with open(md_file, encoding="utf-8") as f:
            md_content = f.read()

        # Comprehensive regex pattern to match various RFC formats
        # Pattern explanation:
        # \b - word boundary to avoid false matches
        # [Rr][Ff][Cc] - case-insensitive "RFC"
        # [\s-]? - optional space or hyphen
        # (\d+) - capture group for RFC number (one or more digits)
        # (?:\.(?:md|xml|html))? - optional file extension (.md, .xml, .html)
        # (?:\.)? - optional trailing dot
        # \b - word boundary
        rfc_pattern = re.compile(r"\b[Rr][Ff][Cc][\s-]?(\d+)(?:\.(?:md|xml|html))?(?:\.)?\b")

        # Find all RFC references
        for match in rfc_pattern.finditer(md_content):
            rfc_number = f"rfc{match.group(1)}"
            rfc_refs.add(rfc_number)

    except FileNotFoundError:
        logging.warning(f"File not found: {md_file}")
    except Exception as e:
        logging.warning(f"Error extracting RFC numbers from markdown {md_file}: {e}")

    return rfc_refs


def build_index_file(output_dir: Path) -> None:
    """
    Build index.md file with sorted list of all RFCs in directory.

    Args:
        output_dir: Directory containing RFC markdown files
    """
    logger = logging.getLogger(__name__)

    # Find all RFC markdown files (excluding index.md)
    rfc_files = []
    for md_file in output_dir.glob("rfc*.md"):
        if md_file.name != "index.md":
            # Extract RFC number from filename
            match = re.match(r"rfc(\d+)\.md", md_file.name)
            if match:
                rfc_number = int(match.group(1))
                rfc_files.append((rfc_number, md_file))

    if not rfc_files:
        logger.warning(f"No RFC markdown files found in {output_dir}")
        return

    # Sort by RFC number
    rfc_files.sort(key=lambda x: x[0])

    # Build index content
    index_lines = [
        "# RFC Index",
        "",
        "This index contains all RFC documents converted to Markdown format.",
        "",
    ]

    for rfc_number, md_file in rfc_files:
        rfc_name = f"rfc{rfc_number}"
        title = ""

        # Try to extract title from XML file first
        xml_file = output_dir / f"{rfc_name}.xml"
        if xml_file.exists():
            try:
                tree = etree.parse(str(xml_file))
                root = tree.getroot()
                front = root.find("front")
                if front is not None:
                    title_elem = front.find("title")
                    if title_elem is not None and title_elem.text:
                        title = title_elem.text.strip()
            except Exception as e:
                logger.debug(f"Could not extract title from {xml_file}: {e}")

        # If no XML or no title, try HTML file
        if not title:
            html_file = output_dir / f"{rfc_name}.html"
            if html_file.exists():
                try:
                    with open(html_file, encoding="utf-8") as f:
                        html_content = f.read()
                    soup = BeautifulSoup(html_content, "html.parser")

                    # Try to get title from <title> tag
                    title_tag = soup.find("title")
                    if title_tag and title_tag.string:
                        title = title_tag.string.strip()
                        # Remove "RFC XXXX - " prefix if present
                        title = re.sub(r"^RFC\s*\d+\s*[-:]\s*", "", title, flags=re.IGNORECASE)

                    # If no title tag, try first <h1>
                    if not title:
                        h1_tag = soup.find("h1")
                        if h1_tag:
                            title = h1_tag.get_text().strip()
                            title = re.sub(r"^RFC\s*\d+\s*[-:]\s*", "", title, flags=re.IGNORECASE)
                except Exception as e:
                    logger.debug(f"Could not extract title from {html_file}: {e}")

        # Format the index entry
        if title:
            index_lines.append(f"- [RFC {rfc_number}]({md_file.name}): {title}")
        else:
            index_lines.append(f"- [RFC {rfc_number}]({md_file.name}):")

    # Write index file
    index_file = output_dir / "index.md"
    index_content = "\n".join(index_lines) + "\n"

    with open(index_file, "w", encoding="utf-8") as f:
        f.write(index_content)

    logger.info(f"Generated index file: {index_file} with {len(rfc_files)} RFCs")
