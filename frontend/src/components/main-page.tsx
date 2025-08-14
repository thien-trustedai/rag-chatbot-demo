'use client';

import { useState, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { PositionData } from '../types/domain';
import { PDFHighlightPosition } from '../types/pdf';
import ChatInterface from './chat/ChatInterface';
import FileUpload from './FileUpload';

const PDFViewer = dynamic(() => import('./PDFViewer'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading PDF Viewer...</p>
      </div>
    </div>
  ),
});

export default function MainPage() {
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [selectedPage, setSelectedPage] = useState<number>(1);
  const [activeHighlight, setActiveHighlight] = useState<PositionData | undefined>();

  const pdfHighlightPosition = useMemo<PDFHighlightPosition | undefined>(() => {
    if (!activeHighlight) return undefined;
    
    const boundingRect = activeHighlight.boundingRect || activeHighlight.bounding_rectangle;
    const rects = activeHighlight.rects || activeHighlight.rectangles || [];
    
    if (!boundingRect) return undefined;
    
    return {
      boundingRect,
      rects
    };
  }, [activeHighlight]);

  const navigateToPage = (page: number, position?: PositionData) => {
    console.log('NavigateToPage called with:', {
      page,
      position,
      boundingRect: position?.boundingRect || position?.bounding_rectangle
    });
    
    setSelectedPage(page);
    setActiveHighlight(position);
    
    if (position) {
      setTimeout(() => setActiveHighlight(undefined), 5000);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="bg-white shadow-sm border-b p-4">
        <h1 className="text-2xl font-bold text-gray-900">TrustedAI</h1>
      </header>
      {!documentId ? (
        <div className="flex-1 flex items-center justify-center">
          <FileUpload onUploadComplete={setDocumentId} />
        </div>
      ) : (
        <div className="flex-1 flex overflow-hidden">
          <div className="w-1/2 border-r border-gray-200">
            <ChatInterface 
              documentId={documentId} 
              onPageReference={navigateToPage}
            />
          </div>
          <div className="w-1/2">
            <PDFViewer 
              documentId={documentId} 
              selectedPage={selectedPage}
              highlightPosition={pdfHighlightPosition}
            />
          </div>
        </div>
      )}
    </div>
  );
}