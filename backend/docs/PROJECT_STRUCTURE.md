# Project Structure

The codebase has been reorganized into a clean, modular structure:

## Directory Layout

```
.
├── extractors/              # Main extraction modules
│   ├── pdf_hybrid_extractor.py    # Hybrid extraction with dual strategies
│   ├── pdf_simple_extractor.py    # Simple single-page extractor
│   └── parallel_pdf_extractor.py  # Parallel multi-page processor
│
├── core/                    # Core models and configuration
│   ├── pdf_extraction_config.py   # Constants and configuration
│   └── pdf_extraction_models.py   # Data models and structures
│
├── processors/              # Processing components
│   ├── text_processor.py          # Text element processing
│   ├── image_extractor.py         # Image/figure extraction
│   ├── table_exporter.py          # Table data export
│   └── element_preprocessor.py    # Element preprocessing
│
├── classifiers/             # Classification components
│   ├── element_classifier_simple.py  # Basic element classification
│   └── element_classifier_hybrid.py  # Advanced hybrid classification
│
├── utils/                   # Utility modules
│   ├── bbox_operations.py         # Bounding box operations
│   ├── caption_detector.py        # Caption detection/extraction
│   ├── file_manager.py            # File and PDF management
│   └── parallel_combiner.py      # Parallel result combination
│
├── output/                  # Output generation
│   ├── document_structure.py      # Document structure building
│   └── markdown_generator.py      # Markdown output generation
│
├── rag/                     # RAG system components
│   ├── index_to_chromadb.py      # ChromaDB indexing
│   ├── rag_query.py               # RAG query system
│   └── chat_with_pdf.py          # Interactive chat interface
│
└── extract_pdf.py          # Main entry point script
```

## Key Improvements

1. **Clear Separation of Concerns**
   - Core configuration and models separated from implementation
   - Processing logic isolated in dedicated modules
   - Clean distinction between extractors, processors, and utilities

2. **Logical Grouping**
   - Related functionality grouped in directories
   - RAG system components isolated from extraction logic
   - Output generation separated from processing

3. **Consistent Naming**
   - Main extractors retain `pdf_` prefix for clarity
   - Utility modules have descriptive names without redundant prefixes
   - Clear distinction between simple and hybrid approaches

## Usage

Main entry point for PDF extraction:
```bash
python extract_pdf.py <pdf_file> [output_dir] [max_workers] [dpi]
```

Example:
```bash
python extract_pdf.py document.pdf my_output 4 150
```

## Module Dependencies

- **Extractors** depend on all other modules
- **Processors** depend on core and utils
- **Classifiers** depend on core and utils
- **Utils** depend only on core
- **Output** depends on core
- **RAG** depends on extraction results

This structure ensures clean dependencies and makes the codebase easier to maintain and extend.