"""Pattern detection module for schema anti-patterns and optimization opportunities.

This module implements detectors for various database schema anti-patterns including
LOB cliffs, expensive joins, document vs relational mismatches, and duality view opportunities.
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List

from src.recommendation.models import (
    ColumnMetadata,
    DetectedPattern,
    QueryPattern,
    SchemaMetadata,
    TableMetadata,
    WorkloadFeatures,
)

logger = logging.getLogger(__name__)


class LOBCliffDetector:
    """Detector for LOB cliff anti-patterns.

    LOB cliff occurs when small updates to large LOB/JSON columns cause
    performance issues due to out-of-line storage fragmentation.

    Oracle 23ai context:
    - OSON binary format is efficient for updates
    - Text JSON in CLOB is inefficient
    - In-row storage limit is typically 4KB

    Attributes:
        large_doc_threshold_bytes: Size threshold for out-of-line storage (default: 4096)
        high_update_frequency_threshold: Updates per day threshold (default: 100)
        small_update_selectivity_threshold: Selectivity threshold for small updates (default: 0.1)
    """

    def __init__(
        self,
        large_doc_threshold_bytes: int = 4096,
        high_update_frequency_threshold: int = 100,
        small_update_selectivity_threshold: float = 0.1,
    ):
        """Initialize LOBCliffDetector with configurable thresholds.

        Args:
            large_doc_threshold_bytes: Size threshold for out-of-line storage
            high_update_frequency_threshold: Minimum updates per day to trigger detection
            small_update_selectivity_threshold: Maximum selectivity for small updates
        """
        self.large_doc_threshold_bytes = large_doc_threshold_bytes
        self.high_update_frequency_threshold = high_update_frequency_threshold
        self.small_update_selectivity_threshold = small_update_selectivity_threshold

        logger.info(
            f"LOBCliffDetector initialized with thresholds: "
            f"doc_size={large_doc_threshold_bytes}B, "
            f"update_freq={high_update_frequency_threshold}/day, "
            f"selectivity={small_update_selectivity_threshold}"
        )

    def detect(
        self, tables: List[TableMetadata], workload: WorkloadFeatures
    ) -> List[DetectedPattern]:
        """Detect LOB cliff anti-patterns in given tables and workload.

        Args:
            tables: List of table metadata to analyze
            workload: Workload features including query patterns

        Returns:
            List of detected LOB cliff patterns
        """
        patterns = []

        for table in tables:
            # Step 1: Identify LOB/JSON columns
            lob_columns = self._identify_lob_columns(table)

            if not lob_columns:
                continue

            # Step 2: Analyze update patterns for this table
            update_queries = self._get_update_queries(table, workload)

            if not update_queries:
                continue

            # Step 3: Analyze each LOB column
            for col in lob_columns:
                pattern = self._analyze_lob_column(table, col, update_queries)
                if pattern:
                    patterns.append(pattern)

        logger.info(f"Detected {len(patterns)} LOB cliff patterns")
        return patterns

    def _identify_lob_columns(self, table: TableMetadata) -> List[ColumnMetadata]:
        """Identify LOB/JSON columns in a table.

        Args:
            table: Table metadata to analyze

        Returns:
            List of columns with LOB/JSON data types
        """
        return [col for col in table.columns if col.data_type in ["CLOB", "BLOB", "JSON"]]

    def _get_update_queries(
        self, table: TableMetadata, workload: WorkloadFeatures
    ) -> List[QueryPattern]:
        """Get update queries affecting a specific table.

        Args:
            table: Table to find updates for
            workload: Workload containing query patterns

        Returns:
            List of UPDATE queries that affect this table
        """
        return [q for q in workload.queries if q.query_type == "UPDATE" and table.name in q.tables]

    def _analyze_lob_column(
        self, table: TableMetadata, col: ColumnMetadata, update_queries: List[QueryPattern]
    ) -> DetectedPattern | None:
        """Analyze a specific LOB column for cliff pattern.

        Args:
            table: Table containing the column
            col: LOB column to analyze
            update_queries: Update queries affecting this table

        Returns:
            DetectedPattern if LOB cliff detected, None otherwise
        """
        # Calculate metrics
        avg_doc_size = col.avg_size if col.avg_size else table.avg_row_len
        update_frequency = sum(q.executions for q in update_queries)
        update_selectivity = self._calculate_update_selectivity(update_queries, col)

        # Calculate risk score based on multiple factors
        risk_score = 0.0

        # Factor 1: Large documents (out-of-line storage)
        if avg_doc_size > self.large_doc_threshold_bytes:
            risk_score += 0.3

        # Factor 2: High update frequency
        if update_frequency > self.high_update_frequency_threshold:
            risk_score += 0.3

        # Factor 3: Small updates (low selectivity)
        if update_selectivity < self.small_update_selectivity_threshold:
            risk_score += 0.2

        # Factor 4: Text JSON in CLOB (inefficient format)
        if col.data_type == "CLOB":
            risk_score += 0.2

        # Only create pattern if risk exceeds threshold
        if risk_score < 0.6:
            return None

        # Determine severity based on risk score
        if risk_score >= 0.8:
            severity = "HIGH"
        else:
            severity = "MEDIUM"

        # Determine storage type
        storage_type = "out_of_line" if avg_doc_size > self.large_doc_threshold_bytes else "in_row"

        # Determine format
        format_type = "OSON" if col.data_type == "JSON" else "TEXT"

        # Create pattern
        pattern_id = f"LOB_CLIFF_{table.name}_{col.name}"
        affected_object = f"{table.name}.{col.name}"

        description = (
            f"Frequent small updates to large {col.data_type} column causing LOB fragmentation"
        )

        recommendation_hint = "Consider splitting document or using separate metadata table"

        pattern = DetectedPattern(
            pattern_id=pattern_id,
            pattern_type="LOB_CLIFF",
            severity=severity,
            confidence=risk_score,
            affected_objects=[affected_object],
            description=description,
            metrics={
                "avg_document_size_kb": avg_doc_size / 1024,
                "updates_per_day": update_frequency,
                "update_selectivity": update_selectivity,
                "storage_type": storage_type,
                "format": format_type,
            },
            recommendation_hint=recommendation_hint,
        )

        logger.debug(
            f"Detected LOB cliff pattern: {pattern_id} "
            f"(risk={risk_score:.2f}, severity={severity})"
        )

        return pattern

    def _calculate_update_selectivity(
        self, update_queries: List[QueryPattern], col: ColumnMetadata
    ) -> float:
        """Calculate update selectivity for a column.

        Update selectivity represents the proportion of the document/column
        that is typically modified in an update. Lower selectivity indicates
        small updates relative to total size.

        For simplicity in this implementation, we estimate based on average
        query characteristics. In production, this would use actual AWR data
        showing bytes modified vs total column size.

        Args:
            update_queries: List of update queries
            col: Column being analyzed

        Returns:
            Estimated selectivity (0.0-1.0)
        """
        if not update_queries:
            return 1.0  # Full document updates

        # Simplified heuristic: queries with high execution frequency
        # and short elapsed time likely do small updates
        total_weight = 0.0
        selectivity_sum = 0.0

        for query in update_queries:
            weight = query.executions
            total_weight += weight

            # Heuristic: faster queries likely update smaller portions
            # Base selectivity of 0.03 for very fast queries (< 5ms)
            # Up to 0.5 for slower queries (> 50ms)
            if query.avg_elapsed_time_ms < 5:
                estimated_selectivity = 0.03
            elif query.avg_elapsed_time_ms < 20:
                estimated_selectivity = 0.08
            elif query.avg_elapsed_time_ms < 50:
                estimated_selectivity = 0.15
            else:
                estimated_selectivity = 0.5

            selectivity_sum += estimated_selectivity * weight

        if total_weight == 0:
            return 0.5  # Default middle value

        weighted_selectivity = selectivity_sum / total_weight
        return weighted_selectivity


class JoinDimensionAnalyzer:
    """Analyzer for expensive join patterns that could benefit from denormalization.

    Join Dimension: A table frequently joined to access a small set of columns.
    Common pattern: orders JOIN customers to get customer_name, customer_tier

    Denormalization candidate when:
    1. Join appears in >10% of queries
    2. Only 1-5 columns fetched from dimension table
    3. Dimension table is relatively small (< 1M rows) or stable
    4. Join cost > maintenance cost of denormalization

    Attributes:
        min_join_frequency_percentage: Minimum percentage of queries with this join (default: 10.0)
        max_columns_fetched: Maximum columns to consider for denormalization (default: 5)
        max_dimension_rows: Maximum dimension table size (default: 1000000)
        max_dimension_update_rate: Maximum updates per day to dimension (default: 100)
    """

    def __init__(
        self,
        min_join_frequency_percentage: float = 10.0,
        max_columns_fetched: int = 5,
        max_dimension_rows: int = 1000000,
        max_dimension_update_rate: int = 100,
    ):
        """Initialize JoinDimensionAnalyzer with configurable thresholds.

        Args:
            min_join_frequency_percentage: Minimum join frequency to trigger detection
            max_columns_fetched: Maximum columns to consider
            max_dimension_rows: Maximum dimension table size
            max_dimension_update_rate: Maximum updates per day to dimension
        """
        self.min_join_frequency_percentage = min_join_frequency_percentage
        self.max_columns_fetched = max_columns_fetched
        self.max_dimension_rows = max_dimension_rows
        self.max_dimension_update_rate = max_dimension_update_rate

        logger.info(
            f"JoinDimensionAnalyzer initialized with thresholds: "
            f"min_freq={min_join_frequency_percentage}%, "
            f"max_cols={max_columns_fetched}, "
            f"max_rows={max_dimension_rows}, "
            f"max_updates={max_dimension_update_rate}/day"
        )

    def analyze(self, workload: WorkloadFeatures, schema: SchemaMetadata) -> List[DetectedPattern]:
        """Analyze join patterns for denormalization opportunities.

        Args:
            workload: Workload features including query patterns
            schema: Schema metadata for dimension table lookups

        Returns:
            List of detected expensive join patterns
        """
        patterns = []

        # Step 1: Build join frequency matrix
        join_patterns = self._build_join_frequency_matrix(workload)

        # Step 2: Analyze each frequent join
        total_queries = workload.total_executions

        for join_key, metrics in join_patterns.items():
            # Parse join key
            left_table, right_table = join_key.split("__")

            # Calculate join frequency percentage
            join_frequency_pct = (metrics["count"] / total_queries) * 100

            if join_frequency_pct < self.min_join_frequency_percentage:
                continue  # Low frequency, skip

            # Check column access pattern
            columns_accessed = metrics["columns_accessed"]
            if len(columns_accessed) > self.max_columns_fetched:
                continue  # Too many columns

            # Get dimension table metadata
            dimension_table = schema.get_table(right_table)
            if not dimension_table:
                logger.warning(f"Dimension table {right_table} not found in schema")
                continue

            # Check dimension size and update rate
            if not self._is_suitable_dimension(dimension_table, workload):
                continue

            # Step 3: Calculate denormalization benefit
            pattern = self._create_join_pattern(
                left_table,
                right_table,
                dimension_table,
                metrics,
                join_frequency_pct,
                total_queries,
            )

            if pattern:
                patterns.append(pattern)

        logger.info(f"Detected {len(patterns)} expensive join patterns")
        return patterns

    def _build_join_frequency_matrix(self, workload: WorkloadFeatures) -> Dict[str, Dict[str, Any]]:
        """Build join frequency matrix from workload.

        Args:
            workload: Workload features

        Returns:
            Dictionary mapping join keys to metrics
        """
        join_patterns: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "total_cost": 0.0,
                "columns_accessed": set(),
                "query_ids": [],
            }
        )

        for query in workload.queries:
            if query.join_count > 0 and query.joins:
                for join in query.joins:
                    join_key = f"{join.left_table}__{join.right_table}"
                    join_patterns[join_key]["count"] += query.executions
                    join_patterns[join_key]["total_cost"] += (
                        query.avg_elapsed_time_ms * query.executions
                    )
                    join_patterns[join_key]["columns_accessed"].update(join.columns_fetched)
                    join_patterns[join_key]["query_ids"].append(query.query_id)

        return dict(join_patterns)

    def _is_suitable_dimension(
        self, dimension_table: TableMetadata, workload: WorkloadFeatures
    ) -> bool:
        """Check if dimension table is suitable for denormalization.

        Args:
            dimension_table: Dimension table metadata
            workload: Workload features

        Returns:
            True if suitable, False otherwise
        """
        # Check size constraint
        if dimension_table.num_rows > self.max_dimension_rows:
            # Large dimension - check if it's stable (rarely updated)
            update_rate = self._get_update_rate(dimension_table, workload)
            if update_rate > self.max_dimension_update_rate:
                return False  # Too large and frequently updated

        return True

    def _get_update_rate(self, table: TableMetadata, workload: WorkloadFeatures) -> int:
        """Get update rate for a table from workload.

        Args:
            table: Table metadata
            workload: Workload features

        Returns:
            Number of updates per day
        """
        update_count = 0
        for query in workload.queries:
            if query.query_type == "UPDATE" and table.name in query.tables:
                update_count += query.executions

        return update_count

    def _create_join_pattern(
        self,
        left_table: str,
        right_table: str,
        dimension_table: TableMetadata,
        metrics: Dict[str, Any],
        join_frequency_pct: float,
        total_queries: int,
    ) -> DetectedPattern | None:
        """Create join pattern from analyzed metrics.

        Args:
            left_table: Left table in join
            right_table: Right table (dimension) in join
            dimension_table: Dimension table metadata
            metrics: Join metrics
            join_frequency_pct: Join frequency percentage
            total_queries: Total query count

        Returns:
            DetectedPattern if net benefit is positive, None otherwise
        """
        # Calculate costs
        avg_join_cost_ms = metrics["total_cost"] / metrics["count"]

        # Estimate maintenance cost of denormalization
        # Simplified: assume denormalization adds overhead to dimension updates
        update_propagation_cost = self._estimate_update_propagation_cost(
            dimension_table, len(metrics["columns_accessed"])
        )

        net_benefit_ms_per_day = metrics["total_cost"] - update_propagation_cost

        if net_benefit_ms_per_day <= 0:
            return None  # No net benefit

        # Determine severity
        if net_benefit_ms_per_day > 10000:  # 10+ seconds saved per day
            severity = "HIGH"
        else:
            severity = "MEDIUM"

        # Calculate confidence based on join frequency
        confidence = min(join_frequency_pct / 100, 0.95)

        # Create pattern
        pattern_id = f"EXPENSIVE_JOIN_{left_table}__{right_table}"
        affected_objects = [left_table, right_table]

        description = (
            f"Expensive join between {left_table} and {right_table} "
            f"executed {metrics['count']} times/day"
        )

        columns_list = list(metrics["columns_accessed"])
        recommendation_hint = f"Consider denormalizing {', '.join(columns_list)} into {left_table}"

        pattern = DetectedPattern(
            pattern_id=pattern_id,
            pattern_type="EXPENSIVE_JOIN",
            severity=severity,
            confidence=confidence,
            affected_objects=affected_objects,
            description=description,
            metrics={
                "join_frequency_per_day": metrics["count"],
                "join_frequency_percentage": join_frequency_pct,
                "avg_join_cost_ms": avg_join_cost_ms,
                "total_join_cost_ms_per_day": metrics["total_cost"],
                "columns_accessed": columns_list,
                "dimension_table_rows": dimension_table.num_rows,
                "net_benefit_ms_per_day": net_benefit_ms_per_day,
            },
            recommendation_hint=recommendation_hint,
        )

        logger.debug(
            f"Detected expensive join pattern: {pattern_id} "
            f"(freq={join_frequency_pct:.1f}%, net_benefit={net_benefit_ms_per_day:.0f}ms/day)"
        )

        return pattern

    def _estimate_update_propagation_cost(
        self, dimension_table: TableMetadata, num_columns: int
    ) -> float:
        """Estimate cost of propagating updates from dimension to fact table.

        This is a simplified heuristic. In production, this would use actual
        cardinality and update patterns.

        Args:
            dimension_table: Dimension table metadata
            num_columns: Number of columns to denormalize

        Returns:
            Estimated cost in ms per day
        """
        # Simplified heuristic:
        # - Small dimensions (< 10K rows): minimal propagation cost
        # - Medium dimensions (10K-100K): moderate cost
        # - Large dimensions (100K+): higher cost

        if dimension_table.num_rows < 10000:
            base_cost = 100  # 100ms per day
        elif dimension_table.num_rows < 100000:
            base_cost = 1000  # 1s per day
        else:
            base_cost = 5000  # 5s per day

        # Scale by number of columns
        cost_factor = 1.0 + (num_columns * 0.2)
        return base_cost * cost_factor


class DocumentRelationalClassifier:
    """Classifier for document vs relational storage optimization.

    Analyzes query patterns to determine if a table should be stored as
    a document (JSON) or relational structure based on access patterns.

    Document Storage Indicators:
    1. Queries fetch entire rows (SELECT *)
    2. Nested/hierarchical data structure
    3. Schema flexibility needed (varying attributes)
    4. Object-oriented access pattern

    Relational Storage Indicators:
    1. Column-specific queries
    2. Aggregate queries (SUM, AVG, GROUP BY)
    3. Complex JOIN patterns
    4. Fixed schema with well-defined relationships

    Attributes:
        strong_signal_threshold: Minimum |net_score| to recommend (default: 0.3)
        select_all_weight: Weight for SELECT * factor (default: 0.4)
        object_access_weight: Weight for object access factor (default: 0.3)
        schema_flexibility_weight: Weight for schema flexibility (default: 0.2)
        multi_column_update_weight: Weight for multi-column updates (default: 0.1)
    """

    def __init__(
        self,
        strong_signal_threshold: float = 0.3,
        select_all_weight: float = 0.4,
        object_access_weight: float = 0.3,
        schema_flexibility_weight: float = 0.2,
        multi_column_update_weight: float = 0.1,
    ):
        """Initialize DocumentRelationalClassifier with configurable weights.

        Args:
            strong_signal_threshold: Minimum score difference to recommend
            select_all_weight: Weight for SELECT * percentage
            object_access_weight: Weight for object access pattern
            schema_flexibility_weight: Weight for nullable columns
            multi_column_update_weight: Weight for multi-column updates
        """
        self.strong_signal_threshold = strong_signal_threshold
        self.select_all_weight = select_all_weight
        self.object_access_weight = object_access_weight
        self.schema_flexibility_weight = schema_flexibility_weight
        self.multi_column_update_weight = multi_column_update_weight

        logger.info(
            f"DocumentRelationalClassifier initialized with threshold={strong_signal_threshold}"
        )

    def classify(
        self,
        tables: List[TableMetadata],
        workload: WorkloadFeatures,
        schema: SchemaMetadata,
    ) -> List[DetectedPattern]:
        """Classify tables as document or relational candidates.

        Args:
            tables: List of tables to analyze
            workload: Workload features
            schema: Schema metadata

        Returns:
            List of detected patterns
        """
        patterns = []

        for table in tables:
            # Get queries accessing this table
            table_queries = self._get_table_queries(table, workload)

            if not table_queries:
                continue

            # Calculate document score
            document_score = self._calculate_document_score(table, table_queries)

            # Calculate relational score
            relational_score = self._calculate_relational_score(table, table_queries)

            # Determine recommendation
            net_score = document_score - relational_score

            if abs(net_score) > self.strong_signal_threshold:
                pattern = self._create_pattern(
                    table, net_score, document_score, relational_score, table_queries
                )
                if pattern:
                    patterns.append(pattern)

        logger.info(f"Classified {len(patterns)} tables for storage optimization")
        return patterns

    def _get_table_queries(
        self, table: TableMetadata, workload: WorkloadFeatures
    ) -> List[QueryPattern]:
        """Get queries that access a specific table.

        Args:
            table: Table to find queries for
            workload: Workload features

        Returns:
            List of queries accessing this table
        """
        return [q for q in workload.queries if table.name in q.tables]

    def _calculate_document_score(self, table: TableMetadata, queries: List[QueryPattern]) -> float:
        """Calculate document storage score.

        Args:
            table: Table metadata
            queries: Queries accessing this table

        Returns:
            Document score (0.0-1.0)
        """
        score = 0.0
        total_executions = sum(q.executions for q in queries)

        if total_executions == 0:
            return 0.0

        # Factor 1: SELECT * percentage (40% weight)
        select_all_executions = sum(q.executions for q in queries if self._is_select_all(q))
        select_all_pct = select_all_executions / total_executions
        score += select_all_pct * self.select_all_weight

        # Factor 2: Object access pattern (30% weight)
        # For now, use SELECT * as proxy for object access
        # In production, would check for child table fetches
        score += select_all_pct * self.object_access_weight

        # Factor 3: Schema flexibility (20% weight)
        nullable_pct = len([c for c in table.columns if c.nullable]) / len(table.columns)
        if nullable_pct > 0.5:  # More than 50% nullable indicates flexibility
            score += self.schema_flexibility_weight

        # Factor 4: Multi-column updates (10% weight)
        multi_col_update_pct = self._calculate_multi_column_update_percentage(queries)
        score += multi_col_update_pct * self.multi_column_update_weight

        return score

    def _calculate_relational_score(
        self, table: TableMetadata, queries: List[QueryPattern]
    ) -> float:
        """Calculate relational storage score.

        Args:
            table: Table metadata
            queries: Queries accessing this table

        Returns:
            Relational score (0.0-1.0)
        """
        score = 0.0
        total_executions = sum(q.executions for q in queries)

        if total_executions == 0:
            return 0.0

        # Factor 1: Aggregate queries (50% weight)
        aggregate_executions = sum(q.executions for q in queries if self._has_aggregates(q))
        aggregate_pct = aggregate_executions / total_executions
        score += aggregate_pct * 0.5

        # Factor 2: Complex joins (50% weight)
        # Consider joins with 2+ tables as complex
        join_executions = sum(q.executions for q in queries if q.join_count >= 2)
        join_pct = join_executions / total_executions
        score += join_pct * 0.5

        return score

    def _is_select_all(self, query: QueryPattern) -> bool:
        """Check if query is SELECT *.

        Args:
            query: Query pattern to check

        Returns:
            True if SELECT * query
        """
        if query.query_type != "SELECT":
            return False

        sql = query.sql_text.upper()
        # Simple heuristic: contains "SELECT *"
        return "SELECT *" in sql or "SELECT\n*" in sql or "SELECT\t*" in sql

    def _has_aggregates(self, query: QueryPattern) -> bool:
        """Check if query has aggregate functions.

        Args:
            query: Query pattern to check

        Returns:
            True if query has aggregates
        """
        if query.query_type != "SELECT":
            return False

        sql = query.sql_text.upper()
        aggregates = ["SUM(", "AVG(", "COUNT(", "MAX(", "MIN(", "GROUP BY"]
        return any(agg in sql for agg in aggregates)

    def _calculate_multi_column_update_percentage(self, queries: List[QueryPattern]) -> float:
        """Calculate percentage of updates that affect multiple columns.

        Args:
            queries: List of queries

        Returns:
            Percentage (0.0-1.0)
        """
        update_queries = [q for q in queries if q.query_type == "UPDATE"]
        if not update_queries:
            return 0.0

        total_update_executions = sum(q.executions for q in update_queries)
        if total_update_executions == 0:
            return 0.0

        # Heuristic: count SET clauses with multiple columns
        multi_col_executions = 0
        for query in update_queries:
            sql = query.sql_text.upper()
            # Count commas in SET clause (rough heuristic)
            if "SET" in sql:
                set_clause = (
                    sql.split("SET")[1].split("WHERE")[0] if "WHERE" in sql else sql.split("SET")[1]
                )
                comma_count = set_clause.count(",")
                if comma_count >= 2:  # 3+ columns being updated
                    multi_col_executions += query.executions

        return multi_col_executions / total_update_executions

    def _create_pattern(
        self,
        table: TableMetadata,
        net_score: float,
        document_score: float,
        relational_score: float,
        queries: List[QueryPattern],
    ) -> DetectedPattern | None:
        """Create pattern from classification results.

        Args:
            table: Table being classified
            net_score: Net score (document - relational)
            document_score: Document storage score
            relational_score: Relational storage score
            queries: Queries accessing this table

        Returns:
            DetectedPattern or None
        """
        confidence = abs(net_score)

        if net_score > 0:  # Document candidate
            pattern_type = "DOCUMENT_CANDIDATE"
            description = (
                f"Table {table.name} accessed as complete objects, "
                f"candidate for JSON document storage"
            )
            recommendation_hint = f"Convert {table.name} to JSON collection with document storage"

            # Calculate metrics
            total_executions = sum(q.executions for q in queries)
            select_all_executions = sum(q.executions for q in queries if self._is_select_all(q))
            select_all_pct = (
                (select_all_executions / total_executions * 100) if total_executions > 0 else 0
            )

            nullable_pct = len([c for c in table.columns if c.nullable]) / len(table.columns) * 100

            multi_col_update_pct = self._calculate_multi_column_update_percentage(queries) * 100

            metrics = {
                "document_score": document_score,
                "relational_score": relational_score,
                "select_all_percentage": select_all_pct,
                "nullable_column_percentage": nullable_pct,
                "multi_column_update_percentage": multi_col_update_pct,
            }

        else:  # Relational candidate (net_score < 0)
            pattern_type = "RELATIONAL_CANDIDATE"
            description = (
                f"Table {table.name} accessed with column-specific and aggregate queries, "
                f"better as relational"
            )
            recommendation_hint = f"Normalize {table.name} into relational structure"

            # Calculate metrics
            total_executions = sum(q.executions for q in queries)
            aggregate_executions = sum(q.executions for q in queries if self._has_aggregates(q))
            aggregate_pct = (
                (aggregate_executions / total_executions * 100) if total_executions > 0 else 0
            )

            join_executions = sum(q.executions for q in queries if q.join_count >= 2)
            join_pct = (join_executions / total_executions * 100) if total_executions > 0 else 0

            metrics = {
                "document_score": document_score,
                "relational_score": relational_score,
                "aggregate_query_percentage": aggregate_pct,
                "join_query_percentage": join_pct,
            }

        pattern_id = f"{pattern_type}_{table.name}"

        pattern = DetectedPattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            severity="MEDIUM",  # Storage optimization is generally medium severity
            confidence=confidence,
            affected_objects=[table.name],
            description=description,
            metrics=metrics,
            recommendation_hint=recommendation_hint,
        )

        logger.debug(
            f"Created {pattern_type} pattern for {table.name} "
            f"(doc_score={document_score:.2f}, rel_score={relational_score:.2f})"
        )

        return pattern


class DualityViewOpportunityFinder:
    """Finder for JSON Duality View opportunities.

    JSON Duality Views in Oracle 23ai provide dual representation:
    - OLTP access: Insert/update individual documents
    - Analytics access: Query across documents with SQL

    Opportunity exists when a table has:
    1. Significant OLTP access (INSERT/UPDATE/simple SELECT)
    2. Significant Analytics access (aggregates, complex joins)
    3. Sufficient overlap to justify dual representation

    Attributes:
        min_oltp_percentage: Minimum OLTP query percentage (default: 10.0)
        min_analytics_percentage: Minimum Analytics query percentage (default: 10.0)
        duality_refresh_overhead_factor: Overhead factor for view refresh (default: 0.1)
    """

    def __init__(
        self,
        min_oltp_percentage: float = 10.0,
        min_analytics_percentage: float = 10.0,
        duality_refresh_overhead_factor: float = 0.1,
    ):
        """Initialize DualityViewOpportunityFinder with configurable thresholds.

        Args:
            min_oltp_percentage: Minimum OLTP percentage to trigger detection
            min_analytics_percentage: Minimum Analytics percentage to trigger detection
            duality_refresh_overhead_factor: Overhead factor for view refresh
        """
        self.min_oltp_percentage = min_oltp_percentage
        self.min_analytics_percentage = min_analytics_percentage
        self.duality_refresh_overhead_factor = duality_refresh_overhead_factor

        logger.info(
            f"DualityViewOpportunityFinder initialized with thresholds: "
            f"min_oltp={min_oltp_percentage}%, "
            f"min_analytics={min_analytics_percentage}%, "
            f"refresh_overhead={duality_refresh_overhead_factor}"
        )

    def find_opportunities(
        self, tables: List[TableMetadata], workload: WorkloadFeatures
    ) -> List[DetectedPattern]:
        """Find JSON Duality View opportunities in workload.

        Args:
            tables: List of tables to analyze
            workload: Workload features

        Returns:
            List of detected duality view opportunities
        """
        patterns = []

        for table in tables:
            # Get queries for this table
            table_queries = self._get_table_queries(table, workload)

            if not table_queries:
                continue

            # Classify queries as OLTP or Analytics
            oltp_executions = self._count_oltp_executions(table_queries)
            analytics_executions = self._count_analytics_executions(table_queries)

            total_executions = sum(q.executions for q in table_queries)

            if total_executions == 0:
                continue

            # Calculate percentages
            oltp_percentage = (oltp_executions / total_executions) * 100
            analytics_percentage = (analytics_executions / total_executions) * 100

            # Check if dual access pattern exists
            if (
                oltp_percentage >= self.min_oltp_percentage
                and analytics_percentage >= self.min_analytics_percentage
            ):
                pattern = self._create_duality_pattern(
                    table,
                    oltp_executions,
                    analytics_executions,
                    oltp_percentage,
                    analytics_percentage,
                    table_queries,
                )
                if pattern:
                    patterns.append(pattern)

        logger.info(f"Found {len(patterns)} JSON Duality View opportunities")
        return patterns

    def _get_table_queries(
        self, table: TableMetadata, workload: WorkloadFeatures
    ) -> List[QueryPattern]:
        """Get queries that access a specific table.

        Args:
            table: Table to find queries for
            workload: Workload features

        Returns:
            List of queries accessing this table
        """
        return [q for q in workload.queries if table.name in q.tables]

    def _count_oltp_executions(self, queries: List[QueryPattern]) -> int:
        """Count OLTP query executions.

        OLTP queries are:
        - INSERT
        - UPDATE
        - DELETE
        - Simple SELECT (no joins, no aggregates)

        Args:
            queries: List of queries

        Returns:
            Total OLTP executions
        """
        oltp_count = 0

        for query in queries:
            if query.query_type in ["INSERT", "UPDATE", "DELETE"]:
                oltp_count += query.executions
            elif query.query_type == "SELECT":
                # Simple SELECT: no joins and no aggregates
                if query.join_count == 0 and not self._has_aggregates(query):
                    oltp_count += query.executions

        return oltp_count

    def _count_analytics_executions(self, queries: List[QueryPattern]) -> int:
        """Count Analytics query executions.

        Analytics queries are:
        - SELECT with aggregates (COUNT, SUM, AVG, etc.)
        - SELECT with complex joins (2+ tables)

        Args:
            queries: List of queries

        Returns:
            Total Analytics executions
        """
        analytics_count = 0

        for query in queries:
            if query.query_type == "SELECT":
                # Analytics: has aggregates OR has joins
                if self._has_aggregates(query) or query.join_count > 0:
                    analytics_count += query.executions

        return analytics_count

    def _has_aggregates(self, query: QueryPattern) -> bool:
        """Check if query has aggregate functions.

        Args:
            query: Query pattern to check

        Returns:
            True if query has aggregates
        """
        sql = query.sql_text.upper()
        aggregates = ["SUM(", "AVG(", "COUNT(", "MAX(", "MIN(", "GROUP BY"]
        return any(agg in sql for agg in aggregates)

    def _create_duality_pattern(
        self,
        table: TableMetadata,
        oltp_executions: int,
        analytics_executions: int,
        oltp_percentage: float,
        analytics_percentage: float,
        queries: List[QueryPattern],
    ) -> DetectedPattern | None:
        """Create duality view pattern from analysis.

        Args:
            table: Table being analyzed
            oltp_executions: OLTP execution count
            analytics_executions: Analytics execution count
            oltp_percentage: OLTP percentage
            analytics_percentage: Analytics percentage
            queries: All queries for this table

        Returns:
            DetectedPattern or None
        """
        # Calculate duality score: min of the two percentages
        # Higher score = more balanced dual access
        duality_score = min(oltp_percentage, analytics_percentage) / 100.0

        # Determine severity based on balance
        if duality_score >= 0.3:  # 30%+ of both types
            severity = "HIGH"
        elif duality_score >= 0.15:  # 15%+ of both types
            severity = "MEDIUM"
        else:
            severity = "LOW"

        # Confidence is same as duality score
        confidence = duality_score

        # Create pattern
        pattern_id = f"DUALITY_VIEW_OPPORTUNITY_{table.schema}_{table.name}"
        affected_objects = [f"{table.schema}.{table.name}"]

        description = (
            f"Table has dual access patterns: "
            f"{oltp_percentage:.1f}% OLTP, {analytics_percentage:.1f}% Analytics"
        )

        recommendation_hint = (
            f"Create JSON Duality View for {table.schema}.{table.name} "
            f"to optimize both OLTP and Analytics access patterns"
        )

        pattern = DetectedPattern(
            pattern_id=pattern_id,
            pattern_type="DUALITY_VIEW_OPPORTUNITY",
            severity=severity,
            confidence=confidence,
            affected_objects=affected_objects,
            description=description,
            metrics={
                "oltp_executions": oltp_executions,
                "analytics_executions": analytics_executions,
                "oltp_percentage": oltp_percentage,
                "analytics_percentage": analytics_percentage,
                "duality_score": duality_score,
            },
            recommendation_hint=recommendation_hint,
        )

        logger.debug(
            f"Found duality view opportunity: {pattern_id} "
            f"(oltp={oltp_percentage:.1f}%, analytics={analytics_percentage:.1f}%, "
            f"score={duality_score:.2f})"
        )

        return pattern
