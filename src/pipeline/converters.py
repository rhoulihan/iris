"""Data model converters for pipeline components.

This module provides utilities to convert Dict results from data collectors
(AWR, schema_collector, query_parser) into typed data models (QueryPattern,
TableMetadata, etc.).
"""

from typing import Any, Dict, List, Optional

from src.recommendation.models import ColumnMetadata, JoinInfo, QueryPattern, TableMetadata


class ConversionError(Exception):
    """Raised when data conversion fails."""

    pass


def dict_to_query_pattern(
    query_dict: Optional[Dict[str, Any]],
    sql_id: Optional[str] = None,
) -> QueryPattern:
    """Convert dictionary to QueryPattern object.

    Args:
        query_dict: Dictionary with query information (from query_parser.parse())
        sql_id: Optional SQL ID to use as query_id (from AWR data)

    Returns:
        QueryPattern object

    Raises:
        ConversionError: If required fields are missing or invalid

    Example:
        >>> query_dict = {
        ...     "query_type": "SELECT",
        ...     "tables": ["users"],
        ...     "join_count": 0,
        ... }
        >>> pattern = dict_to_query_pattern(query_dict, sql_id="abc123")
        >>> print(pattern.query_id)
        abc123
    """
    if query_dict is None:
        raise ConversionError("Cannot convert None to QueryPattern")

    if not query_dict:
        raise ConversionError("Cannot convert empty dict to QueryPattern")

    # Validate required fields
    required_fields = ["query_type", "tables"]
    for field in required_fields:
        if field not in query_dict:
            raise ConversionError(f"Missing required field: {field}")

    # Extract fields with defaults
    try:
        query_id = sql_id or query_dict.get("query_id", "unknown")
        sql_text = query_dict.get("sql_text", "")
        query_type = query_dict["query_type"]
        tables = query_dict["tables"]

        # Handle executions - should be int
        executions_val = query_dict.get("executions", 1)
        if not isinstance(executions_val, int):
            try:
                executions = int(executions_val)
            except (ValueError, TypeError) as e:
                raise ConversionError(f"Invalid type for executions: {type(executions_val)}") from e
        else:
            executions = executions_val

        # Handle avg_elapsed_time_ms - should be float
        elapsed_val = query_dict.get("avg_elapsed_time_ms", 0.0)
        if isinstance(elapsed_val, (int, float)):
            avg_elapsed_time_ms = float(elapsed_val)
        else:
            raise ConversionError(f"Invalid type for avg_elapsed_time_ms: {type(elapsed_val)}")

        join_count = int(query_dict.get("join_count", 0))
        normalized_sql = query_dict.get("normalized", sql_text)

        # Convert joins if present
        joins: List[JoinInfo] = []
        if "joins" in query_dict and query_dict["joins"]:
            for join_dict in query_dict["joins"]:
                join_info = JoinInfo(
                    left_table=join_dict.get("left_table", ""),
                    right_table=join_dict.get("right_table", ""),
                    columns_fetched=join_dict.get("columns_fetched", []),
                    join_type=join_dict.get("join_type", "INNER"),
                )
                joins.append(join_info)

        return QueryPattern(
            query_id=query_id,
            sql_text=sql_text,
            query_type=query_type,
            executions=executions,
            avg_elapsed_time_ms=avg_elapsed_time_ms,
            tables=tables,
            join_count=join_count,
            normalized_sql=normalized_sql,
            joins=joins,
        )

    except (KeyError, ValueError, TypeError) as e:
        raise ConversionError(f"Failed to convert query dict: {e}") from e


def dict_to_table_metadata(table_dict: Optional[Dict[str, Any]]) -> TableMetadata:
    """Convert dictionary to TableMetadata object.

    Args:
        table_dict: Dictionary with table information (from schema_collector)

    Returns:
        TableMetadata object

    Raises:
        ConversionError: If required fields are missing or invalid

    Example:
        >>> table_dict = {
        ...     "table_name": "USERS",
        ...     "owner": "APP",
        ...     "num_rows": 1000,
        ... }
        >>> metadata = dict_to_table_metadata(table_dict)
        >>> print(metadata.name)
        USERS
    """
    if table_dict is None:
        raise ConversionError("Cannot convert None to TableMetadata")

    if not table_dict:
        raise ConversionError("Cannot convert empty dict to TableMetadata")

    # Validate required fields
    required_fields = ["table_name", "owner"]
    for field in required_fields:
        if field not in table_dict:
            raise ConversionError(f"Missing required field: {field}")

    try:
        name = table_dict["table_name"]
        schema = table_dict["owner"]
        # Handle None values from unanalyzed tables
        num_rows = int(table_dict.get("num_rows") or 0)
        avg_row_len = int(table_dict.get("avg_row_len") or 0)

        # Handle compression - can be "ENABLED", "DISABLED", None, etc.
        compression_val = table_dict.get("compression")
        if compression_val in ("ENABLED", True, 1):
            compression = True
        else:
            compression = False

        # Convert columns if present
        columns: List[ColumnMetadata] = []
        if "columns" in table_dict and table_dict["columns"]:
            for col_dict in table_dict["columns"]:
                # Handle nullable - Oracle uses Y/N strings
                nullable_val = col_dict.get("nullable", "Y")
                nullable = False if nullable_val == "N" else True

                # Handle avg_size - may not be present
                avg_size = col_dict.get("avg_col_len")

                column = ColumnMetadata(
                    name=col_dict.get("column_name", ""),
                    data_type=col_dict.get("data_type", ""),
                    nullable=nullable,
                    avg_size=avg_size,
                )
                columns.append(column)

        return TableMetadata(
            name=name,
            schema=schema,
            num_rows=num_rows,
            avg_row_len=avg_row_len,
            columns=columns,
            compression=compression,
        )

    except (KeyError, ValueError, TypeError) as e:
        raise ConversionError(f"Failed to convert table dict: {e}") from e
