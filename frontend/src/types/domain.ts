export interface BoundingRectangle {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  pageWidth?: number;
  pageHeight?: number;
  pageNumber?: number;
}

export interface PositionData {
  boundingRect?: BoundingRectangle;
  bounding_rectangle?: BoundingRectangle;
  rects?: BoundingRectangle[];
  rectangles?: BoundingRectangle[];
  points?: number[][];
  coordinate_points?: number[][];
}

export interface ImageData {
  format: string;
  data: string; // base64 encoded
  width: number;
  height: number;
}

export interface Reference {
  id: string;
  page_number: number;
  text_preview: string;
  relevance_score: number;
  images: ImageData[];
  position?: PositionData;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  references?: Reference[];
}

export interface QueryRequest {
  message: string;
  document_id: string;
}

export interface ChatResponse {
  response: string;
  references: Reference[];
}

export interface DocumentInfo {
  document_id: string;
  total_chunks: number;
  total_pages: number;
  total_text_length: number;
  total_images: number;
  pages: number[];
}

export interface UploadResponse {
  document_id: string;
  filename: string;
  chunks_processed: number;
  message: string;
}

export interface PDFViewerProps {
  documentId: string;
  selectedPage: number;
  highlightPosition?: PositionData;
}

export interface ChatInterfaceProps {
  documentId: string;
  onPageReference: (page: number, position?: PositionData) => void;
}