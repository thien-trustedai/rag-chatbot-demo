#!/usr/bin/env python3
"""
RAG Query System - Retrieves relevant information from ChromaDB and answers questions.
Includes figure and table images in the query when relevant.
"""

import os
import json
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from openai import AzureOpenAI, OpenAI
from PIL import Image
import io


class RAGQuerySystem:
    """RAG system for querying PDF content with visual elements."""
    
    def __init__(self,
                 db_path: str = "./chroma_db",
                 collection_name: str = "pdf_documents",
                 output_dir: str = "output",
                 use_azure: bool = True):
        """Initialize the RAG query system.
        
        Args:
            db_path: Path to ChromaDB storage
            collection_name: Name of the ChromaDB collection
            output_dir: Directory containing extracted images
            use_azure: Whether to use Azure OpenAI
        """
        # Load environment variables
        load_dotenv()
        
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        self.output_dir = Path(output_dir)
        
        # Initialize ChromaDB client with consistent settings
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True  # Use same setting as indexer
            )
        )
        
        # Initialize embedding function (must match what was used for indexing)
        # Check if we should use OpenAI embeddings
        if use_azure or os.environ.get("USE_OPENAI_EMBEDDINGS", "").lower() == "true":
            # Use OpenAI/Azure embeddings to match what was used for indexing
            if use_azure:
                # Azure OpenAI embeddings - check for separate embedding endpoint
                embedding_api_key = os.environ.get("AZURE_OPENAI_EMBEDDING_API_KEY") or os.environ.get("AZURE_OPENAI_API_KEY")
                embedding_endpoint = os.environ.get("AZURE_OPENAI_EMBEDDING_ENDPOINT")
                
                if embedding_endpoint and "embeddings?" in embedding_endpoint:
                    # Full embedding URL provided, extract base URL
                    embedding_base = embedding_endpoint.split("/openai/deployments")[0]
                else:
                    # Use standard endpoint or fall back to main endpoint
                    embedding_base = embedding_endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT") or os.environ.get("AZURE_OPENAI_API_BASE")
                
                # Get embedding deployment name
                deployment_id = os.environ.get("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
                embedding_api_version = os.environ.get("AZURE_OPENAI_EMBEDDING_API_VERSION") or os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")
                
                self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=embedding_api_key,
                    api_base=embedding_base,
                    api_type="azure",
                    api_version=embedding_api_version,
                    deployment_id=deployment_id
                )
                print(f"Using Azure OpenAI embeddings with deployment: {deployment_id}")
                print(f"Embedding endpoint: {embedding_base}")
            else:
                # Standard OpenAI embeddings
                self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=os.environ.get("OPENAI_API_KEY"),
                    api_base=os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1"),
                    model_name=os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
                )
                print(f"Using OpenAI embeddings")
        else:
            # Use SentenceTransformer as fallback
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            print("Using SentenceTransformer embeddings")
        
        # Get collection
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            doc_count = self.collection.count()
            print(f"Connected to collection '{self.collection_name}' with {doc_count} documents")
        except Exception as e:
            raise Exception(f"Failed to connect to collection '{self.collection_name}': {e}")
        
        # Initialize OpenAI client
        if use_azure:
            # Get endpoint from either AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_BASE
            azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT") or os.environ.get("AZURE_OPENAI_API_BASE")
            
            self.llm_client = AzureOpenAI(
                api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
                api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                azure_endpoint=azure_endpoint
            )
            self.model_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
            print(f"Using Azure OpenAI with deployment: {self.model_name}")
        else:
            self.llm_client = OpenAI(
                api_key=os.environ.get("OPENAI_API_KEY")
            )
            self.model_name = os.environ.get("OPENAI_MODEL", "gpt-4-turbo-preview")
            print(f"Using OpenAI with model: {self.model_name}")
    
    def encode_image(self, image_path: Path) -> Optional[str]:
        """Encode an image to base64 for inclusion in API calls.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string or None if error
        """
        try:
            if not image_path.exists():
                print(f"Warning: Image not found: {image_path}")
                return None
            
            # Open and potentially resize image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Resize if too large (max 2048x2048 for most models)
                max_size = 2048
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Save to bytes
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                
                # Encode to base64
                return base64.b64encode(buffer.read()).decode('utf-8')
                
        except Exception as e:
            print(f"Error encoding image {image_path}: {e}")
            return None
    
    def retrieve_context(self, query: str, n_results: int = 10) -> Tuple[List[Dict], List[Dict]]:
        """Retrieve relevant context from ChromaDB.
        
        Args:
            query: User's question
            n_results: Number of results to retrieve
            
        Returns:
            Tuple of (text_contexts, visual_contexts)
        """
        # Query the collection
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        text_contexts = []
        visual_contexts = []
        
        # Process results
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            content = results['documents'][0][i]
            distance = results['distances'][0][i]
            
            context_item = {
                'content': content,
                'metadata': metadata,
                'distance': distance
            }
            
            # Categorize by type
            if metadata['type'] == 'section':
                text_contexts.append(context_item)
            elif metadata['type'] in ['figure', 'table']:
                # Add image path for visual elements
                image_path = self.output_dir / metadata.get('path', '')
                context_item['image_path'] = image_path
                visual_contexts.append(context_item)
        
        return text_contexts, visual_contexts
    
    def format_context_for_prompt(self, text_contexts: List[Dict], visual_contexts: List[Dict]) -> str:
        """Format retrieved contexts into a prompt-friendly string with reference IDs.
        
        Args:
            text_contexts: List of text context items
            visual_contexts: List of visual context items
            
        Returns:
            Formatted context string with reference markers
        """
        context_parts = []
        ref_id = 1
        
        # Add text contexts
        if text_contexts:
            context_parts.append("## Relevant Text Sections:\n")
            for ctx in text_contexts:
                metadata = ctx['metadata']
                context_parts.append(f"\n### [Reference {ref_id}] - Page {metadata.get('page', 'N/A')}:")
                if metadata.get('heading'):
                    context_parts.append(f"**{metadata['heading']}**")
                context_parts.append(ctx['content'][:500])  # Limit length
                context_parts.append(f"*Use [[ref:{ref_id}]] to cite this section*")
                context_parts.append("")
                ref_id += 1
        
        # Add visual contexts descriptions
        if visual_contexts:
            context_parts.append("\n## Relevant Visual Elements:\n")
            for ctx in visual_contexts:
                metadata = ctx['metadata']
                elem_type = metadata['type'].capitalize()
                context_parts.append(f"\n### [Reference {ref_id}] - {elem_type} on Page {metadata.get('page', 'N/A')}:")
                context_parts.append(f"**{metadata.get('caption', 'No caption')}**")
                if metadata.get('description'):
                    context_parts.append(f"Description: {metadata['description']}")
                context_parts.append(f"[{elem_type} image will be included in the query]")
                context_parts.append(f"*Use [[ref:{ref_id}]] to cite this {elem_type.lower()}*")
                context_parts.append("")
                ref_id += 1
        
        return "\n".join(context_parts)
    
    def build_messages(self, query: str, text_contexts: List[Dict], 
                       visual_contexts: List[Dict]) -> List[Dict]:
        """Build messages for the LLM API call.
        
        Args:
            query: User's question
            text_contexts: Retrieved text contexts
            visual_contexts: Retrieved visual contexts
            
        Returns:
            List of message dictionaries for the API
        """
        # Format text context
        context_text = self.format_context_for_prompt(text_contexts, visual_contexts)
        
        # System message
        system_message = {
            "role": "system",
            "content": (
                "You are a helpful assistant that answers questions based on the provided context from a technical document. "
                "The context includes text sections and may include figures and tables.\n\n"
                "CRITICAL REFERENCE USAGE RULES:\n"
                "1. **Minimize reference citations** - Use each reference 1-2 times maximum per response\n"
                "2. **Group related information** - Combine all facts from the same source into coherent paragraphs\n"
                "3. **Strategic placement** - Place [[ref:N]] where it flows naturally, but avoid repeating the same reference multiple times in close proximity\n\n"
                "GOOD examples (minimal, strategic references):\n"
                "✓ 'According to the specifications [[ref:1]], the device has a 2.4GHz processor with 8GB RAM, "
                "supports up to 4 USB devices, and includes built-in WiFi connectivity.'\n"
                "✓ 'The installation process [[ref:2]] involves three main steps: First, connect the power cable. "
                "Second, attach the network cables. Finally, configure the initial settings through the web interface.'\n"
                "✓ 'As shown in Figure 1-2 [[ref:3]], the rear panel contains the power connector (labeled 14), "
                "the on/off switch (labeled 13), and various LED indicators for system status.'\n\n"
                "BAD examples (too many references):\n"
                "✗ 'The device [[ref:1]] has a processor [[ref:1]]. It also has RAM [[ref:1]].'\n"
                "✗ 'The power connector [[ref:3]] is labeled 14 [[ref:3]]. The switch [[ref:3]] is labeled 13 [[ref:3]].'\n"
                "✗ 'According to [[ref:2]], step 1 is X. Also per [[ref:2]], step 2 is Y. [[ref:2]] mentions step 3 is Z.'\n\n"
                "FORMATTING GUIDELINES:\n"
                "- Use clear headings with ## for main sections\n"
                "- Use bullet points or numbered lists for multiple items\n"
                "- Use **bold** for emphasis on key terms\n"
                "- Use code blocks with ``` for commands or code\n"
                "- Use tables for structured data\n\n"
                "STRATEGY: When multiple facts come from the same reference, group them together in one paragraph "
                "with a single citation. You may cite the same reference again later if discussing a different aspect, "
                "but avoid citing the same reference more than twice total. Never cite the same reference multiple times "
                "in the same paragraph or consecutive sentences."
            )
        }
        
        # Build user message content
        user_content = []
        
        # Add the context and question as text
        user_content.append({
            "type": "text",
            "text": f"Context:\n{context_text}\n\nQuestion: {query}"
        })
        
        # Add images when visual contexts are available
        if visual_contexts:
            for ctx in visual_contexts:
                image_path = ctx.get('image_path')
                if image_path and image_path.exists():
                    encoded_image = self.encode_image(image_path)
                    if encoded_image:
                        metadata = ctx['metadata']
                        # Add image with caption
                        user_content.append({
                            "type": "text",
                            "text": f"\n{metadata['type'].capitalize()}: {metadata.get('caption', 'No caption')}"
                        })
                        user_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{encoded_image}"
                            }
                        })
        
        # Create user message
        if len(user_content) == 1:
            # Text-only message
            user_message = {
                "role": "user",
                "content": user_content[0]["text"]
            }
        else:
            # Multi-modal message
            user_message = {
                "role": "user",
                "content": user_content
            }
        
        return [system_message, user_message]
    
    def query(self, question: str, n_results: int = 10, verbose: bool = True, 
              conversation_history: list = None, return_references: bool = True):
        """Answer a question using RAG.
        
        Args:
            question: User's question
            n_results: Number of documents to retrieve
            verbose: Whether to print debug information
            conversation_history: Optional list of previous messages for context
            return_references: Whether to return references along with answer
            
        Returns:
            If return_references is True: Tuple of (answer, references)
            Otherwise: Just the answer string
        """
        # Retrieve relevant context
        if verbose:
            print(f"\nRetrieving context for: '{question}'...")
        
        text_contexts, visual_contexts = self.retrieve_context(question, n_results)
        
        if verbose:
            print(f"Found {len(text_contexts)} text sections and {len(visual_contexts)} visual elements")
            
            # Show what was retrieved
            if visual_contexts:
                print("\nVisual elements retrieved:")
                for ctx in visual_contexts:
                    metadata = ctx['metadata']
                    print(f"  - {metadata['type'].capitalize()}: {metadata.get('caption', 'No caption')} (Page {metadata.get('page')})")
        
        # Build messages for LLM
        messages = self.build_messages(question, text_contexts, visual_contexts)
        
        # Add conversation history if provided
        if conversation_history:
            # Insert history after system message but before current query
            full_messages = [messages[0]]  # System message
            full_messages.extend(conversation_history)  # Previous conversation
            full_messages.append(messages[1])  # Current query with context
            messages = full_messages
        
        # Call LLM
        if verbose:
            print(f"\nQuerying {self.model_name}...")
            if conversation_history:
                print(f"Including {len(conversation_history)} messages from conversation history")
        
        try:
            # For Azure OpenAI, model parameter should be the deployment name
            response = self.llm_client.chat.completions.create(
                model=self.model_name,  # This is the deployment name for Azure
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            if return_references:
                # Format references for frontend
                references = []
                
                # Add text contexts as references
                for i, ctx in enumerate(text_contexts):
                    metadata = ctx.get('metadata', {})
                    
                    # Extract bounding box if available
                    position = None
                    if all(k in metadata for k in ['bbox_x0', 'bbox_y0', 'bbox_x1', 'bbox_y1']):
                        # All elements now use hi-res coordinates - apply uniform 2.78x scaling
                        scale_factor = 2.78
                        position = {
                            'boundingRect': {
                                'x1': metadata.get('bbox_x0', 0) / scale_factor,
                                'y1': metadata.get('bbox_y0', 0) / scale_factor,
                                'x2': metadata.get('bbox_x1', 0) / scale_factor,
                                'y2': metadata.get('bbox_y1', 0) / scale_factor,
                                'pageNumber': metadata.get('page', 1)
                            }
                        }
                    
                    ref = {
                        'id': f"text_{i}",
                        'page_number': metadata.get('page', 1),
                        'text_preview': ctx.get('content', '')[:200],  # First 200 chars
                        'relevance_score': ctx.get('score', 0.5),
                        'images': [],  # No images for text references
                        'position': position
                    }
                    references.append(ref)
                
                # Add visual contexts as references
                for i, ctx in enumerate(visual_contexts):
                    metadata = ctx.get('metadata', {})
                    
                    # Extract bounding box if available
                    position = None
                    if all(k in metadata for k in ['bbox_x0', 'bbox_y0', 'bbox_x1', 'bbox_y1']):
                        # All elements now use hi-res coordinates - apply uniform 2.78x scaling
                        scale_factor = 2.78
                        position = {
                            'boundingRect': {
                                'x1': metadata.get('bbox_x0', 0) / scale_factor,
                                'y1': metadata.get('bbox_y0', 0) / scale_factor,
                                'x2': metadata.get('bbox_x1', 0) / scale_factor,
                                'y2': metadata.get('bbox_y1', 0) / scale_factor,
                                'pageNumber': metadata.get('page', 1)
                            }
                        }
                    
                    ref = {
                        'id': f"visual_{i}",
                        'page_number': metadata.get('page', 1),
                        'text_preview': metadata.get('caption', metadata.get('description', '')),
                        'relevance_score': ctx.get('score', 0.5),
                        'images': [],  # Could add image data if needed
                        'position': position
                    }
                    references.append(ref)
                
                return answer, references
            else:
                return answer
            
        except Exception as e:
            if return_references:
                return f"Error calling LLM: {e}", []
            else:
                return f"Error calling LLM: {e}"


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Query PDF content using RAG")
    parser.add_argument(
        "question",
        nargs="?",
        help="Question to ask (or use interactive mode if not provided)"
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
        "--output-dir",
        default="output",
        help="Directory containing extracted images"
    )
    parser.add_argument(
        "--n-results",
        type=int,
        default=10,
        help="Number of documents to retrieve"
    )
    parser.add_argument(
        "--use-openai",
        action="store_true",
        help="Use OpenAI instead of Azure OpenAI"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress debug output"
    )
    
    args = parser.parse_args()
    
    # Initialize RAG system
    try:
        rag = RAGQuerySystem(
            db_path=args.db_path,
            collection_name=args.collection,
            output_dir=args.output_dir,
            use_azure=not args.use_openai
        )
    except Exception as e:
        print(f"Error initializing RAG system: {e}")
        return
    
    # Interactive or single question mode
    if args.question:
        # Single question mode
        result = rag.query(
            args.question, 
            n_results=args.n_results,
            verbose=not args.quiet,
            return_references=False  # For CLI, just return answer
        )
        print("\n" + "="*50)
        print("Answer:")
        print("="*50)
        print(result)
    else:
        # Interactive mode
        print("\n" + "="*50)
        print("RAG Query System - Interactive Mode")
        print("Type 'quit' or 'exit' to stop")
        print("="*50)
        
        while True:
            try:
                question = input("\nEnter your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if not question:
                    continue
                
                result = rag.query(
                    question,
                    n_results=args.n_results,
                    verbose=not args.quiet,
                    return_references=False  # For CLI, just return answer
                )
                
                print("\n" + "="*50)
                print("Answer:")
                print("="*50)
                print(result)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()