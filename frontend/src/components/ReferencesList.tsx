'use client';

import { ExternalLink } from 'lucide-react';
import { Reference, PositionData } from '../types/domain';

interface ReferencesListProps {
  references: Reference[];
  onReferenceClick: (pageNumber: number, position?: PositionData) => void;
}

export default function ReferencesList({ references, onReferenceClick }: ReferencesListProps) {
  return (
    <div className="mt-3 pt-3 border-t border-gray-200">
      <p className="text-sm font-medium mb-2">References:</p>
      <div className="space-y-2">
        {references.map((reference) => (
          <button
            key={reference.id}
            className="bg-white p-2 rounded border cursor-pointer hover:bg-gray-50 transition-colors w-full text-left"
            onClick={(event) => {
              console.log('🖱️ Reference clicked:', {
                id: reference.id,
                page: reference.page_number,
                text: reference.text_preview?.substring(0, 50),
                position: reference.position
              });
              
              // Visual feedback
              const button = event.currentTarget;
              const originalBg = button.style.backgroundColor;
              button.style.backgroundColor = '#fbbf24'; // Yellow
              button.style.transform = 'scale(0.98)';
              
              setTimeout(() => {
                button.style.backgroundColor = originalBg;
                button.style.transform = 'scale(1)';
              }, 200);
              
              onReferenceClick(reference.page_number, reference.position);
            }}
            aria-label={`Navigate to reference on page ${reference.page_number}`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-blue-600">
                Page {reference.page_number} | ID: {reference.id}
              </span>
              <ExternalLink className="w-3 h-3 text-gray-400" />
            </div>
            <p className="text-xs text-gray-600 line-clamp-2">
              {reference.text_preview}
            </p>
            
            {/* Debug: Show bounding box information */}
            {reference.position?.boundingRect && (
              <div className="mt-1 p-1 bg-gray-100 rounded text-xs font-mono">
                <div className="text-gray-500 font-bold">🎯 DEBUG: Bounding Box</div>
                <div className="text-gray-600">
                  📍 x1: {reference.position.boundingRect.x1?.toFixed(2)}, 
                  y1: {reference.position.boundingRect.y1?.toFixed(2)}
                </div>
                <div className="text-gray-600">
                  📍 x2: {reference.position.boundingRect.x2?.toFixed(2)}, 
                  y2: {reference.position.boundingRect.y2?.toFixed(2)}
                </div>
                <div className="text-gray-600">
                  📏 w: {((reference.position.boundingRect.x2 || 0) - (reference.position.boundingRect.x1 || 0)).toFixed(2)}, 
                  h: {((reference.position.boundingRect.y2 || 0) - (reference.position.boundingRect.y1 || 0)).toFixed(2)}
                </div>
                <div className="text-xs text-purple-600 mt-1">
                  💡 Check browser console for transformation logs
                </div>
              </div>
            )}
            
            {!reference.position?.boundingRect && (
              <div className="mt-1 text-xs text-orange-600">
                ⚠️ No bounding box data
              </div>
            )}
            
            {reference.images && reference.images.length > 0 && (
              <div className="mt-1">
                <span className="text-xs text-purple-600">
                  Contains {reference.images.length} image(s)
                </span>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}