# RAG System Usage Guide

## Overview
This RAG (Retrieval-Augmented Generation) system allows you to chat with your PDF documents using Azure OpenAI. It retrieves relevant text sections and visual elements (figures/tables) to answer your questions.

## Prerequisites

1. **Environment Setup**
   ```bash
   # Activate virtual environment
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements_chromadb.txt
   ```

2. **Azure OpenAI Configuration**
   Create a `.env` file with your Azure OpenAI credentials:
   ```env
   # Embedding endpoint and credentials
   AZURE_OPENAI_EMBEDDING_ENDPOINT=https://your-embedding-resource.openai.azure.com/
   AZURE_OPENAI_EMBEDDING_API_KEY=your_embedding_api_key
   AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
   
   # LLM endpoint and credentials
   AZURE_OPENAI_ENDPOINT=https://your-llm-resource.openai.azure.com/
   AZURE_OPENAI_API_KEY=your_llm_api_key
   AZURE_OPENAI_DEPLOYMENT=gpt-4
   AZURE_OPENAI_API_VERSION=2025-01-01-preview
   ```

## Step-by-Step Usage

### 1. Extract PDF Content
First, extract content from your PDF:
```bash
python parallel_pdf_extractor.py your_document.pdf
```
This creates an `output/` directory with:
- `metadata.json` - Structured document data
- `figures/` - Extracted figures
- `tables/` - Extracted tables
- `extracted_content.md` - Markdown version

### 2. Index to ChromaDB
Index the extracted content into the vector database:
```bash
# Index with Azure OpenAI embeddings
python index_to_chromadb.py --use-openai --azure

# Or clear and reindex
python index_to_chromadb.py --use-openai --azure --clear
```

### 3. Chat with Your PDF
Start the interactive chat:
```bash
python chat_with_pdf.py
```

Or ask a single question:
```bash
python rag_query.py "What are the main findings in the document?"
```

## Interactive Chat Commands

When using `chat_with_pdf.py`:
- `help` - Show available commands
- `status` - Show collection statistics
- `history` - View conversation history
- `reset` - Clear conversation history (start fresh)
- `verbose` - Toggle detailed output
- `clear` - Clear the screen
- `quit/exit` - Exit the chat

### Conversation Memory
The chat system maintains conversation history, allowing you to:
- Ask follow-up questions that reference previous answers
- Have contextual discussions about the document
- Build on previous queries without repeating context

Example conversation:
```
You: What tables are in the document?
Assistant: [Lists tables...]

You: Tell me more about the second one
Assistant: [Provides details about the second table, understanding the reference]

You: What data does it contain?
Assistant: [Explains the data in that specific table]
```

## Example Questions

- "What figures are shown in the document?"
- "Summarize the content on page 3"
- "What does Table 2 show?"
- "Explain the methodology described in the document"
- "What are the key findings?"

## Advanced Usage

### Search Only (No Indexing)
```bash
python index_to_chromadb.py --search-only --search "your query"
```

### Custom Collection Names
```bash
# Index to custom collection
python index_to_chromadb.py --collection my_papers

# Query custom collection
python rag_query.py --collection my_papers "your question"
```

### Verbose Mode
See what's being retrieved:
```bash
python rag_query.py --n-results 10 "your question"
```

## Troubleshooting

### Embedding Dimension Mismatch
If you get "Collection expecting embedding with dimension of 1536, got 384":
- The collection was indexed with different embeddings
- Solution: Clear and reindex with consistent settings
```bash
python index_to_chromadb.py --use-openai --azure --clear
```

### Azure OpenAI Errors
- Verify your deployment names in `.env`
- Ensure you have separate deployments for embeddings and chat
- Check API versions match your Azure resource

### No Results Found
- Verify documents are indexed: `python index_to_chromadb.py --search-only --search "test"`
- Check the `output/metadata.json` file exists and contains data
- Try broader search terms

## Architecture

```
PDF Document
    ↓
[PDF Extractor]
    ↓
metadata.json + images
    ↓
[ChromaDB Indexer]
    ↓
Vector Database
    ↓
[RAG Query System]
    ↓
Azure OpenAI Response
```

## Key Components

1. **parallel_pdf_extractor.py** - Extracts text, figures, and tables from PDFs
2. **index_to_chromadb.py** - Indexes content into vector database
3. **rag_query.py** - Core RAG system for querying
4. **chat_with_pdf.py** - Interactive chat interface

## Notes

- Figures and tables are embedded using their captions for better semantic search
- The system automatically includes relevant images when answering questions about visual elements
- Text sections are chunked and indexed separately for granular retrieval
- Azure OpenAI deployment must support chat completions API