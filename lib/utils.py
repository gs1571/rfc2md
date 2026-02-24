"""
Utility functions for RFC to Markdown converter.
"""

import logging


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
