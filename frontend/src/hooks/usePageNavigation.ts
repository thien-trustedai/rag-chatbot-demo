import { useEffect, useRef } from 'react';
import type { IHighlight } from 'react-pdf-highlighter';
import { PDFViewer } from '@/types/pdf';

export function usePageNavigation(selectedPage: number | null) {
  const pdfViewer = useRef<PDFViewer | null>(null);
  const scrollToHighlight = useRef<(highlight: IHighlight) => void>(() => {});

  const navigateToPage = (pageNumber: number) => {
    if (!pdfViewer.current) {
      return;
    }

    // Use the pdfViewer directly since it's a PDFViewer instance
    if (pdfViewer.current.scrollPageIntoView) {
      pdfViewer.current.scrollPageIntoView({
        pageNumber,
        destArray: [null, { name: 'XYZ' }, null, null, null]
      });
    } else if (pdfViewer.current.viewer) {
      // Get the page element and scroll to it
      const pageElement = pdfViewer.current.viewer.querySelector(
        `[data-page-number="${pageNumber}"]`
      );
      if (pageElement) {
        pageElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  };

  useEffect(() => {
    if (selectedPage) {
      // Try multiple times with shorter delays
      const timers = [
        setTimeout(() => navigateToPage(selectedPage), 100),
        setTimeout(() => navigateToPage(selectedPage), 300),
        setTimeout(() => navigateToPage(selectedPage), 500),
      ];
      return () => timers.forEach(timer => clearTimeout(timer));
    }
  }, [selectedPage]);

  return {
    pdfViewer,
    scrollToHighlight,
    navigateToPage
  };
}