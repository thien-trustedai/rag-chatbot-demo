'use client';

import { useState, useRef, useEffect } from 'react';
import { MessageCircle } from 'lucide-react';
import { ChatMessage, ChatInterfaceProps, PositionData, QueryRequest } from '../../types/domain';
import { apiClient } from '../../services/api';
import MessageList from '../MessageList';
import MessageInput from '../MessageInput';

export default function ChatInterface({ documentId, onPageReference }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndReference = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndReference.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const submitQuery = async (messageText: string) => {
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: messageText,
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const queryRequest: QueryRequest = {
        message: messageText,
        document_id: documentId,
      };

      const result = await apiClient.sendChatMessage(queryRequest);

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: result.response,
        references: result.references,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const navigateToReference = (pageNumber: number, position?: PositionData) => {
    onPageReference(pageNumber, position);
  };

  return (
    <div className="h-full flex flex-col bg-white">      
      <MessageList
        messages={messages}
        isLoading={isLoading}
        onReferenceClick={navigateToReference}
      />

      <MessageInput 
        onSendMessage={submitQuery}
        isLoading={isLoading}
      />

      <div ref={messagesEndReference} />
    </div>
  );
}