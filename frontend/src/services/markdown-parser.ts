export interface ParsedContent {
  type: 'text' | 'bold' | 'italic' | 'reference' | 'heading' | 'code' | 'codeblock' | 'list-item' | 'paragraph' | 'table';
  content: string;
  level?: number; // For headings
  language?: string; // For code blocks
  attributes?: {
    chunkId?: string;
    pageNumber?: number;
    refNumber?: number;
    tokens?: ParsedContent[]; // For nested content
    rows?: string[][]; // For tables
  };
}

export class MarkdownParser {
  parseContent(content: string): ParsedContent[] {
    const parts: ParsedContent[] = [];
    
    // First, handle the [[ref:N]] format from LLM responses
    const processedContent = this.processReferences(content);
    
    // Then parse the markdown
    return this.parseMarkdown(processedContent);
  }

  private processReferences(content: string): string {
    // Convert [[ref:N]] to our internal <ref> format for consistent handling
    return content.replace(/\[\[ref:(\d+)\]\]/g, (match, refNum) => {
      return `<ref data-ref-number="${refNum}">[${refNum}]</ref>`;
    });
  }

  private parseMarkdown(content: string): ParsedContent[] {
    const tokens: ParsedContent[] = [];
    const lines = content.split('\n');
    
    let inCodeBlock = false;
    let codeBlockContent: string[] = [];
    let codeBlockLanguage = '';
    let inTable = false;
    let tableRows: string[][] = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Handle code blocks
      if (line.startsWith('```')) {
        if (!inCodeBlock) {
          inCodeBlock = true;
          codeBlockLanguage = line.slice(3).trim();
          codeBlockContent = [];
        } else {
          tokens.push({
            type: 'codeblock',
            content: codeBlockContent.join('\n'),
            language: codeBlockLanguage
          });
          inCodeBlock = false;
          codeBlockLanguage = '';
        }
        continue;
      }
      
      if (inCodeBlock) {
        codeBlockContent.push(line);
        continue;
      }
      
      // Handle tables
      if (line.includes('|')) {
        const cells = line.split('|').map(cell => cell.trim()).filter(cell => cell);
        
        if (!inTable && cells.length > 0) {
          inTable = true;
          tableRows = [cells];
        } else if (inTable) {
          // Check if it's a separator line
          if (cells.every(cell => /^[-:]+$/.test(cell))) {
            // Skip separator line
            continue;
          }
          tableRows.push(cells);
        }
        continue;
      } else if (inTable) {
        // End of table
        tokens.push({
          type: 'table',
          content: '',
          attributes: {
            rows: tableRows
          }
        });
        inTable = false;
        tableRows = [];
      }
      
      // Handle headings - parse inline elements within them
      const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
      if (headingMatch) {
        const level = headingMatch[1].length;
        const headingTokens = this.parseInlineElements(headingMatch[2]);
        tokens.push({
          type: 'heading',
          content: '',
          level,
          attributes: {
            tokens: headingTokens
          }
        });
        continue;
      }
      
      // Handle list items - parse inline elements within them
      if (line.match(/^[\s]*[-*+]\s+(.+)$/) || line.match(/^[\s]*\d+\.\s+(.+)$/)) {
        const listMatch = line.match(/^[\s]*[-*+]\s+(.+)$/) || line.match(/^[\s]*\d+\.\s+(.+)$/);
        if (listMatch) {
          // Parse inline elements within the list item content
          const listItemTokens = this.parseInlineElements(listMatch[1]);
          tokens.push({
            type: 'list-item',
            content: '', // We'll handle this differently
            attributes: {
              tokens: listItemTokens // Store parsed tokens for rendering
            }
          } as any);
        }
        continue;
      }
      
      // Handle empty lines as paragraph breaks
      if (line.trim() === '') {
        tokens.push({
          type: 'paragraph',
          content: ''
        });
        continue;
      }
      
      // Parse inline elements for regular text
      tokens.push(...this.parseInlineElements(line));
      
      // Add line break if not last line
      if (i < lines.length - 1) {
        tokens.push({ type: 'text', content: '\n' });
      }
    }
    
    // Close any open table at the end
    if (inTable && tableRows.length > 0) {
      tokens.push({
        type: 'table',
        content: '',
        attributes: {
          rows: tableRows
        }
      });
    }
    
    return tokens;
  }

  private parseInlineElements(text: string): ParsedContent[] {
    const tokens: ParsedContent[] = [];
    let remaining = text;
    let lastIndex = 0;
    
    // Combined regex for all inline elements
    const inlineRegex = /(<ref[^>]*>.*?<\/ref>)|(`[^`]+`)|(\*\*|__)(.+?)\3|(\*|_)([^*_]+?)\5/g;
    
    let match;
    while ((match = inlineRegex.exec(text)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        tokens.push({
          type: 'text',
          content: text.slice(lastIndex, match.index)
        });
      }
      
      if (match[1]) {
        // Reference
        const refMatch = match[1].match(/<ref\s+data-ref-number="(\d+)">.*?\[(\d+)\].*?<\/ref>/);
        if (refMatch) {
          tokens.push({
            type: 'reference',
            content: `[${refMatch[2]}]`,
            attributes: {
              refNumber: parseInt(refMatch[1])
            }
          });
        }
      } else if (match[2]) {
        // Inline code
        tokens.push({
          type: 'code',
          content: match[2].slice(1, -1) // Remove backticks
        });
      } else if (match[3]) {
        // Bold
        tokens.push({
          type: 'bold',
          content: match[4]
        });
      } else if (match[5]) {
        // Italic
        tokens.push({
          type: 'italic',
          content: match[6]
        });
      }
      
      lastIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (lastIndex < text.length) {
      tokens.push({
        type: 'text',
        content: text.slice(lastIndex)
      });
    }
    
    return tokens;
  }
}