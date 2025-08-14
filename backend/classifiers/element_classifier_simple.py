"""
Element classification utilities for PDF processing.
Handles classification of elements as figures, tables, or other types.
"""

from typing import List, Optional
from unstructured.documents.elements import (
    Element,
    Image as UnstructuredImage,
    Table
)
from core.pdf_extraction_config import PDFConstants, CaptionKeywords, ElementType
from core.pdf_extraction_models import BoundingBox, BoundingBoxLegacy
from utils.bbox_operations import BoundingBoxOperations, BoundingBoxCalculator
from utils.caption_detector import CaptionDetector, CaptionExtractor


class ElementClassifier:
    """Classifies elements as figures or tables based on context and characteristics."""
    
    @classmethod
    def classify(cls, element: Element, elements: List[Element], 
                element_index: int, page: int) -> str:
        """Classify an element as figure or table (returns string for legacy compatibility)."""
        if cls._is_image_element(element):
            return 'figure'
        
        if isinstance(element, Table):
            return cls._classify_table(element, elements, element_index, page)
        
        return 'unknown'
    
    @classmethod
    def _is_image_element(cls, element: Element) -> bool:
        """Check if element is an image/figure."""
        return (isinstance(element, UnstructuredImage) or 
                (hasattr(element, 'category') and 
                 element.category in ['Image', 'Figure']))
    
    @classmethod
    def _classify_table(cls, element: Table, elements: List[Element],
                       element_index: int, page: int) -> str:
        """Classify Table element based on context and characteristics."""
        # Use CaptionExtractor for extract_all_elements.py compatibility
        caption_info = CaptionExtractor.find_for_element(
            elements, element_index, page
        )
        
        if caption_info.caption_type == 'figure':
            return 'figure'
        
        if caption_info.caption_type == 'table':
            return 'table'
        
        return cls._classify_by_characteristics(element, caption_info.description)
    
    @classmethod
    def _classify_by_characteristics(cls, element: Table, 
                                   description: Optional[str]) -> str:
        """Classify based on size and content characteristics."""
        bbox = BoundingBoxCalculator.extract_from_element(element)
        if bbox and bbox.width > 900 and bbox.height > 600:
            if description and any(word in description for word in 
                                 CaptionKeywords.PANEL_KEYWORDS):
                return 'figure'
        
        content = str(element)
        if cls._appears_to_be_diagram(content):
            return 'figure'
        
        return 'table'
    
    @classmethod
    def _appears_to_be_diagram(cls, content: str) -> bool:
        """Check if content appears to be a labeled diagram."""
        import re
        if re.search(r'\b\d+\s+\d+\s+\d+\s+\d+\b', content):
            single_digits = re.findall(r'\b\d\b', content)
            return len(single_digits) > 10
        return False


class ElementClassifierHybrid:
    """Element classifier for hybrid PDF extractor (uses ElementType enum)."""
    
    @classmethod
    def classify_element(cls, element: Element, elements: List[Element], 
                        element_index: int, current_page: int) -> ElementType:
        """Classify an element as figure or table."""
        if cls._is_image_element(element):
            return ElementType.FIGURE
        
        if isinstance(element, Table):
            return cls._classify_table_element(element, elements, element_index, current_page)
        
        return ElementType.UNKNOWN
    
    @classmethod
    def _is_image_element(cls, element: Element) -> bool:
        """Check if element is an image/figure."""
        return (isinstance(element, UnstructuredImage) or 
                (hasattr(element, 'category') and element.category in ['Image', 'Figure']))
    
    @classmethod
    def _classify_table_element(cls, element: Table, elements: List[Element], 
                              element_index: int, current_page: int) -> ElementType:
        """Classify Table element based on context and characteristics."""
        caption, description, _, caption_type = CaptionDetector.find_caption_and_description(
            elements, element_index, current_page
        )
        
        if caption_type == ElementType.FIGURE:
            return ElementType.FIGURE
        elif caption_type == ElementType.TABLE:
            return ElementType.TABLE
        
        return cls._classify_by_characteristics(element, description)
    
    @classmethod
    def _classify_by_characteristics(cls, element: Table, description: Optional[str]) -> ElementType:
        """Classify based on size and content characteristics."""
        bounding_box = BoundingBoxOperations.create_from_element(element)
        if not bounding_box:
            return ElementType.TABLE
        
        # Large elements without table captions might be figures
        if bounding_box.width > 900 and bounding_box.height > 600:
            if description and any(word in description for word in 
                                 CaptionKeywords.PANEL_KEYWORDS):
                return ElementType.FIGURE
        
        # Check for diagram-like content patterns
        if cls._has_diagram_pattern(str(element)):
            return ElementType.FIGURE
        
        return ElementType.TABLE
    
    @classmethod
    def _has_diagram_pattern(cls, content: str) -> bool:
        """Check if content has patterns typical of labeled diagrams."""
        import re
        
        if re.search(r'\b\d+\s+\d+\s+\d+\s+\d+\b', content):
            single_digits = re.findall(r'\b\d\b', content)
            return len(single_digits) > 10
        
        return False