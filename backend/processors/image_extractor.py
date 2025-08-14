"""
Image extraction utilities for PDF processing.
Handles extraction of images from PDF pages using PyMuPDF.
"""

import fitz
from typing import Optional
from core.pdf_extraction_config import PDFConstants
from core.pdf_extraction_models import BoundingBoxLegacy as BoundingBox


class ImageExtractor:
    """Extracts images from PDF pages using PyMuPDF."""
    
    @staticmethod
    def extract_from_pdf(pdf_path: str, bbox: BoundingBox, page_num: int,
                        output_path: str, dpi: int = PDFConstants.HIGH_DPI) -> bool:
        """
        Extract image from PDF page at specified bounding box.
        
        Args:
            pdf_path: Path to PDF file
            bbox: Bounding box coordinates for image region
            page_num: Page number (1-indexed)
            output_path: Path to save extracted image
            dpi: DPI for image extraction
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]
            
            scaled_rect = fitz.Rect(
                bbox.x0 * PDFConstants.COORDINATE_SCALE_FACTOR,
                bbox.y0 * PDFConstants.COORDINATE_SCALE_FACTOR,
                bbox.x1 * PDFConstants.COORDINATE_SCALE_FACTOR,
                bbox.y1 * PDFConstants.COORDINATE_SCALE_FACTOR
            )
            
            scaled_rect.intersect(page.rect)
            
            zoom_factor = dpi / 72.0
            mat = fitz.Matrix(zoom_factor, zoom_factor)
            pix = page.get_pixmap(matrix=mat, clip=scaled_rect, alpha=False)
            
            pix.save(output_path)
            doc.close()
            return True
            
        except Exception:
            return False


class PDFRegionExtractor:
    """Extracts regions from PDF with coordinate scaling."""
    
    def __init__(self, scale_factor: float = PDFConstants.COORDINATE_SCALE_FACTOR):
        self.scale_factor = scale_factor
    
    def extract_region(self, pdf_path: str, bbox: BoundingBox, page_num: int,
                      output_path: str, dpi: int = PDFConstants.HIGH_DPI) -> bool:
        """
        Extract a region from PDF with proper scaling.
        
        Args:
            pdf_path: Path to PDF file
            bbox: Bounding box for region to extract
            page_num: Page number (1-indexed)
            output_path: Output path for extracted image
            dpi: DPI for extraction
            
        Returns:
            True if successful, False otherwise
        """
        return ImageExtractor.extract_from_pdf(pdf_path, bbox, page_num, output_path, dpi)
    
    @staticmethod
    def extract_region(pdf_path: str, bounding_box: BoundingBox, page_number: int, 
                      output_path: str, dpi: int = PDFConstants.DEFAULT_DPI) -> bool:
        """Extract a region from PDF using PyMuPDF with proper scaling (hybrid extractor compatibility)."""
        try:
            with fitz.open(pdf_path) as document:
                page = document[page_number - 1]
                
                scaled_rectangle = fitz.Rect(
                    bounding_box.x_min * PDFConstants.UNSTRUCTURED_TO_PYMUPDF_SCALE,
                    bounding_box.y_min * PDFConstants.UNSTRUCTURED_TO_PYMUPDF_SCALE,
                    bounding_box.x_max * PDFConstants.UNSTRUCTURED_TO_PYMUPDF_SCALE,
                    bounding_box.y_max * PDFConstants.UNSTRUCTURED_TO_PYMUPDF_SCALE
                )
                
                scaled_rectangle.intersect(page.rect)
                
                zoom_factor = dpi / 72.0
                transformation_matrix = fitz.Matrix(zoom_factor, zoom_factor)
                pixmap = page.get_pixmap(matrix=transformation_matrix, clip=scaled_rectangle, alpha=False)
                
                pixmap.save(output_path)
                
            return True
            
        except Exception:
            return False