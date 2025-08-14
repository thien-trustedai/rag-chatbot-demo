'use client';

import { ChatMessage, PositionData } from '../types/domain';
import MessageContent from './MessageContent';
import ReferencesList from './ReferencesList';

interface MessageItemProps {
  message: ChatMessage;
  onReferenceClick: (pageNumber: number, position?: PositionData) => void;
}

export default function MessageItem({ message, onReferenceClick }: MessageItemProps) {
  return (
    <div className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-lg p-4 ${
          message.type === 'user'
            ? 'bg-blue-600 text-white shadow-md'
            : 'bg-white text-gray-900 shadow-lg border border-gray-200'
        }`}
      >
        {message.type === 'user' ? (
          <p className="whitespace-pre-wrap text-sm">{message.content}</p>
        ) : (
          <MessageContent 
            content={message.content}
            references={message.references}
            onReferenceClick={onReferenceClick}
          />
        )}
      </div>
    </div>
  );
}