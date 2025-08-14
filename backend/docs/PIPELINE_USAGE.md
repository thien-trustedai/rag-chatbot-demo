# PDF Chat Pipeline - Complete Usage Guide

## Overview

The `pdf_chat_pipeline.py` script provides a unified workflow that:
1. Extracts content from PDFs (text, figures, tables)
2. Indexes the content into ChromaDB with embeddings
3. Starts an interactive chat interface for Q&A

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### Environment Variables (.env)

Create a `.env` file with your Azure OpenAI credentials:

```env
# Azure OpenAI for Embeddings
AZURE_OPENAI_EMBEDDING_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_EMBEDDING_API_KEY=your_key
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Azure OpenAI for Chat
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

## Basic Usage

### Complete Pipeline (Extract → Index → Chat)

```bash
python pdf_chat_pipeline.py document.pdf
```

This will:
1. Extract content from `document.pdf` to `pdf_extraction/` directory
2. Index the content into ChromaDB collection `pdf_documents`
3. Start an interactive chat interface

### Custom Output and Collection

```bash
python pdf_chat_pipeline.py document.pdf \
  --output my_extraction \
  --collection my_docs
```

### Clear and Reindex

```bash
python pdf_chat_pipeline.py document.pdf --clear
```

This clears any existing data in the collection before indexing.

## Advanced Options

### Skip Extraction (Use Existing)

If you've already extracted the PDF:

```bash
python pdf_chat_pipeline.py document.pdf \
  --skip-extraction \
  --output existing_extraction
```

### Skip Indexing (Use Existing Index)

If the content is already indexed:

```bash
python pdf_chat_pipeline.py document.pdf \
  --skip-indexing \
  --collection existing_collection
```

### Direct Chat (Skip Both Extraction and Indexing)

To chat with an already processed PDF:

```bash
python pdf_chat_pipeline.py document.pdf \
  --skip-extraction \
  --skip-indexing \
  --collection existing_collection
```

### Parallel Processing

Control the number of workers for extraction:

```bash
python pdf_chat_pipeline.py large_document.pdf --workers 8
```

### Use Local Embeddings

To use local sentence-transformers instead of Azure OpenAI:

```bash
python pdf_chat_pipeline.py document.pdf --no-azure
```

## Chat Interface Commands

Once in the chat interface:

- **help** - Show available commands
- **status** - Display collection statistics
- **history** - View conversation history
- **reset** - Clear conversation memory
- **verbose** - Toggle detailed output (shows references)
- **clear** - Clear the screen
- **quit/exit** - Exit the chat

## Example Workflow

### Process a New PDF

```bash
# 1. Process and chat with a PDF
python pdf_chat_pipeline.py research_paper.pdf --clear

# Output:
📄 Extracting PDF: research_paper.pdf
✓ Extraction complete!
  • Pages processed: 15
  • Figures extracted: 8
  • Tables extracted: 3
  • Text sections: 42

🔍 Indexing to ChromaDB
✓ Indexing complete!
  • Collection: pdf_documents
  • Documents indexed: 53
  • Text chunks: 42
  • Figures indexed: 8
  • Tables indexed: 3

💬 Starting Interactive Chat
Chat interface ready!

🤔 You: What are the main findings of this paper?
🤖 Assistant: Based on the paper, the main findings are...
```

### Resume Chat Later

```bash
# Later, resume chatting without re-processing
python pdf_chat_pipeline.py research_paper.pdf \
  --skip-extraction \
  --skip-indexing
```

## Pipeline Components

### 1. PDF Extraction
- Uses parallel processing for multi-page PDFs
- Extracts text with structure preservation
- Detects and extracts figures with captions
- Extracts tables as both CSV and images
- Generates structured metadata.json

### 2. ChromaDB Indexing
- Creates vector embeddings for all content
- Indexes text sections with page context
- Indexes figure/table captions for visual search
- Supports both Azure OpenAI and local embeddings

### 3. RAG Chat Interface
- Context-aware responses using retrieved content
- Maintains conversation history
- Shows source references in verbose mode
- Supports multi-turn conversations

## Output Structure

After extraction, the following structure is created:

```
output_directory/
├── metadata.json           # Structured document data
├── extracted_content.md    # Markdown version
├── figures/                # Extracted images
│   ├── page1_fig1.png
│   └── ...
└── tables/                 # Extracted tables
    ├── page1_table1.csv
    ├── page1_table1.png
    └── ...
```

## Troubleshooting

### "ChromaDB instance already exists with different settings"
- This occurs when multiple processes try to create clients with different settings
- Solution: Restart the Python process or use consistent settings

### "No Azure credentials found"
- Ensure `.env` file exists with correct Azure OpenAI credentials
- The script loads `.env` automatically

### "Extraction failed"
- Ensure Poppler is installed: `brew install poppler` (macOS)
- Check that the PDF file exists and is readable

### "Indexing failed - dimension mismatch"
- This occurs when switching between embedding models
- Solution: Use `--clear` flag to reset the collection

## Performance Tips

1. **Large PDFs**: Increase workers for faster extraction
   ```bash
   python pdf_chat_pipeline.py large.pdf --workers 8
   ```

2. **Multiple PDFs**: Process separately then index to same collection
   ```bash
   python pdf_chat_pipeline.py doc1.pdf --output doc1_extract
   python pdf_chat_pipeline.py doc2.pdf --output doc2_extract --skip-extraction
   ```

3. **Memory Usage**: For very large PDFs, process in batches
   ```bash
   # Extract first
   python pdf_chat_pipeline.py huge.pdf --output huge_extract
   # Then index separately if needed
   python pdf_chat_pipeline.py huge.pdf --skip-extraction
   ```

## API Integration

The pipeline components can also be used programmatically:

```python
from pdf_chat_pipeline import PDFChatPipeline

# Initialize pipeline
pipeline = PDFChatPipeline(
    pdf_path="document.pdf",
    output_dir="my_extraction",
    collection_name="my_docs",
    use_azure=True,
    clear_db=False,
    max_workers=4
)

# Run complete pipeline
pipeline.run()

# Or run steps individually
if pipeline.extract_pdf():
    if pipeline.index_to_chromadb():
        pipeline.start_chat()
```

## Next Steps

- Process multiple PDFs into the same collection for cross-document Q&A
- Experiment with different embedding models
- Adjust extraction parameters for specific document types
- Integrate with other applications using the API