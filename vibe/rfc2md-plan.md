**Task**:
Develop a Python script `rfc2md.py` to fetch RFC documents from `rfc-editor.org` in XML format (and optionally PDF) and convert the XML content into a well-formatted Markdown file. The script should handle local XML files or fetch them by RFC number. Key requirements include generating a Table of Contents, preserving monospace formatting (artwork/sourcecode), maintaining all internal and external links, and properly handling RFC-specific elements like boilerplate, tables, and figures.

**Plan Structure**:
1.  **Project Setup & CLI**: Define project structure and implement command-line argument parsing.
2.  **Downloader Module**: Implement functionality to fetch XML and PDF files from the IETF website.
3.  **XML Parsing & Markdown Conversion (Basic)**: Implement the core logic to parse RFC XML v3 and convert basic structure (headers, paragraphs) to Markdown.
4.  **Advanced Formatting & Elements**: Handle lists, code blocks (artwork), tables, figures, and inline formatting.
5.  **References & Links**: Implement processing of internal cross-references (`xref`) and external links (`eref`), and generate the References section.
6.  **TOC & Final Polish**: Generate the Table of Contents and assemble the final Markdown document.
7.  **Testing & Validation**: Verify output against reference documents and handle edge cases.

**Execution Plan**:

### Stage 1: Project Setup & CLI
**What to add/implement:**
*   Create `rfc2md.py` with `argparse` setup.
*   Define arguments:
    *   `--rfc`: RFC number (e.g., "RFC9514" or "9514").
    *   `--file`: Path to local XML file (alternative to `--rfc`).
    *   `--pdf`: Flag to download PDF.
    *   `--output-dir`: Directory to save downloaded/generated files (default: current directory).
    *   `--output`: Custom output filename for the Markdown file (optional).
*   Ensure either `--rfc` or `--file` is provided (mutually exclusive).
*   Implement input normalization for `--rfc`: ensure it starts with "rfc" (case-insensitive) for URL construction.
*   Setup basic logging configuration with levels (INFO, DEBUG, ERROR).
*   Create `requirements.txt` with `requests` and `lxml` (for robust XML parsing).
**Files to edit/create:**
*   `rfc2md.py` - Main script entry point.
*   `requirements.txt` - Dependencies.
**Verification commands:**
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Test CLI
python3 rfc2md.py --help
python3 rfc2md.py --rfc RFC9514  # should print placeholder message or start processing
```

### Stage 2: Downloader Module
**What to add/implement:**
*   Implement `download_rfc(rfc_number, output_dir, fetch_pdf=False)` function in `rfc2md.py`.
*   Construct URLs: `https://www.rfc-editor.org/rfc/rfc{number}.xml`.
*   For PDF, handle fallback URLs: try `https://www.rfc-editor.org/rfc/rfc{number}.pdf` first, and if 404, try `https://www.rfc-editor.org/rfc/rfc{number}.txt.pdf`.
*   Use `requests` to fetch content with proper error handling and timeouts.
*   Save files to `output_dir` with appropriate names (e.g., `rfc9514.xml`, `rfc9514.pdf`).
*   Handle HTTP errors (404, 500, network errors) with informative messages.
*   Add progress indication for downloads.
**Files to edit/create:**
*   `rfc2md.py` - Add download logic.
**Framework/Library Documentation:**
*   [Requests Documentation](https://requests.readthedocs.io/en/latest/)
**Verification commands:**
```bash
# Activate virtual environment if not already active
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Test download functionality
python3 rfc2md.py --rfc RFC9514 --pdf --output-dir downloads
# Should download rfc9514.xml and rfc9514.pdf to downloads dir

# Test error handling
python3 rfc2md.py --rfc 9999999 --output-dir downloads
# Should handle 404 gracefully
```

### Stage 3: XML Parsing & Markdown Conversion (Basic)
**What to add/implement:**
*   Implement `XmlToMdConverter` class in `rfc2md.py`.
*   Use `xml.etree.ElementTree` or `lxml.etree` to parse the XML file (prefer lxml for better namespace handling).
*   Implement `convert()` method to traverse the XML tree.
*   Handle `<front>` section:
    *   Extract title from `<title>` tag (including `abbrev` attribute for short title if present).
    *   Extract `<seriesInfo>` (RFC number, stream type).
    *   Extract authors from `<author>` tags (fullname, initials, surname, organization, email, address).
        *   Handle `role="editor"` attribute to mark editors.
    *   Extract date from `<date>` tag (month, year, day if present).
    *   Extract `<area>` and `<workgroup>` tags for organizational information.
    *   Extract `<keyword>` tags.
    *   Extract abstract from `<abstract>` section.
    *   Extract boilerplate sections (`<boilerplate>`) - "Status of This Memo" and "Copyright Notice".
    *   Extract `<link>` elements for related document links (prev, alternate, etc.).
*   Handle `<middle>` section:
    *   Iterate over `<section>` tags recursively.
*   Implement `_parse_section` method:
    *   Map `<section>` nesting depth to Markdown headers (`#`, `##`, `###`, `####`, `#####`, `######`).
    *   Extract `<name>` for header text.
    *   Handle `anchor` attribute for creating HTML anchors.
    *   Map `<t>` tags to paragraphs.
    *   Handle `indent` attribute for proper paragraph formatting.
*   Output the generated Markdown to a file (e.g., `rfc9514.md`).
*   Preserve XML namespace handling (xmlns attributes).
**Files to edit/create:**
*   `rfc2md.py` - Add parsing and conversion logic.
**Examples in existing code:**
*   `examples/rfc9514.xml` - Source XML for testing (lines 1-300 for initial testing).
*   `examples/rfc9514.html`, `examples/rfc9514_v2.html`, `examples/rfc9514.txt` - Reference documents in different formats for comparison of structure and rendering.
**Verification commands:**
```bash
# Activate virtual environment if not already active
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Test basic conversion
python3 rfc2md.py --file examples/rfc9514.xml --output-dir output
# Should produce output/rfc9514.md with title, authors, abstract, and basic section headers

# Compare structure
diff output/rfc9514.md examples/rfc9514.txt  # or use your preferred diff tool
```

### Stage 4: Advanced Formatting & Elements
**What to add/implement:**
*   Extend `XmlToMdConverter` to handle specific XML tags:
    *   `<figure>` and `<artwork>`: Convert to Markdown code blocks with triple backticks. Preserve whitespace and line breaks. Include figure name if present.
    *   `<sourcecode>`: Similar to `<artwork>`, but may include language specification in `type` attribute.
    *   `<ul>`, `<ol>`: Convert to Markdown lists (`-` or `1.`). Handle nesting properly with indentation.
    *   `<dl>`, `<dt>`, `<dd>`: Convert to Markdown definition lists (use `**term**` followed by indented description).
    *   `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>`: Convert to Markdown tables with proper alignment.
    *   Inline formatting:
        *   `<bcp14>`: Convert to **BOLD** (for MUST, SHOULD, etc.).
        *   `<em>`: Convert to *italic*.
        *   `<strong>`: Convert to **bold**.
        *   `<tt>`: Convert to `inline code`.
        *   `<contact>`: Keep as plain text or format as needed.
        *   Handle HTML entities: `&amp;` → `&`, `&lt;` → `<`, `&gt;` → `>`, etc.
    *   `<note>`: Format as blockquotes (prefix lines with `>`).
*   Handle nested structures properly (e.g., lists within lists, tables with complex content).
*   Preserve `pn` (paragraph number) attributes for reference if needed.
**Files to edit/create:**
*   `rfc2md.py` - Add handlers for these tags.
**Examples in existing code:**
*   `examples/rfc9514.xml` - Contains `<artwork>` (lines 379-387, 449-467), `<sourcecode>`, `<table>` (lines 968-984), various list types (lines 306-314, 317-326), and inline formatting.
*   `examples/rfc9514.txt` - Reference for how monospace blocks and lists should look in plain text.
**Verification commands:**
```bash
# Activate virtual environment if not already active
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Test advanced formatting
python3 rfc2md.py --file examples/rfc9514.xml --output-dir output

# Verify output
# - Check output/rfc9514.md for correct code blocks, lists, tables, and inline formatting
# - Verify that artwork blocks preserve exact spacing and alignment
# - Check that tables render correctly in Markdown preview (VS Code, GitHub, etc.)
```

### Stage 5: References & Links
**What to add/implement:**
*   Implement link processing in `XmlToMdConverter`:
    *   `<xref target="...">`: Convert to Markdown links.
        *   If `target` starts with `#`, create internal link: `[text](#target)`.
        *   If `target` is a reference ID (e.g., "RFC2119"), link to references section: `[text](#RFC2119)`.
        *   Handle `format` attribute (counter, title, default) to determine link text.
        *   Use `derivedContent` attribute for link text if available.
    *   `<eref target="...">`: Convert to external links: `[text](url)`.
        *   Use element text or `target` as link text.
*   Process `<back>` section:
    *   Handle `<displayreference>` tags to map reference anchors to display names (e.g., `I-D.ietf-spring-srv6-yang` → `SRV6-YANG`).
    *   Handle `<references>` and `<reference>` tags to generate a "References" section.
    *   Create two subsections: "Normative References" and "Informative References" if both exist.
    *   For each reference, extract:
        *   `anchor` attribute for reference ID.
        *   `<front>/<title>` for document title.
        *   `<author>` information (fullname, initials, surname, organization).
        *   `<seriesInfo>` for RFC number, DOI, BCP, Internet-Draft, etc.
        *   `<date>` for publication date.
        *   `<refcontent>` for additional reference information (e.g., "Work in Progress").
        *   `target` attribute for reference URL.
    *   Format references in a consistent style (e.g., `[RFC2119] Bradner, S., "Key words...", BCP 14, RFC 2119, March 1997.`).
    *   Use display names from `<displayreference>` when formatting reference links.
*   Ensure `<section anchor="...">` attributes are used to generate HTML anchors in Markdown (e.g., `<a name="section-1"></a>` or use header IDs).
*   Handle appendices in `<back>` section similarly to regular sections.
*   Handle special unnumbered sections: `numbered="false"` attribute.
**Files to edit/create:**
*   `rfc2md.py` - Add link processing logic.
**Examples in existing code:**
*   `examples/rfc9514.xml` - Contains many `<xref>` (lines 248, 250, 256, etc.) and `<eref>` (line 105) examples.
*   References section starts at line 1158.
**Verification commands:**
```bash
# Activate virtual environment if not already active
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Test links and references
python3 rfc2md.py --file examples/rfc9514.xml --output-dir output

# Verify output
# - Check output/rfc9514.md that links are clickable and lead to correct sections/references
# - Test internal links by clicking them in a Markdown viewer
# - Verify external links open correct URLs
```

### Stage 6: TOC & Final Polish
**What to add/implement:**
*   Implement TOC generation:
    *   Option 1: Extract TOC from XML `<toc>` section if present (lines 127-242 in example).
    *   Option 2: Generate TOC by collecting all headers and their anchors during the parsing pass.
    *   Create a Markdown list of links at the beginning of the document.
    *   Include section numbers if present in XML.
*   Finalize file output:
    *   Ensure TOC is inserted after the metadata/abstract and before the first section.
    *   Add proper spacing between sections.
    *   Ensure all anchors are properly formatted for Markdown compatibility.
*   Handle special sections:
    *   Acknowledgements (line 1459).
    *   Contributors (line 1471).
    *   Authors' Addresses (line 1519).
*   Create `README.md` with:
    *   Project description.
    *   Installation instructions (`pip install -r requirements.txt`).
    *   Usage examples with all CLI options.
    *   Supported RFC XML version (v3).
    *   Known limitations.
*   Add comprehensive docstrings and comments in English to all functions and classes.
*   Implement proper error handling and user-friendly error messages.
**Files to edit/create:**
*   `rfc2md.py` - Add TOC generation and final polish.
*   `README.md` - Documentation.
**Verification commands:**
```bash
# Activate virtual environment if not already active
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Test TOC generation with remote RFC
python3 rfc2md.py --rfc RFC9514 --output-dir output
# Should produce output/rfc9514.md with complete TOC

# Test with custom output filename
python3 rfc2md.py --file examples/rfc9514.xml --output output/custom.md
# Should produce output/custom.md

# Verify output
# - Check that TOC links work in Markdown viewer
# - Verify all sections are properly formatted and readable
# - Review README.md for completeness
```

### Stage 7: Testing & Validation
**What to add/implement:**
*   Create test suite (optional but recommended):
    *   Test XML parsing with various RFC documents.
    *   Test edge cases (empty sections, missing elements, malformed XML).
    *   Test all CLI argument combinations.
*   Manual validation:
    *   Compare generated Markdown with reference HTML and TXT versions.
    *   Verify all links work correctly.
    *   Check that code blocks preserve formatting.
    *   Ensure tables render correctly.
    *   Validate that special characters are properly escaped.
*   Test with multiple RFC documents:
    *   Try with different RFC numbers (e.g., RFC2119, RFC8174, RFC7752).
    *   Verify handling of different XML structures and edge cases.
*   Performance testing:
    *   Measure conversion time for large RFC documents.
    *   Optimize if necessary.
*   Create a checklist of features to verify:
    - [ ] Title and metadata extraction (including abbrev)
    - [ ] SeriesInfo (RFC number, stream)
    - [ ] Authors and affiliations (including editor role)
    - [ ] Date (month, year, day)
    - [ ] Area and workgroup
    - [ ] Keywords
    - [ ] Abstract formatting
    - [ ] Boilerplate sections
    - [ ] Related document links
    - [ ] Section hierarchy (up to 6 levels)
    - [ ] Paragraphs with proper indentation
    - [ ] Unordered lists
    - [ ] Ordered lists
    - [ ] Definition lists
    - [ ] Nested lists
    - [ ] Code blocks (artwork/sourcecode)
    - [ ] Figures with names
    - [ ] Tables with headers
    - [ ] Inline code
    - [ ] Bold text (bcp14, strong)
    - [ ] Italic text (em)
    - [ ] Internal links (xref)
    - [ ] External links (eref)
    - [ ] References section
    - [ ] Appendices
    - [ ] Table of Contents
    - [ ] Acknowledgements
    - [ ] Contributors
    - [ ] Authors' Addresses
    - [ ] HTML entity handling (&amp;, &lt;, &gt;)
    - [ ] Display reference mapping
    - [ ] Unnumbered sections
    - [ ] Reference URLs and refcontent
**Files to edit/create:**
*   `tests/` directory (optional) - Unit tests.
*   `TESTING.md` (optional) - Testing documentation.
**Verification commands:**
```bash
# Activate virtual environment if not already active
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run comprehensive tests
python3 rfc2md.py --file examples/rfc9514.xml --output-dir output

# Compare outputs
# - Compare output/rfc9514.md with examples/rfc9514.html and examples/rfc9514.txt for completeness
# - Open generated Markdown in different viewers (VS Code, GitHub, etc.) to verify rendering

# Test error handling
python3 rfc2md.py --file nonexistent.xml
# Should show clear error message

# Test with different RFCs
python3 rfc2md.py --rfc RFC2119 --output-dir output
python3 rfc2md.py --rfc RFC8174 --output-dir output
python3 rfc2md.py --rfc RFC7752 --output-dir output

# Run unit tests if created
# python3 -m pytest tests/
```

**Additional Considerations**:

1. **XML Namespace Handling**: RFC XML v3 uses namespaces (`xmlns:xi="http://www.w3.org/2001/XInclude"`). Ensure proper handling with lxml or ElementTree namespace support.

2. **Character Encoding**: Ensure UTF-8 encoding for both input and output files. Handle XML entities properly (`&amp;`, `&lt;`, `&gt;`, `&quot;`, `&apos;`).

3. **Markdown Flavor**: Target GitHub Flavored Markdown (GFM) for maximum compatibility.

4. **Performance**: For large RFC documents, consider streaming or incremental processing if memory becomes an issue.

5. **Extensibility**: Design the converter to be easily extensible for future RFC XML versions or additional output formats.

6. **Logging**: Implement detailed logging for debugging and tracking conversion progress.

7. **Configuration**: Consider adding a configuration file for customizing output format (e.g., TOC style, reference format).

8. **Attribute Handling**: Many XML elements have important attributes:
   - `anchor` - for creating internal links
   - `numbered` - to determine if section should be numbered
   - `role` - for author roles (editor, etc.)
   - `abbrev` - for abbreviated titles
   - `target` - for external links
   - `format`, `sectionFormat`, `derivedContent` - for xref formatting

9. **Special Characters**: Properly escape Markdown special characters when needed (e.g., `*`, `_`, `[`, `]`, `#`, etc.) in regular text to prevent unintended formatting.