"""AWR Data Collector for IRIS project.

This module provides the AWRCollector class for retrieving performance data
from Oracle Automatic Workload Repository (AWR). It collects snapshot information,
SQL statistics, and execution plans.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AWRCollector:
    """Collects performance data from Oracle AWR.

    This class provides methods to retrieve AWR snapshots, SQL statistics,
    and execution plans from Oracle Database's Automatic Workload Repository.

    Attributes:
        connection: Oracle database connection object (oracledb.Connection)

    Example:
        >>> import oracledb
        >>> conn = oracledb.connect(user="iris_user", password="pwd", dsn="localhost/FREEPDB1")
        >>> collector = AWRCollector(conn)
        >>> snapshot_id = collector.get_latest_snapshot_id()
        >>> sql_stats = collector.get_sql_statistics(begin_snap=snapshot_id-1, end_snap=snapshot_id)
    """

    def __init__(self, connection: Any):
        """Initialize AWRCollector with database connection.

        Args:
            connection: Oracle database connection object

        Raises:
            ValueError: If connection is None
            RuntimeError: If AWR views are not accessible
        """
        if connection is None:
            raise ValueError("Database connection required")

        self.connection = connection
        self._validate_awr_access()
        logger.info("AWR Collector initialized successfully")

    def _validate_awr_access(self) -> None:
        """Validate access to AWR views.

        Raises:
            RuntimeError: If AWR views are not accessible
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM DBA_HIST_SNAPSHOT WHERE ROWNUM = 1")
                cursor.fetchone()
            logger.debug("AWR view access validated successfully")
        except Exception as e:
            logger.error(f"Cannot access AWR views: {e}")
            raise RuntimeError(f"Cannot access AWR views: {e}") from e

    def get_latest_snapshot_id(self) -> int:
        """Get the most recent AWR snapshot ID.

        Returns:
            The latest snapshot ID

        Raises:
            RuntimeError: If no AWR snapshots found or query times out
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT MAX(snap_id) FROM DBA_HIST_SNAPSHOT")
                result = cursor.fetchone()

                if result is None or result[0] is None:
                    raise RuntimeError("No AWR snapshots found")

                snapshot_id = int(result[0])
                logger.info(f"Latest snapshot ID: {snapshot_id}")
                return snapshot_id

        except Exception as e:
            if "01013" in str(e):  # ORA-01013: user requested cancel
                raise RuntimeError(f"Query timeout: {e}") from e
            raise

    def get_snapshot_range(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get snapshot IDs within a time range.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of dictionaries containing snapshot information
        """
        query = """
            SELECT snap_id, begin_interval_time
            FROM DBA_HIST_SNAPSHOT
            WHERE begin_interval_time BETWEEN :start_time AND :end_time
            ORDER BY snap_id
        """

        with self.connection.cursor() as cursor:
            cursor.execute(query, start_time=start_time, end_time=end_time)
            rows = cursor.fetchall()

            snapshots = [{"snap_id": row[0], "begin_time": row[1]} for row in rows]

            logger.info(f"Found {len(snapshots)} snapshots in range")
            return snapshots

    def get_snapshot_info(self, snap_id: int) -> Dict[str, Any]:
        """Get detailed information for a specific snapshot.

        Args:
            snap_id: Snapshot ID to retrieve

        Returns:
            Dictionary containing snapshot details
        """
        query = """
            SELECT snap_id, dbid, instance_number,
                   begin_interval_time, end_interval_time, startup_time
            FROM DBA_HIST_SNAPSHOT
            WHERE snap_id = :snap_id
        """

        with self.connection.cursor() as cursor:
            cursor.execute(query, snap_id=snap_id)
            row = cursor.fetchone()

            if row is None:
                logger.warning(f"Snapshot {snap_id} not found")
                return {}

            snapshot_info = {
                "snap_id": row[0],
                "dbid": row[1],
                "instance_number": row[2],
                "begin_time": row[3],
                "end_time": row[4],
                "startup_time": row[5],
            }

            logger.debug(f"Retrieved snapshot info for {snap_id}")
            return snapshot_info

    def get_sql_statistics(
        self, begin_snap: int, end_snap: int, top_n: int = 100
    ) -> List[Dict[str, Any]]:
        """Get SQL statistics for a snapshot range.

        Args:
            begin_snap: Beginning snapshot ID
            end_snap: Ending snapshot ID
            top_n: Number of top SQL statements to return (default: 100)

        Returns:
            List of dictionaries containing SQL statistics
        """
        query = """
            SELECT sql_id,
                   plan_hash_value,
                   SUM(executions_delta) as executions,
                   SUM(elapsed_time_delta) as elapsed_time_total,
                   SUM(cpu_time_delta) as cpu_time_total,
                   SUM(disk_reads_delta) as disk_reads,
                   SUM(buffer_gets_delta) as buffer_gets,
                   SUM(rows_processed_delta) as rows_processed
            FROM DBA_HIST_SQLSTAT
            WHERE snap_id BETWEEN :begin_snap AND :end_snap
              AND executions_delta > 0
            GROUP BY sql_id, plan_hash_value
            ORDER BY elapsed_time_total DESC
            FETCH FIRST :top_n ROWS ONLY
        """

        with self.connection.cursor() as cursor:
            cursor.execute(query, begin_snap=begin_snap, end_snap=end_snap, top_n=top_n)
            rows = cursor.fetchall()

            sql_stats = []
            for row in rows:
                elapsed_time_us = row[3]
                executions = row[2]

                stat = {
                    "sql_id": row[0],
                    "plan_hash_value": row[1],
                    "executions": executions,
                    "elapsed_time_ms": elapsed_time_us / 1000,  # Convert to milliseconds
                    "cpu_time_ms": row[4] / 1000,
                    "disk_reads": row[5],
                    "buffer_gets": row[6],
                    "rows_processed": row[7],
                }

                # Calculate averages
                if executions > 0:
                    stat["avg_elapsed_time_ms"] = elapsed_time_us / executions / 1000
                    stat["avg_cpu_time_ms"] = row[4] / executions / 1000
                else:
                    stat["avg_elapsed_time_ms"] = 0.0
                    stat["avg_cpu_time_ms"] = 0.0

                sql_stats.append(stat)

            logger.info(
                f"Retrieved {len(sql_stats)} SQL statistics for snapshots {begin_snap}-{end_snap}"
            )
            return sql_stats

    def get_sql_text(self, sql_id: str) -> Optional[str]:
        """Get SQL text for a given SQL ID.

        Args:
            sql_id: SQL identifier

        Returns:
            SQL text or None if not found
        """
        query = """
            SELECT sql_text
            FROM DBA_HIST_SQLTEXT
            WHERE sql_id = :sql_id
        """

        with self.connection.cursor() as cursor:
            cursor.execute(query, sql_id=sql_id)
            row = cursor.fetchone()

            if row is None:
                logger.debug(f"SQL text not found for {sql_id}")
                return None

            return str(row[0])

    def get_execution_plan(self, sql_id: str, plan_hash_value: int) -> List[Dict[str, Any]]:
        """Get execution plan for SQL ID and plan hash.

        Args:
            sql_id: SQL identifier
            plan_hash_value: Plan hash value

        Returns:
            List of dictionaries containing execution plan steps
        """
        query = """
            SELECT plan_hash_value, id, operation, options,
                   object_name, cost, cardinality
            FROM DBA_HIST_SQL_PLAN
            WHERE sql_id = :sql_id
              AND plan_hash_value = :plan_hash_value
            ORDER BY id
        """

        with self.connection.cursor() as cursor:
            cursor.execute(query, sql_id=sql_id, plan_hash_value=plan_hash_value)
            rows = cursor.fetchall()

            plan_steps = [
                {
                    "plan_hash_value": row[0],
                    "id": row[1],
                    "operation": row[2],
                    "options": row[3],
                    "object_name": row[4],
                    "cost": row[5],
                    "cardinality": row[6],
                }
                for row in rows
            ]

            if plan_steps:
                logger.debug(
                    f"Retrieved {len(plan_steps)} plan steps for {sql_id}/{plan_hash_value}"
                )
            else:
                logger.debug(f"No execution plan found for {sql_id}/{plan_hash_value}")

            return plan_steps
