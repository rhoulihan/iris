# IRIS Quick Reference

Fast reference for common IRIS commands and usage patterns.

---

## Installation & Setup

```bash
# Install IRIS
pip install -e .

# Verify installation
python -m src.cli.cli --help

# Check version
python -m src.cli.cli version
```

---

## CLI Commands

### Version Information

```bash
# Simple version
python -m src.cli.cli version

# Detailed version
python -m src.cli.cli version --verbose

# JSON output
python -m src.cli.cli version --format json
```

### Run Analysis

```bash
# With connection string
python -m src.cli.cli analyze \
  --connection "user/pass@host:port/service"

# With config file
python -m src.cli.cli analyze --config iris-config.yaml

# JSON output to file
python -m src.cli.cli analyze \
  --connection "user/pass@host:port/service" \
  --format json \
  --output analysis.json
```

### View Recommendations

```bash
# List all recommendations
python -m src.cli.cli recommendations list

# Filter by priority
python -m src.cli.cli recommendations list --priority HIGH

# JSON output
python -m src.cli.cli recommendations list --format json
```

### Explain Recommendation

```bash
# Text explanation
python -m src.cli.cli explain REC-001

# JSON output
python -m src.cli.cli explain REC-001 --format json

# Markdown output to file
python -m src.cli.cli explain REC-001 --format markdown > rec.md
```

---

## REST API

### Start API Server

```bash
# Production
uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# Development (auto-reload)
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

### Health Check

```bash
curl http://localhost:8000/health
```

### Run Analysis

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "database": {
      "host": "localhost",
      "port": 1521,
      "service": "FREEPDB1",
      "username": "iris_user",
      "password": "password"
    }
  }'
```

### Get Sessions

```bash
# List all sessions
curl http://localhost:8000/api/v1/sessions

# Get specific session
curl http://localhost:8000/api/v1/sessions/ANALYSIS-2025-11-21-001
```

### Get Recommendations

```bash
# All recommendations
curl http://localhost:8000/api/v1/recommendations/ANALYSIS-2025-11-21-001

# Filter by priority
curl "http://localhost:8000/api/v1/recommendations/ANALYSIS-2025-11-21-001?priority=HIGH"

# Specific recommendation
curl http://localhost:8000/api/v1/recommendations/ANALYSIS-2025-11-21-001/REC-001
```

---

## Configuration File

**Minimal Configuration (`iris-config.yaml`):**

```yaml
database:
  host: localhost
  port: 1521
  service: FREEPDB1
  username: iris_user
  password: ${DB_PASSWORD}
```

**Full Configuration:**

```yaml
database:
  host: localhost
  port: 1521
  service: FREEPDB1
  username: iris_user
  password: ${DB_PASSWORD}

analysis:
  min_confidence: 0.6
  detectors:
    - LOB_CLIFF
    - JOIN_DIMENSION
    - DOCUMENT_RELATIONAL
    - DUALITY_VIEW
  create_snapshot: true
  pattern_detector:
    min_total_queries: 5000
    min_pattern_query_count: 50
    min_table_query_count: 20
    low_volume_confidence_penalty: 0.3
    snapshot_confidence_min_hours: 24.0

output:
  format: json
  directory: ./iris-reports

safety:
  require_confirmation: true
  create_backup: true
  dry_run_first: true
```

---

## Common Workflows

### Workflow 1: Quick Analysis

```bash
# 1. Run analysis
python -m src.cli.cli analyze --connection "user/pass@host:port/service"

# 2. View HIGH priority recommendations
python -m src.cli.cli recommendations list --priority HIGH

# 3. Get explanation for top recommendation
python -m src.cli.cli explain REC-001
```

### Workflow 2: Automated Analysis

```bash
# 1. Set environment variables
export DB_HOST=localhost
export DB_PORT=1521
export DB_SERVICE=FREEPDB1
export DB_USER=iris_user
export DB_PASS=password

# 2. Run analysis with config
python -m src.cli.cli analyze --config iris-config.yaml --format json --output report.json

# 3. Process results programmatically
python process_recommendations.py report.json
```

### Workflow 3: API Integration

```python
import requests

# 1. Run analysis
response = requests.post(
    "http://localhost:8000/api/v1/analyze",
    json={"database": {...}}
)
analysis_id = response.json()["analysis_id"]

# 2. Get HIGH priority recommendations
recommendations = requests.get(
    f"http://localhost:8000/api/v1/recommendations/{analysis_id}",
    params={"priority": "HIGH"}
).json()

# 3. Process recommendations
for rec in recommendations:
    print(f"{rec['recommendation_id']}: {rec['description']}")
    print(f"  Savings: ${rec['annual_savings']:,.2f}/year")
```

---

## Troubleshooting

### Check Database Connection

```bash
# Test with SQL*Plus
sqlplus iris_user/password@localhost:1521/FREEPDB1

# Verify AWR permissions
SELECT * FROM DBA_HIST_SNAPSHOT WHERE ROWNUM = 1;
```

### Enable Verbose Logging

```bash
python -m src.cli.cli analyze --connection "..." --verbose
```

### View All Available Commands

```bash
python -m src.cli.cli --help
python -m src.cli.cli analyze --help
python -m src.cli.cli recommendations --help
python -m src.cli.cli explain --help
```

---

## Test Suite

### Run All Tests

```bash
# All unit tests
PYTHONPATH=$PWD python -m pytest tests/unit/ -v

# Specific module
PYTHONPATH=$PWD python -m pytest tests/unit/cli/ -v

# With coverage
PYTHONPATH=$PWD python -m pytest tests/unit/ -v --cov=src --cov-report=term
```

### Run Simulations

```bash
# E-Commerce workload (Workload 1)
python tests/simulations/run_simulation.py \
  --workload 1 \
  --duration 60 \
  --scale small \
  --connection "iris_user/password@localhost:1524/FREEPDB1"

# Content Management (Workload 2)
python tests/simulations/run_simulation.py \
  --workload 2 \
  --duration 60 \
  --scale small \
  --connection "iris_user/password@localhost:1524/FREEPDB1"
```

---

## Pattern Detectors

IRIS includes 4 pattern detectors:

| Detector | Pattern Type | Description |
|----------|-------------|-------------|
| **LOB_CLIFF** | Anti-pattern | Small updates to large LOBs causing write amplification |
| **JOIN_DIMENSION** | Opportunity | Frequently joined dimension tables |
| **DOCUMENT_RELATIONAL** | Mismatch | JSON documents stored in relational tables |
| **DUALITY_VIEW** | Oracle 23ai | Mixed OLTP/Analytics workloads |

---

## Output Formats

| Format | Extension | Use Case |
|--------|-----------|----------|
| **text** | `.txt` | Human-readable console output |
| **json** | `.json` | Machine processing, API integration |
| **yaml** | `.yaml` | Configuration management, GitOps |
| **markdown** | `.md` | Documentation, reports |

---

## Environment Variables

```bash
# Database connection
export DB_HOST=localhost
export DB_PORT=1521
export DB_SERVICE=FREEPDB1
export DB_USER=iris_user
export DB_PASS=password

# Python path (for development)
export PYTHONPATH=$PWD
```

---

## Performance Metrics

- **Analysis Time**: ~10-30 seconds for typical workload
- **Pattern Detection**: ~2-5 seconds per detector
- **Recommendation Generation**: ~1-3 seconds per recommendation
- **Test Suite**: 445 tests in ~37 seconds

---

## Support

- **Documentation**: See [USER_GUIDE.md](USER_GUIDE.md)
- **API Docs**: http://localhost:8000/docs (when server running)
- **Issues**: https://github.com/rhoulihan/iris/issues

---

**Last Updated:** 2025-11-22
