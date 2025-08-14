"""
Caption detection and extraction utilities for PDF processing.
Handles finding and classifying captions for figures and tables.
"""

from typing import List, Optional, Tuple
from unstructured.documents.elements import (
    Element, 
    Title,
    Text,
    NarrativeText
)
from core.pdf_extraction_config import PDFConstants, CaptionKeywords, ElementType
from core.pdf_extraction_models import BoundingBox, BoundingBoxLegacy, CaptionInfo
from .bbox_operations import BoundingBoxOperations, BoundingBoxCalculator


class CaptionDetector:
    """Detects captions and descriptions for visual elements."""
    
    # Use keywords from centralized config
    FIGURE_KEYWORDS = CaptionKeywords.FIGURE_KEYWORDS
    TABLE_KEYWORDS = CaptionKeywords.TABLE_KEYWORDS
    DESCRIPTION_KEYWORDS = CaptionKeywords.DESCRIPTION_KEYWORDS
    
    @classmethod
    def find_caption_and_description(cls, elements: List[Element], 
                                   element_index: int, element_page: int) -> Tuple[Optional[str], Optional[str], Optional[BoundingBox], ElementType]:
        """Find caption text and description near an element."""
        caption = None
        description = None
        title_bounding_box = None
        caption_type = ElementType.UNKNOWN
        
        search_start = max(0, element_index - PDFConstants.CAPTION_SEARCH_RANGE)
        search_end = min(len(elements), element_index + PDFConstants.CAPTION_SEARCH_RANGE + 1)
        
        for index in range(search_start, search_end):
            if index == element_index:
                continue
            
            current_element = elements[index]
            
            if not cls._is_on_same_page(current_element, element_page):
                continue
            
            caption_result = cls._extract_caption_from_element(current_element, element_index, index, caption, caption_type)
            if caption_result:
                caption, caption_type, title_bounding_box = caption_result
            
            if not description:
                description = cls._extract_description_from_element(current_element, element_index, index)
        
        return caption, description, title_bounding_box, caption_type
    
    @classmethod
    def _is_on_same_page(cls, element: Element, target_page: int) -> bool:
        """Check if element is on the target page."""
        if not hasattr(element, 'metadata') or not hasattr(element.metadata, 'page_number'):
            return True  # Assume same page if no page info
        
        return element.metadata.page_number == target_page if element.metadata.page_number else True
    
    @classmethod
    def _extract_caption_from_element(cls, element: Element, target_index: int, 
                                    current_index: int, existing_caption: Optional[str], 
                                    existing_type: ElementType) -> Optional[Tuple[str, ElementType, Optional[BoundingBox]]]:
        """Extract caption from Title or Text elements."""
        if isinstance(element, Title):
            return cls._process_title_element(element, target_index, current_index, existing_caption)
        elif isinstance(element, Text) and not existing_caption:
            return cls._process_text_element(element, target_index, current_index)
        
        return None
    
    @classmethod
    def _process_title_element(cls, element: Title, target_index: int, 
                             current_index: int, existing_caption: Optional[str]) -> Optional[Tuple[str, ElementType, Optional[BoundingBox]]]:
        """Process Title element for caption extraction."""
        text = str(element).strip()
        
        # Check for table patterns first (more specific)
        if any(pattern in text.lower() for pattern in cls.TABLE_KEYWORDS):
            if cls._is_closer_match(current_index, target_index, existing_caption):
                return text, ElementType.TABLE, BoundingBoxOperations.create_from_element(element)
        
        # Check for figure patterns
        elif any(pattern in text for pattern in cls.FIGURE_KEYWORDS):
            if cls._is_closer_match(current_index, target_index, existing_caption):
                return text, ElementType.FIGURE, BoundingBoxOperations.create_from_element(element)
        
        return None
    
    @classmethod
    def _process_text_element(cls, element: Text, target_index: int, 
                            current_index: int) -> Optional[Tuple[str, ElementType, Optional[BoundingBox]]]:
        """Process Text element for table caption extraction."""
        text = str(element).strip()
        
        if any(pattern in text.lower() for pattern in cls.TABLE_KEYWORDS):
            return text, ElementType.TABLE, BoundingBoxOperations.create_from_element(element)
        
        return None
    
    @classmethod
    def _is_closer_match(cls, current_index: int, target_index: int, existing_caption: Optional[str]) -> bool:
        """Check if current element is closer than existing caption."""
        return not existing_caption or abs(current_index - target_index) < abs(target_index - current_index)
    
    @classmethod
    def _extract_description_from_element(cls, element: Element, target_index: int, current_index: int) -> Optional[str]:
        """Extract description from NarrativeText elements."""
        if not isinstance(element, NarrativeText) or abs(current_index - target_index) > 2:
            return None
        
        text = str(element).strip()
        if any(pattern in text for pattern in cls.DESCRIPTION_KEYWORDS):
            return text
        
        return None


class CaptionExtractor:
    """Extracts captions for elements (legacy naming for extract_all_elements.py)."""
    
    @staticmethod
    def find_for_element(elements: List[Element], element_index: int, 
                        element_page: int) -> CaptionInfo:
        """Find caption info for an element."""
        start_idx = max(0, element_index - PDFConstants.CAPTION_SEARCH_RANGE)
        end_idx = min(len(elements), element_index + PDFConstants.CAPTION_SEARCH_RANGE + 1)
        
        caption = None
        description = None
        title_bbox = None
        caption_type = 'unknown'
        
        for i in range(start_idx, end_idx):
            if i == element_index:
                continue
                
            element = elements[i]
            if not CaptionExtractor._is_same_page(element, element_page):
                continue
            
            if isinstance(element, Title):
                caption_candidate = CaptionExtractor._extract_title_caption(
                    element, i, element_index, caption
                )
                if caption_candidate:
                    caption, caption_type, title_bbox = caption_candidate
            
            elif isinstance(element, NarrativeText) and not description:
                description = CaptionExtractor._extract_description(
                    element, i, element_index
                )
            
            elif isinstance(element, Text) and not caption:
                caption_candidate = CaptionExtractor._extract_text_caption(
                    element, i, element_index, caption
                )
                if caption_candidate:
                    caption, caption_type, title_bbox = caption_candidate
        
        return CaptionInfo(caption, description, title_bbox, caption_type)
    
    @staticmethod
    def _is_same_page(element: Element, target_page: int) -> bool:
        """Check if element is on the same page."""
        if not (hasattr(element, 'metadata') and 
                hasattr(element.metadata, 'page_number')):
            return True
        return element.metadata.page_number == target_page
    
    @staticmethod
    def _extract_title_caption(element: Title, element_index: int,
                              target_index: int, existing_caption: Optional[str]
                              ) -> Optional[Tuple[str, str, Optional[BoundingBoxLegacy]]]:
        """Extract caption from Title element."""
        text = str(element).strip()
        
        if CaptionExtractor._is_table_caption(text):
            if CaptionExtractor._is_closer_than_existing(
                element_index, target_index, existing_caption
            ):
                return text, 'table', BoundingBoxCalculator.extract_from_element(element)
        
        elif CaptionExtractor._is_figure_caption(text):
            if CaptionExtractor._is_closer_than_existing(
                element_index, target_index, existing_caption
            ):
                return text, 'figure', BoundingBoxCalculator.extract_from_element(element)
        
        return None
    
    @staticmethod
    def _extract_text_caption(element: Text, element_index: int,
                             target_index: int, existing_caption: Optional[str]
                             ) -> Optional[Tuple[str, str, Optional[BoundingBoxLegacy]]]:
        """Extract caption from Text element."""
        text = str(element).strip()
        
        if CaptionExtractor._is_table_caption(text):
            if CaptionExtractor._is_closer_than_existing(
                element_index, target_index, existing_caption
            ):
                return text, 'table', BoundingBoxCalculator.extract_from_element(element)
        
        return None
    
    @staticmethod
    def _extract_description(element: NarrativeText, element_index: int,
                            target_index: int) -> Optional[str]:
        """Extract description from NarrativeText element."""
        if abs(element_index - target_index) <= 2:
            text = str(element).strip()
            if any(pattern in text for pattern in 
                  ['図', 'Figure', 'table', '表', 'Table']):
                return text
        return None
    
    @staticmethod
    def _is_table_caption(text: str) -> bool:
        """Check if text is a table caption."""
        return any(pattern in text.lower() for pattern in 
                  CaptionKeywords.TABLE_KEYWORDS)
    
    @staticmethod
    def _is_figure_caption(text: str) -> bool:
        """Check if text is a figure caption."""
        return any(pattern in text for pattern in 
                  CaptionKeywords.FIGURE_KEYWORDS)
    
    @staticmethod
    def _is_closer_than_existing(element_index: int, target_index: int,
                                existing_caption: Optional[str]) -> bool:
        """Check if element is closer than existing caption."""
        return not existing_caption or abs(element_index - target_index) < 3