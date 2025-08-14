import { useState, useEffect, useRef, useCallback } from 'react';
import type { IHighlight, NewHighlight } from 'react-pdf-highlighter';
import { PDFDocument, PDFHighlightPosition } from '@/types/pdf';

export function useHighlightManagement(
  highlightPosition: PDFHighlightPosition | undefined,
  selectedPage: number | null,
  scrollToHighlight: React.MutableRefObject<(highlight: IHighlight) => void>
) {
  const [highlights, setHighlights] = useState<IHighlight[]>([]);
  const pdfDocument = useRef<PDFDocument | null>(null);

  const parseIdFromHash = () =>
    document.location.hash.slice("#highlight-".length);

  const resetHash = () => {
    document.location.hash = "";
  };

  const getHighlightById = useCallback((id: string) => {
    return highlights.find((highlight) => highlight.id === id);
  }, [highlights]);

  const scrollToHighlightFromHash = useCallback(() => {
    const id = parseIdFromHash();
    const highlight = getHighlightById(id);
    if (highlight && scrollToHighlight.current) {
      scrollToHighlight.current(highlight);
    }
  }, [getHighlightById, scrollToHighlight]);

  useEffect(() => {
    window.addEventListener("hashchange", scrollToHighlightFromHash, false);
    return () => {
      window.removeEventListener("hashchange", scrollToHighlightFromHash, false);
    };
  }, [scrollToHighlightFromHash]);

  useEffect(() => {
    if (!highlightPosition || !selectedPage || !pdfDocument.current) return;

    const createHighlightFromPosition = async () => {
      try {
        const page = await pdfDocument.current!.getPage(selectedPage);
        const viewport = page.getViewport({ scale: 1.0 });
        
        const boundingRect = highlightPosition.boundingRect;
        const rects = highlightPosition.rects || [];
        
        // Use original PDF dimensions
        const pageWidth = viewport.width;
        const pageHeight = viewport.height;
        
        console.log('Creating highlight with position:', {
          boundingRect,
          pageSize: { width: pageWidth, height: pageHeight },
          selectedPage,
          note: 'Backend now provides correctly scaled coordinates'
        });
        
        // Backend provides coordinates in standard PDF coordinate system
        // react-pdf-highlighter expects coordinates in pixels matching the page dimensions
        // Since we pass width: 595, height: 842, coordinates should be in that scale, NOT normalized!
        
        const transformBoundingRect = {
          x1: boundingRect.x1,  // Already in pixels after backend scaling
          y1: boundingRect.y1,  // Already in pixels after backend scaling
          x2: boundingRect.x2,  // Already in pixels after backend scaling
          y2: boundingRect.y2,  // Already in pixels after backend scaling
          width: pageWidth,     // 595
          height: pageHeight,   // 842
          pageNumber: selectedPage,
        };
        
        console.log('Using pixel coordinates:', {
          boundingRect: { x1: boundingRect.x1, y1: boundingRect.y1, x2: boundingRect.x2, y2: boundingRect.y2 },
          pageSize: { width: pageWidth, height: pageHeight },
          note: 'Coordinates should be in pixels (0-595 for x, 0-842 for y)'
        });
        
        const transformedRects = rects.map(rect => ({
          x1: rect.x1,  // Keep in pixels
          y1: rect.y1,  // Keep in pixels
          x2: rect.x2,  // Keep in pixels
          y2: rect.y2,  // Keep in pixels
          width: pageWidth,
          height: pageHeight,
          pageNumber: selectedPage,
        }));
        
        console.log('Transformed coordinates:', { 
          boundingRect: transformBoundingRect, 
          rects: transformedRects,
          pageSize: { width: pageWidth, height: pageHeight }
        });
        
        const highlightId = `position-${Date.now()}`;
        const newHighlight: IHighlight = {
          id: highlightId,
          content: { text: '🎯 DEBUG: This should highlight the referenced text!' },
          position: {
            boundingRect: transformBoundingRect,
            rects: transformedRects.length > 0 ? transformedRects : [transformBoundingRect],
            pageNumber: selectedPage,
          }
        };

        console.log('📍 Creating highlight:', {
          highlightId,
          position: newHighlight.position,
          pageNumber: selectedPage,
          note: 'This highlight should be visible on the PDF'
        });

        // Clear any existing highlights first
        setHighlights([]);
        
        // Add the new highlight after a short delay
        setTimeout(() => {
          console.log('🎨 Adding highlight to state');
          setHighlights([newHighlight]);
          
          // Scroll to highlight after another delay
          setTimeout(() => {
            if (scrollToHighlight.current) {
              console.log('📜 Attempting to scroll to highlight');
              scrollToHighlight.current(newHighlight);
            } else {
              console.warn('❌ scrollToHighlight.current is not available');
            }
          }, 300);
        }, 100);
      } catch (error) {
        console.error('Error creating highlight from position:', error);
      }
    };

    createHighlightFromPosition();
  }, [highlightPosition, selectedPage, scrollToHighlight]);

  const resetHighlights = () => {
    setHighlights([]);
  };

  const addHighlight = (highlight: NewHighlight) => {
    setHighlights([...highlights, { ...highlight, id: String(Math.random()).slice(2) }]);
  };

  return {
    highlights,
    pdfDocument,
    resetHighlights,
    addHighlight,
    resetHash,
    scrollToHighlightFromHash
  };
}