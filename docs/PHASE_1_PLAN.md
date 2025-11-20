# IRIS Phase 1 Implementation Plan (Weeks 1-4)

**Status**: In Progress
**Start Date**: 2025-11-20
**Target Completion**: Week of 2025-12-18
**Goal**: Establish foundation infrastructure and data pipelines with TDD methodology

---

## Overview

Phase 1 establishes the foundational infrastructure, data pipelines, and development practices for the IRIS project. This phase prioritizes **test-driven development**, **data quality**, and **reproducibility**—the three pillars that determine ML system success in production.

**Success Criteria**:
- ✅ Working infrastructure (all services deployed, green health checks)
- ✅ Automated data pipeline (AWR data flowing every 15 minutes)
- ✅ Feature store (online and offline serving functional)
- ✅ 80%+ test coverage across all modules
- ✅ CI/CD pipeline operational
- ✅ Monitoring and observability in place

---

## Week 1: Foundation Setup & Data Collection

### Sprint Goals
1. Complete project structure and development tooling
2. Implement AWR data collection module (TDD)
3. Set up basic monitoring and logging

### Day 1-2: Project Structure & Development Tools

**Tasks**:
- [x] Initialize Git repository
- [x] Create project directory structure
- [ ] Set up pre-commit hooks (black, flake8, mypy, isort)
- [ ] Configure IDE with Python interpreter and Oracle data source
- [ ] Create comprehensive .gitignore
- [ ] Set up pytest configuration

**Directory Structure**:
```
iris/
├── .git/
├── .github/
│   └── workflows/          # GitHub Actions CI/CD
├── docs/                   # All documentation
│   ├── IRIS.md
│   ├── CLAUDE.md
│   ├── DEV_ENVIRONMENT_PLAN.md
│   ├── PHASE_1_PLAN.md     # This file
│   └── api/                # API documentation
├── src/
│   ├── __init__.py
│   ├── common/             # Shared utilities
│   │   ├── __init__.py
│   │   ├── storage_interface.py
│   │   └── cache_interface.py
│   ├── data/               # Data collection & processing
│   │   ├── __init__.py
│   │   ├── awr_collector.py
│   │   ├── query_parser.py
│   │   └── workload_compressor.py
│   ├── features/           # Feature engineering
│   │   ├── __init__.py
│   │   ├── feature_store.py
│   │   ├── query_features.py
│   │   └── metric_features.py
│   ├── models/             # ML models (later phases)
│   │   └── __init__.py
│   └── utils/              # Utility functions
│       ├── __init__.py
│       ├── logging_config.py
│       └── metrics.py
├── tests/
│   ├── __init__.py
│   ├── unit/               # Unit tests
│   │   ├── test_awr_collector.py
│   │   ├── test_storage_interface.py
│   │   └── test_cache_interface.py
│   ├── integration/        # Integration tests
│   │   ├── test_oracle_integration.py
│   │   └── test_data_pipeline.py
│   ├── data/               # Test data and fixtures
│   │   └── fixtures/
│   └── conftest.py         # Pytest configuration
├── docker/
│   ├── docker-compose.dev.yml
│   └── init-scripts/
├── data/                   # Local data (gitignored)
│   ├── raw/
│   ├── processed/
│   └── features/
├── models/                 # Model artifacts (gitignored)
├── notebooks/              # Jupyter notebooks for exploration
├── scripts/
│   ├── start-dev.sh
│   ├── stop-dev.sh
│   └── status.sh
├── .env                    # Environment variables (gitignored)
├── .gitignore
├── requirements.txt
├── requirements-dev.txt    # Development dependencies
├── setup.py                # Package configuration
├── pytest.ini              # Pytest configuration
├── pyproject.toml          # Black, isort configuration
└── README.md
```

**Deliverables**:
- [ ] Complete directory structure created
- [ ] Pre-commit hooks configured and tested
- [ ] IDE configured with debugger and Oracle connection
- [ ] Documentation updated with setup instructions

---

### Day 3-5: AWR Data Collection Module (TDD)

**Objective**: Build a robust AWR data collector that queries Oracle AWR views and extracts workload information.

**Test-Driven Development Workflow**:

**Step 1: Write Tests First** (`tests/unit/test_awr_collector.py`)

```python
"""
Unit tests for AWR data collector.
Tests written BEFORE implementation.
"""
import pytest
from datetime import datetime, timedelta
from src.data.awr_collector import AWRCollector, AWRSnapshot

@pytest.fixture
def oracle_connection():
    """Provide Oracle connection for tests."""
    import oracledb
    conn = oracledb.connect(
        user="iris_user",
        password="IrisUser123!",
        dsn="localhost:1524/FREEPDB1"
    )
    yield conn
    conn.close()

class TestAWRCollector:
    """Test suite for AWR data collector."""

    def test_collector_initialization(self, oracle_connection):
        """Test AWR collector can be initialized with valid connection."""
        collector = AWRCollector(oracle_connection)
        assert collector is not None
        assert collector.connection == oracle_connection

    def test_get_latest_snapshot_id(self, oracle_connection):
        """Test retrieval of latest AWR snapshot ID."""
        collector = AWRCollector(oracle_connection)
        snapshot_id = collector.get_latest_snapshot_id()
        assert isinstance(snapshot_id, int)
        assert snapshot_id > 0

    def test_get_snapshot_range(self, oracle_connection):
        """Test retrieval of snapshot ID range for time period."""
        collector = AWRCollector(oracle_connection)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)

        snapshots = collector.get_snapshot_range(start_time, end_time)
        assert isinstance(snapshots, list)
        assert all(isinstance(s, AWRSnapshot) for s in snapshots)

    def test_collect_sql_statistics(self, oracle_connection):
        """Test collection of SQL statistics from AWR."""
        collector = AWRCollector(oracle_connection)
        snapshot_id = collector.get_latest_snapshot_id()

        sql_stats = collector.collect_sql_statistics(snapshot_id)
        assert isinstance(sql_stats, list)
        assert len(sql_stats) > 0

        # Verify structure of returned data
        first_stat = sql_stats[0]
        required_fields = [
            'sql_id', 'plan_hash_value', 'executions',
            'elapsed_time', 'cpu_time', 'buffer_gets',
            'disk_reads', 'sql_text'
        ]
        for field in required_fields:
            assert field in first_stat

    def test_collect_execution_plans(self, oracle_connection):
        """Test collection of execution plans for SQL statements."""
        collector = AWRCollector(oracle_connection)

        # Get a real SQL ID from recent snapshots
        sql_stats = collector.collect_sql_statistics(
            collector.get_latest_snapshot_id()
        )
        sql_id = sql_stats[0]['sql_id']

        plans = collector.collect_execution_plans(sql_id)
        assert isinstance(plans, list)
        assert len(plans) > 0

    def test_collect_system_metrics(self, oracle_connection):
        """Test collection of system-level metrics."""
        collector = AWRCollector(oracle_connection)
        snapshot_id = collector.get_latest_snapshot_id()

        metrics = collector.collect_system_metrics(snapshot_id)
        assert isinstance(metrics, dict)

        # Verify key metrics present
        expected_metrics = [
            'cpu_utilization', 'memory_usage',
            'io_wait_time', 'session_count'
        ]
        for metric in expected_metrics:
            assert metric in metrics

    def test_invalid_snapshot_id_raises_error(self, oracle_connection):
        """Test that invalid snapshot ID raises appropriate error."""
        collector = AWRCollector(oracle_connection)

        with pytest.raises(ValueError, match="Invalid snapshot ID"):
            collector.collect_sql_statistics(-1)

    def test_missing_connection_raises_error(self):
        """Test that missing connection raises appropriate error."""
        with pytest.raises(ValueError, match="Database connection required"):
            AWRCollector(None)
```

**Step 2: Implement to Pass Tests** (`src/data/awr_collector.py`)

```python
"""
AWR Data Collector Module

Collects performance data from Oracle Automatic Workload Repository (AWR).
Provides interfaces for querying snapshots, SQL statistics, execution plans,
and system metrics.

Author: IRIS Development Team
Created: 2025-11-20
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging
import oracledb

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AWRSnapshot:
    """Represents an AWR snapshot."""
    snapshot_id: int
    instance_number: int
    begin_time: datetime
    end_time: datetime
    snap_level: int


class AWRCollector:
    """
    Collects data from Oracle AWR views.

    This class provides methods to query AWR repository views and extract
    workload information including SQL statistics, execution plans, and
    system metrics.

    Example:
        >>> conn = oracledb.connect(user="iris_user", password="...", dsn="...")
        >>> collector = AWRCollector(conn)
        >>> snapshot_id = collector.get_latest_snapshot_id()
        >>> sql_stats = collector.collect_sql_statistics(snapshot_id)
    """

    def __init__(self, connection: oracledb.Connection):
        """
        Initialize AWR collector with database connection.

        Args:
            connection: Active Oracle database connection with AWR read privileges

        Raises:
            ValueError: If connection is None or invalid
        """
        if connection is None:
            raise ValueError("Database connection required")

        self.connection = connection
        self._validate_awr_access()
        logger.info("AWR Collector initialized successfully")

    def _validate_awr_access(self) -> None:
        """
        Validate that the connection has access to AWR views.

        Raises:
            PermissionError: If AWR views are not accessible
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT COUNT(*)
                FROM dba_hist_snapshot
                WHERE ROWNUM = 1
            """)
            cursor.close()
        except oracledb.DatabaseError as e:
            logger.error(f"AWR access validation failed: {e}")
            raise PermissionError(
                "Cannot access AWR views. Ensure SELECT privileges granted."
            )

    def get_latest_snapshot_id(self) -> int:
        """
        Get the most recent AWR snapshot ID.

        Returns:
            Latest snapshot ID (integer)

        Raises:
            RuntimeError: If no snapshots found
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT MAX(snap_id)
                FROM dba_hist_snapshot
            """)
            result = cursor.fetchone()

            if result is None or result[0] is None:
                raise RuntimeError("No AWR snapshots found")

            snapshot_id = int(result[0])
            logger.debug(f"Latest snapshot ID: {snapshot_id}")
            return snapshot_id

        finally:
            cursor.close()

    def get_snapshot_range(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[AWRSnapshot]:
        """
        Get AWR snapshots within a time range.

        Args:
            start_time: Beginning of time range
            end_time: End of time range

        Returns:
            List of AWRSnapshot objects
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    snap_id,
                    instance_number,
                    begin_interval_time,
                    end_interval_time,
                    snap_level
                FROM dba_hist_snapshot
                WHERE begin_interval_time >= :start_time
                  AND end_interval_time <= :end_time
                ORDER BY snap_id
            """, start_time=start_time, end_time=end_time)

            snapshots = []
            for row in cursor:
                snapshots.append(AWRSnapshot(
                    snapshot_id=row[0],
                    instance_number=row[1],
                    begin_time=row[2],
                    end_time=row[3],
                    snap_level=row[4]
                ))

            logger.info(f"Retrieved {len(snapshots)} snapshots from {start_time} to {end_time}")
            return snapshots

        finally:
            cursor.close()

    def collect_sql_statistics(self, snapshot_id: int) -> List[Dict[str, Any]]:
        """
        Collect SQL statement statistics for a snapshot.

        Args:
            snapshot_id: AWR snapshot ID

        Returns:
            List of dictionaries containing SQL statistics

        Raises:
            ValueError: If snapshot_id is invalid
        """
        if snapshot_id < 0:
            raise ValueError("Invalid snapshot ID")

        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    sql.sql_id,
                    sql.plan_hash_value,
                    sql.executions_delta as executions,
                    sql.elapsed_time_delta as elapsed_time,
                    sql.cpu_time_delta as cpu_time,
                    sql.buffer_gets_delta as buffer_gets,
                    sql.disk_reads_delta as disk_reads,
                    txt.sql_text
                FROM dba_hist_sqlstat sql
                JOIN dba_hist_sqltext txt ON sql.sql_id = txt.sql_id
                WHERE sql.snap_id = :snap_id
                  AND sql.executions_delta > 0
                ORDER BY sql.elapsed_time_delta DESC
                FETCH FIRST 1000 ROWS ONLY
            """, snap_id=snapshot_id)

            sql_stats = []
            for row in cursor:
                sql_stats.append({
                    'sql_id': row[0],
                    'plan_hash_value': row[1],
                    'executions': row[2],
                    'elapsed_time': row[3],
                    'cpu_time': row[4],
                    'buffer_gets': row[5],
                    'disk_reads': row[6],
                    'sql_text': row[7]
                })

            logger.info(f"Collected {len(sql_stats)} SQL statements from snapshot {snapshot_id}")
            return sql_stats

        finally:
            cursor.close()

    def collect_execution_plans(self, sql_id: str) -> List[Dict[str, Any]]:
        """
        Collect execution plans for a SQL statement.

        Args:
            sql_id: Oracle SQL identifier

        Returns:
            List of execution plan steps
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    plan_hash_value,
                    id,
                    operation,
                    options,
                    object_name,
                    cost,
                    cardinality,
                    bytes,
                    cpu_cost,
                    io_cost
                FROM dba_hist_sql_plan
                WHERE sql_id = :sql_id
                ORDER BY plan_hash_value, id
            """, sql_id=sql_id)

            plans = []
            for row in cursor:
                plans.append({
                    'plan_hash_value': row[0],
                    'step_id': row[1],
                    'operation': row[2],
                    'options': row[3],
                    'object_name': row[4],
                    'cost': row[5],
                    'cardinality': row[6],
                    'bytes': row[7],
                    'cpu_cost': row[8],
                    'io_cost': row[9]
                })

            return plans

        finally:
            cursor.close()

    def collect_system_metrics(self, snapshot_id: int) -> Dict[str, float]:
        """
        Collect system-level performance metrics.

        Args:
            snapshot_id: AWR snapshot ID

        Returns:
            Dictionary of metric names and values
        """
        cursor = self.connection.cursor()
        try:
            # Query DBA_HIST_SYSSTAT for key system statistics
            cursor.execute("""
                SELECT
                    stat_name,
                    value
                FROM dba_hist_sysstat
                WHERE snap_id = :snap_id
                  AND stat_name IN (
                      'CPU used by this session',
                      'physical reads',
                      'physical writes',
                      'session logical reads',
                      'db block gets',
                      'consistent gets'
                  )
            """, snap_id=snapshot_id)

            metrics = {}
            for row in cursor:
                metrics[row[0]] = float(row[1])

            # Calculate derived metrics
            metrics['cpu_utilization'] = metrics.get('CPU used by this session', 0.0)
            metrics['memory_usage'] = metrics.get('session logical reads', 0.0)
            metrics['io_wait_time'] = (
                metrics.get('physical reads', 0.0) +
                metrics.get('physical writes', 0.0)
            )

            # Get session count
            cursor.execute("""
                SELECT COUNT(DISTINCT session_id)
                FROM dba_hist_active_sess_history
                WHERE snap_id = :snap_id
            """, snap_id=snapshot_id)

            session_count = cursor.fetchone()
            metrics['session_count'] = float(session_count[0]) if session_count else 0.0

            return metrics

        finally:
            cursor.close()
```

**Step 3: Run Tests**

```bash
# Run tests with coverage
pytest tests/unit/test_awr_collector.py -v --cov=src/data/awr_collector --cov-report=html

# Expected output:
# tests/unit/test_awr_collector.py::TestAWRCollector::test_collector_initialization PASSED
# tests/unit/test_awr_collector.py::TestAWRCollector::test_get_latest_snapshot_id PASSED
# ... (all tests passing)
#
# Coverage: 85%+
```

**Deliverables**:
- [ ] `tests/unit/test_awr_collector.py` - Comprehensive test suite
- [ ] `src/data/awr_collector.py` - Working implementation
- [ ] 85%+ test coverage on AWR collector
- [ ] Documentation in docstrings
- [ ] Example usage in tests

---

## Week 2: Feature Engineering & Data Validation

### Sprint Goals
1. Build query parser and template extraction
2. Implement workload compression (ISUM algorithm basics)
3. Set up data validation with Great Expectations
4. Create feature engineering pipeline

### Day 6-8: Query Parser & Template Extraction

**Objective**: Parse SQL queries, extract templates, and normalize for pattern recognition.

**TDD Workflow**:

**Tests** (`tests/unit/test_query_parser.py`):
```python
class TestQueryParser:
    def test_parse_select_statement(self):
        """Test parsing of SELECT statements."""
        parser = QueryParser()
        sql = "SELECT * FROM customers WHERE customer_id = 123"
        parsed = parser.parse(sql)

        assert parsed.query_type == "SELECT"
        assert "customers" in parsed.tables
        assert "customer_id" in parsed.predicates

    def test_extract_template(self):
        """Test template extraction (remove literals)."""
        parser = QueryParser()
        sql = "SELECT name FROM users WHERE id = 42 AND status = 'active'"
        template = parser.extract_template(sql)

        expected = "SELECT name FROM users WHERE id = ? AND status = ?"
        assert template == expected

    def test_normalize_query(self):
        """Test query normalization (whitespace, case)."""
        parser = QueryParser()
        sql = "  SELECT   * FROM   Customers  "
        normalized = parser.normalize(sql)

        assert normalized == "select * from customers"
```

**Implementation** (`src/data/query_parser.py`):
- Use `sqlparse` library for SQL parsing
- Implement template extraction logic
- Handle multiple SQL dialects (Oracle-specific)

### Day 9-10: Workload Compression

**Objective**: Implement basic workload compression to reduce 10,000+ queries to representative subset.

**Tests** (`tests/unit/test_workload_compressor.py`):
```python
class TestWorkloadCompressor:
    def test_compress_workload(self):
        """Test workload compression reduces query count."""
        compressor = WorkloadCompressor()
        queries = [...]  # 1000 sample queries

        compressed = compressor.compress(queries, target_size=100)

        assert len(compressed) <= 100
        assert compressed.coverage >= 0.95  # 95% workload coverage

    def test_frequency_preservation(self):
        """Test that compression preserves query frequency distribution."""
        # Ensure high-frequency patterns are retained
```

**Implementation** (`src/data/workload_compressor.py`):
- Implement clustering by query structure
- Preserve frequency distributions
- Track coverage metrics

---

## Week 3: Feature Store & Data Pipeline Automation

### Sprint Goals
1. Set up Feature Store (Offline: files, Online: Redis)
2. Implement feature engineering functions
3. Automate data collection pipeline
4. Set up monitoring and logging

### Day 11-13: Feature Store Implementation

**Architecture**:
```
Feature Store
├── Offline Store (Training)
│   ├── Parquet files in data/features/
│   └── Schema versioning
└── Online Store (Serving)
    ├── Redis cache
    └── Sub-10ms latency
```

**Tests** (`tests/unit/test_feature_store.py`):
```python
class TestFeatureStore:
    def test_save_offline_features(self):
        """Test saving features to offline store."""
        store = FeatureStore()
        features = {...}  # Feature dictionary

        store.save_offline(features, version="v1")
        loaded = store.load_offline(version="v1")

        assert loaded == features

    def test_cache_online_features(self):
        """Test caching features in online store."""
        store = FeatureStore()
        features = {...}

        store.cache_online("query_123", features, ttl=3600)
        cached = store.get_online("query_123")

        assert cached == features
```

**Implementation** (`src/features/feature_store.py`):
- Offline storage: Parquet with PyArrow
- Online storage: Redis with pickle serialization
- Feature versioning and schema validation

### Day 14-15: Feature Engineering Functions

**Query-Level Features**:
- Query complexity (number of joins, subqueries)
- Table access patterns
- Predicate selectivity estimates
- Operation types (scan vs index access)

**System-Level Features**:
- CPU utilization
- Memory pressure
- I/O wait time
- Session concurrency

**Tests** (`tests/unit/test_query_features.py`):
```python
class TestQueryFeatures:
    def test_extract_query_complexity(self):
        """Test query complexity feature extraction."""
        sql = "SELECT ... (complex query)"
        features = extract_query_features(sql)

        assert 'num_joins' in features
        assert 'num_subqueries' in features
        assert 'num_tables' in features
```

---

## Week 4: Monitoring, CI/CD, and Integration

### Sprint Goals
1. Set up comprehensive logging
2. Implement basic metrics collection (Prometheus)
3. Create CI/CD pipeline (GitHub Actions)
4. Integration testing of complete data pipeline
5. Documentation and handoff preparation

### Day 16-17: Monitoring & Observability

**Logging Configuration** (`src/utils/logging_config.py`):
```python
import logging
import structlog

def setup_logging(level=logging.INFO):
    """Configure structured logging for IRIS."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

**Metrics Collection** (`src/utils/metrics.py`):
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
awr_queries_total = Counter(
    'iris_awr_queries_total',
    'Total AWR queries executed'
)

feature_extraction_duration = Histogram(
    'iris_feature_extraction_duration_seconds',
    'Time to extract features'
)

active_snapshots = Gauge(
    'iris_active_snapshots',
    'Number of AWR snapshots being processed'
)
```

### Day 18-19: CI/CD Pipeline

**GitHub Actions Workflow** (`.github/workflows/ci.yml`):
```yaml
name: IRIS CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      oracle:
        image: container-registry.oracle.com/database/free:latest
        env:
          ORACLE_PWD: TestPass123!
        ports:
          - 1521:1521
        options: >-
          --health-cmd "echo 'SELECT 1 FROM DUAL;' | sqlplus -s sys/TestPass123!@localhost/FREEPDB1 as sysdba"
          --health-interval 30s
          --health-timeout 10s
          --health-retries 10

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run pre-commit hooks
      run: |
        pre-commit run --all-files

    - name: Run tests with coverage
      run: |
        pytest tests/ -v --cov=src --cov-report=xml --cov-report=html

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

    - name: Build documentation
      run: |
        cd docs && make html
```

### Day 20: Integration Testing & Phase 1 Review

**Integration Test Suite** (`tests/integration/test_data_pipeline.py`):
```python
import pytest
from datetime import datetime, timedelta

class TestDataPipeline:
    """End-to-end integration tests for data pipeline."""

    def test_complete_pipeline_flow(self, oracle_connection):
        """Test complete data flow from AWR to features."""
        # 1. Collect AWR data
        collector = AWRCollector(oracle_connection)
        snapshot_id = collector.get_latest_snapshot_id()
        sql_stats = collector.collect_sql_statistics(snapshot_id)

        assert len(sql_stats) > 0

        # 2. Parse and extract templates
        parser = QueryParser()
        templates = [parser.extract_template(s['sql_text']) for s in sql_stats]

        assert len(templates) == len(sql_stats)

        # 3. Extract features
        features = []
        for sql_stat in sql_stats:
            query_features = extract_query_features(sql_stat['sql_text'])
            features.append(query_features)

        assert len(features) > 0

        # 4. Save to feature store
        store = FeatureStore()
        for i, feature in enumerate(features):
            store.save_offline(feature, version=f"snapshot_{snapshot_id}_query_{i}")

        # 5. Verify retrieval
        loaded = store.load_offline(version=f"snapshot_{snapshot_id}_query_0")
        assert loaded == features[0]
```

**Phase 1 Completion Checklist**:
- [ ] All unit tests passing (85%+ coverage)
- [ ] All integration tests passing
- [ ] CI/CD pipeline green
- [ ] Documentation complete
- [ ] Monitoring operational
- [ ] Demo to stakeholders
- [ ] Retrospective conducted
- [ ] Phase 2 planning completed

---

## Development Standards

### Test-Driven Development (TDD)

**Always follow Red-Green-Refactor cycle**:

1. **Red**: Write failing test first
2. **Green**: Implement minimal code to pass test
3. **Refactor**: Improve code quality while keeping tests green

**Test Coverage Requirements**:
- **Unit Tests**: 80%+ coverage
- **Integration Tests**: All critical paths covered
- **Data Tests**: Great Expectations for all data inputs

### Code Quality

**Pre-commit Hooks** (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--ignore=E203,W503']

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ['--profile', 'black']
```

### Documentation

**Docstring Standards** (Google Style):
```python
def collect_sql_statistics(self, snapshot_id: int) -> List[Dict[str, Any]]:
    """
    Collect SQL statement statistics for a snapshot.

    This function queries DBA_HIST_SQLSTAT to retrieve execution statistics
    for all SQL statements captured in the specified AWR snapshot.

    Args:
        snapshot_id: AWR snapshot ID (must be positive integer)

    Returns:
        List of dictionaries, each containing:
            - sql_id: Oracle SQL identifier
            - plan_hash_value: Execution plan hash
            - executions: Number of executions
            - elapsed_time: Total elapsed time (microseconds)
            - cpu_time: CPU time consumed (microseconds)
            - buffer_gets: Logical reads
            - disk_reads: Physical reads
            - sql_text: Full SQL text

    Raises:
        ValueError: If snapshot_id is invalid (< 0)
        DatabaseError: If AWR views are inaccessible

    Example:
        >>> collector = AWRCollector(conn)
        >>> stats = collector.collect_sql_statistics(12345)
        >>> print(f"Collected {len(stats)} SQL statements")
        Collected 847 SQL statements
    """
```

---

## Risk Management

### Identified Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| AWR data quality issues | High | Great Expectations validation, data quality tests |
| Oracle connection failures | Medium | Connection pooling, retry logic, circuit breakers |
| Performance degradation | Medium | Monitoring, performance tests, query optimization |
| Incomplete test coverage | High | Enforce 80%+ coverage in CI/CD, code review |
| Scope creep | Medium | Strict adherence to Phase 1 plan, weekly reviews |

### Success Metrics

**Technical Metrics**:
- Test coverage >= 80%
- CI/CD pipeline success rate >= 95%
- AWR data collection latency < 5 seconds
- Feature extraction latency < 100ms per query
- Zero security vulnerabilities (high/critical)

**Process Metrics**:
- All Phase 1 tasks completed on time
- Daily standups conducted
- Weekly demos to stakeholders
- Documentation up-to-date

---

## Phase 1 Deliverables

### Code Deliverables
- [ ] AWR data collector module with tests
- [ ] Query parser with template extraction
- [ ] Workload compressor (basic ISUM)
- [ ] Feature engineering functions
- [ ] Feature store (offline & online)
- [ ] Storage and cache abstractions
- [ ] Monitoring and logging infrastructure

### Documentation Deliverables
- [ ] API documentation (auto-generated from docstrings)
- [ ] Architecture decision records (ADRs)
- [ ] Runbook for operations
- [ ] Phase 2 implementation plan
- [ ] Weekly status reports

### Infrastructure Deliverables
- [ ] Docker Compose configuration
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Pre-commit hooks
- [ ] Monitoring dashboards (basic)

---

## Next Steps (Phase 2 Preview)

Phase 2 (Weeks 5-12) will focus on:

1. **Baseline Rule-Based Optimizer** (Weeks 5-6)
   - Heuristic-based recommendations
   - Target 60%+ accuracy
   - Provides fallback during ML failures

2. **LLM Integration** (Weeks 7-9)
   - Fine-tune Qwen 2.5 Coder 7B
   - Deploy with vLLM/TorchServe
   - Target 75%+ accuracy

3. **RL System** (Weeks 10-12)
   - Implement DS-DDPG agent
   - Online learning pipeline
   - Production-ready inference

---

## Daily Standup Template

**What did I accomplish yesterday?**
-

**What will I work on today?**
-

**Any blockers or concerns?**
-

**Test coverage status:**
- Current: ___%
- Target: 80%

---

## Weekly Review Template

**Week [X] Review**

**Completed Tasks:**
-

**In Progress:**
-

**Blocked:**
-

**Metrics:**
- Test coverage: ___%
- CI/CD success rate: ___%
- Bugs found/fixed: ___

**Risks/Issues:**
-

**Next Week Plan:**
-

---

**Status**: This plan is a living document. Update daily with progress, blockers, and learnings.

**Last Updated**: 2025-11-20
**Next Review**: 2025-11-22 (End of Week 1)
