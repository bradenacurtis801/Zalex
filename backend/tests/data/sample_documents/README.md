# Sample Documents for Testing

This directory contains sample documents used for testing the backend.

## File Types

- **PDFs**: Sample PDF documents for testing OCR and text extraction
- **Images**: Sample image files (PNG, JPG, etc.) for testing image OCR
- **Corrupted Files**: Intentionally corrupted files for testing error handling
- **Large Files**: Large files for testing memory management and performance

## Usage

These files are referenced in test fixtures and should be committed to the repository
for consistent testing across different environments.

## Adding New Test Files

When adding new test files:
1. Keep file sizes reasonable (under 1MB for most tests)
2. Use descriptive names that indicate the test purpose
3. Update the corresponding test fixtures to reference new files
4. Document any special characteristics of the files
