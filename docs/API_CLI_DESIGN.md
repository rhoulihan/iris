# IRIS API & CLI Design Document

## Overview

Phase 5 implementation providing user-facing interfaces for the IRIS pipeline.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Layer                            │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  CLI Interface   │         │   REST API       │          │
│  │  (Click/Typer)   │         │   (FastAPI)      │          │
│  └──────────────────┘         └──────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              AnalysisService                          │   │
│  │  - run_analysis()                                     │   │
│  │  - get_recommendations()                              │   │
│  │  - explain_recommendation()                           │   │
│  │  - apply_recommendation()                             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline Layer                            │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Orchestrator    │  │  Pattern Detector│                │
│  │  Cost Calculator │  │  Tradeoff Analyzer│               │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

---

## CLI Interface

### Technology Stack
- **Framework**: Click (lightweight, well-tested, widely used)
- **Configuration**: YAML/JSON config files + environment variables
- **Output**: Rich formatted text, JSON, YAML

### Commands

#### 1. `iris analyze`
Run full pipeline analysis on a database.

```bash
iris analyze \
  --connection "user/pass@host:port/service" \
  --output report.json \
  --format json \
  --snapshot-id <id>

# With config file
iris analyze --config iris-config.yaml

# Interactive mode
iris analyze --interactive
```

**Options:**
- `--connection, -c`: Database connection string (required)
- `--snapshot-id, -s`: Specific AWR snapshot ID (optional, creates new if not provided)
- `--output, -o`: Output file path (default: stdout)
- `--format, -f`: Output format (json, yaml, text) (default: text)
- `--config`: Path to configuration file
- `--interactive, -i`: Interactive mode with prompts
- `--verbose, -v`: Verbose logging
- `--detectors`: Comma-separated list of pattern detectors to enable (default: all)
- `--min-confidence`: Minimum confidence threshold (default: 0.6)

**Output:**
```json
{
  "analysis_id": "ANALYSIS-2025-11-21-001",
  "timestamp": "2025-11-21T10:30:00Z",
  "database": {
    "host": "localhost:1524",
    "service": "FREEPDB1",
    "version": "Oracle Database 26ai"
  },
  "workload_summary": {
    "snapshot_range": [12345, 12346],
    "duration_seconds": 3600,
    "total_queries": 1500,
    "unique_queries": 250
  },
  "patterns_detected": 8,
  "recommendations": 5,
  "recommendations_summary": {
    "high_priority": 2,
    "medium_priority": 2,
    "low_priority": 1
  }
}
```

#### 2. `iris recommendations`
List and filter recommendations.

```bash
# List all recommendations from last analysis
iris recommendations list

# List with filters
iris recommendations list \
  --priority high \
  --pattern-type LOB_CLIFF \
  --min-confidence 0.8

# Get specific recommendation
iris recommendations get REC-001 --format json

# Export recommendations
iris recommendations export --output recommendations.csv --format csv
```

**Subcommands:**
- `list`: List all recommendations with filters
- `get <id>`: Get details for specific recommendation
- `export`: Export recommendations to file

**Options:**
- `--priority`: Filter by priority (high, medium, low)
- `--pattern-type`: Filter by pattern type
- `--min-confidence`: Minimum confidence score
- `--format`: Output format (text, json, yaml, csv)
- `--output`: Output file path

#### 3. `iris explain`
Get detailed explanation for a recommendation.

```bash
iris explain REC-001

# With specific sections
iris explain REC-001 \
  --sections rationale,impact,tradeoffs \
  --format markdown
```

**Options:**
- `--sections`: Comma-separated list of sections (rationale, impact, costs, implementation, tradeoffs, alternatives)
- `--format`: Output format (text, markdown, json)
- `--output`: Output file path

**Output Example:**
```
Recommendation: REC-001
Type: LOB_CLIFF
Priority: HIGH
Confidence: 0.87

═══════════════════════════════════════════════════════════════

RATIONALE
─────────────────────────────────────────────────────────────
Pattern Detected: LOB cliff on table PRODUCT_REVIEWS
Current Issue: Small updates to large CLOB columns causing write amplification
Risk Score: 0.85 (HIGH)

Affected Objects:
  • Table: PRODUCT_REVIEWS (500K rows, avg 15KB/row)
  • Column: REVIEW_TEXT (CLOB, frequently updated)

═══════════════════════════════════════════════════════════════

IMPACT ANALYSIS
─────────────────────────────────────────────────────────────
Affected Queries: 2,500 queries/day
Performance Improvement: +65% (15ms → 5ms average)
Storage Impact: +150MB (normalized tables)

High-frequency queries:
  ✓ UPDATE product_reviews SET rating=? (1,800/day) - 70% faster
  ✓ SELECT review_text (500/day) - No impact
  ✓ INSERT INTO product_reviews (200/day) - 80% faster

═══════════════════════════════════════════════════════════════

IMPLEMENTATION
─────────────────────────────────────────────────────────────
[SQL DDL shown here]

Rollback Plan:
  1. Rename normalized tables
  2. Restore from backup
  3. Drop new tables

Testing Approach:
  • Shadow mode: Run on 10% of traffic for 1 week
  • Monitor: Write latency, storage usage
  • Rollback if: Latency increases >10%

═══════════════════════════════════════════════════════════════
```

#### 4. `iris apply`
Apply a recommendation (with safety checks).

```bash
# Dry run (show what would be executed)
iris apply REC-001 --dry-run

# Apply with confirmation
iris apply REC-001 --confirm

# Apply without confirmation (danger!)
iris apply REC-001 --yes

# Apply with shadow mode
iris apply REC-001 --shadow-mode --traffic-percentage 10
```

**Options:**
- `--dry-run`: Show SQL without executing
- `--confirm`: Prompt for confirmation before execution
- `--yes`: Skip confirmation (dangerous)
- `--shadow-mode`: Enable shadow mode testing
- `--traffic-percentage`: Percentage of traffic for shadow mode (default: 10)
- `--backup`: Create backup before applying (default: true)
- `--rollback-plan`: Output rollback plan to file

**Safety Checks:**
- Validates connection before execution
- Creates backup unless --no-backup specified
- Prompts for confirmation unless --yes specified
- Validates SQL syntax before execution
- Checks for conflicting recommendations

#### 5. `iris config`
Manage configuration.

```bash
# Show current configuration
iris config show

# Set configuration values
iris config set database.host localhost
iris config set analysis.min_confidence 0.7

# Initialize configuration file
iris config init --output iris-config.yaml

# Validate configuration
iris config validate iris-config.yaml
```

#### 6. `iris version`
Show version information.

```bash
iris version

# Output:
# IRIS v1.0.0
# Pipeline: v1.0.0
# Pattern Detectors: 4 (LOB, Join, Document, Duality View)
# Python: 3.10.12
# Oracle Driver: oracledb 1.4.2
```

---

## REST API

### Technology Stack
- **Framework**: FastAPI (async, modern, auto-documentation)
- **Validation**: Pydantic (automatic OpenAPI schema generation)
- **Authentication**: API keys (environment variable)
- **Rate Limiting**: Optional (for production)

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
API key in header:
```
X-API-Key: <your-api-key>
```

### Endpoints

#### 1. POST /api/v1/analyze
Trigger pipeline analysis.

**Request:**
```json
{
  "connection": {
    "host": "localhost",
    "port": 1524,
    "service": "FREEPDB1",
    "username": "iris_user",
    "password": "IrisUser123!"
  },
  "options": {
    "snapshot_id": null,
    "detectors": ["LOB_CLIFF", "JOIN_DIMENSION", "DOCUMENT_RELATIONAL", "DUALITY_VIEW"],
    "min_confidence": 0.6,
    "create_snapshot": true
  }
}
```

**Response (202 Accepted):**
```json
{
  "analysis_id": "ANALYSIS-2025-11-21-001",
  "status": "processing",
  "created_at": "2025-11-21T10:30:00Z",
  "estimated_completion": "2025-11-21T10:35:00Z",
  "status_url": "/api/v1/analyses/ANALYSIS-2025-11-21-001"
}
```

#### 2. GET /api/v1/analyses/{analysis_id}
Get analysis status and results.

**Response:**
```json
{
  "analysis_id": "ANALYSIS-2025-11-21-001",
  "status": "completed",
  "created_at": "2025-11-21T10:30:00Z",
  "completed_at": "2025-11-21T10:34:30Z",
  "database": {
    "host": "localhost:1524",
    "service": "FREEPDB1",
    "version": "Oracle Database 26ai"
  },
  "workload_summary": {
    "snapshot_range": [12345, 12346],
    "duration_seconds": 3600,
    "total_queries": 1500,
    "unique_queries": 250
  },
  "patterns_detected": 8,
  "recommendations": [
    {
      "recommendation_id": "REC-001",
      "type": "LOB_CLIFF",
      "priority": "HIGH",
      "confidence": 0.87,
      "target_table": "PRODUCT_REVIEWS",
      "summary": "LOB cliff detected - split large CLOB into separate table"
    }
  ]
}
```

#### 3. GET /api/v1/recommendations
List recommendations with filters.

**Query Parameters:**
- `analysis_id`: Filter by analysis ID
- `priority`: Filter by priority (high, medium, low)
- `pattern_type`: Filter by pattern type
- `min_confidence`: Minimum confidence score
- `limit`: Number of results (default: 50)
- `offset`: Pagination offset

**Response:**
```json
{
  "total": 5,
  "limit": 50,
  "offset": 0,
  "recommendations": [
    {
      "recommendation_id": "REC-001",
      "analysis_id": "ANALYSIS-2025-11-21-001",
      "type": "LOB_CLIFF",
      "priority": "HIGH",
      "confidence": 0.87,
      "target_table": "PRODUCT_REVIEWS",
      "summary": "LOB cliff detected - split large CLOB into separate table",
      "created_at": "2025-11-21T10:34:30Z"
    }
  ]
}
```

#### 4. GET /api/v1/recommendations/{recommendation_id}
Get detailed recommendation.

**Response:**
```json
{
  "recommendation_id": "REC-001",
  "analysis_id": "ANALYSIS-2025-11-21-001",
  "type": "LOB_CLIFF",
  "priority": "HIGH",
  "confidence": 0.87,
  "target_table": "PRODUCT_REVIEWS",
  "summary": "LOB cliff detected - split large CLOB into separate table",
  "rationale": {
    "pattern_detected": "LOB cliff on PRODUCT_REVIEWS.REVIEW_TEXT",
    "current_cost": "High write amplification on small updates",
    "expected_benefit": "65% improvement on UPDATE operations"
  },
  "impact": {
    "affected_queries": 2500,
    "high_frequency_improvement": "+65%",
    "low_frequency_impact": "+5%",
    "net_benefit_score": 8.5
  },
  "costs": {
    "storage_overhead_mb": 150,
    "compute_overhead_pct": 2,
    "maintenance_complexity": "low"
  },
  "implementation": {
    "sql": "CREATE TABLE product_review_text ...",
    "rollback_plan": "DROP TABLE product_review_text; ...",
    "testing_approach": "Shadow mode with 10% traffic"
  },
  "tradeoffs": [
    {
      "description": "Increased storage by 150MB",
      "justified_by": "65% improvement on 2,500 daily queries"
    }
  ],
  "alternatives": [
    {
      "approach": "Use LOB compression",
      "pros": ["No schema change"],
      "cons": ["Only 20% improvement", "CPU overhead"]
    }
  ],
  "created_at": "2025-11-21T10:34:30Z"
}
```

#### 5. POST /api/v1/recommendations/{recommendation_id}/apply
Apply a recommendation.

**Request:**
```json
{
  "confirm": true,
  "options": {
    "dry_run": false,
    "create_backup": true,
    "shadow_mode": false,
    "traffic_percentage": 10
  }
}
```

**Response (202 Accepted):**
```json
{
  "application_id": "APP-2025-11-21-001",
  "recommendation_id": "REC-001",
  "status": "processing",
  "created_at": "2025-11-21T11:00:00Z",
  "steps": [
    {
      "step": "backup",
      "status": "pending"
    },
    {
      "step": "validation",
      "status": "pending"
    },
    {
      "step": "execution",
      "status": "pending"
    },
    {
      "step": "verification",
      "status": "pending"
    }
  ],
  "status_url": "/api/v1/applications/APP-2025-11-21-001"
}
```

#### 6. GET /api/v1/applications/{application_id}
Get application status.

**Response:**
```json
{
  "application_id": "APP-2025-11-21-001",
  "recommendation_id": "REC-001",
  "status": "completed",
  "created_at": "2025-11-21T11:00:00Z",
  "completed_at": "2025-11-21T11:05:30Z",
  "steps": [
    {
      "step": "backup",
      "status": "completed",
      "duration_seconds": 30
    },
    {
      "step": "validation",
      "status": "completed",
      "duration_seconds": 5
    },
    {
      "step": "execution",
      "status": "completed",
      "duration_seconds": 120
    },
    {
      "step": "verification",
      "status": "completed",
      "duration_seconds": 10
    }
  ],
  "result": {
    "success": true,
    "execution_time_seconds": 165,
    "rollback_plan_saved": "/backups/rollback-REC-001.sql"
  }
}
```

#### 7. GET /api/v1/workloads
List analyzed workloads.

**Response:**
```json
{
  "total": 10,
  "workloads": [
    {
      "analysis_id": "ANALYSIS-2025-11-21-001",
      "database": "localhost:1524/FREEPDB1",
      "snapshot_range": [12345, 12346],
      "duration_seconds": 3600,
      "queries_analyzed": 1500,
      "patterns_detected": 8,
      "recommendations_count": 5,
      "created_at": "2025-11-21T10:30:00Z"
    }
  ]
}
```

#### 8. GET /api/v1/metrics
System metrics and statistics.

**Response:**
```json
{
  "system": {
    "uptime_seconds": 86400,
    "version": "1.0.0"
  },
  "analyses": {
    "total": 150,
    "today": 12,
    "average_duration_seconds": 180
  },
  "recommendations": {
    "total_generated": 450,
    "applied": 45,
    "high_priority": 90,
    "medium_priority": 180,
    "low_priority": 180
  },
  "pattern_detection": {
    "LOB_CLIFF": 60,
    "JOIN_DIMENSION": 120,
    "DOCUMENT_RELATIONAL": 150,
    "DUALITY_VIEW": 120
  }
}
```

#### 9. GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-21T12:00:00Z",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "storage": "ok"
  }
}
```

---

## Data Models

### Analysis Request
```python
from pydantic import BaseModel
from typing import Optional, List

class ConnectionConfig(BaseModel):
    host: str
    port: int = 1521
    service: str
    username: str
    password: str

class AnalysisOptions(BaseModel):
    snapshot_id: Optional[int] = None
    detectors: List[str] = ["LOB_CLIFF", "JOIN_DIMENSION", "DOCUMENT_RELATIONAL", "DUALITY_VIEW"]
    min_confidence: float = 0.6
    create_snapshot: bool = True

class AnalysisRequest(BaseModel):
    connection: ConnectionConfig
    options: AnalysisOptions = AnalysisOptions()
```

### Recommendation Response
```python
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

class RecommendationSummary(BaseModel):
    recommendation_id: str
    analysis_id: str
    type: str
    priority: str
    confidence: float
    target_table: str
    summary: str
    created_at: datetime

class RecommendationDetail(RecommendationSummary):
    rationale: Dict[str, Any]
    impact: Dict[str, Any]
    costs: Dict[str, Any]
    implementation: Dict[str, Any]
    tradeoffs: List[Dict[str, Any]]
    alternatives: List[Dict[str, Any]]
```

---

## Configuration File Format

### iris-config.yaml
```yaml
# Database Connection
database:
  host: localhost
  port: 1524
  service: FREEPDB1
  username: iris_user
  password: ${IRIS_DB_PASSWORD}  # Environment variable

# Analysis Settings
analysis:
  min_confidence: 0.6
  detectors:
    - LOB_CLIFF
    - JOIN_DIMENSION
    - DOCUMENT_RELATIONAL
    - DUALITY_VIEW
  create_snapshot: true

# Output Settings
output:
  format: json
  directory: ./iris-reports

# Safety Settings
safety:
  require_confirmation: true
  create_backup: true
  dry_run_first: true

# API Settings (for API server)
api:
  host: 0.0.0.0
  port: 8000
  api_key: ${IRIS_API_KEY}
  enable_auth: true
  rate_limit: 100  # requests per minute
```

---

## Implementation Order (TDD)

### Phase 1: CLI Foundation
1. Test: CLI entry point and version command
2. Test: Configuration loading
3. Test: Database connection validation
4. Implement: Click commands and configuration

### Phase 2: Analysis Service
1. Test: AnalysisService with mock orchestrator
2. Test: Recommendation storage and retrieval
3. Implement: Service layer

### Phase 3: CLI Commands
1. Test: `iris analyze` command
2. Test: `iris recommendations` commands
3. Test: `iris explain` command
4. Test: `iris apply` command (dry-run only)
5. Implement: All CLI commands

### Phase 4: REST API
1. Test: FastAPI app initialization
2. Test: POST /api/v1/analyze endpoint
3. Test: GET /api/v1/recommendations endpoints
4. Test: Health check
5. Implement: All API endpoints

### Phase 5: Integration
1. Test: End-to-end CLI flow
2. Test: End-to-end API flow
3. Documentation: OpenAPI schema
4. Documentation: CLI usage guide

---

## Security Considerations

### CLI
- Store passwords in environment variables or secure credential store
- Never log passwords or API keys
- Validate all user inputs
- Confirm destructive operations

### API
- API key authentication (X-API-Key header)
- Rate limiting to prevent abuse
- Input validation with Pydantic
- SQL injection prevention (parameterized queries only)
- HTTPS in production

---

## Error Handling

### CLI
- User-friendly error messages
- Exit codes: 0 (success), 1 (error), 2 (validation error)
- Verbose mode for debugging
- Suggest fixes for common errors

### API
- Standard HTTP status codes
- Consistent error response format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid connection parameters",
    "details": {
      "field": "connection.port",
      "issue": "Port must be between 1 and 65535"
    }
  }
}
```

---

## Testing Strategy

### Unit Tests
- CLI command parsing
- Configuration loading
- Service layer logic
- API endpoint handlers

### Integration Tests
- Full CLI workflows
- API request/response cycles
- Database connectivity
- Pipeline orchestrator integration

### End-to-End Tests
- Real database analysis
- Recommendation generation
- Application simulation (dry-run)

---

## Documentation

### CLI
- Man pages
- `--help` for all commands
- Usage examples in README

### API
- Auto-generated OpenAPI/Swagger docs
- Postman collection
- API usage examples in README

---

## Next Steps

1. Create directory structure
2. Add Click to requirements
3. Implement CLI foundation with tests
4. Implement AnalysisService with tests
5. Implement CLI commands
6. Implement REST API
7. Integration tests
8. Documentation
