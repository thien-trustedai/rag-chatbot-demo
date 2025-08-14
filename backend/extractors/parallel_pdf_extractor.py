"""
Refactored parallel PDF extraction system.
Streamlined version using extracted modules for better maintainability.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

# Import from refactored modules
from core.pdf_extraction_config import PDFConstants
from core.pdf_extraction_models import PageExtractionTask
from utils.file_manager import PDFFileManager, PDFPageSplitter
from utils.parallel_combiner import ParallelResultCombiner
from output.markdown_generator import ParallelMarkdownGenerator
from .pdf_hybrid_extractor import HybridPDFExtractor


def process_single_page(task: PageExtractionTask) -> Dict[str, Any]:
    """Process a single page extraction task.
    
    This function runs in a separate process.
    """
    try:
        # Create page-specific output directory
        page_output_dir = os.path.join(task.output_dir, f"page_{task.page_number}")
        os.makedirs(page_output_dir, exist_ok=True)
        
        # Extract using existing hybrid extractor
        # Import here since this runs in a subprocess
        from extractors.pdf_hybrid_extractor import HybridPDFExtractor
        extractor = HybridPDFExtractor(
            pdf_path=task.pdf_path,
            output_directory=page_output_dir,
            dpi=task.dpi
        )
        
        # Run extraction pipeline
        extractor = (extractor
                    .extract_figures_and_tables()
                    .extract_text_fast_mode()
                    .filter_text_within_visuals()
                    .match_detection_probabilities())
        
        # Build metadata for this page
        page_metadata = extractor.structure_builder.build_metadata_structure(
            extractor.filtered_text_elements, 
            extractor.figures, 
            extractor.tables
        )
        
        # Add page number to all elements
        for section in page_metadata.get("structure", []):
            section["page"] = task.page_number
            
            # Update page numbers in figures and tables
            for figure in section.get("figures", []):
                figure["page"] = task.page_number
            for table in section.get("tables", []):
                table["page"] = task.page_number
        
        return {
            "page": task.page_number,
            "success": True,
            "metadata": page_metadata,
            "figures": extractor.figures,
            "tables": extractor.tables,
            "text_elements": extractor.filtered_text_elements
        }
        
    except Exception as e:
        return {
            "page": task.page_number,
            "success": False,
            "error": str(e),
            "metadata": None
        }


class ParallelPDFExtractor:
    """Main class for parallel PDF extraction."""
    
    def __init__(self, pdf_path: str, output_directory: str = "parallel_extraction",
                 dpi: int = PDFConstants.DEFAULT_DPI, max_workers: int = 4):
        self.pdf_path = pdf_path
        self.pdf_name = Path(pdf_path).stem
        self.output_directory = Path(output_directory)
        self.dpi = dpi
        self.max_workers = min(max_workers, cpu_count())
        
        # Initialize managers
        self.file_manager = PDFFileManager(self.output_directory)
        self.result_combiner = ParallelResultCombiner(self.pdf_name, self.output_directory)
        self.markdown_generator = ParallelMarkdownGenerator(self.pdf_name)
        
        # Setup directories
        self.file_manager.setup_directories()
    
    def extract(self) -> Dict[str, Any]:
        """Extract all pages in parallel and combine results."""
        
        # Create temporary directory for page files
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Splitting PDF into pages...")
            
            # Split PDF into pages
            page_files = PDFPageSplitter.split_pdf(self.pdf_path, temp_dir)
            total_pages = len(page_files)
            
            print(f"Processing {total_pages} pages with {self.max_workers} workers...")
            
            # Create extraction tasks
            tasks = self._create_extraction_tasks(page_files)
            
            # Process pages in parallel
            page_results = self._process_pages_parallel(tasks, total_pages)
            
            # Sort results by page number
            page_results.sort(key=lambda x: x["page"])
            
            # Combine results
            print("Combining results...")
            combined_metadata = self.result_combiner.combine_page_results(page_results)
            
            # Move figures and tables to main directories
            self.result_combiner.consolidate_visual_elements(combined_metadata)
            
            # Generate final outputs
            self._generate_final_outputs(combined_metadata)
            
            # Clean up page directories
            self.file_manager.cleanup_page_directories(total_pages)
            
            print(f"Extraction complete! Output saved to {self.output_directory}")
            
            return combined_metadata
    
    def _create_extraction_tasks(self, page_files: List[tuple]) -> List[PageExtractionTask]:
        """Create extraction tasks for all pages."""
        tasks = []
        for page_num, page_path in page_files:
            task = PageExtractionTask(
                pdf_path=page_path,
                page_number=page_num,
                output_dir=str(self.output_directory),
                dpi=self.dpi,
                original_pdf_name=self.pdf_name
            )
            tasks.append(task)
        return tasks
    
    def _process_pages_parallel(self, tasks: List[PageExtractionTask], total_pages: int) -> List[Dict]:
        """Process pages in parallel using ProcessPoolExecutor."""
        page_results = []
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {executor.submit(process_single_page, task): task 
                             for task in tasks}
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    page_results.append(result)
                    
                    if result["success"]:
                        print(f"✓ Processed page {result['page']}/{total_pages}")
                    else:
                        print(f"✗ Failed page {result['page']}: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    print(f"✗ Error processing page {task.page_number}: {e}")
                    page_results.append({
                        "page": task.page_number,
                        "success": False,
                        "error": str(e)
                    })
        
        return page_results
    
    def _generate_final_outputs(self, combined_metadata: Dict[str, Any]) -> None:
        """Generate final markdown and metadata files."""
        # Generate markdown
        self.markdown_generator.generate_combined_markdown(
            self.output_directory / "extracted_content.md",
            combined_metadata
        )
        
        # Save metadata JSON
        self.file_manager.save_metadata_json(combined_metadata)


def main():
    """Main entry point for command-line usage."""
    
    if len(sys.argv) < 2:
        print("Usage: python parallel_pdf_extractor.py <pdf_path> [output_dir] [max_workers] [dpi]")
        print("Example: python parallel_pdf_extractor.py document.pdf")
        print("Example: python parallel_pdf_extractor.py document.pdf output 4 150")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) > 2 else "parallel_extraction"
    max_workers = 4
    dpi = PDFConstants.DEFAULT_DPI
    
    if len(sys.argv) > 3:
        try:
            max_workers = int(sys.argv[3])
        except ValueError:
            print(f"Invalid max_workers value: {sys.argv[3]}")
            sys.exit(1)
    
    if len(sys.argv) > 4:
        try:
            dpi = int(sys.argv[4])
        except ValueError:
            print(f"Invalid DPI value: {sys.argv[4]}")
            sys.exit(1)
    
    try:
        extractor = ParallelPDFExtractor(
            pdf_path=pdf_path,
            output_directory=output_directory,
            max_workers=max_workers,
            dpi=dpi
        )
        
        metadata = extractor.extract()
        
        print(f"\nExtraction Summary:")
        print(f"  Total pages: {metadata['extraction_info']['total_pages']}")
        print(f"  Successful pages: {metadata['extraction_info']['successful_pages']}")
        print(f"  Total figures: {metadata['extraction_info']['total_figures']}")
        print(f"  Total tables: {metadata['extraction_info']['total_tables']}")
        print(f"  Total sections: {metadata['extraction_info']['total_sections']}")
        
    except Exception as e:
        print(f"Error during extraction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()