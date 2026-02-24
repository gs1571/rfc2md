"""
RFC downloader module.

This module handles downloading RFC documents from rfc-editor.org.
"""

import logging
import time
from pathlib import Path

import requests

from lib.utils import extract_rfc_references, normalize_rfc_number


def download_rfc_html(rfc_number, output_dir):
    """
    Download RFC HTML from rfc-editor.org.

    Args:
        rfc_number: Normalized RFC number (e.g., "rfc9514")
        output_dir: Path object for output directory

    Returns:
        Path to downloaded HTML file, or None if download failed
    """
    logger = logging.getLogger(__name__)

    # Extract numeric part for URL construction
    rfc_num = rfc_number.replace("rfc", "")

    # Download HTML
    html_url = f"https://www.rfc-editor.org/rfc/rfc{rfc_num}.html"
    html_file = output_dir / f"rfc{rfc_num}.html"

    logger.info(f"Downloading HTML from: {html_url}")

    try:
        response = requests.get(html_url, timeout=30, stream=True)
        response.raise_for_status()

        # Get file size if available
        total_size = int(response.headers.get("content-length", 0))

        # Download with progress indication
        downloaded = 0
        chunk_size = 8192
        start_time = time.time()

        with open(html_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        logger.debug(
                            f"Downloaded: {downloaded}/{total_size} bytes ({percent:.1f}%)"
                        )

        elapsed = time.time() - start_time
        logger.info(
            f"HTML downloaded successfully: {html_file} ({downloaded} bytes in {elapsed:.2f}s)"
        )

        return html_file

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.error(f"RFC HTML not found: {rfc_number} (404 error)")
        else:
            logger.error(f"HTTP error downloading HTML: {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Network connection error: {e}")
        return None
    except requests.exceptions.Timeout as e:
        logger.error(f"Download timeout: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading HTML: {e}")
        return None
    except OSError as e:
        logger.error(f"Error writing file {html_file}: {e}")
        return None


def download_rfc(rfc_number, output_dir, fetch_pdf=False):
    """
    Download RFC XML and optionally PDF from rfc-editor.org.
    Falls back to HTML if XML is not available.

    Args:
        rfc_number: Normalized RFC number (e.g., "rfc9514")
        output_dir: Path object for output directory
        fetch_pdf: Whether to download PDF version

    Returns:
        Path to downloaded XML or HTML file, or None if download failed
    """
    logger = logging.getLogger(__name__)

    # Extract numeric part for URL construction
    rfc_num = rfc_number.replace("rfc", "")

    # Download XML
    xml_url = f"https://www.rfc-editor.org/rfc/rfc{rfc_num}.xml"
    xml_file = output_dir / f"rfc{rfc_num}.xml"

    logger.info(f"Downloading XML from: {xml_url}")

    try:
        response = requests.get(xml_url, timeout=30, stream=True)
        response.raise_for_status()

        # Get file size if available
        total_size = int(response.headers.get("content-length", 0))

        # Download with progress indication
        downloaded = 0
        chunk_size = 8192
        start_time = time.time()

        with open(xml_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        logger.debug(
                            f"Downloaded: {downloaded}/{total_size} bytes ({percent:.1f}%)"
                        )

        elapsed = time.time() - start_time
        logger.info(
            f"XML downloaded successfully: {xml_file} ({downloaded} bytes in {elapsed:.2f}s)"
        )

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"RFC XML not found: {rfc_number} (404 error), trying HTML fallback")
            # Try HTML fallback
            html_file = download_rfc_html(rfc_number, output_dir)
            if html_file:
                return html_file
            logger.error(f"RFC not found in any format: {rfc_number}")
        else:
            logger.error(f"HTTP error downloading XML: {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Network connection error: {e}")
        return None
    except requests.exceptions.Timeout as e:
        logger.error(f"Download timeout: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading XML: {e}")
        return None
    except OSError as e:
        logger.error(f"Error writing file {xml_file}: {e}")
        return None

    # Download PDF if requested
    if fetch_pdf:
        pdf_file = output_dir / f"rfc{rfc_num}.pdf"

        # Try primary PDF URL first
        pdf_url = f"https://www.rfc-editor.org/rfc/rfc{rfc_num}.pdf"
        logger.info(f"Downloading PDF from: {pdf_url}")

        try:
            response = requests.get(pdf_url, timeout=30, stream=True)
            response.raise_for_status()

            # Download PDF
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            start_time = time.time()

            with open(pdf_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            logger.debug(
                                f"Downloaded: {downloaded}/{total_size} bytes ({percent:.1f}%)"
                            )

            elapsed = time.time() - start_time
            logger.info(
                f"PDF downloaded successfully: {pdf_file} ({downloaded} bytes in {elapsed:.2f}s)"
            )

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # Try fallback URL
                pdf_url_fallback = f"https://www.rfc-editor.org/rfc/rfc{rfc_num}.txt.pdf"
                logger.info(f"Primary PDF not found, trying fallback: {pdf_url_fallback}")

                try:
                    response = requests.get(pdf_url_fallback, timeout=30, stream=True)
                    response.raise_for_status()

                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0
                    start_time = time.time()

                    with open(pdf_file, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)

                    elapsed = time.time() - start_time
                    logger.info(
                        f"PDF downloaded successfully (fallback): {pdf_file} ({downloaded} bytes in {elapsed:.2f}s)"
                    )

                except requests.exceptions.RequestException as e2:
                    logger.warning(f"PDF download failed (both URLs tried): {e2}")
            else:
                logger.warning(f"HTTP error downloading PDF: {e}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error downloading PDF: {e}")
        except OSError as e:
            logger.warning(f"Error writing PDF file {pdf_file}: {e}")

    return xml_file


def download_rfc_recursive(
    rfc_number: str,
    output_dir: Path,
    fetch_pdf: bool = False,
    max_depth: int = 1,
    processed: set[str] | None = None,
) -> dict[str, Path]:
    """
    Recursively download RFC and all referenced RFCs.

    Args:
        rfc_number: RFC number to download (will be normalized)
        output_dir: Directory to save downloaded files
        fetch_pdf: Whether to download PDF files
        max_depth: Maximum recursion depth (default: 1)
        processed: Set of already processed RFCs (for internal use)

    Returns:
        Dictionary mapping RFC numbers to their XML file paths
    """
    logger = logging.getLogger(__name__)

    # Initialize processed set if not provided
    if processed is None:
        processed = set()

    # Normalize RFC number
    rfc_number = normalize_rfc_number(rfc_number)

    # Check if already processed
    if rfc_number in processed:
        logger.debug(f"RFC {rfc_number} already processed, skipping")
        return {}

    # Add to processed set
    processed.add(rfc_number)

    # Initialize result dictionary
    result: dict[str, Path] = {}

    # Determine XML file path
    xml_file = output_dir / f"{rfc_number}.xml"

    # Check if file exists
    if xml_file.exists():
        logger.info(f"RFC {rfc_number} already downloaded, skipping download")
    else:
        # Download the RFC
        logger.info(f"Downloading RFC {rfc_number}...")
        downloaded_file = download_rfc(rfc_number, output_dir, fetch_pdf)

        if downloaded_file is None:
            logger.error(f"Failed to download RFC {rfc_number}")
            return result

    # Add to result
    result[rfc_number] = xml_file

    # Extract references if max_depth > 0
    if max_depth > 0:
        try:
            references = extract_rfc_references(xml_file)
            logger.info(
                f"Found {len(references)} RFC reference(s) in {rfc_number} (depth {max_depth})"
            )

            # Recursively download referenced RFCs
            for ref_rfc in references:
                logger.info(f"Found reference to RFC {ref_rfc} (depth {max_depth})")
                ref_result = download_rfc_recursive(
                    ref_rfc, output_dir, fetch_pdf, max_depth - 1, processed
                )
                result.update(ref_result)

        except Exception as e:
            logger.warning(f"Error extracting references from {rfc_number}: {e}")

    return result
