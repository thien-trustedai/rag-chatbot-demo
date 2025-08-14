'use client';

import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Reference, PositionData } from '../types/domain';

interface MessageContentProps {
  content: string;
  references?: Reference[];
  onReferenceClick: (pageNumber: number, position?: PositionData) => void;
}

export default function MessageContent({ content, references, onReferenceClick }: MessageContentProps) {
  
  const findReferenceByNumber = (refNumber: number) => {
    if (!references || refNumber <= 0) return null;
    return references[refNumber - 1];
  };

  // Process content to make references clickable using a custom component approach
  const processedContent = useMemo(() => {
    // Keep the [[ref:N]] format as-is, we'll handle it in rendering
    return content;
  }, [content]);

  // Helper function to recursively process children and replace references
  const processChildren = (children: any): any => {
    if (typeof children === 'string') {
      // Split by reference pattern and process each part
      const parts = children.split(/(\[\[ref:\d+\]\])/g);
      return parts.map((part, index) => {
        const refMatch = part.match(/\[\[ref:(\d+)\]\]/);
        if (refMatch) {
          const refNum = parseInt(refMatch[1]);
          const reference = findReferenceByNumber(refNum);
          return (
            <button
              key={`ref-${index}`}
              onClick={() => {
                if (reference) {
                  onReferenceClick(reference.page_number || 1, reference.position);
                }
              }}
              className="inline-flex items-center px-1.5 py-0.5 mx-0.5 text-xs font-medium text-blue-700 bg-blue-100 rounded-md hover:bg-blue-200 transition-colors cursor-pointer"
              title={reference ? `Go to page ${reference.page_number}` : 'Reference'}
            >
              [{refNum}]
            </button>
          );
        }
        return part;
      });
    }
    
    if (Array.isArray(children)) {
      return children.map((child, index) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child as React.ReactElement<any>, { key: index });
        }
        return processChildren(child);
      });
    }
    
    if (React.isValidElement(children)) {
      const props = (children as any).props;
      if (props && props.children) {
        return React.cloneElement(children as React.ReactElement<any>, {
          children: processChildren(props.children)
        });
      }
    }
    
    return children;
  };

  // Custom components for rendering markdown elements
  const components = {
    // Headings
    h1: ({children}: any) => <h1 className="text-2xl font-bold mt-4 mb-3">{processChildren(children)}</h1>,
    h2: ({children}: any) => <h2 className="text-xl font-bold mt-3 mb-2">{processChildren(children)}</h2>,
    h3: ({children}: any) => <h3 className="text-lg font-semibold mt-2 mb-2">{processChildren(children)}</h3>,
    h4: ({children}: any) => <h4 className="text-base font-semibold mt-2 mb-1">{processChildren(children)}</h4>,
    
    // Paragraphs - process all children for references
    p: ({children}: any) => <p className="mb-2">{processChildren(children)}</p>,
    
    // Lists
    ul: ({children}: any) => <ul className="list-disc list-inside ml-4 mb-2">{processChildren(children)}</ul>,
    ol: ({children}: any) => <ol className="list-decimal list-inside ml-4 mb-2">{processChildren(children)}</ol>,
    li: ({children}: any) => <li className="mb-1">{processChildren(children)}</li>,
    
    // Code
    code: ({inline, className, children}: any) => {
      // Don't process references inside code blocks
      const codeContent = String(children).replace(/\n$/, '');
      if (inline) {
        return (
          <code className="px-1 py-0.5 bg-gray-200 text-gray-800 rounded text-sm font-mono">
            {codeContent}
          </code>
        );
      }
      const language = className?.replace('language-', '');
      return (
        <code className={`block p-3 bg-gray-900 text-gray-100 rounded-lg overflow-x-auto text-sm font-mono my-2 ${className || ''}`}>
          {codeContent}
        </code>
      );
    },
    
    pre: ({children}: any) => {
      return (
        <pre className="my-2 p-3 bg-gray-900 text-gray-100 rounded-lg overflow-x-auto">
          {children}
        </pre>
      );
    },
    
    // Tables (from remark-gfm)
    table: ({children}: any) => (
      <div className="overflow-x-auto my-3">
        <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
          {children}
        </table>
      </div>
    ),
    thead: ({children}: any) => <thead className="bg-gray-50">{children}</thead>,
    tbody: ({children}: any) => <tbody className="bg-white divide-y divide-gray-200">{children}</tbody>,
    tr: ({children}: any) => <tr>{children}</tr>,
    th: ({children}: any) => (
      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
        {processChildren(children)}
      </th>
    ),
    td: ({children}: any) => (
      <td className="px-3 py-2 text-sm text-gray-900 whitespace-nowrap">
        {processChildren(children)}
      </td>
    ),
    
    // Links
    a: ({href, children}: any) => (
      <a href={href} className="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">
        {processChildren(children)}
      </a>
    ),
    
    // Emphasis - process children for references
    strong: ({children}: any) => <strong className="font-semibold">{processChildren(children)}</strong>,
    em: ({children}: any) => <em className="italic">{processChildren(children)}</em>,
    
    // Blockquote
    blockquote: ({children}: any) => (
      <blockquote className="border-l-4 border-gray-300 pl-4 italic my-2 text-gray-600">
        {processChildren(children)}
      </blockquote>
    ),
    
    // Horizontal rule
    hr: () => <hr className="my-4 border-gray-300" />,
  };

  return (
    <div className="message-content prose prose-sm max-w-none">
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]}
        components={components as any}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
}