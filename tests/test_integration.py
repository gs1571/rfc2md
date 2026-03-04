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
    return generated_file.read_text(encoding="utf-8") == snapshot_file.read_text(encoding="utf-8")


def get_diff(generated_file: Path, snapshot_file: Path, max_lines: int = 100) -> str:
    """
    Get unified diff between generated and snapshot files with color coding.

    Args:
        generated_file: Path to generated MD file
        snapshot_file: Path to snapshot MD file
        max_lines: Maximum number of diff lines to show (default: 100)

    Returns:
        Unified diff as string with context lines, truncated if too long
    """
    diff = list(
        difflib.unified_diff(
            snapshot_file.read_text(encoding="utf-8").splitlines(keepends=True),
            generated_file.read_text(encoding="utf-8").splitlines(keepends=True),
            fromfile=f"expected/{snapshot_file.name}",
            tofile=f"actual/{generated_file.name}",
            n=3,  # Show 3 lines of context around changes
        )
    )

    # Truncate diff if too long
    if len(diff) > max_lines:
        diff = diff[:max_lines]
        diff.append(f"... (diff truncated, showing first {max_lines} lines)\n")

    # Add color coding to diff lines
    result = []
    for line in diff:
        if line.startswith("-") and not line.startswith("---"):
            result.append(f"\033[31m{line}\033[0m")  # Red for removed
        elif line.startswith("+") and not line.startswith("+++"):
            result.append(f"\033[32m{line}\033[0m")  # Green for added
        else:
            result.append(line)

    return "".join(result)


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
        output_file.write_text(converter.convert(), encoding="utf-8")

        # Assert
        if not compare_files(output_file, snapshot_file):
            print(f"\n\n╔{'═'*78}╗")
            print(f"║ SNAPSHOT MISMATCH: {rfc_name:<60} ║")
            print(f"╚{'═'*78}╝\n")
            print(f"Source:   {xml_file}")
            print(f"Snapshot: {snapshot_file}\n")
            print(f"{'─'*80}")
            print("DIFF (expected vs actual):")
            print(f"{'─'*80}")
            print(get_diff(output_file, snapshot_file))
            print(f"{'─'*80}\n")
            print("To update the snapshot, run:")
            print(f"  {get_regeneration_command(xml_file, snapshot_file)}\n")
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
        output_file.write_text(converter.convert(), encoding="utf-8")

        # Assert
        if not compare_files(output_file, snapshot_file):
            print(f"\n\n╔{'═'*78}╗")
            print(f"║ SNAPSHOT MISMATCH: {rfc_name:<60} ║")
            print(f"╚{'═'*78}╝\n")
            print(f"Source:   {html_file}")
            print(f"Snapshot: {snapshot_file}\n")
            print(f"{'─'*80}")
            print("DIFF (expected vs actual):")
            print(f"{'─'*80}")
            print(get_diff(output_file, snapshot_file))
            print(f"{'─'*80}\n")
            print("To update the snapshot, run:")
            print(f"  {get_regeneration_command(html_file, snapshot_file)}\n")
            pytest.fail(f"Snapshot mismatch for {rfc_name}")
        else:
            print(f"[PASS] {rfc_name} - snapshot matches")


@pytest.mark.integration
class TestLocalMdLinks:
    """Integration tests for local MD links in references."""

    def test_local_md_links_in_references(self, tmp_path):
        """
        Test that local MD links are added to RFC references.
        """
        # Arrange
        xml_file = Path("tests/fixtures/xml/rfc9514.xml")
        output_file = tmp_path / "rfc9514.md"

        # Act - convert using XmlToMdConverter
        converter = XmlToMdConverter(xml_file)
        markdown_content = converter.convert()
        output_file.write_text(markdown_content, encoding="utf-8")

        # Assert - check for local MD links in references
        assert "[Local MD](rfc2119.md)" in markdown_content
        assert "[Local MD](rfc7752.md)" in markdown_content
        assert "[Local MD](rfc8402.md)" in markdown_content

        # Verify format: external URL followed by local MD link
        assert (
            "<https://www.rfc-editor.org/info/rfc2119> [Local MD](rfc2119.md)" in markdown_content
        )

        print("[PASS] Local MD links are correctly added to references")

    def test_local_md_links_format(self, tmp_path):
        """
        Test the correct format of local MD links.
        """
        # Arrange
        xml_file = Path("tests/fixtures/xml/rfc9552.xml")
        output_file = tmp_path / "rfc9552.md"

        # Act
        converter = XmlToMdConverter(xml_file)
        markdown_content = converter.convert()
        output_file.write_text(markdown_content, encoding="utf-8")

        # Assert - verify links are in correct format
        lines = markdown_content.split("\n")
        reference_lines = [line for line in lines if "[Local MD](rfc" in line]

        # Should have at least some local MD links
        assert len(reference_lines) > 0

        # Each reference line should have the pattern: <URL> [Local MD](rfcXXXX.md)
        for line in reference_lines:
            assert "[Local MD](rfc" in line
            assert ".md)" in line

        print(f"[PASS] Found {len(reference_lines)} local MD links with correct format")
