"""
Refactored hybrid PDF extraction system.
Streamlined version using extracted modules for better maintainability.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import (
    Element, 
    Image as UnstructuredImage,
    Table,
    PageBreak,
    Header,
    Footer
)

# Import from centralized modules
from core.pdf_extraction_config import ExtractionStrategy, ElementType, PDFConstants
from core.pdf_extraction_models import BoundingBox, ElementMetadata, TextElement
from utils.bbox_operations import BoundingBoxOperations
from utils.caption_detector import CaptionDetector
from classifiers.element_classifier_hybrid import ElementClassifierHybrid
from processors.element_preprocessor import ElementPreprocessor
from processors.image_extractor import PDFRegionExtractor
from processors.table_exporter import TableDataSaver
from processors.text_processor import TextProcessor
from output.document_structure import DocumentStructureBuilder
from output.markdown_generator import MarkdownGenerator
from utils.file_manager import PDFFileManager


class HybridPDFExtractor:
    """
    Main extraction class combining high-resolution element detection 
    with fast text extraction.
    """
    
    def __init__(self, pdf_path: str, output_directory: str = "hybrid_extraction", 
                 dpi: int = PDFConstants.DEFAULT_DPI):
        self.pdf_path = pdf_path
        self.pdf_name = Path(pdf_path).stem
        self.output_directory = Path(output_directory)
        self.dpi = dpi
        
        # Initialize managers and processors
        self.file_manager = PDFFileManager(self.output_directory)
        self.text_processor = TextProcessor()
        self.structure_builder = DocumentStructureBuilder(self.pdf_name)
        self.markdown_generator = MarkdownGenerator(self.pdf_name)
        
        # Setup directories
        self.file_manager.setup_directories()
        
        # Initialize storage
        self._initialize_storage()
    
    def _initialize_storage(self) -> None:
        """Initialize storage containers."""
        self.figures: List[ElementMetadata] = []
        self.tables: List[ElementMetadata] = []
        self.fast_text_elements: List[TextElement] = []
        self.filtered_text_elements: List[TextElement] = []
        self.high_resolution_text_elements: List[TextElement] = []
    
    def extract_figures_and_tables(self) -> 'HybridPDFExtractor':
        """Extract figures and tables using high-resolution mode."""
        elements = self._partition_pdf_high_resolution()
        self._store_high_resolution_text_elements(elements)
        
        figures_tables_metadata = self._extract_visual_elements(elements)
        self._apply_size_filtering(figures_tables_metadata)
        
        return self
    
    def _partition_pdf_high_resolution(self) -> List[Element]:
        """Partition PDF using high-resolution strategy."""
        return partition_pdf(
            filename=self.pdf_path,
            strategy=ExtractionStrategy.HIGH_RESOLUTION.value,
            extract_images_in_pdf=True,
            extract_image_block_types=["Table", "Image", "Figure", "FigureCaption"],
            extract_image_block_to_payload=True,
            include_page_breaks=True,
            include_metadata=True,
            infer_table_structure=True,
            languages=['jpn', 'eng']
        )
    
    def _store_high_resolution_text_elements(self, elements: List[Element]) -> None:
        """Store high-resolution text elements for probability matching."""
        current_page = 1
        
        for element in elements:
            if isinstance(element, PageBreak):
                current_page += 1
                continue
            
            current_page = self._update_current_page(element, current_page)
            
            if self._should_store_text_element(element):
                text_element = self._create_text_element(element, current_page)
                if text_element:
                    self.high_resolution_text_elements.append(text_element)
    
    def _update_current_page(self, element: Element, current_page: int) -> int:
        """Update current page number from element metadata."""
        if (hasattr(element, 'metadata') and hasattr(element.metadata, 'page_number') 
            and element.metadata.page_number):
            return element.metadata.page_number
        return current_page
    
    def _should_store_text_element(self, element: Element) -> bool:
        """Check if element should be stored as text element."""
        return (not isinstance(element, (UnstructuredImage, Table, PageBreak, Footer, Header)) 
                and str(element).strip())
    
    def _create_text_element(self, element: Element, page: int) -> Optional[TextElement]:
        """Create TextElement from unstructured element."""
        text = str(element).strip()
        if not text:
            return None
        
        # Scale fast mode coordinates to hi-res coordinates (multiply by 2.78)
        bounding_box = BoundingBoxOperations.create_from_element(element, scale_to_hires=True)
        detection_probability = None
        
        if (hasattr(element, 'metadata') and 
            hasattr(element.metadata, 'detection_class_prob')):
            detection_probability = element.metadata.detection_class_prob
        
        return TextElement(
            element_type=type(element).__name__,
            text=text,
            page=page,
            bounding_box=bounding_box,
            detection_probability=detection_probability
        )
    
    def _extract_visual_elements(self, elements: List[Element]) -> Dict[str, List[Dict]]:
        """Extract visual elements using refactored logic."""
        from .pdf_simple_extractor import PDFElementExtractor
        
        extractor = PDFElementExtractor(
            output_dir=str(self.output_directory),
            dpi=self.dpi
        )
        
        return extractor.extract(
            pdf_path=self.pdf_path,
            strategy=ExtractionStrategy.HIGH_RESOLUTION.value
        )
    
    def _apply_size_filtering(self, metadata: Dict[str, List[Dict]]) -> None:
        """Apply size filtering to remove small figures."""
        filtered_figures = []
        
        for figure in metadata["figures"]:
            if self._should_keep_figure(figure):
                filtered_figures.append(figure)
        
        self.figures = [self._convert_to_element_metadata(fig, "figure") for fig in filtered_figures]
        self.tables = [self._convert_to_element_metadata(tbl, "table") for tbl in metadata["tables"]]
    
    def _should_keep_figure(self, figure: Dict) -> bool:
        """Check if figure meets minimum size requirements."""
        bounding_box_dict = figure.get('bounding_box')
        if not bounding_box_dict:
            return True
        
        width = bounding_box_dict.get('width', 0)
        height = bounding_box_dict.get('height', 0)
        area = width * height
        
        return not ((width < PDFConstants.MIN_FIGURE_WIDTH and height < PDFConstants.MIN_FIGURE_HEIGHT) 
                   or area < PDFConstants.MIN_FIGURE_AREA)
    
    def _convert_to_element_metadata(self, element_dict: Dict, element_type: str) -> ElementMetadata:
        """Convert dictionary metadata to ElementMetadata object."""
        bounding_box = None
        if element_dict.get('bounding_box'):
            bbox_dict = element_dict['bounding_box']
            bounding_box = BoundingBox(
                x_min=bbox_dict['x0'],
                y_min=bbox_dict['y0'],
                x_max=bbox_dict['x1'],
                y_max=bbox_dict['y1']
            )
        
        return ElementMetadata(
            filename=element_dict.get('filename', ''),
            source_pdf=element_dict.get('source_pdf', ''),
            page_number=element_dict.get('page_number', 1),
            index=element_dict.get(f'{element_type}_index', 0),
            caption=element_dict.get('caption'),
            description=element_dict.get('description'),
            bounding_box=bounding_box,
            original_type=element_dict.get('original_type', ''),
            is_reclassified=element_dict.get('reclassified', False),
            element_id=element_dict.get('element_id')
        )
    
    def extract_text_fast_mode(self) -> 'HybridPDFExtractor':
        """Extract text using fast mode for cleaner results."""
        elements = partition_pdf(
            filename=self.pdf_path,
            strategy=ExtractionStrategy.FAST.value,
            include_page_breaks=True,
            include_metadata=True,
            languages=['jpn', 'eng']
        )
        
        current_page = 1
        
        for element in elements:
            if isinstance(element, PageBreak):
                current_page += 1
                continue
            
            current_page = self._update_current_page(element, current_page)
            
            if isinstance(element, (Footer, Header)):
                continue
            
            text_element = self._create_text_element(element, current_page)
            if text_element:
                self.fast_text_elements.append(text_element)
        
        return self
    
    def filter_text_within_visuals(self) -> 'HybridPDFExtractor':
        """Filter out text elements that are inside figures or tables."""
        self.filtered_text_elements = self.text_processor.filter_text_within_visuals(
            self.fast_text_elements, self.figures, self.tables
        )
        return self
    
    def match_detection_probabilities(self) -> 'HybridPDFExtractor':
        """Match filtered text elements with high-resolution detection probabilities."""
        self.filtered_text_elements = self.text_processor.match_detection_probabilities(
            self.filtered_text_elements, self.high_resolution_text_elements
        )
        return self
    
    def generate_markdown_output(self) -> 'HybridPDFExtractor':
        """Generate clean Markdown output with figures and tables."""
        # Build metadata structure
        metadata = self.structure_builder.build_metadata_structure(
            self.filtered_text_elements, self.figures, self.tables
        )
        
        # Generate markdown file
        all_elements = self.structure_builder.combine_all_elements(
            self.filtered_text_elements, self.figures, self.tables
        )
        self.markdown_generator.generate_markdown_file(
            self.output_directory / "extracted_content.md",
            all_elements
        )
        
        # Save metadata JSON
        self.file_manager.save_metadata_json(metadata)
        
        return self


class ExtractionOrchestrator:
    """Orchestrates the complete PDF extraction workflow."""
    
    @staticmethod
    def execute_extraction(pdf_path: str, output_directory: str = "hybrid_extraction", 
                          dpi: int = PDFConstants.DEFAULT_DPI) -> HybridPDFExtractor:
        """Execute complete extraction workflow."""
        extractor = HybridPDFExtractor(pdf_path, output_directory, dpi)
        
        return (extractor
                .extract_figures_and_tables()
                .extract_text_fast_mode()
                .filter_text_within_visuals()
                .match_detection_probabilities()
                .generate_markdown_output())


def main() -> None:
    """Main entry point for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python hybrid_pdf_extractor_refactored.py <pdf_path> [output_dir] [dpi]")
        print("Example: python hybrid_pdf_extractor_refactored.py document.pdf")
        print("Example: python hybrid_pdf_extractor_refactored.py document.pdf extraction_output 150")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) > 2 else "hybrid_extraction"
    dpi = PDFConstants.DEFAULT_DPI
    
    if len(sys.argv) > 3:
        try:
            dpi = int(sys.argv[3])
        except ValueError:
            print(f"Invalid DPI value: {sys.argv[3]}")
            sys.exit(1)
    
    try:
        ExtractionOrchestrator.execute_extraction(pdf_path, output_directory, dpi)
    except Exception as error:
        print(f"Error during extraction: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()