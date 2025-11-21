"""Data generator for Workload 2: Real-Time Inventory Management.

Generates JSON document inventory data that should be recommended for
relational normalization due to high write velocity.
"""

import json
import logging
import random
from typing import Any

from faker import Faker

logger = logging.getLogger(__name__)


class InventoryDataGenerator:
    """Generates inventory management JSON documents."""

    def __init__(self, num_items: int = 500, seed: int = 42):
        """Initialize data generator.

        Args:
            num_items: Number of inventory items to generate
            seed: Random seed for reproducibility
        """
        self.num_items = num_items
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)

        # Warehouse configuration
        self.warehouses = [
            {"id": "WH-001", "location": "Building A"},
            {"id": "WH-002", "location": "Building B"},
            {"id": "WH-003", "location": "Building C"},
        ]

        # Bin locations per warehouse
        self.bins_per_warehouse = ["A1-001", "A1-002", "A1-003", "B2-001", "B2-002"]

        # Transaction types
        self.txn_types = ["receipt", "shipment", "adjustment", "transfer"]

    def generate_inventory_items(self, connection: Any, batch_size: int = 100):
        """Generate and insert inventory items with JSON documents.

        Args:
            connection: Oracle database connection
            batch_size: Number of records to insert per batch
        """
        logger.info(f"Generating {self.num_items} inventory items...")

        cursor = connection.cursor()
        items = []

        for i in range(self.num_items):
            item_id = f"SKU-{i + 1:05d}"

            # Generate complex JSON document
            inventory_doc = self._generate_inventory_doc(item_id)

            item = {"item_id": item_id, "inventory_doc": json.dumps(inventory_doc)}

            items.append(item)

            if len(items) >= batch_size:
                self._insert_item_batch(cursor, items)
                items = []

        # Insert remaining
        if items:
            self._insert_item_batch(cursor, items)

        connection.commit()
        logger.info(f"Inserted {self.num_items} inventory items")

    def _generate_inventory_doc(self, item_id: str) -> dict:
        """Generate a complex inventory JSON document.

        Args:
            item_id: Item SKU identifier

        Returns:
            Dictionary representing the inventory document
        """
        # Generate warehouses data
        warehouses = []
        for wh in random.sample(self.warehouses, k=random.randint(1, 2)):
            stock_levels = []

            # Each warehouse has 2-3 bin locations
            num_bins = random.randint(2, 3)
            for bin_loc in random.sample(self.bins_per_warehouse, k=num_bins):
                quantity = random.randint(0, 200)
                reserved = random.randint(0, min(50, quantity))

                stock_levels.append({"bin": bin_loc, "quantity": quantity, "reserved": reserved})

            warehouses.append(
                {"warehouseId": wh["id"], "location": wh["location"], "stockLevels": stock_levels}
            )

        # Generate transaction history (growing array - anti-pattern!)
        transactions = []
        num_transactions = random.randint(10, 30)  # Simulates accumulation over time

        for _ in range(num_transactions):
            txn_date = self.fake.date_time_between(start_date="-90d", end_date="now")
            transactions.append(
                {
                    "type": random.choice(self.txn_types),
                    "quantity": random.randint(1, 100),
                    "timestamp": txn_date.isoformat(),
                }
            )

        # Sort transactions by timestamp
        transactions.sort(key=lambda x: x["timestamp"])

        # Generate pricing data
        cost = round(random.uniform(5.0, 100.0), 2)
        retail = round(cost * random.uniform(1.5, 3.0), 2)

        pricing = {
            "cost": cost,
            "retail": retail,
            "discounts": (
                [
                    {"type": "bulk", "threshold": 10, "percent": 5},
                    {"type": "seasonal", "percent": random.choice([10, 15, 20])},
                ]
                if random.random() > 0.5
                else []
            ),
        }

        return {
            "itemId": item_id,
            "description": self.fake.catch_phrase(),
            "warehouses": warehouses,
            "transactions": transactions,
            "pricing": pricing,
        }

    def generate_all(self, connection: Any):
        """Generate all data for Workload 2.

        Args:
            connection: Oracle database connection
        """
        logger.info("Starting Workload 2 data generation...")
        self.generate_inventory_items(connection)
        logger.info("Workload 2 data generation complete")

    def _insert_item_batch(self, cursor: Any, items: list):
        """Insert batch of inventory items."""
        cursor.executemany(
            """
            INSERT INTO inventory_items (item_id, inventory_doc, last_updated)
            VALUES (:item_id, :inventory_doc, SYSTIMESTAMP)
            """,
            items,
        )
