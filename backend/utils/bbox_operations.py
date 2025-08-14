"""
Bounding box utilities for PDF extraction.
Contains operations for bounding box manipulation, comparison, and extraction.
"""

from typing import Optional, List
from core.pdf_extraction_models import BoundingBox, BoundingBoxLegacy
from core.pdf_extraction_config import PDFConstants


class BoundingBoxOperations:
    """Utility class for bounding box operations."""
    
    @staticmethod
    def create_from_element(element, scale_to_hires: bool = False) -> Optional[BoundingBox]:
        """Extract bounding box from element metadata.
        
        Args:
            element: Element with metadata containing coordinates
            scale_to_hires: If True, scale fast mode coordinates to hi-res (multiply by 2.78)
        """
        if not hasattr(element, 'metadata') or not hasattr(element.metadata, 'coordinates'):
            return None
        
        coordinates = element.metadata.coordinates
        if not coordinates or not hasattr(coordinates, 'points'):
            return None
        
        points = coordinates.points
        if not points or len(points) < 2:
            return None
        
        x_coordinates = [point[0] for point in points]
        y_coordinates = [point[1] for point in points]
        
        # Apply scaling if requested (for fast mode -> hi-res conversion)
        if scale_to_hires:
            scale_factor = 2.78  # Fast mode to hi-res scaling
            x_coordinates = [x * scale_factor for x in x_coordinates]
            y_coordinates = [y * scale_factor for y in y_coordinates]
        
        return BoundingBox(
            x_min=min(x_coordinates),
            y_min=min(y_coordinates),
            x_max=max(x_coordinates),
            y_max=max(y_coordinates)
        )
    
    @staticmethod
    def merge(first: BoundingBox, second: BoundingBox) -> BoundingBox:
        """Merge two bounding boxes into one containing both."""
        return BoundingBox(
            x_min=min(first.x_min, second.x_min),
            y_min=min(first.y_min, second.y_min),
            x_max=max(first.x_max, second.x_max),
            y_max=max(first.y_max, second.y_max)
        )
    
    @staticmethod
    def is_contained_within(inner: BoundingBox, outer: BoundingBox, 
                          tolerance: float = PDFConstants.BBOX_TOLERANCE) -> bool:
        """Check if inner bounding box is contained within outer box."""
        return (inner.x_min >= outer.x_min - tolerance and
                inner.y_min >= outer.y_min - tolerance and
                inner.x_max <= outer.x_max + tolerance and
                inner.y_max <= outer.y_max + tolerance)
    
    @staticmethod
    def are_adjacent(first: BoundingBox, second: BoundingBox, 
                    max_gap: float = PDFConstants.MAX_ADJACENCY_GAP) -> bool:
        """Check if two bounding boxes are adjacent within max_gap distance."""
        vertical_gap = min(abs(first.y_min - second.y_max), abs(second.y_min - first.y_max))
        horizontal_gap = min(abs(first.x_min - second.x_max), abs(second.x_min - first.x_max))
        
        has_horizontal_overlap = not (first.x_max < second.x_min or second.x_max < first.x_min)
        has_vertical_overlap = not (first.y_max < second.y_min or second.y_max < first.y_min)
        
        return ((vertical_gap <= max_gap and has_horizontal_overlap) or 
                (horizontal_gap <= max_gap and has_vertical_overlap))


class BoundingBoxCalculator:
    """Calculator for bounding box operations (legacy naming for extract_all_elements.py)."""
    
    @staticmethod
    def extract_from_element(element) -> Optional[BoundingBoxLegacy]:
        """Extract bounding box from element metadata using legacy format."""
        if not (hasattr(element, 'metadata') and 
                hasattr(element.metadata, 'coordinates')):
            return None
        
        coords = element.metadata.coordinates
        if not (coords and hasattr(coords, 'points')):
            return None
        
        points = coords.points
        if not (points and len(points) >= 2):
            return None
        
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        return BoundingBoxLegacy(
            x0=min(x_coords),
            y0=min(y_coords), 
            x1=max(x_coords),
            y1=max(y_coords)
        )
    
    @staticmethod
    def merge(bbox1: BoundingBoxLegacy, bbox2: BoundingBoxLegacy) -> BoundingBoxLegacy:
        """Merge two legacy bounding boxes."""
        return BoundingBoxLegacy(
            x0=min(bbox1.x0, bbox2.x0),
            y0=min(bbox1.y0, bbox2.y0),
            x1=max(bbox1.x1, bbox2.x1),
            y1=max(bbox1.y1, bbox2.y1)
        )
    
    @staticmethod
    def is_contained(inner: BoundingBoxLegacy, outer: BoundingBoxLegacy) -> bool:
        """Check if inner is contained within outer (legacy version)."""
        return (inner.x0 >= outer.x0 - PDFConstants.CONTAINMENT_TOLERANCE and
                inner.y0 >= outer.y0 - PDFConstants.CONTAINMENT_TOLERANCE and
                inner.x1 <= outer.x1 + PDFConstants.CONTAINMENT_TOLERANCE and
                inner.y1 <= outer.y1 + PDFConstants.CONTAINMENT_TOLERANCE)
    
    @staticmethod
    def are_adjacent(bbox1: BoundingBoxLegacy, bbox2: BoundingBoxLegacy) -> bool:
        """Check if two bounding boxes are adjacent (legacy version)."""
        vertical_gap = min(abs(bbox1.y0 - bbox2.y1), abs(bbox2.y0 - bbox1.y1))
        horizontal_gap = min(abs(bbox1.x0 - bbox2.x1), abs(bbox2.x0 - bbox1.x1))
        
        x_overlap = not (bbox1.x1 < bbox2.x0 or bbox2.x1 < bbox1.x0)
        y_overlap = not (bbox1.y1 < bbox2.y0 or bbox2.y1 < bbox1.y0)
        
        return ((vertical_gap <= PDFConstants.ADJACENCY_THRESHOLD and x_overlap) or 
                (horizontal_gap <= PDFConstants.ADJACENCY_THRESHOLD and y_overlap))