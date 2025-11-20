"""Unit tests for AWR data collector.

This module tests the AWRCollector class which retrieves performance data
from Oracle Automatic Workload Repository (AWR).
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock

import pytest


# Test data fixtures
@pytest.fixture
def mock_connection():
    """Provide a mock Oracle database connection."""
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = Mock(return_value=MagicMock())
    conn.cursor.return_value.__exit__ = Mock(return_value=False)
    return conn


@pytest.fixture
def sample_snapshot_data():
    """Provide sample AWR snapshot data."""
    return {
        "snap_id": 12345,
        "dbid": 1234567890,
        "instance_number": 1,
        "begin_time": datetime(2025, 11, 20, 10, 0, 0),
        "end_time": datetime(2025, 11, 20, 10, 15, 0),
        "startup_time": datetime(2025, 11, 1, 0, 0, 0),
    }


@pytest.fixture
def sample_sql_stats():
    """Provide sample SQL statistics data."""
    return [
        {
            "sql_id": "abc123xyz",
            "plan_hash_value": 1234567890,
            "executions": 1000,
            "elapsed_time_total": 50000000,  # microseconds
            "cpu_time_total": 45000000,
            "disk_reads": 10000,
            "buffer_gets": 50000,
            "rows_processed": 100000,
            "sql_text": "SELECT * FROM users WHERE age > :age",
        },
        {
            "sql_id": "def456uvw",
            "plan_hash_value": 9876543210,
            "executions": 500,
            "elapsed_time_total": 25000000,
            "cpu_time_total": 20000000,
            "disk_reads": 5000,
            "buffer_gets": 25000,
            "rows_processed": 50000,
            "sql_text": "INSERT INTO orders VALUES (:1, :2, :3)",
        },
    ]


@pytest.fixture
def sample_execution_plan():
    """Provide sample execution plan data."""
    return [
        {
            "plan_hash_value": 1234567890,
            "id": 0,
            "operation": "SELECT STATEMENT",
            "options": None,
            "object_name": None,
            "cost": 100,
            "cardinality": 1000,
        },
        {
            "plan_hash_value": 1234567890,
            "id": 1,
            "operation": "TABLE ACCESS",
            "options": "FULL",
            "object_name": "USERS",
            "cost": 100,
            "cardinality": 1000,
        },
    ]


class TestAWRCollectorInitialization:
    """Test AWRCollector initialization and connection handling."""

    @pytest.mark.unit
    def test_collector_requires_connection(self):
        """Test that AWRCollector raises ValueError if connection is None."""
        from src.data.awr_collector import AWRCollector

        with pytest.raises(ValueError, match="Database connection required"):
            AWRCollector(None)

    @pytest.mark.unit
    def test_collector_initialization_with_valid_connection(self, mock_connection):
        """Test AWRCollector initialization with valid connection."""
        from src.data.awr_collector import AWRCollector

        collector = AWRCollector(mock_connection)

        assert collector is not None
        assert collector.connection == mock_connection

    @pytest.mark.unit
    def test_collector_validates_awr_access_on_init(self, mock_connection):
        """Test AWRCollector validates AWR view access during initialization."""
        from src.data.awr_collector import AWRCollector

        cursor_mock = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = cursor_mock

        AWRCollector(mock_connection)

        # Should have executed validation query
        cursor_mock.execute.assert_called()
        call_args = cursor_mock.execute.call_args[0][0]
        assert "DBA_HIST_SNAPSHOT" in call_args.upper()

    @pytest.mark.unit
    def test_collector_raises_if_no_awr_access(self, mock_connection):
        """Test AWRCollector raises RuntimeError if AWR views not accessible."""
        from src.data.awr_collector import AWRCollector

        cursor_mock = MagicMock()
        cursor_mock.execute.side_effect = Exception("ORA-00942: table or view does not exist")
        mock_connection.cursor.return_value.__enter__.return_value = cursor_mock

        with pytest.raises(RuntimeError, match="Cannot access AWR views"):
            AWRCollector(mock_connection)


class TestAWRSnapshotRetrieval:
    """Test AWR snapshot data retrieval."""

    @pytest.mark.unit
    def test_get_latest_snapshot_id(self, mock_connection):
        """Should retrieve the most recent AWR snapshot ID."""
        from src.data.awr_collector import AWRCollector

        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = (12345,)
        mock_connection.cursor.return_value.__enter__.return_value = cursor_mock

        collector = AWRCollector(mock_connection)
        snapshot_id = collector.get_latest_snapshot_id()

        assert isinstance(snapshot_id, int)
        assert snapshot_id == 12345

    @pytest.mark.unit
    def test_get_latest_snapshot_id_raises_if_no_snapshots(self, mock_connection):
        """Should raise RuntimeError if no AWR snapshots exist."""
        from src.data.awr_collector import AWRCollector

        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = None
        mock_connection.cursor.return_value.__enter__.return_value = cursor_mock

        collector = AWRCollector(mock_connection)

        with pytest.raises(RuntimeError, match="No AWR snapshots found"):
            collector.get_latest_snapshot_id()

    @pytest.mark.unit
    def test_get_snapshot_range(self, mock_connection, sample_snapshot_data):
        """Should retrieve snapshot IDs within a time range."""
        from src.data.awr_collector import AWRCollector

        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = [
            (12345, sample_snapshot_data["begin_time"]),
            (12346, sample_snapshot_data["begin_time"] + timedelta(minutes=15)),
            (12347, sample_snapshot_data["begin_time"] + timedelta(minutes=30)),
        ]
        mock_connection.cursor.return_value.__enter__.return_value = cursor_mock

        collector = AWRCollector(mock_connection)
        start_time = sample_snapshot_data["begin_time"]
        end_time = start_time + timedelta(hours=1)

        snapshots = collector.get_snapshot_range(start_time, end_time)

        assert len(snapshots) == 3
        assert snapshots[0]["snap_id"] == 12345
        assert isinstance(snapshots[0]["begin_time"], datetime)

    @pytest.mark.unit
    def test_get_snapshot_info(self, mock_connection, sample_snapshot_data):
        """Should retrieve detailed information for a specific snapshot."""
        from src.data.awr_collector import AWRCollector

        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = (
            sample_snapshot_data["snap_id"],
            sample_snapshot_data["dbid"],
            sample_snapshot_data["instance_number"],
            sample_snapshot_data["begin_time"],
            sample_snapshot_data["end_time"],
            sample_snapshot_data["startup_time"],
        )
        mock_connection.cursor.return_value.__enter__.return_value = cursor_mock

        collector = AWRCollector(mock_connection)
        snapshot_info = collector.get_snapshot_info(12345)

        assert snapshot_info["snap_id"] == 12345
        assert snapshot_info["dbid"] == 1234567890
        assert isinstance(snapshot_info["begin_time"], datetime)


class TestSQLStatisticsCollection:
    """Test SQL statistics collection from AWR."""

    @pytest.mark.unit
    def test_get_sql_statistics(self, mock_connection, sample_sql_stats):
        """Should retrieve SQL statistics for a snapshot range."""
        from src.data.awr_collector import AWRCollector

        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = [
            (
                stat["sql_id"],
                stat["plan_hash_value"],
                stat["executions"],
                stat["elapsed_time_total"],
                stat["cpu_time_total"],
                stat["disk_reads"],
                stat["buffer_gets"],
                stat["rows_processed"],
            )
            for stat in sample_sql_stats
        ]
        mock_connection.cursor.return_value.__enter__.return_value = cursor_mock

        collector = AWRCollector(mock_connection)
        sql_stats = collector.get_sql_statistics(begin_snap=12345, end_snap=12346)

        assert len(sql_stats) == 2
        assert sql_stats[0]["sql_id"] == "abc123xyz"
        assert sql_stats[0]["executions"] == 1000
        assert sql_stats[0]["elapsed_time_ms"] == 50000.0  # Converted to ms

    @pytest.mark.unit
    def test_get_sql_statistics_calculates_averages(self, mock_connection, sample_sql_stats):
        """Should calculate average execution times per SQL."""
        from src.data.awr_collector import AWRCollector

        cursor_mock = MagicMock()
        stat = sample_sql_stats[0]
        cursor_mock.fetchall.return_value = [
            (
                stat["sql_id"],
                stat["plan_hash_value"],
                stat["executions"],
                stat["elapsed_time_total"],
                stat["cpu_time_total"],
                stat["disk_reads"],
                stat["buffer_gets"],
                stat["rows_processed"],
            )
        ]
        mock_connection.cursor.return_value.__enter__.return_value = cursor_mock

        collector = AWRCollector(mock_connection)
        sql_stats = collector.get_sql_statistics(begin_snap=12345, end_snap=12346)

        expected_avg_elapsed = stat["elapsed_time_total"] / stat["executions"] / 1000  # ms
        assert sql_stats[0]["avg_elapsed_time_ms"] == pytest.approx(expected_avg_elapsed, rel=0.01)

    @pytest.mark.unit
    def test_get_sql_text(self, mock_connection, sample_sql_stats):
        """Should retrieve SQL text for a given SQL ID."""
        from src.data.awr_collector import AWRCollector

        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = (sample_sql_stats[0]["sql_text"],)
        mock_connection.cursor.return_value.__enter__.return_value = cursor_mock

        collector = AWRCollector(mock_connection)
        sql_text = collector.get_sql_text("abc123xyz")

        assert sql_text == sample_sql_stats[0]["sql_text"]
        assert "SELECT" in sql_text

    @pytest.mark.unit
    def test_get_sql_text_returns_none_if_not_found(self, mock_connection):
        """Should return None if SQL text not found."""
        from src.data.awr_collector import AWRCollector

        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = None
        mock_connection.cursor.return_value.__enter__.return_value = cursor_mock

        collector = AWRCollector(mock_connection)
        sql_text = collector.get_sql_text("nonexistent")

        assert sql_text is None


class TestExecutionPlanRetrieval:
    """Test execution plan retrieval from AWR."""

    @pytest.mark.unit
    def test_get_execution_plan(self, mock_connection, sample_execution_plan):
        """Should retrieve execution plan for SQL ID and plan hash."""
        from src.data.awr_collector import AWRCollector

        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = [
            (
                plan["plan_hash_value"],
                plan["id"],
                plan["operation"],
                plan["options"],
                plan["object_name"],
                plan["cost"],
                plan["cardinality"],
            )
            for plan in sample_execution_plan
        ]
        mock_connection.cursor.return_value.__enter__.return_value = cursor_mock

        collector = AWRCollector(mock_connection)
        plan = collector.get_execution_plan(sql_id="abc123xyz", plan_hash_value=1234567890)

        assert len(plan) == 2
        assert plan[0]["operation"] == "SELECT STATEMENT"
        assert plan[1]["operation"] == "TABLE ACCESS"
        assert plan[1]["options"] == "FULL"

    @pytest.mark.unit
    def test_get_execution_plan_returns_empty_if_not_found(self, mock_connection):
        """Should return empty list if execution plan not found."""
        from src.data.awr_collector import AWRCollector

        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = []
        mock_connection.cursor.return_value.__enter__.return_value = cursor_mock

        collector = AWRCollector(mock_connection)
        plan = collector.get_execution_plan(sql_id="nonexistent", plan_hash_value=0)

        assert plan == []


class TestAWRCollectorErrorHandling:
    """Test error handling in AWRCollector."""

    @pytest.mark.unit
    def test_handles_database_connection_error(self, mock_connection):
        """Should handle database connection errors gracefully."""
        from src.data.awr_collector import AWRCollector

        cursor_mock = MagicMock()
        cursor_mock.execute.side_effect = Exception("ORA-03114: not connected to ORACLE")
        mock_connection.cursor.return_value.__enter__.return_value = cursor_mock

        with pytest.raises(RuntimeError):
            AWRCollector(mock_connection)

    @pytest.mark.unit
    def test_handles_query_timeout(self, mock_connection):
        """Should handle query timeout errors."""
        from src.data.awr_collector import AWRCollector

        cursor_mock = MagicMock()
        # First call for validation succeeds
        cursor_mock.execute.side_effect = [
            None,  # Validation query
            Exception("ORA-01013: user requested cancel of current operation"),
        ]
        mock_connection.cursor.return_value.__enter__.return_value = cursor_mock

        collector = AWRCollector(mock_connection)

        with pytest.raises(RuntimeError, match="Query timeout"):
            collector.get_latest_snapshot_id()

    @pytest.mark.unit
    def test_closes_cursor_on_error(self, mock_connection):
        """Should properly close cursor even when errors occur."""
        from src.data.awr_collector import AWRCollector

        cursor_mock = MagicMock()
        # First call for validation succeeds, second call for get_latest_snapshot_id fails
        cursor_mock.fetchone.side_effect = [(1,), Exception("Database error")]
        mock_connection.cursor.return_value.__enter__.return_value = cursor_mock

        collector = AWRCollector(mock_connection)

        with pytest.raises(Exception, match="Database error"):
            collector.get_latest_snapshot_id()

        # Context manager should have handled cursor cleanup
        assert cursor_mock.fetchone.call_count == 2
