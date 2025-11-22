"""Unit tests for LOB Cliff Detector.

This module tests the LOBCliffDetector class which identifies tables where
small updates to large LOB/JSON columns cause performance issues.
"""

import pytest

from src.recommendation.models import ColumnMetadata, QueryPattern, TableMetadata, WorkloadFeatures


# Test fixtures
@pytest.fixture
def table_with_large_json_column():
    """Provide table with large JSON column susceptible to LOB cliff."""
    return TableMetadata(
        name="ORDERS",
        schema="APP",
        num_rows=1000000,
        avg_row_len=5000,
        columns=[
            ColumnMetadata(name="ORDER_ID", data_type="NUMBER", nullable=False, avg_size=8),
            ColumnMetadata(name="ORDER_DATA", data_type="JSON", nullable=True, avg_size=6000),
            ColumnMetadata(name="STATUS", data_type="VARCHAR2", nullable=False, avg_size=20),
        ],
    )


@pytest.fixture
def table_with_clob_column():
    """Provide table with text CLOB column storing JSON."""
    return TableMetadata(
        name="DOCUMENTS",
        schema="APP",
        num_rows=500000,
        avg_row_len=8000,
        columns=[
            ColumnMetadata(name="DOC_ID", data_type="NUMBER", nullable=False, avg_size=8),
            ColumnMetadata(name="CONTENT", data_type="CLOB", nullable=True, avg_size=10000),
            ColumnMetadata(name="CREATED_AT", data_type="DATE", nullable=False, avg_size=8),
        ],
    )


@pytest.fixture
def frequent_update_queries():
    """Provide workload with frequent small updates to LOB columns."""
    return WorkloadFeatures(
        queries=[
            QueryPattern(
                query_id="update_001",
                sql_text="UPDATE ORDERS SET ORDER_DATA = :data WHERE ORDER_ID = :id",
                query_type="UPDATE",
                executions=3000,  # 3000 updates to LOB column
                avg_elapsed_time_ms=15.0,
                tables=["ORDERS"],
                join_count=0,
            ),
            QueryPattern(
                query_id="update_002",
                sql_text="UPDATE ORDERS SET STATUS = :status WHERE ORDER_ID = :id",
                query_type="UPDATE",
                executions=1500,  # 1500 non-LOB updates
                avg_elapsed_time_ms=5.0,
                tables=["ORDERS"],
                join_count=0,
            ),
            QueryPattern(
                query_id="select_001",
                sql_text="SELECT ORDER_ID, ORDER_DATA, STATUS FROM ORDERS WHERE ORDER_ID = :id",
                query_type="SELECT",
                executions=1000,  # 1000 reads
                avg_elapsed_time_ms=3.0,
                tables=["ORDERS"],
                join_count=0,
            ),
        ],
        total_executions=5500,  # Above 5000 threshold
        unique_patterns=3,
    )


@pytest.fixture
def infrequent_update_queries():
    """Provide workload with infrequent updates but sufficient total volume.

    2 LOB updates in 1-hour snapshot = 48 updates/day (below 100/day threshold)
    But total workload has 5500 queries to pass volume check.
    """
    return WorkloadFeatures(
        queries=[
            QueryPattern(
                query_id="update_rare",
                sql_text="UPDATE DOCUMENTS SET CONTENT = :content WHERE DOC_ID = :id",
                query_type="UPDATE",
                executions=2,  # 2 * 24 = 48 updates/day (below threshold)
                avg_elapsed_time_ms=20.0,
                tables=["DOCUMENTS"],
                join_count=0,
            ),
            QueryPattern(
                query_id="select_many",
                sql_text="SELECT DOC_ID, CONTENT FROM DOCUMENTS WHERE DOC_ID = :id",
                query_type="SELECT",
                executions=5498,  # Many reads to reach 5500 total
                avg_elapsed_time_ms=5.0,
                tables=["DOCUMENTS"],
                join_count=0,
            ),
        ],
        total_executions=5500,
        unique_patterns=2,
    )


class TestLOBCliffDetectorInitialization:
    """Test LOBCliffDetector initialization."""

    @pytest.mark.unit
    def test_detector_initialization_with_defaults(self):
        """Test that LOBCliffDetector initializes with default thresholds."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        detector = LOBCliffDetector()

        assert detector is not None
        assert detector.large_doc_threshold_bytes == 4096
        assert detector.high_update_frequency_threshold == 100
        assert detector.small_update_selectivity_threshold == 0.1

    @pytest.mark.unit
    def test_detector_initialization_with_custom_thresholds(self):
        """Test that LOBCliffDetector accepts custom thresholds."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        detector = LOBCliffDetector(
            large_doc_threshold_bytes=8192,
            high_update_frequency_threshold=200,
            small_update_selectivity_threshold=0.05,
        )

        assert detector.large_doc_threshold_bytes == 8192
        assert detector.high_update_frequency_threshold == 200
        assert detector.small_update_selectivity_threshold == 0.05


class TestLOBCliffDetection:
    """Test LOB cliff pattern detection."""

    @pytest.mark.unit
    def test_detects_high_risk_lob_cliff(
        self, table_with_large_json_column, frequent_update_queries
    ):
        """Test detection of high-risk LOB cliff pattern."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        detector = LOBCliffDetector()
        # Use 24-hour snapshot for full confidence (no snapshot penalty)
        patterns = detector.detect(
            [table_with_large_json_column], frequent_update_queries, snapshot_duration_hours=24.0
        )

        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.pattern_type == "LOB_CLIFF"
        assert pattern.severity == "HIGH"
        assert pattern.confidence >= 0.6
        assert "ORDERS.ORDER_DATA" in pattern.affected_objects

    @pytest.mark.unit
    def test_no_detection_for_small_columns(self, frequent_update_queries):
        """Test that small columns don't trigger LOB cliff detection."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        small_table = TableMetadata(
            name="USERS",
            schema="APP",
            num_rows=100000,
            avg_row_len=200,
            columns=[
                ColumnMetadata(name="USER_ID", data_type="NUMBER", nullable=False, avg_size=8),
                ColumnMetadata(name="PROFILE", data_type="JSON", nullable=True, avg_size=500),
            ],
        )

        detector = LOBCliffDetector()
        patterns = detector.detect(
            [small_table], frequent_update_queries, snapshot_duration_hours=24.0
        )

        assert len(patterns) == 0

    @pytest.mark.unit
    def test_no_detection_for_infrequent_updates(
        self, table_with_clob_column, infrequent_update_queries
    ):
        """Test that infrequent updates don't trigger detection."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        detector = LOBCliffDetector()
        patterns = detector.detect(
            [table_with_clob_column], infrequent_update_queries, snapshot_duration_hours=24.0
        )

        assert len(patterns) == 0

    @pytest.mark.unit
    def test_no_detection_for_tables_without_lob_columns(self, frequent_update_queries):
        """Test that tables without LOB columns are ignored."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        non_lob_table = TableMetadata(
            name="CUSTOMERS",
            schema="APP",
            num_rows=50000,
            avg_row_len=150,
            columns=[
                ColumnMetadata(name="CUST_ID", data_type="NUMBER", nullable=False, avg_size=8),
                ColumnMetadata(name="NAME", data_type="VARCHAR2", nullable=False, avg_size=100),
                ColumnMetadata(name="EMAIL", data_type="VARCHAR2", nullable=True, avg_size=50),
            ],
        )

        detector = LOBCliffDetector()
        patterns = detector.detect(
            [non_lob_table], frequent_update_queries, snapshot_duration_hours=24.0
        )

        assert len(patterns) == 0

    @pytest.mark.unit
    def test_severity_classification(self, table_with_large_json_column):
        """Test that severity is correctly classified based on risk score."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        # High frequency updates (should be HIGH severity)
        high_frequency = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="update_high",
                    sql_text="UPDATE ORDERS SET ORDER_DATA = :data WHERE ORDER_ID = :id",
                    query_type="UPDATE",
                    executions=1000,  # Frequent LOB updates
                    avg_elapsed_time_ms=15.0,
                    tables=["ORDERS"],
                    join_count=0,
                ),
                QueryPattern(
                    query_id="select_background",
                    sql_text="SELECT ORDER_ID, ORDER_DATA FROM ORDERS WHERE ORDER_ID = :id",
                    query_type="SELECT",
                    executions=4500,  # Background reads to reach 5500 total
                    avg_elapsed_time_ms=3.0,
                    tables=["ORDERS"],
                    join_count=0,
                ),
            ],
            total_executions=5500,
            unique_patterns=2,
        )

        detector = LOBCliffDetector()
        patterns = detector.detect(
            [table_with_large_json_column], high_frequency, snapshot_duration_hours=24.0
        )

        assert len(patterns) == 1
        assert patterns[0].severity == "HIGH"
        assert patterns[0].confidence >= 0.8

    @pytest.mark.unit
    def test_medium_severity_for_moderate_risk(self, table_with_large_json_column):
        """Test medium severity for moderate risk patterns."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        # Moderate frequency updates with slightly slower queries (should be MEDIUM severity)
        # Slower query means higher selectivity (not small updates), reducing risk score
        moderate_frequency = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="update_mod",
                    sql_text="UPDATE ORDERS SET ORDER_DATA = :data WHERE ORDER_ID = :id",
                    query_type="UPDATE",
                    executions=150,  # Moderate LOB updates
                    avg_elapsed_time_ms=25.0,  # Slower query -> higher selectivity
                    tables=["ORDERS"],
                    join_count=0,
                ),
                QueryPattern(
                    query_id="select_background",
                    sql_text="SELECT ORDER_ID, STATUS FROM ORDERS WHERE ORDER_ID = :id",
                    query_type="SELECT",
                    executions=5350,  # Background reads to reach 5500 total
                    avg_elapsed_time_ms=2.0,
                    tables=["ORDERS"],
                    join_count=0,
                ),
            ],
            total_executions=5500,
            unique_patterns=2,
        )

        detector = LOBCliffDetector()
        patterns = detector.detect(
            [table_with_large_json_column], moderate_frequency, snapshot_duration_hours=24.0
        )

        assert len(patterns) == 1
        assert patterns[0].severity == "MEDIUM"
        assert 0.6 <= patterns[0].confidence < 0.8


class TestLOBCliffMetrics:
    """Test metrics calculation for LOB cliff patterns."""

    @pytest.mark.unit
    def test_pattern_includes_correct_metrics(
        self, table_with_large_json_column, frequent_update_queries
    ):
        """Test that detected pattern includes all required metrics."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        detector = LOBCliffDetector()
        patterns = detector.detect(
            [table_with_large_json_column], frequent_update_queries, snapshot_duration_hours=24.0
        )

        assert len(patterns) == 1
        metrics = patterns[0].metrics

        assert "avg_document_size_kb" in metrics
        assert "updates_per_day" in metrics
        assert "update_selectivity" in metrics
        assert "storage_type" in metrics
        assert "format" in metrics

        assert metrics["storage_type"] in ["in_row", "out_of_line"]
        assert metrics["format"] in ["OSON", "TEXT"]

    @pytest.mark.unit
    def test_storage_type_detection(self):
        """Test correct storage type classification based on size."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        # Large document (out-of-line)
        large_table = TableMetadata(
            name="LARGE_DOCS",
            schema="APP",
            num_rows=10000,
            avg_row_len=8000,
            columns=[
                ColumnMetadata(name="ID", data_type="NUMBER", nullable=False, avg_size=8),
                ColumnMetadata(name="DATA", data_type="JSON", nullable=True, avg_size=6000),
            ],
        )

        workload = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="upd",
                    sql_text="UPDATE LARGE_DOCS SET DATA = :d WHERE ID = :id",
                    query_type="UPDATE",
                    executions=200,  # LOB updates
                    avg_elapsed_time_ms=10.0,
                    tables=["LARGE_DOCS"],
                ),
                QueryPattern(
                    query_id="sel",
                    sql_text="SELECT ID, DATA FROM LARGE_DOCS WHERE ID = :id",
                    query_type="SELECT",
                    executions=5300,  # Background reads to reach 5500 total
                    avg_elapsed_time_ms=5.0,
                    tables=["LARGE_DOCS"],
                ),
            ],
            total_executions=5500,
            unique_patterns=2,
        )

        detector = LOBCliffDetector()
        patterns = detector.detect([large_table], workload, snapshot_duration_hours=24.0)

        assert len(patterns) == 1
        assert patterns[0].metrics["storage_type"] == "out_of_line"

    @pytest.mark.unit
    def test_format_detection_for_json_vs_clob(self):
        """Test format detection distinguishes JSON from CLOB columns."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        json_table = TableMetadata(
            name="JSON_TABLE",
            schema="APP",
            num_rows=10000,
            avg_row_len=5000,
            columns=[
                ColumnMetadata(name="ID", data_type="NUMBER", nullable=False, avg_size=8),
                ColumnMetadata(name="DATA", data_type="JSON", nullable=True, avg_size=5000),
            ],
        )

        clob_table = TableMetadata(
            name="CLOB_TABLE",
            schema="APP",
            num_rows=10000,
            avg_row_len=5000,
            columns=[
                ColumnMetadata(name="ID", data_type="NUMBER", nullable=False, avg_size=8),
                ColumnMetadata(name="DATA", data_type="CLOB", nullable=True, avg_size=5000),
            ],
        )

        workload = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="upd1",
                    sql_text="UPDATE JSON_TABLE SET DATA = :d WHERE ID = :id",
                    query_type="UPDATE",
                    executions=200,  # JSON LOB updates
                    avg_elapsed_time_ms=10.0,
                    tables=["JSON_TABLE"],
                ),
                QueryPattern(
                    query_id="upd2",
                    sql_text="UPDATE CLOB_TABLE SET DATA = :d WHERE ID = :id",
                    query_type="UPDATE",
                    executions=200,  # CLOB updates
                    avg_elapsed_time_ms=10.0,
                    tables=["CLOB_TABLE"],
                ),
                QueryPattern(
                    query_id="sel1",
                    sql_text="SELECT ID, DATA FROM JSON_TABLE WHERE ID = :id",
                    query_type="SELECT",
                    executions=2550,  # Background reads
                    avg_elapsed_time_ms=5.0,
                    tables=["JSON_TABLE"],
                ),
                QueryPattern(
                    query_id="sel2",
                    sql_text="SELECT ID, DATA FROM CLOB_TABLE WHERE ID = :id",
                    query_type="SELECT",
                    executions=2550,  # Background reads
                    avg_elapsed_time_ms=5.0,
                    tables=["CLOB_TABLE"],
                ),
            ],
            total_executions=5500,
            unique_patterns=4,
        )

        detector = LOBCliffDetector()
        patterns = detector.detect([json_table, clob_table], workload, snapshot_duration_hours=24.0)

        assert len(patterns) == 2

        json_pattern = [p for p in patterns if "JSON_TABLE" in p.affected_objects[0]][0]
        clob_pattern = [p for p in patterns if "CLOB_TABLE" in p.affected_objects[0]][0]

        assert json_pattern.metrics["format"] == "OSON"
        assert clob_pattern.metrics["format"] == "TEXT"


class TestLOBCliffRecommendations:
    """Test recommendation hints for LOB cliff patterns."""

    @pytest.mark.unit
    def test_recommendation_hint_provided(
        self, table_with_large_json_column, frequent_update_queries
    ):
        """Test that detection includes recommendation hint."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        detector = LOBCliffDetector()
        patterns = detector.detect(
            [table_with_large_json_column], frequent_update_queries, snapshot_duration_hours=24.0
        )

        assert len(patterns) == 1
        assert patterns[0].recommendation_hint
        assert len(patterns[0].recommendation_hint) > 0

    @pytest.mark.unit
    def test_recommendation_mentions_splitting_or_separation(
        self, table_with_large_json_column, frequent_update_queries
    ):
        """Test that recommendation suggests splitting or separating data."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        detector = LOBCliffDetector()
        patterns = detector.detect(
            [table_with_large_json_column], frequent_update_queries, snapshot_duration_hours=24.0
        )

        assert len(patterns) == 1
        hint = patterns[0].recommendation_hint.lower()

        assert any(
            keyword in hint for keyword in ["split", "separate", "metadata", "table", "column"]
        )


class TestLOBCliffEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_empty_tables_list(self, frequent_update_queries):
        """Test handling of empty tables list."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        detector = LOBCliffDetector()
        patterns = detector.detect([], frequent_update_queries)

        assert len(patterns) == 0

    @pytest.mark.unit
    def test_empty_workload(self, table_with_large_json_column):
        """Test handling of empty workload."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        empty_workload = WorkloadFeatures(queries=[], total_executions=0, unique_patterns=0)

        detector = LOBCliffDetector()
        patterns = detector.detect(
            [table_with_large_json_column], empty_workload, snapshot_duration_hours=24.0
        )

        assert len(patterns) == 0

    @pytest.mark.unit
    def test_multiple_lob_columns_in_same_table(self, frequent_update_queries):
        """Test detection of multiple LOB columns in same table."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        multi_lob_table = TableMetadata(
            name="COMPLEX_TABLE",
            schema="APP",
            num_rows=100000,
            avg_row_len=15000,
            columns=[
                ColumnMetadata(name="ID", data_type="NUMBER", nullable=False, avg_size=8),
                ColumnMetadata(name="DATA1", data_type="JSON", nullable=True, avg_size=6000),
                ColumnMetadata(name="DATA2", data_type="CLOB", nullable=True, avg_size=7000),
            ],
        )

        workload = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="upd1",
                    sql_text="UPDATE COMPLEX_TABLE SET DATA1 = :d WHERE ID = :id",
                    query_type="UPDATE",
                    executions=200,  # JSON LOB updates
                    avg_elapsed_time_ms=10.0,
                    tables=["COMPLEX_TABLE"],
                ),
                QueryPattern(
                    query_id="upd2",
                    sql_text="UPDATE COMPLEX_TABLE SET DATA2 = :d WHERE ID = :id",
                    query_type="UPDATE",
                    executions=150,  # CLOB updates
                    avg_elapsed_time_ms=12.0,
                    tables=["COMPLEX_TABLE"],
                ),
                QueryPattern(
                    query_id="sel",
                    sql_text="SELECT ID, DATA1, DATA2 FROM COMPLEX_TABLE WHERE ID = :id",
                    query_type="SELECT",
                    executions=5150,  # Background reads to reach 5500 total
                    avg_elapsed_time_ms=8.0,
                    tables=["COMPLEX_TABLE"],
                ),
            ],
            total_executions=5500,
            unique_patterns=3,
        )

        detector = LOBCliffDetector()
        patterns = detector.detect([multi_lob_table], workload, snapshot_duration_hours=24.0)

        assert len(patterns) == 2
        assert (
            "COMPLEX_TABLE.DATA1" in patterns[0].affected_objects
            or "COMPLEX_TABLE.DATA1" in patterns[1].affected_objects
        )
        assert (
            "COMPLEX_TABLE.DATA2" in patterns[0].affected_objects
            or "COMPLEX_TABLE.DATA2" in patterns[1].affected_objects
        )

    @pytest.mark.unit
    def test_pattern_id_uniqueness(self, table_with_large_json_column, frequent_update_queries):
        """Test that each detected pattern has a unique ID."""
        from src.recommendation.pattern_detector import LOBCliffDetector

        detector = LOBCliffDetector()
        patterns = detector.detect(
            [table_with_large_json_column], frequent_update_queries, snapshot_duration_hours=24.0
        )

        pattern_ids = [p.pattern_id for p in patterns]
        assert len(pattern_ids) == len(set(pattern_ids))  # All unique
