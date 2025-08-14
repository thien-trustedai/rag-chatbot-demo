import { QueryRequest, ChatResponse, UploadResponse, DocumentInfo } from '../types/domain';
import { API_BASE_URL, API_ENDPOINTS } from '../config/environment';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export class ChatApiClient {
  private async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new ApiError(response.status, `Request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async sendChatMessage(request: QueryRequest): Promise<ChatResponse> {
    return this.makeRequest<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(API_ENDPOINTS.uploadPdf, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new ApiError(response.status, 'Failed to upload document');
    }

    return response.json();
  }

  async getDocumentInfo(documentId: string): Promise<DocumentInfo> {
    return this.makeRequest<DocumentInfo>(`/document/${documentId}/info`);
  }

  getDocumentUrl(documentId: string): string {
    return API_ENDPOINTS.getPdf(documentId);
  }
}

export const apiClient = new ChatApiClient();