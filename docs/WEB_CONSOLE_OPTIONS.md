# IRIS Web Console - Architecture Options Analysis

**Created**: 2025-11-22
**Status**: Research & Planning
**Scope**: Evaluate web console deployment strategies for IRIS

---

## Executive Summary

IRIS currently has a **FastAPI REST API** (Phase 5 complete) that provides programmatic access to all core functionality. This document evaluates four architectural approaches for adding a web-based management console:

1. **Oracle APEX** - Low-code, Oracle-native platform
2. **Oracle Enterprise Manager Plugin** - Deep EM integration
3. **Client-Side SPA** - Modern JavaScript framework with FastAPI
4. **Hybrid Approach** - Standalone web app + EM plugin packaging

**Recommendation**: **Option 4 (Hybrid Approach)** provides maximum flexibility, allowing both standalone deployment and future EM integration while leveraging existing FastAPI infrastructure.

---

## Current State: IRIS API Infrastructure

### What We Have (Phase 5 Complete)

**FastAPI REST API** (`src/api/app.py`):
- ✅ Health check endpoint
- ✅ POST `/api/v1/analyze` - Run workload analysis
- ✅ GET `/api/v1/sessions/{id}` - Get analysis session details
- ✅ GET `/api/v1/sessions` - List all sessions
- ✅ GET `/api/v1/recommendations/{analysis_id}` - Get recommendations
- ✅ GET `/api/v1/recommendations/{analysis_id}/{rec_id}` - Get specific recommendation
- ✅ Pydantic models for validation
- ✅ OpenAPI/Swagger documentation (auto-generated)

**What's Missing**:
- ❌ Web-based UI for non-technical users
- ❌ Visual dashboards for pattern detection trends
- ❌ Interactive recommendation comparison
- ❌ Real-time analysis progress tracking
- ❌ Cost/benefit visualization charts
- ❌ One-click SQL execution for recommendations

---

## Option 1: Oracle APEX (Low-Code Platform)

### Overview

Oracle Application Express (APEX) is Oracle's enterprise low-code platform for building web applications directly on Oracle Database.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│ Browser (Client)                                    │
├─────────────────────────────────────────────────────┤
│ Oracle APEX (Web Server - Oracle REST Data Services)│
├─────────────────────────────────────────────────────┤
│ Oracle Database 23ai                                │
│   ├─> IRIS Schema (tables for sessions, recs)      │
│   ├─> APEX Workspace                               │
│   └─> APEX Applications                            │
└─────────────────────────────────────────────────────┘
```

### Technical Details

**Database Integration**:
- APEX has **native, zero-latency** access to Oracle Database
- SQL Workshop for data manipulation and querying
- Built-in report generation, charts, and dashboards
- No additional middleware layer required

**Development Model**:
- Drag-and-drop page designer
- Declarative framework for complex logic
- Professional business application themes/templates
- Instant preview (no deployment step)

**Data Access**:
- Direct SQL queries against AWR views (DBA_HIST_*)
- Can call PL/SQL procedures
- Can integrate with REST APIs (call IRIS FastAPI endpoints)
- Can store analysis results in Oracle tables

### Pros

✅ **Zero Licensing Cost**: Fully supported, no-cost feature of Oracle Database
✅ **Native Oracle Integration**: Direct access to AWR, DBA views, and IRIS data
✅ **Rapid Development**: Low-code drag-and-drop builder, 10x faster than custom coding
✅ **Enterprise Features**: Built-in authentication, authorization, auditing
✅ **Professional UI**: World-class themes and responsive design templates
✅ **Zero Infrastructure**: Runs entirely within Oracle Database (no Node.js, no containers)
✅ **Oracle Ecosystem Fit**: Natural choice for Oracle shops, familiar to DBAs
✅ **Mobile Support**: Responsive design works on tablets/phones

### Cons

❌ **Vendor Lock-In**: 100% Oracle-specific, no portability
❌ **Limited Customization**: Constrained by APEX framework and templates
❌ **Learning Curve**: APEX-specific knowledge required (not transferable to other projects)
❌ **No Offline Mode**: Requires Oracle Database connection
❌ **Not Standalone**: Cannot run independently of Oracle Database
❌ **Limited Modern UI Libraries**: Cannot use React/Vue component ecosystems
❌ **EM Integration Unclear**: Not obvious how to package as EM plugin

### Implementation Effort

**Estimated Time**: 2-3 weeks

1. **Week 1**: APEX workspace setup, data model design
   - Create APEX workspace in FREEPDB1
   - Design tables for analysis sessions, recommendations
   - Build REST API integration to call FastAPI endpoints
   - Implement authentication/authorization

2. **Week 2**: Core pages development
   - Dashboard (analysis history, pattern trends)
   - Analysis execution page (run new analysis)
   - Recommendations list (filterable, sortable)
   - Recommendation detail page (with SQL preview)

3. **Week 3**: Advanced features
   - Interactive charts (pattern distribution, cost/benefit)
   - Comparison view (side-by-side recommendations)
   - SQL execution (with confirmation/rollback)
   - Export to CSV/PDF

### Deployment

**Requirements**:
- Oracle Database 23ai or 26ai with APEX installed
- Oracle REST Data Services (ORDS) 21.4+
- Database user with APEX workspace privileges

**Deployment Steps**:
1. Create APEX workspace
2. Import application export file (`.sql` file)
3. Configure database connection
4. Assign users to workspace
5. Access via `https://your-db:8080/ords/iris`

---

## Option 2: Oracle Enterprise Manager Plugin

### Overview

Develop IRIS as an Oracle Enterprise Manager plugin using the Extensibility Development Kit (EDK), providing deep integration with Oracle's monitoring infrastructure.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│ Browser (Client)                                    │
├─────────────────────────────────────────────────────┤
│ Oracle Enterprise Manager OMS (Oracle Mgmt Server) │
│   ├─> IRIS Plugin (Java UI Components)             │
│   ├─> WebLogic Server                              │
│   └─> Repository Database                          │
├─────────────────────────────────────────────────────┤
│ Management Agent (on target database)               │
│   └─> IRIS Discovery & Monitoring Plugin           │
├─────────────────────────────────────────────────────┤
│ Target: Oracle Database 23ai                        │
│   └─> AWR, Schema Metadata                         │
└─────────────────────────────────────────────────────┘
```

### Technical Details

**Plugin Components**:
1. **OMS Plugin**: Java UI components, metadata files, deployed to OMS
2. **Discovery Plugin**: Target discovery logic, deployed to Management Agent
3. **Monitoring Plugin**: Metrics collection, AWR integration, deployed to Agent

**Development Stack**:
- **Language**: Java 17+ (required by EM)
- **Build Tool**: Maven or Gradle
- **UI Framework**: Oracle ADF (Application Development Framework) or JavaScript
- **Packaging**: EDK tools (`empdk`) for plugin packaging
- **Deployment**: Software Library → OMS deployment

**EM Extensibility Framework**:
- Provides support for packaging and deploying metadata
- Deploys to OMS, Management Agent, or both
- Lifecycle management (install, upgrade, uninstall)
- Automatic integration with EM console navigation

### Pros

✅ **Deep EM Integration**: Native look-and-feel, integrated navigation
✅ **Centralized Management**: Manage IRIS alongside other EM targets
✅ **Enterprise Deployment**: Push updates to all agents from central OMS
✅ **Unified Monitoring**: Correlate IRIS recommendations with EM metrics
✅ **Role-Based Access**: Leverage EM's existing RBAC and authentication
✅ **Cross-Database Visibility**: Analyze multiple databases from single console
✅ **AWR Warehouse Integration**: Access centralized historical performance data
✅ **Enterprise Credibility**: EM plugin status elevates IRIS to enterprise-grade tool

### Cons

❌ **Complex Development**: Java + EM EDK learning curve, 3-6 months development time
❌ **Requires EM Infrastructure**: Cannot use without Enterprise Manager deployment
❌ **Limited User Base**: Only organizations with EM can use (not all Oracle shops have EM)
❌ **Restrictive Framework**: Must conform to EM UI patterns and navigation
❌ **Deployment Overhead**: Requires OMS deployment, agent updates, restart cycles
❌ **Testing Complexity**: Requires full EM environment for development/testing
❌ **Not Standalone**: No independent deployment option
❌ **Slower Iteration**: Change → Package → Deploy → Restart cycle vs instant web app updates

### Implementation Effort

**Estimated Time**: 3-6 months (significant undertaking)

1. **Month 1-2**: EDK setup and plugin skeleton
   - Install Oracle EM 24ai or 24.1
   - Download EDK (13.1.0.0.0_edk_partner.zip)
   - Study reference implementations
   - Build plugin skeleton (metadata, discovery, monitoring)
   - Packaging with empdk tools

2. **Month 2-3**: Core functionality
   - Target discovery (identify IRIS-compatible databases)
   - AWR data collection via Management Agent
   - Pattern detection integration
   - Recommendation storage in EM repository

3. **Month 3-4**: UI development
   - Java UI components or JavaScript pages
   - Analysis dashboard
   - Recommendations view
   - SQL execution integration

4. **Month 4-6**: Testing, deployment, documentation
   - Integration testing with EM 24ai
   - Multi-database testing
   - Plugin deployment procedures
   - User documentation

### Deployment

**Requirements**:
- Oracle Enterprise Manager 13c, 24.1, or 24ai
- Management Agents on target databases
- Software Library for plugin distribution
- EM administrator privileges

**Deployment Steps**:
1. Upload plugin to Software Library
2. Deploy plugin to OMS (requires OMS restart)
3. Deploy discovery plugin to Management Agents
4. Add database targets
5. Configure IRIS monitoring
6. Access via EM console → Targets → Databases → IRIS tab

---

## Option 3: Client-Side SPA (Modern JavaScript + FastAPI)

### Overview

Build a modern single-page application (SPA) using Vue.js, React, or Svelte, served as static files by FastAPI. This leverages the existing REST API.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│ Browser (Client)                                    │
│   ├─> Vue.js/React/Svelte SPA (static files)       │
│   └─> JavaScript (API calls to FastAPI)            │
├─────────────────────────────────────────────────────┤
│ FastAPI Server (Python)                             │
│   ├─> Serve Static Files (dist/)                   │
│   ├─> REST API Endpoints (/api/v1/*)               │
│   └─> IRIS Pipeline Orchestrator                   │
├─────────────────────────────────────────────────────┤
│ Oracle Database 23ai                                │
│   └─> AWR, Schema Metadata                         │
└─────────────────────────────────────────────────────┘
```

### Framework Comparison

| Framework | Bundle Size | Performance | Learning Curve | Ecosystem | 2025 Status |
|-----------|-------------|-------------|----------------|-----------|-------------|
| **Svelte** | **Smallest** (1/10th of React) | **Fastest** (no virtual DOM) | Easy (intuitive) | Growing | **Best for speed** |
| **Vue.js** | Small | Fast | **Easiest** | Large | **Best for beginners** |
| **React** | Large | Good | Moderate | **Largest** | **Best for libraries** |

**Recommendation**: **Svelte** for IRIS
- Smallest bundle (critical for mobile users)
- Fastest rendering (real-time dashboard updates)
- Least boilerplate code
- Modern, compile-time optimization
- Growing ecosystem (sufficient for IRIS needs)

### Technical Details

**Frontend Stack**:
- **Framework**: Svelte 5.x (or Vue 3.x as alternative)
- **Build Tool**: Vite (fast HMR, optimized builds)
- **UI Components**: Tailwind CSS + DaisyUI (or ShadCN for Svelte)
- **Charts**: Chart.js or D3.js for visualization
- **HTTP Client**: Fetch API (native) or Axios
- **State Management**: Svelte stores (built-in) or Pinia (Vue)
- **Routing**: SvelteKit routing or Vue Router

**Backend Integration**:
```python
# src/api/app.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Serve SPA static files
app.mount("/", StaticFiles(directory="dist", html=True), name="static")

# Existing API routes remain unchanged
@app.post("/api/v1/analyze")
async def analyze(...):
    ...
```

### Pros

✅ **Modern UX**: Cutting-edge UI/UX with rich component libraries
✅ **Standalone Deployment**: No Oracle Database required for UI (only API backend)
✅ **Flexible Hosting**: Deploy to any web server (Vercel, Netlify, AWS S3, etc.)
✅ **Portable**: Can connect to any IRIS backend (dev, staging, prod)
✅ **Developer Experience**: Hot module replacement, fast iteration cycles
✅ **Ecosystem**: Access to thousands of npm packages (charts, tables, forms)
✅ **Mobile Responsive**: Modern frameworks are mobile-first by default
✅ **Offline Capable**: Service workers enable progressive web app (PWA) features
✅ **FastAPI Integration**: Existing API works without modification
✅ **Open Source**: No vendor lock-in, transferable skills

### Cons

❌ **Requires Build Step**: Must compile SPA before deployment (Vite build)
❌ **JavaScript Complexity**: Modern JS tooling has steep learning curve
❌ **Client-Side Only**: Cannot access Oracle Database directly (must go through API)
❌ **No Direct AWR Access**: All data must be fetched via FastAPI (adds latency)
❌ **Deployment Overhead**: Need web server + FastAPI server (2 components)
❌ **Not Oracle Native**: Doesn't feel like "Oracle product" to DBAs

### Implementation Effort

**Estimated Time**: 3-4 weeks

1. **Week 1**: Project setup and core pages
   - Initialize Svelte + Vite project
   - Configure Tailwind CSS + DaisyUI
   - Implement routing (dashboard, analysis, recommendations)
   - Create API client service (fetch wrapper)
   - Build dashboard page (analysis history cards)

2. **Week 2**: Analysis and recommendations
   - Analysis execution form (database connection input)
   - Real-time analysis progress (polling or WebSocket)
   - Recommendations list (filterable by priority/pattern type)
   - Recommendation detail view (SQL preview, cost/benefit)

3. **Week 3**: Visualizations and advanced features
   - Chart.js integration (pattern distribution pie chart)
   - Cost vs benefit scatter plot
   - Comparison view (side-by-side recommendations)
   - Export to CSV/JSON
   - Dark mode toggle

4. **Week 4**: Polish and deployment
   - Error handling and loading states
   - Responsive design testing (mobile, tablet)
   - Production build optimization
   - FastAPI static file serving configuration
   - Deployment documentation

### Code Example

**Svelte Component** (Analysis Dashboard):
```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from './services/api';

  let sessions = [];
  let loading = true;

  onMount(async () => {
    try {
      sessions = await api.getSessions();
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      loading = false;
    }
  });
</script>

<div class="container mx-auto p-6">
  <h1 class="text-3xl font-bold mb-6">Analysis History</h1>

  {#if loading}
    <div class="loading loading-spinner loading-lg"></div>
  {:else if sessions.length === 0}
    <p class="text-gray-500">No analysis sessions yet.</p>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each sessions as session}
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <h2 class="card-title">{session.analysis_id}</h2>
            <p>Created: {new Date(session.created_at).toLocaleString()}</p>
            <p>Patterns: {session.patterns_detected || 'N/A'}</p>
            <div class="card-actions justify-end">
              <a href="/sessions/{session.analysis_id}" class="btn btn-primary">View</a>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
```

### Deployment

**Development**:
```bash
cd frontend
npm run dev  # Vite dev server on http://localhost:5173
```

**Production**:
```bash
# Build SPA
cd frontend
npm run build  # Output: dist/

# Copy to FastAPI static directory
cp -r dist/* ../src/api/static/

# Run FastAPI server
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

**Access**: `http://localhost:8000/`

---

## Option 4: Hybrid Approach (Recommended)

### Overview

Build a **standalone web console** (Option 3) that can **also be packaged as an Oracle EM plugin** (Option 2) for organizations with Enterprise Manager.

This provides maximum flexibility:
- Standalone deployment for users without EM
- EM plugin for enterprise customers with existing EM infrastructure
- Single codebase maintained for both deployment modes

### Architecture

**Standalone Mode**:
```
Browser → FastAPI (static files + REST API) → Oracle Database
```

**EM Plugin Mode**:
```
Browser → EM OMS → IRIS Plugin (iframe to FastAPI) → Oracle Database
         ↓
    Management Agent (discovery/monitoring)
```

### Technical Strategy

**Phase 1: Standalone Web Console** (Weeks 1-4)
1. Build Svelte SPA with Tailwind CSS (Option 3)
2. Integrate with existing FastAPI REST API
3. Deploy as FastAPI static file serving
4. **Deliverable**: Fully functional standalone web console

**Phase 2: EM Plugin Wrapper** (Weeks 5-8)
1. Create EM plugin metadata (XML files)
2. Develop Java plugin skeleton (discovery, monitoring)
3. Embed Svelte SPA in EM plugin (iframe or URL redirect)
4. Package with empdk tools
5. **Deliverable**: EM plugin that launches IRIS web console

### How EM Integration Works

**Approach A: Embedded iframe**
- EM plugin contains iframe pointing to FastAPI URL
- Click "IRIS" in EM console → iframe opens with web console
- Web console connects to FastAPI backend

**Approach B: Launcher Link**
- EM plugin adds menu item: "Launch IRIS Console"
- Clicking launches new browser tab with web console
- Simpler than iframe, less EM integration work

**Approach C: Full Rewrite**
- Rebuild UI components using Oracle ADF (EM's Java UI framework)
- Most integrated but most expensive (3-6 months)
- Not recommended for initial version

### Pros

✅ **Best of Both Worlds**: Standalone flexibility + EM integration option
✅ **Incremental Complexity**: Build simple first, add EM later
✅ **Market Reach**: Serve both EM users and non-EM users
✅ **Single Codebase**: One web console for both deployment modes
✅ **Risk Mitigation**: If EM integration fails, standalone still works
✅ **Phased Development**: Can ship standalone version immediately
✅ **Future-Proof**: EM plugin can be optional add-on

### Cons

❌ **Dual Maintenance**: Must maintain both standalone and EM plugin
❌ **Testing Overhead**: Test both deployment modes
❌ **EM Limitations**: iframe approach has navigation constraints
❌ **Longer Timeline**: 8 weeks vs 3-4 weeks for standalone only

### Implementation Effort

**Total Time**: 8 weeks

**Phase 1 (Weeks 1-4)**: Standalone Web Console
- Same as Option 3 (Svelte SPA + FastAPI)

**Phase 2 (Weeks 5-8)**: EM Plugin Wrapper
- Week 5: EM plugin skeleton (discovery, metadata)
- Week 6: iframe integration or launcher link
- Week 7: Packaging and deployment testing
- Week 8: Documentation and deployment guide

### Deployment Modes

**Mode 1: Standalone** (No EM)
```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
# Access: http://localhost:8000/
```

**Mode 2: EM Plugin** (With EM)
1. Deploy plugin to OMS via Software Library
2. Add database targets
3. EM console shows "IRIS" tab
4. Clicking tab opens iframe with web console
5. Web console connects to FastAPI backend (separate process)

---

## Detailed Comparison Matrix

| Criteria | APEX | EM Plugin | SPA (Svelte) | Hybrid |
|----------|------|-----------|--------------|--------|
| **Development Time** | 2-3 weeks | 3-6 months | 3-4 weeks | 8 weeks |
| **Developer Skill Required** | APEX/PL/SQL | Java, EM EDK | JavaScript, Svelte | JS + Java basics |
| **Standalone Deployment** | ❌ No (requires Oracle DB) | ❌ No (requires EM) | ✅ Yes | ✅ Yes |
| **EM Integration** | ⚠️ Unclear | ✅ Native | ❌ No | ✅ Yes (Phase 2) |
| **Oracle Ecosystem Fit** | ✅ Excellent | ✅ Excellent | ⚠️ Moderate | ✅ Good |
| **Modern UI/UX** | ⚠️ Good (APEX themes) | ⚠️ Constrained by EM | ✅ Excellent | ✅ Excellent |
| **Customization** | ⚠️ Limited | ❌ Very limited | ✅ Unlimited | ✅ Unlimited |
| **Maintenance Burden** | ⚠️ Moderate | ❌ High | ✅ Low | ⚠️ Moderate |
| **Portability** | ❌ Oracle-only | ❌ Oracle-only | ✅ Portable | ⚠️ Partial |
| **Mobile Support** | ✅ Yes (responsive) | ⚠️ Limited | ✅ Yes (PWA capable) | ✅ Yes |
| **Cost** | ✅ $0 (DB feature) | ✅ $0 (EM feature) | ✅ $0 (open source) | ✅ $0 |
| **FastAPI Integration** | ⚠️ Via REST calls | ⚠️ Complex | ✅ Native | ✅ Native |
| **Time to Market** | ✅ Fast (2-3 weeks) | ❌ Slow (3-6 months) | ✅ Fast (3-4 weeks) | ⚠️ Medium (8 weeks) |
| **Risk Level** | ⚠️ Vendor lock-in | ❌ High complexity | ✅ Low | ⚠️ Medium |

---

## Recommendation: Hybrid Approach (Option 4)

### Why Hybrid?

1. **Maximum Flexibility**: Serve both EM and non-EM users
2. **Phased Development**: Ship standalone version first, add EM plugin later
3. **Risk Mitigation**: If EM plugin fails, standalone still delivers value
4. **Market Coverage**: Appeal to wider audience (not just EM shops)
5. **Modern UX**: Leverage Svelte ecosystem for best-in-class UI
6. **FastAPI Synergy**: Builds on existing Phase 5 investment

### Implementation Roadmap

**Phase 1: Standalone Web Console** (Weeks 1-4) - **Priority 1**

**Sprint 1 (Week 1)**:
- ✅ Initialize Svelte + Vite project
- ✅ Configure Tailwind CSS + DaisyUI
- ✅ Implement routing (/, /analyze, /sessions/:id, /recommendations/:id)
- ✅ Create API client service (fetch wrapper with error handling)
- ✅ Build dashboard page (analysis history cards)

**Sprint 2 (Week 2)**:
- ✅ Analysis execution form (database connection, min_confidence slider)
- ✅ Real-time progress indicator (polling /api/v1/sessions/{id})
- ✅ Recommendations list page (filterable, sortable)
- ✅ Recommendation detail page (description, SQL, cost/benefit)

**Sprint 3 (Week 3)**:
- ✅ Chart.js integration (pattern distribution pie chart, cost scatter plot)
- ✅ Comparison view (select multiple recommendations, side-by-side)
- ✅ Export functionality (CSV, JSON download)
- ✅ Dark mode toggle (Tailwind CSS dark: classes)

**Sprint 4 (Week 4)**:
- ✅ Error handling (API failures, network errors)
- ✅ Loading states (skeletons, spinners)
- ✅ Responsive design testing (mobile, tablet)
- ✅ FastAPI static file serving configuration
- ✅ Production build optimization (Vite --minify)

**Deliverable**: Fully functional standalone web console at http://localhost:8000/

**Phase 2: EM Plugin Wrapper** (Weeks 5-8) - **Priority 2** (Optional)

**Sprint 5 (Week 5)**:
- ✅ Install Oracle EM 24ai development environment
- ✅ Download EM EDK (13.1.0.0.0_edk_partner.zip)
- ✅ Create plugin skeleton (metadata XML, discovery scripts)
- ✅ Study reference implementations

**Sprint 6 (Week 6)**:
- ✅ Implement iframe integration (embed Svelte SPA in EM UI)
- ✅ Configure plugin navigation (menu item, tab)
- ✅ Test URL passing (database connection context from EM to SPA)

**Sprint 7 (Week 7)**:
- ✅ Package plugin with empdk tools
- ✅ Deploy to test EM environment
- ✅ Integration testing (discovery, navigation, iframe loading)

**Sprint 8 (Week 8)**:
- ✅ Documentation (EM plugin installation guide)
- ✅ User guide (EM-specific workflows)
- ✅ Troubleshooting guide
- ✅ Release packaging

**Deliverable**: EM plugin (.opar file) for deployment to Enterprise Manager

---

## Technology Stack (Recommended)

### Frontend (Svelte SPA)
- **Framework**: Svelte 5.x
- **Build Tool**: Vite 6.x
- **Language**: TypeScript (type safety)
- **UI Library**: Tailwind CSS 3.x + DaisyUI 4.x
- **Charts**: Chart.js 4.x (simple, performant)
- **HTTP Client**: Native fetch API
- **State Management**: Svelte stores (built-in)
- **Routing**: SvelteKit or svelte-routing

### Backend (Existing)
- **API**: FastAPI 0.115+ (already implemented)
- **Static Serving**: FastAPI StaticFiles (serves Svelte dist/)
- **Python**: 3.10+

### Development Tools
- **Package Manager**: npm or pnpm
- **Linting**: ESLint + Prettier
- **Type Checking**: TypeScript compiler
- **Testing**: Vitest (unit) + Playwright (E2E)

### Optional (EM Plugin)
- **Language**: Java 17+
- **Build Tool**: Maven
- **Packaging**: EM EDK empdk tools

---

## File Structure (Hybrid Approach)

```
iris/
├── frontend/                    # Svelte SPA (NEW)
│   ├── src/
│   │   ├── routes/
│   │   │   ├── +page.svelte           # Dashboard
│   │   │   ├── analyze/+page.svelte   # Run analysis
│   │   │   └── sessions/
│   │   │       └── [id]/+page.svelte  # Session detail
│   │   ├── lib/
│   │   │   ├── components/            # Reusable UI components
│   │   │   ├── services/
│   │   │   │   └── api.ts             # API client wrapper
│   │   │   └── stores/                # Svelte stores
│   │   └── app.html
│   ├── static/                        # Public assets (images, icons)
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── package.json
│   └── tsconfig.json
│
├── src/
│   ├── api/
│   │   └── app.py                     # FastAPI (existing, add static files)
│   ├── cli/                           # Existing CLI
│   ├── recommendation/                # Existing pattern detection
│   ├── pipeline/                      # Existing orchestrator
│   └── services/                      # Existing analysis service
│
├── em-plugin/                   # EM Plugin (Phase 2, NEW)
│   ├── metadata/
│   │   ├── plugin.xml                 # Plugin metadata
│   │   └── targets.xml                # Target type definitions
│   ├── discovery/
│   │   └── iris_discovery.sh          # Target discovery script
│   ├── ui/
│   │   └── iris_console_launcher.jsp  # iframe/link to Svelte SPA
│   └── pom.xml                        # Maven build file
│
├── docs/
│   ├── WEB_CONSOLE_GUIDE.md           # User guide for web console
│   └── EM_PLUGIN_GUIDE.md             # EM plugin installation
│
└── README.md
```

---

## Deployment Scenarios

### Scenario 1: Standalone (Dev/Test)

**Use Case**: Developer testing, small deployments, non-EM environments

**Steps**:
```bash
# Build frontend
cd frontend
npm install
npm run build  # Output: dist/

# Copy to FastAPI static directory
mkdir -p src/api/static
cp -r dist/* src/api/static/

# Run FastAPI server
uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# Access web console
open http://localhost:8000/
```

**Users**: Individual DBAs, developers, proof-of-concept

---

### Scenario 2: Production (Docker)

**Use Case**: Production deployment without EM, cloud environments

**Docker Compose**:
```yaml
version: '3.8'

services:
  iris-api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - ORACLE_HOST=db.example.com
      - ORACLE_PORT=1521
      - ORACLE_SERVICE=FREEPDB1
    volumes:
      - ./src:/app/src
      - ./frontend/dist:/app/src/api/static
```

**Users**: Mid-size organizations, cloud deployments, Kubernetes

---

### Scenario 3: EM Plugin (Enterprise)

**Use Case**: Large enterprises with Oracle Enterprise Manager 13c, 24.1, or 24ai

**Steps**:
1. Download IRIS EM plugin (.opar file)
2. Upload to EM Software Library
3. Deploy plugin to OMS (requires OMS restart)
4. Deploy discovery plugin to Management Agents
5. Add database targets
6. Navigate to Targets → Databases → Select database → "IRIS" tab
7. Click "IRIS" tab → iframe opens with Svelte SPA
8. SPA connects to FastAPI backend (running on database server or central server)

**Users**: Fortune 500, large enterprises, complex multi-database environments

---

## Security Considerations

### Authentication & Authorization

**Standalone Mode**:
- Option A: Basic Auth (FastAPI HTTPBasic)
- Option B: JWT tokens (recommended)
- Option C: OAuth 2.0 / OIDC (for SSO)

**EM Plugin Mode**:
- Leverage EM's existing authentication
- Pass EM user session to FastAPI backend
- RBAC: Map EM roles to IRIS permissions

### Data Security

- HTTPS only (TLS 1.3)
- Secure cookies (HttpOnly, SameSite)
- CORS configuration (allow only EM domains in plugin mode)
- SQL injection prevention (parameterized queries, already in place)
- Secrets management (environment variables, Vault integration)

---

## Cost Analysis

| Approach | Development Cost | Hosting Cost | Licensing Cost | Total (Year 1) |
|----------|-----------------|--------------|----------------|----------------|
| **APEX** | 2-3 weeks × $200/hr = $8K-12K | $0 (DB server) | $0 | **$8K-12K** |
| **EM Plugin** | 3-6 months × $200/hr = $96K-192K | $0 (EM server) | $0 | **$96K-192K** |
| **SPA (Svelte)** | 3-4 weeks × $200/hr = $12K-16K | $50/month (cloud) | $0 | **$12.6K-16.6K** |
| **Hybrid** | 8 weeks × $200/hr = $32K | $50/month (cloud) | $0 | **$32.6K** |

**Note**: Assumes $200/hour fully-loaded developer cost (salary, benefits, overhead)

---

## Next Steps

### Immediate (Week 1)

1. **Decision Gate**: Confirm Hybrid Approach with stakeholders
2. **Initialize Frontend Project**: Svelte + Vite + Tailwind CSS
3. **Design UI Mockups**: Dashboard, analysis form, recommendations list
4. **Update FastAPI**: Add static file serving configuration
5. **Create WEB_CONSOLE_GUIDE.md**: User guide and developer setup

### Short-Term (Weeks 2-4)

1. **Implement Core Pages**: Dashboard, analysis, recommendations
2. **API Integration**: Connect Svelte to FastAPI endpoints
3. **Visualizations**: Chart.js integration for pattern trends
4. **Testing**: Unit tests (Vitest), E2E tests (Playwright)
5. **Deployment**: Docker Compose for production

### Medium-Term (Weeks 5-8) - Optional

1. **EM Plugin Research**: Install EM 24ai, download EDK
2. **Plugin Skeleton**: Metadata, discovery scripts
3. **iframe Integration**: Embed Svelte SPA in EM UI
4. **Testing**: EM plugin deployment and integration testing
5. **Documentation**: EM_PLUGIN_GUIDE.md

---

## Conclusion

The **Hybrid Approach** provides the optimal balance of:
- **Speed to Market**: 4 weeks for standalone version
- **Flexibility**: Serves EM and non-EM users
- **Modern UX**: Leverages Svelte ecosystem
- **Risk Mitigation**: Standalone works even if EM plugin fails
- **Investment Protection**: Builds on existing FastAPI infrastructure

**Recommendation**: Proceed with **Phase 1 (Standalone Web Console)** immediately. Evaluate **Phase 2 (EM Plugin)** based on customer demand and EM adoption rates.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-22
**Author**: IRIS Development Team
**Status**: Ready for Review
