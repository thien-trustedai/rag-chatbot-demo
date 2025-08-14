'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { PDFHighlightPosition } from '@/types/pdf';
import { useDocumentInfo } from '@/hooks/useDocumentInfo';
import { usePageNavigation } from '@/hooks/usePageNavigation';
import { useHighlightManagement } from '@/hooks/useHighlightManagement';

const PDFContent = dynamic(() => import('./pdf/PDFContent'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading PDF viewer...</p>
      </div>
    </div>
  ),
});

interface PDFViewerProps {
  documentId: string;
  selectedPage: number;
  highlightPosition?: PDFHighlightPosition;
}

export default function PDFViewer({ documentId, selectedPage, highlightPosition }: PDFViewerProps) {
  const { documentInfo, isLoading } = useDocumentInfo(documentId);
  const { pdfViewer, scrollToHighlight } = usePageNavigation(selectedPage);
  const {
    highlights,
    pdfDocument,
    resetHighlights,
    addHighlight
  } = useHighlightManagement(highlightPosition, selectedPage, scrollToHighlight);

  if (!documentId) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-100">
        <p className="text-gray-500">No document selected</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-100">
      <div className="flex-1 overflow-hidden" style={{ position: 'relative' }}>
        {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading PDF...</p>
              </div>
            </div>
          ) : (
            <PDFContent
              documentId={documentId}
              highlights={highlights}
              onAddHighlight={addHighlight}
              onPdfViewerRef={(viewer) => { pdfViewer.current = viewer; }}
              onPdfDocumentRef={(document) => { pdfDocument.current = document; }}
              onScrollRef={(scrollTo) => { 
                scrollToHighlight.current = scrollTo; 
              }}
            />
          )}
      </div>
    </div>
  );
}