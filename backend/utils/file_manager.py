"""
File management utilities for PDF extraction.
Handles directory creation, cleanup, and file organization.
"""

import shutil
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import tempfile
import os
import fitz


class PDFFileManager:
    """Manages file system operations for PDF extraction."""
    
    def __init__(self, output_directory: Path):
        self.output_directory = Path(output_directory)
        self.figures_directory = self.output_directory / "figures"
        self.tables_directory = self.output_directory / "tables"
    
    def setup_directories(self) -> None:
        """Create necessary output directories."""
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.figures_directory.mkdir(exist_ok=True)
        self.tables_directory.mkdir(exist_ok=True)
    
    def cleanup_page_directories(self, total_pages: int) -> None:
        """Remove temporary page directories."""
        for page_num in range(1, total_pages + 1):
            page_dir = self.output_directory / f"page_{page_num}"
            if page_dir.exists():
                shutil.rmtree(page_dir)
    
    def save_metadata_json(self, metadata: Dict[str, Any]) -> None:
        """Save metadata to JSON file."""
        metadata_path = self.output_directory / "metadata.json"
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def save_markdown_file(self, content: str, filename: str = "extracted_content.md") -> None:
        """Save markdown content to file."""
        markdown_path = self.output_directory / filename
        
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(content)


class PDFPageSplitter:
    """Handles splitting PDF into individual page files."""
    
    @staticmethod
    def split_pdf(pdf_path: str, temp_dir: str) -> List[Tuple[int, str]]:
        """Split PDF into individual page files.
        
        Returns list of (page_number, page_pdf_path) tuples.
        """
        page_files = []
        
        with fitz.open(pdf_path) as doc:
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Create new document with single page
                page_doc = fitz.open()
                page_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                
                # Save to temp file
                page_path = os.path.join(temp_dir, f"page_{page_num + 1}.pdf")
                page_doc.save(page_path)
                page_doc.close()
                
                page_files.append((page_num + 1, page_path))
        
        return page_files


class TempDirectoryManager:
    """Context manager for temporary directory handling."""
    
    def __init__(self):
        self.temp_dir = None
    
    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp()
        return self.temp_dir
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)