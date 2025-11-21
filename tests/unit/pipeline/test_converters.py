"""Unit tests for data model converters.

This module tests conversion utilities that transform Dict results from
data collectors into typed data models.
"""

import pytest

from src.pipeline.converters import ConversionError, dict_to_query_pattern, dict_to_table_metadata
from src.recommendation.models import QueryPattern, TableMetadata


class TestQueryPatternConversion:
    """Test Dict → QueryPattern conversion."""

    def test_convert_complete_query_dict(self):
        """Should convert complete query dict to QueryPattern."""
        query_dict = {
            "query_id": "abc123",
            "sql_text": "SELECT * FROM users WHERE id = :1",
            "query_type": "SELECT",
            "executions": 100,
            "avg_elapsed_time_ms": 5.2,
            "tables": ["users"],
            "join_count": 0,
            "normalized": "SELECT * FROM users WHERE id = ?",
            "joins": [],
        }

        result = dict_to_query_pattern(query_dict)

        assert isinstance(result, QueryPattern)
        assert result.query_id == "abc123"
        assert result.sql_text == "SELECT * FROM users WHERE id = :1"
        assert result.query_type == "SELECT"
        assert result.executions == 100
        assert result.avg_elapsed_time_ms == 5.2
        assert result.tables == ["users"]
        assert result.join_count == 0

    def test_convert_with_defaults(self):
        """Should use default values for optional fields."""
        query_dict = {
            "query_type": "INSERT",
            "tables": ["orders"],
        }

        result = dict_to_query_pattern(query_dict)

        assert result.query_type == "INSERT"
        assert result.tables == ["orders"]
        assert result.executions == 1  # Default
        assert result.avg_elapsed_time_ms == 0.0  # Default
        assert result.join_count == 0  # Default

    def test_convert_missing_required_fields_raises_error(self):
        """Should raise ConversionError if required fields missing."""
        query_dict = {
            "query_id": "abc123",
            # Missing query_type and tables
        }

        with pytest.raises(ConversionError, match="Missing required field"):
            dict_to_query_pattern(query_dict)

    def test_convert_with_joins(self):
        """Should convert query with join information."""
        query_dict = {
            "query_type": "SELECT",
            "tables": ["orders", "customers"],
            "join_count": 1,
            "joins": [
                {
                    "left_table": "orders",
                    "right_table": "customers",
                    "columns_fetched": ["customer_name"],
                    "join_type": "INNER",
                }
            ],
        }

        result = dict_to_query_pattern(query_dict)

        assert result.join_count == 1
        assert len(result.joins) == 1
        assert result.joins[0].left_table == "orders"
        assert result.joins[0].right_table == "customers"

    def test_convert_invalid_executions_type(self):
        """Should raise ConversionError for invalid data types."""
        query_dict = {
            "query_type": "SELECT",
            "tables": ["users"],
            "executions": "not a number",  # Invalid type
        }

        with pytest.raises(ConversionError, match="Invalid type"):
            dict_to_query_pattern(query_dict)


class TestTableMetadataConversion:
    """Test Dict → TableMetadata conversion."""

    def test_convert_complete_table_dict(self):
        """Should convert complete table dict to TableMetadata."""
        table_dict = {
            "table_name": "USERS",
            "owner": "APP",
            "num_rows": 10000,
            "avg_row_len": 250,
            "compression": "ENABLED",
            "columns": [
                {
                    "column_name": "ID",
                    "data_type": "NUMBER",
                    "nullable": "N",
                    "avg_col_len": 8,
                },
                {
                    "column_name": "NAME",
                    "data_type": "VARCHAR2",
                    "nullable": "Y",
                    "avg_col_len": 50,
                },
            ],
        }

        result = dict_to_table_metadata(table_dict)

        assert isinstance(result, TableMetadata)
        assert result.name == "USERS"
        assert result.schema == "APP"
        assert result.num_rows == 10000
        assert result.avg_row_len == 250
        assert result.compression is True
        assert len(result.columns) == 2
        assert result.columns[0].name == "ID"
        assert result.columns[0].data_type == "NUMBER"
        assert result.columns[0].nullable is False

    def test_convert_with_defaults(self):
        """Should use default values for optional fields."""
        table_dict = {
            "table_name": "PRODUCTS",
            "owner": "SALES",
        }

        result = dict_to_table_metadata(table_dict)

        assert result.name == "PRODUCTS"
        assert result.schema == "SALES"
        assert result.num_rows == 0  # Default
        assert result.avg_row_len == 0  # Default
        assert result.compression is False  # Default
        assert result.columns == []  # Default

    def test_convert_missing_required_fields_raises_error(self):
        """Should raise ConversionError if required fields missing."""
        table_dict = {
            "owner": "APP",
            # Missing table_name
        }

        with pytest.raises(ConversionError, match="Missing required field"):
            dict_to_table_metadata(table_dict)

    def test_convert_compression_variations(self):
        """Should handle various compression value formats."""
        # ENABLED
        result1 = dict_to_table_metadata(
            {"table_name": "T1", "owner": "APP", "compression": "ENABLED"}
        )
        assert result1.compression is True

        # DISABLED
        result2 = dict_to_table_metadata(
            {"table_name": "T2", "owner": "APP", "compression": "DISABLED"}
        )
        assert result2.compression is False

        # None
        result3 = dict_to_table_metadata({"table_name": "T3", "owner": "APP", "compression": None})
        assert result3.compression is False

    def test_convert_nullable_variations(self):
        """Should handle Y/N nullable values correctly."""
        table_dict = {
            "table_name": "TEST",
            "owner": "APP",
            "columns": [
                {"column_name": "COL1", "data_type": "NUMBER", "nullable": "N"},
                {"column_name": "COL2", "data_type": "VARCHAR2", "nullable": "Y"},
            ],
        }

        result = dict_to_table_metadata(table_dict)

        assert result.columns[0].nullable is False
        assert result.columns[1].nullable is True

    def test_convert_column_without_avg_size(self):
        """Should handle columns without avg_col_len."""
        table_dict = {
            "table_name": "TEST",
            "owner": "APP",
            "columns": [{"column_name": "ID", "data_type": "NUMBER", "nullable": "N"}],
        }

        result = dict_to_table_metadata(table_dict)

        assert result.columns[0].avg_size is None


class TestConversionErrorHandling:
    """Test error handling in converters."""

    def test_conversion_error_message(self):
        """Should provide clear error messages."""
        try:
            dict_to_query_pattern({})
        except ConversionError as e:
            assert "empty dict" in str(e).lower() or "query_type" in str(e).lower()

    def test_none_input_raises_error(self):
        """Should handle None input gracefully."""
        with pytest.raises(ConversionError, match="Cannot convert None"):
            dict_to_query_pattern(None)

        with pytest.raises(ConversionError, match="Cannot convert None"):
            dict_to_table_metadata(None)

    def test_empty_dict_raises_error(self):
        """Should reject empty dictionaries."""
        with pytest.raises(ConversionError):
            dict_to_query_pattern({})

        with pytest.raises(ConversionError):
            dict_to_table_metadata({})
