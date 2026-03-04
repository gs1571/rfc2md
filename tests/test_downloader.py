"""
Unit tests for lib/downloader.py module.

This module tests RFC downloading functionality with mocked network requests.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

from lib.downloader import download_rfc_html, download_rfc, download_rfc_recursive


class TestDownloadRfcHtml:
    """Test download_rfc_html function."""

    @patch('lib.downloader.requests.get')
    def test_download_rfc_html_success(self, mock_get, tmp_path):
        """Test successful HTML download."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '1000'}
        mock_response.iter_content = Mock(return_value=[b'<html>test</html>'])
        mock_get.return_value = mock_response
        
        # Test download
        result = download_rfc_html("rfc9514", tmp_path)
        
        assert result is not None
        assert result == tmp_path / "rfc9514.html"
        assert result.exists()
        assert result.read_bytes() == b'<html>test</html>'
        mock_get.assert_called_once()

    @patch('lib.downloader.requests.get')
    def test_download_rfc_html_with_progress(self, mock_get, tmp_path):
        """Test HTML download with progress tracking."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '500'}
        mock_response.iter_content = Mock(return_value=[b'test'])
        mock_get.return_value = mock_response
        
        result = download_rfc_html("rfc9514", tmp_path, current=1, total=10)
        
        assert result is not None
        assert result.exists()

    @patch('lib.downloader.requests.get')
    def test_download_rfc_html_404_error(self, mock_get, tmp_path):
        """Test HTML download with 404 error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        
        result = download_rfc_html("rfc9999", tmp_path)
        
        assert result is None

    @patch('lib.downloader.requests.get')
    def test_download_rfc_html_connection_error(self, mock_get, tmp_path):
        """Test HTML download with connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        
        result = download_rfc_html("rfc9514", tmp_path)
        
        assert result is None

    @patch('lib.downloader.requests.get')
    def test_download_rfc_html_timeout(self, mock_get, tmp_path):
        """Test HTML download with timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        
        result = download_rfc_html("rfc9514", tmp_path)
        
        assert result is None

    @patch('lib.downloader.requests.get')
    def test_download_rfc_html_request_exception(self, mock_get, tmp_path):
        """Test HTML download with generic request exception."""
        mock_get.side_effect = requests.exceptions.RequestException("Generic error")
        
        result = download_rfc_html("rfc9514", tmp_path)
        
        assert result is None

    @patch('lib.downloader.requests.get')
    def test_download_rfc_html_os_error(self, mock_get, tmp_path):
        """Test HTML download with file write error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '100'}
        mock_response.iter_content = Mock(return_value=[b'test'])
        mock_get.return_value = mock_response
        
        # Make directory read-only to cause write error
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            result = download_rfc_html("rfc9514", tmp_path)
        
        assert result is None


class TestDownloadRfc:
    """Test download_rfc function."""

    @patch('lib.downloader.requests.get')
    def test_download_rfc_xml_success(self, mock_get, tmp_path):
        """Test successful XML download."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '2000'}
        mock_response.iter_content = Mock(return_value=[b'<?xml version="1.0"?><rfc/>'])
        mock_get.return_value = mock_response
        
        result = download_rfc("rfc9514", tmp_path)
        
        assert result is not None
        primary_file, extra_files = result
        assert primary_file == tmp_path / "rfc9514.xml"
        assert primary_file.exists()
        assert extra_files == {}

    @patch('lib.downloader.download_rfc_html')
    @patch('lib.downloader.requests.get')
    def test_download_rfc_fallback_to_html(self, mock_get, mock_download_html, tmp_path):
        """Test fallback to HTML when XML not found."""
        # Mock XML 404 error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        
        # Mock HTML download success
        html_file = tmp_path / "rfc9514.html"
        html_file.write_text("<html>test</html>")
        mock_download_html.return_value = html_file
        
        result = download_rfc("rfc9514", tmp_path)
        
        assert result is not None
        primary_file, extra_files = result
        assert primary_file == html_file
        mock_download_html.assert_called_once()

    @patch('lib.downloader.download_rfc_html')
    @patch('lib.downloader.requests.get')
    def test_download_rfc_xml_and_html_both_fail(self, mock_get, mock_download_html, tmp_path):
        """Test when both XML and HTML downloads fail."""
        # Mock XML 404 error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        
        # Mock HTML download failure
        mock_download_html.return_value = None
        
        result = download_rfc("rfc9999", tmp_path)
        
        assert result is None

    @patch('lib.downloader.requests.get')
    def test_download_rfc_with_pdf_extra_format(self, mock_get, tmp_path):
        """Test downloading with PDF extra format."""
        # Mock XML download
        xml_response = Mock()
        xml_response.status_code = 200
        xml_response.headers = {'content-length': '1000'}
        xml_response.iter_content = Mock(return_value=[b'<?xml?>'])
        
        # Mock PDF download
        pdf_response = Mock()
        pdf_response.status_code = 200
        pdf_response.headers = {'content-length': '5000'}
        pdf_response.iter_content = Mock(return_value=[b'%PDF-1.4'])
        
        mock_get.side_effect = [xml_response, pdf_response]
        
        result = download_rfc("rfc9514", tmp_path, extra_formats=["pdf"])
        
        assert result is not None
        primary_file, extra_files = result
        assert primary_file == tmp_path / "rfc9514.xml"
        assert "pdf" in extra_files
        assert extra_files["pdf"] == tmp_path / "rfc9514.pdf"
        assert extra_files["pdf"].exists()

    @patch('lib.downloader.requests.get')
    def test_download_rfc_with_pdf_fallback_url(self, mock_get, tmp_path):
        """Test PDF download with fallback URL."""
        # Mock XML download
        xml_response = Mock()
        xml_response.status_code = 200
        xml_response.headers = {'content-length': '1000'}
        xml_response.iter_content = Mock(return_value=[b'<?xml?>'])
        
        # Mock PDF primary URL 404
        pdf_404_response = Mock()
        pdf_404_response.status_code = 404
        pdf_404_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=pdf_404_response)
        
        # Mock PDF fallback URL success
        pdf_fallback_response = Mock()
        pdf_fallback_response.status_code = 200
        pdf_fallback_response.headers = {'content-length': '5000'}
        pdf_fallback_response.iter_content = Mock(return_value=[b'%PDF-1.4'])
        
        mock_get.side_effect = [xml_response, pdf_404_response, pdf_fallback_response]
        
        result = download_rfc("rfc9514", tmp_path, extra_formats=["pdf"])
        
        assert result is not None
        primary_file, extra_files = result
        assert "pdf" in extra_files
        assert extra_files["pdf"].exists()

    @patch('lib.downloader.requests.get')
    def test_download_rfc_with_text_extra_format(self, mock_get, tmp_path):
        """Test downloading with text extra format."""
        # Mock XML download
        xml_response = Mock()
        xml_response.status_code = 200
        xml_response.headers = {'content-length': '1000'}
        xml_response.iter_content = Mock(return_value=[b'<?xml?>'])
        
        # Mock text download
        text_response = Mock()
        text_response.status_code = 200
        text_response.headers = {'content-length': '3000'}
        text_response.iter_content = Mock(return_value=[b'RFC text content'])
        
        mock_get.side_effect = [xml_response, text_response]
        
        result = download_rfc("rfc9514", tmp_path, extra_formats=["text"])
        
        assert result is not None
        primary_file, extra_files = result
        assert "text" in extra_files
        assert extra_files["text"] == tmp_path / "rfc9514.txt"
        assert extra_files["text"].exists()

    @patch('lib.downloader.requests.get')
    def test_download_rfc_with_xml_extra_format(self, mock_get, tmp_path):
        """Test downloading with xml extra format (already primary)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '1000'}
        mock_response.iter_content = Mock(return_value=[b'<?xml?>'])
        mock_get.return_value = mock_response
        
        result = download_rfc("rfc9514", tmp_path, extra_formats=["xml"])
        
        assert result is not None
        primary_file, extra_files = result
        assert "xml" in extra_files
        assert extra_files["xml"] == primary_file

    @patch('lib.downloader.download_rfc_html')
    @patch('lib.downloader.requests.get')
    def test_download_rfc_with_html_extra_format_when_html_primary(self, mock_get, mock_download_html, tmp_path):
        """Test downloading with html extra format when HTML is primary file."""
        # Mock XML 404 to trigger HTML fallback
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        
        html_file = tmp_path / "rfc9514.html"
        html_file.write_text("<html>test</html>")
        mock_download_html.return_value = html_file
        
        result = download_rfc("rfc9514", tmp_path, extra_formats=["html"])
        
        assert result is not None
        primary_file, extra_files = result
        assert "html" in extra_files
        assert extra_files["html"] == primary_file

    @patch('lib.downloader.download_rfc_html')
    @patch('lib.downloader.requests.get')
    def test_download_rfc_with_html_extra_format_when_xml_primary(self, mock_get, mock_download_html, tmp_path):
        """Test downloading with html extra format when XML is primary file."""
        # Mock XML download success
        xml_response = Mock()
        xml_response.status_code = 200
        xml_response.headers = {'content-length': '1000'}
        xml_response.iter_content = Mock(return_value=[b'<?xml?>'])
        mock_get.return_value = xml_response
        
        # Mock HTML download
        html_file = tmp_path / "rfc9514.html"
        html_file.write_text("<html>test</html>")
        mock_download_html.return_value = html_file
        
        result = download_rfc("rfc9514", tmp_path, extra_formats=["html"])
        
        assert result is not None
        primary_file, extra_files = result
        assert primary_file.suffix == ".xml"
        assert "html" in extra_files
        assert extra_files["html"] == html_file
        mock_download_html.assert_called_once()

    @patch('lib.downloader.requests.get')
    def test_download_rfc_connection_error(self, mock_get, tmp_path):
        """Test download with connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        
        result = download_rfc("rfc9514", tmp_path)
        
        assert result is None

    @patch('lib.downloader.requests.get')
    def test_download_rfc_timeout(self, mock_get, tmp_path):
        """Test download with timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        
        result = download_rfc("rfc9514", tmp_path)
        
        assert result is None


class TestDownloadRfcRecursive:
    """Test download_rfc_recursive function."""

    @patch('lib.downloader.download_rfc')
    @patch('lib.downloader.extract_rfc_references_from_xml')
    def test_download_rfc_recursive_depth_0(self, mock_extract, mock_download, tmp_path):
        """Test recursive download with depth 0 (no recursion)."""
        xml_file = tmp_path / "rfc9514.xml"
        xml_file.write_text("<?xml?>")
        mock_download.return_value = (xml_file, {})
        
        result = download_rfc_recursive("rfc9514", tmp_path, max_depth=0)
        
        assert "rfc9514" in result
        assert result["rfc9514"][0] == xml_file
        # Should not extract references at depth 0
        mock_extract.assert_not_called()

    @patch('lib.downloader.download_rfc')
    @patch('lib.downloader.extract_rfc_references_from_xml')
    def test_download_rfc_recursive_depth_1(self, mock_extract, mock_download, tmp_path):
        """Test recursive download with depth 1."""
        # Setup main RFC
        xml_file = tmp_path / "rfc9514.xml"
        xml_file.write_text("<?xml?>")
        
        # Setup referenced RFC
        ref_xml_file = tmp_path / "rfc2119.xml"
        ref_xml_file.write_text("<?xml?>")
        
        mock_download.side_effect = [
            (xml_file, {}),
            (ref_xml_file, {})
        ]
        mock_extract.side_effect = [
            {"rfc2119"},  # First call for rfc9514
            set()  # Second call for rfc2119 (no more refs)
        ]
        
        result = download_rfc_recursive("rfc9514", tmp_path, max_depth=1)
        
        assert "rfc9514" in result
        assert "rfc2119" in result
        assert len(result) == 2

    @patch('lib.downloader.download_rfc')
    def test_download_rfc_recursive_already_processed(self, mock_download, tmp_path):
        """Test that already processed RFCs are skipped."""
        xml_file = tmp_path / "rfc9514.xml"
        xml_file.write_text("<?xml?>")
        mock_download.return_value = (xml_file, {})
        
        processed = {"rfc9514"}
        result = download_rfc_recursive("rfc9514", tmp_path, processed=processed)
        
        assert result == {}
        mock_download.assert_not_called()

    @patch('lib.downloader.extract_rfc_references_from_xml')
    def test_download_rfc_recursive_existing_xml_file(self, mock_extract, tmp_path):
        """Test with existing XML file (skip download)."""
        xml_file = tmp_path / "rfc9514.xml"
        xml_file.write_text("<?xml?>")
        mock_extract.return_value = set()
        
        result = download_rfc_recursive("rfc9514", tmp_path, max_depth=1)
        
        assert "rfc9514" in result
        assert result["rfc9514"][0] == xml_file
        # Should still extract references from existing file
        mock_extract.assert_called_once()

    @patch('lib.downloader.extract_rfc_references_from_html')
    def test_download_rfc_recursive_existing_html_file(self, mock_extract, tmp_path):
        """Test with existing HTML file (skip download)."""
        html_file = tmp_path / "rfc9514.html"
        html_file.write_text("<html>test</html>")
        mock_extract.return_value = set()
        
        result = download_rfc_recursive("rfc9514", tmp_path, max_depth=1)
        
        assert "rfc9514" in result
        assert result["rfc9514"][0] == html_file
        # Should extract references from HTML file
        mock_extract.assert_called_once()

    @patch('lib.downloader.download_rfc')
    def test_download_rfc_recursive_download_failure(self, mock_download, tmp_path):
        """Test handling of download failure."""
        mock_download.return_value = None
        
        result = download_rfc_recursive("rfc9999", tmp_path)
        
        assert result == {}

    @patch('lib.downloader.download_rfc')
    @patch('lib.downloader.extract_rfc_references_from_xml')
    def test_download_rfc_recursive_with_extra_formats(self, mock_extract, mock_download, tmp_path):
        """Test recursive download with extra formats (file doesn't exist yet)."""
        # Don't create the file beforehand - let download_rfc be called
        xml_file = tmp_path / "rfc9999.xml"  # Use different RFC that doesn't exist
        pdf_file = tmp_path / "rfc9999.pdf"
        
        # Create files when download_rfc is called
        def create_files(*args, **kwargs):
            xml_file.write_text("<?xml?>")
            pdf_file.write_bytes(b"%PDF")
            return (xml_file, {"pdf": pdf_file})
        
        mock_download.side_effect = create_files
        mock_extract.return_value = set()
        
        result = download_rfc_recursive("rfc9999", tmp_path, extra_formats=["pdf"])
        
        assert "rfc9999" in result
        primary, extras = result["rfc9999"]
        assert primary == xml_file
        assert "pdf" in extras
        assert extras["pdf"] == pdf_file

    @patch('lib.downloader.download_rfc')
    @patch('lib.downloader.extract_rfc_references_from_xml')
    def test_download_rfc_recursive_extraction_error(self, mock_extract, mock_download, tmp_path):
        """Test handling of reference extraction error."""
        xml_file = tmp_path / "rfc9514.xml"
        xml_file.write_text("<?xml?>")
        mock_download.return_value = (xml_file, {})
        mock_extract.side_effect = Exception("Extraction failed")
        
        # Should not raise exception, just log warning
        result = download_rfc_recursive("rfc9514", tmp_path, max_depth=1)
        
        assert "rfc9514" in result

    @patch('lib.downloader.download_rfc')
    @patch('lib.downloader.extract_rfc_references_from_xml')
    def test_download_rfc_recursive_normalizes_rfc_number(self, mock_extract, mock_download, tmp_path):
        """Test that RFC numbers are normalized."""
        xml_file = tmp_path / "rfc9514.xml"
        xml_file.write_text("<?xml?>")
        mock_download.return_value = (xml_file, {})
        mock_extract.return_value = set()
        
        # Pass unnormalized RFC number
        result = download_rfc_recursive("9514", tmp_path)
        
        assert "rfc9514" in result

    @patch('lib.downloader.download_rfc')
    @patch('lib.downloader.extract_rfc_references_from_xml')
    def test_download_rfc_recursive_depth_2(self, mock_extract, mock_download, tmp_path):
        """Test recursive download with depth 2."""
        # Setup files
        rfc1 = tmp_path / "rfc9514.xml"
        rfc2 = tmp_path / "rfc2119.xml"
        rfc3 = tmp_path / "rfc8174.xml"
        
        for f in [rfc1, rfc2, rfc3]:
            f.write_text("<?xml?>")
        
        mock_download.side_effect = [
            (rfc1, {}),
            (rfc2, {}),
            (rfc3, {})
        ]
        
        mock_extract.side_effect = [
            {"rfc2119"},  # rfc9514 references rfc2119
            {"rfc8174"},  # rfc2119 references rfc8174
            set()  # rfc8174 has no references
        ]
        
        result = download_rfc_recursive("rfc9514", tmp_path, max_depth=2)
        
        assert len(result) == 3
        assert "rfc9514" in result
        assert "rfc2119" in result
        assert "rfc8174" in result