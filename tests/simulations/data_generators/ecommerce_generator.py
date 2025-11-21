"""Data generator for Workload 1: E-Commerce User Profiles.

Generates realistic customer data with addresses, preferences, and order history
to populate the relational schema that should be recommended for document storage.
"""

import logging
import random
from typing import Any

from faker import Faker

logger = logging.getLogger(__name__)


class ECommerceDataGenerator:
    """Generates e-commerce customer profile data."""

    def __init__(self, num_customers: int = 1000, seed: int = 42):
        """Initialize data generator.

        Args:
            num_customers: Number of customers to generate
            seed: Random seed for reproducibility
        """
        self.num_customers = num_customers
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)

        # Realistic distributions
        self.loyalty_tiers = ["BRONZE", "SILVER", "GOLD", "PLATINUM"]
        self.tier_weights = [0.60, 0.25, 0.10, 0.05]  # Most customers are BRONZE

        self.address_types = ["billing", "shipping", "both"]
        self.pref_categories = [
            "communication",
            "newsletter",
            "marketing",
            "notifications",
            "privacy",
        ]
        self.pref_values = {
            "communication": ["email", "sms", "both", "none"],
            "newsletter": ["daily", "weekly", "monthly", "never"],
            "marketing": ["all", "personalized", "minimal", "none"],
            "notifications": ["all", "important", "minimal", "none"],
            "privacy": ["public", "friends", "private"],
        }

        self.order_statuses = ["COMPLETED", "CANCELLED", "RETURNED"]
        self.status_weights = [0.85, 0.10, 0.05]  # Most orders complete successfully

    def generate_customers(self, connection: Any, batch_size: int = 1000):
        """Generate and insert customer records.

        Args:
            connection: Oracle database connection
            batch_size: Number of records to insert per batch
        """
        logger.info(f"Generating {self.num_customers} customers...")

        cursor = connection.cursor()
        customers = []

        for i in range(self.num_customers):
            customer = {
                "customer_id": i + 1,
                "email": self.fake.email(),
                "name": self.fake.name(),
                "created_date": self.fake.date_between(start_date="-2y", end_date="today"),
                "loyalty_tier": random.choices(self.loyalty_tiers, weights=self.tier_weights)[0],
            }
            customers.append(customer)

            if len(customers) >= batch_size:
                self._insert_customer_batch(cursor, customers)
                customers = []

        # Insert remaining
        if customers:
            self._insert_customer_batch(cursor, customers)

        connection.commit()
        logger.info(f"Inserted {self.num_customers} customers")

    def generate_addresses(self, connection: Any, batch_size: int = 1000):
        """Generate and insert customer addresses (avg 2.5 per customer).

        Args:
            connection: Oracle database connection
            batch_size: Number of records to insert per batch
        """
        logger.info("Generating customer addresses...")

        cursor = connection.cursor()
        addresses = []
        address_id = 1

        for customer_id in range(1, self.num_customers + 1):
            # Each customer has 2-3 addresses
            num_addresses = random.choices([2, 3], weights=[0.7, 0.3])[0]

            for _ in range(num_addresses):
                address = {
                    "address_id": address_id,
                    "customer_id": customer_id,
                    "address_type": random.choice(["billing", "shipping"]),
                    "street": self.fake.street_address(),
                    "city": self.fake.city(),
                    "state": self.fake.state_abbr(),
                    "zip": self.fake.zipcode(),
                }
                addresses.append(address)
                address_id += 1

                if len(addresses) >= batch_size:
                    self._insert_address_batch(cursor, addresses)
                    addresses = []

        # Insert remaining
        if addresses:
            self._insert_address_batch(cursor, addresses)

        connection.commit()
        logger.info(f"Inserted {address_id - 1} addresses")

    def generate_preferences(self, connection: Any, batch_size: int = 1000):
        """Generate and insert customer preferences (avg 5 per customer).

        Args:
            connection: Oracle database connection
            batch_size: Number of records to insert per batch
        """
        logger.info("Generating customer preferences...")

        cursor = connection.cursor()
        preferences = []
        pref_id = 1

        for customer_id in range(1, self.num_customers + 1):
            # Each customer has preferences for all categories
            for category in self.pref_categories:
                pref = {
                    "pref_id": pref_id,
                    "customer_id": customer_id,
                    "category": category,
                    "preference_value": random.choice(self.pref_values[category]),
                }
                preferences.append(pref)
                pref_id += 1

                if len(preferences) >= batch_size:
                    self._insert_preference_batch(cursor, preferences)
                    preferences = []

        # Insert remaining
        if preferences:
            self._insert_preference_batch(cursor, preferences)

        connection.commit()
        logger.info(f"Inserted {pref_id - 1} preferences")

    def generate_order_history(self, connection: Any, batch_size: int = 1000):
        """Generate and insert order history (avg 10 orders per customer).

        Args:
            connection: Oracle database connection
            batch_size: Number of records to insert per batch
        """
        logger.info("Generating order history...")

        cursor = connection.cursor()
        orders = []
        order_id = 1

        for customer_id in range(1, self.num_customers + 1):
            # Each customer has 5-15 orders
            num_orders = random.randint(5, 15)

            for _ in range(num_orders):
                order = {
                    "order_id": order_id,
                    "customer_id": customer_id,
                    "order_date": self.fake.date_between(start_date="-1y", end_date="today"),
                    "total_amount": round(random.uniform(10.0, 500.0), 2),
                    "status": random.choices(self.order_statuses, weights=self.status_weights)[0],
                }
                orders.append(order)
                order_id += 1

                if len(orders) >= batch_size:
                    self._insert_order_batch(cursor, orders)
                    orders = []

        # Insert remaining
        if orders:
            self._insert_order_batch(cursor, orders)

        connection.commit()
        logger.info(f"Inserted {order_id - 1} orders")

    def generate_all(self, connection: Any):
        """Generate all data for Workload 1.

        Args:
            connection: Oracle database connection
        """
        logger.info("Starting Workload 1 data generation...")
        self.generate_customers(connection)
        self.generate_addresses(connection)
        self.generate_preferences(connection)
        self.generate_order_history(connection)
        logger.info("Workload 1 data generation complete")

    def _insert_customer_batch(self, cursor: Any, customers: list):
        """Insert batch of customers."""
        cursor.executemany(
            """
            INSERT INTO customers (customer_id, email, name, created_date, loyalty_tier)
            VALUES (:customer_id, :email, :name, :created_date, :loyalty_tier)
            """,
            customers,
        )

    def _insert_address_batch(self, cursor: Any, addresses: list):
        """Insert batch of addresses."""
        cursor.executemany(
            """
            INSERT INTO customer_addresses
            (address_id, customer_id, address_type, street, city, state, zip)
            VALUES (:address_id, :customer_id, :address_type, :street, :city, :state, :zip)
            """,
            addresses,
        )

    def _insert_preference_batch(self, cursor: Any, preferences: list):
        """Insert batch of preferences."""
        cursor.executemany(
            """
            INSERT INTO customer_preferences (pref_id, customer_id, category, preference_value)
            VALUES (:pref_id, :customer_id, :category, :preference_value)
            """,
            preferences,
        )

    def _insert_order_batch(self, cursor: Any, orders: list):
        """Insert batch of orders."""
        cursor.executemany(
            """
            INSERT INTO customer_order_history
            (order_id, customer_id, order_date, total_amount, status)
            VALUES (:order_id, :customer_id, :order_date, :total_amount, :status)
            """,
            orders,
        )
