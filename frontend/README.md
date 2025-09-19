# ScanPro Frontend

A modern React/Next.js frontend for the ScanPro AI Document Agent.

## Features

- **Document Upload**: Drag & drop interface for PDF, JPG, PNG files
- **Real-time Search**: Chat interface for querying documents
- **Modern UI**: Built with Tailwind CSS and Next.js

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
