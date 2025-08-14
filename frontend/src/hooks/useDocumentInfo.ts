import { useState, useEffect } from 'react';
import { DocumentInfo } from '@/types/pdf';
import { API_ENDPOINTS } from '@/config/environment';

export function useDocumentInfo(documentId: string | null) {
  const [documentInfo, setDocumentInfo] = useState<DocumentInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!documentId) {
      setDocumentInfo(null);
      setIsLoading(false);
      return;
    }

    const fetchDocumentInfo = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await fetch(API_ENDPOINTS.getDocumentInfo(documentId));
        if (!response.ok) {
          throw new Error(`Failed to fetch document info: ${response.statusText}`);
        }
        const info = await response.json();
        setDocumentInfo(info);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch document info');
        setDocumentInfo(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDocumentInfo();
  }, [documentId]);

  return { documentInfo, isLoading, error };
}