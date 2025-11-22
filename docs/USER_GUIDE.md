# IRIS User Guide

Complete guide for using IRIS CLI and REST API to analyze Oracle databases and get schema optimization recommendations.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [CLI Usage](#cli-usage)
3. [REST API Usage](#rest-api-usage)
4. [Configuration](#configuration)
5. [Output Formats](#output-formats)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Oracle Database 23ai or 26ai with AWR enabled
- Python 3.10+ with IRIS installed
- Database user with AWR permissions

### 5-Minute Getting Started

```bash
# 1. Check IRIS version
iris version

# 2. Run analysis with connection string
iris analyze --connection "iris_user/password@localhost:1521/FREEPDB1"

# 3. View recommendations
iris recommendations list

# 4. Get detailed explanation
iris explain REC-001
```

---

## CLI Usage

### Installation

```bash
# Install IRIS
pip install -e .

# Verify installation
iris --help
```

**Expected Output:**
```
Usage: iris [OPTIONS] COMMAND [ARGS]...

  IRIS - Intelligent Recommendation and Inference System.

  Oracle Database schema optimization powered by AI.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  analyze          Run analysis on Oracle database.
  explain          Show detailed explanation for a recommendation.
  recommendations  Manage and view recommendations.
  version          Show IRIS version information.
```

### Command: `iris version`

Display IRIS version information.

#### Basic Usage

```bash
iris version
```

**Expected Output:**
```
IRIS v1.0.0
```

#### Verbose Output

```bash
iris version --verbose
```

**Expected Output:**
```
IRIS v1.0.0
Pipeline: v1.0.0
Pattern Detectors: 4
Python: 3.12.3
Oracle Driver: oracledb 2.5.0
```

#### JSON Output

```bash
iris version --format json
```

**Expected Output:**
```json
{
  "version": "1.0.0",
  "pipeline_version": "1.0.0",
  "pattern_detectors": 4,
  "python_version": "3.12.3",
  "oracle_driver": "oracledb 2.5.0"
}
```

---

### Command: `iris analyze`

Run comprehensive schema analysis on an Oracle database.

#### Method 1: Connection String

```bash
iris analyze --connection "iris_user/IrisUser123!@localhost:1521/FREEPDB1"
```

**Expected Output:**
```
Analysis ID: ANALYSIS-2025-11-21-001
Status: completed
Created: 2025-11-21 10:30:45.123456

Results:
  Patterns detected: 5
  Recommendations: 3
    - HIGH priority: 1
    - MEDIUM priority: 1
    - LOW priority: 1
  Estimated annual savings: $50,000.00
  Execution time: 12.50s
```

#### Method 2: Configuration File

Create `iris-config.yaml`:
```yaml
database:
  host: localhost
  port: 1521
  service: FREEPDB1
  username: iris_user
  password: IrisUser123!

analysis:
  min_confidence: 0.6
  detectors:
    - LOB_CLIFF
    - JOIN_DIMENSION
    - DOCUMENT_RELATIONAL
    - DUALITY_VIEW
  create_snapshot: true

output:
  format: json
  directory: ./iris-reports

safety:
  require_confirmation: true
  create_backup: true
  dry_run_first: true
```

Run analysis:
```bash
iris analyze --config iris-config.yaml
```

#### Method 3: With Environment Variables

Create `iris-config.yaml` with environment variable substitution:
```yaml
database:
  host: ${DB_HOST}
  port: ${DB_PORT}
  service: ${DB_SERVICE}
  username: ${DB_USER}
  password: ${DB_PASS}
```

Set environment variables and run:
```bash
export DB_HOST=localhost
export DB_PORT=1521
export DB_SERVICE=FREEPDB1
export DB_USER=iris_user
export DB_PASS=IrisUser123!

iris analyze --config iris-config.yaml
```

#### JSON Output

```bash
iris analyze \
  --connection "iris_user/IrisUser123!@localhost:1521/FREEPDB1" \
  --format json
```

**Expected Output:**
```json
{
  "analysis_id": "ANALYSIS-2025-11-21-001",
  "created_at": "2025-11-21T10:30:45.123456",
  "status": "completed",
  "patterns_detected": 5,
  "recommendations_generated": 3,
  "high_priority_count": 1,
  "medium_priority_count": 1,
  "low_priority_count": 1,
  "total_annual_savings": 50000.0,
  "execution_time_seconds": 12.5
}
```

#### Save to File

```bash
iris analyze \
  --connection "iris_user/IrisUser123!@localhost:1521/FREEPDB1" \
  --format json \
  --output analysis-report.json
```

**Expected Output:**
```
Analysis results saved to analysis-report.json
```

---

### Command: `iris recommendations list`

List all recommendations from the last analysis.

#### Basic Usage

```bash
iris recommendations list
```

**Expected Output:**
```
Found 3 recommendation(s):

  [HIGH] REC-001
    Type: LOB_CLIFF
    Savings: $25,000.00/year
    Convert LOB columns to JSON for better performance in PRODUCT_REVIEWS table

  [MEDIUM] REC-002
    Type: JOIN_DIMENSION
    Savings: $15,000.00/year
    Denormalize frequently joined dimension table CATEGORIES into PRODUCTS

  [LOW] REC-003
    Type: DOCUMENT_RELATIONAL
    Savings: $10,000.00/year
    Migrate JSON documents in ORDERS table to dedicated collection
```

#### Filter by Priority

```bash
iris recommendations list --priority HIGH
```

**Expected Output:**
```
Found 1 recommendation(s):

  [HIGH] REC-001
    Type: LOB_CLIFF
    Savings: $25,000.00/year
    Convert LOB columns to JSON for better performance in PRODUCT_REVIEWS table
```

#### Filter by Pattern Type

```bash
iris recommendations list --pattern-type LOB_CLIFF
```

#### JSON Output

```bash
iris recommendations list --format json
```

**Expected Output:**
```json
[
  {
    "recommendation_id": "REC-001",
    "type": "LOB_CLIFF",
    "priority": "HIGH",
    "description": "Convert LOB columns to JSON for better performance",
    "annual_savings": 25000.0
  },
  {
    "recommendation_id": "REC-002",
    "type": "JOIN_DIMENSION",
    "priority": "MEDIUM",
    "description": "Denormalize frequently joined dimension table",
    "annual_savings": 15000.0
  }
]
```

---

### Command: `iris explain`

Get detailed explanation for a specific recommendation.

#### Basic Usage

```bash
iris explain REC-001
```

**Expected Output:**
```
Recommendation: REC-001
Type: LOB_CLIFF
Priority: HIGH

============================================================

RATIONALE
Pattern Detected: LOB cliff on table PRODUCT_REVIEWS
Current Cost: Small updates to large CLOB columns causing write amplification
Expected Benefit: 65% reduction in write latency

============================================================

IMPACT ANALYSIS
Estimated Improvement: 65.0%
Annual Savings: $25,000.00
ROI: 2400.0%

============================================================

IMPLEMENTATION
SQL:
-- Create new JSON-based table
CREATE TABLE product_reviews_new (
  review_id NUMBER PRIMARY KEY,
  product_id NUMBER NOT NULL,
  rating NUMBER NOT NULL,
  review_data JSON
);

-- Migrate data
INSERT INTO product_reviews_new
SELECT review_id, product_id, rating,
       JSON_OBJECT('text' VALUE review_text,
                   'author' VALUE reviewer_name)
FROM product_reviews;

-- Swap tables
RENAME product_reviews TO product_reviews_old;
RENAME product_reviews_new TO product_reviews;

Rollback Plan:
-- Swap tables back
RENAME product_reviews TO product_reviews_new;
RENAME product_reviews_old TO product_reviews;
DROP TABLE product_reviews_new;

Testing Approach:
1. Shadow mode testing with dual writes
2. Performance comparison (10k writes)
3. Gradual rollout with monitoring
```

#### JSON Output

```bash
iris explain REC-001 --format json
```

**Expected Output:**
```json
{
  "recommendation_id": "REC-001",
  "type": "LOB_CLIFF",
  "priority": "HIGH",
  "description": "Convert LOB columns to JSON for better performance",
  "rationale": {
    "pattern_detected": "LOB cliff on table PRODUCT_REVIEWS",
    "current_cost": "Small updates to large CLOB columns causing write amplification",
    "expected_benefit": "65% reduction in write latency"
  },
  "implementation": {
    "sql": "CREATE TABLE product_reviews_new (...)",
    "rollback_plan": "RENAME product_reviews TO product_reviews_new...",
    "testing_approach": "1. Shadow mode testing..."
  },
  "estimated_improvement_pct": 65.0,
  "annual_savings": 25000.0,
  "roi_percentage": 2400.0
}
```

#### Markdown Output

```bash
iris explain REC-001 --format markdown > recommendation-REC-001.md
```

---

## REST API Usage

### Starting the API Server

```bash
# Start with uvicorn
uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# Or with auto-reload for development
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Interactive API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints

#### Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "iris-api"
}
```

#### Run Analysis

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "database": {
      "host": "localhost",
      "port": 1521,
      "service": "FREEPDB1",
      "username": "iris_user",
      "password": "IrisUser123!"
    },
    "min_confidence": 0.6
  }'
```

**Expected Response:**
```json
{
  "analysis_id": "ANALYSIS-2025-11-21-001",
  "created_at": "2025-11-21T10:30:45.123456",
  "status": "completed",
  "patterns_detected": 5,
  "recommendations_generated": 3,
  "high_priority_count": 1,
  "medium_priority_count": 1,
  "low_priority_count": 1,
  "total_annual_savings": 50000.0,
  "execution_time_seconds": 12.5
}
```

#### Get Session Details

```bash
curl http://localhost:8000/api/v1/sessions/ANALYSIS-2025-11-21-001
```

**Expected Response:**
```json
{
  "analysis_id": "ANALYSIS-2025-11-21-001",
  "created_at": "2025-11-21T10:30:45.123456",
  "status": "completed",
  "patterns_detected": 5,
  "recommendations_generated": 3,
  "high_priority_count": 1,
  "medium_priority_count": 1,
  "low_priority_count": 1,
  "total_annual_savings": 50000.0,
  "execution_time_seconds": 12.5
}
```

#### List All Sessions

```bash
curl http://localhost:8000/api/v1/sessions
```

**Expected Response:**
```json
[
  {
    "analysis_id": "ANALYSIS-2025-11-21-001",
    "created_at": "2025-11-21T10:30:45.123456",
    "status": "completed",
    "patterns_detected": 5,
    "recommendations_generated": 3
  },
  {
    "analysis_id": "ANALYSIS-2025-11-21-002",
    "created_at": "2025-11-21T11:15:30.987654",
    "status": "completed",
    "patterns_detected": 3,
    "recommendations_generated": 2
  }
]
```

#### Get Recommendations

```bash
curl http://localhost:8000/api/v1/recommendations/ANALYSIS-2025-11-21-001
```

**Expected Response:**
```json
[
  {
    "recommendation_id": "REC-001",
    "type": "LOB_CLIFF",
    "priority": "HIGH",
    "description": "Convert LOB columns to JSON for better performance",
    "target_objects": ["PRODUCT_REVIEWS"],
    "estimated_improvement_pct": 65.0,
    "annual_savings": 25000.0,
    "roi_percentage": 2400.0
  }
]
```

#### Filter Recommendations by Priority

```bash
curl "http://localhost:8000/api/v1/recommendations/ANALYSIS-2025-11-21-001?priority=HIGH"
```

#### Get Specific Recommendation

```bash
curl http://localhost:8000/api/v1/recommendations/ANALYSIS-2025-11-21-001/REC-001
```

**Expected Response:**
```json
{
  "recommendation_id": "REC-001",
  "type": "LOB_CLIFF",
  "priority": "HIGH",
  "description": "Convert LOB columns to JSON for better performance",
  "target_objects": ["PRODUCT_REVIEWS"],
  "estimated_improvement_pct": 65.0,
  "annual_savings": 25000.0,
  "roi_percentage": 2400.0
}
```

### Python Client Example

```python
import requests

# Run analysis
response = requests.post(
    "http://localhost:8000/api/v1/analyze",
    json={
        "database": {
            "host": "localhost",
            "port": 1521,
            "service": "FREEPDB1",
            "username": "iris_user",
            "password": "IrisUser123!"
        },
        "min_confidence": 0.6
    }
)

session = response.json()
analysis_id = session["analysis_id"]
print(f"Analysis ID: {analysis_id}")

# Get recommendations
recommendations = requests.get(
    f"http://localhost:8000/api/v1/recommendations/{analysis_id}"
).json()

for rec in recommendations:
    print(f"{rec['priority']}: {rec['description']}")
    print(f"  Savings: ${rec['annual_savings']:,.2f}/year")
```

---

## Configuration

### Configuration File Format

IRIS uses YAML configuration files with the following sections:

```yaml
# Database connection settings
database:
  host: localhost
  port: 1521
  service: FREEPDB1
  username: iris_user
  password: ${DB_PASSWORD}  # Environment variable substitution

# Analysis configuration
analysis:
  min_confidence: 0.6  # Minimum confidence threshold (0.0-1.0)
  detectors:           # Pattern detectors to enable
    - LOB_CLIFF
    - JOIN_DIMENSION
    - DOCUMENT_RELATIONAL
    - DUALITY_VIEW
  create_snapshot: true  # Create new AWR snapshot

  # Pattern detection volume thresholds (prevents false positives on small workloads)
  pattern_detector:
    min_total_queries: 5000           # Minimum queries in workload for reliable detection
    min_pattern_query_count: 50       # Minimum queries matching a pattern
    min_table_query_count: 20         # Minimum queries per table
    low_volume_confidence_penalty: 0.3  # Confidence reduction (0.0-1.0) for low-volume patterns
    snapshot_confidence_min_hours: 24.0 # Snapshot duration for full confidence (shorter = penalty)

# Output configuration
output:
  format: json           # Output format (json, yaml, text, csv)
  directory: ./iris-reports  # Output directory

# Safety settings
safety:
  require_confirmation: true  # Require confirmation before applying
  create_backup: true        # Create backup before changes
  dry_run_first: true       # Run dry-run before actual changes

# API configuration (for API server)
api:
  host: 0.0.0.0
  port: 8000
  enable_auth: true
  rate_limit: 100  # requests per minute
```

### Environment Variables

IRIS supports environment variable substitution using `${VAR_NAME}` syntax:

```yaml
database:
  host: ${DB_HOST}
  port: ${DB_PORT}
  username: ${DB_USER}
  password: ${DB_PASS}
```

Set environment variables:
```bash
export DB_HOST=localhost
export DB_PORT=1521
export DB_USER=iris_user
export DB_PASS=IrisUser123!
```

---

## Output Formats

### Text Format (Default)

Human-readable text output suitable for console viewing.

```bash
iris analyze --connection "..." --format text
```

### JSON Format

Machine-readable JSON for programmatic processing.

```bash
iris analyze --connection "..." --format json
```

### YAML Format

YAML output for configuration management tools.

```bash
iris analyze --connection "..." --format yaml
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Refused

**Error:**
```
DatabaseConnectionError: Failed to connect to database: Connection refused
```

**Solution:**
- Verify database is running: `docker ps` or `lsnrctl status`
- Check connection parameters (host, port, service name)
- Test with SQL*Plus: `sqlplus iris_user/password@localhost:1521/FREEPDB1`

#### 2. Missing AWR Permissions

**Error:**
```
ORA-00942: table or view does not exist (DBA_HIST_SNAPSHOT)
```

**Solution:**
Grant AWR permissions:
```sql
GRANT SELECT ON SYS.V_$PARAMETER TO iris_user;
GRANT SELECT ON DBA_HIST_SNAPSHOT TO iris_user;
GRANT SELECT ON DBA_HIST_SQLSTAT TO iris_user;
GRANT SELECT ON DBA_HIST_SQLTEXT TO iris_user;
GRANT SELECT ON DBA_HIST_SQL_PLAN TO iris_user;
GRANT EXECUTE ON DBMS_WORKLOAD_REPOSITORY TO iris_user;
```

#### 3. No Analysis Session Found

**Error:**
```
No analysis has been run. Run 'iris analyze' first.
```

**Solution:**
Run analysis before trying to view recommendations:
```bash
iris analyze --connection "..."
iris recommendations list
```

#### 4. Invalid Configuration

**Error:**
```
ConfigError: min_confidence must be between 0.0 and 1.0, got 1.5
```

**Solution:**
Check configuration values:
- `min_confidence`: Must be between 0.0 and 1.0
- `detectors`: Must be valid detector names (LOB_CLIFF, JOIN_DIMENSION, etc.)
- `format`: Must be json, yaml, text, or csv

### Getting Help

```bash
# General help
iris --help

# Command-specific help
iris analyze --help
iris recommendations --help
iris explain --help
```

### Enable Verbose Logging

```bash
iris analyze --connection "..." --verbose
```

### Report Issues

If you encounter issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs with `--verbose` flag
3. Report issues at: https://github.com/rhoulihan/iris/issues

---

## Next Steps

- Review [API_CLI_DESIGN.md](API_CLI_DESIGN.md) for detailed specifications
- Explore [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for architecture details
- Check [SIMULATION_WORKLOADS.md](SIMULATION_WORKLOADS.md) for testing scenarios

---

**Last Updated:** 2025-11-21
