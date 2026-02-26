#!/usr/bin/env python3
"""
RFC to Markdown Converter

This script fetches RFC documents from rfc-editor.org in XML format
and converts them to well-formatted Markdown files.

Supports:
- Fetching RFCs by number (single or multiple) or using local XML files
- Optional download of additional formats (PDF, text, XML, HTML)
- Recursive download of referenced RFCs
- Table of Contents generation
- Preservation of formatting (code blocks, tables, lists)
- Internal and external link handling
"""

import argparse
import logging
import sys
from pathlib import Path

from lib import (
    HtmlToMdConverter,
    XmlToMdConverter,
    download_rfc,
    download_rfc_recursive,
    normalize_rfc_number,
    setup_logging,
)


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
  %(prog)s --rfc 9514 --extra pdf text --output-dir downloads
  %(prog)s --rfc 9514 9552 --extra pdf --output-dir downloads
  %(prog)s --file examples/rfc9514.xml --output output/custom.md
  %(prog)s --rfc RFC9514 --output-dir output --output rfc9514-custom.md
  %(prog)s --rfc 9514 --recursive --extra xml html --max-depth 2
        """,
    )

    # Input source (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--rfc",
        type=str,
        nargs="+",
        help='RFC number(s) to fetch (e.g., "RFC9514" or "9514"). Multiple RFCs can be specified.',
    )
    input_group.add_argument("--file", type=str, help="Path to local RFC XML file")

    # Output options
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Directory to save downloaded/generated files (default: current directory)",
    )
    parser.add_argument(
        "--output", type=str, help="Custom output filename for the Markdown file (optional)"
    )
    parser.add_argument(
        "--extra",
        nargs="*",
        choices=["pdf", "text", "xml", "html"],
        help="Download additional format(s) of the RFC (only with --rfc). "
        "Options: pdf, text, xml, html. Can specify multiple formats.",
    )

    # Recursive download options
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively download all RFCs referenced in the specified RFC",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=1,
        help="Maximum recursion depth for --recursive (default: 1)",
    )

    # Logging options
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Validate arguments
    if args.extra and args.file:
        parser.error("--extra can only be used with --rfc, not with --file")

    if args.recursive and args.file:
        parser.error("--recursive can only be used with --rfc, not with --file")

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
        # args.rfc is now a list, process each RFC
        rfc_numbers = [normalize_rfc_number(rfc) for rfc in args.rfc]
        logger.info(f"Processing RFC(s): {', '.join(rfc_numbers)}")

        # Prepare extra_formats list
        extra_formats = args.extra if args.extra else []

        # Check if recursive download is requested
        if args.recursive:
            # Process each RFC with recursive download
            all_rfc_files = {}
            for rfc_number in rfc_numbers:
                logger.info(
                    f"Starting recursive download for RFC {rfc_number} with max depth {args.max_depth}"
                )
                rfc_files = download_rfc_recursive(
                    rfc_number, output_dir, extra_formats, args.max_depth
                )

                if not rfc_files:
                    logger.error(f"Failed to download RFC {rfc_number}")
                else:
                    all_rfc_files.update(rfc_files)

            if not all_rfc_files:
                logger.error("Failed to download any RFCs")
                sys.exit(1)

            logger.info(f"Downloaded {len(all_rfc_files)} RFC(s), starting conversion...")

            # Convert all downloaded RFCs
            success_count = 0
            total_count = len(all_rfc_files)

            for rfc_num in sorted(all_rfc_files.keys()):
                primary_file, extra_files = all_rfc_files[rfc_num]
                output_file = output_dir / f"{rfc_num}.md"

                try:
                    logger.info(f"Converting {rfc_num} to Markdown...")

                    # Detect file type by extension and convert
                    if primary_file.suffix.lower() == ".html":
                        logger.info(f"Using HTML converter for {rfc_num}")
                        converter = HtmlToMdConverter(primary_file)
                        markdown_content = converter.convert()
                    else:
                        logger.info(f"Using XML converter for {rfc_num}")
                        converter = XmlToMdConverter(primary_file)  # type: ignore[assignment]
                        markdown_content = converter.convert()

                    # Write Markdown to file
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(markdown_content)

                    logger.info(f"Successfully converted {rfc_num} to Markdown")
                    success_count += 1

                    # Remove intermediate files if not in extra_formats
                    # Check if primary file should be kept
                    file_ext = primary_file.suffix.lower().lstrip(".")
                    if file_ext not in extra_formats:
                        logger.debug(f"Removing intermediate file: {primary_file}")
                        primary_file.unlink(missing_ok=True)

                except Exception as e:
                    logger.error(f"Error converting {rfc_num}: {e}", exc_info=args.debug)

            logger.info(
                f"Conversion complete: {success_count}/{total_count} RFCs converted successfully"
            )

            if success_count == 0:
                sys.exit(1)

        else:
            # Non-recursive download - process each RFC individually
            for rfc_number in rfc_numbers:
                logger.info(f"Processing RFC {rfc_number}")

                result = download_rfc(rfc_number, output_dir, extra_formats)
                if result[0] is None:
                    logger.error(f"Failed to download RFC {rfc_number}")
                    continue

                primary_file, extra_files = result

                logger.info(f"Using downloaded file: {primary_file}")

                # Determine output filename
                if args.output and len(rfc_numbers) == 1:
                    # Only use custom output name if processing a single RFC
                    output_file = output_dir / args.output
                else:
                    output_file = output_dir / f"{rfc_number}.md"

                logger.info(f"Output file will be: {output_file.absolute()}")

                # Convert to Markdown (detect file type)
                try:
                    # Detect file type by extension and convert
                    if primary_file.suffix.lower() == ".html":
                        logger.info("Detected HTML file, using HTML converter")
                        converter = HtmlToMdConverter(primary_file)
                        markdown_content = converter.convert()
                    else:
                        logger.info("Using XML converter")
                        converter = XmlToMdConverter(primary_file)  # type: ignore[assignment]
                        markdown_content = converter.convert()

                    # Write Markdown to file
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(markdown_content)

                    logger.info(f"Successfully converted to Markdown: {output_file}")

                    # Remove intermediate file if not in extra_formats
                    file_ext = primary_file.suffix.lower().lstrip(".")
                    if file_ext not in extra_formats:
                        logger.debug(f"Removing intermediate file: {primary_file}")
                        primary_file.unlink(missing_ok=True)

                except Exception as e:
                    logger.error(f"Error during conversion: {e}", exc_info=True)

    else:
        # Process local file
        xml_file = Path(args.file)
        if not xml_file.exists():
            logger.error(f"File not found: {xml_file}")
            sys.exit(1)
        logger.info(f"Processing local file: {xml_file.absolute()}")

        # Determine output filename
        if args.output:
            output_file = output_dir / args.output
        else:
            output_file = output_dir / f"{xml_file.stem}.md"

        logger.info(f"Output file will be: {output_file.absolute()}")

        # Convert to Markdown (detect file type)
        try:
            # Detect file type by extension and convert
            if xml_file.suffix.lower() == ".html":
                logger.info("Detected HTML file, using HTML converter")
                converter = HtmlToMdConverter(xml_file)
                markdown_content = converter.convert()
            else:
                logger.info("Using XML converter")
                converter = XmlToMdConverter(xml_file)  # type: ignore[assignment]
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
