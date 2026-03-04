"""
Unit tests for rfc2md.py CLI module.

This module tests the command-line interface functionality.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import argparse

# Import the module to test
import rfc2md


class TestParseArguments:
    """Test parse_arguments function."""

    def test_parse_arguments_with_rfc(self, monkeypatch):
        """Test parsing with --rfc argument."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514'])
        args = rfc2md.parse_arguments()
        
        assert args.rfc == ['9514']
        assert args.file is None
        assert not hasattr(args, 'from_md') or args.from_md is None

    def test_parse_arguments_with_multiple_rfcs(self, monkeypatch):
        """Test parsing with multiple RFCs."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514', '9552', '8402'])
        args = rfc2md.parse_arguments()
        
        assert args.rfc == ['9514', '9552', '8402']

    def test_parse_arguments_with_file(self, monkeypatch):
        """Test parsing with --file argument."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--file', 'test.xml'])
        args = rfc2md.parse_arguments()
        
        assert args.file == 'test.xml'
        assert args.rfc is None

    def test_parse_arguments_with_from_md(self, monkeypatch):
        """Test parsing with --from-md argument."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--from-md', 'refs.md'])
        args = rfc2md.parse_arguments()
        
        assert args.from_md == 'refs.md'
        assert args.rfc is None

    def test_parse_arguments_with_output_dir(self, monkeypatch):
        """Test parsing with --output-dir argument."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514', '--output-dir', 'downloads'])
        args = rfc2md.parse_arguments()
        
        assert args.output_dir == 'downloads'

    def test_parse_arguments_with_output(self, monkeypatch):
        """Test parsing with --output argument."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514', '--output', 'custom.md'])
        args = rfc2md.parse_arguments()
        
        assert args.output == 'custom.md'

    def test_parse_arguments_with_extra_formats(self, monkeypatch):
        """Test parsing with --extra argument."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514', '--extra', 'pdf', 'text'])
        args = rfc2md.parse_arguments()
        
        assert args.extra == ['pdf', 'text']

    def test_parse_arguments_with_recursive(self, monkeypatch):
        """Test parsing with --recursive argument."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514', '--recursive'])
        args = rfc2md.parse_arguments()
        
        assert args.recursive is True

    def test_parse_arguments_with_max_depth(self, monkeypatch):
        """Test parsing with --max-depth argument."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514', '--recursive', '--max-depth', '2'])
        args = rfc2md.parse_arguments()
        
        assert args.max_depth == 2

    def test_parse_arguments_with_debug(self, monkeypatch):
        """Test parsing with --debug argument."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514', '--debug'])
        args = rfc2md.parse_arguments()
        
        assert args.debug is True

    def test_parse_arguments_with_build_index(self, monkeypatch):
        """Test parsing with --build-index argument."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514', '--build-index'])
        args = rfc2md.parse_arguments()
        
        assert args.build_index is True

    def test_parse_arguments_error_extra_with_file(self, monkeypatch):
        """Test error when using --extra with --file."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--file', 'test.xml', '--extra', 'pdf'])
        
        with pytest.raises(SystemExit):
            rfc2md.parse_arguments()

    def test_parse_arguments_error_recursive_with_file(self, monkeypatch):
        """Test error when using --recursive with --file."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--file', 'test.xml', '--recursive'])
        
        with pytest.raises(SystemExit):
            rfc2md.parse_arguments()

    def test_parse_arguments_error_build_index_with_output(self, monkeypatch):
        """Test error when using --build-index with --output."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514', '--build-index', '--output', 'custom.md'])
        
        with pytest.raises(SystemExit):
            rfc2md.parse_arguments()

    def test_parse_arguments_error_no_input(self, monkeypatch):
        """Test error when no input source is specified."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py'])
        
        with pytest.raises(SystemExit):
            rfc2md.parse_arguments()


class TestMainWithRfc:
    """Test main function with --rfc argument."""

    @patch('rfc2md.build_index_file')
    @patch('rfc2md.XmlToMdConverter')
    @patch('rfc2md.download_rfc')
    @patch('rfc2md.setup_logging')
    def test_main_with_single_rfc(self, mock_setup_logging, mock_download, mock_converter, mock_build_index, monkeypatch, tmp_path):
        """Test main with single RFC."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514', '--output-dir', str(tmp_path)])
        
        # Setup mocks
        xml_file = tmp_path / "rfc9514.xml"
        xml_file.write_text("<?xml?>")
        mock_download.return_value = (xml_file, {})
        
        mock_conv_instance = Mock()
        mock_conv_instance.convert.return_value = "# RFC 9514\n\nTest content"
        mock_converter.return_value = mock_conv_instance
        
        # Run main
        rfc2md.main()
        
        # Verify
        mock_setup_logging.assert_called_once()
        mock_download.assert_called_once()
        mock_converter.assert_called_once_with(xml_file)
        assert (tmp_path / "rfc9514.md").exists()

    @patch('rfc2md.HtmlToMdConverter')
    @patch('rfc2md.download_rfc')
    @patch('rfc2md.setup_logging')
    def test_main_with_html_file(self, mock_setup_logging, mock_download, mock_converter, monkeypatch, tmp_path):
        """Test main with HTML file (fallback)."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514', '--output-dir', str(tmp_path)])
        
        # Setup mocks - return HTML file
        html_file = tmp_path / "rfc9514.html"
        html_file.write_text("<html>test</html>")
        mock_download.return_value = (html_file, {})
        
        mock_conv_instance = Mock()
        mock_conv_instance.convert.return_value = "# RFC 9514\n\nTest content"
        mock_converter.return_value = mock_conv_instance
        
        # Run main
        rfc2md.main()
        
        # Verify HTML converter was used
        mock_converter.assert_called_once_with(html_file)

    @patch('rfc2md.download_rfc')
    @patch('rfc2md.setup_logging')
    def test_main_with_download_failure(self, mock_setup_logging, mock_download, monkeypatch, tmp_path):
        """Test main with download failure."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9999', '--output-dir', str(tmp_path)])
        
        # Setup mocks - download fails
        mock_download.return_value = None
        
        # Run main - should not crash
        rfc2md.main()
        
        # Verify download was attempted
        mock_download.assert_called_once()

    @patch('rfc2md.build_index_file')
    @patch('rfc2md.XmlToMdConverter')
    @patch('rfc2md.download_rfc')
    @patch('rfc2md.setup_logging')
    def test_main_with_build_index(self, mock_setup_logging, mock_download, mock_converter, mock_build_index, monkeypatch, tmp_path):
        """Test main with --build-index flag."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514', '--output-dir', str(tmp_path), '--build-index'])
        
        # Setup mocks
        xml_file = tmp_path / "rfc9514.xml"
        xml_file.write_text("<?xml?>")
        mock_download.return_value = (xml_file, {})
        
        mock_conv_instance = Mock()
        mock_conv_instance.convert.return_value = "# RFC 9514"
        mock_converter.return_value = mock_conv_instance
        
        # Run main
        rfc2md.main()
        
        # Verify index was built
        mock_build_index.assert_called_once_with(tmp_path)

    @patch('rfc2md.XmlToMdConverter')
    @patch('rfc2md.download_rfc')
    @patch('rfc2md.setup_logging')
    def test_main_with_custom_output(self, mock_setup_logging, mock_download, mock_converter, monkeypatch, tmp_path):
        """Test main with custom output filename."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514', '--output-dir', str(tmp_path), '--output', 'custom.md'])
        
        # Setup mocks
        xml_file = tmp_path / "rfc9514.xml"
        xml_file.write_text("<?xml?>")
        mock_download.return_value = (xml_file, {})
        
        mock_conv_instance = Mock()
        mock_conv_instance.convert.return_value = "# RFC 9514"
        mock_converter.return_value = mock_conv_instance
        
        # Run main
        rfc2md.main()
        
        # Verify custom filename was used
        assert (tmp_path / "custom.md").exists()
        assert not (tmp_path / "rfc9514.md").exists()


class TestMainWithRecursive:
    """Test main function with --recursive flag."""

    @patch('rfc2md.build_index_file')
    @patch('rfc2md.XmlToMdConverter')
    @patch('rfc2md.download_rfc_recursive')
    @patch('rfc2md.setup_logging')
    def test_main_with_recursive(self, mock_setup_logging, mock_download_recursive, mock_converter, mock_build_index, monkeypatch, tmp_path):
        """Test main with recursive download."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514', '--output-dir', str(tmp_path), '--recursive'])
        
        # Setup mocks
        xml1 = tmp_path / "rfc9514.xml"
        xml2 = tmp_path / "rfc2119.xml"
        xml1.write_text("<?xml?>")
        xml2.write_text("<?xml?>")
        
        mock_download_recursive.return_value = {
            "rfc9514": (xml1, {}),
            "rfc2119": (xml2, {})
        }
        
        mock_conv_instance = Mock()
        mock_conv_instance.convert.return_value = "# RFC"
        mock_converter.return_value = mock_conv_instance
        
        # Run main
        rfc2md.main()
        
        # Verify both RFCs were converted
        assert (tmp_path / "rfc9514.md").exists()
        assert (tmp_path / "rfc2119.md").exists()

    @patch('rfc2md.download_rfc_recursive')
    @patch('rfc2md.setup_logging')
    def test_main_with_recursive_failure(self, mock_setup_logging, mock_download_recursive, monkeypatch, tmp_path):
        """Test main with recursive download failure."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9999', '--output-dir', str(tmp_path), '--recursive'])
        
        # Setup mocks - download fails
        mock_download_recursive.return_value = {}
        
        # Run main - should exit with error
        with pytest.raises(SystemExit) as exc_info:
            rfc2md.main()
        
        assert exc_info.value.code == 1


class TestMainWithFile:
    """Test main function with --file argument."""

    @patch('rfc2md.XmlToMdConverter')
    @patch('rfc2md.setup_logging')
    def test_main_with_local_xml_file(self, mock_setup_logging, mock_converter, monkeypatch, tmp_path):
        """Test main with local XML file."""
        xml_file = tmp_path / "test.xml"
        xml_file.write_text("<?xml?>")
        
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--file', str(xml_file), '--output-dir', str(tmp_path)])
        
        # Setup mocks
        mock_conv_instance = Mock()
        mock_conv_instance.convert.return_value = "# Test RFC"
        mock_converter.return_value = mock_conv_instance
        
        # Run main
        rfc2md.main()
        
        # Verify
        mock_converter.assert_called_once_with(xml_file)
        assert (tmp_path / "test.md").exists()

    @patch('rfc2md.HtmlToMdConverter')
    @patch('rfc2md.setup_logging')
    def test_main_with_local_html_file(self, mock_setup_logging, mock_converter, monkeypatch, tmp_path):
        """Test main with local HTML file."""
        html_file = tmp_path / "test.html"
        html_file.write_text("<html>test</html>")
        
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--file', str(html_file), '--output-dir', str(tmp_path)])
        
        # Setup mocks
        mock_conv_instance = Mock()
        mock_conv_instance.convert.return_value = "# Test RFC"
        mock_converter.return_value = mock_conv_instance
        
        # Run main
        rfc2md.main()
        
        # Verify HTML converter was used
        mock_converter.assert_called_once_with(html_file)

    @patch('rfc2md.setup_logging')
    def test_main_with_nonexistent_file(self, mock_setup_logging, monkeypatch, tmp_path):
        """Test main with nonexistent file."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--file', 'nonexistent.xml', '--output-dir', str(tmp_path)])
        
        # Run main - should exit with error
        with pytest.raises(SystemExit) as exc_info:
            rfc2md.main()
        
        assert exc_info.value.code == 1

    @patch('rfc2md.XmlToMdConverter')
    @patch('rfc2md.setup_logging')
    def test_main_with_file_conversion_error(self, mock_setup_logging, mock_converter, monkeypatch, tmp_path):
        """Test main with file conversion error."""
        xml_file = tmp_path / "test.xml"
        xml_file.write_text("<?xml?>")
        
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--file', str(xml_file), '--output-dir', str(tmp_path)])
        
        # Setup mocks - converter raises exception
        mock_converter.side_effect = Exception("Conversion failed")
        
        # Run main - should exit with error
        with pytest.raises(SystemExit) as exc_info:
            rfc2md.main()
        
        assert exc_info.value.code == 1


class TestMainWithFromMd:
    """Test main function with --from-md argument."""

    @patch('rfc2md.XmlToMdConverter')
    @patch('rfc2md.download_rfc')
    @patch('rfc2md.extract_rfc_numbers_from_markdown')
    @patch('rfc2md.setup_logging')
    def test_main_with_from_md(self, mock_setup_logging, mock_extract, mock_download, mock_converter, monkeypatch, tmp_path):
        """Test main with --from-md argument."""
        md_file = tmp_path / "refs.md"
        md_file.write_text("RFC 9514, RFC 2119")
        
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--from-md', str(md_file), '--output-dir', str(tmp_path)])
        
        # Setup mocks
        mock_extract.return_value = {"rfc9514", "rfc2119"}
        
        xml1 = tmp_path / "rfc9514.xml"
        xml2 = tmp_path / "rfc2119.xml"
        xml1.write_text("<?xml?>")
        xml2.write_text("<?xml?>")
        
        mock_download.side_effect = [
            (xml1, {}),
            (xml2, {})
        ]
        
        mock_conv_instance = Mock()
        mock_conv_instance.convert.return_value = "# RFC"
        mock_converter.return_value = mock_conv_instance
        
        # Run main
        rfc2md.main()
        
        # Verify
        mock_extract.assert_called_once()
        assert mock_download.call_count == 2

    @patch('rfc2md.extract_rfc_numbers_from_markdown')
    @patch('rfc2md.setup_logging')
    def test_main_with_from_md_no_rfcs_found(self, mock_setup_logging, mock_extract, monkeypatch, tmp_path):
        """Test main with --from-md when no RFCs found."""
        md_file = tmp_path / "empty.md"
        md_file.write_text("No RFCs here")
        
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--from-md', str(md_file), '--output-dir', str(tmp_path)])
        
        # Setup mocks
        mock_extract.return_value = set()
        
        # Run main - should exit with code 0 (warning, not error)
        with pytest.raises(SystemExit) as exc_info:
            rfc2md.main()
        
        assert exc_info.value.code == 0

    @patch('rfc2md.setup_logging')
    def test_main_with_from_md_nonexistent_file(self, mock_setup_logging, monkeypatch, tmp_path):
        """Test main with --from-md and nonexistent file."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--from-md', 'nonexistent.md', '--output-dir', str(tmp_path)])
        
        # Run main - should exit with error
        with pytest.raises(SystemExit) as exc_info:
            rfc2md.main()
        
        assert exc_info.value.code == 1


class TestMainDebugMode:
    """Test main function with debug mode."""

    @patch('rfc2md.XmlToMdConverter')
    @patch('rfc2md.download_rfc')
    @patch('rfc2md.setup_logging')
    def test_main_with_debug_flag(self, mock_setup_logging, mock_download, mock_converter, monkeypatch, tmp_path):
        """Test main with --debug flag."""
        monkeypatch.setattr(sys, 'argv', ['rfc2md.py', '--rfc', '9514', '--output-dir', str(tmp_path), '--debug'])
        
        # Setup mocks
        xml_file = tmp_path / "rfc9514.xml"
        xml_file.write_text("<?xml?>")
        mock_download.return_value = (xml_file, {})
        
        mock_conv_instance = Mock()
        mock_conv_instance.convert.return_value = "# RFC 9514"
        mock_converter.return_value = mock_conv_instance
        
        # Run main
        rfc2md.main()
        
        # Verify debug logging was enabled
        import logging
        mock_setup_logging.assert_called_once_with(logging.DEBUG)