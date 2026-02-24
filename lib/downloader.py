"""
RFC downloader module.

This module handles downloading RFC documents from rfc-editor.org.
"""

import logging
import time

import requests


def download_rfc(rfc_number, output_dir, fetch_pdf=False):
    """
    Download RFC XML and optionally PDF from rfc-editor.org.

    Args:
        rfc_number: Normalized RFC number (e.g., "rfc9514")
        output_dir: Path object for output directory
        fetch_pdf: Whether to download PDF version

    Returns:
        Path to downloaded XML file, or None if download failed
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
            logger.error(f"RFC not found: {rfc_number} (404 error)")
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
