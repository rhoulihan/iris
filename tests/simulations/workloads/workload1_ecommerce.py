"""Workload 1 execution: E-Commerce User Profiles.

Simulates read-heavy workload (95:5 ratio) with frequent joins
that should trigger document storage recommendation.
"""

import logging
import random
import time
from typing import Any

logger = logging.getLogger(__name__)


class ECommerceWorkload:
    """Executes E-Commerce profile access patterns."""

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
        self.target_reads_per_hour = 10000
        self.target_writes_per_hour = 500

        # Calculate per-second rates
        self.reads_per_second = self.target_reads_per_hour / 3600
        self.writes_per_second = self.target_writes_per_hour / 3600

        # Get customer ID range
        self.cursor.execute("SELECT MIN(customer_id), MAX(customer_id) FROM customers")
        self.min_customer_id, self.max_customer_id = self.cursor.fetchone()

        logger.info(f"Customer ID range: {self.min_customer_id} - {self.max_customer_id}")

    def execute(self):
        """Execute the workload for specified duration."""
        logger.info(f"Starting E-Commerce workload for {self.duration_seconds} seconds...")

        start_time = time.time()
        end_time = start_time + self.duration_seconds

        read_count = 0
        write_count = 0

        # Accumulators for rate limiting
        read_accumulator = 0.0
        write_accumulator = 0.0

        last_log_time = start_time

        while time.time() < end_time:
            iteration_start = time.time()

            # Accumulate fractional queries
            read_accumulator += self.reads_per_second
            write_accumulator += self.writes_per_second

            # Execute reads
            while read_accumulator >= 1.0:
                self._execute_read_query()
                read_count += 1
                read_accumulator -= 1.0

            # Execute writes
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

            # Sleep to maintain rate (target ~1 second per iteration)
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

        if query_type < 0.70:  # 70% - Full profile fetch
            self._query_full_profile()
        elif query_type < 0.90:  # 20% - Profile by email
            self._query_profile_by_email()
        else:  # 10% - Preference lookup
            self._query_preferences()

    def _execute_write_query(self):
        """Execute a random write query based on workload distribution."""
        query_type = random.random()

        if query_type < 0.40:  # 40% - New customer
            self._insert_customer()
        elif query_type < 0.70:  # 30% - Add address
            self._insert_address()
        elif query_type < 0.90:  # 20% - Update preference
            self._update_preference()
        else:  # 10% - Update loyalty tier
            self._update_loyalty_tier()

    def _query_full_profile(self):
        """Full profile retrieval with all nested data (70% of reads)."""
        customer_id = random.randint(self.min_customer_id, self.max_customer_id)

        self.cursor.execute(
            """
            SELECT c.*, a.*, p.*, o.*
            FROM customers c
            LEFT JOIN customer_addresses a ON c.customer_id = a.customer_id
            LEFT JOIN customer_preferences p ON c.customer_id = p.customer_id
            LEFT JOIN customer_order_history o ON c.customer_id = o.customer_id
            WHERE c.customer_id = :1
            """,
            [customer_id],
        )
        self.cursor.fetchall()

    def _query_profile_by_email(self):
        """Profile lookup by email (20% of reads)."""
        # Get random email
        self.cursor.execute(
            """
            SELECT email FROM customers
            WHERE ROWNUM = 1 AND customer_id >= :1
            ORDER BY customer_id
            """,
            [random.randint(self.min_customer_id, self.max_customer_id)],
        )
        row = self.cursor.fetchone()
        if not row:
            return

        email = row[0]

        self.cursor.execute(
            """
            SELECT c.*, a.*
            FROM customers c
            LEFT JOIN customer_addresses a ON c.customer_id = a.customer_id
            WHERE c.email = :1
            """,
            [email],
        )
        self.cursor.fetchall()

    def _query_preferences(self):
        """Preference lookup (10% of reads)."""
        customer_id = random.randint(self.min_customer_id, self.max_customer_id)

        self.cursor.execute(
            """
            SELECT p.*
            FROM customer_preferences p
            WHERE p.customer_id = :1
            """,
            [customer_id],
        )
        self.cursor.fetchall()

    def _insert_customer(self):
        """Register new customer (40% of writes)."""
        # Note: In real scenario, would use sequences
        # For simulation, just skip to avoid conflicts
        pass

    def _insert_address(self):
        """Add address (30% of writes)."""
        # Note: Skipping actual inserts to avoid data growth during simulation
        pass

    def _update_preference(self):
        """Update preference (20% of writes)."""
        customer_id = random.randint(self.min_customer_id, self.max_customer_id)
        category = random.choice(["communication", "newsletter", "marketing"])
        value = random.choice(["email", "sms", "both", "none"])

        self.cursor.execute(
            """
            UPDATE customer_preferences
            SET preference_value = :1
            WHERE customer_id = :2 AND category = :3
            """,
            [value, customer_id, category],
        )
        self.connection.commit()

    def _update_loyalty_tier(self):
        """Update loyalty tier (10% of writes)."""
        customer_id = random.randint(self.min_customer_id, self.max_customer_id)
        tier = random.choice(["BRONZE", "SILVER", "GOLD", "PLATINUM"])

        self.cursor.execute(
            """
            UPDATE customers
            SET loyalty_tier = :1
            WHERE customer_id = :2
            """,
            [tier, customer_id],
        )
        self.connection.commit()
