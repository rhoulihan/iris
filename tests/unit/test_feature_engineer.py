"""Unit tests for feature engineering module.

This module tests the FeatureEngineer class which extracts features from
compressed workload data for LLM analysis.
"""

import pytest


# Test data fixtures
@pytest.fixture
def sample_compressed_workload():
    """Provide sample compressed workload data."""
    return {
        "groups": [
            {
                "signature": "abc123",
                "representative_sql": "SELECT * FROM users WHERE age > ?",
                "query_type": "SELECT",
                "complexity": {
                    "table_count": 1,
                    "join_count": 0,
                    "where_conditions": 1,
                    "subquery_count": 0,
                    "function_count": 0,
                },
                "query_count": 3,
                "sql_ids": ["q1", "q2", "q3"],
                "total_executions": 450,
                "total_elapsed_time_ms": 4500.0,
                "total_cpu_time_ms": 4050.0,
                "total_disk_reads": 450,
                "total_buffer_gets": 2250,
                "total_rows_processed": 4500,
                "avg_elapsed_time_ms": 10.0,
                "avg_cpu_time_ms": 9.0,
            },
            {
                "signature": "def456",
                "representative_sql": "INSERT INTO orders VALUES (?, ?, ?)",
                "query_type": "INSERT",
                "complexity": {
                    "table_count": 1,
                    "join_count": 0,
                    "where_conditions": 0,
                    "subquery_count": 0,
                    "function_count": 0,
                },
                "query_count": 1,
                "sql_ids": ["q4"],
                "total_executions": 2000,
                "total_elapsed_time_ms": 100000.0,
                "total_cpu_time_ms": 90000.0,
                "total_disk_reads": 20000,
                "total_buffer_gets": 100000,
                "total_rows_processed": 2000,
                "avg_elapsed_time_ms": 50.0,
                "avg_cpu_time_ms": 45.0,
            },
        ],
        "total_queries": 4,
        "total_executions": 2450,
        "unique_patterns": 2,
        "compression_ratio": 2.0,
    }


@pytest.fixture
def complex_workload():
    """Provide workload with complex queries."""
    return {
        "groups": [
            {
                "signature": "complex1",
                "representative_sql": """
                    SELECT u.id, COUNT(o.id)
                    FROM users u
                    JOIN orders o ON u.id = o.user_id
                    WHERE u.age > ?
                    GROUP BY u.id
                """,
                "query_type": "SELECT",
                "complexity": {
                    "table_count": 2,
                    "join_count": 1,
                    "where_conditions": 1,
                    "subquery_count": 0,
                    "function_count": 1,
                },
                "query_count": 5,
                "sql_ids": ["c1", "c2", "c3", "c4", "c5"],
                "total_executions": 1000,
                "total_elapsed_time_ms": 500000.0,
                "total_cpu_time_ms": 450000.0,
                "total_disk_reads": 100000,
                "total_buffer_gets": 500000,
                "total_rows_processed": 50000,
                "avg_elapsed_time_ms": 500.0,
                "avg_cpu_time_ms": 450.0,
            }
        ],
        "total_queries": 5,
        "total_executions": 1000,
        "unique_patterns": 1,
        "compression_ratio": 5.0,
    }


@pytest.fixture
def empty_workload():
    """Provide empty workload data."""
    return {
        "groups": [],
        "total_queries": 0,
        "total_executions": 0,
        "unique_patterns": 0,
        "compression_ratio": 0.0,
    }


class TestFeatureEngineerInitialization:
    """Test FeatureEngineer initialization."""

    @pytest.mark.unit
    def test_engineer_initialization(self):
        """Test that FeatureEngineer can be initialized."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        assert engineer is not None


class TestFeatureExtraction:
    """Test feature extraction from compressed workload."""

    @pytest.mark.unit
    def test_extract_features_returns_dict(self, sample_compressed_workload):
        """Test that extract_features returns a dictionary."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_extract_features_empty_workload(self, empty_workload):
        """Test feature extraction from empty workload."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(empty_workload)

        assert result is not None
        assert result["total_patterns"] == 0

    @pytest.mark.unit
    def test_extract_features_none_input(self):
        """Test that None input raises ValueError."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()

        with pytest.raises(ValueError, match="Workload data cannot be None"):
            engineer.extract_features(None)


class TestWorkloadSummaryFeatures:
    """Test extraction of workload summary features."""

    @pytest.mark.unit
    def test_summary_has_total_patterns(self, sample_compressed_workload):
        """Test that summary includes total patterns count."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        assert "total_patterns" in result
        assert result["total_patterns"] == 2

    @pytest.mark.unit
    def test_summary_has_total_executions(self, sample_compressed_workload):
        """Test that summary includes total executions."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        assert "total_executions" in result
        assert result["total_executions"] == 2450

    @pytest.mark.unit
    def test_summary_has_compression_ratio(self, sample_compressed_workload):
        """Test that summary includes compression ratio."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        assert "compression_ratio" in result
        assert result["compression_ratio"] == 2.0


class TestQueryTypeDistribution:
    """Test query type distribution features."""

    @pytest.mark.unit
    def test_query_type_distribution_exists(self, sample_compressed_workload):
        """Test that query type distribution is included."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        assert "query_type_distribution" in result
        assert isinstance(result["query_type_distribution"], dict)

    @pytest.mark.unit
    def test_query_type_distribution_counts(self, sample_compressed_workload):
        """Test query type distribution counts."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        dist = result["query_type_distribution"]
        assert "SELECT" in dist
        assert "INSERT" in dist
        assert dist["SELECT"] == 1  # 1 pattern
        assert dist["INSERT"] == 1  # 1 pattern

    @pytest.mark.unit
    def test_query_type_by_executions(self, sample_compressed_workload):
        """Test query type distribution by execution count."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        assert "query_type_by_executions" in result
        dist = result["query_type_by_executions"]
        assert dist["SELECT"] == 450  # Total executions for SELECT
        assert dist["INSERT"] == 2000  # Total executions for INSERT


class TestPerformanceMetrics:
    """Test performance metric features."""

    @pytest.mark.unit
    def test_performance_metrics_exist(self, sample_compressed_workload):
        """Test that performance metrics are included."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        assert "performance_metrics" in result
        assert isinstance(result["performance_metrics"], dict)

    @pytest.mark.unit
    def test_avg_elapsed_time_per_execution(self, sample_compressed_workload):
        """Test average elapsed time calculation."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        metrics = result["performance_metrics"]
        assert "avg_elapsed_time_ms" in metrics
        # Total: 4500 + 100000 = 104500, Executions: 2450
        expected = 104500.0 / 2450
        assert metrics["avg_elapsed_time_ms"] == pytest.approx(expected, rel=0.01)

    @pytest.mark.unit
    def test_avg_cpu_time_per_execution(self, sample_compressed_workload):
        """Test average CPU time calculation."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        metrics = result["performance_metrics"]
        assert "avg_cpu_time_ms" in metrics
        # Total: 4050 + 90000 = 94050, Executions: 2450
        expected = 94050.0 / 2450
        assert metrics["avg_cpu_time_ms"] == pytest.approx(expected, rel=0.01)

    @pytest.mark.unit
    def test_total_disk_reads(self, sample_compressed_workload):
        """Test total disk reads calculation."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        metrics = result["performance_metrics"]
        assert "total_disk_reads" in metrics
        assert metrics["total_disk_reads"] == 450 + 20000

    @pytest.mark.unit
    def test_total_buffer_gets(self, sample_compressed_workload):
        """Test total buffer gets calculation."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        metrics = result["performance_metrics"]
        assert "total_buffer_gets" in metrics
        assert metrics["total_buffer_gets"] == 2250 + 100000


class TestComplexityMetrics:
    """Test query complexity metric features."""

    @pytest.mark.unit
    def test_complexity_metrics_exist(self, sample_compressed_workload):
        """Test that complexity metrics are included."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        assert "complexity_metrics" in result
        assert isinstance(result["complexity_metrics"], dict)

    @pytest.mark.unit
    def test_avg_tables_per_query(self, sample_compressed_workload):
        """Test average tables per query calculation."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        metrics = result["complexity_metrics"]
        assert "avg_tables_per_query" in metrics
        # Both queries have 1 table
        assert metrics["avg_tables_per_query"] == 1.0

    @pytest.mark.unit
    def test_avg_joins_per_query(self, sample_compressed_workload):
        """Test average joins per query calculation."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        metrics = result["complexity_metrics"]
        assert "avg_joins_per_query" in metrics
        # Both queries have 0 joins
        assert metrics["avg_joins_per_query"] == 0.0

    @pytest.mark.unit
    def test_complex_query_metrics(self, complex_workload):
        """Test complexity metrics for complex queries."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(complex_workload)

        metrics = result["complexity_metrics"]
        assert metrics["avg_tables_per_query"] == 2.0
        assert metrics["avg_joins_per_query"] == 1.0
        assert metrics["avg_functions_per_query"] == 1.0


class TestTopQueries:
    """Test extraction of top query patterns."""

    @pytest.mark.unit
    def test_top_queries_exist(self, sample_compressed_workload):
        """Test that top queries are included."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        assert "top_queries_by_executions" in result
        assert isinstance(result["top_queries_by_executions"], list)

    @pytest.mark.unit
    def test_top_queries_ordered_by_executions(self, sample_compressed_workload):
        """Test that top queries are ordered by execution count."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        top_queries = result["top_queries_by_executions"]
        assert len(top_queries) == 2

        # First should be INSERT with 2000 executions
        assert top_queries[0]["query_type"] == "INSERT"
        assert top_queries[0]["total_executions"] == 2000

        # Second should be SELECT with 450 executions
        assert top_queries[1]["query_type"] == "SELECT"
        assert top_queries[1]["total_executions"] == 450

    @pytest.mark.unit
    def test_top_queries_limit(self, sample_compressed_workload):
        """Test that top queries can be limited."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload, top_n=1)

        top_queries = result["top_queries_by_executions"]
        assert len(top_queries) == 1
        assert top_queries[0]["query_type"] == "INSERT"

    @pytest.mark.unit
    def test_top_queries_by_elapsed_time(self, sample_compressed_workload):
        """Test top queries by total elapsed time."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        assert "top_queries_by_elapsed_time" in result
        top_queries = result["top_queries_by_elapsed_time"]

        # First should be INSERT with 100000ms
        assert top_queries[0]["query_type"] == "INSERT"
        assert top_queries[0]["total_elapsed_time_ms"] == 100000.0


class TestIOMetrics:
    """Test I/O metric features."""

    @pytest.mark.unit
    def test_io_metrics_exist(self, sample_compressed_workload):
        """Test that I/O metrics are included."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        assert "io_metrics" in result
        assert isinstance(result["io_metrics"], dict)

    @pytest.mark.unit
    def test_avg_disk_reads_per_execution(self, sample_compressed_workload):
        """Test average disk reads per execution."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        metrics = result["io_metrics"]
        assert "avg_disk_reads_per_execution" in metrics
        # Total: 450 + 20000 = 20450, Executions: 2450
        expected = 20450 / 2450
        assert metrics["avg_disk_reads_per_execution"] == pytest.approx(expected, rel=0.01)

    @pytest.mark.unit
    def test_avg_buffer_gets_per_execution(self, sample_compressed_workload):
        """Test average buffer gets per execution."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        metrics = result["io_metrics"]
        assert "avg_buffer_gets_per_execution" in metrics
        # Total: 2250 + 100000 = 102250, Executions: 2450
        expected = 102250 / 2450
        assert metrics["avg_buffer_gets_per_execution"] == pytest.approx(expected, rel=0.01)

    @pytest.mark.unit
    def test_buffer_hit_ratio(self, sample_compressed_workload):
        """Test buffer cache hit ratio calculation."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        metrics = result["io_metrics"]
        assert "buffer_hit_ratio" in metrics
        # Ratio = (buffer_gets - disk_reads) / buffer_gets
        # (102250 - 20450) / 102250
        expected = (102250 - 20450) / 102250
        assert metrics["buffer_hit_ratio"] == pytest.approx(expected, rel=0.01)


class TestFeatureSummaryForLLM:
    """Test feature summary generation for LLM."""

    @pytest.mark.unit
    def test_generate_summary_exists(self, sample_compressed_workload):
        """Test that summary generation method exists."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        assert "summary" in result
        assert isinstance(result["summary"], str)

    @pytest.mark.unit
    def test_summary_contains_key_metrics(self, sample_compressed_workload):
        """Test that summary contains key metrics."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        summary = result["summary"]
        assert "patterns" in summary.lower()
        assert "executions" in summary.lower()
        assert "2450" in summary  # Total executions

    @pytest.mark.unit
    def test_summary_mentions_query_types(self, sample_compressed_workload):
        """Test that summary mentions query types."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        result = engineer.extract_features(sample_compressed_workload)

        summary = result["summary"]
        assert "SELECT" in summary or "select" in summary.lower()
        assert "INSERT" in summary or "insert" in summary.lower()


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.unit
    def test_empty_groups_list(self):
        """Test handling of empty groups list."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        workload = {
            "groups": [],
            "total_queries": 0,
            "total_executions": 0,
            "unique_patterns": 0,
            "compression_ratio": 0.0,
        }

        result = engineer.extract_features(workload)
        assert result["total_patterns"] == 0
        assert result["performance_metrics"]["avg_elapsed_time_ms"] == 0.0

    @pytest.mark.unit
    def test_missing_optional_fields(self):
        """Test handling of missing optional fields in groups."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        workload = {
            "groups": [
                {
                    "signature": "test",
                    "representative_sql": "SELECT 1",
                    "query_type": "SELECT",
                    "complexity": {"table_count": 0},
                    "query_count": 1,
                    "sql_ids": ["q1"],
                    "total_executions": 100,
                    # Missing some optional fields
                }
            ],
            "total_queries": 1,
            "total_executions": 100,
            "unique_patterns": 1,
            "compression_ratio": 1.0,
        }

        result = engineer.extract_features(workload)
        assert result is not None
        assert result["total_patterns"] == 1

    @pytest.mark.unit
    def test_zero_executions_no_division_error(self):
        """Test that zero executions doesn't cause division by zero."""
        from src.data.feature_engineer import FeatureEngineer

        engineer = FeatureEngineer()
        workload = {
            "groups": [
                {
                    "signature": "test",
                    "representative_sql": "SELECT 1",
                    "query_type": "SELECT",
                    "complexity": {"table_count": 1},
                    "query_count": 1,
                    "sql_ids": ["q1"],
                    "total_executions": 0,
                    "total_elapsed_time_ms": 0.0,
                    "total_cpu_time_ms": 0.0,
                    "total_disk_reads": 0,
                    "total_buffer_gets": 0,
                    "total_rows_processed": 0,
                    "avg_elapsed_time_ms": 0.0,
                    "avg_cpu_time_ms": 0.0,
                }
            ],
            "total_queries": 1,
            "total_executions": 0,
            "unique_patterns": 1,
            "compression_ratio": 1.0,
        }

        result = engineer.extract_features(workload)
        assert result["performance_metrics"]["avg_elapsed_time_ms"] == 0.0
