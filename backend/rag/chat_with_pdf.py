#!/usr/bin/env python3
"""
Interactive chat with PDF documents using RAG.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Handle both module and direct imports
try:
    from .rag_query import RAGQuerySystem
except ImportError:
    from rag_query import RAGQuerySystem

def print_header():
    """Print a nice header for the chat interface."""
    print("\n" + "="*60)
    print("📚 PDF Document Chat System")
    print("="*60)
    print("Ask questions about your indexed PDF documents.")
    print("Type 'help' for commands, 'quit' to exit.")
    print("-"*60)

def print_help():
    """Print help information."""
    print("\n📋 Available Commands:")
    print("-"*40)
    print("  help     - Show this help message")
    print("  status   - Show collection statistics")
    print("  history  - Show conversation history")
    print("  reset    - Clear conversation history")
    print("  clear    - Clear the screen")
    print("  verbose  - Toggle verbose mode")
    print("  quit/exit - Exit the chat")
    print("-"*40)
    print("\n💡 Tips:")
    print("  • The system remembers your conversation context")
    print("  • Use 'reset' to start a fresh conversation")
    print("  • Ask follow-up questions for deeper insights")
    print("-"*40)

def get_collection_stats(rag):
    """Get statistics about the indexed collection."""
    try:
        doc_count = rag.collection.count()
        # Sample query to get document types
        sample = rag.collection.get(limit=100)
        
        if sample and 'metadatas' in sample:
            doc_types = {}
            for metadata in sample['metadatas']:
                doc_type = metadata.get('type', 'unknown')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            return doc_count, doc_types
        return doc_count, {}
    except Exception as e:
        return 0, {}


class PDFChatInterface:
    """Class-based interface for PDF chat."""
    
    def __init__(self, 
                 collection_name: str = "pdf_documents",
                 db_path: str = "./chroma_db",
                 output_dir: str = "output",
                 use_azure: bool = True):
        """
        Initialize the PDF chat interface.
        
        Args:
            collection_name: Name of the ChromaDB collection
            db_path: Path to ChromaDB storage
            output_dir: Directory containing extracted content
            use_azure: Use Azure OpenAI (True) or local models (False)
        """
        self.collection_name = collection_name
        self.db_path = db_path
        self.output_dir = output_dir
        self.use_azure = use_azure
        self.rag = None
        self.verbose = False
        self.conversation_history = []
        
        # Load environment variables
        load_dotenv()
    
    def initialize(self):
        """Initialize the RAG system."""
        print("\n🔄 Initializing RAG system...")
        try:
            self.rag = RAGQuerySystem(
                db_path=self.db_path,
                collection_name=self.collection_name,
                output_dir=self.output_dir,
                use_azure=self.use_azure
            )
            print("✅ System ready!\n")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            print("\nPlease check your configuration:")
            print("1. Ensure ChromaDB has indexed documents (run index_to_chromadb.py)")
            print("2. Verify your Azure OpenAI credentials in .env")
            return False
    
    def run(self):
        """Run the interactive chat loop."""
        if not self.rag:
            if not self.initialize():
                return
        
        # Print header
        print_header()
        
        # Get initial stats
        doc_count, doc_types = get_collection_stats(self.rag)
        print(f"\n📚 Loaded collection: {self.collection_name}")
        print(f"   Documents indexed: {doc_count}")
        
        # Main chat loop
        while True:
            try:
                user_input = input("\n🤔 You: ").strip()
                
                # Handle empty input
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                elif user_input.lower() == 'help':
                    print_help()
                    continue
                
                elif user_input.lower() == 'clear':
                    os.system('clear' if os.name == 'posix' else 'cls')
                    print_header()
                    continue
                
                elif user_input.lower() == 'status':
                    doc_count, doc_types = get_collection_stats(self.rag)
                    print(f"\n📊 Collection Status:")
                    print(f"   Total documents: {doc_count}")
                    if doc_types:
                        for dtype, count in doc_types.items():
                            print(f"   • {dtype.capitalize()}: {count}")
                    continue
                
                elif user_input.lower() == 'verbose':
                    self.verbose = not self.verbose
                    status = "ON" if self.verbose else "OFF"
                    print(f"\n🔧 Verbose mode: {status}")
                    continue
                
                elif user_input.lower() == 'reset':
                    self.conversation_history = []
                    print("\n🔄 Conversation history cleared")
                    continue
                
                elif user_input.lower() == 'history':
                    if self.conversation_history:
                        print(f"\n📜 Conversation History ({len(self.conversation_history)//2} exchanges):")
                        for i in range(0, len(self.conversation_history), 2):
                            if i < len(self.conversation_history):
                                user_msg = self.conversation_history[i].get('content', '')
                                if isinstance(user_msg, list):
                                    user_msg = user_msg[0].get('text', '') if user_msg else ''
                                print(f"\n  You: {user_msg[:100]}...")
                            if i+1 < len(self.conversation_history):
                                assistant_msg = self.conversation_history[i+1].get('content', '')
                                print(f"  Bot: {assistant_msg[:100]}...")
                    else:
                        print("\n📜 No conversation history yet")
                    continue
                
                # Process query
                print("\n🤖 Assistant: ", end="", flush=True)
                
                # Query the RAG system
                response, references = self.rag.query(
                    user_input,
                    conversation_history=self.conversation_history,
                    n_results=5 if self.verbose else 3
                )
                
                # Print response
                print(response)
                
                # Show references in verbose mode
                if self.verbose and references:
                    print("\n📎 References:")
                    for i, ref in enumerate(references, 1):
                        ref_type = ref.get('type', 'text')
                        page = ref.get('page_number', 'N/A')
                        content = ref.get('content', '')[:100] + "..."
                        print(f"   [{i}] {ref_type.capitalize()} (Page {page}): {content}")
                
                # Update conversation history
                self.conversation_history.append({
                    "role": "user",
                    "content": user_input
                })
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": response
                })
                
                # Keep history manageable (last 10 exchanges)
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
                    
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                if self.verbose:
                    import traceback
                    traceback.print_exc()


def main():
    """Main entry point for command-line usage."""
    # Create and run chat interface
    chat = PDFChatInterface(
        collection_name="pdf_documents",
        db_path="./chroma_db",
        output_dir="output",
        use_azure=True
    )
    
    try:
        chat.run()
    except KeyboardInterrupt:
        print("\n\n👋 Chat interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
