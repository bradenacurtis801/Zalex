# ScanPro Frontend

A modern React/Next.js frontend for the ScanPro AI Document Agent.

## Features

- **Document Upload**: Drag & drop interface for PDF, JPG, PNG files
- **Category Management**: Browse and view documents organized by classification categories
- **Document Classification**: Real-time document type classification with confidence scores
- **Real-time Search**: Chat interface for querying documents
- **Error Handling**: Color-coded status messages with proper error feedback
- **Modern UI**: Built with Tailwind CSS and Next.js
- **Responsive Design**: Works on desktop and mobile devices

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

### Environment Variables

Create a `.env.local` file:
```
NEXT_PUBLIC_API_URL=http://localhost:5000
```

## Category Management

The frontend includes a comprehensive category management system that allows users to:

### Browse Categories
- View all available document categories (personas, mercantil, inmuebles, etc.)
- See document counts for each category
- View last updated timestamps

### Document Viewing
- Click on any category to see all documents in that category
- View document details including:
  - Filename and file path
  - Classification confidence score
  - Upload timestamp
  - Document category

### Real-time Updates
- Refresh button to reload categories
- Automatic loading states during data fetching
- Error handling with retry options

### User Interface
- **Three-panel layout**: Upload, Categories, and Search
- **Responsive design**: Works on desktop and mobile
- **Interactive elements**: Hover effects and smooth transitions
- **Status feedback**: Loading spinners and error messages

## Next.js Configuration

The frontend uses Next.js with a custom configuration in `next.config.js`:

### API Proxy Setup

The configuration includes a rewrite rule that creates a proxy between the frontend and backend:

```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:5000/api/:path*',
    },
  ]
}
```

**How it works:**
- **Frontend requests** to `http://localhost:3000/api/query` are automatically forwarded to `http://localhost:5000/api/query`
- **Solves CORS issues** - No need to configure cross-origin headers
- **Seamless integration** - Frontend can use relative URLs like `/api/query` instead of hardcoded backend URLs
- **Development convenience** - Works transparently in development and production

**Example usage:**
```typescript
// This request to the frontend:
fetch('/api/query', { method: 'POST', body: data })

// Gets automatically rewritten to:
fetch('http://localhost:5000/api/query', { method: 'POST', body: data })
```

### Other Configuration

- **`reactStrictMode: true`** - Enables React's Strict Mode for better development experience
- **`swcMinify: true`** - Uses SWC for faster JavaScript minification

## Project Structure

```
frontend/
├── app/                          # Next.js 14 App Router
│   ├── globals.css              # Global styles
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Home page
│   ├── loading.tsx              # Loading UI
│   └── error.tsx                # Error UI
├── components/                   # Reusable UI components
│   ├── ui/                      # Basic UI components
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── StatusMessage.tsx    # Color-coded status messages
│   │   ├── Modal.tsx
│   │   └── index.ts
│   ├── features/                # Feature-specific components
│   │   ├── upload/
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── FileList.tsx
│   │   │   └── UploadProgress.tsx
│   │   └── chat/
│   │       ├── ChatInterface.tsx
│   │       ├── MessageBubble.tsx
│   │       └── SearchResults.tsx
│   └── layout/                  # Layout components
│       ├── Header.tsx
│       ├── Sidebar.tsx
│       └── Footer.tsx
├── generated/                    # OpenAPI generated client
│   ├── apis/
│   ├── models/
│   └── index.ts
├── api.ts                       # Centralized API client configuration
├── hooks/                        # Custom React hooks
│   ├── useUpload.ts
│   ├── useSearch.ts
│   └── useLocalStorage.ts
├── lib/                          # Utility libraries
│   ├── utils.ts
│   ├── constants.ts
│   └── validations.ts
├── scripts/                      # Build and generation scripts
│   ├── generate-api.sh          # Unix API generation script
│   └── generate-api.bat         # Windows API generation script
├── styles/                       # Additional styles
│   ├── components.css
│   └── utilities.css
├── public/                       # Static assets
│   ├── images/
│   ├── icons/
│   └── favicon.ico
├── .env.local                    # Environment variables
├── .env.example                  # Example env file
├── .gitignore
├── next.config.js
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
├── package.json
└── README.md
```

## API Integration

The frontend uses OpenAPI Generator to create type-safe API clients from the FastAPI backend.

### Generating API Client

1. **Start your FastAPI backend** (must be running on localhost:5000 or adjust the package.json file to point to where the backend is running)
2. **Generate the client**:
   ```bash
   npm run generate-api
   ```

3. **Generated files** will be in `frontend/generated/`

### API Endpoints

The frontend communicates with the FastAPI backend through:
- `POST /api/upload` - Upload documents
- `POST /api/query` - Search documents

### Using Generated Client

```typescript
import { DefaultApi } from '@/generated'

const api = new DefaultApi()
const result = await api.uploadFiles(files)
```

## Error Handling

The frontend provides comprehensive error handling with visual feedback:

### Status Message Types

- **Success** (Green): Successful operations
- **Error** (Red): System errors, OCR failures, server errors
- **Warning** (Yellow): Validation warnings, user input issues

### Error Categories

- **503 Service Unavailable**: Service temporarily unavailable (OCR or classification service)
- **500 Internal Server Error**: Server processing errors
- **400 Bad Request**: Invalid requests or file validation
- **413 Payload Too Large**: File size exceeded

### StatusMessage Component

```typescript
<StatusMessage 
  message="Error: Service temporarily unavailable" 
  type="error" 
/>
```

The component automatically applies appropriate styling based on the message type.
