"""
Text processing utilities for PDF extraction.
Handles text matching, similarity calculation, and filtering.
"""

from typing import List, Optional
from core.pdf_extraction_models import TextElement, ElementMetadata, BoundingBox
from core.pdf_extraction_config import PDFConstants
from utils.bbox_operations import BoundingBoxOperations


class TextProcessor:
    """Processes and filters text elements from PDF extraction."""
    
    def __init__(self):
        self.high_resolution_text_elements: List[TextElement] = []
        self.filtered_text_elements: List[TextElement] = []
    
    def filter_text_within_visuals(self, 
                                  fast_text_elements: List[TextElement],
                                  figures: List[ElementMetadata],
                                  tables: List[ElementMetadata]) -> List[TextElement]:
        """Filter out text elements that are inside figures or tables."""
        filtered = []
        
        for text_element in fast_text_elements:
            if not self._is_text_inside_visual_element(text_element, figures, tables):
                filtered.append(text_element)
        
        return filtered
    
    def _is_text_inside_visual_element(self, 
                                      text_element: TextElement,
                                      figures: List[ElementMetadata],
                                      tables: List[ElementMetadata]) -> bool:
        """Check if text element is inside any visual element."""
        if not text_element.bounding_box:
            return False
        
        return (self._is_inside_figures(text_element, figures) or 
                self._is_inside_tables(text_element, tables))
    
    def _is_inside_figures(self, text_element: TextElement, figures: List[ElementMetadata]) -> bool:
        """Check if text is inside any figure."""
        for figure in figures:
            if (figure.page_number == text_element.page and 
                figure.bounding_box and
                self._is_text_inside_scaled_bbox(text_element, figure.bounding_box)):
                return True
        return False
    
    def _is_inside_tables(self, text_element: TextElement, tables: List[ElementMetadata]) -> bool:
        """Check if text is inside any table."""
        for table in tables:
            if (table.page_number == text_element.page and 
                table.bounding_box and
                self._is_text_inside_scaled_bbox(text_element, table.bounding_box)):
                return True
        return False
    
    def _is_text_inside_scaled_bbox(self, text_element: TextElement, visual_bbox: BoundingBox) -> bool:
        """Check if text is inside visual bounding box.
        
        Since fast mode coordinates are now scaled to hi-res during extraction,
        no additional scaling is needed here.
        """
        return BoundingBoxOperations.is_contained_within(text_element.bounding_box, visual_bbox)
    
    def match_detection_probabilities(self,
                                    filtered_text_elements: List[TextElement],
                                    high_resolution_text_elements: List[TextElement]) -> List[TextElement]:
        """Match filtered text elements with high-resolution detection probabilities."""
        for fast_element in filtered_text_elements:
            matching_element = self._find_matching_high_res_element(
                fast_element, high_resolution_text_elements
            )
            if matching_element:
                self._apply_high_res_classification(fast_element, matching_element)
        
        return filtered_text_elements
    
    def _find_matching_high_res_element(self, 
                                       fast_element: TextElement,
                                       high_resolution_text_elements: List[TextElement]) -> Optional[TextElement]:
        """Find matching high-resolution element for probability transfer."""
        best_match = None
        best_similarity_score = 0
        
        for high_res_element in high_resolution_text_elements:
            if high_res_element.page != fast_element.page:
                continue
            
            similarity_score = self.calculate_text_similarity(fast_element.text, high_res_element.text)
            if similarity_score > best_similarity_score:
                best_similarity_score = similarity_score
                best_match = high_res_element
        
        return best_match if best_similarity_score > 0 else None
    
    @staticmethod
    def calculate_text_similarity(fast_text: str, high_res_text: str) -> float:
        """Calculate similarity between two text strings."""
        fast_text = fast_text.strip()
        high_res_text = high_res_text.strip()
        
        if fast_text == high_res_text:
            return 1.0
        
        if fast_text in high_res_text or high_res_text in fast_text:
            overlap_length = min(len(fast_text), len(high_res_text))
            return overlap_length / max(len(fast_text), len(high_res_text))
        
        return 0.0
    
    def _apply_high_res_classification(self, fast_element: TextElement, high_res_element: TextElement) -> None:
        """Apply high-resolution classification to fast element."""
        if high_res_element.detection_probability is not None:
            fast_element.detection_probability = high_res_element.detection_probability
        
        # Keep fast mode bounding box coordinates for sections
        # Only update classification, not coordinates
        
        fast_element.original_type = fast_element.element_type
        fast_element.element_type = high_res_element.element_type