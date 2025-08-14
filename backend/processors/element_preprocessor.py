"""
Element processing utilities for PDF extraction.
Handles preprocessing, containment rules, and adjacency detection.
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from unstructured.documents.elements import (
    Element,
    Image as UnstructuredImage,
    Table,
    PageBreak,
    Footer,
    Header
)
from core.pdf_extraction_config import PDFConstants
from core.pdf_extraction_models import ElementInfo, BoundingBox, BoundingBoxLegacy
from utils.bbox_operations import BoundingBoxOperations, BoundingBoxCalculator
from utils.caption_detector import CaptionDetector, CaptionExtractor


class ElementProcessor:
    """Processes elements for extraction (used by extract_all_elements.py)."""
    
    @staticmethod
    def preprocess_elements(elements: List[Element]) -> List[ElementInfo]:
        """Preprocess elements applying containment and adjacency rules."""
        elements_with_bbox = ElementProcessor._build_element_list(elements)
        ElementProcessor._apply_containment_rules(elements_with_bbox, elements)
        ElementProcessor._apply_adjacency_rules(elements_with_bbox, elements)
        return elements_with_bbox
    
    @staticmethod
    def _build_element_list(elements: List[Element]) -> List[ElementInfo]:
        """Build list of visual elements with bounding boxes."""
        elements_with_bbox = []
        
        for idx, element in enumerate(elements):
            if not ElementProcessor._should_process_element(element):
                continue
            
            bbox = BoundingBoxCalculator.extract_from_element(element)
            page = ElementProcessor._get_page_number(element)
            
            if bbox:
                elements_with_bbox.append(
                    ElementInfo(element, idx, bbox, page)
                )
        
        return elements_with_bbox
    
    @staticmethod
    def _should_process_element(element: Element) -> bool:
        """Check if element should be processed."""
        return (isinstance(element, (UnstructuredImage, Table)) or 
                (hasattr(element, 'category') and 
                 element.category in ['Image', 'Figure']))
    
    @staticmethod
    def _get_page_number(element: Element) -> int:
        """Get page number from element."""
        if (hasattr(element, 'metadata') and 
            hasattr(element.metadata, 'page_number') and
            element.metadata.page_number):
            return element.metadata.page_number
        return 1
    
    @staticmethod
    def _apply_containment_rules(elements_with_bbox: List[ElementInfo],
                                original_elements: List[Element]) -> None:
        """Apply rules for contained elements and same-caption duplicates."""
        for i, elem1 in enumerate(elements_with_bbox):
            if elem1.skip:
                continue
            
            caption1_info = CaptionExtractor.find_for_element(
                original_elements, elem1.index, elem1.page
            )
            
            for j, elem2 in enumerate(elements_with_bbox):
                if i == j or elem2.skip or elem1.page != elem2.page:
                    continue
                
                if BoundingBoxCalculator.is_contained(elem1.bbox, elem2.bbox):
                    elem1.skip = True
                    break
                
                caption2_info = CaptionExtractor.find_for_element(
                    original_elements, elem2.index, elem2.page
                )
                
                if ElementProcessor._should_skip_duplicate_caption(
                    caption1_info.text, caption2_info.text, 
                    elem1.bbox, elem2.bbox
                ):
                    elem1.skip = True
                    break
    
    @staticmethod
    def _should_skip_duplicate_caption(caption1: Optional[str], 
                                      caption2: Optional[str],
                                      bbox1: BoundingBoxLegacy, 
                                      bbox2: BoundingBoxLegacy) -> bool:
        """Check if element should be skipped due to duplicate caption."""
        if not (caption1 and caption2 and caption1 == caption2):
            return False
        return bbox1.area < bbox2.area
    
    @staticmethod
    def _apply_adjacency_rules(elements_with_bbox: List[ElementInfo],
                              original_elements: List[Element]) -> None:
        """Apply rules for merging adjacent elements when one lacks caption."""
        for i, elem1 in enumerate(elements_with_bbox):
            if elem1.skip or elem1.merge_with is not None:
                continue
            
            caption1_info = CaptionExtractor.find_for_element(
                original_elements, elem1.index, elem1.page
            )
            
            if caption1_info.text:
                continue
            
            for j, elem2 in enumerate(elements_with_bbox):
                if (i == j or elem2.skip or elem2.merge_with is not None or
                    elem1.page != elem2.page):
                    continue
                
                if BoundingBoxCalculator.are_adjacent(elem1.bbox, elem2.bbox):
                    caption2_info = CaptionExtractor.find_for_element(
                        original_elements, elem2.index, elem2.page
                    )
                    
                    if caption2_info.text:
                        elem1.merge_with = elem2.index
                        break


class ElementPreprocessor:
    """Preprocesses elements to handle containment and adjacency rules (hybrid extractor)."""
    
    @dataclass
    class ProcessedElement:
        element: Element
        original_index: int
        should_skip: bool
        merge_with_index: Optional[int]
        
    def __init__(self, elements: List[Element]):
        self.elements = elements
        self.processed_elements: List[self.ProcessedElement] = []
        
    def preprocess(self) -> List[Tuple[Element, int, bool, Optional[int]]]:
        """Preprocess elements applying containment and adjacency rules."""
        elements_with_bounding_boxes = self._build_elements_with_bboxes()
        self._apply_containment_rules(elements_with_bounding_boxes)
        self._apply_adjacency_rules(elements_with_bounding_boxes)
        
        return [(elem.element, elem.original_index, elem.should_skip, elem.merge_with_index) 
                for elem in self.processed_elements]
    
    def _build_elements_with_bboxes(self) -> List[Dict]:
        """Build list of visual elements with bounding boxes."""
        elements_with_bboxes = []
        
        for index, element in enumerate(self.elements):
            if not self._is_visual_element(element):
                continue
            
            bounding_box = BoundingBoxOperations.create_from_element(element)
            if not bounding_box:
                continue
            
            page_number = self._get_page_number(element)
            
            element_info = {
                'element': element,
                'index': index,
                'bounding_box': bounding_box,
                'page': page_number,
                'skip': False,
                'merge_with': None
            }
            elements_with_bboxes.append(element_info)
            
            self.processed_elements.append(self.ProcessedElement(
                element=element,
                original_index=index,
                should_skip=False,
                merge_with_index=None
            ))
        
        return elements_with_bboxes
    
    def _is_visual_element(self, element: Element) -> bool:
        """Check if element is a visual element (Image or Table)."""
        return (isinstance(element, (UnstructuredImage, Table)) or 
                (hasattr(element, 'category') and element.category in ['Image', 'Figure']))
    
    def _get_page_number(self, element: Element) -> int:
        """Extract page number from element metadata."""
        if (hasattr(element, 'metadata') and hasattr(element.metadata, 'page_number') 
            and element.metadata.page_number):
            return element.metadata.page_number
        return 1
    
    def _apply_containment_rules(self, elements_with_bboxes: List[Dict]) -> None:
        """Apply rules for contained elements and same-caption duplicates."""
        for i, first_element in enumerate(elements_with_bboxes):
            if first_element['skip']:
                continue
            
            first_caption = self._get_element_caption(first_element)
            
            for j, second_element in enumerate(elements_with_bboxes):
                if i == j or second_element['skip']:
                    continue
                
                if first_element['page'] != second_element['page']:
                    continue
                
                if self._should_skip_contained_element(first_element, second_element):
                    first_element['skip'] = True
                    self.processed_elements[i].should_skip = True
                    break
                
                if self._should_skip_duplicate_caption(first_element, second_element, first_caption):
                    first_element['skip'] = True
                    self.processed_elements[i].should_skip = True
                    break
    
    def _get_element_caption(self, element_info: Dict) -> Optional[str]:
        """Get caption for an element."""
        caption, _, _, _ = CaptionDetector.find_caption_and_description(
            self.elements, element_info['index'], element_info['page']
        )
        return caption
    
    def _should_skip_contained_element(self, first: Dict, second: Dict) -> bool:
        """Check if first element should be skipped because it's contained in second."""
        return BoundingBoxOperations.is_contained_within(first['bounding_box'], second['bounding_box'])
    
    def _should_skip_duplicate_caption(self, first: Dict, second: Dict, first_caption: Optional[str]) -> bool:
        """Check if first element should be skipped due to duplicate caption."""
        if not first_caption:
            return False
        
        second_caption = self._get_element_caption(second)
        if not second_caption or first_caption != second_caption:
            return False
        
        first_area = first['bounding_box'].area
        second_area = second['bounding_box'].area
        
        return first_area < second_area
    
    def _apply_adjacency_rules(self, elements_with_bboxes: List[Dict]) -> None:
        """Apply rules for merging adjacent elements when one lacks caption."""
        for i, first_element in enumerate(elements_with_bboxes):
            if first_element['skip'] or first_element['merge_with'] is not None:
                continue
            
            first_caption = self._get_element_caption(first_element)
            
            if first_caption:  # Only merge elements without captions
                continue
            
            merge_target = self._find_adjacent_element_with_caption(first_element, elements_with_bboxes)
            if merge_target:
                first_element['merge_with'] = merge_target['index']
                self.processed_elements[i].merge_with_index = merge_target['index']
    
    def _find_adjacent_element_with_caption(self, target_element: Dict, all_elements: List[Dict]) -> Optional[Dict]:
        """Find adjacent element with caption for merging."""
        for candidate in all_elements:
            if (candidate['skip'] or candidate['merge_with'] is not None or
                candidate['page'] != target_element['page']):
                continue
            
            if not BoundingBoxOperations.are_adjacent(target_element['bounding_box'], candidate['bounding_box']):
                continue
            
            candidate_caption = self._get_element_caption(candidate)
            if candidate_caption:
                return candidate
        
        return None