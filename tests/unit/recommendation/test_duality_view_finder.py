"""Unit tests for DualityViewOpportunityFinder.

Tests the detection of JSON Duality View opportunities based on dual
access patterns (OLTP + Analytics).
"""

import pytest

from src.recommendation.models import (
    ColumnMetadata,
    JoinInfo,
    QueryPattern,
    TableMetadata,
    WorkloadFeatures,
)
from src.recommendation.pattern_detector import DualityViewOpportunityFinder


@pytest.fixture
def sample_table():
    """Create a sample table for testing."""
    return TableMetadata(
        name="ORDERS",
        schema="SALES",
        num_rows=1000000,
        avg_row_len=500,
        columns=[
            ColumnMetadata(name="ORDER_ID", data_type="NUMBER", nullable=False),
            ColumnMetadata(name="CUSTOMER_ID", data_type="NUMBER", nullable=False),
            ColumnMetadata(name="ORDER_DATE", data_type="DATE", nullable=False),
            ColumnMetadata(name="TOTAL_AMOUNT", data_type="NUMBER", nullable=True),
            ColumnMetadata(name="STATUS", data_type="VARCHAR2", nullable=True),
        ],
    )


@pytest.fixture
def oltp_queries():
    """Create OLTP queries (INSERTs, UPDATEs, simple SELECTs)."""
    return [
        QueryPattern(
            query_id="sql_001",
            sql_text="INSERT INTO ORDERS VALUES (:1, :2, :3, :4, :5)",
            query_type="INSERT",
            executions=500,
            avg_elapsed_time_ms=2.0,
            tables=["ORDERS"],
        ),
        QueryPattern(
            query_id="sql_002",
            sql_text="UPDATE ORDERS SET STATUS = :1 WHERE ORDER_ID = :2",
            query_type="UPDATE",
            executions=300,
            avg_elapsed_time_ms=3.0,
            tables=["ORDERS"],
        ),
        QueryPattern(
            query_id="sql_003",
            sql_text="SELECT * FROM ORDERS WHERE ORDER_ID = :1",
            query_type="SELECT",
            executions=1000,
            avg_elapsed_time_ms=1.5,
            tables=["ORDERS"],
        ),
    ]


@pytest.fixture
def analytics_queries():
    """Create Analytics queries (aggregates, complex joins)."""
    return [
        QueryPattern(
            query_id="sql_004",
            sql_text="SELECT COUNT(*), AVG(TOTAL_AMOUNT) FROM ORDERS GROUP BY STATUS",
            query_type="SELECT",
            executions=200,
            avg_elapsed_time_ms=50.0,
            tables=["ORDERS"],
        ),
        QueryPattern(
            query_id="sql_005",
            sql_text="SELECT o.*, c.NAME FROM ORDERS o JOIN CUSTOMERS c ON o.CUSTOMER_ID = c.CUSTOMER_ID",
            query_type="SELECT",
            executions=150,
            avg_elapsed_time_ms=30.0,
            tables=["ORDERS", "CUSTOMERS"],
            join_count=1,
            joins=[
                JoinInfo(
                    left_table="ORDERS",
                    right_table="CUSTOMERS",
                    columns_fetched=["NAME"],
                )
            ],
        ),
    ]


def test_initialization():
    """Test that DualityViewOpportunityFinder initializes with default parameters."""
    finder = DualityViewOpportunityFinder()
    assert finder.min_oltp_percentage == 10.0
    assert finder.min_analytics_percentage == 10.0
    assert finder.duality_refresh_overhead_factor == 0.1


def test_initialization_with_custom_parameters():
    """Test that DualityViewOpportunityFinder initializes with custom parameters."""
    finder = DualityViewOpportunityFinder(
        min_oltp_percentage=15.0,
        min_analytics_percentage=20.0,
        duality_refresh_overhead_factor=0.15,
    )
    assert finder.min_oltp_percentage == 15.0
    assert finder.min_analytics_percentage == 20.0
    assert finder.duality_refresh_overhead_factor == 0.15


def test_detects_duality_view_opportunity(sample_table, oltp_queries, analytics_queries):
    """Test detection of table with dual access patterns."""
    finder = DualityViewOpportunityFinder()

    # Add background queries to reach 5000+ total while maintaining dual access pattern
    # Need to keep analytics >= 10% (500+) and OLTP >= 10% (500+)
    background_queries = [
        QueryPattern(
            query_id="sql_bg1",
            sql_text="SELECT ORDER_ID, STATUS FROM ORDERS WHERE CUSTOMER_ID = :1",
            query_type="SELECT",
            executions=2500,  # Background OLTP reads
            avg_elapsed_time_ms=1.0,
            tables=["ORDERS"],
        ),
        QueryPattern(
            query_id="sql_bg2",
            sql_text="SELECT AVG(TOTAL_AMOUNT), COUNT(*) FROM ORDERS GROUP BY ORDER_DATE",
            query_type="SELECT",
            executions=350,  # Background analytics to reach 700 total (14%)
            avg_elapsed_time_ms=40.0,
            tables=["ORDERS"],
        ),
    ]

    workload = WorkloadFeatures(
        queries=oltp_queries + analytics_queries + background_queries,
        total_executions=5000,
        unique_patterns=7,
    )

    patterns = finder.find_opportunities([sample_table], workload)

    assert len(patterns) == 1
    assert patterns[0].pattern_type == "DUALITY_VIEW_OPPORTUNITY"
    assert patterns[0].affected_objects == ["SALES.ORDERS"]


def test_no_detection_for_oltp_only(sample_table, oltp_queries):
    """Test that OLTP-only tables are not flagged for duality views."""
    finder = DualityViewOpportunityFinder()

    # Add more OLTP queries to reach 5000+ total (still OLTP-only)
    additional_oltp = [
        QueryPattern(
            query_id="sql_bg1",
            sql_text="SELECT * FROM ORDERS WHERE ORDER_ID = :1",
            query_type="SELECT",
            executions=3200,  # More OLTP reads
            avg_elapsed_time_ms=1.5,
            tables=["ORDERS"],
        ),
    ]

    workload = WorkloadFeatures(
        queries=oltp_queries + additional_oltp,
        total_executions=5000,
        unique_patterns=4,
    )

    patterns = finder.find_opportunities([sample_table], workload)

    assert len(patterns) == 0


def test_no_detection_for_analytics_only(sample_table, analytics_queries):
    """Test that Analytics-only tables are not flagged for duality views."""
    finder = DualityViewOpportunityFinder()

    # Add more analytics queries to reach 5000+ total (still analytics-only)
    additional_analytics = [
        QueryPattern(
            query_id="sql_bg1",
            sql_text="SELECT SUM(TOTAL_AMOUNT) FROM ORDERS GROUP BY ORDER_DATE",
            query_type="SELECT",
            executions=4650,  # More analytics queries
            avg_elapsed_time_ms=40.0,
            tables=["ORDERS"],
        ),
    ]

    workload = WorkloadFeatures(
        queries=analytics_queries + additional_analytics,
        total_executions=5000,
        unique_patterns=3,
    )

    patterns = finder.find_opportunities([sample_table], workload)

    assert len(patterns) == 0


def test_no_detection_for_empty_workload(sample_table):
    """Test that empty workload produces no patterns."""
    finder = DualityViewOpportunityFinder()
    workload = WorkloadFeatures(queries=[], total_executions=0, unique_patterns=0)

    patterns = finder.find_opportunities([sample_table], workload)

    assert len(patterns) == 0


def test_severity_classification(sample_table, oltp_queries, analytics_queries):
    """Test severity classification based on duality score."""
    finder = DualityViewOpportunityFinder()

    # Balanced workload (roughly 50/50 OLTP and Analytics) for HIGH severity
    background_queries = [
        QueryPattern(
            query_id="sql_bg1",
            sql_text="SELECT ORDER_ID FROM ORDERS WHERE ORDER_ID = :1",
            query_type="SELECT",
            executions=800,  # OLTP reads
            avg_elapsed_time_ms=1.0,
            tables=["ORDERS"],
        ),
        QueryPattern(
            query_id="sql_bg2",
            sql_text="SELECT AVG(TOTAL_AMOUNT) FROM ORDERS GROUP BY STATUS",
            query_type="SELECT",
            executions=2200,  # Analytics (make analytics ~46% for better balance)
            avg_elapsed_time_ms=30.0,
            tables=["ORDERS"],
        ),
    ]

    workload = WorkloadFeatures(
        queries=oltp_queries + analytics_queries + background_queries,
        total_executions=5000,
        unique_patterns=7,
    )

    patterns = finder.find_opportunities([sample_table], workload)

    # With balanced workload (OLTP ~54%, Analytics ~46%), duality score ~46% = HIGH severity
    assert patterns[0].severity in ["HIGH", "MEDIUM"]


def test_pattern_metrics_include_required_fields(sample_table, oltp_queries, analytics_queries):
    """Test that pattern metrics include all required fields."""
    finder = DualityViewOpportunityFinder()

    background_queries = [
        QueryPattern(
            query_id="sql_bg1",
            sql_text="UPDATE ORDERS SET STATUS = :1 WHERE ORDER_ID = :2",
            query_type="UPDATE",
            executions=2500,  # Background OLTP updates
            avg_elapsed_time_ms=2.0,
            tables=["ORDERS"],
        ),
        QueryPattern(
            query_id="sql_bg2",
            sql_text="SELECT SUM(TOTAL_AMOUNT) FROM ORDERS",
            query_type="SELECT",
            executions=350,  # Background analytics
            avg_elapsed_time_ms=25.0,
            tables=["ORDERS"],
        ),
    ]

    workload = WorkloadFeatures(
        queries=oltp_queries + analytics_queries + background_queries,
        total_executions=5000,
        unique_patterns=7,
    )

    patterns = finder.find_opportunities([sample_table], workload)

    assert "oltp_executions" in patterns[0].metrics
    assert "analytics_executions" in patterns[0].metrics
    assert "oltp_percentage" in patterns[0].metrics
    assert "analytics_percentage" in patterns[0].metrics
    assert "duality_score" in patterns[0].metrics


def test_duality_score_calculation(sample_table, oltp_queries, analytics_queries):
    """Test that duality score is calculated correctly."""
    finder = DualityViewOpportunityFinder()

    background_queries = [
        QueryPattern(
            query_id="sql_bg1",
            sql_text="INSERT INTO ORDERS VALUES (:1, :2, :3, :4, :5)",
            query_type="INSERT",
            executions=2500,  # Background OLTP inserts
            avg_elapsed_time_ms=2.0,
            tables=["ORDERS"],
        ),
        QueryPattern(
            query_id="sql_bg2",
            sql_text="SELECT MIN(TOTAL_AMOUNT), MAX(TOTAL_AMOUNT) FROM ORDERS",
            query_type="SELECT",
            executions=350,  # Background analytics
            avg_elapsed_time_ms=20.0,
            tables=["ORDERS"],
        ),
    ]

    workload = WorkloadFeatures(
        queries=oltp_queries + analytics_queries + background_queries,
        total_executions=5000,
        unique_patterns=7,
    )

    patterns = finder.find_opportunities([sample_table], workload)

    # Duality score should be min(oltp_percentage, analytics_percentage) / 100
    oltp_pct = patterns[0].metrics["oltp_percentage"]
    analytics_pct = patterns[0].metrics["analytics_percentage"]
    expected_score = min(oltp_pct, analytics_pct) / 100.0

    assert abs(patterns[0].metrics["duality_score"] - expected_score) < 0.01


def test_recommendation_mentions_duality_views(sample_table, oltp_queries, analytics_queries):
    """Test that recommendation mentions JSON Duality Views."""
    finder = DualityViewOpportunityFinder()

    background_queries = [
        QueryPattern(
            query_id="sql_bg1",
            sql_text="SELECT * FROM ORDERS WHERE ORDER_ID = :1",
            query_type="SELECT",
            executions=2500,  # Background OLTP reads
            avg_elapsed_time_ms=1.0,
            tables=["ORDERS"],
        ),
        QueryPattern(
            query_id="sql_bg2",
            sql_text="SELECT COUNT(DISTINCT CUSTOMER_ID) FROM ORDERS",
            query_type="SELECT",
            executions=350,  # Background analytics
            avg_elapsed_time_ms=35.0,
            tables=["ORDERS"],
        ),
    ]

    workload = WorkloadFeatures(
        queries=oltp_queries + analytics_queries + background_queries,
        total_executions=5000,
        unique_patterns=7,
    )

    patterns = finder.find_opportunities([sample_table], workload)

    assert "JSON Duality View" in patterns[0].recommendation_hint
    assert "OLTP" in patterns[0].recommendation_hint
    assert "Analytics" in patterns[0].recommendation_hint


def test_description_includes_percentages(sample_table, oltp_queries, analytics_queries):
    """Test that description includes OLTP and Analytics percentages."""
    finder = DualityViewOpportunityFinder()

    background_queries = [
        QueryPattern(
            query_id="sql_bg1",
            sql_text="SELECT ORDER_ID, STATUS FROM ORDERS WHERE CUSTOMER_ID = :1",
            query_type="SELECT",
            executions=2500,  # Background OLTP reads
            avg_elapsed_time_ms=1.0,
            tables=["ORDERS"],
        ),
        QueryPattern(
            query_id="sql_bg2",
            sql_text="SELECT COUNT(*) FROM ORDERS WHERE ORDER_DATE > :1",
            query_type="SELECT",
            executions=350,  # Background analytics
            avg_elapsed_time_ms=30.0,
            tables=["ORDERS"],
        ),
    ]

    workload = WorkloadFeatures(
        queries=oltp_queries + analytics_queries + background_queries,
        total_executions=5000,
        unique_patterns=7,
    )

    patterns = finder.find_opportunities([sample_table], workload)

    description = patterns[0].description
    assert "OLTP" in description
    assert "Analytics" in description
    assert "%" in description


def test_pattern_id_uniqueness(sample_table, oltp_queries, analytics_queries):
    """Test that each detected pattern has a unique ID."""
    finder = DualityViewOpportunityFinder()

    # Create two tables
    table1 = sample_table
    table2 = TableMetadata(
        name="LINE_ITEMS",
        schema="SALES",
        num_rows=5000000,
        avg_row_len=200,
        columns=[
            ColumnMetadata(name="LINE_ID", data_type="NUMBER", nullable=False),
            ColumnMetadata(name="ORDER_ID", data_type="NUMBER", nullable=False),
        ],
    )

    # Create queries for both tables with dual access
    queries = (
        oltp_queries
        + analytics_queries
        + [
            QueryPattern(
                query_id="sql_006",
                sql_text="INSERT INTO LINE_ITEMS VALUES (:1, :2)",
                query_type="INSERT",
                executions=500,  # OLTP for LINE_ITEMS
                avg_elapsed_time_ms=1.0,
                tables=["LINE_ITEMS"],
            ),
            QueryPattern(
                query_id="sql_007",
                sql_text="SELECT COUNT(*) FROM LINE_ITEMS GROUP BY ORDER_ID",
                query_type="SELECT",
                executions=200,  # Analytics for LINE_ITEMS
                avg_elapsed_time_ms=20.0,
                tables=["LINE_ITEMS"],
            ),
            QueryPattern(
                query_id="sql_bg1",
                sql_text="SELECT * FROM ORDERS WHERE ORDER_ID = :1",
                query_type="SELECT",
                executions=2150,  # Background OLTP for ORDERS
                avg_elapsed_time_ms=1.0,
                tables=["ORDERS"],
            ),
        ]
    )

    workload = WorkloadFeatures(
        queries=queries,
        total_executions=5000,
        unique_patterns=8,
    )

    patterns = finder.find_opportunities([table1, table2], workload)

    pattern_ids = [p.pattern_id for p in patterns]
    assert len(pattern_ids) == len(set(pattern_ids))  # All IDs unique


def test_confidence_score_range(sample_table, oltp_queries, analytics_queries):
    """Test that confidence score is between 0.0 and 1.0."""
    finder = DualityViewOpportunityFinder()

    background_queries = [
        QueryPattern(
            query_id="sql_bg1",
            sql_text="UPDATE ORDERS SET STATUS = :1 WHERE ORDER_ID = :2",
            query_type="UPDATE",
            executions=2500,  # Background OLTP updates
            avg_elapsed_time_ms=3.0,
            tables=["ORDERS"],
        ),
        QueryPattern(
            query_id="sql_bg2",
            sql_text="SELECT COUNT(*), SUM(TOTAL_AMOUNT) FROM ORDERS GROUP BY CUSTOMER_ID",
            query_type="SELECT",
            executions=350,  # Background analytics
            avg_elapsed_time_ms=45.0,
            tables=["ORDERS"],
        ),
    ]

    workload = WorkloadFeatures(
        queries=oltp_queries + analytics_queries + background_queries,
        total_executions=5000,
        unique_patterns=7,
    )

    patterns = finder.find_opportunities([sample_table], workload)

    assert 0.0 <= patterns[0].confidence <= 1.0


def test_low_analytics_percentage_below_threshold(sample_table, oltp_queries):
    """Test that tables with low analytics percentage are not flagged."""
    finder = DualityViewOpportunityFinder(min_analytics_percentage=15.0)

    # Add a small number of analytics queries (< 15%) plus background OLTP
    analytics_queries = [
        QueryPattern(
            query_id="sql_004",
            sql_text="SELECT COUNT(*) FROM ORDERS",
            query_type="SELECT",
            executions=500,  # 10% of total (below 15% threshold)
            avg_elapsed_time_ms=20.0,
            tables=["ORDERS"],
        ),
    ]

    background_oltp = [
        QueryPattern(
            query_id="sql_bg1",
            sql_text="SELECT * FROM ORDERS WHERE ORDER_ID = :1",
            query_type="SELECT",
            executions=3500,  # More OLTP to reach 5000 total
            avg_elapsed_time_ms=1.0,
            tables=["ORDERS"],
        ),
    ]

    workload = WorkloadFeatures(
        queries=oltp_queries + analytics_queries + background_oltp,
        total_executions=5000,
        unique_patterns=5,
    )

    patterns = finder.find_opportunities([sample_table], workload)

    # Should not detect because analytics percentage < 15%
    assert len(patterns) == 0


def test_aggregate_query_classification():
    """Test that queries with aggregates are classified as Analytics."""
    finder = DualityViewOpportunityFinder()

    table = TableMetadata(
        name="PRODUCTS",
        schema="INVENTORY",
        num_rows=10000,
        avg_row_len=300,
        columns=[
            ColumnMetadata(name="PRODUCT_ID", data_type="NUMBER", nullable=False),
        ],
    )

    queries = [
        # OLTP queries
        QueryPattern(
            query_id="sql_001",
            sql_text="INSERT INTO PRODUCTS VALUES (:1)",
            query_type="INSERT",
            executions=400,  # OLTP inserts
            avg_elapsed_time_ms=2.0,
            tables=["PRODUCTS"],
        ),
        # Analytics queries with various aggregates
        QueryPattern(
            query_id="sql_002",
            sql_text="SELECT COUNT(*) FROM PRODUCTS",
            query_type="SELECT",
            executions=200,  # Analytics aggregate
            avg_elapsed_time_ms=10.0,
            tables=["PRODUCTS"],
        ),
        QueryPattern(
            query_id="sql_003",
            sql_text="SELECT AVG(PRICE) FROM PRODUCTS",
            query_type="SELECT",
            executions=150,  # Analytics aggregate
            avg_elapsed_time_ms=15.0,
            tables=["PRODUCTS"],
        ),
        # Background OLTP to reach 5000+ total
        QueryPattern(
            query_id="sql_bg1",
            sql_text="SELECT * FROM PRODUCTS WHERE PRODUCT_ID = :1",
            query_type="SELECT",
            executions=2650,  # OLTP reads
            avg_elapsed_time_ms=1.0,
            tables=["PRODUCTS"],
        ),
        # Background analytics to maintain dual access
        QueryPattern(
            query_id="sql_bg2",
            sql_text="SELECT SUM(PRICE) FROM PRODUCTS GROUP BY CATEGORY",
            query_type="SELECT",
            executions=1600,  # Analytics aggregate
            avg_elapsed_time_ms=25.0,
            tables=["PRODUCTS"],
        ),
    ]

    workload = WorkloadFeatures(
        queries=queries,
        total_executions=5000,
        unique_patterns=5,
    )

    patterns = finder.find_opportunities([table], workload)

    # Should detect because we have both OLTP and Analytics
    assert len(patterns) == 1
    assert patterns[0].metrics["analytics_executions"] == 1950  # 200 + 150 + 1600
