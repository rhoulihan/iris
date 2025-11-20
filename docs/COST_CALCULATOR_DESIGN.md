# Cost Calculator Module Design

**Phase**: 2
**Status**: In Progress
**Last Updated**: 2025-11-20

---

## Overview

The Cost Calculator module quantifies the business value of pattern detection findings by:
1. Estimating current costs of anti-patterns
2. Projecting costs after optimization
3. Calculating implementation effort
4. Computing ROI and priority scores
5. Generating actionable, prioritized recommendations

---

## Architecture

### Module Structure

```
src/recommendation/
├── cost_calculator.py          # Main cost calculation engine
├── cost_models.py              # Cost model definitions
└── roi_calculator.py           # ROI and priority scoring
```

### Core Components

1. **CostEstimator** - Base class for cost estimation
2. **PatternCostCalculator** - Pattern-specific cost calculators
   - LOBCliffCostCalculator
   - JoinDenormalizationCostCalculator
   - DocumentStorageCostCalculator
   - DualityViewCostCalculator
3. **ROICalculator** - Computes ROI and net benefit
4. **PriorityScorer** - Ranks recommendations by priority

---

## Cost Model Design

### Input Data

```python
@dataclass
class CostCalculationInput:
    """Input for cost calculation."""
    pattern: DetectedPattern          # From Pattern Detector
    table_metadata: TableMetadata     # Schema information
    workload: WorkloadFeatures        # Query patterns
    cost_config: CostConfiguration    # Tunable cost parameters
```

### Output Data

```python
@dataclass
class CostEstimate:
    """Cost estimate for a detected pattern."""
    pattern_id: str
    pattern_type: str

    # Cost breakdown
    current_cost_per_day: float       # Cost with anti-pattern ($/day)
    optimized_cost_per_day: float     # Cost after optimization ($/day)
    implementation_cost: float        # One-time implementation cost ($)

    # Savings and ROI
    annual_savings: float             # (current - optimized) * 365
    net_benefit: float                # annual_savings - implementation_cost
    roi_percentage: float             # (net_benefit / implementation_cost) * 100
    payback_period_days: int          # implementation_cost / daily_savings

    # Priority
    priority_score: float             # 0-100 composite score
    priority_tier: str                # HIGH, MEDIUM, LOW

    # Cost components breakdown
    cost_breakdown: Dict[str, float]  # Detailed cost factors
    assumptions: List[str]            # Assumptions made in calculation
```

---

## Cost Models by Pattern Type

### 1. LOB Cliff Cost Model

**Current Cost Components:**
- **I/O Read Cost**: Reading large LOB on every SELECT
  - `read_cost = num_reads * avg_lob_size_kb * cost_per_kb_read`
- **I/O Write Amplification**: Writing entire LOB for small updates
  - `write_cost = num_updates * avg_lob_size_kb * cost_per_kb_write`
- **Block Chaining Cost**: Fragmentation from updates
  - `chain_cost = num_updates * chain_overhead_factor`

**Optimized Cost:**
- **Separated LOB Storage**: LOB in separate table/SecureFile
  - `optimized_read_cost = num_reads * avg_lob_size_kb * cost_per_kb_read * 0.7`  # 30% reduction
  - `optimized_write_cost = num_updates * updated_bytes * cost_per_kb_write`  # Only updated bytes

**Implementation Cost:**
- Schema refactoring (LOW-MEDIUM): $500-$2,000
- Data migration (MEDIUM-HIGH): $1,000-$5,000
- Application changes (LOW): $200-$1,000

**Formula:**
```python
daily_savings = (current_read + current_write + chain_cost) -
                (optimized_read + optimized_write)
annual_savings = daily_savings * 365
roi = (annual_savings - implementation_cost) / implementation_cost * 100
```

---

### 2. Join Denormalization Cost Model

**Current Cost Components:**
- **Join CPU Cost**: Processing joins
  - `join_cpu_cost = num_joins * join_cardinality * cpu_cost_per_row`
- **Join I/O Cost**: Reading dimension table
  - `join_io_cost = num_joins * dimension_rows * cost_per_row_read`
- **Network Cost**: Transferring joined data
  - `network_cost = num_joins * data_transferred_kb * network_cost_per_kb`

**Optimized Cost:**
- **Denormalized Read**: Direct access, no join
  - `denorm_read_cost = num_queries * cost_per_row_read`  # Single table access
- **Update Propagation**: Cost to keep denormalized data in sync
  - `sync_cost = num_dim_updates * num_fact_rows * cost_per_update`

**Implementation Cost:**
- Schema changes (MEDIUM): $1,000-$3,000
- Trigger/sync logic (MEDIUM-HIGH): $2,000-$5,000
- Testing (MEDIUM): $1,000-$2,000

**Formula:**
```python
current_cost = join_cpu_cost + join_io_cost + network_cost
optimized_cost = denorm_read_cost + sync_cost
daily_savings = current_cost - optimized_cost
# Only recommend if daily_savings > 0
```

---

### 3. Document Storage Cost Model

**Current Cost (Relational):**
- **Wide Row Fetch**: Reading many columns
  - `row_fetch_cost = num_selects * num_columns * cost_per_column`
- **Index Maintenance**: Multiple indexes on columns
  - `index_cost = num_updates * num_indexes * index_update_cost`
- **Storage**: Normalized table storage
  - `storage_cost = table_size_gb * cost_per_gb_per_day`

**Optimized Cost (JSON):**
- **Document Fetch**: Single JSON column
  - `json_fetch_cost = num_selects * json_doc_size_kb * cost_per_kb_read`
- **Index Maintenance**: JSON indexes only
  - `json_index_cost = num_updates * num_json_indexes * json_index_cost`
- **Storage**: JSON collection storage
  - `json_storage_cost = json_collection_size_gb * cost_per_gb_per_day * 0.8`  # 20% savings

**Implementation Cost:**
- Schema redesign (MEDIUM-HIGH): $2,000-$5,000
- Data transformation (HIGH): $3,000-$8,000
- Application refactoring (HIGH): $5,000-$10,000

**Formula:**
```python
# Calculate document score difference
doc_benefit_score = document_score - relational_score
if doc_benefit_score > 0.3:  # Strong document candidate
    daily_savings = current_cost - optimized_cost
    # Factor in higher implementation cost
```

---

### 4. JSON Duality View Cost Model

**Current Cost (Dual Systems):**
- **Redundant Storage**: Storing same data in RDBMS + JSON/NoSQL
  - `redundant_storage = data_size_gb * 2 * cost_per_gb_per_day`
- **Sync Overhead**: Keeping systems in sync
  - `sync_cost = num_updates * sync_latency_ms * cost_per_ms`
- **Operational Complexity**: Managing two systems
  - `ops_cost = fixed_ops_cost_per_day`

**Optimized Cost (Duality View):**
- **Single Storage**: Data stored once
  - `single_storage = data_size_gb * cost_per_gb_per_day`
- **View Overhead**: Minimal materialization cost
  - `view_cost = num_queries * view_overhead_factor`

**Implementation Cost:**
- Create duality views (LOW-MEDIUM): $500-$2,000
- Update application endpoints (MEDIUM): $1,000-$3,000
- Remove old NoSQL system (HIGH): $3,000-$8,000

**Formula:**
```python
# High value due to eliminating entire parallel system
daily_savings = redundant_storage + sync_cost + ops_cost - (single_storage + view_cost)
annual_savings = daily_savings * 365
# Often very high ROI due to operational simplification
```

---

## Cost Configuration

### Tunable Parameters

```python
@dataclass
class CostConfiguration:
    """Configurable cost parameters for different environments."""

    # I/O costs ($/KB)
    cost_per_kb_read: float = 0.0001       # $0.0001 per KB read
    cost_per_kb_write: float = 0.0002      # $0.0002 per KB write

    # CPU costs
    cpu_cost_per_row: float = 0.000001     # $0.000001 per row processed

    # Storage costs ($/GB/day)
    cost_per_gb_per_day: float = 0.03      # $0.03 per GB per day

    # Network costs
    network_cost_per_kb: float = 0.00005   # $0.00005 per KB transferred

    # Implementation costs (labor)
    hourly_rate: float = 150.0             # $150/hour developer rate

    # Time estimates (hours)
    schema_change_hours: float = 8.0       # 1 day for schema change
    migration_hours: float = 16.0          # 2 days for data migration
    app_change_hours: float = 40.0         # 5 days for app changes
    testing_hours: float = 16.0            # 2 days for testing

    # Risk factors
    risk_multiplier: float = 1.2           # 20% buffer for risks
```

---

## Priority Scoring Algorithm

### Priority Score Calculation

```python
def calculate_priority_score(cost_estimate: CostEstimate) -> float:
    """
    Calculate priority score (0-100) based on multiple factors.

    Factors:
    1. ROI (30%) - Higher ROI = higher priority
    2. Annual Savings (25%) - Absolute value matters
    3. Payback Period (20%) - Shorter payback = higher priority
    4. Implementation Cost (15%) - Lower cost = easier to approve
    5. Pattern Severity (10%) - HIGH severity patterns prioritized
    """

    # Normalize each factor to 0-1 scale
    roi_score = normalize_roi(cost_estimate.roi_percentage)
    savings_score = normalize_savings(cost_estimate.annual_savings)
    payback_score = normalize_payback(cost_estimate.payback_period_days)
    impl_score = normalize_impl_cost(cost_estimate.implementation_cost)
    severity_score = severity_to_score(cost_estimate.pattern.severity)

    # Weighted combination
    priority = (
        roi_score * 0.30 +
        savings_score * 0.25 +
        payback_score * 0.20 +
        impl_score * 0.15 +
        severity_score * 0.10
    ) * 100

    return min(100.0, max(0.0, priority))
```

### Priority Tiers

- **HIGH**: Priority score >= 70
  - ROI > 200% OR Annual savings > $50,000 OR Payback < 30 days
- **MEDIUM**: Priority score 40-69
  - ROI 100-200% OR Annual savings $10,000-$50,000
- **LOW**: Priority score < 40
  - ROI < 100% OR Annual savings < $10,000

---

## Example Calculations

### Example 1: LOB Cliff on AUDIT_LOGS

**Input:**
- Table: AUDIT_LOGS (5M rows)
- LOB Column: PAYLOAD (8KB average, CLOB)
- Reads: 10,000/day
- Updates: 500/day (5% of payload updated)

**Current Cost:**
```
Read cost = 10,000 * 8 * 0.0001 = $8/day
Write amplification = 500 * 8 * 0.0002 = $0.80/day
Chain overhead = 500 * 0.01 = $5/day
Total current = $13.80/day = $5,037/year
```

**Optimized Cost (SecureFile):**
```
Read cost = 10,000 * 8 * 0.0001 * 0.7 = $5.60/day  (30% improvement)
Write cost = 500 * 0.4 * 0.0002 = $0.04/day  (only updated bytes)
Total optimized = $5.64/day = $2,059/year
```

**Savings & ROI:**
```
Annual savings = $5,037 - $2,059 = $2,978
Implementation cost = $3,500 (schema + migration + testing)
Net benefit = $2,978 - $3,500 = -$522 (negative in year 1)
Payback period = $3,500 / ($13.80 - $5.64) = 429 days (~14 months)
ROI (3-year) = (($2,978 * 3) - $3,500) / $3,500 = 155%
```

**Priority Score**: MEDIUM (55/100)

---

### Example 2: Expensive Join (ORDERS ↔ CUSTOMERS)

**Input:**
- Join frequency: 50,000/day
- Dimension size: 100K customers
- Fact size: 10M orders
- Columns denormalized: 3 (NAME, TIER, EMAIL)

**Current Cost:**
```
Join CPU = 50,000 * 100,000 * 0.000001 = $5,000/day (!!)
Join I/O = 50,000 * 5 * 0.0001 = $25/day
Total current = $5,025/day = $1,834,125/year
```

**Optimized Cost:**
```
Denorm reads = 50,000 * 0.0001 = $5/day
Dimension updates = 50/day * 10M * 0.000001 = $500/day
Total optimized = $505/day = $184,325/year
```

**Savings & ROI:**
```
Annual savings = $1,834,125 - $184,325 = $1,649,800 (!!)
Implementation cost = $8,000 (schema + triggers + testing)
Net benefit = $1,649,800 - $8,000 = $1,641,800
ROI = ($1,641,800 / $8,000) * 100 = 20,522% (!!!)
Payback = 8,000 / 4,520 = 1.8 days (!!)
```

**Priority Score**: HIGH (98/100)

---

## Testing Strategy

### Unit Tests

1. **Cost Calculation Tests**
   - Test each pattern-specific calculator
   - Verify formulas with known inputs
   - Test edge cases (zero costs, negative savings)

2. **ROI Calculator Tests**
   - Test ROI formulas
   - Test payback period calculation
   - Test with various time horizons

3. **Priority Scorer Tests**
   - Test priority score calculation
   - Test tier assignment
   - Test normalization functions

### Integration Tests

1. **End-to-End Flow**
   - Pattern Detector → Cost Calculator
   - Use synthetic workloads from Phase 1
   - Verify realistic cost estimates

2. **Sensitivity Analysis**
   - Test with different cost configurations
   - Verify priority rankings change appropriately

---

## Implementation Plan

### Phase 2.1: Core Cost Models (Day 1)
- [ ] Define cost model data structures
- [ ] Implement CostConfiguration
- [ ] Create CostEstimate and supporting models
- [ ] Write unit tests for models

### Phase 2.2: Pattern-Specific Calculators (Day 2)
- [ ] LOBCliffCostCalculator
- [ ] JoinDenormalizationCostCalculator
- [ ] DocumentStorageCostCalculator
- [ ] DualityViewCostCalculator
- [ ] Comprehensive unit tests for each

### Phase 2.3: ROI & Priority Scoring (Day 2-3)
- [ ] ROICalculator implementation
- [ ] PriorityScorer implementation
- [ ] Priority tier assignment logic
- [ ] Unit tests for ROI and priority

### Phase 2.4: Integration & Validation (Day 3)
- [ ] Integrate with Pattern Detector output
- [ ] End-to-end integration tests
- [ ] Validate with realistic scenarios
- [ ] Document assumptions and limitations

---

## Success Criteria

✅ All unit tests passing
✅ Integration with Pattern Detector validated
✅ Realistic cost estimates for all pattern types
✅ Priority scores correlate with expected business value
✅ Documentation complete with examples
✅ Ready for Phase 3 (LLM Integration)

---

## Future Enhancements

1. **Machine Learning Cost Models**: Learn from historical migrations
2. **Multi-Year Projections**: NPV calculations for long-term planning
3. **Risk Assessment**: Incorporate migration risk into calculations
4. **Custom Cost Profiles**: Industry-specific cost parameters
5. **Batch Optimization**: Recommend optimal order for implementing changes
