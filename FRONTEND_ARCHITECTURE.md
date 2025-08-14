# Frontend Architecture Documentation

## Overview

The frontend is a **Next.js 15** application with TypeScript, using the new App Router. It provides a split-screen interface for PDF viewing and chat interaction.

## Technology Stack

- **Framework**: Next.js 15.4.5 (with Turbopack)
- **UI Library**: React 19.1.0
- **Styling**: Tailwind CSS v4
- **PDF Rendering**: pdfjs-dist + react-pdf-highlighter
- **Icons**: Lucide React
- **Language**: TypeScript 5

## Directory Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── page.tsx           # Main entry point
│   │   ├── layout.tsx         # Root layout
│   │   └── globals.css        # Global styles
│   │
│   ├── components/            # React components
│   │   ├── main-page.tsx     # Main application container
│   │   ├── FileUpload.tsx    # PDF upload component
│   │   ├── PDFViewer.tsx     # PDF display component
│   │   ├── chat/             # Chat-related components
│   │   │   └── ChatInterface.tsx
│   │   ├── MessageList.tsx   # Message display
│   │   ├── MessageInput.tsx  # Chat input
│   │   ├── MessageItem.tsx   # Individual message
│   │   ├── MessageContent.tsx # Message formatting
│   │   ├── ReferencesList.tsx # Reference links
│   │   └── pdf/              # PDF-specific components
│   │
│   ├── services/             # API and business logic
│   │   ├── api.ts           # API client
│   │   └── markdown-parser.ts # Markdown processing
│   │
│   ├── config/              # Configuration
│   │   └── environment.ts   # API endpoints
│   │
│   ├── types/               # TypeScript definitions
│   │   ├── domain.ts       # Business domain types
│   │   ├── pdf.ts          # PDF-related types
│   │   └── react-pdf-highlighter.ts
│   │
│   ├── hooks/               # Custom React hooks
│   └── lib/                 # Utility functions
│
├── public/                   # Static assets
├── package.json             # Dependencies
└── next.config.ts           # Next.js configuration
```

## Key Components

### 1. MainPage Component (`main-page.tsx`)
- **Purpose**: Main application container
- **State Management**:
  - `documentId`: Current uploaded document ID
  - `selectedPage`: Current PDF page number
  - `activeHighlight`: Current highlighted text position
- **Layout**: Split-screen (50/50) with chat on left, PDF on right

### 2. FileUpload Component
- **Purpose**: Handle PDF file uploads
- **Features**:
  - Drag-and-drop support
  - File validation (PDF only)
  - Upload progress indication
- **API**: POST to `/upload-pdf`

### 3. ChatInterface Component
- **Purpose**: Chat interaction with the document
- **Features**:
  - Message history display
  - Real-time message sending
  - Reference navigation
- **API**: POST to `/chat`
- **State**: Manages messages array locally

### 4. PDFViewer Component
- **Purpose**: Display PDF documents
- **Features**:
  - Page navigation
  - Text highlighting
  - Zoom controls
- **Library**: Uses `pdfjs-dist` and `react-pdf-highlighter`
- **Dynamic Import**: Loaded client-side only (SSR disabled)

## API Integration

### API Configuration (`config/environment.ts`)
```typescript
API_BASE_URL = 'http://localhost:8000'

Endpoints:
- /upload-pdf           # Upload PDF
- /chat                # Send chat message
- /pdf/{documentId}    # Get PDF file
- /document/{documentId}/info  # Get document info
```

### API Client (`services/api.ts`)
- **Class**: `ChatApiClient`
- **Methods**:
  - `uploadDocument(file)`: Upload PDF file
  - `sendChatMessage(request)`: Send chat query
  - `getDocumentInfo(documentId)`: Get document metadata
  - `getDocumentUrl(documentId)`: Get PDF URL

## Data Flow

1. **Upload Flow**:
   ```
   User selects PDF → FileUpload → API (/upload-pdf) → Returns document_id → MainPage state
   ```

2. **Chat Flow**:
   ```
   User types message → ChatInterface → API (/chat) → Returns response + references → Update messages
   ```

3. **Reference Navigation**:
   ```
   User clicks reference → ChatInterface → onPageReference callback → MainPage → PDFViewer navigation
   ```

## Type System

### Core Types (`types/domain.ts`)

- **ChatMessage**: User/assistant messages with references
- **Reference**: Document references with page numbers and positions
- **QueryRequest**: Chat request structure
- **ChatResponse**: API response with references
- **PositionData**: PDF text position coordinates
- **BoundingRectangle**: Text bounding box coordinates

## State Management

- **Local Component State**: Using React hooks (useState, useEffect)
- **No Global State**: Each component manages its own state
- **Props Drilling**: Parent-child communication via props
- **Document ID**: Passed as prop to child components

## Key Features

1. **Split Screen Interface**
   - Left: Chat interface
   - Right: PDF viewer
   - Responsive layout

2. **Reference Linking**
   - Click references in chat to navigate PDF
   - Automatic highlighting of referenced text
   - 5-second highlight timeout

3. **Real-time Interaction**
   - Immediate message display
   - Loading states during API calls
   - Error handling with user feedback

## API Requirements from Backend

The frontend expects these endpoints from the backend:

1. **POST /upload-pdf**
   - Input: FormData with PDF file
   - Output: `{ document_id, filename, chunks_processed, message }`

2. **POST /chat**
   - Input: `{ message, document_id }`
   - Output: `{ response, references: [...] }`

3. **GET /pdf/{documentId}**
   - Output: PDF file stream

4. **GET /document/{documentId}/info**
   - Output: Document metadata

## Integration Points

### Current API Mismatches to Fix:

1. **Upload Response**: 
   - Frontend expects: `document_id`
   - Backend returns: `document_id` ✅ (matches)

2. **Chat Request**:
   - Frontend sends: `{ message, document_id }`
   - Backend expects: `{ message, session_id }` ❌ (needs mapping)

3. **Chat Response**:
   - Frontend expects: `{ response, references }`
   - Backend returns: `{ response, references, session_id }` ✅ (compatible)

4. **Document Info**:
   - Frontend endpoint: `/document/{id}/info`
   - Backend endpoint: `/document/{id}` ❌ (slight path difference)

## Development Commands

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linting
npm run lint
```

## Environment Variables

Create `.env.local`:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Browser Compatibility

- Modern browsers with ES6+ support
- PDF.js requirements
- WebSocket support (for future real-time features)

## Performance Optimizations

1. **Dynamic Imports**: PDF viewer loaded only when needed
2. **Turbopack**: Fast development builds
3. **Client-side Rendering**: PDF viewer runs client-side only
4. **Lazy Loading**: Components loaded on demand

## Next Steps for Integration

1. ✅ Frontend structure understood
2. ✅ API endpoints identified
3. ⏳ Need to align API contracts:
   - Map `document_id` to `session_id` in chat
   - Fix document info endpoint path
4. ⏳ Test full integration flow
5. ⏳ Handle WebSocket for real-time updates (optional)