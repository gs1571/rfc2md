# Tests

## Overview

This project includes comprehensive testing with two types of tests:
- **Unit tests**: Test individual functions and classes in isolation
- **Integration tests**: Test complete RFC conversion with snapshot comparison

## Test Structure

```
tests/
├── __init__.py
├── README.md                    # This file
├── test_utils.py               # Unit tests for utility functions
├── test_html_converter.py      # Unit tests for HTML converter
├── test_integration.py         # Integration tests with snapshots
├── fixtures/                   # Test input files
│   ├── xml/                   # XML RFC files for testing
│   └── html/                  # HTML RFC files for testing
└── snapshots/                  # Expected MD outputs (snapshots)
```

## Integration Tests (Snapshot Testing)

Integration tests use snapshot testing approach:

1. **Source files** are stored in `tests/fixtures/xml/` and `tests/fixtures/html/`
2. **Expected outputs** (snapshots) are stored in `tests/snapshots/`
3. **Test process**:
   - Convert source file (XML or HTML) to Markdown
   - Compare generated MD with snapshot
   - If mismatch: show diff and regeneration command
   - If match: test passes

### Why Separate XML and HTML?

HTML is a strict fallback when XML is not available. We test both formats separately:
- `TestXmlConversion` - tests all XML files from `tests/fixtures/xml/`
- `TestHtmlConversion` - tests all HTML files from `tests/fixtures/html/`

This ensures no duplication and clear separation of concerns.

## Running Tests

### All tests
```bash
source .venv/bin/activate && pytest
```

### Unit tests only
```bash
source .venv/bin/activate && pytest -m "not integration"
```

### Integration tests only
```bash
source .venv/bin/activate && pytest -m integration
```

### Specific test class
```bash
# XML conversion tests
source .venv/bin/activate && pytest tests/test_integration.py::TestXmlConversion -v

# HTML conversion tests
source .venv/bin/activate && pytest tests/test_integration.py::TestHtmlConversion -v
```

### Specific RFC test
```bash
# Test specific XML file
source .venv/bin/activate && pytest tests/test_integration.py::TestXmlConversion::test_xml_to_markdown_conversion[rfc9514.xml] -v

# Test specific HTML file
source .venv/bin/activate && pytest tests/test_integration.py::TestHtmlConversion::test_html_to_markdown_conversion[rfc7752.html] -v
```

### With coverage report
```bash
source .venv/bin/activate && pytest --cov=lib --cov-report=html
```

## Updating Snapshots

When you intentionally change conversion logic and need to update snapshots:

### Update single snapshot
```bash
# For XML file
source .venv/bin/activate && python rfc2md.py --file tests/fixtures/xml/rfc9514.xml --output tests/snapshots/rfc9514.md

# For HTML file
source .venv/bin/activate && python rfc2md.py --file tests/fixtures/html/rfc7752.html --output tests/snapshots/rfc7752.md
```

### Update all snapshots
```bash
# Update all XML snapshots
for file in tests/fixtures/xml/*.xml; do
    base=$(basename "$file" .xml)
    source .venv/bin/activate && python rfc2md.py --file "$file" --output "tests/snapshots/$base.md"
done

# Update all HTML snapshots
for file in tests/fixtures/html/*.html; do
    base=$(basename "$file" .html)
    source .venv/bin/activate && python rfc2md.py --file "$file" --output "tests/snapshots/$base.md"
done
```

## Debugging Failed Tests

When integration test fails:

1. **Read the diff** - test output shows unified diff between expected and actual
2. **Check if change is intentional**:
   - If YES: update snapshot using command from test output
   - If NO: fix the bug in conversion code
3. **Re-run test** to verify fix

Example test failure output:
```
================================================================================
Snapshot mismatch for rfc9514!
================================================================================

Diff:
--- snapshot/rfc9514.md
+++ generated/rfc9514.md
@@ -10,7 +10,7 @@
-Old line
+New line

================================================================================
To update snapshot, run:
source .venv/bin/activate && python rfc2md.py --file tests/fixtures/xml/rfc9514.xml --output tests/snapshots/rfc9514.md
================================================================================
```

## Test Markers

Tests use pytest markers for categorization:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower, end-to-end)
- `@pytest.mark.slow` - Slow-running tests

Run tests by marker:
```bash
# Only unit tests
pytest -m unit

# Only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```

## Adding New Tests

### Adding new RFC for testing

1. Add source file to appropriate fixtures folder:
   - XML: `tests/fixtures/xml/rfcXXXX.xml`
   - HTML: `tests/fixtures/html/rfcXXXX.html`

2. Generate initial snapshot:
   ```bash
   source .venv/bin/activate && python rfc2md.py --file tests/fixtures/xml/rfcXXXX.xml --output tests/snapshots/rfcXXXX.md
   ```

3. Run tests to verify:
   ```bash
   source .venv/bin/activate && pytest tests/test_integration.py -v
   ```

The parametrized tests will automatically pick up new files!

## Continuous Integration

Tests run automatically on:
- Every commit (via GitHub Actions)
- Pull requests
- Before merging to main branch

CI runs:
- Linting (ruff)
- Type checking (mypy)
- Unit tests
- Integration tests
- Coverage reporting