"""
Tests for index generation functionality.
"""

import tempfile
from pathlib import Path

from lib.utils import build_index_file


def test_build_index_file_empty_directory():
    """Test index generation with empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Should not raise an error, just log a warning
        build_index_file(output_dir)

        # Index file should not be created for empty directory
        index_file = output_dir / "index.md"
        assert not index_file.exists()


def test_build_index_file_with_md_files_no_sources():
    """Test index generation with MD files but no source files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create some RFC markdown files
        (output_dir / "rfc9514.md").write_text("# RFC 9514\n\nContent")
        (output_dir / "rfc9552.md").write_text("# RFC 9552\n\nContent")
        (output_dir / "rfc8402.md").write_text("# RFC 8402\n\nContent")

        # Generate index
        build_index_file(output_dir)

        # Check index file was created
        index_file = output_dir / "index.md"
        assert index_file.exists()

        # Read and verify content
        content = index_file.read_text()
        assert "# RFC Index" in content
        assert "This index contains all RFC documents" in content

        # Check RFCs are sorted numerically
        assert content.index("RFC 8402") < content.index("RFC 9514")
        assert content.index("RFC 9514") < content.index("RFC 9552")

        # Check entries without titles (no source files)
        assert "[RFC 8402](rfc8402.md):" in content
        assert "[RFC 9514](rfc9514.md):" in content
        assert "[RFC 9552](rfc9552.md):" in content


def test_build_index_file_with_xml_sources():
    """Test index generation with XML source files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create RFC markdown files
        (output_dir / "rfc9514.md").write_text("# RFC 9514\n\nContent")
        (output_dir / "rfc9552.md").write_text("# RFC 9552\n\nContent")

        # Create XML source files with titles
        xml_9514 = """<?xml version="1.0" encoding="UTF-8"?>
<rfc xmlns:xi="http://www.w3.org/2001/XInclude" version="3">
  <front>
    <title>BGP-LS Extensions for SRv6</title>
  </front>
</rfc>"""
        (output_dir / "rfc9514.xml").write_text(xml_9514)

        xml_9552 = """<?xml version="1.0" encoding="UTF-8"?>
<rfc xmlns:xi="http://www.w3.org/2001/XInclude" version="3">
  <front>
    <title>Distribution of Link-State Information</title>
  </front>
</rfc>"""
        (output_dir / "rfc9552.xml").write_text(xml_9552)

        # Generate index
        build_index_file(output_dir)

        # Check index file was created
        index_file = output_dir / "index.md"
        assert index_file.exists()

        # Read and verify content
        content = index_file.read_text()

        # Check titles were extracted
        assert "[RFC 9514](rfc9514.md): BGP-LS Extensions for SRv6" in content
        assert "[RFC 9552](rfc9552.md): Distribution of Link-State Information" in content


def test_build_index_file_with_html_sources():
    """Test index generation with HTML source files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create RFC markdown files
        (output_dir / "rfc8402.md").write_text("# RFC 8402\n\nContent")

        # Create HTML source file with title
        html_8402 = """<!DOCTYPE html>
<html>
<head>
    <title>RFC 8402 - Segment Routing Architecture</title>
</head>
<body>
    <h1>Segment Routing Architecture</h1>
</body>
</html>"""
        (output_dir / "rfc8402.html").write_text(html_8402)

        # Generate index
        build_index_file(output_dir)

        # Check index file was created
        index_file = output_dir / "index.md"
        assert index_file.exists()

        # Read and verify content
        content = index_file.read_text()

        # Check title was extracted (should remove "RFC 8402 - " prefix)
        assert "[RFC 8402](rfc8402.md): Segment Routing Architecture" in content


def test_build_index_file_sorting():
    """Test that RFCs are sorted numerically, not lexicographically."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create RFC files in non-sorted order
        (output_dir / "rfc100.md").write_text("Content")
        (output_dir / "rfc20.md").write_text("Content")
        (output_dir / "rfc3.md").write_text("Content")
        (output_dir / "rfc1000.md").write_text("Content")

        # Generate index
        build_index_file(output_dir)

        # Read content
        index_file = output_dir / "index.md"
        content = index_file.read_text()

        # Check numerical sorting (3 < 20 < 100 < 1000)
        pos_3 = content.index("RFC 3")
        pos_20 = content.index("RFC 20")
        pos_100 = content.index("RFC 100")
        pos_1000 = content.index("RFC 1000")

        assert pos_3 < pos_20 < pos_100 < pos_1000


def test_build_index_file_excludes_index_md():
    """Test that index.md itself is not included in the index."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create RFC files and an existing index
        (output_dir / "rfc9514.md").write_text("Content")
        (output_dir / "index.md").write_text("Old index")

        # Generate index
        build_index_file(output_dir)

        # Read new index
        index_file = output_dir / "index.md"
        content = index_file.read_text()

        # Should not reference itself
        assert "index.md" not in content
        # Should only have RFC 9514
        assert "[RFC 9514](rfc9514.md):" in content


def test_build_index_file_mixed_sources():
    """Test index generation with mixed XML and HTML sources."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create RFC markdown files
        (output_dir / "rfc9514.md").write_text("Content")
        (output_dir / "rfc8402.md").write_text("Content")
        (output_dir / "rfc7752.md").write_text("Content")

        # XML source for 9514
        xml_9514 = """<?xml version="1.0" encoding="UTF-8"?>
<rfc version="3">
  <front>
    <title>BGP-LS Extensions</title>
  </front>
</rfc>"""
        (output_dir / "rfc9514.xml").write_text(xml_9514)

        # HTML source for 8402
        html_8402 = """<html><head><title>Segment Routing</title></head></html>"""
        (output_dir / "rfc8402.html").write_text(html_8402)

        # No source for 7752

        # Generate index
        build_index_file(output_dir)

        # Read content
        index_file = output_dir / "index.md"
        content = index_file.read_text()

        # Check all three RFCs with appropriate titles
        assert "[RFC 7752](rfc7752.md):" in content  # No title
        assert "[RFC 8402](rfc8402.md): Segment Routing" in content
        assert "[RFC 9514](rfc9514.md): BGP-LS Extensions" in content
