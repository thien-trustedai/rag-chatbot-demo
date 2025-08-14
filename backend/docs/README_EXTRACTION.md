# PDF Extraction Experiments

This directory contains scripts for extracting figures, tables, and text from PDF documents.

## Scripts

### `hybrid_pdf_extractor.py`
The main hybrid extraction script that combines the best of both extraction strategies:
- **Hi-res mode**: For accurate figure/table detection and text element classification
- **Fast mode**: For clean text extraction without OCR artifacts
- **Smart merging**: Automatically merges related elements (e.g., figure legends with figures)
- **Caption detection**: Finds and assigns captions to figures and tables
- **Text classification matching**: Applies ML-based classifications from hi-res to clean fast-mode text

**Usage:**
```bash
python hybrid_pdf_extractor.py <pdf_file> [output_dir] [dpi]

# Example:
python hybrid_pdf_extractor.py data/document.pdf output_folder 150
```

**Output:**
- `clean_text.md`: Markdown file with properly structured text, figures, and tables
- `figures/`: Directory containing extracted figure images
- `tables/`: Directory containing extracted table images and data

### `extract_all_elements.py`
Standalone figure and table extraction script with smart reclassification:
- Extracts figures and tables using hi-res strategy
- Reclassifies misidentified elements based on captions and content
- Merges adjacent elements that belong together

**Usage:**
```bash
python extract_all_elements.py <pdf_file> [output_dir] [dpi]

# Example:
python extract_all_elements.py data/document.pdf extracted_elements 300
```

## Key Features

1. **Hybrid Extraction**: Combines multiple extraction strategies for optimal results
2. **Smart Classification**: Uses ML models to properly classify text elements (Title, Header, ListItem, etc.)
3. **Automatic Merging**: Identifies and merges related elements (e.g., legends above figures)
4. **Caption Assignment**: Automatically finds and assigns captions to visual elements
5. **Clean Text Output**: Filters out text within figures/tables for clean extraction
6. **Coordinate Scaling**: Properly handles different coordinate systems between extraction modes

## Dependencies

```bash
pip install unstructured
pip install unstructured[pdf]
pip install PyMuPDF
pip install pandas
pip install pillow
```

## Test Data

The `data/` directory contains sample PDF pages for testing the extraction scripts.