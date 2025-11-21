"""Workload 2 execution: Real-Time Inventory Management.

Simulates write-heavy workload (70:30 ratio) with JSON document updates
that should trigger relational normalization recommendation.
"""

import logging
import random
import time
from typing import Any

logger = logging.getLogger(__name__)


class InventoryWorkload:
    """Executes high-velocity inventory update patterns."""

    def __init__(self, connection: Any, duration_seconds: int = 300):
        """Initialize workload executor.

        Args:
            connection: Oracle database connection
            duration_seconds: How long to run the workload
        """
        self.connection = connection
        self.duration_seconds = duration_seconds
        self.cursor = connection.cursor()

        # Query execution counts (per hour targets)
        self.target_reads_per_hour = 3000
        self.target_writes_per_hour = 7000

        # Calculate per-second rates
        self.reads_per_second = self.target_reads_per_hour / 3600
        self.writes_per_second = self.target_writes_per_hour / 3600

        # Get item ID range
        self.cursor.execute("SELECT MIN(item_id), MAX(item_id) FROM inventory_items")
        result = self.cursor.fetchall()
        if result and result[0][0]:
            self.item_ids = [
                row[0]
                for row in self.cursor.execute("SELECT item_id FROM inventory_items").fetchall()
            ]
        else:
            self.item_ids = []

        logger.info(f"Loaded {len(self.item_ids)} inventory items")

    def execute(self):
        """Execute the workload for specified duration."""
        logger.info(f"Starting Inventory workload for {self.duration_seconds} seconds...")

        if not self.item_ids:
            logger.warning("No inventory items found - skipping workload")
            return {"reads": 0, "writes": 0, "duration": 0}

        start_time = time.time()
        end_time = start_time + self.duration_seconds

        read_count = 0
        write_count = 0

        read_accumulator = 0.0
        write_accumulator = 0.0

        last_log_time = start_time

        while time.time() < end_time:
            iteration_start = time.time()

            read_accumulator += self.reads_per_second
            write_accumulator += self.writes_per_second

            # Execute reads (30% of workload)
            while read_accumulator >= 1.0:
                self._execute_read_query()
                read_count += 1
                read_accumulator -= 1.0

            # Execute writes (70% of workload)
            while write_accumulator >= 1.0:
                self._execute_write_query()
                write_count += 1
                write_accumulator -= 1.0

            # Log progress every 30 seconds
            if time.time() - last_log_time >= 30:
                elapsed = time.time() - start_time
                logger.info(
                    f"Progress: {elapsed:.0f}s - Reads: {read_count}, Writes: {write_count}"
                )
                last_log_time = time.time()

            elapsed_iteration = time.time() - iteration_start
            if elapsed_iteration < 1.0:
                time.sleep(1.0 - elapsed_iteration)

        total_duration = time.time() - start_time
        logger.info(
            f"Workload complete: {read_count} reads, {write_count} writes in {total_duration:.1f}s"
        )

        return {"reads": read_count, "writes": write_count, "duration": total_duration}

    def _execute_read_query(self):
        """Execute a random read query based on workload distribution."""
        query_type = random.random()

        if query_type < 0.60:  # 60% - Stock level check
            self._query_stock_level()
        elif query_type < 0.90:  # 30% - Available quantity
            self._query_available_quantity()
        else:  # 10% - Warehouse-specific lookup
            self._query_warehouse_stock()

    def _execute_write_query(self):
        """Execute a random write query based on workload distribution."""
        query_type = random.random()

        if query_type < 0.40:  # 40% - Update stock quantity
            self._update_stock_quantity()
        elif query_type < 0.70:  # 30% - Reserve stock
            self._reserve_stock()
        elif query_type < 0.90:  # 20% - Add transaction
            self._add_transaction()
        else:  # 10% - Insert new item (skipped in simulation)
            pass

    def _query_stock_level(self):
        """Stock level check (60% of reads)."""
        item_id = random.choice(self.item_ids)

        self.cursor.execute(
            """
            SELECT JSON_VALUE(inventory_doc, '$.warehouses[*].stockLevels[*].quantity')
            FROM inventory_items
            WHERE item_id = :1
            """,
            [item_id],
        )
        self.cursor.fetchone()

    def _query_available_quantity(self):
        """Available quantity lookup (30% of reads)."""
        item_id = random.choice(self.item_ids)

        self.cursor.execute(
            """
            SELECT
                JSON_VALUE(inventory_doc, '$.warehouses[0].stockLevels[0].quantity') -
                JSON_VALUE(inventory_doc, '$.warehouses[0].stockLevels[0].reserved') as available
            FROM inventory_items
            WHERE item_id = :1
            """,
            [item_id],
        )
        self.cursor.fetchone()

    def _query_warehouse_stock(self):
        """Warehouse-specific lookup (10% of reads)."""
        # This triggers table scan - anti-pattern!
        self.cursor.execute(
            """
            SELECT item_id, inventory_doc
            FROM inventory_items
            WHERE JSON_EXISTS(inventory_doc, '$.warehouses[?(@.warehouseId == "WH-001")]')
            AND ROWNUM <= 10
            """
        )
        self.cursor.fetchall()

    def _update_stock_quantity(self):
        """Update stock quantity (40% of writes) - expensive JSON_TRANSFORM."""
        item_id = random.choice(self.item_ids)
        new_qty = random.randint(0, 200)

        try:
            self.cursor.execute(
                """
                UPDATE inventory_items
                SET inventory_doc = JSON_TRANSFORM(
                    inventory_doc,
                    SET '$.warehouses[0].stockLevels[0].quantity' = :1
                ),
                last_updated = SYSTIMESTAMP
                WHERE item_id = :2
                """,
                [new_qty, item_id],
            )
            self.connection.commit()
        except Exception as e:
            logger.debug(f"Update failed: {e}")
            self.connection.rollback()

    def _reserve_stock(self):
        """Reserve stock (30% of writes) - complex JSON operation."""
        item_id = random.choice(self.item_ids)
        reserve_qty = random.randint(1, 20)

        try:
            # This is a complex operation that would benefit from relational schema
            self.cursor.execute(
                """
                UPDATE inventory_items
                SET inventory_doc = JSON_TRANSFORM(
                    inventory_doc,
                    SET '$.warehouses[0].stockLevels[0].reserved' =
                        CAST(JSON_VALUE(inventory_doc, '$.warehouses[0].stockLevels[0].reserved') AS NUMBER) + :1
                ),
                last_updated = SYSTIMESTAMP
                WHERE item_id = :2
                """,
                [reserve_qty, item_id],
            )
            self.connection.commit()
        except Exception as e:
            logger.debug(f"Reserve failed: {e}")
            self.connection.rollback()

    def _add_transaction(self):
        """Add transaction record (20% of writes) - growing array anti-pattern."""
        item_id = random.choice(self.item_ids)
        txn_type = random.choice(["receipt", "shipment", "adjustment"])
        quantity = random.randint(1, 50)

        try:
            self.cursor.execute(
                """
                UPDATE inventory_items
                SET inventory_doc = JSON_TRANSFORM(
                    inventory_doc,
                    APPEND '$.transactions' = JSON_OBJECT(
                        'type' VALUE :1,
                        'quantity' VALUE :2,
                        'timestamp' VALUE TO_CHAR(SYSTIMESTAMP, 'YYYY-MM-DD"T"HH24:MI:SS')
                    )
                ),
                last_updated = SYSTIMESTAMP
                WHERE item_id = :3
                """,
                [txn_type, quantity, item_id],
            )
            self.connection.commit()
        except Exception as e:
            logger.debug(f"Transaction append failed: {e}")
            self.connection.rollback()
