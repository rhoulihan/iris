# IRIS Web Console - Implementation Plan

**Version**: 1.0
**Created**: 2025-11-22
**Status**: Draft for Review
**Timeline**: 4 weeks (Phase 1 - Standalone Web Console)

---

## 1. Executive Summary

This document outlines the technical implementation plan for the IRIS Web Console Phase 1. It maps the requirements from `WEB_CONSOLE_REQUIREMENTS.md` to specific technical tasks, components, and timelines.

### 1.1 Technology Stack

**Frontend**:
- **Framework**: Svelte 5.x (compile-time optimization, smallest bundle)
- **Build Tool**: Vite 6.x (fast HMR, optimized production builds)
- **Language**: TypeScript 5.x (type safety)
- **UI Framework**: Tailwind CSS 3.x + DaisyUI 4.x (utility-first, component library)
- **Charts**: Chart.js 4.x (simple, performant)
- **HTTP Client**: Native Fetch API (no dependencies)
- **Routing**: SvelteKit or svelte-routing
- **State Management**: Svelte stores (built-in, reactive)
- **Icons**: Heroicons or Lucide Icons (SVG, tree-shakeable)
- **Dates**: date-fns (lightweight, modular)

**Backend** (Existing + Enhancements):
- **API**: FastAPI 0.115+ (already implemented)
- **Static Serving**: FastAPI StaticFiles (serves Svelte dist/)
- **Database**: Oracle Database 23ai/26ai
- **ORM**: SQLAlchemy (for new tables: connections, notifications, preferences)

**Development Tools**:
- **Package Manager**: pnpm (faster than npm, disk-efficient)
- **Linting**: ESLint + TypeScript ESLint
- **Formatting**: Prettier
- **Testing**: Vitest (unit), Playwright (E2E)
- **Version Control**: Git + GitHub

### 1.2 Project Structure

```
iris/
├── frontend/                           # Svelte SPA (NEW)
│   ├── src/
│   │   ├── routes/                    # SvelteKit routes
│   │   │   ├── +layout.svelte         # Root layout (header, sidebar, footer)
│   │   │   ├── +page.svelte           # Dashboard (/)
│   │   │   ├── analyze/
│   │   │   │   └── +page.svelte       # New Analysis Wizard
│   │   │   ├── sessions/
│   │   │   │   ├── +page.svelte       # Analysis History
│   │   │   │   └── [id]/
│   │   │   │       └── +page.svelte   # Session Detail
│   │   │   ├── recommendations/
│   │   │   │   ├── +page.svelte       # Recommendations List
│   │   │   │   ├── compare/+page.svelte # Comparison View
│   │   │   │   └── [id]/+page.svelte  # Recommendation Detail
│   │   │   ├── simulations/
│   │   │   │   ├── +page.svelte       # Simulation Library
│   │   │   │   ├── [id]/+page.svelte  # Simulation Execution
│   │   │   │   └── history/+page.svelte # Simulation History
│   │   │   ├── config/
│   │   │   │   └── +page.svelte       # Configuration Page
│   │   │   └── login/
│   │   │       └── +page.svelte       # Login Page
│   │   ├── lib/
│   │   │   ├── components/            # Reusable UI components
│   │   │   │   ├── ui/                # Base components (Button, Card, Modal, etc.)
│   │   │   │   ├── charts/            # Chart components (PieChart, BarChart, etc.)
│   │   │   │   ├── layout/            # Layout components (Header, Sidebar, Footer)
│   │   │   │   └── domain/            # Domain-specific (RecommendationCard, AnalysisProgress)
│   │   │   ├── services/
│   │   │   │   ├── api.ts             # API client wrapper
│   │   │   │   ├── auth.ts            # Authentication service
│   │   │   │   └── notifications.ts   # Notification service
│   │   │   ├── stores/                # Svelte stores
│   │   │   │   ├── auth.ts            # Auth state
│   │   │   │   ├── sessions.ts        # Analysis sessions
│   │   │   │   ├── recommendations.ts # Recommendations
│   │   │   │   └── config.ts          # Configuration
│   │   │   ├── types/                 # TypeScript types
│   │   │   │   ├── analysis.ts
│   │   │   │   ├── recommendation.ts
│   │   │   │   └── simulation.ts
│   │   │   └── utils/                 # Utility functions
│   │   │       ├── formatters.ts      # Date, currency, number formatting
│   │   │       ├── validators.ts      # Input validation
│   │   │       └── constants.ts       # App constants
│   │   └── app.html                   # HTML template
│   ├── static/                        # Public assets
│   │   ├── favicon.ico
│   │   ├── logo.svg
│   │   └── images/
│   ├── tests/
│   │   ├── unit/                      # Vitest unit tests
│   │   └── e2e/                       # Playwright E2E tests
│   ├── .env.example
│   ├── package.json
│   ├── vite.config.ts
│   ├── svelte.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── playwright.config.ts
│   └── README.md
│
├── src/                                # Backend (Existing + Enhancements)
│   ├── api/
│   │   ├── app.py                     # FastAPI (ENHANCED: add static files, new endpoints)
│   │   ├── endpoints/                 # NEW: organize endpoints
│   │   │   ├── sessions.py            # Session endpoints (existing)
│   │   │   ├── recommendations.py     # Recommendation endpoints (existing + new)
│   │   │   ├── config.py              # NEW: Configuration endpoints
│   │   │   ├── connections.py         # NEW: Saved connections
│   │   │   ├── simulations.py         # NEW: Simulation endpoints
│   │   │   ├── metrics.py             # NEW: Metrics/analytics
│   │   │   └── notifications.py       # NEW: Notifications
│   │   ├── models/                    # NEW: Pydantic models
│   │   │   ├── connection.py
│   │   │   ├── config.py
│   │   │   ├── simulation.py
│   │   │   └── notification.py
│   │   └── middleware/                # NEW: Auth, CORS, error handling
│   │       ├── auth.py
│   │       └── cors.py
│   ├── db/                            # NEW: Database layer
│   │   ├── models.py                  # SQLAlchemy ORM models (connections, notifications, etc.)
│   │   ├── session.py                 # Database session management
│   │   └── migrations/                # Alembic migrations
│   └── ...                            # Existing modules (recommendation, pipeline, etc.)
│
└── docs/
    ├── WEB_CONSOLE_REQUIREMENTS.md    # This file's companion
    └── WEB_CONSOLE_IMPLEMENTATION_PLAN.md # This file
```

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Browser (Client)                                                │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Svelte SPA                                               │  │
│  │  ├─ Routes (SvelteKit)                                  │  │
│  │  ├─ Components (UI, Charts, Forms)                      │  │
│  │  ├─ Stores (State Management)                           │  │
│  │  ├─ Services (API Client, Auth)                         │  │
│  │  └─ Utils (Formatters, Validators)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          │ HTTP/JSON                            │
│                          ▼                                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ FastAPI Server (Python)                                         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Static Files Serving                                      │  │
│  │  └─ /  → Svelte SPA (dist/)                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ REST API Endpoints                                        │  │
│  │  ├─ /api/v1/sessions      (Existing)                    │  │
│  │  ├─ /api/v1/recommendations (Existing + Enhanced)       │  │
│  │  ├─ /api/v1/config         (NEW)                        │  │
│  │  ├─ /api/v1/connections    (NEW)                        │  │
│  │  ├─ /api/v1/simulations    (NEW)                        │  │
│  │  ├─ /api/v1/metrics        (NEW)                        │  │
│  │  └─ /api/v1/notifications  (NEW)                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          │ SQLAlchemy ORM                       │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Database Layer (NEW)                                      │  │
│  │  ├─ Saved Connections Table                             │  │
│  │  ├─ Notifications Table                                  │  │
│  │  ├─ User Preferences Table                              │  │
│  │  ├─ Config History Table                                │  │
│  │  └─ Simulation Executions Table                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ IRIS Pipeline Orchestrator (Existing)                    │  │
│  │  ├─ AWR Collector                                        │  │
│  │  ├─ Pattern Detectors                                    │  │
│  │  ├─ Cost Calculator                                      │  │
│  │  └─ Recommendation Engine                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Oracle Database 23ai/26ai                                       │
│  ├─ AWR (DBA_HIST_*)                                           │
│  ├─ Schema Metadata (DBA_TABLES, DBA_INDEXES, etc.)           │
│  └─ Simulation Schemas (IRIS_SIM_*)                           │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

**Analysis Execution Flow**:
1. User fills analysis form → Frontend validates → POST `/api/v1/analyze`
2. FastAPI creates session ID → Returns 202 Accepted immediately
3. Frontend polls GET `/api/v1/sessions/{id}` every 2 seconds
4. Backend runs pipeline (AWR → Pattern Detection → Cost Calculation)
5. Backend updates session status (in_progress → completed)
6. Frontend displays results when status = completed

**Recommendation Management Flow**:
1. User views recommendations → GET `/api/v1/recommendations/{analysis_id}`
2. Frontend renders list with filters/sorting
3. User clicks recommendation → GET `/api/v1/recommendations/{analysis_id}/{rec_id}`
4. Frontend displays detail page
5. User changes status (approve) → PATCH `/api/v1/recommendations/{id}` {status: 'approved'}
6. Backend updates database, returns updated recommendation
7. Frontend optimistically updates UI, then confirms with server response

---

## 3. Component Breakdown

### 3.1 UI Component Library

We'll use **DaisyUI** (Tailwind CSS component library) for base components, with custom domain components on top.

#### Base Components (from DaisyUI)
- Button, Input, Select, Checkbox, Radio
- Card, Modal, Dropdown, Tabs, Accordion
- Table, Pagination, Breadcrumbs
- Alert, Badge, Progress, Spinner
- Navbar, Drawer (sidebar), Footer

#### Custom Components (to build)

**Layout Components**:
```svelte
<!-- src/lib/components/layout/Header.svelte -->
<script lang="ts">
  import { user } from '$lib/stores/auth';
  import NotificationBell from './NotificationBell.svelte';
</script>

<header class="navbar bg-base-100 shadow-lg">
  <div class="flex-1">
    <a href="/" class="btn btn-ghost text-xl">
      <img src="/logo.svg" alt="IRIS" class="w-8 h-8" />
      IRIS
    </a>
  </div>
  <div class="flex-none gap-2">
    <NotificationBell />
    <div class="dropdown dropdown-end">
      <label tabindex="0" class="btn btn-ghost btn-circle avatar">
        <div class="w-10 rounded-full bg-primary text-primary-content flex items-center justify-center">
          {$user?.username?.[0]?.toUpperCase() || 'U'}
        </div>
      </label>
      <ul tabindex="0" class="mt-3 p-2 shadow menu menu-compact dropdown-content bg-base-100 rounded-box w-52">
        <li><a href="/config">Settings</a></li>
        <li><a on:click={logout}>Logout</a></li>
      </ul>
    </div>
  </div>
</header>
```

**Domain Components**:

1. **AnalysisCard** (`src/lib/components/domain/AnalysisCard.svelte`)
   - Props: `session: AnalysisSession`
   - Displays: ID, date, database, status badge, patterns count
   - Action: Click to navigate to session detail

2. **RecommendationCard** (`src/lib/components/domain/RecommendationCard.svelte`)
   - Props: `recommendation: Recommendation`
   - Displays: Pattern type icon, target, severity, priority, savings
   - Action: Click to view detail, checkbox for multi-select

3. **AnalysisProgress** (`src/lib/components/domain/AnalysisProgress.svelte`)
   - Props: `session: AnalysisSession`
   - Displays: Multi-stage progress bar with status badges
   - Auto-refreshes via poll

4. **PatternDistributionChart** (`src/lib/components/charts/PatternDistributionChart.svelte`)
   - Props: `data: Record<PatternType, number>`
   - Renders: Chart.js pie chart
   - Interactive: Click segment to filter

5. **CostBenefitScatterPlot** (`src/lib/components/charts/CostBenefitScatterPlot.svelte`)
   - Props: `recommendations: Recommendation[]`
   - Renders: Chart.js scatter plot (bubble chart)
   - Interactive: Click bubble to view recommendation

### 3.2 Service Layer

#### API Client (`src/lib/services/api.ts`)

```typescript
// Base API client with error handling and auth
class ApiClient {
  private baseURL = '/api/v1';

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const token = localStorage.getItem('token');
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options?.headers,
    };

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        headers,
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Redirect to login
          goto('/login');
        }
        throw new Error(`API Error: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Convenience methods
  get<T>(endpoint: string) {
    return this.request<T>(endpoint);
  }

  post<T>(endpoint: string, data: unknown) {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  patch<T>(endpoint: string, data: unknown) {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  delete<T>(endpoint: string) {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const api = new ApiClient();

// Domain-specific API functions
export const sessionsApi = {
  list: () => api.get<AnalysisSession[]>('/sessions'),
  get: (id: string) => api.get<AnalysisSession>(`/sessions/${id}`),
  create: (data: AnalyzeRequest) => api.post<{ analysis_id: string }>('/analyze', data),
  cancel: (id: string) => api.post<void>(`/sessions/${id}/cancel`, {}),
};

export const recommendationsApi = {
  list: (analysisId: string) =>
    api.get<Recommendation[]>(`/recommendations/${analysisId}`),
  get: (analysisId: string, recId: string) =>
    api.get<Recommendation>(`/recommendations/${analysisId}/${recId}`),
  updateStatus: (id: string, status: RecommendationStatus) =>
    api.patch<Recommendation>(`/recommendations/${id}`, { status }),
};

export const simulationsApi = {
  list: () => api.get<Simulation[]>('/simulations'),
  execute: (id: string, config: SimulationConfig) =>
    api.post<{ execution_id: string }>(`/simulations/${id}/execute`, config),
  status: (executionId: string) =>
    api.get<SimulationExecution>(`/simulations/${executionId}/status`),
  cancel: (executionId: string) =>
    api.post<void>(`/simulations/${executionId}/cancel`, {}),
};

// ... more domain APIs
```

#### Auth Service (`src/lib/services/auth.ts`)

```typescript
import { writable } from 'svelte/store';
import type { User } from '$lib/types/user';

export const user = writable<User | null>(null);
export const isAuthenticated = writable(false);

export const authService = {
  async login(username: string, password: string) {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      throw new Error('Invalid credentials');
    }

    const { token, user: userData } = await response.json();
    localStorage.setItem('token', token);
    user.set(userData);
    isAuthenticated.set(true);

    return userData;
  },

  logout() {
    localStorage.removeItem('token');
    user.set(null);
    isAuthenticated.set(false);
  },

  async checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
      return false;
    }

    try {
      const userData = await fetch('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      }).then(r => r.json());

      user.set(userData);
      isAuthenticated.set(true);
      return true;
    } catch {
      this.logout();
      return false;
    }
  },
};
```

### 3.3 State Management

Using Svelte stores for global state:

```typescript
// src/lib/stores/sessions.ts
import { writable, derived } from 'svelte/store';
import { sessionsApi } from '$lib/services/api';

export const sessions = writable<AnalysisSession[]>([]);
export const activeSessions = derived(
  sessions,
  $sessions => $sessions.filter(s => s.status === 'in_progress')
);

export const sessionsStore = {
  async load() {
    const data = await sessionsApi.list();
    sessions.set(data);
  },

  async refresh(id: string) {
    const session = await sessionsApi.get(id);
    sessions.update(all => {
      const index = all.findIndex(s => s.analysis_id === id);
      if (index >= 0) {
        all[index] = session;
      } else {
        all.unshift(session);
      }
      return all;
    });
  },

  startPolling(id: string, callback?: (session: AnalysisSession) => void) {
    const interval = setInterval(async () => {
      const session = await sessionsApi.get(id);
      this.refresh(id);

      if (session.status !== 'in_progress') {
        clearInterval(interval);
        callback?.(session);
      }
    }, 2000);

    return () => clearInterval(interval);
  },
};
```

---

## 4. Development Phases & Timeline

### Phase 1: Setup & Foundation (Week 1)

#### Sprint 1.1: Project Initialization (Days 1-2) ✅ COMPLETE (2025-11-22)

**Tasks**:
- [x] Initialize Svelte + SvelteKit project (used `npx sv create` - pnpm unavailable)
- [x] Configure Tailwind CSS v4 + DaisyUI v5 (with @tailwindcss/postcss)
- [x] Configure TypeScript (strict mode enabled in tsconfig.json)
- [x] Set up ESLint v9 (flat config) + Prettier
- [x] **Added: Security scanning** (eslint-plugin-security, npm audit pre-commit hook)
- [x] **Added: Frontend pre-commit hooks** (ESLint, Prettier, svelte-check, npm audit)
- [x] Create project structure (components/{ui,charts,layout,domain}, services, stores, types, utils)
- [x] **Added: API client service** (typed methods for all endpoints)
- [x] **Added: Svelte stores** (sessions, recommendations, config, theme)
- [x] **Added: TypeScript types** (analysis, recommendation, simulation, connection)
- [x] **Added: Utility functions** (formatters, validators, constants)
- [x] Set up Vite config (API proxy for development, build optimization)
- [x] Create .env.example

**Deliverables**:
- ✅ Frontend project initialized at `/frontend`
- ✅ Dev server runs on http://localhost:5173
- ✅ Tailwind CSS + DaisyUI working (verified with dashboard demo)
- ✅ TypeScript strict mode enforced
- ✅ Production build verified (0 errors, 0 warnings)
- ✅ Security scanning active (ReDoS prevention, dependency auditing)

---

#### Sprint 1.2: Base UI Components & Layout (Days 3-4) ✅ COMPLETE (2025-11-22)

**Tasks**:
- [x] Create root layout (`+layout.svelte`)
  - [x] Header with logo, navigation, user menu, theme toggle
  - [x] Sidebar navigation (collapsible with expandable sections)
  - [x] Main content area
  - [x] Footer with version info
- [x] Build base UI components:
  - [x] Button (primary, secondary, accent, success, warning, error, ghost, link, outline, loading states)
  - [x] Card (header, body, actions with slots)
  - [x] Modal (with backdrop, keyboard navigation, customizable actions)
  - [x] Alert (success, error, warning, info, dismissible)
  - [x] Badge (severity, status, priority with DaisyUI integration)
  - [x] Table (sortable headers, custom renderers, zebra striping)
  - [x] Input (with label, error, helper text, validation)
  - [x] Select (dropdown with options, placeholder, validation)
  - [x] Checkbox (with label, colors, sizes)
  - [x] Loading spinner (multiple types, full-screen mode)
  - [x] Empty state (icon, title, description, action button)
  - [x] ThemeToggle (light/dark/auto mode switcher)
- [x] Implement theme switcher (light/dark/auto mode with localStorage persistence)
- [x] Theme system responds to system preference changes
- [x] Component index files for easy imports

**Deliverables**:
- ✅ 15 reusable Svelte components created (3 layout + 12 UI)
- ✅ Responsive layout working on desktop/tablet/mobile
- ✅ Theme toggle functional (light/dark/auto with system preference detection)
- ✅ Navigation working (sidebar with collapsible sections)
- ✅ Production build verified (0 TypeScript errors, 0 ESLint warnings)
- ✅ All components properly typed with TypeScript

**Testing**:
- ✅ TypeScript compilation: 0 errors
- ✅ ESLint checks: 0 warnings
- ✅ Production build: Successful (build time: 1m 9s)

---

#### Sprint 1.3: API Client & Auth (Days 5-6)

**Tasks**:
- [ ] Implement API client service (api.ts)
  - [ ] Base request method with error handling
  - [ ] GET, POST, PATCH, DELETE helpers
  - [ ] Authentication header injection
  - [ ] Retry logic for transient failures (3 attempts, exponential backoff)
- [ ] Implement auth service (auth.ts)
  - [ ] Login function (username/password → JWT)
  - [ ] Logout function
  - [ ] Check auth status (on app load)
  - [ ] Auto-logout on 401 responses
- [ ] Create auth store (Svelte writable store)
- [ ] Build Login page
  - [ ] Username/password form
  - [ ] "Remember me" checkbox
  - [ ] Error message display
  - [ ] Redirect to dashboard on success
- [ ] Implement auth guard (protect routes, redirect to login if unauthenticated)
- [ ] Backend: Add /api/v1/auth/login and /api/v1/auth/me endpoints

**Deliverables**:
- API client service functional (tested with mock API)
- Login page working (redirects to dashboard)
- Protected routes (unauthenticated users redirected to login)
- JWT token stored in localStorage

**Testing**:
- Unit tests: API client error handling, token injection
- E2E test: Login flow (valid credentials, invalid credentials)

---

#### Sprint 1.4: Dashboard Page (Day 7)

**Tasks**:
- [ ] Build Dashboard page (`routes/+page.svelte`)
  - [ ] Summary cards (4 metrics: analyses, acceptance rate, savings, active)
  - [ ] Activity feed (recent 10 sessions, scrollable)
  - [ ] Pattern distribution pie chart (Chart.js)
  - [ ] Quick action cards (top 3 recommendations)
- [ ] Create AnalysisCard component (for activity feed)
- [ ] Create PatternDistributionChart component (Chart.js wrapper)
- [ ] Implement auto-refresh (every 30 seconds)
- [ ] Backend: Add GET /api/v1/metrics/summary endpoint
- [ ] Backend: Add GET /api/v1/metrics/pattern-distribution endpoint

**Deliverables**:
- Dashboard page displaying real data (or mock data if backend not ready)
- Auto-refresh working (30-second interval)
- Charts rendering correctly

**Testing**:
- Unit tests: Chart data transformation
- E2E test: Dashboard loads, metrics displayed

---

### Phase 2: Core Features (Week 2)

#### Sprint 2.1: Analysis Wizard (Days 8-9)

**Tasks**:
- [ ] Build New Analysis Wizard page (`routes/analyze/+page.svelte`)
  - [ ] Multi-step form (3 steps: Connection, Config, Review)
  - [ ] Step 1: Database connection form (host, port, service, username, password)
    - [ ] "Test Connection" button (validates before proceeding)
    - [ ] Save connection checkbox
    - [ ] Load saved connection dropdown
  - [ ] Step 2: Analysis configuration
    - [ ] Min confidence slider (0.0-1.0)
    - [ ] Pattern detector checkboxes
    - [ ] Advanced settings (collapsible accordion)
  - [ ] Step 3: Review summary
    - [ ] Display all selections
    - [ ] "Run Analysis" button
- [ ] Create form validation (client-side + highlight errors)
- [ ] Implement wizard navigation (next, back, submit)
- [ ] Backend: Add POST /api/v1/connections/test endpoint
- [ ] Backend: Add GET/POST /api/v1/connections endpoints

**Deliverables**:
- Analysis wizard functional (3 steps)
- Connection test working
- Form validation preventing invalid submissions
- Redirects to session detail on submit

**Testing**:
- Unit tests: Form validation rules
- E2E test: Complete wizard flow, create analysis

---

#### Sprint 2.2: Analysis Session Detail & Progress (Days 10-11)

**Tasks**:
- [ ] Build Session Detail page (`routes/sessions/[id]/+page.svelte`)
  - [ ] Session metadata (ID, date, database, duration, status)
  - [ ] Workload summary panel
  - [ ] Pattern distribution chart
  - [ ] Recommendations table (embedded)
  - [ ] Action buttons (export, re-run, delete)
- [ ] Create AnalysisProgress component (multi-stage progress bar)
  - [ ] Stage indicators (AWR → Feature Engineering → Pattern Detection → Cost Calculation → Recommendations)
  - [ ] Status badges (pending, in_progress, completed, failed)
  - [ ] Elapsed time / Estimated time remaining
  - [ ] Cancel button (with confirmation modal)
- [ ] Implement polling for in-progress sessions (every 2 seconds)
- [ ] Backend: Add POST /api/v1/sessions/{id}/cancel endpoint
- [ ] Backend: Enhance GET /api/v1/sessions/{id} to include progress info

**Deliverables**:
- Session detail page showing complete analysis info
- Real-time progress updates (polling)
- Cancel analysis working

**Testing**:
- Unit tests: Progress percentage calculation
- E2E test: Start analysis, watch progress, cancel

---

#### Sprint 2.3: Analysis History (Days 12)

**Tasks**:
- [ ] Build Analysis History page (`routes/sessions/+page.svelte`)
  - [ ] Data table (sortable, filterable)
  - [ ] Filter panel (date range, status, database)
  - [ ] Search bar (by ID or database name)
  - [ ] Pagination (20 per page)
  - [ ] Click row to navigate to session detail
- [ ] Implement table sorting (client-side)
- [ ] Implement filtering (client-side, future: server-side)
- [ ] Backend: Enhance GET /api/v1/sessions with pagination, sorting, filtering

**Deliverables**:
- Analysis history page with working table
- Sorting and filtering functional
- Pagination working

**Testing**:
- Unit tests: Filter logic, sort logic
- E2E test: Filter by status, sort by date

---

#### Sprint 2.4: Recommendations List (Days 13-14)

**Tasks**:
- [ ] Build Recommendations List page (`routes/recommendations/+page.svelte`)
  - [ ] Data table (multi-select checkboxes)
  - [ ] Filter panel (priority, pattern type, severity, status)
  - [ ] Sort controls (priority score, annual savings, confidence)
  - [ ] Bulk actions toolbar (change status, export, compare)
  - [ ] Click row to view detail
- [ ] Create RecommendationCard component (for list view)
- [ ] Implement bulk status update
- [ ] Implement multi-select comparison (redirect to compare page)
- [ ] Backend: Add GET /api/v1/recommendations (cross-session, filterable)
- [ ] Backend: Add PATCH /api/v1/recommendations/{id} (update status)

**Deliverables**:
- Recommendations list page functional
- Filtering and sorting working
- Bulk actions (status update, comparison) working

**Testing**:
- Unit tests: Filter/sort logic, bulk selection
- E2E test: Select multiple, change status, compare

---

### Phase 3: Advanced Features (Week 3)

#### Sprint 3.1: Recommendation Detail (Days 15-16)

**Tasks**:
- [ ] Build Recommendation Detail page (`routes/recommendations/[id]/+page.svelte`)
  - [ ] Header (ID, pattern type, severity badge, priority gauge)
  - [ ] Tabs: Overview, Implementation, Cost/Benefit, Tradeoffs, Alternatives
  - [ ] Overview tab: Description, impact analysis
  - [ ] Implementation tab: SQL code (syntax highlighted, copy button), rollback SQL, testing checklist
  - [ ] Cost/Benefit tab: Charts (ROI gauge, savings bar chart), metrics table
  - [ ] Tradeoffs tab: Tradeoffs table with justifications
  - [ ] Alternatives tab: Comparison table (pros/cons)
  - [ ] Action buttons: Approve, Reject (with reason modal), Defer (with date picker), Export
- [ ] Create SyntaxHighlighter component (Prism.js or Highlight.js)
- [ ] Create ROIGauge component (Chart.js gauge/doughnut chart)
- [ ] Backend: Already exists GET /api/v1/recommendations/{analysis_id}/{rec_id}

**Deliverables**:
- Recommendation detail page with all sections
- SQL syntax highlighting working
- Status change (approve/reject) working

**Testing**:
- E2E test: View recommendation, approve, verify status updated

---

#### Sprint 3.2: Recommendation Comparison (Days 17)

**Tasks**:
- [ ] Build Comparison page (`routes/recommendations/compare/+page.svelte`)
  - [ ] Query params: ?ids=rec1,rec2,rec3
  - [ ] Side-by-side table (2-4 recommendations)
  - [ ] Highlight differences (color-coded cells)
  - [ ] Show SQL side-by-side (split view)
  - [ ] Bulk actions (approve all, reject all)
  - [ ] Export comparison to PDF
- [ ] Implement difference highlighting logic
- [ ] Backend: Add GET /api/v1/recommendations/{ids}?compare=true

**Deliverables**:
- Comparison page functional (2-4 recommendations)
- Differences highlighted
- Export to PDF working

**Testing**:
- E2E test: Select 2 recommendations, compare, export PDF

---

#### Sprint 3.3: Charts & Visualizations (Days 18-19)

**Tasks**:
- [ ] Create CostBenefitScatterPlot component
  - [ ] Chart.js scatter plot (bubble chart)
  - [ ] X-axis: Implementation Cost, Y-axis: Annual Savings
  - [ ] Bubble size: Priority Score, Color: Pattern Type
  - [ ] Click bubble to navigate to recommendation
  - [ ] Interactive legend (toggle pattern types)
- [ ] Create PatternTrendsChart component
  - [ ] Chart.js line chart (patterns over time)
  - [ ] X-axis: Date, Y-axis: Pattern Count
  - [ ] Multiple lines (one per pattern type)
  - [ ] Hover tooltip with exact counts
- [ ] Add charts to Dashboard page
- [ ] Backend: Add GET /api/v1/metrics/pattern-trends?days={n}

**Deliverables**:
- Cost/benefit scatter plot working
- Pattern trends chart working
- Charts integrated into dashboard

**Testing**:
- Unit tests: Chart data transformation
- Visual regression test (optional, Chromatic)

---

#### Sprint 3.4: Configuration Page (Days 20-21)

**Tasks**:
- [ ] Build Configuration page (`routes/config/+page.svelte`)
  - [ ] Tabbed interface (one tab per detector: LOB Cliff, Join Dimension, Document/Relational, Duality View, Global Settings)
  - [ ] Each tab: Range sliders with numeric input, reset to default buttons, help tooltips
  - [ ] Global settings tab: min_total_queries, min_pattern_query_count, etc.
  - [ ] Impact simulation button (shows how many recommendations would change)
  - [ ] Save/Revert buttons (sticky footer)
- [ ] Implement live validation (highlight invalid values)
- [ ] Implement impact simulation (call backend API)
- [ ] Backend: Add GET/PUT /api/v1/config/pattern-detectors
- [ ] Backend: Add POST /api/v1/config/pattern-detectors/simulate

**Deliverables**:
- Configuration page functional
- Impact simulation working
- Save/revert working

**Testing**:
- Unit tests: Validation rules, slider bounds
- E2E test: Change config, simulate impact, save

---

### Phase 4: Polish & Deployment (Week 4)

#### Sprint 4.1: Simulations (Days 22-23)

**Tasks**:
- [ ] Build Simulation Library page (`routes/simulations/+page.svelte`)
  - [ ] Simulation cards (grid layout)
  - [ ] Each card: Name, description, expected patterns, duration, "Run" button
  - [ ] Run simulation modal (connection, duration, scale, cleanup checkbox)
- [ ] Build Simulation Execution page (`routes/simulations/[id]/+page.svelte`)
  - [ ] Multi-stage progress bar (Schema → Data → Workload → Snapshot → Analysis)
  - [ ] Real-time metrics (QPS, elapsed time)
  - [ ] Validation results table (expected vs actual, pass/fail badges)
  - [ ] Cancel button
  - [ ] Export report button
- [ ] Implement polling for simulation status (every 2 seconds)
- [ ] Backend: Add GET /api/v1/simulations
- [ ] Backend: Add POST /api/v1/simulations/{id}/execute
- [ ] Backend: Add GET /api/v1/simulations/{execution_id}/status
- [ ] Backend: Add POST /api/v1/simulations/{execution_id}/cancel

**Deliverables**:
- Simulation library page functional
- Simulation execution with real-time progress
- Validation results displayed

**Testing**:
- E2E test: Run simulation, monitor progress, verify validation

---

#### Sprint 4.2: Notifications & Export (Days 24)

**Tasks**:
- [ ] Implement NotificationBell component
  - [ ] Badge with unread count
  - [ ] Dropdown panel with notifications
  - [ ] Mark as read button
  - [ ] Click notification to navigate to linked resource
- [ ] Create notifications store (polling every 60 seconds)
- [ ] Implement PDF export (using jsPDF or backend-generated PDF)
- [ ] Implement CSV/JSON export (download links)
- [ ] Backend: Add GET /api/v1/notifications
- [ ] Backend: Add PATCH /api/v1/notifications/{id}/read
- [ ] Backend: Add POST /api/v1/export/pdf

**Deliverables**:
- Notifications working (in-app)
- PDF export functional
- CSV/JSON export working

**Testing**:
- E2E test: Trigger notification, mark as read, export PDF

---

#### Sprint 4.3: Error Handling & Loading States (Days 25)

**Tasks**:
- [ ] Implement global error boundary (catch component errors)
- [ ] Create error pages (404, 500, offline)
- [ ] Add loading states to all pages (skeleton screens)
- [ ] Add loading indicators to buttons (spinner on click)
- [ ] Implement toast notifications (success, error messages)
- [ ] Add retry mechanism for failed API calls (3 attempts, exponential backoff)
- [ ] Add offline detection (show banner when connection lost)

**Deliverables**:
- Error handling comprehensive (no crashes)
- Loading states on all async operations
- Toast notifications working

**Testing**:
- E2E test: Simulate network failure, verify retry/error handling

---

#### Sprint 4.4: Testing & Documentation (Days 26-27)

**Tasks**:
- [ ] Write unit tests (target: 70% coverage)
  - [ ] API client (error handling, retries)
  - [ ] Form validation
  - [ ] Data transformation (chart data)
  - [ ] Utility functions (formatters, validators)
- [ ] Write E2E tests (Playwright)
  - [ ] Login flow
  - [ ] Run analysis end-to-end
  - [ ] View recommendations
  - [ ] Change recommendation status
  - [ ] Export PDF
  - [ ] Run simulation
- [ ] Accessibility testing (WAVE tool, manual keyboard navigation)
- [ ] Performance testing (Lighthouse: 90+ score)
- [ ] Write user guide (WEB_CONSOLE_USER_GUIDE.md)
- [ ] Write developer guide (WEB_CONSOLE_DEV_GUIDE.md)
- [ ] Create troubleshooting guide

**Deliverables**:
- Unit tests: 70%+ coverage
- E2E tests: Critical paths covered
- Accessibility: WCAG 2.1 AA compliant
- Performance: Lighthouse score 90+
- Documentation complete

**Testing**:
- Run full test suite: `pnpm test`
- Run E2E tests: `pnpm test:e2e`
- Run accessibility audit
- Run performance audit (Lighthouse)

---

#### Sprint 4.5: Production Build & Deployment (Day 28)

**Tasks**:
- [ ] Configure production build (Vite build optimization)
  - [ ] Minification, tree-shaking, code splitting
  - [ ] Environment variable configuration
  - [ ] Source maps (for debugging)
- [ ] Build production bundle: `pnpm build`
- [ ] Configure FastAPI to serve static files
  ```python
  # src/api/app.py
  from fastapi.staticfiles import StaticFiles

  app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
  ```
- [ ] Test production build locally
- [ ] Create Docker Compose file for deployment
  ```yaml
  version: '3.8'
  services:
    iris-web:
      build:
        context: .
        dockerfile: Dockerfile.web
      ports:
        - "8000:8000"
      environment:
        - ORACLE_HOST=db.example.com
        - ORACLE_PORT=1521
      volumes:
        - ./frontend/dist:/app/frontend/dist
  ```
- [ ] Write deployment guide (DEPLOYMENT.md)
- [ ] Create release notes (CHANGELOG.md)

**Deliverables**:
- Production build created (frontend/dist/)
- FastAPI serving static files correctly
- Docker Compose working
- Deployment guide complete

**Testing**:
- Smoke test: Deploy locally, verify all features working
- Load test: 100 concurrent users (Locust or k6)

---

## 5. Backend API Enhancements

### 5.1 New Endpoints to Implement

**Priority: P0 (Must Have for Phase 1)**

```python
# src/api/endpoints/config.py

@router.get("/config/pattern-detectors")
async def get_pattern_detector_config():
    """Get current pattern detector configuration."""
    # Return PatternDetectorConfig object
    pass

@router.put("/config/pattern-detectors")
async def update_pattern_detector_config(config: PatternDetectorConfigUpdate):
    """Update pattern detector configuration."""
    # Validate, save to database, return updated config
    pass

@router.post("/config/pattern-detectors/simulate")
async def simulate_config_impact(config: PatternDetectorConfigUpdate):
    """Simulate impact of config change on existing recommendations."""
    # Re-run pattern detection with new config on recent sessions
    # Return: { changed_recommendations: [...], severity_changes: {...} }
    pass
```

```python
# src/api/endpoints/connections.py

@router.get("/connections")
async def list_saved_connections(current_user: User):
    """List all saved database connections for current user."""
    pass

@router.post("/connections")
async def create_connection(connection: ConnectionCreate, current_user: User):
    """Save new database connection (password encrypted)."""
    pass

@router.post("/connections/{id}/test")
async def test_connection(id: str):
    """Test database connection (validate credentials)."""
    # Try to connect to Oracle, return success/failure
    pass

@router.delete("/connections/{id}")
async def delete_connection(id: str, current_user: User):
    """Delete saved connection."""
    pass
```

```python
# src/api/endpoints/simulations.py

@router.get("/simulations")
async def list_simulations():
    """List available simulation workloads."""
    # Return: [{ id: "workload-1", name: "E-Commerce", ... }, ...]
    pass

@router.post("/simulations/{id}/execute")
async def execute_simulation(id: str, config: SimulationConfig):
    """Run simulation workload."""
    # Start background task (Celery or asyncio)
    # Return: { execution_id: "sim-exec-123" }
    pass

@router.get("/simulations/{execution_id}/status")
async def get_simulation_status(execution_id: str):
    """Get real-time simulation progress."""
    # Return: { stage: "workload", percent: 45, queries_executed: 2250, ... }
    pass

@router.post("/simulations/{execution_id}/cancel")
async def cancel_simulation(execution_id: str):
    """Cancel running simulation."""
    pass
```

```python
# src/api/endpoints/metrics.py

@router.get("/metrics/summary")
async def get_metrics_summary():
    """Get dashboard metrics summary."""
    # Return: {
    #   total_analyses: 42,
    #   acceptance_rate: 0.35,
    #   total_savings: 125000,
    #   active_analyses: 2
    # }
    pass

@router.get("/metrics/pattern-distribution")
async def get_pattern_distribution():
    """Get pattern type distribution across all sessions."""
    # Return: { LOB_CLIFF: 15, JOIN_DIMENSION: 32, ... }
    pass

@router.get("/metrics/pattern-trends")
async def get_pattern_trends(days: int = 30):
    """Get pattern detection trends over time."""
    # Return: [{ date: "2025-11-22", LOB_CLIFF: 2, JOIN_DIMENSION: 5, ... }, ...]
    pass
```

```python
# src/api/endpoints/notifications.py

@router.get("/notifications")
async def get_notifications(unread: bool = False, current_user: User):
    """Get notifications for current user."""
    pass

@router.patch("/notifications/{id}/read")
async def mark_notification_read(id: str):
    """Mark notification as read."""
    pass

@router.delete("/notifications")
async def clear_notifications(current_user: User):
    """Clear all notifications for current user."""
    pass
```

```python
# src/api/endpoints/auth.py (NEW)

@router.post("/auth/login")
async def login(credentials: LoginRequest):
    """Authenticate user, return JWT token."""
    # Validate username/password
    # Generate JWT token (expires in 8 hours)
    # Return: { token: "eyJ...", user: { id: "...", username: "...", role: "admin" } }
    pass

@router.get("/auth/me")
async def get_current_user(current_user: User):
    """Get current authenticated user."""
    # Return user details from JWT token
    pass
```

### 5.2 Enhanced Endpoints

```python
# src/api/endpoints/sessions.py (ENHANCED)

@router.get("/sessions")
async def list_sessions(
    page: int = 1,
    per_page: int = 20,
    sort: str = "created_at",
    order: str = "desc",
    status: Optional[str] = None,
    database: Optional[str] = None,
):
    """List analysis sessions with pagination, filtering, sorting."""
    # Add pagination: LIMIT per_page OFFSET (page-1)*per_page
    # Add filtering: WHERE status = ? AND database LIKE ?
    # Add sorting: ORDER BY {sort} {order}
    pass

@router.post("/sessions/{id}/cancel")
async def cancel_session(id: str):
    """Cancel running analysis."""
    # Set status = 'cancelled', stop background task
    pass
```

```python
# src/api/endpoints/recommendations.py (ENHANCED)

@router.get("/recommendations")
async def list_all_recommendations(
    priority: Optional[str] = None,
    pattern_type: Optional[str] = None,
    status: Optional[str] = None,
    sort: str = "priority_score",
    order: str = "desc",
):
    """List recommendations across all sessions (filterable, sortable)."""
    # Join across sessions, apply filters
    pass

@router.patch("/recommendations/{id}")
async def update_recommendation(id: str, update: RecommendationUpdate):
    """Update recommendation status or notes."""
    # Allow updating: status, notes, status_updated_by
    pass

@router.get("/recommendations/{ids}")
async def get_multiple_recommendations(ids: str, compare: bool = False):
    """Get multiple recommendations (for comparison)."""
    # Parse comma-separated IDs
    # Return list of recommendations
    # If compare=true, format for side-by-side display
    pass
```

### 5.3 Database Schema (New Tables)

**SQLAlchemy models to create**:

```python
# src/db/models.py

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SavedConnection(Base):
    __tablename__ = "saved_connections"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False)
    name = Column(String(100), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    service = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    password_encrypted = Column(Text, nullable=False)  # AES-256
    is_default = Column(Boolean, default=False)
    tags = Column(JSON, nullable=True)  # ["dev", "prod"]
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False)
    type = Column(String(50), nullable=False)  # analysis_completed, etc.
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    action_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False)
    read_at = Column(DateTime, nullable=True)

class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id = Column(String(36), primary_key=True)
    theme = Column(String(20), default="auto")  # light, dark, auto
    notifications_enabled = Column(Boolean, default=True)
    email_digest = Column(Boolean, default=False)
    default_filters = Column(JSON, nullable=True)
    items_per_page = Column(Integer, default=20)
    updated_at = Column(DateTime, nullable=False)

class ConfigHistory(Base):
    __tablename__ = "config_history"

    id = Column(String(36), primary_key=True)
    config_type = Column(String(50), nullable=False)  # pattern_detectors
    config_data = Column(JSON, nullable=False)
    changed_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False)

class SimulationExecution(Base):
    __tablename__ = "simulation_executions"

    id = Column(String(36), primary_key=True)
    simulation_id = Column(String(50), nullable=False)
    database_connection = Column(JSON, nullable=False)
    config = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False)
    progress_data = Column(JSON, nullable=True)
    validation_results = Column(JSON, nullable=True)
    analysis_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
```

---

## 6. Testing Strategy

### 6.1 Unit Testing (Vitest)

**Target Coverage**: 70%+

**Test Files Structure**:
```
frontend/tests/unit/
├── components/
│   ├── Button.test.ts
│   ├── Card.test.ts
│   └── RecommendationCard.test.ts
├── services/
│   ├── api.test.ts
│   └── auth.test.ts
├── stores/
│   └── sessions.test.ts
└── utils/
    ├── formatters.test.ts
    └── validators.test.ts
```

**Sample Test**:
```typescript
// frontend/tests/unit/services/api.test.ts

import { describe, it, expect, vi } from 'vitest';
import { api } from '$lib/services/api';

describe('API Client', () => {
  it('should add Authorization header when token exists', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: 'test' }),
    });
    global.fetch = mockFetch;
    localStorage.setItem('token', 'test-token');

    await api.get('/test');

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/test',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
        }),
      })
    );
  });

  it('should retry 3 times on transient failure', async () => {
    const mockFetch = vi.fn()
      .mockRejectedValueOnce(new Error('Network error'))
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ ok: true, json: async () => ({ data: 'success' }) });
    global.fetch = mockFetch;

    const result = await api.get('/test');

    expect(mockFetch).toHaveBeenCalledTimes(3);
    expect(result).toEqual({ data: 'success' });
  });
});
```

### 6.2 E2E Testing (Playwright)

**Critical Paths to Test**:

```typescript
// frontend/tests/e2e/analysis.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Analysis Workflow', () => {
  test('should complete full analysis workflow', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="username"]', 'testuser');
    await page.fill('[name="password"]', 'password');
    await page.click('button[type="submit"]');

    // Wait for dashboard
    await expect(page).toHaveURL('/');

    // Start new analysis
    await page.click('text=New Analysis');
    await expect(page).toHaveURL('/analyze');

    // Fill connection form
    await page.fill('[name="host"]', 'localhost');
    await page.fill('[name="port"]', '1521');
    await page.fill('[name="service"]', 'FREEPDB1');
    await page.fill('[name="username"]', 'iris_user');
    await page.fill('[name="password"]', 'password');

    // Test connection
    await page.click('text=Test Connection');
    await expect(page.locator('.alert-success')).toBeVisible();

    // Next step
    await page.click('text=Next');

    // Configure analysis
    await page.click('[name="min_confidence"]');
    await page.fill('[name="min_confidence"]', '0.7');

    // Next step
    await page.click('text=Next');

    // Review and submit
    await page.click('text=Run Analysis');

    // Wait for redirect to session detail
    await expect(page).toHaveURL(/\/sessions\/ANALYSIS-/);

    // Verify progress bar appears
    await expect(page.locator('.progress')).toBeVisible();

    // Wait for completion (or timeout after 60s)
    await expect(page.locator('text=completed')).toBeVisible({ timeout: 60000 });

    // Verify recommendations appear
    await expect(page.locator('.recommendation-card')).toHaveCount(1); // At least 1
  });
});
```

### 6.3 Accessibility Testing

**Tools**:
- **WAVE** (browser extension) - automated accessibility audit
- **axe DevTools** (browser extension) - WCAG compliance checker
- **Manual keyboard navigation** - test all interactive elements with Tab, Enter, Escape

**Checklist**:
- [ ] All images have alt text
- [ ] All form inputs have associated labels
- [ ] Focus indicators visible on all interactive elements
- [ ] Color contrast ratio ≥ 4.5:1 (text) and ≥ 3:1 (UI components)
- [ ] Keyboard navigation works (no mouse required)
- [ ] Screen reader compatibility (test with NVDA or VoiceOver)
- [ ] Heading hierarchy correct (h1 → h2 → h3, no skipping)
- [ ] ARIA labels present on custom components

### 6.4 Performance Testing

**Tools**:
- **Lighthouse** (Chrome DevTools) - automated performance audit
- **WebPageTest** - real-world performance testing
- **Locust** (Python) - load testing

**Targets**:
- Lighthouse Performance Score: ≥90
- First Contentful Paint (FCP): < 1.5s
- Largest Contentful Paint (LCP): < 2.5s
- Time to Interactive (TTI): < 3.5s
- Cumulative Layout Shift (CLS): < 0.1

**Load Testing**:
```python
# tests/load/test_web_console.py

from locust import HttpUser, task, between

class WebConsoleUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login
        response = self.client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "password"
        })
        self.token = response.json()["token"]
        self.client.headers["Authorization"] = f"Bearer {self.token}"

    @task(3)
    def view_dashboard(self):
        self.client.get("/api/v1/metrics/summary")
        self.client.get("/api/v1/metrics/pattern-distribution")

    @task(2)
    def view_sessions(self):
        self.client.get("/api/v1/sessions?page=1&per_page=20")

    @task(1)
    def view_recommendations(self):
        self.client.get("/api/v1/recommendations?sort=priority_score")

# Run: locust -f tests/load/test_web_console.py --users 100 --spawn-rate 10 --host http://localhost:8000
```

---

## 7. Deployment

### 7.1 Development Deployment

```bash
# Terminal 1: Frontend dev server
cd frontend
pnpm dev
# Access: http://localhost:5173

# Terminal 2: Backend API server
cd ..
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
# API: http://localhost:8000/docs
```

### 7.2 Production Deployment

**Build Frontend**:
```bash
cd frontend
pnpm build
# Output: frontend/dist/
```

**FastAPI Configuration**:
```python
# src/api/app.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="IRIS API",
    version="1.0.0",
    docs_url="/api/docs",  # Move Swagger UI to /api/docs
    redoc_url="/api/redoc"
)

# CORS for development (remove in production or configure allowed origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes (existing)
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
# ... include all new routers

# Serve Svelte SPA (MUST be last, catch-all route)
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
```

**Run Production Server**:
```bash
# Install uvicorn with production dependencies
pip install uvicorn[standard] gunicorn

# Run with Gunicorn (production ASGI server)
gunicorn src.api.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -

# Access: http://localhost:8000/
```

### 7.3 Docker Deployment

**Dockerfile**:
```dockerfile
# Dockerfile

# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

# Stage 2: Python backend
FROM python:3.10-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY src/ ./src/

# Copy frontend build from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Expose port
EXPOSE 8000

# Run with Gunicorn
CMD ["gunicorn", "src.api.app:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]
```

**Docker Compose**:
```yaml
# docker-compose.web.yml

version: '3.8'

services:
  iris-web:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ORACLE_HOST=${ORACLE_HOST}
      - ORACLE_PORT=${ORACLE_PORT}
      - ORACLE_SERVICE=${ORACLE_SERVICE}
      - ORACLE_USER=${ORACLE_USER}
      - ORACLE_PASSWORD=${ORACLE_PASSWORD}
      - JWT_SECRET=${JWT_SECRET}
    volumes:
      - ./data:/app/data  # Persistent data (if needed)
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Deployment**:
```bash
# Build and run
docker-compose -f docker-compose.web.yml up -d

# View logs
docker-compose -f docker-compose.web.yml logs -f iris-web

# Stop
docker-compose -f docker-compose.web.yml down
```

---

## 8. Timeline Summary

| Week | Sprint | Deliverable | Status |
|------|--------|-------------|--------|
| **Week 1** | 1.1 | Project initialization, Tailwind CSS setup | 🟢 Ready |
| | 1.2 | Base UI components, layout, dark mode | 🟢 Ready |
| | 1.3 | API client, auth service, login page | 🟢 Ready |
| | 1.4 | Dashboard page with charts | 🟢 Ready |
| **Week 2** | 2.1 | Analysis wizard (3-step form) | 🟢 Ready |
| | 2.2 | Session detail, real-time progress | 🟢 Ready |
| | 2.3 | Analysis history (table, filters) | 🟢 Ready |
| | 2.4 | Recommendations list, bulk actions | 🟢 Ready |
| **Week 3** | 3.1 | Recommendation detail (tabs, SQL, charts) | 🟢 Ready |
| | 3.2 | Recommendation comparison | 🟢 Ready |
| | 3.3 | Charts (cost/benefit, pattern trends) | 🟢 Ready |
| | 3.4 | Configuration page (pattern detectors) | 🟢 Ready |
| **Week 4** | 4.1 | Simulations (library, execution, validation) | 🟢 Ready |
| | 4.2 | Notifications, PDF/CSV export | 🟢 Ready |
| | 4.3 | Error handling, loading states, toasts | 🟢 Ready |
| | 4.4 | Testing (unit 70%, E2E critical paths) | 🟢 Ready |
| | 4.5 | Production build, Docker, deployment guide | 🟢 Ready |

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **API performance degradation** | Implement pagination (20 items/page), caching (server-side), database indexing |
| **Chart rendering slow with large datasets** | Sample data (max 1000 points), virtual scrolling for tables, lazy loading |
| **Frontend complexity delays timeline** | Start with MVP (P0 features only), defer P2 features to future releases, reuse DaisyUI components |
| **Backend API changes break frontend** | TypeScript types from OpenAPI spec, integration tests, API versioning (/api/v1) |
| **Authentication security issues** | JWT with short expiration (8hrs), HTTPS only, secure cookies (HttpOnly, SameSite), CSRF tokens |

---

## 10. Success Criteria

- [ ] All P0 (Must Have) features implemented and tested
- [ ] Dashboard loads in < 2 seconds
- [ ] Analysis execution works end-to-end (wizard → progress → results)
- [ ] Recommendations viewable, filterable, and exportable
- [ ] Configuration changes save and apply correctly
- [ ] Simulations execute and validate correctly
- [ ] Unit test coverage ≥ 70%
- [ ] E2E tests passing for critical paths
- [ ] WCAG 2.1 AA compliance verified
- [ ] Production deployment successful (Docker Compose)
- [ ] User guide and developer guide published

---

**Document Status**: DRAFT - Ready for Review
**Next Steps**: Review with team, finalize requirements, begin Sprint 1.1
**Approvers**: Product Owner, Tech Lead, UI/UX Designer

---

**End of Implementation Plan**
