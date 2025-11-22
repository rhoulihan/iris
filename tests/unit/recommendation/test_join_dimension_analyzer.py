"""Unit tests for Join Dimension Analyzer.

This module tests the JoinDimensionAnalyzer class which identifies expensive
join patterns that could benefit from denormalization.
"""

import pytest

from src.recommendation.models import (
    ColumnMetadata,
    JoinInfo,
    QueryPattern,
    SchemaMetadata,
    TableMetadata,
    WorkloadFeatures,
)


# Test fixtures
@pytest.fixture
def small_dimension_table():
    """Provide small dimension table metadata."""
    return TableMetadata(
        name="CUSTOMERS",
        schema="APP",
        num_rows=10000,
        avg_row_len=200,
        columns=[
            ColumnMetadata(name="CUSTOMER_ID", data_type="NUMBER", nullable=False, avg_size=8),
            ColumnMetadata(
                name="CUSTOMER_NAME", data_type="VARCHAR2", nullable=False, avg_size=100
            ),
            ColumnMetadata(name="CUSTOMER_TIER", data_type="VARCHAR2", nullable=True, avg_size=20),
            ColumnMetadata(name="EMAIL", data_type="VARCHAR2", nullable=True, avg_size=100),
        ],
    )


@pytest.fixture
def large_dimension_table():
    """Provide large dimension table metadata."""
    return TableMetadata(
        name="PRODUCTS",
        schema="APP",
        num_rows=2000000,
        avg_row_len=300,
        columns=[
            ColumnMetadata(name="PRODUCT_ID", data_type="NUMBER", nullable=False, avg_size=8),
            ColumnMetadata(name="PRODUCT_NAME", data_type="VARCHAR2", nullable=False, avg_size=200),
            ColumnMetadata(name="CATEGORY", data_type="VARCHAR2", nullable=True, avg_size=50),
        ],
    )


@pytest.fixture
def fact_table():
    """Provide fact table metadata."""
    return TableMetadata(
        name="ORDERS",
        schema="APP",
        num_rows=5000000,
        avg_row_len=150,
        columns=[
            ColumnMetadata(name="ORDER_ID", data_type="NUMBER", nullable=False, avg_size=8),
            ColumnMetadata(name="CUSTOMER_ID", data_type="NUMBER", nullable=False, avg_size=8),
            ColumnMetadata(name="PRODUCT_ID", data_type="NUMBER", nullable=False, avg_size=8),
            ColumnMetadata(name="ORDER_DATE", data_type="DATE", nullable=False, avg_size=8),
            ColumnMetadata(name="AMOUNT", data_type="NUMBER", nullable=False, avg_size=8),
        ],
    )


@pytest.fixture
def frequent_join_workload():
    """Provide workload with frequent joins."""
    return WorkloadFeatures(
        queries=[
            QueryPattern(
                query_id="join_001",
                sql_text="SELECT o.*, c.customer_name, c.customer_tier FROM orders o JOIN customers c ON o.customer_id = c.customer_id",
                query_type="SELECT",
                executions=5000,
                avg_elapsed_time_ms=25.0,
                tables=["ORDERS", "CUSTOMERS"],
                join_count=1,
                joins=[
                    JoinInfo(
                        left_table="ORDERS",
                        right_table="CUSTOMERS",
                        columns_fetched=["customer_name", "customer_tier"],
                        join_type="INNER",
                    )
                ],
            ),
            QueryPattern(
                query_id="join_002",
                sql_text="SELECT o.order_id, c.customer_name FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE o.order_date > :date",
                query_type="SELECT",
                executions=3000,
                avg_elapsed_time_ms=20.0,
                tables=["ORDERS", "CUSTOMERS"],
                join_count=1,
                joins=[
                    JoinInfo(
                        left_table="ORDERS",
                        right_table="CUSTOMERS",
                        columns_fetched=["customer_name"],
                        join_type="INNER",
                    )
                ],
            ),
            QueryPattern(
                query_id="select_001",
                sql_text="SELECT * FROM orders WHERE order_id = :id",
                query_type="SELECT",
                executions=2000,
                avg_elapsed_time_ms=5.0,
                tables=["ORDERS"],
                join_count=0,
            ),
        ],
        total_executions=10000,
        unique_patterns=3,
    )


@pytest.fixture
def infrequent_join_workload():
    """Provide workload with infrequent joins."""
    return WorkloadFeatures(
        queries=[
            QueryPattern(
                query_id="join_rare",
                sql_text="SELECT o.*, p.product_name FROM orders o JOIN products p ON o.product_id = p.product_id",
                query_type="SELECT",
                executions=50,
                avg_elapsed_time_ms=30.0,
                tables=["ORDERS", "PRODUCTS"],
                join_count=1,
                joins=[
                    JoinInfo(
                        left_table="ORDERS",
                        right_table="PRODUCTS",
                        columns_fetched=["product_name"],
                        join_type="INNER",
                    )
                ],
            ),
            QueryPattern(
                query_id="select_002",
                sql_text="SELECT * FROM orders WHERE customer_id = :id",
                query_type="SELECT",
                executions=5000,
                avg_elapsed_time_ms=10.0,
                tables=["ORDERS"],
                join_count=0,
            ),
        ],
        total_executions=5050,
        unique_patterns=2,
    )


class TestJoinDimensionAnalyzerInitialization:
    """Test JoinDimensionAnalyzer initialization."""

    @pytest.mark.unit
    def test_analyzer_initialization_with_defaults(self):
        """Test that JoinDimensionAnalyzer initializes with default thresholds."""
        from src.recommendation.pattern_detector import JoinDimensionAnalyzer

        analyzer = JoinDimensionAnalyzer()

        assert analyzer is not None
        assert analyzer.min_join_frequency_percentage == 10.0
        assert analyzer.max_columns_fetched == 5
        assert analyzer.max_dimension_rows == 1000000
        assert analyzer.max_dimension_update_rate == 100

    @pytest.mark.unit
    def test_analyzer_initialization_with_custom_thresholds(self):
        """Test that JoinDimensionAnalyzer accepts custom thresholds."""
        from src.recommendation.pattern_detector import JoinDimensionAnalyzer

        analyzer = JoinDimensionAnalyzer(
            min_join_frequency_percentage=5.0,
            max_columns_fetched=3,
            max_dimension_rows=500000,
            max_dimension_update_rate=50,
        )

        assert analyzer.min_join_frequency_percentage == 5.0
        assert analyzer.max_columns_fetched == 3
        assert analyzer.max_dimension_rows == 500000
        assert analyzer.max_dimension_update_rate == 50


class TestJoinDimensionDetection:
    """Test join dimension pattern detection."""

    @pytest.mark.unit
    def test_detects_frequent_join_pattern(
        self, small_dimension_table, fact_table, frequent_join_workload
    ):
        """Test detection of frequent join patterns."""
        from src.recommendation.pattern_detector import JoinDimensionAnalyzer

        schema = SchemaMetadata(
            tables={
                "CUSTOMERS": small_dimension_table,
                "ORDERS": fact_table,
            }
        )

        analyzer = JoinDimensionAnalyzer()
        patterns = analyzer.analyze(frequent_join_workload, schema)

        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.pattern_type == "EXPENSIVE_JOIN"
        assert pattern.severity in ["HIGH", "MEDIUM"]
        assert "ORDERS" in pattern.affected_objects
        assert "CUSTOMERS" in pattern.affected_objects

    @pytest.mark.unit
    def test_no_detection_for_infrequent_joins(
        self, large_dimension_table, fact_table, infrequent_join_workload
    ):
        """Test that infrequent joins don't trigger detection."""
        from src.recommendation.pattern_detector import JoinDimensionAnalyzer

        schema = SchemaMetadata(
            tables={
                "PRODUCTS": large_dimension_table,
                "ORDERS": fact_table,
            }
        )

        analyzer = JoinDimensionAnalyzer()
        patterns = analyzer.analyze(infrequent_join_workload, schema)

        assert len(patterns) == 0

    @pytest.mark.unit
    def test_no_detection_for_large_dimension_with_high_updates(
        self, large_dimension_table, fact_table
    ):
        """Test that large, frequently-updated dimensions are not recommended."""
        from src.recommendation.pattern_detector import JoinDimensionAnalyzer

        # Create workload with frequent joins to large dimension
        workload = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="join_large",
                    sql_text="SELECT o.*, p.product_name FROM orders o JOIN products p ON o.product_id = p.product_id",
                    query_type="SELECT",
                    executions=2000,  # Joins to large dimension
                    avg_elapsed_time_ms=50.0,
                    tables=["ORDERS", "PRODUCTS"],
                    join_count=1,
                    joins=[
                        JoinInfo(
                            left_table="ORDERS",
                            right_table="PRODUCTS",
                            columns_fetched=["product_name"],
                            join_type="INNER",
                        )
                    ],
                ),
                # Add frequent updates to PRODUCTS table
                QueryPattern(
                    query_id="update_products",
                    sql_text="UPDATE products SET product_name = :name WHERE product_id = :id",
                    query_type="UPDATE",
                    executions=500,  # Frequent dimension updates
                    avg_elapsed_time_ms=10.0,
                    tables=["PRODUCTS"],
                    join_count=0,
                ),
                QueryPattern(
                    query_id="select_orders",
                    sql_text="SELECT * FROM orders WHERE order_id = :id",
                    query_type="SELECT",
                    executions=3000,  # Background reads to reach 5500 total
                    avg_elapsed_time_ms=5.0,
                    tables=["ORDERS"],
                    join_count=0,
                ),
            ],
            total_executions=5500,
            unique_patterns=3,
        )

        schema = SchemaMetadata(
            tables={
                "PRODUCTS": large_dimension_table,
                "ORDERS": fact_table,
            }
        )

        analyzer = JoinDimensionAnalyzer()
        patterns = analyzer.analyze(workload, schema)

        # Should not detect because dimension is too large and frequently updated
        assert len(patterns) == 0

    @pytest.mark.unit
    def test_no_detection_for_too_many_columns(self, small_dimension_table, fact_table):
        """Test that joins fetching too many columns don't trigger detection."""
        from src.recommendation.pattern_detector import JoinDimensionAnalyzer

        # Join fetching all columns from dimension
        workload = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="join_all",
                    sql_text="SELECT o.*, c.* FROM orders o JOIN customers c ON o.customer_id = c.customer_id",
                    query_type="SELECT",
                    executions=2000,  # Join fetching too many columns
                    avg_elapsed_time_ms=30.0,
                    tables=["ORDERS", "CUSTOMERS"],
                    join_count=1,
                    joins=[
                        JoinInfo(
                            left_table="ORDERS",
                            right_table="CUSTOMERS",
                            columns_fetched=[
                                "customer_id",
                                "customer_name",
                                "customer_tier",
                                "email",
                                "address",
                                "phone",
                            ],
                            join_type="INNER",
                        )
                    ],
                ),
                QueryPattern(
                    query_id="select_orders",
                    sql_text="SELECT * FROM orders WHERE order_id = :id",
                    query_type="SELECT",
                    executions=3500,  # Background reads to reach 5500 total
                    avg_elapsed_time_ms=5.0,
                    tables=["ORDERS"],
                    join_count=0,
                ),
            ],
            total_executions=5500,
            unique_patterns=2,
        )

        schema = SchemaMetadata(
            tables={
                "CUSTOMERS": small_dimension_table,
                "ORDERS": fact_table,
            }
        )

        analyzer = JoinDimensionAnalyzer()
        patterns = analyzer.analyze(workload, schema)

        assert len(patterns) == 0


class TestJoinDimensionMetrics:
    """Test metrics calculation for join dimension patterns."""

    @pytest.mark.unit
    def test_pattern_includes_correct_metrics(
        self, small_dimension_table, fact_table, frequent_join_workload
    ):
        """Test that detected pattern includes all required metrics."""
        from src.recommendation.pattern_detector import JoinDimensionAnalyzer

        schema = SchemaMetadata(
            tables={
                "CUSTOMERS": small_dimension_table,
                "ORDERS": fact_table,
            }
        )

        analyzer = JoinDimensionAnalyzer()
        patterns = analyzer.analyze(frequent_join_workload, schema)

        assert len(patterns) == 1
        metrics = patterns[0].metrics

        assert "join_frequency_per_day" in metrics
        assert "join_frequency_percentage" in metrics
        assert "avg_join_cost_ms" in metrics
        assert "total_join_cost_ms_per_day" in metrics
        assert "columns_accessed" in metrics
        assert "dimension_table_rows" in metrics
        assert "net_benefit_ms_per_day" in metrics

        # Verify values
        assert metrics["join_frequency_per_day"] == 8000  # 5000 + 3000
        assert metrics["join_frequency_percentage"] == 80.0  # 8000 / 10000
        assert metrics["dimension_table_rows"] == 10000

    @pytest.mark.unit
    def test_columns_accessed_aggregation(
        self, small_dimension_table, fact_table, frequent_join_workload
    ):
        """Test that columns from multiple queries are aggregated."""
        from src.recommendation.pattern_detector import JoinDimensionAnalyzer

        schema = SchemaMetadata(
            tables={
                "CUSTOMERS": small_dimension_table,
                "ORDERS": fact_table,
            }
        )

        analyzer = JoinDimensionAnalyzer()
        patterns = analyzer.analyze(frequent_join_workload, schema)

        assert len(patterns) == 1
        columns = patterns[0].metrics["columns_accessed"]

        # Should have both customer_name and customer_tier
        assert "customer_name" in columns
        assert "customer_tier" in columns


class TestJoinDimensionSeverity:
    """Test severity classification for join dimension patterns."""

    @pytest.mark.unit
    def test_high_severity_for_high_frequency_joins(self, small_dimension_table, fact_table):
        """Test HIGH severity for very frequent joins."""
        from src.recommendation.pattern_detector import JoinDimensionAnalyzer

        # Very high frequency workload
        workload = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="join_vhigh",
                    sql_text="SELECT o.*, c.customer_name FROM orders o JOIN customers c ON o.customer_id = c.customer_id",
                    query_type="SELECT",
                    executions=9000,
                    avg_elapsed_time_ms=50.0,  # Expensive join
                    tables=["ORDERS", "CUSTOMERS"],
                    join_count=1,
                    joins=[
                        JoinInfo(
                            left_table="ORDERS",
                            right_table="CUSTOMERS",
                            columns_fetched=["customer_name"],
                            join_type="INNER",
                        )
                    ],
                ),
            ],
            total_executions=10000,
            unique_patterns=1,
        )

        schema = SchemaMetadata(
            tables={
                "CUSTOMERS": small_dimension_table,
                "ORDERS": fact_table,
            }
        )

        analyzer = JoinDimensionAnalyzer()
        patterns = analyzer.analyze(workload, schema)

        assert len(patterns) == 1
        assert patterns[0].severity == "HIGH"


class TestJoinDimensionRecommendations:
    """Test recommendation hints for join dimension patterns."""

    @pytest.mark.unit
    def test_recommendation_hint_provided(
        self, small_dimension_table, fact_table, frequent_join_workload
    ):
        """Test that detection includes recommendation hint."""
        from src.recommendation.pattern_detector import JoinDimensionAnalyzer

        schema = SchemaMetadata(
            tables={
                "CUSTOMERS": small_dimension_table,
                "ORDERS": fact_table,
            }
        )

        analyzer = JoinDimensionAnalyzer()
        patterns = analyzer.analyze(frequent_join_workload, schema)

        assert len(patterns) == 1
        assert patterns[0].recommendation_hint
        assert len(patterns[0].recommendation_hint) > 0

    @pytest.mark.unit
    def test_recommendation_mentions_denormalization(
        self, small_dimension_table, fact_table, frequent_join_workload
    ):
        """Test that recommendation suggests denormalization."""
        from src.recommendation.pattern_detector import JoinDimensionAnalyzer

        schema = SchemaMetadata(
            tables={
                "CUSTOMERS": small_dimension_table,
                "ORDERS": fact_table,
            }
        )

        analyzer = JoinDimensionAnalyzer()
        patterns = analyzer.analyze(frequent_join_workload, schema)

        assert len(patterns) == 1
        hint = patterns[0].recommendation_hint.lower()

        assert any(keyword in hint for keyword in ["denormaliz", "column", "into"])


class TestJoinDimensionEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_empty_workload(self, small_dimension_table, fact_table):
        """Test handling of empty workload."""
        from src.recommendation.pattern_detector import JoinDimensionAnalyzer

        empty_workload = WorkloadFeatures(queries=[], total_executions=0, unique_patterns=0)

        schema = SchemaMetadata(
            tables={
                "CUSTOMERS": small_dimension_table,
                "ORDERS": fact_table,
            }
        )

        analyzer = JoinDimensionAnalyzer()
        patterns = analyzer.analyze(empty_workload, schema)

        assert len(patterns) == 0

    @pytest.mark.unit
    def test_workload_with_no_joins(self, small_dimension_table, fact_table):
        """Test handling of workload with no joins."""
        from src.recommendation.pattern_detector import JoinDimensionAnalyzer

        workload = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="select_only",
                    sql_text="SELECT * FROM orders WHERE order_id = :id",
                    query_type="SELECT",
                    executions=5000,
                    avg_elapsed_time_ms=5.0,
                    tables=["ORDERS"],
                    join_count=0,
                ),
            ],
            total_executions=5000,
            unique_patterns=1,
        )

        schema = SchemaMetadata(
            tables={
                "CUSTOMERS": small_dimension_table,
                "ORDERS": fact_table,
            }
        )

        analyzer = JoinDimensionAnalyzer()
        patterns = analyzer.analyze(workload, schema)

        assert len(patterns) == 0

    @pytest.mark.unit
    def test_multiple_join_patterns(self, small_dimension_table, fact_table):
        """Test detection of multiple different join patterns."""
        from src.recommendation.pattern_detector import JoinDimensionAnalyzer

        # Create another small dimension
        categories = TableMetadata(
            name="CATEGORIES",
            schema="APP",
            num_rows=100,
            avg_row_len=50,
            columns=[
                ColumnMetadata(name="CATEGORY_ID", data_type="NUMBER", nullable=False, avg_size=8),
                ColumnMetadata(
                    name="CATEGORY_NAME", data_type="VARCHAR2", nullable=False, avg_size=50
                ),
            ],
        )

        workload = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="join_customers",
                    sql_text="SELECT o.*, c.customer_name FROM orders o JOIN customers c ON o.customer_id = c.customer_id",
                    query_type="SELECT",
                    executions=4000,
                    avg_elapsed_time_ms=25.0,
                    tables=["ORDERS", "CUSTOMERS"],
                    join_count=1,
                    joins=[
                        JoinInfo(
                            left_table="ORDERS",
                            right_table="CUSTOMERS",
                            columns_fetched=["customer_name"],
                            join_type="INNER",
                        )
                    ],
                ),
                QueryPattern(
                    query_id="join_categories",
                    sql_text="SELECT o.*, cat.category_name FROM orders o JOIN categories cat ON o.category_id = cat.category_id",
                    query_type="SELECT",
                    executions=3000,
                    avg_elapsed_time_ms=20.0,
                    tables=["ORDERS", "CATEGORIES"],
                    join_count=1,
                    joins=[
                        JoinInfo(
                            left_table="ORDERS",
                            right_table="CATEGORIES",
                            columns_fetched=["category_name"],
                            join_type="INNER",
                        )
                    ],
                ),
            ],
            total_executions=7000,
            unique_patterns=2,
        )

        schema = SchemaMetadata(
            tables={
                "CUSTOMERS": small_dimension_table,
                "CATEGORIES": categories,
                "ORDERS": fact_table,
            }
        )

        analyzer = JoinDimensionAnalyzer()
        patterns = analyzer.analyze(workload, schema)

        assert len(patterns) == 2

    @pytest.mark.unit
    def test_pattern_id_uniqueness(self, small_dimension_table, fact_table, frequent_join_workload):
        """Test that each detected pattern has a unique ID."""
        from src.recommendation.pattern_detector import JoinDimensionAnalyzer

        schema = SchemaMetadata(
            tables={
                "CUSTOMERS": small_dimension_table,
                "ORDERS": fact_table,
            }
        )

        analyzer = JoinDimensionAnalyzer()
        patterns = analyzer.analyze(frequent_join_workload, schema)

        pattern_ids = [p.pattern_id for p in patterns]
        assert len(pattern_ids) == len(set(pattern_ids))  # All unique
