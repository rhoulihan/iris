# Recommendation Engine - Detailed Design Specification

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Module 1: Pattern Detector](#module-1-pattern-detector)
3. [Module 2: Cost Calculator](#module-2-cost-calculator)
4. [Module 3: Tradeoff Analyzer](#module-3-tradeoff-analyzer)
5. [Module 4: Recommendation Engine](#module-4-recommendation-engine)
6. [Data Flow & Integration](#data-flow--integration)
7. [Implementation Roadmap](#implementation-roadmap)

---

## Architecture Overview

### Core Principle
The Recommendation Engine is a **multi-stage pipeline** that transforms raw database performance data into actionable, prioritized schema optimization recommendations with quantified tradeoffs.

### Design Philosophy
1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Quantified Decision Making**: Every recommendation backed by numerical metrics
3. **Frequency-Weighted Optimization**: Optimize what runs most often
4. **Conservative Thresholds**: Only recommend when net benefit is clear
5. **LLM for Synthesis**: Use Claude to reason about complex multi-dimensional tradeoffs
6. **Explainability**: Every recommendation includes clear justification

### Module Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    Recommendation Engine                         │
│                    (Orchestrator Layer)                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
┌─────────────┐  ┌──────────────┐  ┌─────────────┐
│   Pattern   │  │     Cost     │  │  Tradeoff   │
│  Detector   │→ │  Calculator  │→ │  Analyzer   │
└─────────────┘  └──────────────┘  └─────────────┘
         ↓               ↓               ↓
    Patterns        Cost Metrics    Prioritized
   Detected        Calculated      Recommendations
```

---

## Module 1: Pattern Detector

### Purpose
Identify schema anti-patterns and optimization opportunities from workload and schema analysis.

### Input Schema
```python
@dataclass
class PatternDetectorInput:
    """Input to pattern detection module."""
    workload_features: Dict[str, Any]  # From FeatureEngineer
    schema_metadata: Dict[str, Any]    # From SchemaCollector
    performance_baseline: Dict[str, float]  # Current metrics (optional)
```

### Output Schema
```python
@dataclass
class DetectedPattern:
    """A detected anti-pattern or optimization opportunity."""
    pattern_id: str
    pattern_type: str  # "LOB_CLIFF", "EXPENSIVE_JOIN", "DOCUMENT_CANDIDATE", "DUALITY_OPPORTUNITY"
    severity: str  # "HIGH", "MEDIUM", "LOW"
    confidence: float  # 0.0-1.0
    affected_objects: List[str]  # Table/column names
    description: str
    metrics: Dict[str, Any]  # Pattern-specific metrics
    recommendation_hint: str  # Initial suggestion

@dataclass
class PatternDetectorOutput:
    """Output from pattern detection."""
    patterns: List[DetectedPattern]
    detection_timestamp: datetime
    analysis_summary: Dict[str, int]  # Count by pattern type
```

---

### Sub-Module 1.1: LOB Cliff Detector

**Objective**: Identify tables where small updates to large LOB/JSON columns cause performance issues.

#### Detection Algorithm

```python
def detect_lob_cliffs(
    tables: List[TableMetadata],
    workload: WorkloadFeatures
) -> List[DetectedPattern]:
    """Detect LOB cliff anti-patterns.

    LOB Cliff occurs when:
    1. Table has LOB/CLOB/JSON column
    2. Frequent small UPDATEs to that column
    3. Document size > threshold (e.g., 4KB for in-row storage limit)
    4. Updates cause out-of-line storage fragmentation

    Oracle 23ai Context:
    - OSON binary format is efficient for updates
    - Text JSON in CLOB is inefficient
    - In-Memory JSON optimization helps but doesn't prevent cliff
    """

    patterns = []

    for table in tables:
        # Step 1: Identify LOB/JSON columns
        lob_columns = [
            col for col in table.columns
            if col.data_type in ['CLOB', 'BLOB', 'JSON']
        ]

        if not lob_columns:
            continue

        # Step 2: Analyze update patterns
        update_queries = [
            q for q in workload.queries
            if q.query_type == 'UPDATE' and table.name in q.tables
        ]

        if not update_queries:
            continue

        for col in lob_columns:
            # Step 3: Calculate LOB cliff risk score
            avg_doc_size = get_avg_column_size(table, col)
            update_frequency = sum(q.executions for q in update_queries)
            update_selectivity = calculate_update_selectivity(update_queries, col)

            # Risk factors:
            # - Large documents (> 4KB out-of-line storage)
            # - High update frequency (> 100/day)
            # - Small updates (< 10% of document changed)
            # - Using text JSON (not OSON)

            risk_score = 0.0

            if avg_doc_size > 4096:  # Out-of-line storage
                risk_score += 0.3

            if update_frequency > 100:  # Frequent updates
                risk_score += 0.3

            if update_selectivity < 0.1:  # Small updates
                risk_score += 0.2

            if col.data_type == 'CLOB' and is_json_content(table, col):  # Text JSON
                risk_score += 0.2

            # Step 4: Generate pattern if risk exceeds threshold
            if risk_score >= 0.6:  # HIGH threshold
                severity = "HIGH" if risk_score >= 0.8 else "MEDIUM"

                patterns.append(DetectedPattern(
                    pattern_id=f"LOB_CLIFF_{table.name}_{col.name}",
                    pattern_type="LOB_CLIFF",
                    severity=severity,
                    confidence=risk_score,
                    affected_objects=[f"{table.name}.{col.name}"],
                    description=f"Frequent small updates to large {col.data_type} column causing LOB fragmentation",
                    metrics={
                        "avg_document_size_kb": avg_doc_size / 1024,
                        "updates_per_day": update_frequency,
                        "update_selectivity": update_selectivity,
                        "storage_type": "out_of_line" if avg_doc_size > 4096 else "in_row",
                        "format": "OSON" if col.data_type == 'JSON' else "TEXT",
                    },
                    recommendation_hint="Consider splitting document or using separate metadata table"
                ))

    return patterns
```

#### Key Metrics
- **Average Document Size**: Bytes per LOB/JSON column
- **Update Frequency**: Updates per day to LOB columns
- **Update Selectivity**: Percentage of document modified per update
- **Storage Type**: In-row vs out-of-line (4KB threshold)
- **Format**: OSON (binary) vs Text JSON

#### Recommendation Strategies
1. **Split Document**: Separate frequently-updated metadata from stable large content
2. **Separate Table**: Move LOB column to 1:1 related table
3. **Use Duality View**: If document needs both OLTP and analytics access
4. **Compress**: Use Oracle compression for rarely-updated LOBs

---

### Sub-Module 1.2: Join Dimension Analyzer

**Objective**: Identify expensive join patterns that could benefit from denormalization.

#### Detection Algorithm

```python
def analyze_join_dimensions(
    queries: List[QueryPattern],
    schema: SchemaMetadata
) -> List[DetectedPattern]:
    """Analyze join patterns for denormalization opportunities.

    Join Dimension: A table frequently joined to access a small set of columns.
    Common pattern: orders JOIN customers to get customer_name, customer_tier

    Denormalization candidate when:
    1. Join appears in >10% of queries
    2. Only 1-3 columns fetched from dimension table
    3. Dimension table is relatively small (< 1M rows) or stable
    4. Join cost > maintenance cost of denormalization
    """

    patterns = []

    # Step 1: Build join frequency matrix
    join_patterns = defaultdict(lambda: {
        "count": 0,
        "total_cost": 0.0,
        "columns_accessed": set(),
        "query_ids": []
    })

    for query in queries:
        if query.join_count > 0:
            for join in query.joins:
                join_key = f"{join.left_table}__{join.right_table}"
                join_patterns[join_key]["count"] += query.executions
                join_patterns[join_key]["total_cost"] += query.elapsed_time_ms * query.executions
                join_patterns[join_key]["columns_accessed"].update(join.columns_fetched)
                join_patterns[join_key]["query_ids"].append(query.query_id)

    # Step 2: Analyze each frequent join
    total_queries = sum(q.executions for q in queries)

    for join_key, metrics in join_patterns.items():
        left_table, right_table = join_key.split("__")

        # Calculate join frequency percentage
        join_frequency_pct = (metrics["count"] / total_queries) * 100

        if join_frequency_pct < 10:  # Low frequency, skip
            continue

        # Check column access pattern
        columns_accessed = metrics["columns_accessed"]
        dimension_table = schema.get_table(right_table)

        if len(columns_accessed) > 5:  # Too many columns, not a good candidate
            continue

        if dimension_table.num_rows > 1_000_000:  # Large dimension, expensive to denormalize
            # But check stability - if rarely updated, might still be worth it
            update_rate = get_update_rate(dimension_table, queries)
            if update_rate > 100:  # More than 100 updates/day
                continue

        # Step 3: Calculate denormalization benefit
        avg_join_cost_ms = metrics["total_cost"] / metrics["count"]

        # Estimate maintenance cost of denormalization
        update_propagation_cost = estimate_update_propagation_cost(
            dimension_table, left_table, columns_accessed
        )

        net_benefit_ms_per_day = (
            metrics["total_cost"] -  # Join cost saved
            update_propagation_cost  # Maintenance cost added
        )

        if net_benefit_ms_per_day > 0:  # Positive benefit
            severity = "HIGH" if net_benefit_ms_per_day > 10000 else "MEDIUM"
            confidence = min(join_frequency_pct / 100, 0.95)

            patterns.append(DetectedPattern(
                pattern_id=f"EXPENSIVE_JOIN_{join_key}",
                pattern_type="EXPENSIVE_JOIN",
                severity=severity,
                confidence=confidence,
                affected_objects=[left_table, right_table],
                description=f"Expensive join between {left_table} and {right_table} executed {metrics['count']} times/day",
                metrics={
                    "join_frequency_per_day": metrics["count"],
                    "join_frequency_percentage": join_frequency_pct,
                    "avg_join_cost_ms": avg_join_cost_ms,
                    "total_join_cost_ms_per_day": metrics["total_cost"],
                    "columns_accessed": list(columns_accessed),
                    "dimension_table_rows": dimension_table.num_rows,
                    "net_benefit_ms_per_day": net_benefit_ms_per_day,
                },
                recommendation_hint=f"Consider denormalizing {', '.join(columns_accessed)} into {left_table}"
            ))

    return patterns
```

#### Key Metrics
- **Join Frequency**: Percentage of queries containing this join
- **Join Cost**: Total execution time spent on joins per day
- **Column Selectivity**: Number of columns accessed from dimension
- **Dimension Size**: Row count of joined table
- **Update Rate**: Frequency of updates to dimension table
- **Net Benefit**: Join cost saved minus denormalization maintenance cost

#### Recommendation Strategies
1. **Column Denormalization**: Copy frequently-accessed columns to fact table
2. **Materialized View**: Create pre-joined view for analytics queries
3. **Caching**: Use Oracle TimesTen for dimension table caching
4. **Duality View**: If dimension needs both document and relational access

---

### Sub-Module 1.3: Document vs Relational Classifier

**Objective**: Identify tables that should be stored as documents vs relational structures.

#### Detection Algorithm

```python
def classify_document_vs_relational(
    tables: List[TableMetadata],
    queries: List[QueryPattern]
) -> List[DetectedPattern]:
    """Classify tables as document or relational candidates.

    Document Storage Indicators:
    1. Queries fetch entire rows (SELECT *)
    2. Nested/hierarchical data structure (1:many child tables)
    3. Schema flexibility needed (varying attributes)
    4. Object-oriented access pattern (always fetch complete object)

    Relational Storage Indicators:
    1. Column-specific queries (SELECT col1, col2)
    2. Aggregate queries (SUM, AVG, GROUP BY)
    3. Complex JOIN patterns across multiple tables
    4. Fixed schema with well-defined relationships
    """

    patterns = []

    for table in tables:
        # Analyze queries accessing this table
        table_queries = [q for q in queries if table.name in q.tables]

        if not table_queries:
            continue

        # Calculate document score (0.0 = relational, 1.0 = document)
        document_score = 0.0

        # Factor 1: SELECT * vs column-specific (40% weight)
        select_all_pct = sum(
            q.executions for q in table_queries if is_select_all(q)
        ) / sum(q.executions for q in table_queries)
        document_score += select_all_pct * 0.4

        # Factor 2: Object access pattern (30% weight)
        # Check if queries always fetch related child records
        has_child_tables = len(get_child_tables(table, schema)) > 0
        if has_child_tables:
            fetch_children_pct = calculate_child_fetch_percentage(table, table_queries)
            document_score += fetch_children_pct * 0.3

        # Factor 3: Schema flexibility needs (20% weight)
        # Check if table has many nullable columns (indicating varying attributes)
        nullable_column_pct = len([c for c in table.columns if c.nullable]) / len(table.columns)
        if nullable_column_pct > 0.5:
            document_score += 0.2

        # Factor 4: Update patterns (10% weight)
        # Document storage is better if updates affect multiple columns together
        multi_column_update_pct = calculate_multi_column_update_percentage(table, queries)
        document_score += multi_column_update_pct * 0.1

        # Countering factors for relational
        relational_score = 0.0

        # Aggregate queries favor relational
        aggregate_query_pct = sum(
            q.executions for q in table_queries if has_aggregates(q)
        ) / sum(q.executions for q in table_queries)
        relational_score += aggregate_query_pct * 0.5

        # Complex joins favor relational
        join_query_pct = sum(
            q.executions for q in table_queries if q.join_count > 2
        ) / sum(q.executions for q in table_queries)
        relational_score += join_query_pct * 0.5

        # Determine recommendation
        net_score = document_score - relational_score

        if abs(net_score) > 0.3:  # Strong signal
            if net_score > 0:  # Document candidate
                patterns.append(DetectedPattern(
                    pattern_id=f"DOCUMENT_CANDIDATE_{table.name}",
                    pattern_type="DOCUMENT_CANDIDATE",
                    severity="MEDIUM",
                    confidence=abs(net_score),
                    affected_objects=[table.name],
                    description=f"Table {table.name} accessed as complete objects, candidate for JSON document storage",
                    metrics={
                        "document_score": document_score,
                        "relational_score": relational_score,
                        "select_all_percentage": select_all_pct * 100,
                        "child_fetch_percentage": fetch_children_pct * 100 if has_child_tables else 0,
                        "nullable_column_percentage": nullable_column_pct * 100,
                        "multi_column_update_percentage": multi_column_update_pct * 100,
                    },
                    recommendation_hint=f"Convert {table.name} to JSON collection with document storage"
                ))
            else:  # Relational candidate (currently stored as document)
                patterns.append(DetectedPattern(
                    pattern_id=f"RELATIONAL_CANDIDATE_{table.name}",
                    pattern_type="RELATIONAL_CANDIDATE",
                    severity="MEDIUM",
                    confidence=abs(net_score),
                    affected_objects=[table.name],
                    description=f"Table {table.name} accessed with column-specific and aggregate queries, better as relational",
                    metrics={
                        "document_score": document_score,
                        "relational_score": relational_score,
                        "aggregate_query_percentage": aggregate_query_pct * 100,
                        "join_query_percentage": join_query_pct * 100,
                    },
                    recommendation_hint=f"Normalize {table.name} into relational structure"
                ))

    return patterns
```

#### Key Metrics
- **Document Score**: 0.0-1.0 indicating document storage suitability
- **SELECT * Percentage**: How often entire rows are fetched
- **Child Fetch Percentage**: How often related child records are fetched
- **Nullable Column Percentage**: Indicator of schema flexibility needs
- **Multi-Column Update Percentage**: Updates affecting multiple columns together
- **Aggregate Query Percentage**: Queries using SUM/AVG/GROUP BY (favors relational)
- **Join Query Percentage**: Complex join queries (favors relational)

#### Recommendation Strategies
1. **Convert to JSON Collection**: Store as JSON documents in Oracle 23ai
2. **Use JSON Duality View**: If both document and relational access needed
3. **Normalize**: Convert document to relational tables
4. **Hybrid**: Keep core attributes relational, flexible attributes as JSON column

---

### Sub-Module 1.4: Duality View Opportunity Finder

**Objective**: Identify tables that would benefit from JSON Duality Views (Oracle 23ai feature).

#### Detection Algorithm

```python
def find_duality_opportunities(
    tables: List[TableMetadata],
    queries: List[QueryPattern]
) -> List[DetectedPattern]:
    """Find opportunities for JSON Duality Views.

    Duality View is Oracle 23ai feature providing:
    - Document view for OLTP applications (JSON access)
    - Relational view for Analytics queries (SQL access)
    - Automatic synchronization between both

    Best candidates:
    1. Table accessed both as documents AND with analytics queries
    2. OLTP workload needs fast object access
    3. Analytics workload needs column-specific aggregations
    4. High enough query frequency to justify view overhead
    """

    patterns = []

    for table in tables:
        table_queries = [q for q in queries if table.name in q.tables]

        if not table_queries:
            continue

        # Classify queries into OLTP vs Analytics
        oltp_queries = []  # INSERT, UPDATE, DELETE, simple SELECT
        analytics_queries = []  # Complex SELECT with aggregates, joins

        for query in table_queries:
            if is_oltp_query(query):
                oltp_queries.append(query)
            elif is_analytics_query(query):
                analytics_queries.append(query)

        oltp_executions = sum(q.executions for q in oltp_queries)
        analytics_executions = sum(q.executions for q in analytics_queries)
        total_executions = oltp_executions + analytics_executions

        if total_executions == 0:
            continue

        oltp_percentage = (oltp_executions / total_executions) * 100
        analytics_percentage = (analytics_executions / total_executions) * 100

        # Duality View is beneficial when both access patterns are significant
        # Threshold: Both OLTP and Analytics > 10% of workload
        if oltp_percentage > 10 and analytics_percentage > 10:

            # Calculate benefit score
            # Higher benefit when both access patterns are common
            duality_score = min(oltp_percentage, analytics_percentage) / 100

            # Analyze current inefficiencies
            oltp_benefit = calculate_document_access_benefit(table, oltp_queries)
            analytics_benefit = calculate_relational_access_benefit(table, analytics_queries)

            # Calculate Duality View overhead
            refresh_overhead = estimate_duality_view_overhead(table)

            net_benefit = (oltp_benefit + analytics_benefit) - refresh_overhead

            if net_benefit > 0:
                severity = "HIGH" if duality_score > 0.3 else "MEDIUM"

                patterns.append(DetectedPattern(
                    pattern_id=f"DUALITY_OPPORTUNITY_{table.name}",
                    pattern_type="DUALITY_OPPORTUNITY",
                    severity=severity,
                    confidence=duality_score,
                    affected_objects=[table.name],
                    description=f"Table {table.name} has both OLTP ({oltp_percentage:.1f}%) and Analytics ({analytics_percentage:.1f}%) access patterns",
                    metrics={
                        "oltp_query_percentage": oltp_percentage,
                        "analytics_query_percentage": analytics_percentage,
                        "oltp_executions_per_day": oltp_executions,
                        "analytics_executions_per_day": analytics_executions,
                        "oltp_benefit_ms_per_day": oltp_benefit,
                        "analytics_benefit_ms_per_day": analytics_benefit,
                        "refresh_overhead_ms_per_day": refresh_overhead,
                        "net_benefit_ms_per_day": net_benefit,
                    },
                    recommendation_hint=f"Create JSON Duality View for {table.name} to optimize both access patterns"
                ))

    return patterns
```

#### Helper Functions

```python
def is_oltp_query(query: QueryPattern) -> bool:
    """Determine if query is OLTP-style."""
    return (
        query.query_type in ['INSERT', 'UPDATE', 'DELETE'] or
        (query.query_type == 'SELECT' and
         query.join_count <= 1 and
         not has_aggregates(query) and
         query.avg_elapsed_time_ms < 50)  # Fast queries
    )

def is_analytics_query(query: QueryPattern) -> bool:
    """Determine if query is Analytics-style."""
    return (
        query.query_type == 'SELECT' and (
            has_aggregates(query) or
            query.join_count > 2 or
            'GROUP BY' in query.normalized_sql.upper() or
            query.avg_elapsed_time_ms > 100  # Slower analytical queries
        )
    )
```

#### Key Metrics
- **OLTP Query Percentage**: Percentage of workload that is OLTP
- **Analytics Query Percentage**: Percentage of workload that is Analytics
- **OLTP Benefit**: Time saved by providing document access
- **Analytics Benefit**: Time saved by providing relational access
- **Refresh Overhead**: Cost of maintaining Duality View
- **Net Benefit**: Total benefit minus overhead

#### Recommendation Strategies
1. **Create JSON Duality View**: Primary recommendation for dual access patterns
2. **Partial Duality View**: Only include frequently-accessed columns
3. **Read-Only Duality View**: For tables with rare updates
4. **Hybrid Approach**: Duality View for hot data, separate tables for cold data

---

## Module 2: Cost Calculator

### Purpose
Quantify the performance, storage, compute, and maintenance impacts of proposed changes.

### Input Schema
```python
@dataclass
class CostCalculatorInput:
    """Input to cost calculation module."""
    detected_pattern: DetectedPattern
    current_schema: SchemaMetadata
    current_workload: WorkloadFeatures
    proposed_change: ProposedChange  # What we're evaluating
```

### Output Schema
```python
@dataclass
class CostAnalysis:
    """Cost analysis for a proposed change."""
    change_id: str
    performance_impact: PerformanceImpact
    storage_cost: StorageCost
    compute_cost: ComputeCost
    maintenance_burden: MaintenanceBurden
    net_benefit_score: float  # Weighted combination of all factors
    break_even_days: Optional[int]  # Days until benefits exceed costs
```

### Sub-Module 2.1: Performance Impact Calculator

```python
@dataclass
class PerformanceImpact:
    """Performance impact of a proposed change."""
    queries_improved: int
    queries_degraded: int
    time_saved_ms_per_day: float
    time_cost_ms_per_day: float
    net_time_ms_per_day: float
    affected_query_details: List[Dict[str, Any]]

def calculate_performance_impact(
    proposed_change: ProposedChange,
    workload: WorkloadFeatures,
    schema: SchemaMetadata
) -> PerformanceImpact:
    """Calculate performance impact of proposed change.

    Strategy:
    1. Identify affected queries (queries that touch modified objects)
    2. For each affected query:
       a. Estimate current cost (from execution plan or actual metrics)
       b. Estimate new cost with proposed change (hypothetical analysis)
       c. Calculate delta weighted by execution frequency
    3. Sum positive and negative impacts
    4. Return net impact

    Challenge: Hypothetical cost estimation
    - For indexes: Use Oracle's hypothetical index feature
    - For schema changes: Estimate based on cardinality/selectivity
    - For duality views: Benchmark similar patterns
    """

    queries_improved = 0
    queries_degraded = 0
    time_saved = 0.0
    time_cost = 0.0
    details = []

    affected_queries = identify_affected_queries(proposed_change, workload)

    for query in affected_queries:
        # Current cost
        current_cost_ms = query.avg_elapsed_time_ms
        current_daily_cost = current_cost_ms * query.executions

        # Estimated new cost
        new_cost_ms = estimate_new_cost(query, proposed_change, schema)
        new_daily_cost = new_cost_ms * query.executions

        # Delta
        delta_daily = new_daily_cost - current_daily_cost

        if delta_daily < 0:  # Improvement
            queries_improved += 1
            time_saved += abs(delta_daily)
        elif delta_daily > 0:  # Degradation
            queries_degraded += 1
            time_cost += delta_daily

        details.append({
            "query_id": query.query_id,
            "sql_preview": query.sql_text[:100],
            "executions_per_day": query.executions,
            "current_cost_ms": current_cost_ms,
            "estimated_new_cost_ms": new_cost_ms,
            "daily_impact_ms": delta_daily,
            "impact_type": "IMPROVEMENT" if delta_daily < 0 else "DEGRADATION"
        })

    return PerformanceImpact(
        queries_improved=queries_improved,
        queries_degraded=queries_degraded,
        time_saved_ms_per_day=time_saved,
        time_cost_ms_per_day=time_cost,
        net_time_ms_per_day=time_saved - time_cost,
        affected_query_details=details
    )
```

### Sub-Module 2.2: Storage Cost Calculator

```python
@dataclass
class StorageCost:
    """Storage cost of a proposed change."""
    additional_storage_mb: float
    percentage_increase: float
    storage_type: str  # "INDEX", "DENORMALIZATION", "DUALITY_VIEW"
    compressed_size_mb: Optional[float]  # If compression applicable

def calculate_storage_cost(
    proposed_change: ProposedChange,
    schema: SchemaMetadata
) -> StorageCost:
    """Calculate storage overhead of proposed change."""

    if proposed_change.type == "CREATE_INDEX":
        # Index size estimation
        # Simplified: avg_row_length × num_rows × index_columns × 1.2 (B-tree overhead)
        table = schema.get_table(proposed_change.table_name)
        index_columns = proposed_change.index_columns

        avg_row_length = table.avg_row_len
        num_rows = table.num_rows
        column_factor = len(index_columns) / len(table.columns)

        index_size_bytes = avg_row_length * num_rows * column_factor * 1.2
        index_size_mb = index_size_bytes / (1024 * 1024)

        table_size_mb = (avg_row_length * num_rows) / (1024 * 1024)
        percentage_increase = (index_size_mb / table_size_mb) * 100

        return StorageCost(
            additional_storage_mb=index_size_mb,
            percentage_increase=percentage_increase,
            storage_type="INDEX",
            compressed_size_mb=index_size_mb * 0.5 if table.compression else None
        )

    elif proposed_change.type == "DENORMALIZE_COLUMNS":
        # Denormalization: Duplicate data in fact table
        fact_table = schema.get_table(proposed_change.fact_table)
        denorm_columns = proposed_change.denorm_columns

        # Size of denormalized columns
        denorm_data_size = sum(
            get_column_size(col) for col in denorm_columns
        ) * fact_table.num_rows

        denorm_size_mb = denorm_data_size / (1024 * 1024)

        current_table_size_mb = (fact_table.avg_row_len * fact_table.num_rows) / (1024 * 1024)
        percentage_increase = (denorm_size_mb / current_table_size_mb) * 100

        return StorageCost(
            additional_storage_mb=denorm_size_mb,
            percentage_increase=percentage_increase,
            storage_type="DENORMALIZATION",
            compressed_size_mb=None
        )

    elif proposed_change.type == "DUALITY_VIEW":
        # Duality View: Materialized view overhead
        # Depends on refresh strategy (FAST, COMPLETE, NEVER)
        table = schema.get_table(proposed_change.table_name)

        # Duality view stores mapping metadata
        # Estimate: 10-20% overhead for index + metadata
        table_size_mb = (table.avg_row_len * table.num_rows) / (1024 * 1024)
        view_overhead_mb = table_size_mb * 0.15  # 15% overhead

        return StorageCost(
            additional_storage_mb=view_overhead_mb,
            percentage_increase=15.0,
            storage_type="DUALITY_VIEW",
            compressed_size_mb=None
        )

    else:
        return StorageCost(
            additional_storage_mb=0.0,
            percentage_increase=0.0,
            storage_type="UNKNOWN",
            compressed_size_mb=None
        )
```

### Sub-Module 2.3: Compute Cost Calculator

```python
@dataclass
class ComputeCost:
    """Compute cost of a proposed change."""
    cpu_overhead_percentage: float
    memory_overhead_mb: float
    maintenance_operations: List[str]
    estimated_cpu_ms_per_day: float

def calculate_compute_cost(
    proposed_change: ProposedChange,
    workload: WorkloadFeatures,
    schema: SchemaMetadata
) -> ComputeCost:
    """Calculate compute overhead of proposed change."""

    if proposed_change.type == "DUALITY_VIEW":
        # Duality View: Refresh overhead
        table = schema.get_table(proposed_change.table_name)

        # Calculate refresh frequency based on update rate
        update_rate = get_update_rate(table, workload)

        if update_rate > 1000:  # High update rate
            refresh_strategy = "FAST"  # Incremental refresh
            refresh_cpu_ms = update_rate * 2  # 2ms per update to refresh
        elif update_rate > 100:
            refresh_strategy = "COMPLETE"  # Full refresh hourly
            refresh_cpu_ms = (table.num_rows * 0.01) * 24  # Full scan 24 times/day
        else:
            refresh_strategy = "NEVER"  # On-demand refresh
            refresh_cpu_ms = 0

        cpu_overhead_pct = (refresh_cpu_ms / (24 * 3600 * 1000)) * 100  # % of day
        memory_overhead = table.num_rows * table.avg_row_len * 0.1 / (1024 * 1024)  # 10% for view cache

        return ComputeCost(
            cpu_overhead_percentage=cpu_overhead_pct,
            memory_overhead_mb=memory_overhead,
            maintenance_operations=[f"REFRESH_{refresh_strategy}"],
            estimated_cpu_ms_per_day=refresh_cpu_ms
        )

    elif proposed_change.type == "DENORMALIZE_COLUMNS":
        # Denormalization: Update propagation cost
        fact_table = schema.get_table(proposed_change.fact_table)
        dimension_table = schema.get_table(proposed_change.dimension_table)

        # When dimension updates, must propagate to fact table
        dimension_update_rate = get_update_rate(dimension_table, workload)

        # Estimate: Each dimension update requires fact table update
        # Cost: dimension_updates × avg_fact_rows_per_dimension × update_cost
        avg_fact_rows = fact_table.num_rows / dimension_table.num_rows
        update_propagation_cost = dimension_update_rate * avg_fact_rows * 1  # 1ms per row update

        cpu_overhead_pct = (update_propagation_cost / (24 * 3600 * 1000)) * 100

        return ComputeCost(
            cpu_overhead_percentage=cpu_overhead_pct,
            memory_overhead_mb=0.0,  # No additional memory
            maintenance_operations=["UPDATE_PROPAGATION"],
            estimated_cpu_ms_per_day=update_propagation_cost
        )

    else:
        # Indexes, schema changes: negligible compute overhead
        return ComputeCost(
            cpu_overhead_percentage=0.0,
            memory_overhead_mb=0.0,
            maintenance_operations=[],
            estimated_cpu_ms_per_day=0.0
        )
```

### Sub-Module 2.4: Maintenance Burden Scorer

```python
@dataclass
class MaintenanceBurden:
    """Maintenance burden of a proposed change."""
    complexity_score: int  # 1-10 scale
    app_changes_required: bool
    dba_effort_hours: float
    rollback_complexity: str  # "SIMPLE", "MODERATE", "COMPLEX"
    operational_risk: str  # "LOW", "MEDIUM", "HIGH"

def score_maintenance_burden(
    proposed_change: ProposedChange,
    schema: SchemaMetadata
) -> MaintenanceBurden:
    """Score maintenance burden of proposed change."""

    if proposed_change.type == "CREATE_INDEX":
        return MaintenanceBurden(
            complexity_score=2,
            app_changes_required=False,
            dba_effort_hours=0.5,
            rollback_complexity="SIMPLE",  # DROP INDEX
            operational_risk="LOW"
        )

    elif proposed_change.type == "DENORMALIZE_COLUMNS":
        return MaintenanceBurden(
            complexity_score=6,
            app_changes_required=True,  # Must update insert/update logic
            dba_effort_hours=8.0,
            rollback_complexity="MODERATE",  # Must remove columns, update app
            operational_risk="MEDIUM"
        )

    elif proposed_change.type == "DUALITY_VIEW":
        return MaintenanceBurden(
            complexity_score=4,
            app_changes_required=False,  # Transparent to app
            dba_effort_hours=2.0,
            rollback_complexity="SIMPLE",  # DROP VIEW
            operational_risk="LOW"
        )

    elif proposed_change.type == "CONVERT_TO_JSON":
        return MaintenanceBurden(
            complexity_score=9,
            app_changes_required=True,  # Major app refactoring
            dba_effort_hours=40.0,
            rollback_complexity="COMPLEX",  # Data migration required
            operational_risk="HIGH"
        )

    else:
        return MaintenanceBurden(
            complexity_score=5,
            app_changes_required=False,
            dba_effort_hours=4.0,
            rollback_complexity="MODERATE",
            operational_risk="MEDIUM"
        )
```

---

## Module 3: Tradeoff Analyzer

### Purpose
Prioritize recommendations, resolve conflicts, and apply decision thresholds.

### Input Schema
```python
@dataclass
class TradeoffAnalyzerInput:
    """Input to tradeoff analysis."""
    patterns: List[DetectedPattern]
    cost_analyses: Dict[str, CostAnalysis]  # Keyed by pattern_id
    workload: WorkloadFeatures
    constraints: OptimizationConstraints
```

### Output Schema
```python
@dataclass
class PrioritizedRecommendation:
    """A prioritized recommendation with tradeoff analysis."""
    pattern: DetectedPattern
    cost_analysis: CostAnalysis
    priority_score: float  # 0.0-100.0
    conflicts_with: List[str]  # Pattern IDs
    tradeoffs: List[Tradeoff]
    accept_decision: bool
    decision_rationale: str
```

### Sub-Module 3.1: Query Frequency Weighter

```python
def weight_by_query_frequency(
    patterns: List[DetectedPattern],
    cost_analyses: Dict[str, CostAnalysis],
    workload: WorkloadFeatures
) -> List[PrioritizedRecommendation]:
    """Weight recommendations by affected query frequency.

    Strategy: High-frequency queries get higher priority.
    Formula: priority_score = base_score × frequency_multiplier

    Frequency Multiplier:
    - Top 10% queries (p90+): 10x weight
    - Top 30% queries (p70-p90): 5x weight
    - Top 50% queries (p50-p70): 2x weight
    - Bottom 50% queries: 1x weight
    """

    # Calculate query frequency percentiles
    all_queries = workload.queries
    query_frequencies = [q.executions for q in all_queries]
    p50 = np.percentile(query_frequencies, 50)
    p70 = np.percentile(query_frequencies, 70)
    p90 = np.percentile(query_frequencies, 90)

    recommendations = []

    for pattern in patterns:
        cost_analysis = cost_analyses[pattern.pattern_id]

        # Identify affected queries
        affected_queries = [
            q for q in all_queries
            if any(obj in q.tables for obj in pattern.affected_objects)
        ]

        # Calculate frequency multiplier
        total_frequency = sum(q.executions for q in affected_queries)

        if total_frequency >= p90:
            frequency_multiplier = 10.0
        elif total_frequency >= p70:
            frequency_multiplier = 5.0
        elif total_frequency >= p50:
            frequency_multiplier = 2.0
        else:
            frequency_multiplier = 1.0

        # Base score from net benefit
        base_score = cost_analysis.net_benefit_score

        # Final priority
        priority_score = base_score * frequency_multiplier

        recommendations.append(PrioritizedRecommendation(
            pattern=pattern,
            cost_analysis=cost_analysis,
            priority_score=priority_score,
            conflicts_with=[],  # To be filled by conflict detector
            tradeoffs=[],  # To be filled later
            accept_decision=True,  # Provisional, may change
            decision_rationale=f"Base benefit {base_score:.1f} × frequency multiplier {frequency_multiplier:.1f}"
        ))

    # Sort by priority score
    recommendations.sort(key=lambda r: r.priority_score, reverse=True)

    return recommendations
```

### Sub-Module 3.2: Conflict Detector & Resolver

```python
@dataclass
class Conflict:
    """A conflict between two recommendations."""
    pattern_a: str
    pattern_b: str
    conflict_type: str  # "MUTUALLY_EXCLUSIVE", "REDUNDANT", "CASCADING"
    resolution: str  # Which pattern to prefer

def detect_and_resolve_conflicts(
    recommendations: List[PrioritizedRecommendation]
) -> List[PrioritizedRecommendation]:
    """Detect and resolve conflicts between recommendations."""

    conflicts = []

    # Check all pairs for conflicts
    for i, rec_a in enumerate(recommendations):
        for j, rec_b in enumerate(recommendations[i+1:], start=i+1):

            # Conflict Type 1: Mutually Exclusive
            # Example: Can't denormalize and normalize the same table
            if is_mutually_exclusive(rec_a.pattern, rec_b.pattern):
                conflict = Conflict(
                    pattern_a=rec_a.pattern.pattern_id,
                    pattern_b=rec_b.pattern.pattern_id,
                    conflict_type="MUTUALLY_EXCLUSIVE",
                    resolution=rec_a.pattern.pattern_id if rec_a.priority_score > rec_b.priority_score else rec_b.pattern.pattern_id
                )
                conflicts.append(conflict)

                # Mark conflict
                rec_a.conflicts_with.append(rec_b.pattern.pattern_id)
                rec_b.conflicts_with.append(rec_a.pattern.pattern_id)

            # Conflict Type 2: Redundant
            # Example: Two different denormalization strategies for same join
            elif is_redundant(rec_a.pattern, rec_b.pattern):
                conflict = Conflict(
                    pattern_a=rec_a.pattern.pattern_id,
                    pattern_b=rec_b.pattern.pattern_id,
                    conflict_type="REDUNDANT",
                    resolution=rec_a.pattern.pattern_id if rec_a.priority_score > rec_b.priority_score else rec_b.pattern.pattern_id
                )
                conflicts.append(conflict)

            # Conflict Type 3: Cascading
            # Example: Denormalizing might eliminate need for index
            elif has_cascading_effect(rec_a.pattern, rec_b.pattern):
                # Keep both, but note dependency
                rec_a.tradeoffs.append(Tradeoff(
                    description=f"If {rec_a.pattern.pattern_type} is applied, {rec_b.pattern.pattern_type} may become unnecessary",
                    impact="May reduce benefit of other recommendation"
                ))

    # Resolve conflicts
    for conflict in conflicts:
        if conflict.conflict_type in ["MUTUALLY_EXCLUSIVE", "REDUNDANT"]:
            # Reject the lower-priority pattern
            rejected_id = conflict.pattern_b if conflict.resolution == conflict.pattern_a else conflict.pattern_a

            for rec in recommendations:
                if rec.pattern.pattern_id == rejected_id:
                    rec.accept_decision = False
                    rec.decision_rationale += f" | REJECTED: Conflicts with {conflict.resolution}"

    return recommendations
```

### Sub-Module 3.3: Threshold Checker

```python
@dataclass
class OptimizationConstraints:
    """Constraints for optimization decisions."""
    min_net_benefit_ms_per_day: float = 1000.0  # Minimum 1 second/day saved
    max_storage_overhead_percentage: float = 20.0
    max_compute_overhead_percentage: float = 5.0
    max_maintenance_complexity: int = 7  # 1-10 scale
    acceptable_query_degradation_percentage: float = 5.0  # Max 5% queries can degrade

def apply_threshold_checks(
    recommendations: List[PrioritizedRecommendation],
    constraints: OptimizationConstraints
) -> List[PrioritizedRecommendation]:
    """Apply threshold checks to filter recommendations."""

    for rec in recommendations:
        if not rec.accept_decision:  # Already rejected
            continue

        cost = rec.cost_analysis
        pattern = rec.pattern

        # Threshold 1: Minimum net benefit
        if cost.performance_impact.net_time_ms_per_day < constraints.min_net_benefit_ms_per_day:
            rec.accept_decision = False
            rec.decision_rationale += f" | REJECTED: Net benefit {cost.performance_impact.net_time_ms_per_day:.0f}ms/day below threshold {constraints.min_net_benefit_ms_per_day:.0f}ms/day"
            continue

        # Threshold 2: Storage overhead
        if cost.storage_cost.percentage_increase > constraints.max_storage_overhead_percentage:
            rec.accept_decision = False
            rec.decision_rationale += f" | REJECTED: Storage overhead {cost.storage_cost.percentage_increase:.1f}% exceeds threshold {constraints.max_storage_overhead_percentage:.1f}%"
            continue

        # Threshold 3: Compute overhead
        if cost.compute_cost.cpu_overhead_percentage > constraints.max_compute_overhead_percentage:
            rec.accept_decision = False
            rec.decision_rationale += f" | REJECTED: CPU overhead {cost.compute_cost.cpu_overhead_percentage:.1f}% exceeds threshold {constraints.max_compute_overhead_percentage:.1f}%"
            continue

        # Threshold 4: Maintenance complexity
        if cost.maintenance_burden.complexity_score > constraints.max_maintenance_complexity:
            rec.accept_decision = False
            rec.decision_rationale += f" | REJECTED: Maintenance complexity {cost.maintenance_burden.complexity_score} exceeds threshold {constraints.max_maintenance_complexity}"
            continue

        # Threshold 5: Query degradation
        total_affected = cost.performance_impact.queries_improved + cost.performance_impact.queries_degraded
        if total_affected > 0:
            degradation_pct = (cost.performance_impact.queries_degraded / total_affected) * 100

            if degradation_pct > constraints.acceptable_query_degradation_percentage:
                rec.accept_decision = False
                rec.decision_rationale += f" | REJECTED: {degradation_pct:.1f}% queries degrade, exceeds threshold {constraints.acceptable_query_degradation_percentage:.1f}%"
                continue

        # Threshold 6: Break-even analysis
        if cost.break_even_days and cost.break_even_days > 90:  # More than 3 months to break even
            rec.tradeoffs.append(Tradeoff(
                description=f"Long break-even period: {cost.break_even_days} days",
                impact="Benefits may take time to realize"
            ))

    return recommendations
```

### Sub-Module 3.4: Diminishing Returns Detector

```python
def detect_diminishing_returns(
    recommendations: List[PrioritizedRecommendation]
) -> List[PrioritizedRecommendation]:
    """Detect diminishing returns in recommendation list.

    Strategy: Apply recommendations in priority order, stop when
    marginal benefit drops below 5% of first recommendation.
    """

    if not recommendations:
        return recommendations

    # Filter accepted recommendations
    accepted_recs = [r for r in recommendations if r.accept_decision]

    if not accepted_recs:
        return recommendations

    # Sort by priority
    accepted_recs.sort(key=lambda r: r.priority_score, reverse=True)

    # First recommendation benefit is baseline
    first_benefit = accepted_recs[0].cost_analysis.performance_impact.net_time_ms_per_day

    if first_benefit <= 0:
        return recommendations

    # Check marginal benefit
    for i, rec in enumerate(accepted_recs):
        if i == 0:  # Always accept first
            continue

        marginal_benefit = rec.cost_analysis.performance_impact.net_time_ms_per_day
        marginal_percentage = (marginal_benefit / first_benefit) * 100

        if marginal_percentage < 5.0:  # Less than 5% of first recommendation
            rec.tradeoffs.append(Tradeoff(
                description=f"Marginal benefit {marginal_percentage:.1f}% of top recommendation",
                impact="Low incremental value"
            ))

            # Mark as low priority but don't reject
            rec.priority_score *= 0.5

    return recommendations
```

---

## Module 4: Recommendation Engine

### Purpose
Orchestrate all modules, generate comprehensive LLM prompts, and format final recommendations.

### Main Orchestration Flow

```python
class RecommendationEngine:
    """Main orchestrator for schema policy recommendations."""

    def __init__(
        self,
        pattern_detector: PatternDetector,
        cost_calculator: CostCalculator,
        tradeoff_analyzer: TradeoffAnalyzer,
        llm_client: ClaudeClient
    ):
        self.pattern_detector = pattern_detector
        self.cost_calculator = cost_calculator
        self.tradeoff_analyzer = tradeoff_analyzer
        self.llm_client = llm_client

    def generate_recommendations(
        self,
        workload_data: Dict[str, Any],
        schema_data: Dict[str, Any],
        constraints: OptimizationConstraints = OptimizationConstraints()
    ) -> RecommendationResult:
        """Generate schema policy recommendations.

        Complete pipeline:
        1. Detect patterns
        2. Calculate costs
        3. Analyze tradeoffs
        4. Generate LLM prompt
        5. Synthesize with Claude
        6. Format output
        """

        # Step 1: Pattern Detection
        logger.info("Step 1: Detecting schema patterns...")
        patterns = self.pattern_detector.detect_all_patterns(
            workload_data, schema_data
        )
        logger.info(f"Detected {len(patterns)} patterns")

        # Step 2: Cost Calculation
        logger.info("Step 2: Calculating costs...")
        cost_analyses = {}
        for pattern in patterns:
            cost_analyses[pattern.pattern_id] = self.cost_calculator.calculate_costs(
                pattern, schema_data, workload_data
            )
        logger.info(f"Calculated costs for {len(cost_analyses)} patterns")

        # Step 3: Tradeoff Analysis
        logger.info("Step 3: Analyzing tradeoffs...")
        prioritized_recs = self.tradeoff_analyzer.analyze(
            patterns, cost_analyses, workload_data, constraints
        )
        logger.info(f"Prioritized {len([r for r in prioritized_recs if r.accept_decision])} accepted recommendations")

        # Step 4: Generate LLM Prompt
        logger.info("Step 4: Generating LLM prompt...")
        llm_prompt = self._generate_comprehensive_prompt(
            patterns, cost_analyses, prioritized_recs, workload_data, schema_data
        )

        # Step 5: LLM Synthesis
        logger.info("Step 5: Requesting Claude analysis...")
        llm_response = self.llm_client.send_message(
            message=llm_prompt,
            system=SCHEMA_POLICY_SYSTEM_PROMPT,
            max_tokens=8000,
            temperature=0.3  # Lower temperature for more focused analysis
        )

        # Step 6: Format Final Recommendations
        logger.info("Step 6: Formatting recommendations...")
        final_recommendations = self._format_recommendations(
            prioritized_recs, llm_response["text"]
        )

        return RecommendationResult(
            recommendations=final_recommendations,
            summary=self._generate_summary(final_recommendations),
            llm_analysis=llm_response["text"],
            patterns_detected=len(patterns),
            recommendations_accepted=len([r for r in final_recommendations if r.accepted]),
            total_estimated_benefit_ms_per_day=sum(
                r.cost_analysis.performance_impact.net_time_ms_per_day
                for r in final_recommendations if r.accepted
            )
        )

    def _generate_comprehensive_prompt(
        self,
        patterns: List[DetectedPattern],
        cost_analyses: Dict[str, CostAnalysis],
        prioritized_recs: List[PrioritizedRecommendation],
        workload: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> str:
        """Generate comprehensive prompt for Claude."""

        prompt = f"""# Oracle 23ai Schema Policy Analysis Request

## Context
You are analyzing an Oracle 23ai database to provide sophisticated schema optimization recommendations. Your goal is to identify opportunities for performance improvement while carefully considering tradeoffs.

## Workload Summary
{json.dumps(workload.get('summary', {}), indent=2)}

## Schema Overview
- Total Tables: {len(schema.get('tables', []))}
- Total Indexes: {len(schema.get('indexes', []))}
- Total Constraints: {len(schema.get('constraints', []))}

## Detected Patterns ({len(patterns)} total)
"""

        # Add each pattern with metrics
        for pattern in patterns[:10]:  # Top 10 patterns
            cost = cost_analyses[pattern.pattern_id]
            prompt += f"""
### {pattern.pattern_type}: {pattern.description}
- **Severity**: {pattern.severity}
- **Confidence**: {pattern.confidence:.2%}
- **Affected Objects**: {', '.join(pattern.affected_objects)}
- **Performance Impact**: {cost.performance_impact.net_time_ms_per_day:.0f}ms/day net benefit
- **Storage Cost**: +{cost.storage_cost.additional_storage_mb:.1f}MB ({cost.storage_cost.percentage_increase:.1f}% increase)
- **Compute Overhead**: {cost.compute_cost.cpu_overhead_percentage:.2f}% CPU
- **Maintenance Burden**: {cost.maintenance_burden.complexity_score}/10
"""

        prompt += f"""

## Prioritized Recommendations ({len([r for r in prioritized_recs if r.accept_decision])} accepted)
"""

        for rec in prioritized_recs:
            if rec.accept_decision:
                prompt += f"""
### Priority {rec.priority_score:.1f}: {rec.pattern.pattern_type}
- **Action**: {rec.pattern.recommendation_hint}
- **Net Benefit**: {rec.cost_analysis.performance_impact.net_time_ms_per_day:.0f}ms/day
- **Queries Improved**: {rec.cost_analysis.performance_impact.queries_improved}
- **Queries Degraded**: {rec.cost_analysis.performance_impact.queries_degraded}
- **Tradeoffs**: {', '.join([t.description for t in rec.tradeoffs]) if rec.tradeoffs else 'None'}
"""

        prompt += """

## Analysis Request

Please provide:

1. **Synthesis**: How do these patterns relate? Are there overarching themes?

2. **Prioritization Validation**: Do you agree with the priority ranking? Would you adjust based on:
   - Business impact vs technical complexity
   - Risk assessment
   - Dependencies between changes

3. **Creative Solutions**: Are there alternative approaches we haven't considered?
   - Could JSON Duality Views solve multiple problems at once?
   - Are there partial solutions with lower risk?
   - Could incremental changes be safer than big-bang migrations?

4. **Implementation Strategy**: For the top 3 recommendations:
   - Step-by-step implementation approach
   - Testing strategy
   - Rollback plan
   - Monitoring metrics to track success

5. **Long-term Considerations**:
   - How will these changes affect future scalability?
   - Are we creating new technical debt?
   - What happens as workload evolves?

Please be specific, quantitative where possible, and highlight any concerns or risks.
"""

        return prompt

    def _format_recommendations(
        self,
        prioritized_recs: List[PrioritizedRecommendation],
        llm_analysis: str
    ) -> List[FinalRecommendation]:
        """Format recommendations with LLM insights."""

        final_recs = []

        for rec in prioritized_recs:
            if not rec.accept_decision:
                continue

            final_rec = FinalRecommendation(
                recommendation_id=f"REC-{rec.pattern.pattern_id}",
                title=f"{rec.pattern.pattern_type}: {rec.pattern.recommendation_hint}",
                priority=self._map_priority(rec.priority_score),
                pattern=rec.pattern,
                cost_analysis=rec.cost_analysis,

                implementation=Implementation(
                    sql=self._generate_implementation_sql(rec),
                    steps=self._generate_implementation_steps(rec),
                    estimated_duration="TBD",  # Extract from LLM
                    prerequisites=[],
                ),

                rollback=RollbackPlan(
                    sql=self._generate_rollback_sql(rec),
                    steps=self._generate_rollback_steps(rec),
                    data_loss_risk=rec.cost_analysis.maintenance_burden.operational_risk,
                ),

                testing=TestingApproach(
                    strategy="Shadow mode → 10% traffic → full rollout",
                    metrics_to_monitor=[
                        "Query execution time",
                        "Storage growth",
                        "CPU utilization",
                    ],
                    success_criteria=[
                        f"Query time reduced by >{rec.cost_analysis.performance_impact.net_time_ms_per_day / 1000:.1f}s/day",
                        f"No degradation on high-frequency queries",
                    ],
                ),

                tradeoffs=[
                    TradeoffExplanation(
                        aspect=t.description,
                        impact=t.impact,
                        mitigation="TBD"  # Extract from LLM
                    ) for t in rec.tradeoffs
                ],

                llm_insights=self._extract_recommendation_insights(rec, llm_analysis),

                accepted=True
            )

            final_recs.append(final_rec)

        return final_recs
```

---

## Data Flow & Integration

### Complete Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. INPUT COLLECTION                                              │
├─────────────────────────────────────────────────────────────────┤
│ - Workload Data (FeatureEngineer)                               │
│ - Schema Metadata (SchemaCollector)                             │
│ - Optimization Constraints (User)                               │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. PATTERN DETECTION (Parallel Execution)                       │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐  ┌────────────────────────┐            │
│ │ LOB Cliff Detector  │  │ Join Analyzer          │            │
│ └─────────────────────┘  └────────────────────────┘            │
│ ┌─────────────────────┐  ┌────────────────────────┐            │
│ │ Doc/Rel Classifier  │  │ Duality Finder         │            │
│ └─────────────────────┘  └────────────────────────┘            │
│                                                                  │
│ OUTPUT: List[DetectedPattern]                                   │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. COST CALCULATION (For Each Pattern)                          │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐  ┌────────────────────────┐            │
│ │ Performance Impact  │  │ Storage Cost           │            │
│ └─────────────────────┘  └────────────────────────┘            │
│ ┌─────────────────────┐  ┌────────────────────────┐            │
│ │ Compute Cost        │  │ Maintenance Burden     │            │
│ └─────────────────────┘  └────────────────────────┘            │
│                                                                  │
│ OUTPUT: Dict[pattern_id, CostAnalysis]                          │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. TRADEOFF ANALYSIS (Sequential Pipeline)                      │
├─────────────────────────────────────────────────────────────────┤
│ Step 1: Frequency Weighting                                     │
│    → Priority Scores                                             │
│                                                                  │
│ Step 2: Conflict Detection & Resolution                         │
│    → Non-Conflicting Set                                        │
│                                                                  │
│ Step 3: Threshold Checking                                      │
│    → Accept/Reject Decisions                                    │
│                                                                  │
│ Step 4: Diminishing Returns                                     │
│    → Final Priority Adjustment                                  │
│                                                                  │
│ OUTPUT: List[PrioritizedRecommendation]                         │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. LLM SYNTHESIS (Claude Analysis)                              │
├─────────────────────────────────────────────────────────────────┤
│ Generate Comprehensive Prompt:                                  │
│ - All detected patterns with metrics                            │
│ - Cost/benefit analysis                                         │
│ - Prioritization and tradeoffs                                  │
│ - Request synthesis and creative solutions                      │
│                                                                  │
│ Claude Reasoning:                                                │
│ - Validate prioritization                                       │
│ - Identify synergies                                            │
│ - Suggest alternative approaches                                │
│ - Provide implementation guidance                               │
│                                                                  │
│ OUTPUT: LLM Analysis Text                                        │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. RECOMMENDATION FORMATTING                                     │
├─────────────────────────────────────────────────────────────────┤
│ For Each Accepted Recommendation:                               │
│ - Generate implementation SQL                                    │
│ - Create rollback plan                                          │
│ - Define testing approach                                       │
│ - Extract LLM insights                                          │
│ - Format structured output                                      │
│                                                                  │
│ OUTPUT: List[FinalRecommendation]                               │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. RESULT DELIVERY                                               │
├─────────────────────────────────────────────────────────────────┤
│ RecommendationResult:                                            │
│ - Final recommendations (structured)                             │
│ - Executive summary                                              │
│ - Full LLM analysis                                             │
│ - Metrics (patterns, accepted, total benefit)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

### Phase 1: Pattern Detector (Week 1-2)
1. Implement base `PatternDetector` class
2. Implement `LOBCliffDetector` (TDD)
3. Implement `JoinDimensionAnalyzer` (TDD)
4. Implement `DocumentRelationalClassifier` (TDD)
5. Implement `DualityOpportunityFinder` (TDD)
6. Integration tests with sample workloads

### Phase 2: Cost Calculator (Week 2-3)
1. Implement base `CostCalculator` class
2. Implement `PerformanceImpactCalculator` (TDD)
3. Implement `StorageCostCalculator` (TDD)
4. Implement `ComputeCostCalculator` (TDD)
5. Implement `MaintenanceBurdenScorer` (TDD)
6. Integration tests with cost estimation validation

### Phase 3: Tradeoff Analyzer (Week 3-4)
1. Implement base `TradeoffAnalyzer` class
2. Implement `QueryFrequencyWeighter` (TDD)
3. Implement `ConflictDetectorResolver` (TDD)
4. Implement `ThresholdChecker` (TDD)
5. Implement `DiminishingReturnsDetector` (TDD)
6. Integration tests with complex scenarios

### Phase 4: Recommendation Engine (Week 4-5)
1. Implement `RecommendationEngine` orchestrator
2. Implement LLM prompt generation
3. Implement response parsing and formatting
4. Implement SQL generation for recommendations
5. End-to-end integration tests
6. Real workload validation

### Phase 5: Testing & Refinement (Week 5-6)
1. Comprehensive integration testing
2. Performance benchmarking
3. Edge case handling
4. Documentation and examples
5. User acceptance testing

---

## Success Criteria

1. **Pattern Detection Accuracy**: >90% precision on known anti-patterns
2. **Cost Estimation**: Within 20% of actual measured impact
3. **Recommendation Quality**: >85% of recommendations accepted by DBAs
4. **Performance**: Complete analysis in <5 minutes for workloads with 10K queries
5. **Test Coverage**: >90% for all modules

---

*End of Design Document*
