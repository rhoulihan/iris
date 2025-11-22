# IRIS Web Console - Detailed Requirements Specification

**Version**: 1.0
**Created**: 2025-11-22
**Status**: Draft for Review
**Scope**: Phase 1 - Standalone Web Console

---

## 1. Executive Summary

### 1.1 Project Overview

IRIS Web Console is a modern, browser-based management interface for the Intelligent Recommendation and Inference System. It provides database administrators, developers, and operations teams with:

- **Visual workload analysis** - Interactive dashboards for pattern detection trends
- **Configuration management** - Centralized tuning of pattern detectors and thresholds
- **Simulation orchestration** - Execute and monitor test workloads
- **Recommendation management** - Review, compare, and approve schema optimizations
- **Real-time monitoring** - Live analysis progress and system metrics

### 1.2 Design Principles (Based on 2024 Best Practices)

1. **Minimalism & Clarity**: Clean interfaces, effective whitespace, focus on critical data
2. **Data Storytelling**: Interactive visualizations with drill-down capabilities
3. **Mobile-First**: Responsive design for tablets and phones
4. **Dark Mode Support**: Reduced eye strain for extended monitoring sessions
5. **Personalization**: Customizable dashboards and preferences
6. **Accessibility**: WCAG 2.1 AA compliance, high-contrast themes

### 1.3 Success Criteria

- ✅ **Time to Insight**: < 30 seconds from login to viewing top recommendations
- ✅ **Analysis Execution**: Start new analysis in ≤ 3 clicks
- ✅ **Performance**: Dashboard loads in < 2 seconds, charts render in < 500ms
- ✅ **Usability**: Non-technical users can execute analysis without training
- ✅ **Reliability**: 99.9% uptime for console (separate from analysis execution)

---

## 2. User Personas & Use Cases

### 2.1 Primary Personas

#### Persona 1: Senior DBA (Database Administrator)
- **Name**: Maria Chen
- **Role**: Senior Oracle DBA at Fortune 500 company
- **Goals**:
  - Proactively identify schema optimization opportunities
  - Validate recommendations before implementing in production
  - Track recommendation acceptance rate and ROI
  - Compare IRIS recommendations across multiple databases
- **Pain Points**:
  - Limited time for manual workload analysis
  - Risk-averse (needs high-confidence recommendations)
  - Requires detailed SQL and rollback plans
- **Technical Proficiency**: Expert (SQL, AWR, EM)

#### Persona 2: Application Developer
- **Name**: David Park
- **Role**: Senior Application Developer
- **Goals**:
  - Understand why queries are slow
  - Get recommendations for schema changes during development
  - Test schema changes in dev environment using simulations
  - Collaborate with DBAs on optimization strategies
- **Pain Points**:
  - Limited database tuning knowledge
  - Needs clear explanations of recommendations
  - Wants to test before requesting DBA changes
- **Technical Proficiency**: Intermediate (SQL, basic database concepts)

#### Persona 3: Operations Engineer
- **Name**: Sarah Johnson
- **Role**: DevOps/SRE Engineer
- **Goals**:
  - Monitor database performance trends
  - Automate workload analysis as part of CI/CD
  - Set up alerts for degrading patterns
  - Generate reports for executive team
- **Pain Points**:
  - Needs API access for automation
  - Wants scheduled analysis runs
  - Requires exportable reports
- **Technical Proficiency**: Advanced (Automation, scripting, monitoring)

### 2.2 Core Use Cases

#### UC-01: Run Ad-Hoc Workload Analysis
**Actor**: DBA
**Precondition**: User has database credentials
**Flow**:
1. User clicks "New Analysis" button
2. System presents database connection form
3. User enters credentials (or selects from saved connections)
4. User sets analysis parameters (min_confidence, detectors to enable)
5. User clicks "Run Analysis"
6. System shows real-time progress indicator
7. System displays results when complete
**Postcondition**: Analysis session saved, recommendations generated

#### UC-02: Review and Compare Recommendations
**Actor**: DBA
**Precondition**: Analysis completed with ≥2 recommendations
**Flow**:
1. User navigates to Recommendations page
2. System displays list (filterable by priority, pattern type)
3. User selects multiple recommendations (checkboxes)
4. User clicks "Compare" button
5. System shows side-by-side comparison (cost, benefit, SQL)
6. User marks recommendations as Approved/Rejected/Deferred
**Postcondition**: Recommendation status updated

#### UC-03: Execute Simulation Workload
**Actor**: Developer
**Precondition**: Simulation workload defined
**Flow**:
1. User navigates to Simulations page
2. User selects workload type (E-Commerce, Inventory, Orders)
3. User configures duration, scale, connection string
4. User clicks "Run Simulation"
5. System executes workload on target database
6. System captures AWR snapshots (begin/end)
7. System automatically runs analysis on simulation data
8. System displays expected vs actual pattern detection results
**Postcondition**: Simulation results saved, validation report generated

#### UC-04: Configure Pattern Detectors
**Actor**: DBA
**Precondition**: User has admin privileges
**Flow**:
1. User navigates to Configuration page
2. System displays current settings (organized by detector)
3. User adjusts thresholds (sliders with live validation)
4. User sees preview of impact ("X recommendations would change severity")
5. User saves configuration
6. System applies to new analyses (existing sessions unchanged)
**Postcondition**: New configuration active

#### UC-05: Monitor Real-Time Analysis Progress
**Actor**: Operations Engineer
**Precondition**: Analysis running
**Flow**:
1. User navigates to active analysis session
2. System shows live progress (AWR collection → Pattern Detection → Cost Calculation)
3. System displays partial results as they become available
4. User can cancel analysis mid-execution
**Postcondition**: User informed of completion or cancellation

#### UC-06: Export Recommendations for Approval
**Actor**: DBA
**Precondition**: Recommendations reviewed
**Flow**:
1. User selects recommendations to export
2. User clicks "Export" button
3. User chooses format (PDF report, CSV data, JSON API)
4. System generates export with:
   - Executive summary
   - Detailed recommendations with SQL
   - Cost/benefit analysis
   - Implementation checklist
5. User downloads file
**Postcondition**: Exportable report generated

---

## 3. Functional Requirements

### 3.1 Dashboard & Home Screen

#### FR-1.1: Overview Dashboard
**Priority**: P0 (Must Have)
**Description**: Display high-level summary of IRIS activity

**Acceptance Criteria**:
- [ ] Shows total analyses run (all-time, last 30 days)
- [ ] Shows recommendation acceptance rate (approved / total)
- [ ] Shows total estimated savings (sum of approved recommendations)
- [ ] Displays recent activity timeline (last 10 sessions)
- [ ] Shows pattern detection distribution (pie chart: LOB Cliff, Join, Document, Duality View)
- [ ] Displays top 3 highest-priority pending recommendations (quick action)
- [ ] Refreshes automatically every 30 seconds for active analyses

**UI Components**:
- Summary cards (4 metrics: analyses, acceptance rate, savings, active)
- Activity feed (scrollable list with timestamps)
- Pattern distribution chart (Chart.js pie chart)
- Quick action cards (top recommendations with "View Details" button)

**Data Sources**:
- GET `/api/v1/sessions` - Analysis history
- GET `/api/v1/recommendations/{id}` - Recommendation details
- GET `/api/v1/metrics/summary` - **NEW API** for aggregate metrics

---

#### FR-1.2: Real-Time Analysis Progress
**Priority**: P0 (Must Have)
**Description**: Show live progress of running analyses

**Acceptance Criteria**:
- [ ] Progress bar shows current stage (AWR Collection → Feature Engineering → Pattern Detection → Cost Calculation → Recommendation Generation)
- [ ] Each stage shows status: Pending, In Progress, Completed, Failed
- [ ] Displays elapsed time and estimated time remaining
- [ ] Shows partial results as they become available (e.g., patterns detected before cost calculation completes)
- [ ] Allows cancellation with confirmation dialog
- [ ] Auto-refreshes every 2 seconds via polling (future: WebSocket)
- [ ] Shows error details if stage fails

**UI Components**:
- Multi-stage progress bar (horizontal stepper)
- Status badges (color-coded: blue=in progress, green=complete, red=failed)
- Cancel button with confirmation modal
- Collapsible error log section

**Data Sources**:
- GET `/api/v1/sessions/{id}` - Poll for status updates
- POST `/api/v1/sessions/{id}/cancel` - **NEW API** for cancellation

---

### 3.2 Analysis Management

#### FR-2.1: New Analysis Wizard
**Priority**: P0 (Must Have)
**Description**: Guided workflow to execute new workload analysis

**Acceptance Criteria**:
- [ ] Step 1: Database Connection
  - [ ] Form fields: Host, Port, Service, Username, Password
  - [ ] "Test Connection" button (validates before proceeding)
  - [ ] Save connection option (encrypted storage, checkbox)
  - [ ] Load saved connection dropdown
- [ ] Step 2: Analysis Configuration
  - [ ] Min confidence slider (0.0 - 1.0, default 0.6)
  - [ ] Pattern detector checkboxes (all enabled by default)
  - [ ] Advanced settings (collapsible):
    - [ ] min_total_queries (default 5000)
    - [ ] min_pattern_query_count (default 50)
    - [ ] snapshot_confidence_min_hours (default 24.0)
  - [ ] Create AWR snapshot checkbox (default: true)
- [ ] Step 3: Review & Execute
  - [ ] Summary of selections
  - [ ] "Run Analysis" button
  - [ ] Redirects to progress page on submit

**UI Components**:
- Multi-step form wizard (3 steps)
- Input validation (client-side + server-side)
- Saved connections dropdown (with edit/delete icons)
- Help tooltips for advanced settings

**Data Sources**:
- POST `/api/v1/analyze` - Execute analysis
- POST `/api/v1/connections/test` - **NEW API** for connection validation
- GET `/api/v1/connections` - **NEW API** for saved connections
- POST `/api/v1/connections` - **NEW API** to save connection

---

#### FR-2.2: Analysis History
**Priority**: P0 (Must Have)
**Description**: View all past analysis sessions

**Acceptance Criteria**:
- [ ] Displays all sessions in reverse chronological order (newest first)
- [ ] Shows: Analysis ID, Created At, Database, Status, Patterns Detected, Duration
- [ ] Filterable by:
  - [ ] Date range (last 7 days, 30 days, 90 days, custom)
  - [ ] Status (completed, failed, in progress)
  - [ ] Database (multi-select if multiple databases analyzed)
- [ ] Sortable by: Date, Duration, Patterns Detected
- [ ] Search by Analysis ID or database name
- [ ] Pagination (20 per page)
- [ ] Click row to view session detail

**UI Components**:
- Data table (sortable, filterable)
- Filter panel (collapsible sidebar)
- Search bar (debounced search)
- Pagination controls

**Data Sources**:
- GET `/api/v1/sessions?page={n}&sort={field}&filter={json}` - **ENHANCED API** with pagination/filtering

---

#### FR-2.3: Analysis Session Detail
**Priority**: P0 (Must Have)
**Description**: Detailed view of single analysis session

**Acceptance Criteria**:
- [ ] Session metadata: ID, created at, database, duration, status
- [ ] Workload summary:
  - [ ] Total queries analyzed
  - [ ] Unique query patterns
  - [ ] Snapshot duration (hours)
- [ ] Pattern detection results:
  - [ ] Count by type (LOB Cliff, Join, Document, Duality View)
  - [ ] Distribution chart
- [ ] List of recommendations (link to recommendation detail)
- [ ] Export button (PDF, CSV, JSON)
- [ ] Re-run analysis button (pre-fills wizard with same settings)
- [ ] Delete session button (with confirmation)

**UI Components**:
- Session header (metadata cards)
- Workload summary panel
- Pattern distribution chart (bar or pie)
- Recommendations table (embedded)
- Action buttons (export, re-run, delete)

**Data Sources**:
- GET `/api/v1/sessions/{id}` - Session details
- GET `/api/v1/recommendations/{analysis_id}` - Recommendations for session

---

### 3.3 Recommendation Management

#### FR-3.1: Recommendations List
**Priority**: P0 (Must Have)
**Description**: View and filter all recommendations

**Acceptance Criteria**:
- [ ] Displays all recommendations across all sessions
- [ ] Shows: ID, Pattern Type, Target Object, Severity, Priority, Status, Annual Savings
- [ ] Filterable by:
  - [ ] Priority (HIGH, MEDIUM, LOW)
  - [ ] Pattern Type (LOB_CLIFF, JOIN_DIMENSION, DOCUMENT_RELATIONAL, DUALITY_VIEW)
  - [ ] Severity (HIGH, MEDIUM, LOW)
  - [ ] Status (Pending, Approved, Rejected, Deferred, Implemented)
  - [ ] Analysis Session
- [ ] Sortable by: Priority Score, Annual Savings, Confidence, Created Date
- [ ] Bulk actions:
  - [ ] Select multiple (checkboxes)
  - [ ] Change status (dropdown)
  - [ ] Export selected
  - [ ] Compare selected (up to 4)
- [ ] Click row to view recommendation detail

**UI Components**:
- Data table with multi-select
- Filter panel (collapsible)
- Bulk action toolbar
- Sort controls (column headers)
- Status badges (color-coded)

**Data Sources**:
- GET `/api/v1/recommendations?filter={json}&sort={field}` - **NEW API** for cross-session recommendations
- PATCH `/api/v1/recommendations/{id}` - **NEW API** for status updates

---

#### FR-3.2: Recommendation Detail
**Priority**: P0 (Must Have)
**Description**: Comprehensive view of single recommendation

**Acceptance Criteria**:
- [ ] Header:
  - [ ] Recommendation ID, pattern type icon, severity badge
  - [ ] Target object (table/column)
  - [ ] Status dropdown (editable)
  - [ ] Priority score (visual gauge: 0-100)
- [ ] Description:
  - [ ] Problem statement (what pattern was detected)
  - [ ] Impact analysis (affected queries, performance impact)
- [ ] Recommendation:
  - [ ] Suggested optimization (clear explanation)
  - [ ] Implementation SQL (syntax highlighted, copy button)
  - [ ] Rollback SQL (syntax highlighted, copy button)
  - [ ] Testing approach (step-by-step checklist)
- [ ] Cost/Benefit Analysis:
  - [ ] Annual savings ($/year)
  - [ ] Implementation cost (labor hours, $)
  - [ ] ROI percentage
  - [ ] Payback period (days)
  - [ ] Net benefit score
- [ ] Tradeoffs:
  - [ ] List of tradeoffs (overhead vs benefit)
  - [ ] Justification for each
- [ ] Alternatives:
  - [ ] Alternative approaches (if any)
  - [ ] Pros/cons comparison table
- [ ] Metrics:
  - [ ] Confidence score (0.0-1.0)
  - [ ] Affected queries count
  - [ ] High-frequency query improvement (%)
  - [ ] Low-frequency query impact (%)
- [ ] Actions:
  - [ ] "Approve" button → status = Approved
  - [ ] "Reject" button → opens rejection reason modal
  - [ ] "Defer" button → opens schedule picker
  - [ ] "Execute SQL" button → **Future**: opens SQL execution wizard
  - [ ] "Export" button → PDF/JSON download

**UI Components**:
- Multi-section layout (tabbed or accordion)
- SQL code editor (syntax highlighting, read-only)
- Cost/benefit charts (bar chart, ROI gauge)
- Tradeoffs table
- Action buttons (prominent CTAs)
- Confirmation modals (approve, reject, execute)

**Data Sources**:
- GET `/api/v1/recommendations/{analysis_id}/{rec_id}` - Recommendation details
- PATCH `/api/v1/recommendations/{id}` - Update status
- POST `/api/v1/recommendations/{id}/execute` - **FUTURE API** for SQL execution

---

#### FR-3.3: Recommendation Comparison
**Priority**: P1 (Should Have)
**Description**: Side-by-side comparison of multiple recommendations

**Acceptance Criteria**:
- [ ] Allows selecting 2-4 recommendations from list
- [ ] Displays side-by-side table with:
  - [ ] Pattern Type
  - [ ] Target Object
  - [ ] Severity / Priority
  - [ ] Annual Savings
  - [ ] Implementation Cost
  - [ ] ROI
  - [ ] Confidence
  - [ ] Affected Queries
- [ ] Highlights differences (color-coded cells)
- [ ] Shows implementation SQL side-by-side
- [ ] Allows bulk status change (approve all, reject all)
- [ ] Export comparison to PDF

**UI Components**:
- Comparison table (scrollable, sticky headers)
- Difference highlighting (yellow background)
- Bulk action buttons (above table)
- Export button

**Data Sources**:
- GET `/api/v1/recommendations/{ids}?compare=true` - **NEW API** for comparison view

---

### 3.4 Configuration Management

#### FR-4.1: Pattern Detector Configuration
**Priority**: P0 (Must Have)
**Description**: Adjust pattern detection thresholds

**Acceptance Criteria**:
- [ ] Organized by detector type (tabs or accordion):
  - [ ] LOB Cliff Detector
  - [ ] Join Dimension Analyzer
  - [ ] Document/Relational Classifier
  - [ ] Duality View Opportunity Finder
- [ ] Each detector shows:
  - [ ] Current thresholds (sliders with numeric input)
  - [ ] Default values (reset button)
  - [ ] Description of each parameter (help tooltips)
  - [ ] Live validation (highlight invalid values)
- [ ] Global settings:
  - [ ] min_total_queries (default 5000)
  - [ ] min_pattern_query_count (default 50)
  - [ ] min_table_query_count (default 20)
  - [ ] low_volume_confidence_penalty (0.0-1.0, default 0.3)
  - [ ] snapshot_confidence_min_hours (default 24.0)
- [ ] Impact preview:
  - [ ] "Simulate Impact" button
  - [ ] Shows how many existing recommendations would change severity/priority
  - [ ] Warning if changes are significant (>10% impact)
- [ ] Save/Revert buttons
- [ ] Configuration versioning (dropdown to load previous configs)

**UI Components**:
- Tabbed interface (one tab per detector)
- Range sliders with numeric input
- Reset to default buttons (per parameter, per detector)
- Impact simulation panel (collapsible)
- Save/Cancel buttons (sticky footer)

**Data Sources**:
- GET `/api/v1/config/pattern-detectors` - **NEW API** for current config
- PUT `/api/v1/config/pattern-detectors` - **NEW API** to update config
- POST `/api/v1/config/pattern-detectors/simulate` - **NEW API** for impact simulation
- GET `/api/v1/config/pattern-detectors/history` - **NEW API** for config versions

---

#### FR-4.2: Saved Database Connections
**Priority**: P1 (Should Have)
**Description**: Manage frequently used database connections

**Acceptance Criteria**:
- [ ] List of saved connections (name, host, service, username)
- [ ] Add new connection form
- [ ] Edit connection (update credentials, test connection)
- [ ] Delete connection (with confirmation)
- [ ] Password encrypted at rest (backend responsibility)
- [ ] Default connection (radio button, used in analysis wizard)
- [ ] Connection groups/tags (organize by environment: dev, staging, prod)

**UI Components**:
- CRUD table (create, read, update, delete)
- Add/Edit modal form
- Test connection button (inline validation)
- Delete confirmation dialog
- Tag badges (clickable for filtering)

**Data Sources**:
- GET `/api/v1/connections` - **NEW API**
- POST `/api/v1/connections` - **NEW API**
- PUT `/api/v1/connections/{id}` - **NEW API**
- DELETE `/api/v1/connections/{id}` - **NEW API**
- POST `/api/v1/connections/{id}/test` - **NEW API**

---

#### FR-4.3: User Preferences
**Priority**: P2 (Nice to Have)
**Description**: Personalize console experience

**Acceptance Criteria**:
- [ ] Theme selection (Light, Dark, Auto)
- [ ] Default dashboard widgets (customize which charts appear)
- [ ] Default filters (e.g., always filter to HIGH priority recommendations)
- [ ] Notification preferences (email on analysis completion, daily digest)
- [ ] Time zone selection
- [ ] Export format preference (PDF, CSV, JSON)
- [ ] Items per page (10, 20, 50, 100)

**UI Components**:
- Preferences panel (accessible via user menu)
- Toggle switches, dropdowns, checkboxes
- Save/Cancel buttons

**Data Sources**:
- GET `/api/v1/users/me/preferences` - **NEW API**
- PUT `/api/v1/users/me/preferences` - **NEW API**

---

### 3.5 Simulation Management

#### FR-5.1: Simulation Workload Library
**Priority**: P1 (Should Have)
**Description**: Browse and execute pre-defined simulation workloads

**Acceptance Criteria**:
- [ ] Lists available simulations (cards or table):
  - [ ] Workload 1: E-Commerce (relational → document)
  - [ ] Workload 2: Inventory (document → relational)
  - [ ] Workload 3: Orders (hybrid → duality views)
  - [ ] Future: User-defined workloads
- [ ] Each simulation card shows:
  - [ ] Name and description
  - [ ] Expected patterns to detect
  - [ ] Estimated duration
  - [ ] Schema requirements (tables created)
  - [ ] "Run Simulation" button
- [ ] Click "Run Simulation" opens configuration modal:
  - [ ] Database connection (dropdown from saved connections)
  - [ ] Duration (minutes, default 60)
  - [ ] Scale (small=10K rows, medium=100K, large=1M)
  - [ ] Cleanup after execution (checkbox, default true)

**UI Components**:
- Simulation cards (grid layout)
- Run simulation modal (form)
- Duration slider (1-180 minutes)
- Scale selector (radio buttons)

**Data Sources**:
- GET `/api/v1/simulations` - **NEW API** for simulation catalog
- POST `/api/v1/simulations/{id}/execute` - **NEW API** to run simulation

---

#### FR-5.2: Simulation Execution & Monitoring
**Priority**: P1 (Should Have)
**Description**: Real-time monitoring of running simulations

**Acceptance Criteria**:
- [ ] Shows current stage:
  - [ ] Schema Creation (0-10%)
  - [ ] Data Generation (10-30%)
  - [ ] Workload Execution (30-80%)
  - [ ] AWR Snapshot Collection (80-90%)
  - [ ] Analysis Execution (90-100%)
- [ ] Displays:
  - [ ] Elapsed time / Total time
  - [ ] Queries executed / Total queries
  - [ ] Current QPS (queries per second)
- [ ] Allows cancellation (stops workload, optionally drops schema)
- [ ] On completion:
  - [ ] Shows validation results (expected vs actual patterns detected)
  - [ ] Pass/Fail badge for each expected pattern
  - [ ] Links to generated analysis session
  - [ ] Export simulation report (PDF)

**UI Components**:
- Multi-stage progress bar
- Real-time metrics (auto-refresh every 2 seconds)
- Validation results table (checkmarks/X icons)
- Cancel button
- Export report button

**Data Sources**:
- GET `/api/v1/simulations/{execution_id}/status` - **NEW API** for progress
- POST `/api/v1/simulations/{execution_id}/cancel` - **NEW API**
- GET `/api/v1/simulations/{execution_id}/report` - **NEW API** for validation report

---

#### FR-5.3: Simulation History
**Priority**: P2 (Nice to Have)
**Description**: View past simulation executions

**Acceptance Criteria**:
- [ ] Lists all simulation runs (table)
- [ ] Shows: Workload Type, Database, Duration, Status, Validation Pass/Fail, Created At
- [ ] Filterable by workload type, status, validation result
- [ ] Click row to view detailed validation report
- [ ] Delete simulation run (with confirmation)

**UI Components**:
- Data table (sortable, filterable)
- Validation badge (pass=green, fail=red)
- Delete button (trash icon)

**Data Sources**:
- GET `/api/v1/simulations/executions` - **NEW API** for history
- DELETE `/api/v1/simulations/executions/{id}` - **NEW API**

---

### 3.6 Visualization & Charts

#### FR-6.1: Pattern Distribution Charts
**Priority**: P0 (Must Have)
**Description**: Visualize pattern detection across analyses

**Acceptance Criteria**:
- [ ] Pie chart: Pattern type distribution (LOB Cliff %, Join %, Document %, Duality View %)
- [ ] Bar chart: Patterns detected over time (X-axis: date, Y-axis: count, stacked by type)
- [ ] Drill-down: Click chart segment to filter recommendations
- [ ] Interactive tooltips (hover to see exact counts)
- [ ] Export chart as PNG

**UI Components**:
- Chart.js pie and bar charts
- Click handlers for drill-down
- Export button

**Data Sources**:
- GET `/api/v1/metrics/pattern-distribution` - **NEW API**
- GET `/api/v1/metrics/pattern-trends?days={n}` - **NEW API**

---

#### FR-6.2: Cost/Benefit Scatter Plot
**Priority**: P1 (Should Have)
**Description**: Visualize ROI of recommendations

**Acceptance Criteria**:
- [ ] Scatter plot:
  - [ ] X-axis: Implementation Cost ($)
  - [ ] Y-axis: Annual Savings ($)
  - [ ] Bubble size: Priority Score
  - [ ] Bubble color: Pattern Type
- [ ] Quadrant lines (high savings/low cost = optimal)
- [ ] Click bubble to view recommendation detail
- [ ] Filter by pattern type (legend clickable)
- [ ] Zoom/pan controls

**UI Components**:
- Chart.js scatter plot with bubble chart
- Interactive legend
- Zoom controls

**Data Sources**:
- GET `/api/v1/recommendations?include_metrics=true` - **ENHANCED API**

---

#### FR-6.3: Workload Heatmap
**Priority**: P2 (Nice to Have)
**Description**: Visualize query activity by time of day

**Acceptance Criteria**:
- [ ] Heatmap:
  - [ ] X-axis: Hour of day (0-23)
  - [ ] Y-axis: Day of week (Mon-Sun)
  - [ ] Color intensity: Query volume
- [ ] Helps identify peak workload times
- [ ] Hover tooltip shows exact query count
- [ ] Useful for scheduling maintenance windows

**UI Components**:
- D3.js or Chart.js heatmap
- Color gradient (light=low, dark=high)

**Data Sources**:
- GET `/api/v1/workload/heatmap?analysis_id={id}` - **NEW API**

---

### 3.7 Notifications & Alerts

#### FR-7.1: In-App Notifications
**Priority**: P1 (Should Have)
**Description**: Display important events to user

**Acceptance Criteria**:
- [ ] Notification bell icon (header, shows unread count badge)
- [ ] Click to open notifications panel (dropdown)
- [ ] Notification types:
  - [ ] Analysis completed
  - [ ] High-priority recommendation detected
  - [ ] Configuration changed
  - [ ] Simulation completed
  - [ ] Error occurred
- [ ] Each notification shows:
  - [ ] Icon (color-coded by type)
  - [ ] Title and description
  - [ ] Timestamp (relative: "5 minutes ago")
  - [ ] Action link ("View Analysis", "View Recommendation")
  - [ ] Mark as read button
- [ ] Mark all as read button
- [ ] Clear all button
- [ ] Auto-dismiss after 30 days

**UI Components**:
- Notification bell with badge
- Dropdown panel (scrollable, max 10 recent)
- Notification items (icon, text, actions)

**Data Sources**:
- GET `/api/v1/notifications?unread=true` - **NEW API**
- PATCH `/api/v1/notifications/{id}/read` - **NEW API**
- DELETE `/api/v1/notifications` - **NEW API** (clear all)

---

#### FR-7.2: Email Notifications
**Priority**: P2 (Nice to Have)
**Description**: Send emails for critical events

**Acceptance Criteria**:
- [ ] Configurable via User Preferences
- [ ] Email triggers:
  - [ ] Analysis completed (with summary and link)
  - [ ] High-priority recommendation detected
  - [ ] Simulation validation failed
- [ ] Email template:
  - [ ] IRIS branding
  - [ ] Event summary
  - [ ] Link to console (direct deep link)
  - [ ] Unsubscribe link
- [ ] Daily digest option (single email with all day's events)

**UI Components**:
- Email template (HTML)
- Preference toggles in settings

**Data Sources**:
- Backend service (no frontend API)

---

### 3.8 Export & Reporting

#### FR-8.1: PDF Report Generation
**Priority**: P1 (Should Have)
**Description**: Generate executive-ready PDF reports

**Acceptance Criteria**:
- [ ] Report types:
  - [ ] Single recommendation (detailed)
  - [ ] Analysis session summary (all recommendations)
  - [ ] Executive dashboard (metrics + top 5 recommendations)
  - [ ] Simulation validation report
- [ ] PDF includes:
  - [ ] IRIS logo and branding
  - [ ] Report title and date
  - [ ] Table of contents (multi-page reports)
  - [ ] Charts and visualizations (as images)
  - [ ] SQL code (syntax highlighted)
  - [ ] Footer with page numbers
- [ ] Download or email option

**UI Components**:
- Export button (multiple formats dropdown)
- Email modal (recipient, subject, message)

**Data Sources**:
- POST `/api/v1/export/pdf` - **NEW API** (returns PDF binary)

---

#### FR-8.2: CSV/JSON Export
**Priority**: P1 (Should Have)
**Description**: Export data for external processing

**Acceptance Criteria**:
- [ ] Export recommendations to CSV:
  - [ ] Columns: ID, Pattern Type, Target, Severity, Priority, Savings, Cost, ROI, Status
  - [ ] Optional: include all metrics (extended CSV)
- [ ] Export to JSON:
  - [ ] Full recommendation objects (with nested data)
  - [ ] Useful for API integrations, CI/CD pipelines
- [ ] Batch export (all recommendations from session or filtered list)

**UI Components**:
- Export button (format dropdown: CSV, JSON)
- Download link

**Data Sources**:
- GET `/api/v1/recommendations?format=csv` - **ENHANCED API**
- GET `/api/v1/recommendations?format=json` - **ENHANCED API**

---

## 4. Non-Functional Requirements

### 4.1 Performance

#### NFR-1.1: Page Load Time
- [ ] Dashboard loads in < 2 seconds (initial load, cached assets)
- [ ] Subsequent page navigation < 500ms (SPA routing)
- [ ] Chart rendering < 500ms (up to 100 data points)
- [ ] Table rendering < 1 second (up to 1000 rows)

#### NFR-1.2: API Response Time
- [ ] GET requests: < 200ms (p95)
- [ ] POST requests (analysis execution): < 500ms to acknowledge (async processing)
- [ ] Recommendation list (100 items): < 300ms

#### NFR-1.3: Real-Time Updates
- [ ] Progress polling interval: 2 seconds
- [ ] Dashboard auto-refresh: 30 seconds
- [ ] Notification check: 60 seconds
- [ ] Future: WebSocket for sub-second updates

#### NFR-1.4: Scalability
- [ ] Support 100 concurrent users
- [ ] Handle 10,000 recommendations in UI (with pagination)
- [ ] Handle 1,000 analysis sessions (with pagination)

---

### 4.2 Usability

#### NFR-2.1: Accessibility (WCAG 2.1 AA)
- [ ] Keyboard navigation (tab order, focus indicators)
- [ ] Screen reader compatibility (ARIA labels, semantic HTML)
- [ ] High contrast mode (minimum 4.5:1 ratio)
- [ ] Resizable text (up to 200% without layout breakage)
- [ ] Alt text for all images and charts

#### NFR-2.2: Responsive Design
- [ ] Desktop: 1920x1080 and above (primary)
- [ ] Laptop: 1366x768 minimum
- [ ] Tablet: 768x1024 (portrait and landscape)
- [ ] Mobile: 375x667 minimum (read-only mode, no analysis execution)

#### NFR-2.3: Browser Compatibility
- [ ] Chrome 100+ (primary)
- [ ] Firefox 100+
- [ ] Safari 15+ (macOS, iOS)
- [ ] Edge 100+
- [ ] No IE11 support

#### NFR-2.4: Internationalization (Future)
- [ ] UI text externalized (i18n framework)
- [ ] Initial language: English (US)
- [ ] Future: Spanish, German, Japanese, Chinese

---

### 4.3 Security

#### NFR-3.1: Authentication
- [ ] JWT-based authentication (token stored in secure HttpOnly cookie)
- [ ] Login page with username/password
- [ ] Future: SSO/SAML integration, OAuth 2.0
- [ ] Session timeout: 8 hours (configurable)
- [ ] Auto-logout on browser close

#### NFR-3.2: Authorization
- [ ] Role-based access control (RBAC):
  - [ ] Admin: Full access (configuration, user management)
  - [ ] Analyst: Run analyses, view recommendations, export
  - [ ] Viewer: Read-only (dashboards, recommendations)
- [ ] Future: Fine-grained permissions (per database, per analysis)

#### NFR-3.3: Data Security
- [ ] HTTPS only (TLS 1.3)
- [ ] Database credentials encrypted at rest (AES-256)
- [ ] Secrets management (environment variables, future: HashiCorp Vault)
- [ ] CORS configured (allow only trusted origins)
- [ ] CSRF protection (token validation)
- [ ] Input sanitization (XSS prevention)
- [ ] Parameterized queries (SQL injection prevention - already in backend)

#### NFR-3.4: Audit Logging
- [ ] Log all user actions:
  - [ ] Login/logout
  - [ ] Analysis execution
  - [ ] Configuration changes
  - [ ] Recommendation status changes
  - [ ] Export events
- [ ] Logs include: User ID, Action, Timestamp, IP Address, Resource ID
- [ ] Logs stored for 90 days (configurable)
- [ ] Future: Integration with SIEM (Security Information and Event Management)

---

### 4.4 Reliability

#### NFR-4.1: Availability
- [ ] Console uptime: 99.9% (separate from backend analysis execution)
- [ ] Graceful degradation (show cached data if API unavailable)
- [ ] Error boundaries (prevent full app crash on component error)

#### NFR-4.2: Error Handling
- [ ] User-friendly error messages (no stack traces to user)
- [ ] Detailed errors logged to console (dev mode only)
- [ ] Retry mechanism for transient failures (3 retries with exponential backoff)
- [ ] Offline mode detection ("Connection lost" banner)

#### NFR-4.3: Data Integrity
- [ ] Client-side validation (immediate feedback)
- [ ] Server-side validation (final check)
- [ ] Optimistic UI updates (instant feedback, rollback on failure)
- [ ] Auto-save drafts (analysis configuration, partially filled forms)

---

### 4.5 Maintainability

#### NFR-5.1: Code Quality
- [ ] TypeScript for type safety
- [ ] ESLint + Prettier for consistent formatting
- [ ] Component-based architecture (reusable UI components)
- [ ] Storybook for component documentation (future)

#### NFR-5.2: Testing
- [ ] Unit test coverage: ≥70% (Vitest)
- [ ] E2E tests for critical paths (Playwright):
  - [ ] Login
  - [ ] Run analysis
  - [ ] View recommendations
  - [ ] Export PDF
- [ ] Visual regression tests (Chromatic, future)

#### NFR-5.3: Documentation
- [ ] Component documentation (JSDoc comments)
- [ ] User guide (markdown docs)
- [ ] API integration guide (for developers)
- [ ] Troubleshooting guide

---

## 5. Data Requirements

### 5.1 API Endpoints (New/Enhanced)

#### New Endpoints Required

**Configuration Management**:
- GET `/api/v1/config/pattern-detectors` - Get current configuration
- PUT `/api/v1/config/pattern-detectors` - Update configuration
- POST `/api/v1/config/pattern-detectors/simulate` - Simulate impact of config change
- GET `/api/v1/config/pattern-detectors/history` - Configuration version history

**Saved Connections**:
- GET `/api/v1/connections` - List saved connections
- POST `/api/v1/connections` - Create connection
- PUT `/api/v1/connections/{id}` - Update connection
- DELETE `/api/v1/connections/{id}` - Delete connection
- POST `/api/v1/connections/{id}/test` - Test connection

**Recommendations (Enhanced)**:
- GET `/api/v1/recommendations` - Cross-session recommendations (filter, sort)
- PATCH `/api/v1/recommendations/{id}` - Update status/notes
- GET `/api/v1/recommendations/{ids}?compare=true` - Comparison view

**Simulations**:
- GET `/api/v1/simulations` - List available simulations
- POST `/api/v1/simulations/{id}/execute` - Run simulation
- GET `/api/v1/simulations/{execution_id}/status` - Progress
- POST `/api/v1/simulations/{execution_id}/cancel` - Cancel
- GET `/api/v1/simulations/{execution_id}/report` - Validation report
- GET `/api/v1/simulations/executions` - History
- DELETE `/api/v1/simulations/executions/{id}` - Delete run

**Metrics & Analytics**:
- GET `/api/v1/metrics/summary` - Dashboard aggregates
- GET `/api/v1/metrics/pattern-distribution` - Pattern type counts
- GET `/api/v1/metrics/pattern-trends?days={n}` - Time series
- GET `/api/v1/workload/heatmap?analysis_id={id}` - Query activity heatmap

**Notifications**:
- GET `/api/v1/notifications?unread=true` - Get notifications
- PATCH `/api/v1/notifications/{id}/read` - Mark as read
- DELETE `/api/v1/notifications` - Clear all

**Export**:
- POST `/api/v1/export/pdf` - Generate PDF report
- GET `/api/v1/recommendations?format=csv` - CSV export
- GET `/api/v1/recommendations?format=json` - JSON export

**User Management**:
- GET `/api/v1/users/me/preferences` - User preferences
- PUT `/api/v1/users/me/preferences` - Update preferences

**Session Management (Enhanced)**:
- POST `/api/v1/sessions/{id}/cancel` - Cancel running analysis
- GET `/api/v1/sessions?page={n}&sort={field}&filter={json}` - Pagination, filtering

---

### 5.2 Data Models (Frontend)

#### Analysis Session
```typescript
interface AnalysisSession {
  analysis_id: string;
  created_at: string; // ISO 8601
  database: {
    host: string;
    port: number;
    service: string;
  };
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  duration_seconds: number | null;
  patterns_detected: number | null;
  workload_summary: {
    total_queries: number;
    unique_patterns: number;
    snapshot_duration_hours: number;
  } | null;
  error: string | null;
}
```

#### Recommendation
```typescript
interface Recommendation {
  recommendation_id: string;
  analysis_id: string;
  pattern_type: 'LOB_CLIFF' | 'JOIN_DIMENSION' | 'DOCUMENT_RELATIONAL' | 'DUALITY_VIEW';
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  priority_score: number; // 0-100
  confidence: number; // 0.0-1.0
  target_object: string; // table.column or table
  description: string;
  implementation_sql: string;
  rollback_sql: string;
  testing_approach: string;
  cost_benefit: {
    annual_savings_usd: number;
    implementation_cost_usd: number;
    roi_percentage: number;
    payback_period_days: number;
  };
  metrics: {
    affected_queries: number;
    high_frequency_improvement_pct: number;
    low_frequency_impact_pct: number;
  };
  tradeoffs: Array<{
    description: string;
    justified_by: string;
  }>;
  alternatives: Array<{
    approach: string;
    pros: string[];
    cons: string[];
  }>;
  status: 'pending' | 'approved' | 'rejected' | 'deferred' | 'implemented';
  status_updated_at: string | null;
  status_updated_by: string | null;
  notes: string | null;
}
```

#### Simulation Execution
```typescript
interface SimulationExecution {
  execution_id: string;
  simulation_id: string; // workload-1, workload-2, etc.
  simulation_name: string;
  database: {
    host: string;
    port: number;
    service: string;
  };
  config: {
    duration_minutes: number;
    scale: 'small' | 'medium' | 'large';
    cleanup: boolean;
  };
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  progress: {
    stage: 'schema' | 'data' | 'workload' | 'snapshot' | 'analysis';
    percent: number; // 0-100
    queries_executed: number;
    queries_total: number;
    elapsed_seconds: number;
  } | null;
  validation_results: Array<{
    expected_pattern: string;
    detected: boolean;
    confidence: number;
  }> | null;
  analysis_id: string | null; // linked analysis session
  created_at: string;
  completed_at: string | null;
}
```

#### Notification
```typescript
interface Notification {
  notification_id: string;
  user_id: string;
  type: 'analysis_completed' | 'high_priority_rec' | 'config_changed' | 'simulation_completed' | 'error';
  title: string;
  description: string;
  action_url: string | null; // deep link
  created_at: string;
  read_at: string | null;
}
```

---

## 6. Integration Requirements

### 6.1 Oracle Database Integration

#### Required Permissions
- **AWR Access**: SELECT on DBA_HIST_* views
- **Schema Metadata**: SELECT on DBA_TABLES, DBA_TAB_COLUMNS, DBA_INDEXES, DBA_CONSTRAINTS
- **Snapshot Management**: EXECUTE on DBMS_WORKLOAD_REPOSITORY (for creating snapshots)
- **Simulation Schemas**: CREATE TABLE, DROP TABLE, INSERT, UPDATE, DELETE (in designated schema)

#### Connection Pooling
- [ ] FastAPI backend maintains connection pool (SQLAlchemy)
- [ ] Frontend does NOT connect directly to Oracle (security)
- [ ] All database access via REST API

---

### 6.2 External Integrations (Future)

#### Monitoring Systems
- [ ] Prometheus metrics export (analysis count, recommendation count, error rate)
- [ ] Grafana dashboard templates
- [ ] Alertmanager integration (critical errors)

#### CI/CD Pipelines
- [ ] REST API for automation (already available)
- [ ] CLI tool for scripted analysis (already available)
- [ ] Webhook notifications (future)

#### Collaboration Tools
- [ ] Slack notifications (analysis completed, high-priority recommendations)
- [ ] Microsoft Teams integration
- [ ] JIRA ticket creation (recommendation = ticket)

---

## 7. Constraints & Assumptions

### 7.1 Constraints

- **Technology**: Must use Svelte + FastAPI (as per architecture decision)
- **Budget**: Open-source tools only (no licensed libraries)
- **Timeline**: Phase 1 must complete in 4 weeks
- **Browser Support**: Modern browsers only (no IE11)
- **Backend Dependency**: Requires existing FastAPI to be operational

### 7.2 Assumptions

- **User Base**: 10-100 concurrent users initially
- **Analysis Volume**: 10-50 analyses per day
- **Recommendation Volume**: 100-500 recommendations per analysis
- **Database Count**: 1-10 databases managed initially
- **Network**: Users have reliable internet (no offline mode required)
- **Authentication**: Simple JWT authentication sufficient (no complex SSO initially)

---

## 8. Acceptance Criteria (Overall)

### 8.1 Functional Acceptance

- [ ] All P0 (Must Have) requirements implemented and tested
- [ ] All critical user journeys tested end-to-end:
  - [ ] Login → Run Analysis → View Recommendations → Export PDF
  - [ ] Run Simulation → View Validation Results
  - [ ] Configure Pattern Detectors → Simulate Impact → Save
- [ ] No P0 or P1 bugs remaining
- [ ] User acceptance testing passed (2 DBAs, 1 developer)

### 8.2 Non-Functional Acceptance

- [ ] Performance: Dashboard loads < 2s, API response < 200ms (p95)
- [ ] Security: HTTPS enforced, credentials encrypted, CSRF protection active
- [ ] Accessibility: WCAG 2.1 AA compliance verified (automated + manual testing)
- [ ] Browser Compatibility: Tested on Chrome, Firefox, Safari, Edge
- [ ] Responsive Design: Tested on desktop (1920x1080), laptop (1366x768), tablet (768x1024)

### 8.3 Documentation Acceptance

- [ ] User Guide published (markdown + PDF)
- [ ] API Integration Guide published
- [ ] Troubleshooting Guide published
- [ ] Component documentation complete (JSDoc)

### 8.4 Testing Acceptance

- [ ] Unit test coverage ≥70%
- [ ] E2E tests passing for critical paths
- [ ] Load testing: 100 concurrent users (dashboard remains responsive)
- [ ] Security testing: OWASP Top 10 vulnerabilities checked

---

## 9. Out of Scope (Phase 1)

The following features are explicitly **NOT** included in Phase 1:

- ❌ Oracle Enterprise Manager plugin integration (deferred to Phase 2)
- ❌ Multi-tenant support (single organization only)
- ❌ Advanced RBAC (fine-grained permissions per database)
- ❌ SSO/SAML authentication (basic JWT only)
- ❌ Real-time collaboration (multiple users editing same analysis)
- ❌ Advanced visualization (3D charts, network graphs)
- ❌ Machine learning model retraining UI
- ❌ Mobile apps (iOS, Android native)
- ❌ Offline mode (requires internet connection)
- ❌ Custom workload builder (pre-defined simulations only)
- ❌ SQL execution from UI (view only, not execute)
- ❌ Automated recommendation implementation (manual DBA approval required)
- ❌ A/B testing recommendations (deploy and compare)
- ❌ Cost tracking (actual spend vs estimated savings)

---

## 10. Open Questions & Risks

### 10.1 Open Questions

1. **Authentication**: Do we need LDAP/Active Directory integration, or is JWT sufficient?
2. **Multi-Database**: Should users be able to compare recommendations across databases?
3. **Recommendation Lifecycle**: Do we need workflow states (submitted → reviewed → approved → implemented)?
4. **Alerts**: Should critical recommendations trigger immediate notifications (email, Slack)?
5. **Historical Data**: How long should we retain analysis sessions and recommendations?

### 10.2 Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| API performance degradation with large datasets | Medium | High | Implement pagination, caching, database indexing |
| Complex visualizations impact browser performance | Medium | Medium | Lazy loading, virtual scrolling, chart sampling |
| Users overwhelmed by too many recommendations | Medium | Medium | Intelligent filtering, priority-based sorting, guided workflows |
| Database credentials stored insecurely | Low | High | AES-256 encryption, secure secret management, audit logging |
| Frontend complexity delays timeline | Medium | High | Incremental delivery, MVP-first approach, code reuse |

---

## 11. Success Metrics (Post-Launch)

### 11.1 Adoption Metrics

- [ ] Weekly active users (target: 20+ in first month)
- [ ] Analyses run per week (target: 50+ in first month)
- [ ] Recommendations generated per week (target: 500+)

### 11.2 Engagement Metrics

- [ ] Average session duration (target: 10+ minutes)
- [ ] Recommendations viewed (target: 80% of generated)
- [ ] Recommendations approved (target: 30% acceptance rate)
- [ ] Exports generated (target: 20% of sessions)

### 11.3 Quality Metrics

- [ ] Recommendation accuracy (target: 85% user satisfaction)
- [ ] False positive rate (target: <15%)
- [ ] Time to recommendation (target: <5 minutes from analysis start)

### 11.4 Technical Metrics

- [ ] Dashboard load time (target: <2s, p95)
- [ ] API response time (target: <200ms, p95)
- [ ] Error rate (target: <1%)
- [ ] Uptime (target: 99.9%)

---

**Document Status**: DRAFT - Ready for Review
**Next Steps**: Review with stakeholders, incorporate feedback, finalize requirements
**Approvers**: Product Owner, Lead Developer, Senior DBA

---

**Appendix A: UI Mockup References**

(Placeholder for wireframes and mockups - to be created after requirements approval)

- Dashboard (home screen)
- Analysis wizard (3-step flow)
- Recommendations list (table view)
- Recommendation detail (full page)
- Configuration page (pattern detector settings)
- Simulation execution (progress view)

---

**Appendix B: Glossary**

- **AWR**: Automatic Workload Repository (Oracle performance data)
- **DBA**: Database Administrator
- **Duality View**: Oracle 23ai feature for dual OLTP/Analytics access
- **LOB**: Large Object (CLOB, BLOB)
- **Pattern Detector**: Component that identifies schema anti-patterns
- **ROI**: Return on Investment
- **SPA**: Single Page Application
- **Simulation**: Pre-defined test workload for validation

---

**End of Requirements Document**
