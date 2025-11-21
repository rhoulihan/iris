"""AWR snapshot helper for simulations.

Provides utilities to create manual AWR snapshots before/after workload execution.
"""

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class AWRSnapshotHelper:
    """Helper for creating and managing AWR snapshots during simulations."""

    def __init__(self, connection: Any):
        """Initialize AWR snapshot helper.

        Args:
            connection: Oracle database connection
        """
        self.connection = connection
        self.cursor = connection.cursor()

    def create_snapshot(self) -> int:
        """Create a manual AWR snapshot.

        Returns:
            The created snapshot ID

        Raises:
            RuntimeError: If snapshot creation fails
        """
        try:
            logger.info("Creating AWR snapshot...")

            # Create bind variable for output
            snap_id_var = self.cursor.var(int)

            # Create manual snapshot using DBMS_WORKLOAD_REPOSITORY
            self.cursor.execute(
                """
                BEGIN
                    :snap_id := DBMS_WORKLOAD_REPOSITORY.CREATE_SNAPSHOT();
                END;
                """,
                snap_id=snap_id_var,
            )

            snapshot_id = snap_id_var.getvalue()
            self.connection.commit()

            logger.info(f"Created AWR snapshot ID: {snapshot_id}")
            return int(snapshot_id)

        except Exception as e:
            logger.error(f"Failed to create AWR snapshot: {e}")
            raise RuntimeError(f"AWR snapshot creation failed: {e}") from e

    def wait_for_snapshot(self, snapshot_id: int, timeout: int = 60):
        """Wait for snapshot to complete processing.

        Args:
            snapshot_id: Snapshot ID to wait for
            timeout: Maximum seconds to wait

        Raises:
            TimeoutError: If snapshot doesn't complete within timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                self.cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM DBA_HIST_SNAPSHOT
                    WHERE snap_id = :1
                    """,
                    [snapshot_id],
                )

                count = self.cursor.fetchone()[0]

                if count > 0:
                    logger.debug(f"Snapshot {snapshot_id} is available")
                    return

                time.sleep(2)

            except Exception as e:
                logger.debug(f"Waiting for snapshot: {e}")
                time.sleep(2)

        raise TimeoutError(f"Snapshot {snapshot_id} did not complete within {timeout}s")

    def get_latest_snapshot_id(self) -> int:
        """Get the latest snapshot ID.

        Returns:
            Latest snapshot ID
        """
        self.cursor.execute("SELECT MAX(snap_id) FROM DBA_HIST_SNAPSHOT")
        result = self.cursor.fetchone()

        if result and result[0]:
            return int(result[0])

        raise RuntimeError("No AWR snapshots found")

    def check_awr_enabled(self) -> bool:
        """Check if AWR is enabled on this database.

        Returns:
            True if AWR is enabled, False otherwise
        """
        try:
            self.cursor.execute(
                """
                SELECT value
                FROM SYS.V_$PARAMETER
                WHERE name = 'statistics_level'
                """
            )

            result = self.cursor.fetchone()

            if result and result[0] in ("TYPICAL", "ALL"):
                logger.info(f"AWR enabled (statistics_level={result[0]})")
                return True

            logger.warning(
                f"AWR may not be enabled (statistics_level={result[0] if result else 'UNKNOWN'})"
            )
            return False

        except Exception as e:
            logger.error(f"Failed to check AWR status: {e}")
            return False

    def get_snapshot_info(self, snapshot_id: int) -> dict:
        """Get information about a snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Dictionary with snapshot information
        """
        self.cursor.execute(
            """
            SELECT
                snap_id,
                TO_CHAR(begin_interval_time, 'YYYY-MM-DD HH24:MI:SS') as begin_time,
                TO_CHAR(end_interval_time, 'YYYY-MM-DD HH24:MI:SS') as end_time,
                snap_level
            FROM DBA_HIST_SNAPSHOT
            WHERE snap_id = :1
            """,
            [snapshot_id],
        )

        result = self.cursor.fetchone()

        if not result:
            raise ValueError(f"Snapshot {snapshot_id} not found")

        return {
            "snap_id": result[0],
            "begin_time": result[1],
            "end_time": result[2],
            "snap_level": result[3],
        }
