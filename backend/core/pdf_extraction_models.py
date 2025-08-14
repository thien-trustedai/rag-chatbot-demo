"""
Data models and structures for PDF extraction system.
Contains dataclasses and helper structures used across the extraction pipeline.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List, Any


@dataclass
class BoundingBox:
    """Represents a bounding box with coordinates and computed properties."""
    
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    
    @property
    def width(self) -> float:
        """Calculate width of the bounding box."""
        return self.x_max - self.x_min
    
    @property
    def height(self) -> float:
        """Calculate height of the bounding box."""
        return self.y_max - self.y_min
    
    @property
    def area(self) -> float:
        """Calculate area of the bounding box."""
        return self.width * self.height
    
    def to_dict(self) -> Dict[str, float]:
        """Convert bounding box to dictionary format."""
        return {
            "x0": round(self.x_min, 2),
            "y0": round(self.y_min, 2),
            "x1": round(self.x_max, 2),
            "y1": round(self.y_max, 2),
            "width": round(self.width, 2),
            "height": round(self.height, 2)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'BoundingBox':
        """Create BoundingBox from dictionary with x0, y0, x1, y1 format."""
        return cls(
            x_min=data.get('x0', 0),
            y_min=data.get('y0', 0),
            x_max=data.get('x1', 0),
            y_max=data.get('y1', 0)
        )


# Alternative naming for backward compatibility
@dataclass  
class BoundingBoxLegacy:
    """Legacy BoundingBox with different property names."""
    
    x0: float
    y0: float
    x1: float
    y1: float
    
    @property
    def width(self) -> float:
        return self.x1 - self.x0
    
    @property
    def height(self) -> float:
        return self.y1 - self.y0
    
    @property
    def area(self) -> float:
        return self.width * self.height
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "x0": round(self.x0, 2),
            "y0": round(self.y0, 2),
            "x1": round(self.x1, 2),
            "y1": round(self.y1, 2),
            "width": round(self.width, 2),
            "height": round(self.height, 2)
        }
    
    def to_standard(self) -> BoundingBox:
        """Convert to standard BoundingBox format."""
        return BoundingBox(
            x_min=self.x0,
            y_min=self.y0,
            x_max=self.x1,
            y_max=self.y1
        )


@dataclass
class ElementMetadata:
    """Metadata for extracted visual elements (figures/tables)."""
    
    filename: str
    source_pdf: str
    page_number: int
    index: int
    caption: Optional[str]
    description: Optional[str]
    bounding_box: Optional[BoundingBox]
    original_type: str
    is_reclassified: bool
    element_id: Optional[str]


@dataclass
class TextElement:
    """Represents a text element extracted from PDF."""
    
    element_type: str
    text: str
    page: int
    bounding_box: Optional[BoundingBox]
    detection_probability: Optional[float] = None
    original_type: Optional[str] = None


@dataclass
class PageExtractionTask:
    """Represents a single page extraction task for parallel processing."""
    
    pdf_path: str
    page_number: int
    output_dir: str
    dpi: int
    original_pdf_name: str


@dataclass
class CaptionInfo:
    """Information about element captions and descriptions."""
    
    text: Optional[str]
    description: Optional[str]
    bbox: Optional[BoundingBox]
    caption_type: str


@dataclass
class ElementInfo:
    """Information about a visual element for processing."""
    
    element: Any  # Element type from unstructured
    index: int
    bbox: Optional[BoundingBox]
    page: int
    skip: bool = False
    merge_with: Optional[int] = None