import React, { useRef, useEffect } from 'react';
import { PDFDocument, PDFViewer } from '@/types/pdf';
import { API_ENDPOINTS } from '@/config/environment';

interface SimplePDFContentProps {
  documentId: string;
  onPdfViewerRef?: (viewer: PDFViewer | null) => void;
  onPdfDocumentRef: (document: PDFDocument | null) => void;
}

export default function SimplePDFContent({
  documentId,
  onPdfViewerRef,
  onPdfDocumentRef
}: SimplePDFContentProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const pdfUrl = API_ENDPOINTS.getPdf(documentId);

  useEffect(() => {
    // For now, just use an iframe to display the PDF
    // This is simpler and doesn't include highlighting
    if (containerRef.current) {
      containerRef.current.innerHTML = `
        <iframe 
          src="${pdfUrl}" 
          width="100%" 
          height="100%" 
          style="border: none;"
          title="PDF Document"
        />
      `;
    }

    // Since we're using iframe, we don't have direct access to viewer/document
    // But we can still notify parent components
    if (onPdfViewerRef) {
      onPdfViewerRef(null);
    }
    if (onPdfDocumentRef) {
      onPdfDocumentRef(null);
    }
  }, [documentId, pdfUrl, onPdfViewerRef, onPdfDocumentRef]);

  return (
    <div 
      ref={containerRef} 
      style={{ width: '100%', height: '100%' }}
      className="pdf-content-container"
    />
  );
}