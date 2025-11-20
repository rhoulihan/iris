# Synthetic Workload Scenarios for IRIS Testing

This document defines comprehensive synthetic workloads for end-to-end testing of the IRIS recommendation engine.

## Overview

We test the complete data pipeline:
```
AWR Data → Query Parser → Workload Compressor → Feature Engineer →
Schema Collector → Pattern Detector → Validation
```

## Scenario Categories

### 1. Clear Positive Cases (Should Detect Patterns)

#### Scenario 1.1: E-Commerce with Expensive Joins
**Schema**: Normalized e-commerce (orders, customers, products, order_items)
**Pattern**: EXPENSIVE_JOIN
**Workload**: 80% of queries join orders → customers to fetch customer_name, customer_tier
**Expected**: Recommend denormalizing customer_name, customer_tier into orders table
**Metrics**:
- Join frequency: 80% of 10,000 queries/day
- Columns fetched: 2 (name, tier)
- Dimension table: 50,000 customers (stable)
- Net benefit: High (join cost >> update propagation cost)

#### Scenario 1.2: Document Storage Anti-Pattern
**Schema**: User profiles stored as relational (users table with 20+ columns)
**Pattern**: DOCUMENT_CANDIDATE
**Workload**: 90% SELECT *, 5% single-column updates, 5% reads
**Expected**: Recommend JSON collection with document storage
**Metrics**:
- SELECT * percentage: 90%
- Nullable columns: 60% (schema flexibility)
- Multi-column updates: 70%
- No aggregates or joins

#### Scenario 1.3: LOB Cliff Anti-Pattern
**Schema**: Audit logs with large JSON payloads in CLOB
**Pattern**: LOB_CLIFF
**Workload**: Frequent small updates to status field within 8KB JSON documents
**Expected**: Detect LOB cliff, recommend splitting metadata
**Metrics**:
- Document size: 8KB average (above 4KB threshold)
- Update frequency: 500/day
- Update selectivity: 0.05 (5% of document modified)
- Format: TEXT JSON in CLOB (inefficient)

#### Scenario 1.4: Duality View Opportunity
**Schema**: Product catalog with both transactional and analytical access
**Pattern**: DUALITY_VIEW_OPPORTUNITY
**Workload**: 40% OLTP (INSERT/UPDATE product), 35% Analytics (aggregates, reporting)
**Expected**: Recommend JSON Duality View for dual representation
**Metrics**:
- OLTP percentage: 40%
- Analytics percentage: 35%
- Duality score: 0.35 (HIGH severity)

---

### 2. Clear Negative Cases (Should NOT Detect Patterns)

#### Scenario 2.1: Efficient Normalized Schema
**Schema**: Well-normalized inventory system
**Workload**: Column-specific queries, appropriate indexes, low join cost
**Expected**: No recommendations
**Reasoning**: System is already optimized

#### Scenario 2.2: Pure Relational Workload
**Schema**: Analytics data warehouse
**Workload**: 100% aggregates, complex joins, no SELECT *
**Expected**: RELATIONAL_CANDIDATE (not document)
**Reasoning**: Relational storage is optimal

---

### 3. Edge Cases and Nuanced Scenarios (Requires Careful Analysis)

#### Scenario 3.1: LOB Cliff FALSE POSITIVE - Cached Read-Heavy
**Schema**: Document repository with large JSON documents (10KB)
**Pattern**: Should NOT flag LOB_CLIFF despite large size
**Workload**:
- Small updates: 10/day (LOW frequency, below 100 threshold)
- Large reads: 50,000/day (read-heavy)
- Cache hit rate: 95%
**Expected**: No LOB cliff detection
**Reasoning**: Low update frequency + high caching = no performance issue
**Tuning Required**: Update frequency threshold (100/day) should prevent detection

#### Scenario 3.2: Join Denormalization FALSE POSITIVE - Volatile Dimension
**Schema**: Orders → Products join for product_name, product_price
**Pattern**: Should NOT recommend denormalization despite expensive join
**Workload**:
- Join frequency: 70% (high)
- Dimension updates: 500/day (product prices change frequently)
- Dimension size: 100,000 products
**Expected**: No denormalization recommendation
**Reasoning**: Update propagation cost > join cost
**Tuning Required**: Net benefit calculation should account for high update rate

#### Scenario 3.3: Document Storage FALSE POSITIVE - Mixed Access
**Schema**: Event logs with both object access and aggregations
**Pattern**: Neutral (no clear recommendation)
**Workload**:
- SELECT *: 40%
- Aggregates (COUNT, SUM): 45%
- Joins: 15%
**Expected**: No recommendation (document_score - relational_score < 0.3)
**Reasoning**: Mixed access patterns, no clear winner
**Metrics**:
- Document score: 0.4 (40% SELECT * × 1.0)
- Relational score: 0.45 (45% aggregates × 0.5 + 15% joins × 0.5)
- Net score: -0.05 (below 0.3 threshold)

#### Scenario 3.4: Duality View FALSE POSITIVE - Low Volume
**Schema**: Admin configuration table with dual access
**Pattern**: Should NOT recommend duality view despite balanced access
**Workload**:
- OLTP: 30% (balanced)
- Analytics: 25% (balanced)
- Total queries: 50/day (LOW volume)
**Expected**: Detection but LOW severity / questioned benefit
**Reasoning**: Duality view overhead not justified for low-volume table
**Metrics**:
- Duality score: 0.25 (MEDIUM severity based on current thresholds)
**Tuning Required**: Consider adding minimum volume threshold

#### Scenario 3.5: Selective LOB Update with High Selectivity
**Schema**: Product catalog with large image metadata JSON (12KB)
**Pattern**: Should flag LOB_CLIFF
**Workload**:
- Document size: 12KB (3x threshold)
- Updates: 200/day (2x threshold)
- Update selectivity: 0.02 (only 2% modified - price field)
- Format: CLOB (text JSON)
**Expected**: Detect LOB_CLIFF with HIGH severity
**Reasoning**: All risk factors present
**Metrics**:
- Risk score: 0.3 (size) + 0.3 (freq) + 0.2 (selectivity) + 0.2 (format) = 1.0

#### Scenario 3.6: Join with Small Dimension but Many Columns
**Schema**: Orders → CustomerPreferences (50 preference columns)
**Pattern**: Should NOT recommend denormalization
**Workload**:
- Join frequency: 60%
- Columns fetched: 15 (exceeds 5-column threshold)
- Dimension size: 10,000 rows (small)
**Expected**: No recommendation
**Reasoning**: Too many columns to denormalize (complexity/maintenance)
**Tuning Required**: max_columns_fetched threshold (5) should prevent detection

---

## Test Data Requirements

### Schema Definitions
Each scenario requires:
1. Table DDL (CREATE TABLE statements)
2. Sample data (representative row counts)
3. Index definitions

### Synthetic AWR Data
For each scenario, generate:
1. `DBA_HIST_SNAPSHOT` - Snapshot metadata
2. `DBA_HIST_SQLTEXT` - SQL statements
3. `DBA_HIST_SQLSTAT` - Execution statistics (executions, elapsed_time, etc.)
4. `DBA_HIST_SQL_PLAN` - Execution plans (for join analysis)
5. `DBA_HIST_SEG_STAT` - Segment statistics (table access patterns)
6. `DBA_HIST_SYSSTAT` - System statistics

### Workload Characteristics
- **Duration**: 1-hour snapshot window
- **Query Volume**: 1,000 - 50,000 queries/hour depending on scenario
- **Query Diversity**: Mix of SELECT, INSERT, UPDATE, DELETE
- **Execution Patterns**: Realistic distributions (Pareto: 20% queries = 80% executions)

---

## Validation Criteria

### Pattern Detection Accuracy
For each scenario:
- ✅ **True Positive**: Correctly detects intended pattern
- ✅ **True Negative**: Correctly ignores non-pattern
- ❌ **False Positive**: Incorrectly flags pattern when shouldn't
- ❌ **False Negative**: Misses pattern that should be detected

### Metrics Accuracy
Validate that detected patterns have correct:
- Pattern type
- Severity level (HIGH, MEDIUM, LOW)
- Confidence score (0.0-1.0)
- Affected objects
- Metrics (risk scores, percentages, costs)

### Threshold Tuning
Based on edge case results, tune:
- LOB cliff update frequency threshold (currently 100/day)
- Join dimension max_columns_fetched (currently 5)
- Document/relational strong signal threshold (currently 0.3)
- Duality view minimum volume threshold (not currently implemented)

---

## Implementation Plan

### Phase 1: Schema and Data Generation
1. Create schema definitions for all scenarios
2. Build synthetic AWR data generator
3. Generate test datasets

### Phase 2: Integration Test Framework
1. End-to-end pipeline test harness
2. Data flow validation at each stage
3. Pattern detection assertions

### Phase 3: Edge Case Validation
1. Run all 6 edge case scenarios
2. Validate expected behavior
3. Document any threshold tuning needed

### Phase 4: Reporting and Documentation
1. Test coverage report
2. Pattern detection accuracy metrics
3. Recommendations for threshold adjustments

---

## Expected Outcomes

### Success Criteria
- **100% accuracy** on clear positive cases (Scenarios 1.1-1.4)
- **100% accuracy** on clear negative cases (Scenarios 2.1-2.2)
- **≥80% accuracy** on edge cases (Scenarios 3.1-3.6)
- All data pipeline stages validated end-to-end
- Documented threshold tuning recommendations

### Deliverables
1. Synthetic workload generator tool
2. Complete integration test suite
3. Validation report with findings
4. Updated thresholds (if needed)
5. Edge case documentation for future reference
