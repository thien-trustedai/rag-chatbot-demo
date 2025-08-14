#!/usr/bin/env python3
"""
Unified PDF Chat Pipeline
Extracts PDF content, indexes to ChromaDB, and starts interactive chat.
"""

import sys
import os
import argparse
import time
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.text import Text

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from extractors.parallel_pdf_extractor import ParallelPDFExtractor
from rag.index_to_chromadb import PDFMetadataIndexer
from rag.chat_with_pdf import PDFChatInterface
from core.pdf_extraction_config import PDFConstants

console = Console()


class PDFChatPipeline:
    """Complete pipeline for PDF extraction, indexing, and chat."""
    
    def __init__(self, 
                 pdf_path: str,
                 output_dir: Optional[str] = None,
                 collection_name: Optional[str] = None,
                 use_azure: bool = True,
                 clear_db: bool = False,
                 max_workers: int = 4):
        """
        Initialize the PDF chat pipeline.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory for extraction output (default: pdf_extraction)
            collection_name: ChromaDB collection name (default: pdf_documents)
            use_azure: Use Azure OpenAI for embeddings and chat
            clear_db: Clear existing collection before indexing
            max_workers: Number of parallel workers for extraction
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Set defaults
        self.output_dir = output_dir or "pdf_extraction"
        self.collection_name = collection_name or "pdf_documents"
        self.use_azure = use_azure
        self.clear_db = clear_db
        self.max_workers = max_workers
        
        # Components will be initialized during pipeline execution
        self.extractor = None
        self.indexer = None
        self.chat_interface = None
    
    def extract_pdf(self) -> bool:
        """
        Extract content from PDF using parallel processing.
        
        Returns:
            bool: True if extraction successful
        """
        console.print(f"\n[bold blue]📄 Extracting PDF:[/bold blue] {self.pdf_path.name}")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                
                # Initialize extractor
                task = progress.add_task("Initializing extractor...", total=100)
                self.extractor = ParallelPDFExtractor(
                    pdf_path=str(self.pdf_path),
                    output_directory=self.output_dir,
                    max_workers=self.max_workers
                )
                progress.update(task, completed=20)
                
                # Extract content
                progress.update(task, description="Processing pages...")
                summary = self.extractor.extract()
                progress.update(task, completed=100)
            
            # Display summary
            console.print(Panel(
                f"[green]✓[/green] Extraction complete!\n\n"
                f"• Pages processed: {summary.get('total_pages', 0)}\n"
                f"• Figures extracted: {summary.get('total_figures', 0)}\n"
                f"• Tables extracted: {summary.get('total_tables', 0)}\n"
                f"• Text sections: {summary.get('total_sections', 0)}",
                title="Extraction Summary",
                border_style="green"
            ))
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Extraction failed: {e}[/red]")
            return False
    
    def index_to_chromadb(self) -> bool:
        """
        Index extracted content to ChromaDB.
        
        Returns:
            bool: True if indexing successful
        """
        console.print(f"\n[bold blue]🔍 Indexing to ChromaDB[/bold blue]")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                # Initialize indexer
                task = progress.add_task("Initializing ChromaDB...", total=None)
                
                self.indexer = PDFMetadataIndexer(
                    collection_name=self.collection_name,
                    use_openai=self.use_azure,
                    azure=self.use_azure
                )
                
                if self.clear_db:
                    progress.update(task, description="Clearing existing collection...")
                    self.indexer.clear_collection()
                
                # Index the extracted content
                progress.update(task, description="Loading metadata...")
                metadata_path = Path(self.output_dir) / "metadata.json"
                
                if not metadata_path.exists():
                    raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
                
                progress.update(task, description="Indexing content...")
                stats = self.indexer.index_from_metadata(
                    str(metadata_path),
                    base_dir=self.output_dir
                )
            
            # Display indexing summary
            console.print(Panel(
                f"[green]✓[/green] Indexing complete!\n\n"
                f"• Collection: {self.collection_name}\n"
                f"• Documents indexed: {stats.get('total_documents', 0)}\n"
                f"• Text chunks: {stats.get('text_chunks', 0)}\n"
                f"• Figures indexed: {stats.get('figures', 0)}\n"
                f"• Tables indexed: {stats.get('tables', 0)}",
                title="Indexing Summary",
                border_style="green"
            ))
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Indexing failed: {e}[/red]")
            return False
    
    def start_chat(self) -> None:
        """Start the interactive chat interface."""
        console.print(f"\n[bold blue]💬 Starting Interactive Chat[/bold blue]")
        
        try:
            # Initialize chat interface
            self.chat_interface = PDFChatInterface(
                collection_name=self.collection_name,
                use_azure=self.use_azure
            )
            
            # Display welcome message
            console.print(Panel(
                "[green]Chat interface ready![/green]\n\n"
                "Commands:\n"
                "• Type your questions about the PDF\n"
                "• 'help' - Show available commands\n"
                "• 'status' - Show collection statistics\n"
                "• 'history' - View conversation history\n"
                "• 'reset' - Clear conversation memory\n"
                "• 'verbose' - Toggle detailed output\n"
                "• 'quit' or 'exit' - Exit the chat\n",
                title=f"Chatting with: {self.pdf_path.name}",
                border_style="blue"
            ))
            
            # Start chat loop
            self.chat_interface.run()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Chat interrupted by user[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Chat failed: {e}[/red]")
    
    def run(self) -> None:
        """Run the complete pipeline."""
        console.print(Panel.fit(
            f"[bold]PDF Chat Pipeline[/bold]\n"
            f"Processing: {self.pdf_path.name}",
            border_style="cyan"
        ))
        
        # Step 1: Extract PDF
        if not self.extract_pdf():
            console.print("[red]Pipeline failed at extraction stage[/red]")
            return
        
        # Step 2: Index to ChromaDB
        if not self.index_to_chromadb():
            console.print("[red]Pipeline failed at indexing stage[/red]")
            return
        
        # Step 3: Start chat
        self.start_chat()
        
        console.print("\n[bold green]✨ Pipeline completed successfully![/bold green]")


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="PDF Chat Pipeline - Extract, Index, and Chat with PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with a PDF
  python pdf_chat_pipeline.py document.pdf
  
  # Specify output directory and collection name
  python pdf_chat_pipeline.py document.pdf --output my_extraction --collection my_docs
  
  # Clear existing data and re-index
  python pdf_chat_pipeline.py document.pdf --clear
  
  # Use local embeddings instead of Azure
  python pdf_chat_pipeline.py document.pdf --no-azure
  
  # Skip extraction if already done
  python pdf_chat_pipeline.py document.pdf --skip-extraction
  
  # Skip indexing if already done
  python pdf_chat_pipeline.py document.pdf --skip-indexing
        """
    )
    
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--output', '-o', default='pdf_extraction',
                        help='Output directory for extraction (default: pdf_extraction)')
    parser.add_argument('--collection', '-c', default='pdf_documents',
                        help='ChromaDB collection name (default: pdf_documents)')
    parser.add_argument('--clear', action='store_true',
                        help='Clear existing collection before indexing')
    parser.add_argument('--no-azure', action='store_true',
                        help='Use local embeddings instead of Azure OpenAI')
    parser.add_argument('--workers', '-w', type=int, default=4,
                        help='Number of parallel workers for extraction (default: 4)')
    parser.add_argument('--skip-extraction', action='store_true',
                        help='Skip extraction step (use existing output)')
    parser.add_argument('--skip-indexing', action='store_true',
                        help='Skip indexing step (use existing index)')
    
    args = parser.parse_args()
    
    # Check if skip flags make sense
    if args.skip_extraction and args.skip_indexing:
        # Just start chat with existing data
        console.print("[yellow]Skipping extraction and indexing, starting chat directly...[/yellow]")
        chat = PDFChatInterface(
            collection_name=args.collection,
            use_azure=not args.no_azure
        )
        try:
            chat.run()
        except KeyboardInterrupt:
            console.print("\n[yellow]Chat interrupted by user[/yellow]")
        return
    
    # Create pipeline
    pipeline = PDFChatPipeline(
        pdf_path=args.pdf_path,
        output_dir=args.output,
        collection_name=args.collection,
        use_azure=not args.no_azure,
        clear_db=args.clear,
        max_workers=args.workers
    )
    
    # Run with skip options
    if args.skip_extraction:
        console.print("[yellow]Skipping extraction step[/yellow]")
        # Check if output exists
        if not Path(args.output).exists():
            console.print(f"[red]Output directory not found: {args.output}[/red]")
            console.print("[red]Cannot skip extraction without existing output[/red]")
            return
    else:
        if not pipeline.extract_pdf():
            return
    
    if args.skip_indexing:
        console.print("[yellow]Skipping indexing step[/yellow]")
    else:
        if not pipeline.index_to_chromadb():
            return
    
    # Always start chat at the end
    pipeline.start_chat()


if __name__ == "__main__":
    main()