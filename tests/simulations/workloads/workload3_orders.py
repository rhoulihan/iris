"""Workload 3 execution: Sales Order System with Analytics.

Simulates hybrid OLTP/Analytics workload (60:40 ratio) that should
trigger Duality View recommendation.
"""

import logging
import random
import time
from typing import Any

logger = logging.getLogger(__name__)


class OrdersWorkload:
    """Executes hybrid OLTP and analytics query patterns."""

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
        self.target_oltp_per_hour = 6000  # 60% of total
        self.target_analytics_per_hour = 4000  # 40% of total

        # Calculate per-second rates
        self.oltp_per_second = self.target_oltp_per_hour / 3600
        self.analytics_per_second = self.target_analytics_per_hour / 3600

        # Get order ID range
        self.cursor.execute("SELECT MIN(order_id), MAX(order_id) FROM orders")
        self.min_order_id, self.max_order_id = self.cursor.fetchone()

        logger.info(f"Order ID range: {self.min_order_id} - {self.max_order_id}")

    def execute(self):
        """Execute the workload for specified duration."""
        logger.info(f"Starting Orders workload for {self.duration_seconds} seconds...")

        start_time = time.time()
        end_time = start_time + self.duration_seconds

        oltp_count = 0
        analytics_count = 0

        oltp_accumulator = 0.0
        analytics_accumulator = 0.0

        last_log_time = start_time

        while time.time() < end_time:
            iteration_start = time.time()

            oltp_accumulator += self.oltp_per_second
            analytics_accumulator += self.analytics_per_second

            # Execute OLTP queries (60% of workload)
            while oltp_accumulator >= 1.0:
                self._execute_oltp_query()
                oltp_count += 1
                oltp_accumulator -= 1.0

            # Execute Analytics queries (40% of workload)
            while analytics_accumulator >= 1.0:
                self._execute_analytics_query()
                analytics_count += 1
                analytics_accumulator -= 1.0

            # Log progress every 30 seconds
            if time.time() - last_log_time >= 30:
                elapsed = time.time() - start_time
                logger.info(
                    f"Progress: {elapsed:.0f}s - OLTP: {oltp_count}, Analytics: {analytics_count}"
                )
                last_log_time = time.time()

            elapsed_iteration = time.time() - iteration_start
            if elapsed_iteration < 1.0:
                time.sleep(1.0 - elapsed_iteration)

        total_duration = time.time() - start_time
        logger.info(
            f"Workload complete: {oltp_count} OLTP, {analytics_count} analytics in {total_duration:.1f}s"
        )

        return {"oltp": oltp_count, "analytics": analytics_count, "duration": total_duration}

    def _execute_oltp_query(self):
        """Execute a random OLTP query based on workload distribution."""
        query_type = random.random()

        if query_type < 0.50:  # 50% - Order lookup
            self._query_order_lookup()
        elif query_type < 0.70:  # 20% - Create order (simulated)
            pass
        elif query_type < 0.90:  # 20% - Add order items (simulated)
            pass
        else:  # 10% - Update order status
            self._update_order_status()

    def _execute_analytics_query(self):
        """Execute a random analytics query based on workload distribution."""
        query_type = random.random()

        if query_type < 0.25:  # 25% - Daily sales summary
            self._query_daily_sales()
        elif query_type < 0.50:  # 25% - Top products
            self._query_top_products()
        elif query_type < 0.75:  # 25% - Customer order history with JSON
            self._query_customer_history_json()
        else:  # 25% - Real-time dashboard
            self._query_dashboard()

    def _query_order_lookup(self):
        """Order lookup with items and payments (50% of OLTP)."""
        order_id = random.randint(self.min_order_id, self.max_order_id)

        self.cursor.execute(
            """
            SELECT o.*, oi.*, op.*
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            LEFT JOIN order_payments op ON o.order_id = op.order_id
            WHERE o.order_id = :1
            """,
            [order_id],
        )
        self.cursor.fetchall()

    def _update_order_status(self):
        """Update order status (10% of OLTP)."""
        order_id = random.randint(self.min_order_id, self.max_order_id)
        status = random.choice(["PENDING", "SHIPPED", "COMPLETED", "CANCELLED"])

        self.cursor.execute(
            """
            UPDATE orders
            SET status = :1
            WHERE order_id = :2
            """,
            [status, order_id],
        )
        self.connection.commit()

    def _query_daily_sales(self):
        """Daily sales summary (25% of analytics) - aggregation query."""
        self.cursor.execute(
            """
            SELECT
                TRUNC(order_date) as day,
                COUNT(*) as order_count,
                SUM(total_amount) as revenue,
                AVG(total_amount) as avg_order_value
            FROM orders
            WHERE order_date >= TRUNC(SYSDATE) - 30
            GROUP BY TRUNC(order_date)
            ORDER BY day DESC
            """
        )
        self.cursor.fetchall()

    def _query_top_products(self):
        """Top products analysis (25% of analytics) - complex join + aggregation."""
        self.cursor.execute(
            """
            SELECT
                oi.product_id,
                COUNT(DISTINCT oi.order_id) as orders,
                SUM(oi.quantity) as units_sold,
                SUM(oi.quantity * oi.unit_price) as revenue
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.order_date >= TRUNC(SYSDATE) - 7
            GROUP BY oi.product_id
            ORDER BY revenue DESC
            FETCH FIRST 20 ROWS ONLY
            """
        )
        self.cursor.fetchall()

    def _query_customer_history_json(self):
        """Retrieve customer order history with JSON aggregation (25% of analytics).

        This query manually builds JSON - a perfect use case for Duality Views!
        """
        # Random customer
        customer_id = random.randint(1, 10000)

        self.cursor.execute(
            """
            SELECT
                o.order_id,
                o.order_date,
                o.status,
                (
                    SELECT JSON_ARRAYAGG(
                        JSON_OBJECT(
                            'product_id' VALUE oi.product_id,
                            'quantity' VALUE oi.quantity,
                            'price' VALUE oi.unit_price
                        )
                    )
                    FROM order_items oi
                    WHERE oi.order_id = o.order_id
                ) as items
            FROM orders o
            WHERE o.customer_id = :1
            AND ROWNUM <= 10
            ORDER BY o.order_date DESC
            """,
            [customer_id],
        )
        self.cursor.fetchall()

    def _query_dashboard(self):
        """Real-time dashboard query (25% of analytics) - summary stats."""
        self.cursor.execute(
            """
            SELECT
                COUNT(*) as total_orders,
                COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending,
                SUM(total_amount) as total_revenue
            FROM orders
            WHERE order_date >= TRUNC(SYSDATE)
            """
        )
        self.cursor.fetchone()
