"""
Element classification for hybrid PDF extraction.
Specialized version with enum-based classification.
"""

from typing import List, Optional
from unstructured.documents.elements import Element, Table, Image as UnstructuredImage
from core.pdf_extraction_config import ElementType
from utils.caption_detector import CaptionDetector
from utils.bbox_operations import BoundingBoxOperations


class ElementClassifierHybrid:
    """Classifies elements as figures or tables based on context and characteristics."""
    
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
                                 ['panel', 'パネル', 'diagram', '図', 'Figure']):
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