"""
Production-ready PDF element extraction module.
Handles figures and tables with smart classification and merging.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import (
    Element, 
    Image as UnstructuredImage,
    Table,
    FigureCaption,
    Text,
    Title,
    NarrativeText
)

# Import constants from centralized config
from core.pdf_extraction_config import PDFConstants, CaptionKeywords, FileExtensions, DirectoryNames
# Import models - use legacy BoundingBox for backward compatibility
from core.pdf_extraction_models import BoundingBoxLegacy as BoundingBox, CaptionInfo, ElementInfo
# Import utilities
from utils.bbox_operations import BoundingBoxCalculator
from utils.caption_detector import CaptionExtractor
from classifiers.element_classifier_simple import ElementClassifier
from processors.element_preprocessor import ElementProcessor
from processors.image_extractor import ImageExtractor
from processors.table_exporter import TableDataExporter

# Keep local aliases for backward compatibility
COORDINATE_SCALE_FACTOR = PDFConstants.COORDINATE_SCALE_FACTOR
MIN_FIGURE_WIDTH = PDFConstants.MIN_FIGURE_WIDTH
MIN_FIGURE_HEIGHT = PDFConstants.MIN_FIGURE_HEIGHT
MIN_FIGURE_AREA = PDFConstants.MIN_FIGURE_AREA
DEFAULT_DPI = PDFConstants.HIGH_DPI  # Note: extract_all_elements uses 300 DPI by default
CAPTION_SEARCH_RANGE = PDFConstants.CAPTION_SEARCH_RANGE
ADJACENCY_THRESHOLD = PDFConstants.ADJACENCY_THRESHOLD
CONTAINMENT_TOLERANCE = PDFConstants.CONTAINMENT_TOLERANCE


# BoundingBoxCalculator is now imported from pdf_bbox_utils
# CaptionExtractor is now imported from pdf_caption_utils
# ElementClassifier is now imported from pdf_element_classifier
# ElementProcessor is now imported from pdf_element_processor
# ImageExtractor is now imported from pdf_image_extractor
# TableDataExporter is now imported from pdf_table_exporter


class PDFElementExtractor:
    
    def __init__(self, output_dir: str = "extracted_elements", dpi: int = DEFAULT_DPI):
        self.output_dir = output_dir
        self.dpi = dpi
        self.figures_dir = os.path.join(output_dir, "figures")
        self.tables_dir = os.path.join(output_dir, "tables")
        self._create_directories()
    
    def _create_directories(self) -> None:
        os.makedirs(self.figures_dir, exist_ok=True)
        os.makedirs(self.tables_dir, exist_ok=True)
    
    def extract(self, pdf_path: str, strategy: str = "hi_res") -> Dict[str, List[Dict[str, Any]]]:
        pdf_name = Path(pdf_path).stem
        
        elements = partition_pdf(
            filename=pdf_path,
            strategy=strategy,
            extract_images_in_pdf=True,
            extract_image_block_types=["Table", "Image", "Figure", "FigureCaption"],
            extract_image_block_to_payload=True,
            include_page_breaks=True,
            include_metadata=True,
            infer_table_structure=True
        )
        
        preprocessed_elements = ElementProcessor.preprocess_elements(elements)
        
        visual_metadata = self._process_elements(
            elements, preprocessed_elements, pdf_name, pdf_path
        )
        
        text_metadata = self._extract_text_elements(elements)
        
        return {
            "figures": visual_metadata.get("figures", []),
            "tables": visual_metadata.get("tables", []),
            "text_blocks": text_metadata
        }
    
    def _process_elements(self, original_elements: List[Element],
                         preprocessed: List[ElementInfo], pdf_name: str,
                         pdf_path: str) -> Dict[str, List[Dict[str, Any]]]:
        figures_metadata = []
        tables_metadata = []
        figure_counter = 0
        table_counter = 0
        merged_indices = set()
        
        for elem_info in preprocessed:
            if elem_info.skip or elem_info.index in merged_indices:
                continue
            
            element, bbox = self._resolve_merge(
                elem_info, preprocessed, merged_indices
            )
            
            classification = ElementClassifier.classify(
                element, original_elements, elem_info.index, elem_info.page
            )
            
            if classification == 'figure':
                figure_counter += 1
                metadata = self._process_figure(
                    element, bbox, elem_info.page, figure_counter,
                    pdf_name, pdf_path, original_elements, elem_info.index
                )
                if metadata:
                    figures_metadata.append(metadata)
            
            elif classification == 'table':
                table_counter += 1
                metadata = self._process_table(
                    element, bbox, elem_info.page, table_counter,
                    pdf_name, pdf_path, original_elements, elem_info.index
                )
                if metadata:
                    tables_metadata.append(metadata)
        
        return {"figures": figures_metadata, "tables": tables_metadata}
    
    def _extract_text_elements(self, elements: List[Element]) -> List[Dict[str, Any]]:
        """Extract text elements organized by blocks."""
        from unstructured.documents.elements import (
            Header, Footer, PageBreak, ListItem, NarrativeText
        )
        
        text_blocks = []
        current_block = None
        block_counter = 0
        
        for idx, element in enumerate(elements):
            if isinstance(element, (UnstructuredImage, Table, FigureCaption)):
                continue
            
            if isinstance(element, PageBreak):
                if current_block and current_block["content"].strip():
                    text_blocks.append(current_block)
                current_block = None
                continue
            
            if isinstance(element, (Header, Footer)):
                continue
            
            page_num = self._get_element_page(element)
            elem_type = self._classify_text_element(element)
            elem_text = str(element).strip()
            
            if not elem_text:
                continue
            
            if elem_type in ["heading", "title"]:
                if current_block and current_block["content"].strip():
                    text_blocks.append(current_block)
                
                block_counter += 1
                current_block = {
                    "type": "section",
                    "block_index": block_counter,
                    "page": page_num,
                    "heading": elem_text,
                    "heading_level": self._get_heading_level(element),
                    "content": "",
                    "elements": [],
                    "bounding_box": BoundingBoxCalculator.extract_from_element(element)
                }
            elif current_block:
                current_block["content"] += "\n\n" + elem_text if current_block["content"] else elem_text
                current_block["elements"].append({
                    "type": elem_type,
                    "text": elem_text,
                    "index": idx
                })
                
                elem_bbox = BoundingBoxCalculator.extract_from_element(element)
                if elem_bbox and current_block.get("bounding_box"):
                    current_block["bounding_box"] = BoundingBoxCalculator.merge(
                        current_block["bounding_box"], elem_bbox
                    )
            else:
                block_counter += 1
                current_block = {
                    "type": "paragraph",
                    "block_index": block_counter,
                    "page": page_num,
                    "heading": None,
                    "content": elem_text,
                    "elements": [{
                        "type": elem_type,
                        "text": elem_text,
                        "index": idx
                    }],
                    "bounding_box": BoundingBoxCalculator.extract_from_element(element)
                }
        
        if current_block and current_block["content"].strip():
            text_blocks.append(current_block)
        
        for block in text_blocks:
            if block.get("bounding_box"):
                block["bounding_box"] = block["bounding_box"].to_dict()
        
        return text_blocks
    
    def _get_element_page(self, element: Element) -> int:
        """Get page number for an element."""
        if (hasattr(element, 'metadata') and 
            hasattr(element.metadata, 'page_number') and
            element.metadata.page_number):
            return element.metadata.page_number
        return 1
    
    def _classify_text_element(self, element: Element) -> str:
        """Classify the type of text element."""
        from unstructured.documents.elements import (
            ListItem, Header, Footer
        )
        
        if isinstance(element, Title):
            return "title"
        elif isinstance(element, Header):
            return "header"
        elif isinstance(element, Footer):
            return "footer"
        elif isinstance(element, ListItem):
            return "list_item"
        elif isinstance(element, NarrativeText):
            return "paragraph"
        elif isinstance(element, Text):
            text = str(element).strip()
            if self._is_heading_text(text):
                return "heading"
            return "text"
        else:
            return "unknown"
    
    def _is_heading_text(self, text: str) -> bool:
        """Check if text appears to be a heading."""
        if len(text) > 100:
            return False
        
        heading_patterns = [
            r'^第\s*\d+\s*章',
            r'^Chapter\s+\d+',
            r'^Section\s+\d+',
            r'^\d+\.\s+[A-Z]',
            r'^[A-Z][^.!?]*$'
        ]
        
        import re
        for pattern in heading_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def _get_heading_level(self, element: Element) -> int:
        """Determine the heading level."""
        text = str(element).strip()
        
        import re
        if re.match(r'^第\s*\d+\s*章|^Chapter\s+\d+', text):
            return 1
        elif re.match(r'^\d+\.\s+', text):
            return 2
        elif isinstance(element, Title):
            if hasattr(element, 'metadata') and hasattr(element.metadata, 'category_depth'):
                return element.metadata.category_depth
            return 2
        else:
            return 3
    
    def _resolve_merge(self, elem_info: ElementInfo,
                      preprocessed: List[ElementInfo],
                      merged_indices: set) -> Tuple[Element, Optional[BoundingBox]]:
        if elem_info.merge_with is None:
            return elem_info.element, elem_info.bbox
        
        merge_elem_info = next(
            (e for e in preprocessed if e.index == elem_info.merge_with), None
        )
        
        if merge_elem_info:
            merged_indices.update([elem_info.index, elem_info.merge_with])
            merged_bbox = BoundingBoxCalculator.merge(
                elem_info.bbox, merge_elem_info.bbox
            )
            return merge_elem_info.element, merged_bbox
        
        return elem_info.element, elem_info.bbox
    
    def _process_figure(self, element: Element, bbox: Optional[BoundingBox],
                       page: int, counter: int, pdf_name: str, pdf_path: str,
                       original_elements: List[Element], 
                       element_index: int) -> Optional[Dict[str, Any]]:
        if not self._is_valid_figure_size(bbox):
            return None
        
        caption_info = CaptionExtractor.find_for_element(
            original_elements, element_index, page
        )
        
        final_bbox = self._merge_with_caption_bbox(bbox, caption_info.bbox)
        filename = f"fig{counter}.png"
        filepath = os.path.join(self.figures_dir, filename)
        
        if not ImageExtractor.extract_from_pdf(
            pdf_path, final_bbox, page, filepath, self.dpi
        ):
            return None
        
        return {
            "filename": filename,
            "source_pdf": pdf_name,
            "page_number": page,
            "figure_index": counter,
            "caption": caption_info.text,
            "description": caption_info.description,
            "bounding_box": final_bbox.to_dict(),
            "original_type": type(element).__name__,
            "reclassified": type(element).__name__ == 'Table',
            "element_id": getattr(element, 'id', None)
        }
    
    def _process_table(self, element: Element, bbox: Optional[BoundingBox],
                      page: int, counter: int, pdf_name: str, pdf_path: str,
                      original_elements: List[Element],
                      element_index: int) -> Optional[Dict[str, Any]]:
        caption_info = CaptionExtractor.find_for_element(
            original_elements, element_index, page
        )
        
        saved_files = []
        
        if isinstance(element, Table):
            csv_filename = f"table{counter}.csv"
            csv_path = os.path.join(self.tables_dir, csv_filename)
            if TableDataExporter.save_as_csv(element, csv_path):
                saved_files.append(csv_filename)
        
        if bbox:
            final_bbox = self._merge_with_caption_bbox(bbox, caption_info.bbox)
            img_filename = f"table{counter}.png"
            img_filepath = os.path.join(self.tables_dir, img_filename)
            
            if ImageExtractor.extract_from_pdf(
                pdf_path, final_bbox, page, img_filepath, self.dpi
            ):
                saved_files.append(img_filename)
        
        return {
            "files": saved_files,
            "source_pdf": pdf_name,
            "page_number": page,
            "table_index": counter,
            "caption": caption_info.text,
            "description": caption_info.description,
            "content": str(element)[:500] if isinstance(element, Table) else None,
            "bounding_box": final_bbox.to_dict() if bbox else None,
            "original_type": type(element).__name__,
            "reclassified": type(element).__name__ == 'Image',
            "element_id": getattr(element, 'id', None)
        }
    
    def _is_valid_figure_size(self, bbox: Optional[BoundingBox]) -> bool:
        if not bbox:
            return False
        return not ((bbox.width < MIN_FIGURE_WIDTH and 
                    bbox.height < MIN_FIGURE_HEIGHT) or
                   bbox.area < MIN_FIGURE_AREA)
    
    def _merge_with_caption_bbox(self, bbox: Optional[BoundingBox],
                                caption_bbox: Optional[BoundingBox]
                                ) -> Optional[BoundingBox]:
        if bbox and caption_bbox:
            return BoundingBoxCalculator.merge(bbox, caption_bbox)
        return bbox


class MetadataManager:
    
    @staticmethod
    def save(metadata: Dict[str, List[Dict[str, Any]]], output_dir: str) -> None:
        MetadataManager._save_figures_metadata(metadata["figures"], output_dir)
        MetadataManager._save_tables_metadata(metadata["tables"], output_dir)
        MetadataManager._save_combined_metadata(metadata, output_dir)
    
    @staticmethod
    def _save_figures_metadata(figures: List[Dict[str, Any]], output_dir: str) -> None:
        if not figures:
            return
        
        figures_json = os.path.join(output_dir, "figures", "metadata.json")
        with open(figures_json, 'w', encoding='utf-8') as f:
            json.dump(figures, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def _save_tables_metadata(tables: List[Dict[str, Any]], output_dir: str) -> None:
        if not tables:
            return
        
        tables_json = os.path.join(output_dir, "tables", "metadata.json")
        with open(tables_json, 'w', encoding='utf-8') as f:
            json.dump(tables, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def _save_combined_metadata(metadata: Dict[str, List[Dict[str, Any]]], output_dir: str) -> None:
        """Save combined metadata with markdown structure information."""
        combined_metadata = MetadataManager._build_combined_metadata(metadata)
        
        metadata_json = os.path.join(output_dir, "metadata.json")
        with open(metadata_json, 'w', encoding='utf-8') as f:
            json.dump(combined_metadata, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def _build_combined_metadata(metadata: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Build comprehensive metadata including markdown structure."""
        all_elements = []
        
        for text_block in metadata.get("text_blocks", []):
            element = {
                "type": "text_block",
                "block_type": text_block.get("type", "paragraph"),
                "page": text_block["page"],
                "index": text_block["block_index"],
                "heading": text_block.get("heading"),
                "heading_level": text_block.get("heading_level"),
                "content": text_block["content"],
                "bounding_box": text_block.get("bounding_box"),
                "element_count": len(text_block.get("elements", []))
            }
            all_elements.append(element)
        
        for figure in metadata.get("figures", []):
            element = {
                "type": "figure",
                "page": figure["page_number"],
                "index": figure["figure_index"],
                "caption": figure.get("caption"),
                "description": figure.get("description"),
                "filename": figure["filename"],
                "path": f"figures/{figure['filename']}",
                "bounding_box": figure.get("bounding_box"),
                "reclassified": figure.get("reclassified", False),
                "original_type": figure.get("original_type"),
                "markdown_reference": f"![{figure.get('caption', 'Figure ' + str(figure['figure_index']))}](figures/{figure['filename']})"
            }
            all_elements.append(element)
        
        for table in metadata.get("tables", []):
            element = {
                "type": "table",
                "page": table["page_number"],
                "index": table["table_index"],
                "caption": table.get("caption"),
                "description": table.get("description"),
                "files": table.get("files", []),
                "bounding_box": table.get("bounding_box"),
                "reclassified": table.get("reclassified", False),
                "original_type": table.get("original_type")
            }
            
            if any(f.endswith('.png') for f in table.get("files", [])):
                png_file = next(f for f in table["files"] if f.endswith('.png'))
                element["image_path"] = f"tables/{png_file}"
                element["markdown_reference"] = f"![{table.get('caption', 'Table ' + str(table['table_index']))}](tables/{png_file})"
            
            if any(f.endswith('.csv') for f in table.get("files", [])):
                csv_file = next(f for f in table["files"] if f.endswith('.csv'))
                element["data_path"] = f"tables/{csv_file}"
            
            all_elements.append(element)
        
        all_elements.sort(key=lambda x: (x["page"], x.get("bounding_box", {}).get("y0", 0)))
        
        pages_structure = {}
        for element in all_elements:
            page = element["page"]
            if page not in pages_structure:
                pages_structure[page] = []
            pages_structure[page].append(element)
        
        return {
            "extraction_info": {
                "total_figures": len(metadata.get("figures", [])),
                "total_tables": len(metadata.get("tables", [])),
                "total_text_blocks": len(metadata.get("text_blocks", [])),
                "total_elements": len(all_elements),
                "pages_with_elements": list(pages_structure.keys())
            },
            "elements": all_elements,
            "pages_structure": pages_structure,
            "markdown_structure": MetadataManager._generate_markdown_structure(all_elements)
        }
    
    @staticmethod
    def _generate_markdown_structure(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate markdown document structure."""
        structure = []
        current_page = None
        
        for element in elements:
            if element["page"] != current_page:
                current_page = element["page"]
                structure.append({
                    "type": "page_header",
                    "page": current_page,
                    "markdown": f"## Page {current_page}"
                })
            
            if element["type"] == "text_block":
                if element["block_type"] == "section":
                    heading_level = element.get("heading_level") or 2
                    heading_prefix = "#" * (heading_level + 1)
                    structure.append({
                        "type": "section",
                        "page": element["page"],
                        "index": element["index"],
                        "heading": element.get("heading"),
                        "markdown": f"{heading_prefix} {element.get('heading', '')}\n\n{element['content']}"
                    })
                else:
                    structure.append({
                        "type": "paragraph",
                        "page": element["page"],
                        "index": element["index"],
                        "markdown": element["content"]
                    })
            elif element["type"] == "figure":
                structure.append({
                    "type": "figure",
                    "page": element["page"],
                    "index": element["index"],
                    "caption": element.get("caption"),
                    "markdown": f"### 🖼️ Figure: {element.get('caption', 'Figure ' + str(element['index']))}\n\n{element['markdown_reference']}"
                })
            elif element["type"] == "table":
                caption = element.get("caption", f"Table {element['index']}")
                markdown = f"### 📋 Table: {caption}"
                
                if "markdown_reference" in element:
                    markdown += f"\n\n{element['markdown_reference']}"
                
                if "data_path" in element:
                    markdown += f"\n\n[📊 Download CSV]({element['data_path']})"
                
                structure.append({
                    "type": "table",
                    "page": element["page"],
                    "index": element["index"],
                    "caption": caption,
                    "markdown": markdown
                })
        
        return structure


def extract_all_elements(pdf_path: str, output_dir: str = "extracted_elements",
                        strategy: str = "hi_res", 
                        dpi: int = DEFAULT_DPI) -> Dict[str, List[Dict[str, Any]]]:
    extractor = PDFElementExtractor(output_dir, dpi)
    return extractor.extract(pdf_path, strategy)


def save_metadata(metadata: Dict[str, List[Dict[str, Any]]], output_dir: str) -> None:
    MetadataManager.save(metadata, output_dir)


def main() -> None:
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extract_all_elements.py <pdf_path> [output_dir] [dpi]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "extracted_elements"
    dpi = DEFAULT_DPI
    
    if len(sys.argv) > 3:
        try:
            dpi = int(sys.argv[3])
        except ValueError:
            print(f"Invalid DPI value: {sys.argv[3]}")
            sys.exit(1)
    
    metadata = extract_all_elements(pdf_path, output_dir, dpi=dpi)
    save_metadata(metadata, output_dir)


if __name__ == "__main__":
    main()