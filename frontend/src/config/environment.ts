export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  uploadPdf: `${API_BASE_URL}/upload-pdf`,
  chat: `${API_BASE_URL}/chat`,
  getPdf: (documentId: string) => `${API_BASE_URL}/pdf/${documentId}`,
  getDocumentInfo: (documentId: string) => `${API_BASE_URL}/document/${documentId}/info`,
} as const;