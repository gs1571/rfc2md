"""
RFC to Markdown Converter Library

This package contains modules for converting RFC XML and HTML documents to Markdown format.
"""

from .converter import XmlToMdConverter
from .downloader import download_rfc, download_rfc_html, download_rfc_recursive
from .html_converter import HtmlToMdConverter
from .utils import normalize_rfc_number, setup_logging

__all__ = [
    "XmlToMdConverter",
    "HtmlToMdConverter",
    "download_rfc",
    "download_rfc_html",
    "download_rfc_recursive",
    "normalize_rfc_number",
    "setup_logging",
]
