import React from 'react';
import { DocumentInfo } from '@/types/pdf';

interface DocumentStatsProps {
  documentInfo: DocumentInfo;
}

export default function DocumentStats({ documentInfo }: DocumentStatsProps) {
  // Handle missing or undefined fields gracefully
  const totalPages = documentInfo?.total_pages || documentInfo?.page_count || 0;
  const totalChunks = documentInfo?.total_chunks || documentInfo?.chunk_count || 0;
  const totalTextLength = documentInfo?.total_text_length || 0;
  const totalImages = documentInfo?.total_images || 0;

  return (
    <div className="p-4 bg-white border-t border-gray-200">
      <div className="text-sm text-gray-600 grid grid-cols-2 gap-4">
        <div>
          <span className="font-medium">Pages:</span> {totalPages}
        </div>
        <div>
          <span className="font-medium">Chunks:</span> {totalChunks}
        </div>
        <div>
          <span className="font-medium">Text Length:</span> {totalTextLength.toLocaleString()} chars
        </div>
        <div>
          <span className="font-medium">Images:</span> {totalImages}
        </div>
      </div>
    </div>
  );
}