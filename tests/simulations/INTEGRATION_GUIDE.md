# IRIS Pipeline Integration Guide

This document describes how the simulation workloads are integrated with the IRIS pipeline for end-to-end testing and validation.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Simulation Runner (CLI)                        │
│                   tests/simulations/run_simulation.py            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌────────────────┐ ┌───────────────┐ ┌──────────────┐
│  Workload 1    │ │  Workload 2   │ │  Workload 3  │
│  E-Commerce    │ │  Inventory    │ │  Orders      │
│  (Rel → Doc)   │ │  (Doc → Rel)  │ │  (Hybrid →   │
│                │ │               │ │   Duality)   │
└────────┬───────┘ └───────┬───────┘ └──────┬───────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                ┌──────────▼───────────┐
                │   AWR Snapshots      │
                │   (begin/end)        │
                └──────────┬───────────┘
                           │
                ┌──────────▼───────────┐
                │  Pipeline            │
                │  Orchestrator        │
                │  (src/pipeline/)     │
                └──────────┬───────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌────────────────┐ ┌───────────────┐ ┌──────────────┐
│ Pattern        │ │ Cost          │ │ Tradeoff     │
│ Detection      │ │ Analysis      │ │ Analysis     │
└────────┬───────┘ └───────┬───────┘ └──────┬───────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                ┌──────────▼───────────┐
                │  Recommendations     │
                │  Generation          │
                └──────────┬───────────┘
                           │
                ┌──────────▼───────────┐
                │  Recommendation      │
                │  Validator           │
                │  (tests/simulations/)│
                └──────────────────────┘
```

## 📦 Components

### 1. AWR Snapshot Helper
**File**: `tests/simulations/awr_helper.py`

Manages AWR snapshot creation and validation:
- `create_snapshot()` - Creates manual AWR snapshots
- `wait_for_snapshot()` - Waits for snapshot to be available
- `check_awr_enabled()` - Verifies AWR is enabled
- `get_snapshot_info()` - Retrieves snapshot metadata

### 2. Recommendation Validator
**File**: `tests/simulations/recommendation_validator.py`

Validates pipeline recommendations against expected outcomes:
- Expected patterns defined for each workload
- Validates pattern type, confidence, priority
- Checks recommendation text keywords
- Validates generated SQL keywords

#### Expected Recommendations

| Workload | Pattern Type | Min Confidence | Priority | Keywords |
|----------|--------------|----------------|----------|----------|
| 1: E-Commerce | DOCUMENT_RELATIONAL | 0.7 | HIGH | document, json, read-heavy, join |
| 2: Inventory | DOCUMENT_RELATIONAL | 0.7 | HIGH | relational, normalize, write-heavy |
| 3: Orders | DUALITY_VIEW_OPPORTUNITY | 0.7 | HIGH/MEDIUM | duality, view, hybrid, oltp, analytics |

### 3. Integration Tests
**File**: `tests/simulations/test_pipeline_simulations.py`

pytest-based integration tests with fixtures:
- `workload_setup` - Sets up schema and data for each workload
- Tests validate pattern detection and recommendation quality
- Uses pytest markers for selective test execution

### 4. Pytest Fixtures
**File**: `tests/simulations/conftest.py`

Shared test fixtures:
- `oracle_connection` - Database connection (session-scoped)
- `clean_workload_schemas` - Schema cleanup before/after tests
- `skip_if_no_awr` - Skip tests if AWR not available

## 🚀 Usage

### Command-Line Execution

```bash
# Run Workload 1 with full pipeline analysis
python tests/simulations/run_simulation.py \
    --workload 1 \
    --duration 300 \
    --scale small

# Run all workloads with pipeline analysis
python tests/simulations/run_simulation.py \
    --workload all \
    --duration 300 \
    --scale medium

# Skip pipeline analysis (workload only)
python tests/simulations/run_simulation.py \
    --workload 2 \
    --duration 300 \
    --skip-pipeline

# Use existing data and skip pipeline
python tests/simulations/run_simulation.py \
    --workload 1 \
    --duration 300 \
    --skip-data-gen \
    --skip-pipeline
```

### Pytest Execution

```bash
# Run all simulation tests
pytest tests/simulations/test_pipeline_simulations.py -v

# Run specific workload tests
pytest tests/simulations/test_pipeline_simulations.py::TestWorkload1ECommerce -v

# Run integration tests only
pytest tests/simulations/ -m integration -v

# Skip if AWR not available
pytest tests/simulations/ -v  # Will auto-skip if AWR disabled
```

## 🔄 Workflow Steps

### 1. Schema Creation
- Load SQL from `sql/workloadN_schema.sql`
- Create tables, indexes, sequences
- Handle errors gracefully (tables may already exist)

### 2. Data Generation
- Use Faker library for realistic data
- Batch inserts for performance
- Configurable scale (small/medium/large)
- Skip if `--skip-data-gen` specified

### 3. AWR Snapshot (Begin)
- Check if AWR is enabled (`statistics_level = TYPICAL/ALL`)
- Create manual snapshot: `DBMS_WORKLOAD_REPOSITORY.CREATE_SNAPSHOT()`
- Wait for snapshot to be available in `DBA_HIST_SNAPSHOT`
- Store `begin_snap_id`

### 4. Workload Execution
- Execute query patterns with rate limiting
- Maintain target throughput (queries/second)
- Log progress every 30 seconds
- Collect statistics (reads, writes, duration)

### 5. AWR Snapshot (End)
- Create second manual snapshot
- Wait for availability
- Store `end_snap_id`

### 6. Pipeline Orchestration
- Configure pipeline based on workload:
  - **Workload 1**: Enable join_analysis + document_analysis
  - **Workload 2**: Enable document_analysis only
  - **Workload 3**: Enable join_analysis + duality_view_analysis
- Run `PipelineOrchestrator.run(begin_snap_id, end_snap_id, schemas)`
- Collect `PipelineResult`

### 7. Recommendation Validation
- Load expected outcomes for workload
- Validate:
  - ✅ Recommendations generated (count > 0)
  - ✅ Pattern type matches expected
  - ✅ Confidence >= threshold
  - ✅ Priority in acceptable range
  - ✅ Keywords present in recommendation text
  - ✅ SQL keywords present (if SQL generated)
- Print validation results
- Return pass/fail status

## 📊 Output Example

```
======================================================================
Running Workload 1: E-Commerce
======================================================================

[INFO] Creating schema for Workload 1...
[INFO] Schema created successfully
[INFO] Generating data for Workload 1 (scale: small)...
[INFO] Inserted 100 customers
[INFO] Inserted 250 addresses
[INFO] Inserted 500 preferences
[INFO] Inserted 1000 orders
[INFO] Data generation complete

[INFO] Creating AWR snapshot (begin)...
[INFO] Begin snapshot ID: 12345

[INFO] Executing Workload 1 queries...
[INFO] Progress: 30s - Reads: 150, Writes: 8
[INFO] Progress: 60s - Reads: 300, Writes: 16
...
[INFO] Workload execution complete: {'reads': 1500, 'writes': 80, 'duration': 300.5}

[INFO] Creating AWR snapshot (end)...
[INFO] End snapshot ID: 12346

[INFO] Running IRIS pipeline analysis...
[INFO] Stage 1: Collecting AWR data and schema metadata
[INFO] Collected 1580 queries and 4 tables
[INFO] Stage 2: Feature engineering
[INFO] Stage 3: Pattern detection
[INFO] Detected 2 expensive join patterns
[INFO] Detected 1 document/relational patterns
[INFO] Total patterns detected: 3
[INFO] Stage 4: Cost/benefit analysis
[INFO] Stage 5: Tradeoff analysis
[INFO] Stage 6: Recommendation generation

[INFO] Validating recommendations...

======================================================================
Validation Results: E-Commerce User Profiles
======================================================================

Recommendations Generated: 3
Overall Result: ✅ PASSED

Validations:
  ✅ has_recommendations
  ✅ pattern_type_match
  ✅ confidence_threshold
  ✅ priority_acceptable
  ✅ keywords_found
  ✅ sql_keywords_found

======================================================================

======================================================================
Workload 1 Complete
======================================================================
Statistics: {'reads': 1500, 'writes': 80, 'duration': 300.5}
AWR Snapshots: 12345 - 12346
Recommendations: 3
Annual Savings: $45,230.00
Validation: ✅ PASSED
======================================================================
```

## 🎯 Validation Criteria

### Critical Validations (Must Pass)
1. **has_recommendations**: At least one recommendation generated
2. **pattern_type_match**: Matches expected pattern type
3. **confidence_threshold**: Confidence >= min_confidence (0.7)

### Advisory Validations (Warnings if Failed)
4. **priority_acceptable**: Priority in expected range
5. **keywords_found**: All expected keywords in recommendation text
6. **sql_keywords_found**: Expected SQL keywords present (if SQL provided)

## 🧪 Testing Strategy

### Unit Tests
- AWR Helper: Test snapshot creation, waiting, info retrieval
- Recommendation Validator: Test validation logic for each workload
- Individual components in isolation

### Integration Tests
- Schema creation and data generation
- Workload execution and statistics collection
- End-to-end pipeline with mocked AWR data

### System Tests (Requires Oracle Database)
- Full workflow with real AWR snapshots
- Pipeline orchestrator with real query patterns
- Recommendation validation against expected outcomes

## 🔧 Configuration

### Environment Variables
```bash
export ORACLE_USER=iris_user
export ORACLE_PASSWORD=IrisUser123!
export ORACLE_DSN=localhost:1524/FREEPDB1
```

### Pipeline Configuration
Each workload has optimized pipeline config:

```python
# Workload 1: E-Commerce (Relational → Document)
PipelineConfig(
    enable_join_analysis=True,
    enable_document_analysis=True,
    enable_lob_detection=False,
    enable_duality_view_analysis=False,
    min_confidence_threshold=0.3,
)

# Workload 2: Inventory (Document → Relational)
PipelineConfig(
    enable_document_analysis=True,
    enable_lob_detection=False,
    enable_join_analysis=False,
    enable_duality_view_analysis=False,
    min_confidence_threshold=0.3,
)

# Workload 3: Orders (Hybrid → Duality Views)
PipelineConfig(
    enable_join_analysis=True,
    enable_duality_view_analysis=True,
    enable_lob_detection=False,
    enable_document_analysis=False,
    min_confidence_threshold=0.3,
)
```

## 📝 Next Steps

### Completed ✅
1. ✅ Run simulation with `--skip-pipeline` to verify workload execution
2. ✅ Schema creation and data generation working
3. ✅ Workload execution successful (166 reads, 8 writes in 60s)
4. ✅ Fixed SQL parsing to handle multi-line statements with comments

### Pending ⏳
1. ⏳ Grant AWR permissions to iris_user (SELECT on V$PARAMETER, DBA_HIST_*)
2. ⏳ Run full simulation with pipeline analysis
3. ⏳ Validate recommendations match expected outcomes

### Future Enhancements
1. Add more workload scenarios (LOB cliff detection)
2. Implement automated recommendation acceptance testing
3. Add performance benchmarking
4. Create CI/CD pipeline for automated testing
5. Generate comprehensive test reports

## 🐛 Troubleshooting

### AWR Not Enabled
```sql
-- Check statistics_level
SELECT value FROM V$PARAMETER WHERE name = 'statistics_level';

-- Enable AWR (requires SYSDBA)
ALTER SYSTEM SET statistics_level = TYPICAL;
```

### Permission Issues
```sql
-- Grant AWR permissions
GRANT SELECT ON DBA_HIST_SNAPSHOT TO iris_user;
GRANT SELECT ON DBA_HIST_SQLSTAT TO iris_user;
GRANT EXECUTE ON DBMS_WORKLOAD_REPOSITORY TO iris_user;
```

### Snapshot Creation Fails
```bash
# Check if snapshots are being created
sqlplus iris_user/IrisUser123!@localhost:1524/FREEPDB1
SELECT snap_id, TO_CHAR(begin_interval_time, 'YYYY-MM-DD HH24:MI:SS')
FROM DBA_HIST_SNAPSHOT
ORDER BY snap_id DESC
FETCH FIRST 10 ROWS ONLY;
```

## 📚 References

- **Workload Specifications**: `docs/SIMULATION_WORKLOADS.md`
- **Simulation README**: `tests/simulations/README.md`
- **Pipeline Architecture**: `docs/IRIS.md`
- **Implementation Plan**: `docs/IMPLEMENTATION_PLAN.md`
