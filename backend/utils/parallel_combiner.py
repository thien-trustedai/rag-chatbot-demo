"""
Result combination utilities for parallel PDF extraction.
Handles merging results from multiple page extractions.
"""

from typing import List, Dict, Any
from pathlib import Path
import shutil


class ParallelResultCombiner:
    """Combines results from parallel page extraction."""
    
    def __init__(self, pdf_name: str, output_directory: Path):
        self.pdf_name = pdf_name
        self.output_directory = output_directory
        self.figures_directory = output_directory / "figures"
        self.tables_directory = output_directory / "tables"
    
    def combine_page_results(self, page_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine metadata from all pages into a single structure."""
        
        combined_structure = []
        total_figures = 0
        total_tables = 0
        figure_counter = 0
        table_counter = 0
        section_counter = 0
        
        for page_result in page_results:
            if not page_result["success"] or not page_result["metadata"]:
                continue
            
            page_num = page_result["page"]
            page_metadata = page_result["metadata"]
            
            # Process each section in the page
            for section in page_metadata.get("structure", []):
                section_counter += 1
                
                # Update section ID and index
                section["id"] = f"section_{section_counter}"
                section["index"] = section_counter
                section["page"] = page_num
                
                # Renumber figures in section
                for figure in section.get("figures", []):
                    figure_counter += 1
                    old_index = figure["index"]
                    figure["index"] = figure_counter
                    figure["id"] = f"figure_{figure_counter}"
                    figure["page"] = page_num
                    
                    # Store mapping for consolidation
                    figure["_page_local_index"] = old_index
                    figure["_global_index"] = figure_counter
                    
                    # Update path to use global index with page number
                    figure["filename"] = f"page{page_num}_fig{figure_counter}.png"
                    figure["path"] = f"figures/page{page_num}_fig{figure_counter}.png"
                    
                    total_figures += 1
                
                # Renumber tables in section
                for table in section.get("tables", []):
                    table_counter += 1
                    old_index = table["index"]
                    table["index"] = table_counter
                    table["id"] = f"table_{table_counter}"
                    table["page"] = page_num
                    
                    # Store mapping for consolidation
                    table["_page_local_index"] = old_index
                    table["_global_index"] = table_counter
                    
                    # Update paths to use global index with page number
                    table["filename"] = f"page{page_num}_table{table_counter}.png"
                    table["path"] = f"tables/page{page_num}_table{table_counter}.png"
                    table["csv_path"] = f"tables/page{page_num}_table{table_counter}.csv"
                    
                    total_tables += 1
                
                # Fix text_content to have correct figure/table references
                self.fix_text_content_references(section)
                
                combined_structure.append(section)
        
        # Build final metadata
        combined_metadata = {
            "extraction_info": {
                "source_pdf": self.pdf_name,
                "total_pages": len(page_results),
                "successful_pages": sum(1 for r in page_results if r["success"]),
                "total_figures": total_figures,
                "total_tables": total_tables,
                "total_sections": len(combined_structure)
            },
            "structure": combined_structure
        }
        
        return combined_metadata
    
    def fix_text_content_references(self, section: Dict[str, Any]) -> None:
        """Fix figure and table references in text_content to use correct page numbers."""
        text_content = section.get("text_content", "")
        page_num = section.get("page", 1)
        
        # Fix figure references
        for figure in section.get("figures", []):
            global_index = figure.get("_global_index", figure.get("index", 1))
            # Replace any page1_figX references with the correct page and global index
            old_ref = f"figures/page1_fig{figure.get('_page_local_index', 1)}.png"
            new_ref = f"figures/page{page_num}_fig{global_index}.png"
            text_content = text_content.replace(old_ref, new_ref)
        
        # Fix table references
        for table in section.get("tables", []):
            global_index = table.get("_global_index", table.get("index", 1))
            # Replace any page1_tableX references with the correct page and global index
            old_ref = f"tables/page1_table{table.get('_page_local_index', 1)}.png"
            new_ref = f"tables/page{page_num}_table{global_index}.png"
            text_content = text_content.replace(old_ref, new_ref)
        
        section["text_content"] = text_content
    
    def consolidate_visual_elements(self, combined_metadata: Dict[str, Any]) -> None:
        """Move figures and tables from page directories to main directories using correct numbering."""
        
        # Copy files using the mappings already set in combine_page_results
        for section in combined_metadata.get("structure", []):
            page_num = section.get("page", 1)
            page_dir = self.output_directory / f"page_{page_num}"
            
            if not page_dir.exists():
                continue
            
            # Copy figures using global index
            for figure in section.get("figures", []):
                self._copy_figure_files(figure, page_num, page_dir)
                # Clean up temporary metadata
                figure.pop("_page_local_index", None)
                figure.pop("_global_index", None)
            
            # Copy tables using global index
            for table in section.get("tables", []):
                self._copy_table_files(table, page_num, page_dir)
                # Clean up temporary metadata
                table.pop("_page_local_index", None)
                table.pop("_global_index", None)
    
    def _copy_figure_files(self, figure: Dict, page_num: int, page_dir: Path) -> None:
        """Copy figure files from page directory to main figures directory."""
        page_local_index = figure.get("_page_local_index", 1)
        global_index = figure.get("_global_index", figure.get("index", 1))
        
        # Original file is named with just the page-local index
        source_pattern = f"fig{page_local_index}.*"
        page_figures_dir = page_dir / "figures"
        
        if page_figures_dir.exists():
            matching_files = list(page_figures_dir.glob(source_pattern))
            if matching_files:
                source_file = matching_files[0]
                # Use global index in the new filename
                ext = source_file.suffix
                new_name = f"page{page_num}_fig{global_index}{ext}"
                new_path = self.figures_directory / new_name
                
                if not new_path.exists():
                    shutil.copy2(source_file, new_path)
    
    def _copy_table_files(self, table: Dict, page_num: int, page_dir: Path) -> None:
        """Copy table files from page directory to main tables directory."""
        page_local_index = table.get("_page_local_index", 1)
        global_index = table.get("_global_index", table.get("index", 1))
        
        page_tables_dir = page_dir / "tables"
        
        if page_tables_dir.exists():
            # Copy PNG file
            png_files = list(page_tables_dir.glob(f"table{page_local_index}.png"))
            if png_files:
                source_file = png_files[0]
                new_name = f"page{page_num}_table{global_index}.png"
                new_path = self.tables_directory / new_name
                if not new_path.exists():
                    shutil.copy2(source_file, new_path)
            
            # Copy CSV file
            csv_files = list(page_tables_dir.glob(f"table{page_local_index}.csv"))
            if csv_files:
                source_file = csv_files[0]
                new_name = f"page{page_num}_table{global_index}.csv"
                new_path = self.tables_directory / new_name
                if not new_path.exists():
                    shutil.copy2(source_file, new_path)