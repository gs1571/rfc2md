"""
Integration tests for RFC to Markdown conversion with snapshot testing.
"""

import difflib
from pathlib import Path

import pytest

from lib.converter import XmlToMdConverter
from lib.html_converter import HtmlToMdConverter


def compare_files(generated_file: Path, snapshot_file: Path) -> bool:
    """
    Compare generated file with snapshot file.

    Args:
        generated_file: Path to generated MD file
        snapshot_file: Path to snapshot MD file

    Returns:
        True if files are identical, False otherwise
    """
    generated_content = generated_file.read_text(encoding="utf-8")
    snapshot_content = snapshot_file.read_text(encoding="utf-8")
    return generated_content == snapshot_content


def get_diff(generated_file: Path, snapshot_file: Path, max_lines: int = 50) -> str:
    """
    Get unified diff between generated and snapshot files with color coding.

    Args:
        generated_file: Path to generated MD file
        snapshot_file: Path to snapshot MD file
        max_lines: Maximum number of diff lines to show (default: 50)

    Returns:
        Unified diff as string with context lines, truncated if too long
    """
    generated_lines = generated_file.read_text(encoding="utf-8").splitlines(keepends=True)
    snapshot_lines = snapshot_file.read_text(encoding="utf-8").splitlines(keepends=True)

    diff = list(
        difflib.unified_diff(
            snapshot_lines,
            generated_lines,
            fromfile=f"expected/{snapshot_file.name}",
            tofile=f"actual/{generated_file.name}",
            n=3,  # Show 3 lines of context around changes
        )
    )

    # Add color coding to diff lines
    colored_diff = []
    for line in diff:
        if line.startswith("-") and not line.startswith("---"):
            # Red for removed lines
            colored_diff.append(f"\033[31m{line}\033[0m")
        elif line.startswith("+") and not line.startswith("+++"):
            # Green for added lines
            colored_diff.append(f"\033[32m{line}\033[0m")
        else:
            colored_diff.append(line)

    # Truncate diff if too long
    if len(colored_diff) > max_lines:
        truncated_diff = colored_diff[:max_lines]
        truncated_diff.append(
            f"... (diff truncated, showing first {max_lines} of {len(colored_diff)} lines)\n"
        )
        return "".join(truncated_diff)

    return "".join(colored_diff)


def get_regeneration_command(source_file: Path, snapshot_file: Path) -> str:
    """
    Generate command to regenerate snapshot.

    Args:
        source_file: Path to source RFC file (XML or HTML)
        snapshot_file: Path to snapshot file to update

    Returns:
        Command string to regenerate snapshot
    """
    return f"source .venv/bin/activate && python rfc2md.py --file {source_file} --output {snapshot_file}"


@pytest.mark.integration
class TestXmlConversion:
    """Integration tests for XML to Markdown conversion."""

    @pytest.mark.parametrize("xml_file", list(Path("tests/fixtures/xml").glob("*.xml")))
    def test_xml_to_markdown_conversion(self, tmp_path, xml_file):
        """
        Test XML to Markdown conversion against snapshot.

        Args:
            tmp_path: Pytest fixture for temporary directory
            xml_file: Path to XML file to test
        """
        # Arrange
        rfc_name = xml_file.stem  # e.g., "rfc9514"
        snapshot_file = Path("tests/snapshots") / f"{rfc_name}.md"
        output_file = tmp_path / f"{rfc_name}.md"

        # Act - convert using XmlToMdConverter
        print(f"\n[TEST] Converting {rfc_name}...")
        converter = XmlToMdConverter(xml_file)
        markdown_content = converter.convert()
        output_file.write_text(markdown_content, encoding="utf-8")

        # Assert
        if not compare_files(output_file, snapshot_file):
            diff_text = get_diff(output_file, snapshot_file)
            regen_cmd = get_regeneration_command(xml_file, snapshot_file)

            error_msg = (
                f"\n\n"
                f"╔{'═'*78}╗\n"
                f"║ SNAPSHOT MISMATCH: {rfc_name:<60} ║\n"
                f"╚{'═'*78}╝\n"
                f"\n"
                f"Source:   {xml_file}\n"
                f"Snapshot: {snapshot_file}\n"
                f"\n"
                f"{'─'*80}\n"
                f"DIFF (expected vs actual):\n"
                f"{'─'*80}\n"
                f"{diff_text}\n"
                f"{'─'*80}\n"
                f"\n"
                f"To update the snapshot, run:\n"
                f"  {regen_cmd}\n"
                f"\n"
            )
            print(error_msg)
            pytest.fail(f"Snapshot mismatch for {rfc_name}")
        else:
            print(f"[PASS] {rfc_name} - snapshot matches")


@pytest.mark.integration
class TestHtmlConversion:
    """Integration tests for HTML to Markdown conversion."""

    @pytest.mark.parametrize("html_file", list(Path("tests/fixtures/html").glob("*.html")))
    def test_html_to_markdown_conversion(self, tmp_path, html_file):
        """
        Test HTML to Markdown conversion against snapshot.

        Args:
            tmp_path: Pytest fixture for temporary directory
            html_file: Path to HTML file to test
        """
        # Arrange
        rfc_name = html_file.stem  # e.g., "rfc7752"
        snapshot_file = Path("tests/snapshots") / f"{rfc_name}.md"
        output_file = tmp_path / f"{rfc_name}.md"

        # Act - convert using HtmlToMdConverter
        print(f"\n[TEST] Converting {rfc_name}...")
        converter = HtmlToMdConverter(html_file)
        markdown_content = converter.convert()
        output_file.write_text(markdown_content, encoding="utf-8")

        # Assert
        if not compare_files(output_file, snapshot_file):
            diff_text = get_diff(output_file, snapshot_file)
            regen_cmd = get_regeneration_command(html_file, snapshot_file)

            error_msg = (
                f"\n\n"
                f"╔{'═'*78}╗\n"
                f"║ SNAPSHOT MISMATCH: {rfc_name:<60} ║\n"
                f"╚{'═'*78}╝\n"
                f"\n"
                f"Source:   {html_file}\n"
                f"Snapshot: {snapshot_file}\n"
                f"\n"
                f"{'─'*80}\n"
                f"DIFF (expected vs actual):\n"
                f"{'─'*80}\n"
                f"{diff_text}\n"
                f"{'─'*80}\n"
                f"\n"
                f"To update the snapshot, run:\n"
                f"  {regen_cmd}\n"
                f"\n"
            )
            print(error_msg)
            pytest.fail(f"Snapshot mismatch for {rfc_name}")
        else:
            print(f"[PASS] {rfc_name} - snapshot matches")
