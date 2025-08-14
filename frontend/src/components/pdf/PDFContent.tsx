/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useRef, useEffect } from 'react';
import type { IHighlight, NewHighlight } from 'react-pdf-highlighter';
import { PDFDocument, PDFViewer } from '@/types/pdf';
import { API_ENDPOINTS } from '@/config/environment';

// Import components directly without dynamic import for now
import {
  PdfLoader,
  PdfHighlighter,
  Tip,
  Highlight,
  Popup,
} from 'react-pdf-highlighter';
import "react-pdf-highlighter/dist/style.css";

interface PDFContentProps {
  documentId: string;
  highlights: IHighlight[];
  onAddHighlight: (highlight: NewHighlight) => void;
  onPdfViewerRef?: (viewer: PDFViewer | null) => void;
  onPdfDocumentRef: (document: PDFDocument | null) => void;
  onScrollRef: (scrollTo: (highlight: IHighlight) => void) => void;
}

export default function PDFContent({
  documentId,
  highlights,
  onAddHighlight,
  onPdfViewerRef,
  onPdfDocumentRef,
  onScrollRef
}: PDFContentProps) {
  const pdfUrl = API_ENDPOINTS.getPdf(documentId);
  const highlighterRef = useRef<any>(null);
  const scrollToRef = useRef<((highlight: IHighlight) => void) | null>(null);
  const currentPdfDoc = useRef<any>(null);

  // Clean up PDF document when component unmounts or document changes
  useEffect(() => {
    return () => {
      if (currentPdfDoc.current && !currentPdfDoc.current.destroyed) {
        if (process.env.NODE_ENV === 'development') {
          console.log('Cleaning up PDF document:', documentId);
        }
        try {
          currentPdfDoc.current.destroy();
        } catch (error) {
          console.error('Error destroying PDF document:', error);
        }
      }
    };
  }, [documentId]);

  // Set up the ref callback when the highlighter is mounted
  useEffect(() => {
    if (highlighterRef.current && onPdfViewerRef) {
      // Try different ways to access the viewer
      const highlighter = highlighterRef.current;
      
      // Check for viewer in different locations
      const viewer = highlighter.viewer || 
                    highlighter._viewer || 
                    highlighter.pdfViewer ||
                    highlighter._pdfViewer ||
                    (highlighter.props && highlighter.props.pdfViewer);
      
      if (viewer) {
        onPdfViewerRef(viewer);
      } else {
        // If no viewer found, pass the highlighter itself
        // as it might have navigation methods
        onPdfViewerRef(highlighter);
      }
    }
  }, [onPdfViewerRef]);


  return (
    <div style={{ height: '100%', width: '100%', position: 'relative' }}>
      <PdfLoader 
        key={documentId}  // Force re-render when document changes
        url={pdfUrl}
        beforeLoad={<div>Loading PDF...</div>}
      >
        {(pdfDocument: any) => {
          if (pdfDocument && !pdfDocument.destroyed) {
            // Log document details for debugging (only in development)
            if (process.env.NODE_ENV === 'development') {
              console.log('PDF Document loaded:', {
                documentId,
                numPages: pdfDocument.numPages,
                fingerprint: pdfDocument.fingerprint
              });
            }
            currentPdfDoc.current = pdfDocument;
            onPdfDocumentRef(pdfDocument);
          }
          
          return (
            <PdfHighlighter
              ref={highlighterRef}
              pdfDocument={pdfDocument}
              enableAreaSelection={(event: any) => event.altKey}
              onScrollChange={() => {}}
              pdfScaleValue="page-width"
              highlights={highlights}
              scrollRef={(scrollTo: any) => {
                // Store the scroll function locally and pass to parent
                scrollToRef.current = scrollTo;
                onScrollRef(scrollTo);
              }}
              onSelectionFinished={(
                position: any,
                content: any,
                hideTipAndSelection: any,
                transformSelection: any
              ) => (
                <Tip
                  onOpen={transformSelection}
                  onConfirm={(comment: any) => {
                    onAddHighlight({ content, position, comment });
                    hideTipAndSelection();
                  }}
                />
              )}
              highlightTransform={(
                highlight: any,
                index: number,
                setTip: any,
                hideTip: any,
                _viewportToScaled: any,
                _screenshot: any,
                isScrolledTo: boolean
              ) => (
                <Popup
                  popupContent={<div>{highlight.comment?.text}</div>}
                  onMouseOver={(popupContent: any) =>
                    setTip(highlight, () => popupContent)
                  }
                  onMouseOut={hideTip}
                  key={index}
                >
                  <Highlight
                    isScrolledTo={isScrolledTo}
                    position={highlight.position}
                    comment={highlight.comment}
                  />
                </Popup>
              )}
            />
          );
        }}
      </PdfLoader>
    </div>
  );
}