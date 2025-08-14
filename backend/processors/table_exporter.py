"""
Table data export utilities for PDF processing.
Handles exporting table data to CSV and text formats.
"""

from typing import Optional
from io import StringIO
import pandas as pd
from unstructured.documents.elements import Table


class TableDataExporter:
    """Exports table data to various formats."""
    
    @staticmethod
    def save_as_csv(element: Table, filepath: str) -> bool:
        """
        Save table element as CSV file.
        
        Args:
            element: Table element to export
            filepath: Path to save CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if TableDataExporter._has_html_content(element):
                return TableDataExporter._save_html_table(element, filepath)
            else:
                return TableDataExporter._save_text_content(element, filepath)
        except Exception:
            return False
    
    @staticmethod
    def _has_html_content(element: Table) -> bool:
        """Check if table element has HTML content."""
        return (hasattr(element, 'metadata') and 
                hasattr(element.metadata, 'text_as_html'))
    
    @staticmethod
    def _save_html_table(element: Table, filepath: str) -> bool:
        """Save table with HTML content as CSV."""
        html_content = element.metadata.text_as_html
        tables = pd.read_html(StringIO(html_content))
        if tables:
            tables[0].to_csv(filepath, index=False)
            return True
        return False
    
    @staticmethod
    def _save_text_content(element: Table, filepath: str) -> bool:
        """Save table text content as text file."""
        text_filepath = filepath.replace('.csv', '.txt')
        with open(text_filepath, 'w', encoding='utf-8') as f:
            f.write(str(element))
        return True


class TableDataSaver:
    """Alternative implementation for saving table data (used by hybrid extractor)."""
    
    def __init__(self, default_format: str = 'csv'):
        self.default_format = default_format
    
    def save(self, table: Table, output_path: str) -> bool:
        """
        Save table to file.
        
        Args:
            table: Table element to save
            output_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        return TableDataExporter.save_as_csv(table, output_path)
    
    @staticmethod
    def save_table_as_csv(table_element: Table, file_path: str) -> bool:
        """Save table content as CSV or text file (hybrid extractor compatibility)."""
        return TableDataExporter.save_as_csv(table_element, file_path)
    
    def export_to_dataframe(self, table: Table) -> Optional[pd.DataFrame]:
        """
        Convert table to pandas DataFrame.
        
        Args:
            table: Table element to convert
            
        Returns:
            DataFrame if successful, None otherwise
        """
        try:
            if hasattr(table, 'metadata') and hasattr(table.metadata, 'text_as_html'):
                html_content = table.metadata.text_as_html
                tables = pd.read_html(StringIO(html_content))
                if tables:
                    return tables[0]
        except Exception:
            pass
        return None