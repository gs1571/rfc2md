#!/usr/bin/env python3
"""
RFC to Markdown Converter

This script fetches RFC documents from rfc-editor.org in XML format
and converts them to well-formatted Markdown files.

Supports:
- Fetching RFCs by number or using local XML files
- Optional PDF download
- Table of Contents generation
- Preservation of formatting (code blocks, tables, lists)
- Internal and external link handling
"""

import argparse
import logging
import sys
from pathlib import Path

from lib import XmlToMdConverter, download_rfc, normalize_rfc_number, setup_logging


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Convert RFC XML documents to Markdown format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --rfc RFC9514
  %(prog)s --rfc 9514 --pdf --output-dir downloads
  %(prog)s --file examples/rfc9514.xml --output output/custom.md
  %(prog)s --rfc RFC9514 --output-dir output --output rfc9514-custom.md
        """,
    )

    # Input source (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--rfc", type=str, help='RFC number to fetch (e.g., "RFC9514" or "9514")'
    )
    input_group.add_argument("--file", type=str, help="Path to local RFC XML file")

    # Output options
    parser.add_argument(
        "--pdf", action="store_true", help="Download PDF version of the RFC (only with --rfc)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Directory to save downloaded/generated files (default: current directory)",
    )
    parser.add_argument(
        "--output", type=str, help="Custom output filename for the Markdown file (optional)"
    )

    # Logging options
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Validate arguments
    if args.pdf and args.file:
        parser.error("--pdf can only be used with --rfc, not with --file")

    return args


def main():
    """Main entry point for the RFC to Markdown converter."""
    args = parse_arguments()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level)

    logger = logging.getLogger(__name__)

    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir.absolute()}")

    # Process RFC
    if args.rfc:
        rfc_number = normalize_rfc_number(args.rfc)
        logger.info(f"Processing RFC: {rfc_number}")

        # Download RFC files
        xml_file = download_rfc(rfc_number, output_dir, fetch_pdf=args.pdf)
        if xml_file is None:
            logger.error("Failed to download RFC")
            sys.exit(1)

        logger.info(f"Using downloaded file: {xml_file}")
    else:
        xml_file = Path(args.file)
        if not xml_file.exists():
            logger.error(f"File not found: {xml_file}")
            sys.exit(1)
        logger.info(f"Processing local file: {xml_file.absolute()}")

    # Determine output filename
    if args.output:
        output_file = output_dir / args.output
    elif args.rfc:
        rfc_number = normalize_rfc_number(args.rfc)
        output_file = output_dir / f"{rfc_number}.md"
    else:
        output_file = output_dir / f"{xml_file.stem}.md"

    logger.info(f"Output file will be: {output_file.absolute()}")

    # Convert XML to Markdown
    try:
        converter = XmlToMdConverter(xml_file)
        markdown_content = converter.convert()

        # Write Markdown to file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        logger.info(f"Successfully converted to Markdown: {output_file}")

    except Exception as e:
        logger.error(f"Error during conversion: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
