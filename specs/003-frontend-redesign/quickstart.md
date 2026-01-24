# Quickstart: Frontend Redesign

**Date**: 2026-01-24
**Feature**: Frontend Redesign - Bitcoin Auto Trading Dashboard

## Prerequisites

- Node.js 18+ (LTS recommended)
- npm 9+ or pnpm
- Backend server running on port 8000
- Auth server running on port 9000

## Setup Steps

### 1. Delete Existing Frontend (Full Rebuild)

```bash
cd /home/ubuntu/Bitcoin-Auto-Trading

# Backup current frontend (optional)
mv frontend frontend_backup_$(date +%Y%m%d)

# Create new frontend directory
mkdir frontend
cd frontend
```

### 2. Initialize Vite + React + TypeScript Project

```bash
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install
```

### 3. Install Core Dependencies

```bash
# Routing and state management
npm install react-router-dom @tanstack/react-query axios

# TradingView Lightweight Charts
npm install lightweight-charts

# Tailwind CSS utilities
npm install clsx tailwind-merge class-variance-authority

# Icons (shadcn/ui default)
npm install lucide-react
```

### 4. Install Dev Dependencies

```bash
# Testing
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom

# Types
npm install -D @types/node
```

### 5. Set Up Tailwind CSS

```bash
# Already installed by Vite template, but verify
npm install -D tailwindcss postcss autoprefixer

# Initialize Tailwind
npx tailwindcss init -p
```

Update `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0E14',
        surface: '#151921',
        accent: '#FACC15',
        up: '#10B981',
        down: '#F43F5E',
        neutral: '#F59E0B',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
```

Update `src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: Inter, system-ui, sans-serif;
}

body {
  @apply bg-background text-white;
}
```

### 6. Set Up shadcn/ui

```bash
# Initialize shadcn/ui
npx shadcn@latest init

# When prompted:
# - Style: Default
# - Base color: Slate
# - CSS variables: Yes
# - React Server Components: No
# - Components directory: src/core/components/ui
# - Utils: src/core/utils/cn.ts
```

Install required components:

```bash
npx shadcn@latest add button card dialog table tabs select input badge skeleton alert tooltip dropdown-menu progress slider switch
```

### 7. Set Up Path Aliases

Update `tsconfig.json`:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@core/*": ["./src/core/*"],
      "@api/*": ["./src/api/*"],
      "@components/*": ["./src/components/*"],
      "@views/*": ["./src/views/*"],
      "@stores/*": ["./src/stores/*"]
    }
  }
}
```

Update `vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@core': path.resolve(__dirname, './src/core'),
      '@api': path.resolve(__dirname, './src/api'),
      '@components': path.resolve(__dirname, './src/components'),
      '@views': path.resolve(__dirname, './src/views'),
      '@stores': path.resolve(__dirname, './src/stores'),
    },
  },
})
```

### 8. Create Folder Structure

```bash
mkdir -p src/{core/{api,components/ui,composables,layouts,errors,types,utils},api,stores,components/{dashboard,trading,signals,portfolio,admin},views,router,assets/styles}
```

Expected structure:

```
src/
├── core/
│   ├── api/
│   │   └── client.ts
│   ├── components/
│   │   └── ui/              # shadcn/ui components
│   ├── composables/
│   ├── layouts/
│   ├── errors/
│   ├── types/
│   └── utils/
├── api/                      # Domain API functions
├── stores/                   # Auth context
├── components/               # Domain components
│   ├── dashboard/
│   ├── trading/
│   ├── signals/
│   ├── portfolio/
│   └── admin/
├── views/                    # Page components
├── router/                   # Routes and guards
└── assets/
    └── styles/
```

### 9. Set Up Environment Variables

Create `.env`:

```bash
VITE_API_URL=http://localhost:8000
VITE_AUTH_URL=http://localhost:9000
```

Create `.env.production`:

```bash
VITE_API_URL=https://api.yourdomain.com
VITE_AUTH_URL=https://auth.yourdomain.com
```

### 10. Create Base API Client

Create `src/core/api/client.ts`:

```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL}/api/v1`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Handle 401 with token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(
          `${import.meta.env.VITE_AUTH_URL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken }
        );

        const { access_token, refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
```

### 11. Set Up TanStack Query

Update `src/main.tsx`:

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      refetchOnWindowFocus: false,
      retry: 3,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
```

### 12. Run Development Server

```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

---

## Verification Checklist

- [ ] `npm run dev` starts without errors
- [ ] Tailwind CSS classes apply correctly
- [ ] shadcn/ui Button component renders
- [ ] Path aliases resolve correctly (`@/`, `@core/`, etc.)
- [ ] API client can reach backend (check browser network tab)
- [ ] Environment variables load correctly

---

## Next Steps

1. Implement Auth Context (`src/stores/auth.store.ts`)
2. Create Router with guards (`src/router/`)
3. Build Layout components (`src/core/layouts/`)
4. Implement Dashboard view first (P1 priority)
5. Add remaining pages in priority order

---

## Useful Commands

```bash
# Development
npm run dev           # Start dev server
npm run build         # Production build
npm run preview       # Preview production build

# Testing
npm run test          # Run Vitest
npm run test:ui       # Run Vitest with UI

# Linting
npm run lint          # Run ESLint
npm run lint:fix      # Fix ESLint issues

# Add shadcn component
npx shadcn@latest add [component-name]
```
