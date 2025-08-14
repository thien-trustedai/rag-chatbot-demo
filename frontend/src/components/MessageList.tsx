'use client';

import { ChatMessage, PositionData } from '../types/domain';
import MessageItem from './MessageItem';

interface MessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onReferenceClick: (pageNumber: number, position?: PositionData) => void;
}

export default function MessageList({ messages, isLoading, onReferenceClick }: MessageListProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
      {messages.length === 0 && (
        <div className="text-center text-gray-500 mt-8 bg-white rounded-lg p-6 shadow-sm">
          <p className="text-lg">Start a conversation by asking a question about your document.</p>
          <p className="text-sm mt-2 text-gray-400">Try: &ldquo;What is this document about?&rdquo; or &ldquo;Summarize the main points&rdquo;</p>
        </div>
      )}

      {messages.map((message) => (
        <MessageItem
          key={message.id}
          message={message}
          onReferenceClick={onReferenceClick}
        />
      ))}

      {isLoading && (
        <div className="flex justify-start">
          <div className="bg-white rounded-lg p-4 shadow-lg border border-gray-200">
            <div className="flex items-center space-x-2">
              <div className="animate-pulse flex space-x-1">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
              <span className="text-sm text-gray-600">Analyzing document...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}