export interface DocumentInfo {
  total_pages: number;
  total_chunks: number;
  total_text_length: number;
  total_images: number;
}

export interface PDFBoundingRect {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  width?: number;
  height?: number;
  pageNumber?: number;
}

export interface PDFHighlightPosition {
  boundingRect: PDFBoundingRect;
  rects: PDFBoundingRect[];
  pageNumber?: number;
}

export interface PDFViewport {
  width: number;
  height: number;
}

export interface PDFPage {
  getViewport(options: { scale: number }): PDFViewport;
}

export interface PDFDocument {
  numPages: number;
  getPage(pageNumber: number): Promise<PDFPage>;
  destroyed?: boolean;
}

export interface PDFViewer {
  scrollPageIntoView(options: {
    pageNumber: number;
    destArray?: Array<null | { name: string } | number>;
  }): void;
  viewer?: {
    scrollPageIntoView(options: {
      pageNumber: number;
      destArray?: Array<null | { name: string } | number>;
    }): void;
  };
}