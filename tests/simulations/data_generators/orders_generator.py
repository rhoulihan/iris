"""Data generator for Workload 3: Sales Order System with Analytics.

Generates order data for hybrid OLTP/Analytics workload that should be
recommended for Duality Views.
"""

import logging
import random
from typing import Any

from faker import Faker

logger = logging.getLogger(__name__)


class OrdersDataGenerator:
    """Generates sales order data for OLTP and analytics workloads."""

    def __init__(self, num_orders: int = 5000, seed: int = 42):
        """Initialize data generator.

        Args:
            num_orders: Number of orders to generate
            seed: Random seed for reproducibility
        """
        self.num_orders = num_orders
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)

        # Order configuration
        self.order_statuses = ["COMPLETED", "PENDING", "CANCELLED", "SHIPPED"]
        self.status_weights = [0.70, 0.15, 0.10, 0.05]

        self.payment_methods = ["credit_card", "debit_card", "paypal", "bank_transfer"]
        self.payment_weights = [0.60, 0.20, 0.15, 0.05]

        # Product catalog (simplified)
        self.product_ids = list(range(1, 201))  # 200 products

    def generate_orders(self, connection: Any, batch_size: int = 1000):
        """Generate and insert orders.

        Args:
            connection: Oracle database connection
            batch_size: Number of records to insert per batch
        """
        logger.info(f"Generating {self.num_orders} orders...")

        cursor = connection.cursor()
        orders = []

        for i in range(self.num_orders):
            # Random customer (1-10000 possible customers)
            customer_id = random.randint(1, 10000)

            # Order dates distributed over last 90 days
            order_date = self.fake.date_between(start_date="-90d", end_date="today")

            # Generate order
            order = {
                "order_id": i + 1,
                "customer_id": customer_id,
                "order_date": order_date,
                "status": random.choices(self.order_statuses, weights=self.status_weights)[0],
                "total_amount": 0,  # Will be calculated from items
                "shipping_address": self.fake.address().replace("\n", ", "),
                "billing_address": self.fake.address().replace("\n", ", "),
            }
            orders.append(order)

            if len(orders) >= batch_size:
                self._insert_order_batch(cursor, orders)
                orders = []

        # Insert remaining
        if orders:
            self._insert_order_batch(cursor, orders)

        connection.commit()
        logger.info(f"Inserted {self.num_orders} orders")

    def generate_order_items(self, connection: Any, batch_size: int = 1000):
        """Generate and insert order items (avg 4 per order).

        Args:
            connection: Oracle database connection
            batch_size: Number of records to insert per batch
        """
        logger.info("Generating order items...")

        cursor = connection.cursor()
        items = []
        item_id = 1

        # Track order totals for update
        order_totals = {}

        for order_id in range(1, self.num_orders + 1):
            # Each order has 2-6 items
            num_items = random.randint(2, 6)
            order_total = 0.0

            for _ in range(num_items):
                product_id = random.choice(self.product_ids)
                quantity = random.randint(1, 5)
                unit_price = round(random.uniform(10.0, 200.0), 2)
                discount = random.choice([0, 5, 10, 15]) if random.random() > 0.7 else 0

                item_total = quantity * unit_price * (1 - discount / 100)
                order_total += item_total

                item = {
                    "item_id": item_id,
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "discount": discount,
                }
                items.append(item)
                item_id += 1

                if len(items) >= batch_size:
                    self._insert_item_batch(cursor, items)
                    items = []

            order_totals[order_id] = round(order_total, 2)

        # Insert remaining items
        if items:
            self._insert_item_batch(cursor, items)

        # Update order totals
        logger.info("Updating order totals...")
        cursor.executemany(
            """
            UPDATE orders
            SET total_amount = :total
            WHERE order_id = :order_id
            """,
            [{"order_id": oid, "total": total} for oid, total in order_totals.items()],
        )

        connection.commit()
        logger.info(f"Inserted {item_id - 1} order items")

    def generate_payments(self, connection: Any, batch_size: int = 1000):
        """Generate and insert payments (some orders have split payments).

        Args:
            connection: Oracle database connection
            batch_size: Number of records to insert per batch
        """
        logger.info("Generating payments...")

        cursor = connection.cursor()
        payments = []
        payment_id = 1

        # Get order totals
        cursor.execute("SELECT order_id, total_amount FROM orders WHERE total_amount > 0")
        order_totals = {row[0]: row[1] for row in cursor.fetchall()}

        for order_id, total in order_totals.items():
            # 10% of orders have split payment
            if random.random() < 0.10 and total > 100:
                # Split into 2 payments
                split1 = round(total * random.uniform(0.4, 0.6), 2)
                split2 = round(total - split1, 2)

                for amount in [split1, split2]:
                    payment = {
                        "payment_id": payment_id,
                        "order_id": order_id,
                        "payment_method": random.choices(
                            self.payment_methods, weights=self.payment_weights
                        )[0],
                        "amount": amount,
                    }
                    payments.append(payment)
                    payment_id += 1
            else:
                # Single payment
                payment = {
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "payment_method": random.choices(
                        self.payment_methods, weights=self.payment_weights
                    )[0],
                    "amount": total,
                }
                payments.append(payment)
                payment_id += 1

            if len(payments) >= batch_size:
                self._insert_payment_batch(cursor, payments)
                payments = []

        # Insert remaining
        if payments:
            self._insert_payment_batch(cursor, payments)

        connection.commit()
        logger.info(f"Inserted {payment_id - 1} payments")

    def generate_all(self, connection: Any):
        """Generate all data for Workload 3.

        Args:
            connection: Oracle database connection
        """
        logger.info("Starting Workload 3 data generation...")
        self.generate_orders(connection)
        self.generate_order_items(connection)
        self.generate_payments(connection)
        logger.info("Workload 3 data generation complete")

    def _insert_order_batch(self, cursor: Any, orders: list):
        """Insert batch of orders."""
        cursor.executemany(
            """
            INSERT INTO orders
            (order_id, customer_id, order_date, status, total_amount,
             shipping_address, billing_address)
            VALUES (:order_id, :customer_id, :order_date, :status, :total_amount,
                    :shipping_address, :billing_address)
            """,
            orders,
        )

    def _insert_item_batch(self, cursor: Any, items: list):
        """Insert batch of order items."""
        cursor.executemany(
            """
            INSERT INTO order_items
            (item_id, order_id, product_id, quantity, unit_price, discount)
            VALUES (:item_id, :order_id, :product_id, :quantity, :unit_price, :discount)
            """,
            items,
        )

    def _insert_payment_batch(self, cursor: Any, payments: list):
        """Insert batch of payments."""
        cursor.executemany(
            """
            INSERT INTO order_payments
            (payment_id, order_id, payment_method, amount, payment_date)
            VALUES (:payment_id, :order_id, :payment_method, :amount, SYSDATE)
            """,
            payments,
        )
