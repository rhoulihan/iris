"""Unit tests for schema metadata collector.

This module tests the SchemaCollector class which retrieves Oracle database
schema metadata including tables, indexes, constraints, and statistics.
"""

from unittest.mock import MagicMock

import pytest


# Test data fixtures
@pytest.fixture
def mock_connection():
    """Provide a mock database connection."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn


@pytest.fixture
def sample_table_metadata():
    """Provide sample table metadata."""
    return [
        {
            "table_name": "USERS",
            "owner": "APP_SCHEMA",
            "tablespace_name": "USERS_TS",
            "num_rows": 100000,
            "avg_row_len": 150,
            "last_analyzed": "2024-01-15 10:30:00",
        },
        {
            "table_name": "ORDERS",
            "owner": "APP_SCHEMA",
            "tablespace_name": "ORDERS_TS",
            "num_rows": 500000,
            "avg_row_len": 200,
            "last_analyzed": "2024-01-15 10:35:00",
        },
    ]


@pytest.fixture
def sample_column_metadata():
    """Provide sample column metadata."""
    return [
        {
            "table_name": "USERS",
            "column_name": "USER_ID",
            "data_type": "NUMBER",
            "data_length": 22,
            "nullable": "N",
            "column_id": 1,
            "num_distinct": 100000,
            "num_nulls": 0,
        },
        {
            "table_name": "USERS",
            "column_name": "USERNAME",
            "data_type": "VARCHAR2",
            "data_length": 50,
            "nullable": "N",
            "column_id": 2,
            "num_distinct": 100000,
            "num_nulls": 0,
        },
        {
            "table_name": "USERS",
            "column_name": "EMAIL",
            "data_type": "VARCHAR2",
            "data_length": 100,
            "nullable": "Y",
            "column_id": 3,
            "num_distinct": 95000,
            "num_nulls": 5000,
        },
    ]


@pytest.fixture
def sample_index_metadata():
    """Provide sample index metadata."""
    return [
        {
            "index_name": "USERS_PK",
            "table_name": "USERS",
            "owner": "APP_SCHEMA",
            "index_type": "NORMAL",
            "uniqueness": "UNIQUE",
            "status": "VALID",
            "columns": ["USER_ID"],
        },
        {
            "index_name": "USERS_USERNAME_IDX",
            "table_name": "USERS",
            "owner": "APP_SCHEMA",
            "index_type": "NORMAL",
            "uniqueness": "NONUNIQUE",
            "status": "VALID",
            "columns": ["USERNAME"],
        },
        {
            "index_name": "USERS_EMAIL_IDX",
            "table_name": "USERS",
            "owner": "APP_SCHEMA",
            "index_type": "NORMAL",
            "uniqueness": "NONUNIQUE",
            "status": "VALID",
            "columns": ["EMAIL"],
        },
    ]


@pytest.fixture
def sample_constraint_metadata():
    """Provide sample constraint metadata."""
    return [
        {
            "constraint_name": "USERS_PK",
            "table_name": "USERS",
            "constraint_type": "P",
            "columns": ["USER_ID"],
            "status": "ENABLED",
        },
        {
            "constraint_name": "ORDERS_USER_FK",
            "table_name": "ORDERS",
            "constraint_type": "R",
            "columns": ["USER_ID"],
            "r_table_name": "USERS",
            "r_columns": ["USER_ID"],
            "status": "ENABLED",
        },
        {
            "constraint_name": "USERS_EMAIL_UK",
            "table_name": "USERS",
            "constraint_type": "U",
            "columns": ["EMAIL"],
            "status": "ENABLED",
        },
    ]


class TestSchemaCollectorInitialization:
    """Test SchemaCollector initialization."""

    @pytest.mark.unit
    def test_collector_initialization(self, mock_connection):
        """Test that SchemaCollector can be initialized."""
        from src.data.schema_collector import SchemaCollector

        mock_connection.cursor().fetchone.return_value = (1,)

        collector = SchemaCollector(mock_connection)
        assert collector is not None
        assert collector.connection == mock_connection

    @pytest.mark.unit
    def test_collector_validates_connection(self):
        """Test that SchemaCollector validates connection."""
        from src.data.schema_collector import SchemaCollector

        with pytest.raises(ValueError, match="Database connection required"):
            SchemaCollector(None)

    @pytest.mark.unit
    def test_collector_validates_schema_access(self, mock_connection):
        """Test that collector validates access to schema views."""
        from src.data.schema_collector import SchemaCollector

        # Simulate no access to schema views
        mock_connection.cursor().fetchone.side_effect = Exception("Access denied")

        with pytest.raises(RuntimeError, match="Cannot access schema metadata views"):
            SchemaCollector(mock_connection)


class TestTableMetadataCollection:
    """Test table metadata collection."""

    @pytest.mark.unit
    def test_get_tables_returns_list(self, mock_connection):
        """Test that get_tables returns a list."""
        from src.data.schema_collector import SchemaCollector

        mock_connection.cursor().fetchone.return_value = (1,)
        mock_connection.cursor().fetchall.return_value = []

        collector = SchemaCollector(mock_connection)
        result = collector.get_tables(owner="APP_SCHEMA")

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_get_tables_with_owner(self, mock_connection, sample_table_metadata):
        """Test getting tables for specific owner."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)
        cursor_mock.fetchall.return_value = [tuple(t.values()) for t in sample_table_metadata]
        cursor_mock.description = [(k,) for k in sample_table_metadata[0].keys()]

        collector = SchemaCollector(mock_connection)
        result = collector.get_tables(owner="APP_SCHEMA")

        assert len(result) == 2
        assert result[0]["table_name"] == "USERS"
        assert result[1]["table_name"] == "ORDERS"

    @pytest.mark.unit
    def test_get_tables_includes_statistics(self, mock_connection, sample_table_metadata):
        """Test that table metadata includes statistics."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)
        cursor_mock.fetchall.return_value = [tuple(sample_table_metadata[0].values())]
        cursor_mock.description = [(k,) for k in sample_table_metadata[0].keys()]

        collector = SchemaCollector(mock_connection)
        result = collector.get_tables(owner="APP_SCHEMA")

        table = result[0]
        assert "num_rows" in table
        assert "avg_row_len" in table
        assert table["num_rows"] == 100000

    @pytest.mark.unit
    def test_get_tables_filters_by_owner(self, mock_connection):
        """Test that owner parameter is used in query."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)
        cursor_mock.fetchall.return_value = []

        collector = SchemaCollector(mock_connection)
        collector.get_tables(owner="APP_SCHEMA")

        # Verify execute was called with owner parameter
        execute_calls = cursor_mock.execute.call_args_list
        assert len(execute_calls) >= 1
        # The last call should be the get_tables query with owner
        last_call = execute_calls[-1]
        assert "APP_SCHEMA" in str(last_call) or any(
            "APP_SCHEMA" in str(arg) for arg in last_call[0]
        )


class TestColumnMetadataCollection:
    """Test column metadata collection."""

    @pytest.mark.unit
    def test_get_columns_returns_list(self, mock_connection):
        """Test that get_columns returns a list."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)
        cursor_mock.fetchall.return_value = []

        collector = SchemaCollector(mock_connection)
        result = collector.get_columns(owner="APP_SCHEMA", table_name="USERS")

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_get_columns_for_table(self, mock_connection, sample_column_metadata):
        """Test getting columns for specific table."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)
        cursor_mock.fetchall.return_value = [tuple(c.values()) for c in sample_column_metadata]
        cursor_mock.description = [(k,) for k in sample_column_metadata[0].keys()]

        collector = SchemaCollector(mock_connection)
        result = collector.get_columns(owner="APP_SCHEMA", table_name="USERS")

        assert len(result) == 3
        assert result[0]["column_name"] == "USER_ID"
        assert result[1]["column_name"] == "USERNAME"
        assert result[2]["column_name"] == "EMAIL"

    @pytest.mark.unit
    def test_get_columns_includes_data_types(self, mock_connection, sample_column_metadata):
        """Test that column metadata includes data types."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)
        cursor_mock.fetchall.return_value = [tuple(sample_column_metadata[0].values())]
        cursor_mock.description = [(k,) for k in sample_column_metadata[0].keys()]

        collector = SchemaCollector(mock_connection)
        result = collector.get_columns(owner="APP_SCHEMA", table_name="USERS")

        column = result[0]
        assert "data_type" in column
        assert "data_length" in column
        assert "nullable" in column
        assert column["data_type"] == "NUMBER"

    @pytest.mark.unit
    def test_get_columns_includes_statistics(self, mock_connection, sample_column_metadata):
        """Test that column metadata includes statistics."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)
        cursor_mock.fetchall.return_value = [tuple(sample_column_metadata[0].values())]
        cursor_mock.description = [(k,) for k in sample_column_metadata[0].keys()]

        collector = SchemaCollector(mock_connection)
        result = collector.get_columns(owner="APP_SCHEMA", table_name="USERS")

        column = result[0]
        assert "num_distinct" in column
        assert "num_nulls" in column


class TestIndexMetadataCollection:
    """Test index metadata collection."""

    @pytest.mark.unit
    def test_get_indexes_returns_list(self, mock_connection):
        """Test that get_indexes returns a list."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)
        cursor_mock.fetchall.return_value = []

        collector = SchemaCollector(mock_connection)
        result = collector.get_indexes(owner="APP_SCHEMA", table_name="USERS")

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_get_indexes_for_table(self, mock_connection, sample_index_metadata):
        """Test getting indexes for specific table."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)

        # Mock index results
        index_rows = [
            ("USERS_PK", "USERS", "APP_SCHEMA", "NORMAL", "UNIQUE", "VALID", "USER_ID", 1),
            (
                "USERS_USERNAME_IDX",
                "USERS",
                "APP_SCHEMA",
                "NORMAL",
                "NONUNIQUE",
                "VALID",
                "USERNAME",
                1,
            ),
            (
                "USERS_EMAIL_IDX",
                "USERS",
                "APP_SCHEMA",
                "NORMAL",
                "NONUNIQUE",
                "VALID",
                "EMAIL",
                1,
            ),
        ]
        cursor_mock.fetchall.return_value = index_rows

        collector = SchemaCollector(mock_connection)
        result = collector.get_indexes(owner="APP_SCHEMA", table_name="USERS")

        assert len(result) == 3
        assert result[0]["index_name"] == "USERS_PK"
        assert result[1]["index_name"] == "USERS_USERNAME_IDX"
        assert result[2]["index_name"] == "USERS_EMAIL_IDX"

    @pytest.mark.unit
    def test_get_indexes_includes_columns(self, mock_connection):
        """Test that index metadata includes column information."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)

        # Mock multi-column index
        index_rows = [
            (
                "USERS_COMPOSITE_IDX",
                "USERS",
                "APP_SCHEMA",
                "NORMAL",
                "NONUNIQUE",
                "VALID",
                "USERNAME",
                1,
            ),
            (
                "USERS_COMPOSITE_IDX",
                "USERS",
                "APP_SCHEMA",
                "NORMAL",
                "NONUNIQUE",
                "VALID",
                "EMAIL",
                2,
            ),
        ]
        cursor_mock.fetchall.return_value = index_rows

        collector = SchemaCollector(mock_connection)
        result = collector.get_indexes(owner="APP_SCHEMA", table_name="USERS")

        # Should consolidate multi-column index into one entry
        assert len(result) == 1
        assert result[0]["index_name"] == "USERS_COMPOSITE_IDX"
        assert "columns" in result[0]
        assert result[0]["columns"] == ["USERNAME", "EMAIL"]

    @pytest.mark.unit
    def test_get_indexes_shows_uniqueness(self, mock_connection):
        """Test that index metadata indicates uniqueness."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)

        index_rows = [
            ("USERS_PK", "USERS", "APP_SCHEMA", "NORMAL", "UNIQUE", "VALID", "USER_ID", 1),
        ]
        cursor_mock.fetchall.return_value = index_rows

        collector = SchemaCollector(mock_connection)
        result = collector.get_indexes(owner="APP_SCHEMA", table_name="USERS")

        assert result[0]["uniqueness"] == "UNIQUE"


class TestConstraintMetadataCollection:
    """Test constraint metadata collection."""

    @pytest.mark.unit
    def test_get_constraints_returns_list(self, mock_connection):
        """Test that get_constraints returns a list."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)
        cursor_mock.fetchall.return_value = []

        collector = SchemaCollector(mock_connection)
        result = collector.get_constraints(owner="APP_SCHEMA", table_name="USERS")

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_get_constraints_for_table(self, mock_connection):
        """Test getting constraints for specific table."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)

        constraint_rows = [
            ("USERS_PK", "USERS", "P", "ENABLED", "USER_ID", 1, None, None),
            ("USERS_EMAIL_UK", "USERS", "U", "ENABLED", "EMAIL", 1, None, None),
        ]
        cursor_mock.fetchall.return_value = constraint_rows

        collector = SchemaCollector(mock_connection)
        result = collector.get_constraints(owner="APP_SCHEMA", table_name="USERS")

        assert len(result) == 2
        assert result[0]["constraint_name"] == "USERS_PK"
        assert result[1]["constraint_name"] == "USERS_EMAIL_UK"

    @pytest.mark.unit
    def test_get_constraints_distinguishes_types(self, mock_connection):
        """Test that constraints are typed correctly."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)

        constraint_rows = [
            ("USERS_PK", "USERS", "P", "ENABLED", "USER_ID", 1, None, None),
            ("USERS_EMAIL_UK", "USERS", "U", "ENABLED", "EMAIL", 1, None, None),
            ("ORDERS_USER_FK", "ORDERS", "R", "ENABLED", "USER_ID", 1, "USERS", "USER_ID"),
        ]
        cursor_mock.fetchall.return_value = constraint_rows

        collector = SchemaCollector(mock_connection)
        result = collector.get_constraints(owner="APP_SCHEMA")

        types = {c["constraint_type"] for c in result}
        assert "P" in types  # Primary key
        assert "U" in types  # Unique
        assert "R" in types  # Foreign key

    @pytest.mark.unit
    def test_get_constraints_includes_foreign_key_refs(self, mock_connection):
        """Test that foreign key constraints include reference information."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)

        constraint_rows = [
            ("ORDERS_USER_FK", "ORDERS", "R", "ENABLED", "USER_ID", 1, "USERS", "USER_ID"),
        ]
        cursor_mock.fetchall.return_value = constraint_rows

        collector = SchemaCollector(mock_connection)
        result = collector.get_constraints(owner="APP_SCHEMA", table_name="ORDERS")

        fk = result[0]
        assert fk["constraint_type"] == "R"
        assert "r_table_name" in fk
        assert fk["r_table_name"] == "USERS"


class TestSchemaMetadataIntegration:
    """Test complete schema metadata retrieval."""

    @pytest.mark.unit
    def test_get_schema_metadata_complete(self, mock_connection):
        """Test getting complete schema metadata."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)
        cursor_mock.fetchall.return_value = []

        collector = SchemaCollector(mock_connection)
        result = collector.get_schema_metadata(owner="APP_SCHEMA")

        assert result is not None
        assert "tables" in result
        assert "indexes" in result
        assert "constraints" in result

    @pytest.mark.unit
    def test_get_schema_metadata_for_specific_table(self, mock_connection):
        """Test getting schema metadata for specific table."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)
        cursor_mock.fetchall.return_value = []

        collector = SchemaCollector(mock_connection)
        result = collector.get_schema_metadata(owner="APP_SCHEMA", table_name="USERS")

        assert result is not None
        assert "tables" in result
        assert "columns" in result
        assert "indexes" in result
        assert "constraints" in result


class TestErrorHandling:
    """Test error handling in schema collection."""

    @pytest.mark.unit
    def test_handles_database_errors(self, mock_connection):
        """Test handling of database errors during collection."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)
        cursor_mock.fetchall.side_effect = Exception("Database error")

        collector = SchemaCollector(mock_connection)

        with pytest.raises(RuntimeError, match="Failed to retrieve"):
            collector.get_tables(owner="APP_SCHEMA")

    @pytest.mark.unit
    def test_handles_empty_results(self, mock_connection):
        """Test handling of empty result sets."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)
        cursor_mock.fetchall.return_value = []

        collector = SchemaCollector(mock_connection)
        result = collector.get_tables(owner="NONEXISTENT")

        assert result == []

    @pytest.mark.unit
    def test_handles_missing_statistics(self, mock_connection):
        """Test handling of tables without statistics."""
        from src.data.schema_collector import SchemaCollector

        cursor_mock = mock_connection.cursor()
        cursor_mock.fetchone.return_value = (1,)

        # Table without statistics (NULLs for num_rows, etc.)
        table_row = [("USERS", "APP_SCHEMA", "USERS_TS", None, None, None)]
        cursor_mock.fetchall.return_value = table_row
        cursor_mock.description = [
            ("table_name",),
            ("owner",),
            ("tablespace_name",),
            ("num_rows",),
            ("avg_row_len",),
            ("last_analyzed",),
        ]

        collector = SchemaCollector(mock_connection)
        result = collector.get_tables(owner="APP_SCHEMA")

        assert len(result) == 1
        assert result[0]["table_name"] == "USERS"
