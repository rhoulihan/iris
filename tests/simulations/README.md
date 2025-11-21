# IRIS Pipeline Simulations

This directory contains comprehensive simulation workloads for testing and validating the IRIS recommendation pipeline.

## 📁 Directory Structure

```
tests/simulations/
├── README.md                           # This file
├── run_simulation.py                   # CLI entry point
├── test_pipeline_simulations.py        # Integration tests
├── sql/                                # SQL schema files
│   ├── workload1_schema.sql           # E-Commerce schema
│   ├── workload2_schema.sql           # Inventory schema
│   ├── workload3_schema.sql           # Orders schema
│   └── cleanup.sql                     # Cleanup all schemas
├── data_generators/                    # Data generation scripts
│   ├── ecommerce_generator.py         # Workload 1 data
│   ├── inventory_generator.py         # Workload 2 data
│   └── orders_generator.py            # Workload 3 data
└── workloads/                          # Workload execution scripts
    ├── workload1_ecommerce.py         # E-Commerce query patterns
    ├── workload2_inventory.py         # Inventory query patterns
    └── workload3_orders.py            # Orders query patterns
```

## 🎯 Workload Descriptions

### Workload 1: E-Commerce User Profiles
**Expected Recommendation**: Document Storage

- **Pattern**: Relational → Document
- **Read/Write Ratio**: 95:5 (highly read-heavy)
- **Schema**: 4-table relational (customers, addresses, preferences, orders)
- **Key Signal**: Frequent 3-4 table joins fetching entire customer profile
- **Confidence**: HIGH
- **Benefit**: 80% latency reduction (15ms → 3ms)

### Workload 2: Real-Time Inventory Management
**Expected Recommendation**: Relational Normalization

- **Pattern**: Document → Relational
- **Read/Write Ratio**: 30:70 (write-heavy)
- **Schema**: JSON documents with nested arrays
- **Key Signal**: High update velocity, frequent JSON_TRANSFORM, growing arrays
- **Confidence**: HIGH
- **Benefit**: 90% update time reduction (20ms → 2ms)

### Workload 3: Sales Order System with Analytics
**Expected Recommendation**: Duality Views

- **Pattern**: Hybrid OLTP/Analytics
- **Read/Write Ratio**: 60% OLTP, 40% Analytics
- **Schema**: Relational with complex joins
- **Key Signal**: Dual access patterns (transactional + JSON aggregation)
- **Confidence**: MEDIUM-HIGH
- **Benefit**: Support both patterns without duplication

## 🚀 Quick Start

### Prerequisites

1. Oracle Database 23ai or later running
2. Python virtual environment activated
3. Required Python packages installed (faker, oracledb)

```bash
# Install additional dependencies
pip install faker
```

### Running Simulations

#### Run Single Workload

```bash
# Workload 1: E-Commerce (5 minutes, small dataset)
python tests/simulations/run_simulation.py --workload 1 --duration 300 --scale small

# Workload 2: Inventory (10 minutes, medium dataset)
python tests/simulations/run_simulation.py --workload 2 --duration 600 --scale medium

# Workload 3: Orders (5 minutes, large dataset)
python tests/simulations/run_simulation.py --workload 3 --duration 300 --scale large
```

#### Run All Workloads

```bash
# Run all three workloads sequentially
python tests/simulations/run_simulation.py --workload all --duration 300 --scale small
```

#### Use Existing Data

```bash
# Skip data generation (use existing data)
python tests/simulations/run_simulation.py --workload 1 --duration 300 --skip-data-gen
```

#### Cleanup

```bash
# Remove all workload schemas and data
python tests/simulations/run_simulation.py --cleanup
```

### Custom Connection String

```bash
# Specify custom Oracle connection
python tests/simulations/run_simulation.py \
    --workload 1 \
    --duration 300 \
    --connection iris_user/IrisUser123!@localhost:1524/FREEPDB1
```

## 📊 Data Scales

| Scale | Workload 1 | Workload 2 | Workload 3 |
|-------|------------|------------|------------|
| **Small** | 100 customers | 50 items | 500 orders |
| **Medium** | 1,000 customers | 500 items | 5,000 orders |
| **Large** | 10,000 customers | 5,000 items | 50,000 orders |

**Note**: Data generation time increases significantly with scale.

## 🧪 Integration Tests

Run integration tests using pytest:

```bash
# Run all simulation tests
pytest tests/simulations/test_pipeline_simulations.py -v

# Run specific workload test
pytest tests/simulations/test_pipeline_simulations.py::TestWorkload1ECommerce -v

# Run with markers
pytest tests/simulations/ -m integration -v
```

## 📝 Workload Execution Flow

Each simulation follows this workflow:

1. **Schema Creation**
   - Load SQL schema from `sql/workloadN_schema.sql`
   - Create tables, indexes, sequences

2. **Data Generation**
   - Use data generator from `data_generators/`
   - Generate realistic data using Faker library
   - Insert data in batches for performance

3. **Workload Execution**
   - Execute query patterns from `workloads/`
   - Maintain target throughput (queries per second)
   - Log progress and statistics

4. **Pipeline Analysis** (TODO)
   - Collect AWR snapshots
   - Run PipelineOrchestrator
   - Generate recommendations
   - Validate against expected outcomes

5. **Cleanup** (optional)
   - Drop tables, sequences, indexes
   - Reset database to clean state

## 🎛️ Configuration Options

### Duration (`--duration`)
- Default: 300 seconds (5 minutes)
- Minimum: 60 seconds (for meaningful AWR data)
- Recommended: 300-600 seconds per workload

### Scale (`--scale`)
- **small**: Fast generation (~1 min), suitable for quick tests
- **medium**: Moderate generation (~5-10 min), realistic workload
- **large**: Slow generation (~30-60 min), production-like scale

### Skip Data Generation (`--skip-data-gen`)
- Use when schema and data already exist
- Useful for re-running workloads with different durations
- Reduces setup time significantly

## 🔍 Validation Criteria

Each workload has specific success criteria defined in `docs/SIMULATION_WORKLOADS.md`:

### Workload 1 Success
- ✅ JoinDimensionAnalyzer detects expensive joins
- ✅ DocumentRelationalClassifier recommends DOCUMENT storage
- ✅ Confidence ≥ 0.7
- ✅ Priority = HIGH
- ✅ Generated SQL includes JSON document schema

### Workload 2 Success
- ✅ DocumentRelationalClassifier recommends RELATIONAL schema
- ✅ Confidence ≥ 0.7
- ✅ Priority = HIGH
- ✅ Generated SQL includes normalized relational tables

### Workload 3 Success
- ✅ DualityViewOpportunityFinder detects hybrid pattern
- ✅ Recommendation includes Duality View creation
- ✅ Confidence ≥ 0.7
- ✅ Priority = MEDIUM or HIGH
- ✅ Generated SQL includes CREATE JSON RELATIONAL DUALITY VIEW

## 📈 Expected Query Patterns

### Workload 1: E-Commerce
- **Read Queries** (95%):
  - 70%: Full profile fetch (4-table join)
  - 20%: Profile by email (2-table join)
  - 10%: Preference lookup (single table)

- **Write Queries** (5%):
  - 40%: New customer registration
  - 30%: Add address
  - 20%: Update preference
  - 10%: Update loyalty tier

### Workload 2: Inventory
- **Read Queries** (30%):
  - 60%: Stock level check (JSON_VALUE)
  - 30%: Available quantity (JSON_VALUE with calculation)
  - 10%: Warehouse lookup (JSON_EXISTS - table scan!)

- **Write Queries** (70%):
  - 40%: Update stock quantity (JSON_TRANSFORM)
  - 30%: Reserve stock (JSON_TRANSFORM with arithmetic)
  - 20%: Add transaction (JSON_TRANSFORM APPEND)
  - 10%: Insert new item

### Workload 3: Orders
- **OLTP Queries** (60%):
  - 50%: Order lookup (2-3 table join)
  - 20%: Create order
  - 20%: Add order items
  - 10%: Update order status

- **Analytics Queries** (40%):
  - 25%: Daily sales summary (GROUP BY + aggregation)
  - 25%: Top products (complex join + aggregation)
  - 25%: Customer history (JSON_ARRAYAGG)
  - 25%: Real-time dashboard (aggregation)

## 🐛 Troubleshooting

### Connection Errors
```bash
# Verify Oracle is running
docker ps | grep oracle

# Test connection manually
sqlplus iris_user/IrisUser123!@localhost:1524/FREEPDB1
```

### Data Generation Fails
```bash
# Check disk space
df -h

# Check Oracle tablespace
SELECT tablespace_name, SUM(bytes)/1024/1024 AS MB FROM dba_free_space GROUP BY tablespace_name;
```

### Workload Execution Slow
```bash
# Reduce duration
--duration 60

# Use smaller scale
--scale small

# Check system resources
top
```

### Cleanup Fails
```bash
# Manual cleanup via SQL*Plus
sqlplus iris_user/IrisUser123!@localhost:1524/FREEPDB1
@tests/simulations/sql/cleanup.sql
```

## 📚 Additional Resources

- **Workload Specifications**: See `docs/SIMULATION_WORKLOADS.md`
- **Pipeline Architecture**: See `docs/IRIS.md`
- **Implementation Plan**: See `docs/IMPLEMENTATION_PLAN.md`

## 🤝 Contributing

To add new workloads:

1. Create SQL schema in `sql/workloadN_schema.sql`
2. Create data generator in `data_generators/workloadN_generator.py`
3. Create workload executor in `workloads/workloadN_execution.py`
4. Add integration tests in `test_pipeline_simulations.py`
5. Update this README with workload description
6. Document expected recommendations in `docs/SIMULATION_WORKLOADS.md`

## 📄 License

Part of the IRIS project. See main project LICENSE file.
