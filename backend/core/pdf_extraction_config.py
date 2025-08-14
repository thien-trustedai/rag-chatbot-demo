"""
Configuration module for PDF extraction system.
Contains all constants and configuration values used across the extraction pipeline.
"""

from enum import Enum


class ExtractionStrategy(Enum):
    """PDF extraction strategies."""
    HIGH_RESOLUTION = "hi_res"
    FAST = "fast"


class ElementType(Enum):
    """Types of elements that can be extracted from PDFs."""
    FIGURE = "figure"
    TABLE = "table"
    UNKNOWN = "unknown"


class PDFConstants:
    """Constants for PDF processing and extraction."""
    
    # Coordinate scaling factors
    UNSTRUCTURED_TO_PYMUPDF_SCALE = 0.36  # Scale from Unstructured to PyMuPDF coordinates
    HIGH_RES_TO_FAST_SCALE = 1.0 / 2.78  # Scale from high-res to fast mode coordinates
    COORDINATE_SCALE_FACTOR = 0.36  # Legacy alias for UNSTRUCTURED_TO_PYMUPDF_SCALE
    
    # DPI settings
    DEFAULT_DPI = 150
    HIGH_DPI = 300  # Used in extract_all_elements.py as default
    
    # Size thresholds for figures
    MIN_FIGURE_WIDTH = 100
    MIN_FIGURE_HEIGHT = 100
    MIN_FIGURE_AREA = 20000
    
    # Search and proximity parameters
    CAPTION_SEARCH_RANGE = 5  # Number of elements to search before/after for captions
    BBOX_TOLERANCE = 5.0  # Tolerance for bounding box containment checks
    MAX_ADJACENCY_GAP = 100.0  # Maximum gap for elements to be considered adjacent
    ADJACENCY_THRESHOLD = 100.0  # Legacy alias for MAX_ADJACENCY_GAP
    CONTAINMENT_TOLERANCE = 5.0  # Legacy alias for BBOX_TOLERANCE


class CaptionKeywords:
    """Keywords used for caption detection and classification."""
    
    FIGURE_KEYWORDS = ['図', 'Figure', 'Fig.', 'Image', 'Diagram']
    TABLE_KEYWORDS = ['table', '表', 'テーブル', 'tab.', 'tbl']
    DESCRIPTION_KEYWORDS = ['図', 'Figure', 'table', '表', 'Table']
    
    # Additional keywords for classification
    PANEL_KEYWORDS = ['panel', 'パネル', 'diagram', '図', 'Figure']


class FileExtensions:
    """File extensions used in the system."""
    
    PNG = '.png'
    CSV = '.csv'
    TXT = '.txt'
    JSON = '.json'
    MD = '.md'
    PDF = '.pdf'


class DirectoryNames:
    """Standard directory names for output organization."""
    
    FIGURES = 'figures'
    TABLES = 'tables'
    OUTPUT = 'output'
    BASELINE_OUTPUT = 'baseline_output'
    PARALLEL_EXTRACTION = 'parallel_extraction'
    HYBRID_EXTRACTION = 'hybrid_extraction'
    EXTRACTED_ELEMENTS = 'extracted_elements'