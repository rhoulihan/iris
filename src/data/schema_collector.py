"""Schema Metadata Collector for IRIS project.

This module provides the SchemaCollector class for retrieving Oracle database
schema metadata including tables, columns, indexes, and constraints.
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SchemaCollector:
    """Collects schema metadata from Oracle database.

    This class provides methods to retrieve table structures, column definitions,
    indexes, and constraints from Oracle Database's data dictionary views.

    Attributes:
        connection: Oracle database connection object (oracledb.Connection)

    Example:
        >>> import oracledb
        >>> conn = oracledb.connect(user="iris_user", password="pwd", dsn="localhost/FREEPDB1")
        >>> collector = SchemaCollector(conn)
        >>> tables = collector.get_tables(owner="APP_SCHEMA")
        >>> indexes = collector.get_indexes(owner="APP_SCHEMA", table_name="USERS")
    """

    def __init__(self, connection: Any):
        """Initialize SchemaCollector with database connection.

        Args:
            connection: Oracle database connection object

        Raises:
            ValueError: If connection is None
            RuntimeError: If schema metadata views are not accessible
        """
        if connection is None:
            raise ValueError("Database connection required")

        self.connection = connection
        self._validate_schema_access()
        logger.info("Schema Collector initialized successfully")

    def _validate_schema_access(self) -> None:
        """Validate access to schema metadata views.

        Raises:
            RuntimeError: If unable to access schema views
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM all_tables WHERE ROWNUM = 1")
            cursor.fetchone()
            cursor.close()
            logger.debug("Schema metadata access validated")
        except Exception as e:
            logger.error(f"Cannot access schema metadata views: {e}")
            raise RuntimeError("Cannot access schema metadata views") from e

    def get_tables(self, owner: str, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve table metadata.

        Args:
            owner: Schema owner name
            table_name: Optional table name to filter (default: all tables)

        Returns:
            List of dictionaries containing table metadata:
                - table_name: Name of the table
                - owner: Schema owner
                - tablespace_name: Tablespace where table is stored
                - num_rows: Number of rows (from statistics)
                - avg_row_len: Average row length (from statistics)
                - last_analyzed: Last statistics collection date

        Raises:
            RuntimeError: If unable to retrieve table metadata
        """
        try:
            cursor = self.connection.cursor()

            query = """
                SELECT
                    table_name,
                    owner,
                    tablespace_name,
                    num_rows,
                    avg_row_len,
                    TO_CHAR(last_analyzed, 'YYYY-MM-DD HH24:MI:SS') as last_analyzed
                FROM all_tables
                WHERE owner = :owner
            """

            params = {"owner": owner}
            if table_name:
                query += " AND table_name = :table_name"
                params["table_name"] = table_name

            query += " ORDER BY table_name"

            cursor.execute(query, params)
            columns = [col[0].lower() for col in cursor.description]
            rows = cursor.fetchall()
            cursor.close()

            tables = []
            for row in rows:
                table_dict = dict(zip(columns, row))
                tables.append(table_dict)

            logger.info(f"Retrieved {len(tables)} tables for owner {owner}")
            return tables

        except Exception as e:
            logger.error(f"Failed to retrieve table metadata: {e}")
            raise RuntimeError(f"Failed to retrieve table metadata: {e}") from e

    def get_columns(self, owner: str, table_name: str) -> List[Dict[str, Any]]:
        """Retrieve column metadata for a table.

        Args:
            owner: Schema owner name
            table_name: Table name

        Returns:
            List of dictionaries containing column metadata:
                - table_name: Name of the table
                - column_name: Name of the column
                - data_type: Data type (e.g., VARCHAR2, NUMBER)
                - data_length: Length for character types
                - nullable: Y/N indicating if NULL values allowed
                - column_id: Position in table
                - num_distinct: Number of distinct values
                - num_nulls: Number of NULL values

        Raises:
            RuntimeError: If unable to retrieve column metadata
        """
        try:
            cursor = self.connection.cursor()

            query = """
                SELECT
                    c.table_name,
                    c.column_name,
                    c.data_type,
                    c.data_length,
                    c.nullable,
                    c.column_id,
                    s.num_distinct,
                    s.num_nulls
                FROM all_tab_columns c
                LEFT JOIN all_tab_col_statistics s
                    ON c.owner = s.owner
                    AND c.table_name = s.table_name
                    AND c.column_name = s.column_name
                WHERE c.owner = :owner
                    AND c.table_name = :table_name
                ORDER BY c.column_id
            """

            cursor.execute(query, {"owner": owner, "table_name": table_name})
            columns = [col[0].lower() for col in cursor.description]
            rows = cursor.fetchall()
            cursor.close()

            column_list = []
            for row in rows:
                column_dict = dict(zip(columns, row))
                column_list.append(column_dict)

            logger.info(f"Retrieved {len(column_list)} columns for {owner}.{table_name}")
            return column_list

        except Exception as e:
            logger.error(f"Failed to retrieve column metadata: {e}")
            raise RuntimeError(f"Failed to retrieve column metadata: {e}") from e

    def get_indexes(self, owner: str, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve index metadata.

        Args:
            owner: Schema owner name
            table_name: Optional table name to filter (default: all tables)

        Returns:
            List of dictionaries containing index metadata:
                - index_name: Name of the index
                - table_name: Name of the table
                - owner: Schema owner
                - index_type: Type (NORMAL, BITMAP, etc.)
                - uniqueness: UNIQUE or NONUNIQUE
                - status: VALID or INVALID
                - columns: List of column names in index order

        Raises:
            RuntimeError: If unable to retrieve index metadata
        """
        try:
            cursor = self.connection.cursor()

            query = """
                SELECT
                    i.index_name,
                    i.table_name,
                    i.owner,
                    i.index_type,
                    i.uniqueness,
                    i.status,
                    ic.column_name,
                    ic.column_position
                FROM all_indexes i
                JOIN all_ind_columns ic
                    ON i.owner = ic.index_owner
                    AND i.index_name = ic.index_name
                WHERE i.owner = :owner
            """

            params = {"owner": owner}
            if table_name:
                query += " AND i.table_name = :table_name"
                params["table_name"] = table_name

            query += " ORDER BY i.index_name, ic.column_position"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()

            # Group columns by index
            indexes_dict: Dict[str, Dict[str, Any]] = defaultdict(
                lambda: {
                    "columns": [],
                    "index_name": None,
                    "table_name": None,
                    "owner": None,
                    "index_type": None,
                    "uniqueness": None,
                    "status": None,
                }
            )

            for row in rows:
                (
                    index_name,
                    table_name_val,
                    owner_val,
                    index_type,
                    uniqueness,
                    status,
                    column_name,
                    column_position,
                ) = row

                idx_key = index_name
                if indexes_dict[idx_key]["index_name"] is None:
                    indexes_dict[idx_key].update(
                        {
                            "index_name": index_name,
                            "table_name": table_name_val,
                            "owner": owner_val,
                            "index_type": index_type,
                            "uniqueness": uniqueness,
                            "status": status,
                        }
                    )
                indexes_dict[idx_key]["columns"].append(column_name)

            indexes = list(indexes_dict.values())
            logger.info(f"Retrieved {len(indexes)} indexes for owner {owner}")
            return indexes

        except Exception as e:
            logger.error(f"Failed to retrieve index metadata: {e}")
            raise RuntimeError(f"Failed to retrieve index metadata: {e}") from e

    def get_constraints(self, owner: str, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve constraint metadata.

        Args:
            owner: Schema owner name
            table_name: Optional table name to filter (default: all tables)

        Returns:
            List of dictionaries containing constraint metadata:
                - constraint_name: Name of the constraint
                - table_name: Name of the table
                - constraint_type: P (primary key), U (unique), R (foreign key), C (check)
                - status: ENABLED or DISABLED
                - columns: List of column names
                - r_table_name: Referenced table (for foreign keys)
                - r_columns: Referenced columns (for foreign keys)

        Raises:
            RuntimeError: If unable to retrieve constraint metadata
        """
        try:
            cursor = self.connection.cursor()

            query = """
                SELECT
                    c.constraint_name,
                    c.table_name,
                    c.constraint_type,
                    c.status,
                    cc.column_name,
                    cc.position,
                    rc.table_name as r_table_name,
                    rcc.column_name as r_column_name
                FROM all_constraints c
                JOIN all_cons_columns cc
                    ON c.owner = cc.owner
                    AND c.constraint_name = cc.constraint_name
                LEFT JOIN all_constraints rc
                    ON c.r_owner = rc.owner
                    AND c.r_constraint_name = rc.constraint_name
                LEFT JOIN all_cons_columns rcc
                    ON rc.owner = rcc.owner
                    AND rc.constraint_name = rcc.constraint_name
                    AND cc.position = rcc.position
                WHERE c.owner = :owner
                    AND c.constraint_type IN ('P', 'U', 'R')
            """

            params = {"owner": owner}
            if table_name:
                query += " AND c.table_name = :table_name"
                params["table_name"] = table_name

            query += " ORDER BY c.constraint_name, cc.position"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()

            # Group columns by constraint
            constraints_dict: Dict[str, Dict[str, Any]] = defaultdict(
                lambda: {
                    "columns": [],
                    "r_columns": [],
                    "constraint_name": None,
                    "table_name": None,
                    "constraint_type": None,
                    "status": None,
                    "r_table_name": None,
                }
            )

            for row in rows:
                (
                    constraint_name,
                    table_name_val,
                    constraint_type,
                    status,
                    column_name,
                    position,
                    r_table_name,
                    r_column_name,
                ) = row

                const_key = constraint_name
                if constraints_dict[const_key]["constraint_name"] is None:
                    constraints_dict[const_key].update(
                        {
                            "constraint_name": constraint_name,
                            "table_name": table_name_val,
                            "constraint_type": constraint_type,
                            "status": status,
                            "r_table_name": r_table_name,
                        }
                    )
                constraints_dict[const_key]["columns"].append(column_name)
                if r_column_name:
                    constraints_dict[const_key]["r_columns"].append(r_column_name)

            # Clean up empty r_columns lists
            constraints = []
            for const in constraints_dict.values():
                if not const["r_columns"]:
                    del const["r_columns"]
                if const["r_table_name"] is None:
                    del const["r_table_name"]
                constraints.append(const)

            logger.info(f"Retrieved {len(constraints)} constraints for owner {owner}")
            return constraints

        except Exception as e:
            logger.error(f"Failed to retrieve constraint metadata: {e}")
            raise RuntimeError(f"Failed to retrieve constraint metadata: {e}") from e

    def get_schema_metadata(self, owner: str, table_name: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve complete schema metadata.

        Args:
            owner: Schema owner name
            table_name: Optional table name to filter (default: all tables)

        Returns:
            Dictionary containing complete schema metadata:
                - tables: List of table metadata
                - columns: List of column metadata (if table_name specified)
                - indexes: List of index metadata
                - constraints: List of constraint metadata
        """
        result: Dict[str, Any] = {
            "tables": self.get_tables(owner, table_name),
            "indexes": self.get_indexes(owner, table_name),
            "constraints": self.get_constraints(owner, table_name),
        }

        # If specific table requested, include column metadata
        if table_name:
            result["columns"] = self.get_columns(owner, table_name)

        logger.info(f"Retrieved complete schema metadata for owner {owner}")
        return result
