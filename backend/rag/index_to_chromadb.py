#!/usr/bin/env python3
"""
Script to index PDF extraction metadata into ChromaDB vector database.
Uses captions for figure and table embeddings.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions


class PDFMetadataIndexer:
    """Index PDF extraction metadata into ChromaDB."""
    
    def __init__(self, 
                 metadata_path: str = "output/metadata.json",
                 db_path: str = "./chroma_db",
                 collection_name: str = "pdf_documents",
                 use_openai: bool = False,
                 azure: bool = False,
                 openai_config: Optional[Dict[str, str]] = None):
        """Initialize the indexer with ChromaDB.
        
        Args:
            metadata_path: Path to the metadata.json file
            db_path: Path to store ChromaDB data
            collection_name: Name of the ChromaDB collection
            use_openai: Whether to use OpenAI embeddings
            azure: Whether to use Azure OpenAI (if use_openai is True)
            openai_config: OpenAI configuration dict with api_key, api_base, etc.
        """
        self.metadata_path = Path(metadata_path)
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Choose embedding function based on configuration
        if use_openai:
            if not openai_config:
                # Try to load from environment variables
                openai_config = {
                    "api_key": os.environ.get("OPENAI_API_KEY", ""),
                    "api_base": os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1"),
                    "model_name": os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
                }
                
                # Check for Azure-specific environment variables
                if azure or os.environ.get("AZURE_OPENAI_EMBEDDING_API_KEY") or os.environ.get("AZURE_OPENAI_API_KEY"):
                    # Use separate embedding endpoint if available
                    embedding_api_key = os.environ.get("AZURE_OPENAI_EMBEDDING_API_KEY") or os.environ.get("AZURE_OPENAI_API_KEY")
                    embedding_endpoint = os.environ.get("AZURE_OPENAI_EMBEDDING_ENDPOINT")
                    
                    if embedding_endpoint and "embeddings?" in embedding_endpoint:
                        # Full embedding URL provided, extract base URL
                        embedding_base = embedding_endpoint.split("/openai/deployments")[0]
                    else:
                        embedding_base = embedding_endpoint or os.environ.get("AZURE_OPENAI_API_BASE") or os.environ.get("AZURE_OPENAI_ENDPOINT")
                    
                    openai_config = {
                        "api_key": embedding_api_key,
                        "api_base": embedding_base,
                        "api_type": "azure",
                        "api_version": os.environ.get("AZURE_OPENAI_EMBEDDING_API_VERSION") or os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15"),
                        "model_name": os.environ.get("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
                    }
            
            if not openai_config.get("api_key"):
                raise ValueError("OpenAI API key is required when use_openai=True. "
                               "Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY environment variable.")
            
            # Create OpenAI embedding function
            if openai_config.get("api_type") == "azure":
                # For Azure, we need deployment_id instead of model_name
                deployment_id = openai_config.get("deployment_id") or openai_config.get("model_name", "text-embedding-3-small")
                self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=openai_config["api_key"],
                    api_base=openai_config["api_base"],
                    api_type="azure",
                    api_version=openai_config.get("api_version", "2023-05-15"),
                    deployment_id=deployment_id
                )
                print(f"Using Azure OpenAI embeddings with deployment: {deployment_id}")
            else:
                self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=openai_config["api_key"],
                    api_base=openai_config.get("api_base", "https://api.openai.com/v1"),
                    model_name=openai_config.get("model_name", "text-embedding-3-small")
                )
                print(f"Using OpenAI embeddings with model: {openai_config.get('model_name')}")
        else:
            # Use SentenceTransformer as default
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            print("Using SentenceTransformer embeddings with model: all-MiniLM-L6-v2")
        
        # Get or create collection
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            print(f"Using existing collection: {self.collection_name}")
            # Get document count
            try:
                existing_count = self.collection.count()
                if existing_count > 0:
                    print(f"Collection contains {existing_count} existing documents")
            except Exception as e:
                pass
        except Exception as e:
            # Collection doesn't exist, try to create it
            try:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_function,
                    metadata={"hnsw:space": "cosine"}
                )
                print(f"Created new collection: {self.collection_name}")
            except Exception as create_error:
                # Collection might exist but with different embedding function
                print(f"Collection {self.collection_name} exists. Deleting and recreating...")
                try:
                    # Check if collection actually exists before trying to delete
                    existing_collections = [col.name for col in self.client.list_collections()]
                    if self.collection_name in existing_collections:
                        self.client.delete_collection(name=self.collection_name)
                        print(f"Deleted existing collection: {self.collection_name}")
                    
                    # Now create the collection
                    self.collection = self.client.create_collection(
                        name=self.collection_name,
                        embedding_function=self.embedding_function,
                        metadata={"hnsw:space": "cosine"}
                    )
                    print(f"Created new collection: {self.collection_name}")
                except Exception as recreate_error:
                    print(f"Error managing collection: {recreate_error}")
                    raise
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            ids_to_delete = self.collection.get()['ids']
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                print(f"Cleared {len(ids_to_delete)} documents from collection")
            else:
                print("Collection is already empty")
        except Exception as e:
            print(f"Error clearing collection: {e}")
    
    def generate_id(self, content: str, doc_type: str, index: int) -> str:
        """Generate a unique ID for a document.
        
        Args:
            content: Content to hash
            doc_type: Type of document (section, figure, table)
            index: Index of the element
            
        Returns:
            Unique ID string
        """
        hash_input = f"{doc_type}_{index}_{content[:100]}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def load_metadata(self) -> Dict[str, Any]:
        """Load metadata from JSON file.
        
        Returns:
            Metadata dictionary
        """
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_path}")
        
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def clean_metadata(self, metadata_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Clean metadata by removing None values and converting to strings.
        
        Args:
            metadata_dict: Metadata dictionary with potential None values
            
        Returns:
            Cleaned metadata dictionary
        """
        cleaned = {}
        for key, value in metadata_dict.items():
            if value is None:
                cleaned[key] = ""
            elif isinstance(value, bool):
                cleaned[key] = str(value).lower()
            elif isinstance(value, (int, float)):
                cleaned[key] = value
            else:
                cleaned[key] = str(value)
        return cleaned
    
    def prepare_documents(self, metadata: Dict[str, Any]) -> tuple:
        """Prepare documents for indexing.
        
        Args:
            metadata: Loaded metadata dictionary
            
        Returns:
            Tuple of (documents, metadatas, ids)
        """
        documents = []
        metadatas = []
        ids = []
        
        source_pdf = metadata.get("extraction_info", {}).get("source_pdf", "unknown")
        
        # Process each section
        for section in metadata.get("structure", []):
            section_id = section.get("id", f"section_{section.get('index', 0)}")
            page_num = section.get("page", 1)
            heading = section.get("heading", "") or ""
            
            # Index section text content
            text_content = section.get("text_content", "")
            if text_content.strip():
                doc_id = self.generate_id(text_content, "section", section.get("index", 0))
                
                # Create searchable content with heading
                searchable_content = f"{heading}\n\n{text_content}" if heading else text_content
                
                documents.append(searchable_content)
                
                section_metadata = {
                    "type": "section",
                    "source_pdf": source_pdf,
                    "section_id": section_id,
                    "section_index": section.get("index", 0),
                    "page": page_num,
                    "heading": heading or "No heading",
                    "heading_type": section.get("heading_type", "") or "",
                    "char_count": len(text_content)
                }
                
                # Add bounding box if available
                bbox = section.get("bounding_box")
                if bbox:
                    section_metadata["bbox_x0"] = bbox.get("x0", 0)
                    section_metadata["bbox_y0"] = bbox.get("y0", 0)
                    section_metadata["bbox_x1"] = bbox.get("x1", 0)
                    section_metadata["bbox_y1"] = bbox.get("y1", 0)
                    section_metadata["bbox_width"] = bbox.get("width", 0)
                    section_metadata["bbox_height"] = bbox.get("height", 0)
                
                metadatas.append(self.clean_metadata(section_metadata))
                ids.append(doc_id)
            
            # Index figures using captions
            for figure in section.get("figures", []):
                caption = figure.get("caption") or f"Figure {figure.get('index', 0)}"
                description = figure.get("description", "") or ""
                
                # Combine caption and description for embedding
                figure_text = caption
                if description:
                    figure_text += f"\n{description}"
                
                if figure_text.strip():
                    doc_id = self.generate_id(figure_text, "figure", figure.get("index", 0))
                    
                    documents.append(figure_text)
                    
                    figure_metadata = {
                        "type": "figure",
                        "source_pdf": source_pdf,
                        "section_id": section_id,
                        "figure_id": figure.get("id", "") or "",
                        "figure_index": figure.get("index", 0),
                        "page": page_num,
                        "caption": caption,
                        "description": description or "",
                        "filename": figure.get("filename", "") or "",
                        "path": figure.get("path", "") or "",
                        "original_type": figure.get("original_type", "Image") or "Image",
                        "reclassified": figure.get("reclassified", False)
                    }
                    
                    # Add bounding box if available
                    bbox = figure.get("bounding_box")
                    if bbox:
                        figure_metadata["bbox_x0"] = bbox.get("x0", 0)
                        figure_metadata["bbox_y0"] = bbox.get("y0", 0)
                        figure_metadata["bbox_x1"] = bbox.get("x1", 0)
                        figure_metadata["bbox_y1"] = bbox.get("y1", 0)
                        figure_metadata["bbox_width"] = bbox.get("width", 0)
                        figure_metadata["bbox_height"] = bbox.get("height", 0)
                    
                    metadatas.append(self.clean_metadata(figure_metadata))
                    ids.append(doc_id)
            
            # Index tables using captions
            for table in section.get("tables", []):
                caption = table.get("caption") or f"Table {table.get('index', 0)}"
                description = table.get("description", "") or ""
                
                # Combine caption and description for embedding
                table_text = caption
                if description:
                    table_text += f"\n{description}"
                
                if table_text.strip():
                    doc_id = self.generate_id(table_text, "table", table.get("index", 0))
                    
                    documents.append(table_text)
                    
                    table_metadata = {
                        "type": "table",
                        "source_pdf": source_pdf,
                        "section_id": section_id,
                        "table_id": table.get("id", "") or "",
                        "table_index": table.get("index", 0),
                        "page": page_num,
                        "caption": caption,
                        "description": description or "",
                        "filename": table.get("filename", "") or "",
                        "path": table.get("path", "") or "",
                        "csv_path": table.get("csv_path", "") or "",
                        "original_type": table.get("original_type", "Table") or "Table",
                        "reclassified": table.get("reclassified", False)
                    }
                    
                    # Add bounding box if available
                    bbox = table.get("bounding_box")
                    if bbox:
                        table_metadata["bbox_x0"] = bbox.get("x0", 0)
                        table_metadata["bbox_y0"] = bbox.get("y0", 0)
                        table_metadata["bbox_x1"] = bbox.get("x1", 0)
                        table_metadata["bbox_y1"] = bbox.get("y1", 0)
                        table_metadata["bbox_width"] = bbox.get("width", 0)
                        table_metadata["bbox_height"] = bbox.get("height", 0)
                    
                    metadatas.append(self.clean_metadata(table_metadata))
                    ids.append(doc_id)
        
        return documents, metadatas, ids
    
    def index_documents(self) -> Dict[str, int]:
        """Index all documents into ChromaDB.
        
        Returns:
            Statistics about indexed documents
        """
        # Load metadata
        metadata = self.load_metadata()
        print(f"Loaded metadata from: {self.metadata_path}")
        
        # Prepare documents
        documents, metadatas, ids = self.prepare_documents(metadata)
        
        if not documents:
            print("No documents to index!")
            return {"total": 0}
        
        # Add documents to collection in batches
        batch_size = 100
        total_indexed = 0
        
        for i in range(0, len(documents), batch_size):
            batch_end = min(i + batch_size, len(documents))
            
            self.collection.add(
                documents=documents[i:batch_end],
                metadatas=metadatas[i:batch_end],
                ids=ids[i:batch_end]
            )
            
            total_indexed += (batch_end - i)
            print(f"Indexed {total_indexed}/{len(documents)} documents...")
        
        # Count document types
        stats = {
            "total": len(documents),
            "sections": sum(1 for m in metadatas if m["type"] == "section"),
            "figures": sum(1 for m in metadatas if m["type"] == "figure"),
            "tables": sum(1 for m in metadatas if m["type"] == "table")
        }
        
        return stats
    
    def index_from_metadata(self, metadata_path: str, base_dir: str = "output") -> Dict[str, int]:
        """Index documents from a metadata file (wrapper for pipeline).
        
        Args:
            metadata_path: Path to metadata JSON file
            base_dir: Base directory for relative paths
            
        Returns:
            Statistics dictionary with indexing results
        """
        # Update paths - ensure they are Path objects
        self.metadata_path = Path(metadata_path)
        self.base_dir = Path(base_dir)
        
        # Call the main indexing method
        stats = self.index_documents()
        
        # Return stats in the expected format
        return {
            "total_documents": stats.get("total", 0),
            "text_chunks": stats.get("sections", 0),
            "figures": stats.get("figures", 0),
            "tables": stats.get("tables", 0)
        }
    
    def search(self, query: str, n_results: int = 5, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search the indexed documents.
        
        Args:
            query: Search query
            n_results: Number of results to return
            doc_type: Optional filter by document type (section, figure, table)
            
        Returns:
            List of search results with metadata
        """
        where_clause = {"type": doc_type} if doc_type else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_clause
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            result = {
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i]
            }
            formatted_results.append(result)
        
        return formatted_results


def main():
    """Main function to run the indexing process."""
    import argparse
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Index PDF metadata into ChromaDB")
    parser.add_argument(
        "--metadata", 
        default="output/metadata.json",
        help="Path to metadata.json file"
    )
    parser.add_argument(
        "--db-path",
        default="./chroma_db",
        help="Path to ChromaDB storage"
    )
    parser.add_argument(
        "--collection",
        default="pdf_documents",
        help="ChromaDB collection name"
    )
    parser.add_argument(
        "--use-openai",
        action="store_true",
        help="Use OpenAI embeddings instead of SentenceTransformer"
    )
    parser.add_argument(
        "--azure",
        action="store_true",
        help="Use Azure OpenAI (requires AZURE_OPENAI_* env vars)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing documents before indexing"
    )
    parser.add_argument(
        "--search",
        help="Optional search query to test after indexing"
    )
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Only perform search, skip indexing"
    )
    
    args = parser.parse_args()
    
    # Prepare OpenAI configuration if requested
    openai_config = None
    if args.use_openai:
        if args.azure:
            # Load Azure OpenAI configuration from environment
            # Use separate embedding endpoint if available
            embedding_api_key = os.environ.get("AZURE_OPENAI_EMBEDDING_API_KEY") or os.environ.get("AZURE_OPENAI_API_KEY")
            embedding_endpoint = os.environ.get("AZURE_OPENAI_EMBEDDING_ENDPOINT")
            
            if embedding_endpoint and "embeddings?" in embedding_endpoint:
                # Full embedding URL provided, extract base URL
                api_base = embedding_endpoint.split("/openai/deployments")[0]
            else:
                api_base = embedding_endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT") or os.environ.get("AZURE_OPENAI_API_BASE")
            
            deployment_id = os.environ.get("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
            
            openai_config = {
                "api_key": embedding_api_key,
                "api_base": api_base,
                "api_type": "azure",
                "api_version": os.environ.get("AZURE_OPENAI_EMBEDDING_API_VERSION") or os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15"),
                "deployment_id": deployment_id,
                "model_name": deployment_id
            }
        else:
            # Load standard OpenAI configuration from environment
            openai_config = {
                "api_key": os.environ.get("OPENAI_API_KEY"),
                "api_base": os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1"),
                "model_name": os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            }
    
    # Create indexer
    indexer = PDFMetadataIndexer(
        metadata_path=args.metadata,
        db_path=args.db_path,
        collection_name=args.collection,
        use_openai=args.use_openai,
        openai_config=openai_config
    )
    
    # Clear collection if requested
    if args.clear:
        print("\nClearing existing documents...")
        indexer.clear_collection()
    
    # Skip indexing if search-only mode
    if not args.search_only:
        # Index documents
        print("\nIndexing documents...")
        stats = indexer.index_documents()
        
        print("\n" + "="*50)
        print("Indexing Complete!")
        print("="*50)
        print(f"Total documents indexed: {stats['total']}")
        print(f"  - Sections: {stats['sections']}")
        print(f"  - Figures: {stats['figures']}")
        print(f"  - Tables: {stats['tables']}")
    
    # Test search if query provided
    if args.search:
        print("\n" + "="*50)
        print(f"Search Results for: '{args.search}'")
        print("="*50)
        
        results = indexer.search(args.search, n_results=5)
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Type: {result['metadata']['type']}")
            print(f"Page: {result['metadata']['page']}")
            
            if result['metadata']['type'] == 'section':
                print(f"Heading: {result['metadata'].get('heading', 'N/A')}")
            elif result['metadata']['type'] == 'figure':
                print(f"Caption: {result['metadata'].get('caption', 'N/A')}")
                print(f"Path: {result['metadata'].get('path', 'N/A')}")
            elif result['metadata']['type'] == 'table':
                print(f"Caption: {result['metadata'].get('caption', 'N/A')}")
                print(f"Path: {result['metadata'].get('path', 'N/A')}")
            
            print(f"Distance: {result['distance']:.4f}")
            print(f"Content preview: {result['content'][:200]}...")


if __name__ == "__main__":
    main()