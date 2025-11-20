"""Data models for recommendation engine.

This module defines data structures used throughout the recommendation engine
for pattern detection, cost calculation, and tradeoff analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class DetectedPattern:
    """A detected anti-pattern or optimization opportunity.

    Attributes:
        pattern_id: Unique identifier for this pattern instance
        pattern_type: Type of pattern (LOB_CLIFF, EXPENSIVE_JOIN, etc.)
        severity: Impact level (HIGH, MEDIUM, LOW)
        confidence: Detection confidence score (0.0-1.0)
        affected_objects: List of affected database objects (tables, columns)
        description: Human-readable description of the pattern
        metrics: Pattern-specific metrics as key-value pairs
        recommendation_hint: Initial suggestion for addressing the pattern
    """

    pattern_id: str
    pattern_type: str
    severity: str
    confidence: float
    affected_objects: List[str]
    description: str
    metrics: Dict[str, Any]
    recommendation_hint: str

    def __post_init__(self) -> None:
        """Validate pattern data after initialization."""
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

        if self.severity not in ["HIGH", "MEDIUM", "LOW"]:
            raise ValueError(f"Severity must be HIGH, MEDIUM, or LOW, got {self.severity}")


@dataclass
class PatternDetectorInput:
    """Input data for pattern detection module.

    Attributes:
        workload_features: Workload features from FeatureEngineer
        schema_metadata: Schema metadata from SchemaCollector
        performance_baseline: Current performance metrics (optional)
    """

    workload_features: Dict[str, Any]
    schema_metadata: Dict[str, Any]
    performance_baseline: Optional[Dict[str, float]] = None


@dataclass
class PatternDetectorOutput:
    """Output from pattern detection module.

    Attributes:
        patterns: List of detected patterns
        detection_timestamp: When pattern detection was performed
        analysis_summary: Summary statistics by pattern type
    """

    patterns: List[DetectedPattern]
    detection_timestamp: datetime
    analysis_summary: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Calculate analysis summary if not provided."""
        if not self.analysis_summary:
            self.analysis_summary = {}
            for pattern in self.patterns:
                self.analysis_summary[pattern.pattern_type] = (
                    self.analysis_summary.get(pattern.pattern_type, 0) + 1
                )


@dataclass
class TableMetadata:
    """Metadata for a database table.

    Attributes:
        name: Table name
        schema: Schema/owner name
        num_rows: Row count
        avg_row_len: Average row length in bytes
        columns: List of column metadata
        compression: Whether table uses compression
    """

    name: str
    schema: str
    num_rows: int
    avg_row_len: int
    columns: List["ColumnMetadata"]
    compression: bool = False


@dataclass
class ColumnMetadata:
    """Metadata for a table column.

    Attributes:
        name: Column name
        data_type: Oracle data type (VARCHAR2, NUMBER, JSON, CLOB, etc.)
        nullable: Whether column allows NULL values
        avg_size: Average column size in bytes
    """

    name: str
    data_type: str
    nullable: bool
    avg_size: Optional[int] = None


@dataclass
class JoinInfo:
    """Information about a join in a query.

    Attributes:
        left_table: Left side table in join
        right_table: Right side table in join
        columns_fetched: Columns fetched from right table
        join_type: Type of join (INNER, LEFT, RIGHT, FULL)
    """

    left_table: str
    right_table: str
    columns_fetched: List[str]
    join_type: str = "INNER"


@dataclass
class QueryPattern:
    """Represents a query pattern from workload analysis.

    Attributes:
        query_id: Unique query identifier (SQL_ID)
        sql_text: Query text
        query_type: Query type (SELECT, INSERT, UPDATE, DELETE)
        executions: Execution count
        avg_elapsed_time_ms: Average elapsed time in milliseconds
        tables: List of tables accessed
        join_count: Number of joins in query
        normalized_sql: Normalized SQL text for pattern matching
        joins: List of join information for this query
    """

    query_id: str
    sql_text: str
    query_type: str
    executions: int
    avg_elapsed_time_ms: float
    tables: List[str]
    join_count: int = 0
    normalized_sql: Optional[str] = None
    joins: List[JoinInfo] = field(default_factory=list)


@dataclass
class WorkloadFeatures:
    """Aggregated workload features.

    Attributes:
        queries: List of query patterns
        total_executions: Total query executions
        unique_patterns: Number of unique query patterns
    """

    queries: List[QueryPattern]
    total_executions: int
    unique_patterns: int


@dataclass
class SchemaMetadata:
    """Database schema metadata.

    Attributes:
        tables: Dictionary of table name to TableMetadata
    """

    tables: Dict[str, TableMetadata]

    def get_table(self, table_name: str) -> Optional[TableMetadata]:
        """Get table metadata by name.

        Args:
            table_name: Name of table to retrieve

        Returns:
            TableMetadata if found, None otherwise
        """
        return self.tables.get(table_name)
