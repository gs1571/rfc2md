# RFC to Markdown Converter

A Python tool to convert RFC (Request for Comments) documents from XML format to well-formatted Markdown.

## Features

- **Fetch RFCs**: Download RFC documents directly from rfc-editor.org by RFC number
- **Recursive RFC Download**: Automatically download all referenced RFCs
- **Local Files**: Convert local RFC XML files
- **PDF Download**: Optionally download PDF versions alongside XML
- **Complete Conversion**: Preserves document structure including:
  - Metadata (title, authors, date, keywords, etc.)
  - Abstract and boilerplate sections
  - Section hierarchy (up to 6 levels)
  - Lists (ordered, unordered, definition)
  - Code blocks (artwork and sourcecode)
  - Tables with proper Markdown formatting
  - Figures with names
  - Inline formatting (bold, italic, inline code)
  - Internal cross-references
  - External links
  - References section (Normative and Informative)
  - Appendices
  - Table of Contents

## Installation

1. Clone this repository or download the files
2. Create a virtual environment (recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Convert from RFC Number

Download and convert an RFC by its number:

```bash
python3 rfc2md.py --rfc RFC9514
```

Or without the "RFC" prefix:

```bash
python3 rfc2md.py --rfc 9514
```

### Convert from Local File

Convert a local RFC XML file:

```bash
python3 rfc2md.py --file path/to/rfc9514.xml
```

### Recursive Download

Recursively download all RFCs referenced in the specified RFC:

```bash
# Recursive download with default depth (1 level)
python3 rfc2md.py --rfc 9514 --recursive
```

With custom recursion depth:

```bash
# Recursive download with depth 2
python3 rfc2md.py --rfc 9514 --recursive --max-depth 2
```

With PDF download:

```bash
# Recursive download with PDF
python3 rfc2md.py --rfc 9514 --recursive --pdf --output-dir downloads
```

### Download PDF

Download the PDF version alongside the XML:

```bash
python3 rfc2md.py --rfc 9514 --pdf
```

### Specify Output Directory

Save files to a specific directory:

```bash
python3 rfc2md.py --rfc 9514 --output-dir downloads
```

### Custom Output Filename

Specify a custom name for the Markdown output:

```bash
python3 rfc2md.py --file examples/rfc9514.xml --output custom-name.md
```

### Enable Debug Logging and Keep Source Files

Get detailed logging information and keep intermediate XML/HTML files:

```bash
python3 rfc2md.py --rfc 9514 --debug
```

**Note:** By default, intermediate XML/HTML files are automatically deleted after successful conversion to save disk space. Use the `--debug` flag to keep these files for inspection or debugging purposes.

**Behavior:**
- **Without `--debug`**: Only the final `.md` file is saved (and `.pdf` if requested)
- **With `--debug`**: Both source files (`.xml` or `.html`) and the final `.md` file are saved

## Complete Examples

```bash
# Download RFC 9514 with PDF to downloads directory
python3 rfc2md.py --rfc RFC9514 --pdf --output-dir downloads

# Download RFC 9514 and all its references recursively
python3 rfc2md.py --rfc 9514 --recursive --output-dir output

# Recursive download with depth 2 and debug logging
python3 rfc2md.py --rfc 9514 --recursive --max-depth 2 --debug

# Convert local file with custom output name
python3 rfc2md.py --file examples/rfc9514.xml --output output/my-rfc.md

# Download and convert with debug logging (keeps source files)
python3 rfc2md.py --rfc 9514 --output-dir output --debug

# Keep intermediate files for debugging
python3 rfc2md.py --rfc 9514 --debug --output-dir output

# Recursive download without keeping source files (saves disk space)
python3 rfc2md.py --rfc 9514 --recursive --output-dir output

# Recursive download with debug (keeps all XML/HTML files)
python3 rfc2md.py --rfc 9514 --recursive --debug --output-dir output
```

## Supported RFC XML Version

This tool supports **RFC XML v3** format as specified by the IETF. This is the current standard format used by rfc-editor.org.

## HTML Fallback Support

For older RFCs where XML format is not available, the tool provides HTML fallback conversion:

### Why HTML Fallback?

- Many older RFCs (pre-2010) are only available in HTML or plain text format
- HTML versions contain the complete RFC text in `<pre>` blocks
- Provides better structure preservation than plain text

### HTML Processing Approach

The HTML converter:
1. **Extracts text from `<pre>` blocks** - All RFC content is in preformatted blocks
2. **Removes HTML links** - Links cannot be correctly rendered in monospace markdown blocks
3. **Removes page breaks** - Cleans up pagination artifacts (headers, footers, page numbers)
4. **Processes Table of Contents** - Converts to clickable markdown links
5. **Identifies sections** - Extracts section headers and creates anchors
6. **Wraps in markdown pre blocks** - Preserves monospace formatting with ` ```text ``` `

### Why Links Are Removed

HTML RFC files contain inline links (e.g., `<a href="#section-1">1</a>`). These links:
- Cannot be preserved in monospace markdown blocks without breaking formatting
- Would appear as raw HTML in the output
- Are replaced with internal section anchors in the Table of Contents

### Output Format

HTML-converted RFCs have a simplified structure:
- Document title as H1 header
- Table of Contents with clickable section links
- Content wrapped in ` ```text ``` ` blocks
- Section headers as monospace with anchors
- No HTML metadata in output

### Usage

HTML conversion is automatic when XML is not available:

```bash
# Automatically uses HTML if XML not found
python3 rfc2md.py --rfc 7752

# Explicit HTML file conversion
python3 rfc2md.py --file examples/rfc7752.html
```

## Output Format

The converter generates GitHub Flavored Markdown (GFM) for maximum compatibility with:
- GitHub
- GitLab
- VS Code
- Most Markdown viewers and editors

## Known Limitations

- Only supports RFC XML v3 format
- Some complex table layouts may require manual adjustment
- Nested structures beyond 6 levels are flattened to level 6 (Markdown limitation)
- Recursive download respects already downloaded files (skips re-download but always reconverts)

## Project Structure

```
.
├── rfc2md.py              # Main CLI entry point
├── lib/                   # Library modules
│   ├── __init__.py       # Package initialization
│   ├── converter.py      # XmlToMdConverter class
│   ├── downloader.py     # RFC download functionality
│   └── utils.py          # Utility functions
├── tests/                 # Test suite
│   ├── __init__.py
│   └── test_utils.py     # Unit tests
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── ruff.toml             # Ruff linter configuration
├── mypy.ini              # mypy type checker configuration
├── pytest.ini            # pytest configuration
├── Makefile              # Development commands
├── .github/
│   └── workflows/
│       └── lint.yml      # GitHub Actions CI/CD
├── README.md             # This file
├── examples/             # Example RFC files for testing
└── output/               # Default output directory
```

## Dependencies

### Production
- **requests** (>=2.31.0): For downloading RFC files from rfc-editor.org
- **lxml** (>=4.9.0): For robust XML parsing with namespace support

### Development
- **ruff** (0.1.15): Modern Python linter and formatter
- **mypy** (1.8.0): Static type checker
- **pytest** (7.4.4): Testing framework
- **pytest-cov** (4.1.0): Code coverage plugin

## Development

### Setup Development Environment

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run all checks:
   ```bash
   make all
   ```

### Available Make Commands

- `make install` - Install production dependencies
- `make install-dev` - Install development dependencies
- `make lint` - Run ruff linter
- `make format` - Format code with ruff
- `make type-check` - Run mypy type checker
- `make test` - Run tests with coverage
- `make all` - Run all checks (lint, format-check, type-check, test)
- `make clean` - Remove cache and build artifacts

### Code Quality

The project uses:
- **Ruff** for linting and formatting (replaces flake8, pylint, isort, black)
- **mypy** for static type checking
- **pytest** for testing with coverage reporting
- **GitHub Actions** for CI/CD

All code must pass linting, type checking, and tests before merging.

### Architecture

The converter is organized into modular components:

**lib/converter.py** - Main conversion logic:
- `XmlToMdConverter` class with methods for processing RFC XML elements
- `_process_front()`: Metadata and abstract
- `_process_middle()`: Main document content
- `_process_back()`: References and appendices
- `_process_section()`: Recursive section processing
- `_process_list()`: List handling
- `_process_table()`: Table conversion
- `_process_figure()`: Figure and code block processing
- `_generate_toc()`: Table of Contents generation

**lib/downloader.py** - RFC download functionality:
- `download_rfc()`: Fetch XML and PDF files from rfc-editor.org
- `download_rfc_recursive()`: Recursively download referenced RFCs

**lib/utils.py** - Utility functions:
- `setup_logging()`: Configure logging
- `normalize_rfc_number()`: Normalize RFC number input
- `extract_rfc_references()`: Extract RFC references from XML files

## Contributing

Contributions are welcome! Areas for improvement:
- Support for additional RFC XML versions
- Enhanced table formatting
- Additional output formats (HTML, PDF, etc.)
- Performance optimizations for large documents

## License

See LICENSE file for details.

## Author

Created as part of the RFC documentation tooling project.

## References

- [RFC Editor](https://www.rfc-editor.org/)
- [RFC XML v3 Specification](https://www.rfc-editor.org/rfc/rfc7991.html)
- [GitHub Flavored Markdown](https://github.github.com/gfm/)