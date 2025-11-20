"""Unit tests for workload compressor.

This module tests the WorkloadCompressor class which deduplicates and aggregates
SQL workload data for efficient LLM processing.
"""

import pytest


# Test data fixtures
@pytest.fixture
def sample_sql_statistics():
    """Provide sample SQL statistics from AWR collector."""
    return [
        {
            "sql_id": "abc123",
            "sql_text": "SELECT * FROM users WHERE age > 25",
            "plan_hash_value": 1234567890,
            "executions": 1000,
            "elapsed_time_ms": 50000.0,
            "cpu_time_ms": 45000.0,
            "disk_reads": 10000,
            "buffer_gets": 50000,
            "rows_processed": 100000,
            "avg_elapsed_time_ms": 50.0,
            "avg_cpu_time_ms": 45.0,
        },
        {
            "sql_id": "def456",
            "sql_text": "SELECT * FROM users WHERE age > 30",  # Similar to above
            "plan_hash_value": 1234567890,
            "executions": 500,
            "elapsed_time_ms": 25000.0,
            "cpu_time_ms": 22000.0,
            "disk_reads": 5000,
            "buffer_gets": 25000,
            "rows_processed": 50000,
            "avg_elapsed_time_ms": 50.0,
            "avg_cpu_time_ms": 44.0,
        },
        {
            "sql_id": "ghi789",
            "sql_text": "INSERT INTO orders VALUES (:1, :2, :3)",
            "plan_hash_value": 9876543210,
            "executions": 2000,
            "elapsed_time_ms": 100000.0,
            "cpu_time_ms": 90000.0,
            "disk_reads": 20000,
            "buffer_gets": 100000,
            "rows_processed": 2000,
            "avg_elapsed_time_ms": 50.0,
            "avg_cpu_time_ms": 45.0,
        },
    ]


@pytest.fixture
def duplicate_queries():
    """Provide identical queries with different literals."""
    return [
        {
            "sql_id": "q1",
            "sql_text": "SELECT * FROM products WHERE price < 100",
            "executions": 100,
            "elapsed_time_ms": 1000.0,
            "cpu_time_ms": 900.0,
            "disk_reads": 100,
            "buffer_gets": 500,
            "rows_processed": 1000,
            "avg_elapsed_time_ms": 10.0,
            "avg_cpu_time_ms": 9.0,
        },
        {
            "sql_id": "q2",
            "sql_text": "SELECT * FROM products WHERE price < 200",  # Same structure
            "executions": 150,
            "elapsed_time_ms": 1500.0,
            "cpu_time_ms": 1350.0,
            "disk_reads": 150,
            "buffer_gets": 750,
            "rows_processed": 1500,
            "avg_elapsed_time_ms": 10.0,
            "avg_cpu_time_ms": 9.0,
        },
        {
            "sql_id": "q3",
            "sql_text": "SELECT * FROM products WHERE price < 500",  # Same structure
            "executions": 200,
            "elapsed_time_ms": 2000.0,
            "cpu_time_ms": 1800.0,
            "disk_reads": 200,
            "buffer_gets": 1000,
            "rows_processed": 2000,
            "avg_elapsed_time_ms": 10.0,
            "avg_cpu_time_ms": 9.0,
        },
    ]


@pytest.fixture
def queries_with_missing_text():
    """Provide queries where some have missing SQL text."""
    return [
        {
            "sql_id": "valid1",
            "sql_text": "SELECT * FROM users",
            "executions": 100,
            "elapsed_time_ms": 1000.0,
            "cpu_time_ms": 900.0,
            "disk_reads": 100,
            "buffer_gets": 500,
            "rows_processed": 1000,
            "avg_elapsed_time_ms": 10.0,
            "avg_cpu_time_ms": 9.0,
        },
        {
            "sql_id": "missing1",
            "sql_text": None,  # Missing SQL text
            "executions": 50,
            "elapsed_time_ms": 500.0,
            "cpu_time_ms": 450.0,
            "disk_reads": 50,
            "buffer_gets": 250,
            "rows_processed": 500,
            "avg_elapsed_time_ms": 10.0,
            "avg_cpu_time_ms": 9.0,
        },
        {
            "sql_id": "valid2",
            "sql_text": "UPDATE users SET status = 'active'",
            "executions": 75,
            "elapsed_time_ms": 750.0,
            "cpu_time_ms": 675.0,
            "disk_reads": 75,
            "buffer_gets": 375,
            "rows_processed": 750,
            "avg_elapsed_time_ms": 10.0,
            "avg_cpu_time_ms": 9.0,
        },
    ]


class TestWorkloadCompressorInitialization:
    """Test WorkloadCompressor initialization."""

    @pytest.mark.unit
    def test_compressor_initialization(self):
        """Test that WorkloadCompressor can be initialized."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        assert compressor is not None

    @pytest.mark.unit
    def test_compressor_with_query_parser(self):
        """Test that compressor uses QueryParser internally."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        # Should have a query parser instance
        assert hasattr(compressor, "parser") or hasattr(compressor, "_parser")


class TestWorkloadCompression:
    """Test workload compression functionality."""

    @pytest.mark.unit
    def test_compress_empty_workload(self):
        """Test compression of empty workload."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress([])

        assert result is not None
        assert "groups" in result
        assert len(result["groups"]) == 0

    @pytest.mark.unit
    def test_compress_single_query(self):
        """Test compression of single query."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        queries = [
            {
                "sql_id": "test1",
                "sql_text": "SELECT * FROM users",
                "executions": 100,
                "elapsed_time_ms": 1000.0,
                "cpu_time_ms": 900.0,
                "disk_reads": 100,
                "buffer_gets": 500,
                "rows_processed": 1000,
                "avg_elapsed_time_ms": 10.0,
                "avg_cpu_time_ms": 9.0,
            }
        ]

        result = compressor.compress(queries)

        assert len(result["groups"]) == 1
        assert result["total_queries"] == 1
        assert result["total_executions"] == 100

    @pytest.mark.unit
    def test_compress_duplicate_queries(self, duplicate_queries):
        """Test that duplicate query structures are grouped together."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(duplicate_queries)

        # All 3 queries have same structure, should be grouped into 1
        assert len(result["groups"]) == 1
        assert result["total_queries"] == 3

        group = result["groups"][0]
        # Total executions should be sum of all 3
        assert group["total_executions"] == 100 + 150 + 200

    @pytest.mark.unit
    def test_compress_different_queries(self, sample_sql_statistics):
        """Test that different query structures are separated."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(sample_sql_statistics)

        # Should have 2 groups: SELECT queries (grouped) and INSERT query
        assert len(result["groups"]) == 2
        assert result["total_queries"] == 3


class TestAggregation:
    """Test statistics aggregation."""

    @pytest.mark.unit
    def test_aggregate_executions(self, duplicate_queries):
        """Test aggregation of execution counts."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(duplicate_queries)

        group = result["groups"][0]
        assert group["total_executions"] == 450  # 100 + 150 + 200

    @pytest.mark.unit
    def test_aggregate_elapsed_time(self, duplicate_queries):
        """Test aggregation of elapsed time."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(duplicate_queries)

        group = result["groups"][0]
        # Total elapsed time: 1000 + 1500 + 2000 = 4500
        assert group["total_elapsed_time_ms"] == 4500.0

    @pytest.mark.unit
    def test_calculate_average_metrics(self, duplicate_queries):
        """Test calculation of average metrics per group."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(duplicate_queries)

        group = result["groups"][0]
        # Average elapsed time: 4500 / 450 = 10.0
        assert group["avg_elapsed_time_ms"] == pytest.approx(10.0, rel=0.01)

    @pytest.mark.unit
    def test_aggregate_io_metrics(self, duplicate_queries):
        """Test aggregation of I/O metrics."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(duplicate_queries)

        group = result["groups"][0]
        # Total disk reads: 100 + 150 + 200 = 450
        assert group["total_disk_reads"] == 450
        # Total buffer gets: 500 + 750 + 1000 = 2250
        assert group["total_buffer_gets"] == 2250


class TestGroupMetadata:
    """Test metadata for each query group."""

    @pytest.mark.unit
    def test_group_has_signature(self, sample_sql_statistics):
        """Test that each group has a query signature."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(sample_sql_statistics)

        for group in result["groups"]:
            assert "signature" in group
            assert group["signature"] is not None
            assert len(group["signature"]) > 0

    @pytest.mark.unit
    def test_group_has_representative_sql(self, duplicate_queries):
        """Test that each group has representative SQL text."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(duplicate_queries)

        group = result["groups"][0]
        assert "representative_sql" in group
        assert "SELECT * FROM products WHERE price <" in group["representative_sql"]

    @pytest.mark.unit
    def test_group_has_query_count(self, duplicate_queries):
        """Test that each group tracks number of queries."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(duplicate_queries)

        group = result["groups"][0]
        assert "query_count" in group
        assert group["query_count"] == 3  # 3 duplicate queries

    @pytest.mark.unit
    def test_group_has_sql_ids(self, duplicate_queries):
        """Test that each group contains list of SQL IDs."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(duplicate_queries)

        group = result["groups"][0]
        assert "sql_ids" in group
        assert "q1" in group["sql_ids"]
        assert "q2" in group["sql_ids"]
        assert "q3" in group["sql_ids"]


class TestComplexityMetrics:
    """Test query complexity metrics in groups."""

    @pytest.mark.unit
    def test_group_has_complexity_info(self, sample_sql_statistics):
        """Test that groups include complexity metrics."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(sample_sql_statistics)

        for group in result["groups"]:
            assert "complexity" in group
            assert "table_count" in group["complexity"]

    @pytest.mark.unit
    def test_complexity_identifies_query_type(self, sample_sql_statistics):
        """Test that complexity includes query type."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(sample_sql_statistics)

        # Find SELECT group
        select_group = next(g for g in result["groups"] if "SELECT" in g["representative_sql"])
        assert select_group["query_type"] == "SELECT"

        # Find INSERT group
        insert_group = next(g for g in result["groups"] if "INSERT" in g["representative_sql"])
        assert insert_group["query_type"] == "INSERT"


class TestErrorHandling:
    """Test error handling in workload compression."""

    @pytest.mark.unit
    def test_handle_queries_without_sql_text(self, queries_with_missing_text):
        """Test handling of queries with missing SQL text."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(queries_with_missing_text)

        # Should process valid queries and skip invalid ones
        assert result is not None
        assert len(result["groups"]) == 2  # Only 2 valid queries

    @pytest.mark.unit
    def test_handle_none_input(self):
        """Test handling of None as input."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()

        with pytest.raises(ValueError, match="Workload data cannot be None"):
            compressor.compress(None)

    @pytest.mark.unit
    def test_handle_invalid_query_format(self):
        """Test handling of queries with missing required fields."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        queries = [
            {
                "sql_id": "test1",
                "sql_text": "SELECT * FROM users",
                # Missing executions field
            }
        ]

        # Should handle gracefully
        result = compressor.compress(queries)
        assert result is not None


class TestSummaryStatistics:
    """Test summary statistics in compression result."""

    @pytest.mark.unit
    def test_summary_has_total_queries(self, sample_sql_statistics):
        """Test that result includes total query count."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(sample_sql_statistics)

        assert "total_queries" in result
        assert result["total_queries"] == 3

    @pytest.mark.unit
    def test_summary_has_total_executions(self, sample_sql_statistics):
        """Test that result includes total execution count."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(sample_sql_statistics)

        assert "total_executions" in result
        assert result["total_executions"] == 1000 + 500 + 2000

    @pytest.mark.unit
    def test_summary_has_compression_ratio(self, duplicate_queries):
        """Test that result includes compression ratio."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(duplicate_queries)

        assert "compression_ratio" in result
        # 3 queries compressed to 1 group = 3:1 ratio
        assert result["compression_ratio"] == pytest.approx(3.0, rel=0.01)

    @pytest.mark.unit
    def test_summary_has_group_count(self, sample_sql_statistics):
        """Test that result includes number of groups."""
        from src.data.workload_compressor import WorkloadCompressor

        compressor = WorkloadCompressor()
        result = compressor.compress(sample_sql_statistics)

        assert "unique_patterns" in result
        assert result["unique_patterns"] == 2
