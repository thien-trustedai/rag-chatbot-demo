# PDF RAG Chat System

## Overview

A complete Retrieval-Augmented Generation (RAG) system for chatting with PDF documents using Azure OpenAI. The system extracts text, figures, and tables from PDFs, indexes them in ChromaDB, and provides an interactive chat interface with vision capabilities.

## 🚀 Quick Start

```bash
# 1. Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure Azure OpenAI
cp .env.example .env
# Edit .env with your credentials

# 3. Process PDF and chat (all-in-one)
python pdf_chat_pipeline.py document.pdf

# Or run steps individually:
# python extractors/parallel_pdf_extractor.py document.pdf
# python rag/index_to_chromadb.py --use-openai --azure
# python rag/chat_with_pdf.py
```

## ✨ Key Features

- **🎯 One-Command Pipeline**: Extract, index, and chat with `pdf_chat_pipeline.py`
- **📄 PDF Processing**: Parallel extraction of text, figures, and tables
- **🔍 Semantic Search**: Vector-based retrieval using ChromaDB
- **🖼️ Vision Support**: Includes images in queries for visual Q&A
- **💬 Conversation Memory**: Maintains context across questions
- **🚀 Azure OpenAI**: Supports separate endpoints for embeddings and chat
- **📊 Rich UI**: Progress bars and formatted output with rich library

## 📁 Project Structure

```
app_new/
├── pdf_chat_pipeline.py         # 🎯 Main unified pipeline script
├── extract_pdf.py              # Entry point for extraction
│
├── extractors/                 # PDF extraction modules
│   ├── pdf_hybrid_extractor.py
│   ├── pdf_simple_extractor.py
│   └── parallel_pdf_extractor.py
│
├── core/                       # Core configuration and models
│   ├── pdf_extraction_config.py
│   └── pdf_extraction_models.py
│
├── processors/                 # Processing components
│   ├── text_processor.py
│   ├── image_extractor.py
│   ├── table_exporter.py
│   └── element_preprocessor.py
│
├── classifiers/               # Element classification
│   ├── element_classifier_simple.py
│   └── element_classifier_hybrid.py
│
├── utils/                     # Utility functions
│   ├── bbox_operations.py
│   ├── caption_detector.py
│   ├── file_manager.py
│   └── parallel_combiner.py
│
├── output/                    # Output generation code
│   ├── document_structure.py
│   └── markdown_generator.py
│
├── rag/                       # RAG system components
│   ├── index_to_chromadb.py
│   ├── rag_query.py
│   └── chat_with_pdf.py
│
└── docs/                      # Documentation
    ├── README.md
    ├── PIPELINE_USAGE.md
    └── PROJECT_STRUCTURE.md
```

## 🛠️ Components

### 1. PDF Extraction (`parallel_pdf_extractor.py`)
- Uses parallel processing for speed
- Extracts text with structure preservation
- Saves figures and tables as PNG images
- Generates comprehensive metadata

### 2. Vector Indexing (`index_to_chromadb.py`)
- Indexes text sections and visual elements
- Uses figure/table captions for embeddings
- Supports Azure OpenAI and local embeddings

### 3. RAG System (`rag_query.py`)
- Retrieves relevant content from ChromaDB
- Includes images in vision-capable models
- Maintains conversation history

### 4. Chat Interface (`chat_with_pdf.py`)
- Interactive command-line interface
- Conversation memory for context
- Built-in commands for control

## 💬 Chat Commands

- `help` - Show available commands
- `status` - Display collection statistics
- `history` - View conversation history
- `reset` - Clear conversation memory
- `verbose` - Toggle detailed output
- `quit` - Exit chat

## 📋 Requirements

### Software
- Python 3.8+
- Poppler (for PDF processing)
- Tesseract OCR (optional)

### Azure OpenAI
- Embedding model (e.g., text-embedding-ada-002)
- Chat model with vision (e.g., gpt-4)

## 🔧 Configuration

Create `.env` from template:

```env
# Embeddings
AZURE_OPENAI_EMBEDDING_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_EMBEDDING_API_KEY=your_key
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Chat/Vision
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

## 📚 Documentation

- **[RAG_USAGE.md](RAG_USAGE.md)** - Detailed usage instructions
- **[README_EXTRACTION.md](README_EXTRACTION.md)** - PDF extraction details

## 🐛 Troubleshooting

### Common Issues

1. **Embedding dimension mismatch**
   ```bash
   python index_to_chromadb.py --clear --use-openai --azure
   ```

2. **No images in responses**
   - Verify Azure model supports vision
   - Check images exist in `output/figures/`

3. **API errors**
   - Verify `.env` configuration
   - Check deployment names

## 📝 License

This project is for demonstration and educational purposes.