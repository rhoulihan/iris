"""Schema definitions for synthetic workload scenarios.

This module defines database schemas for testing the IRIS recommendation engine
with realistic and edge-case workloads.
"""

from dataclasses import dataclass
from typing import List

from src.recommendation.models import ColumnMetadata, TableMetadata


@dataclass
class SchemaScenario:
    """Defines a complete schema scenario for testing.

    Attributes:
        name: Scenario name
        description: What this scenario tests
        tables: List of tables in this schema
        expected_patterns: Pattern types expected to be detected
    """

    name: str
    description: str
    tables: List[TableMetadata]
    expected_patterns: List[str]


# Scenario 1.1: E-Commerce with Expensive Joins
ECOMMERCE_SCHEMA = SchemaScenario(
    name="ecommerce_expensive_joins",
    description="Normalized e-commerce schema with expensive customer joins",
    tables=[
        TableMetadata(
            name="ORDERS",
            schema="ECOMMERCE",
            num_rows=1000000,
            avg_row_len=150,
            columns=[
                ColumnMetadata(name="ORDER_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="CUSTOMER_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="ORDER_DATE", data_type="DATE", nullable=False),
                ColumnMetadata(name="ORDER_STATUS", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="TOTAL_AMOUNT", data_type="NUMBER", nullable=True),
                ColumnMetadata(name="SHIPPING_ADDRESS_ID", data_type="NUMBER", nullable=True),
            ],
        ),
        TableMetadata(
            name="CUSTOMERS",
            schema="ECOMMERCE",
            num_rows=50000,
            avg_row_len=200,
            columns=[
                ColumnMetadata(name="CUSTOMER_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="CUSTOMER_NAME", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="CUSTOMER_TIER", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="EMAIL", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="PHONE", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="CREATED_DATE", data_type="DATE", nullable=False),
            ],
        ),
        TableMetadata(
            name="PRODUCTS",
            schema="ECOMMERCE",
            num_rows=100000,
            avg_row_len=300,
            columns=[
                ColumnMetadata(name="PRODUCT_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="PRODUCT_NAME", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="CATEGORY", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="PRICE", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="DESCRIPTION", data_type="CLOB", nullable=True, avg_size=2000),
            ],
        ),
    ],
    expected_patterns=["EXPENSIVE_JOIN"],
)

# Scenario 1.2: Document Storage Anti-Pattern
USER_PROFILE_SCHEMA = SchemaScenario(
    name="user_profiles_document_candidate",
    description="User profiles stored as relational but accessed as objects",
    tables=[
        TableMetadata(
            name="USER_PROFILES",
            schema="SAAS",
            num_rows=500000,
            avg_row_len=800,
            columns=[
                ColumnMetadata(name="USER_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="USERNAME", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="EMAIL", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="FIRST_NAME", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="LAST_NAME", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="AVATAR_URL", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="BIO", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="LOCATION", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="TIMEZONE", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="LANGUAGE", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="THEME_PREFERENCE", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="NOTIFICATION_SETTINGS", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="PRIVACY_SETTINGS", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="CUSTOM_FIELD_1", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="CUSTOM_FIELD_2", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="CUSTOM_FIELD_3", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="CUSTOM_FIELD_4", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="CUSTOM_FIELD_5", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="LAST_LOGIN", data_type="DATE", nullable=True),
                ColumnMetadata(name="CREATED_AT", data_type="DATE", nullable=False),
            ],
        ),
    ],
    expected_patterns=["DOCUMENT_CANDIDATE"],
)

# Scenario 1.3: LOB Cliff Anti-Pattern
AUDIT_LOG_SCHEMA = SchemaScenario(
    name="audit_logs_lob_cliff",
    description="Audit logs with large JSON payloads and selective updates",
    tables=[
        TableMetadata(
            name="AUDIT_LOGS",
            schema="SECURITY",
            num_rows=5000000,
            avg_row_len=8500,
            columns=[
                ColumnMetadata(name="LOG_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="TIMESTAMP", data_type="DATE", nullable=False),
                ColumnMetadata(name="USER_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="ACTION_TYPE", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="STATUS", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="PAYLOAD", data_type="CLOB", nullable=False, avg_size=8192),
                ColumnMetadata(name="IP_ADDRESS", data_type="VARCHAR2", nullable=True),
            ],
        ),
    ],
    expected_patterns=["LOB_CLIFF"],
)

# Scenario 1.4: Duality View Opportunity
PRODUCT_CATALOG_SCHEMA = SchemaScenario(
    name="product_catalog_duality",
    description="Product catalog with both OLTP and Analytics access patterns",
    tables=[
        TableMetadata(
            name="PRODUCTS",
            schema="CATALOG",
            num_rows=250000,
            avg_row_len=600,
            columns=[
                ColumnMetadata(name="PRODUCT_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="SKU", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="NAME", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="DESCRIPTION", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="CATEGORY", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="PRICE", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="STOCK_QUANTITY", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="SUPPLIER_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="CREATED_DATE", data_type="DATE", nullable=False),
                ColumnMetadata(name="LAST_UPDATED", data_type="DATE", nullable=False),
            ],
        ),
    ],
    expected_patterns=["DUALITY_VIEW_OPPORTUNITY"],
)

# Scenario 3.1: LOB Cliff FALSE POSITIVE - Cached Read-Heavy
DOCUMENT_REPO_SCHEMA = SchemaScenario(
    name="document_repo_cached_reads",
    description="Document repository with large documents but infrequent updates and high caching",
    tables=[
        TableMetadata(
            name="DOCUMENTS",
            schema="CONTENT",
            num_rows=100000,
            avg_row_len=10500,
            columns=[
                ColumnMetadata(name="DOCUMENT_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="TITLE", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="CONTENT", data_type="JSON", nullable=False, avg_size=10240),
                ColumnMetadata(name="METADATA", data_type="JSON", nullable=True, avg_size=512),
                ColumnMetadata(name="VERSION", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="CREATED_DATE", data_type="DATE", nullable=False),
            ],
        ),
    ],
    expected_patterns=[],  # Should NOT detect LOB_CLIFF due to low update frequency
)

# Scenario 3.2: Join Denormalization FALSE POSITIVE - Volatile Dimension
ORDERS_VOLATILE_PRODUCTS_SCHEMA = SchemaScenario(
    name="orders_volatile_products",
    description="Orders with frequent joins to products, but product prices change frequently",
    tables=[
        TableMetadata(
            name="ORDERS",
            schema="RETAIL",
            num_rows=2000000,
            avg_row_len=120,
            columns=[
                ColumnMetadata(name="ORDER_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="CUSTOMER_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="PRODUCT_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="QUANTITY", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="ORDER_DATE", data_type="DATE", nullable=False),
            ],
        ),
        TableMetadata(
            name="PRODUCTS",
            schema="RETAIL",
            num_rows=100000,
            avg_row_len=250,
            columns=[
                ColumnMetadata(name="PRODUCT_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="PRODUCT_NAME", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="CURRENT_PRICE", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="CATEGORY", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="LAST_PRICE_UPDATE", data_type="DATE", nullable=False),
            ],
        ),
    ],
    expected_patterns=[],  # Should NOT recommend denormalization due to high update rate
)

# Scenario 3.3: Document Storage FALSE POSITIVE - Mixed Access
EVENT_LOG_SCHEMA = SchemaScenario(
    name="event_logs_mixed_access",
    description="Event logs with both object access (SELECT *) and aggregations",
    tables=[
        TableMetadata(
            name="EVENT_LOGS",
            schema="ANALYTICS",
            num_rows=10000000,
            avg_row_len=300,
            columns=[
                ColumnMetadata(name="EVENT_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="EVENT_TYPE", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="USER_ID", data_type="NUMBER", nullable=True),
                ColumnMetadata(name="SESSION_ID", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="TIMESTAMP", data_type="DATE", nullable=False),
                ColumnMetadata(name="PROPERTIES", data_type="JSON", nullable=True, avg_size=512),
                ColumnMetadata(name="DEVICE_TYPE", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="COUNTRY", data_type="VARCHAR2", nullable=True),
            ],
        ),
    ],
    expected_patterns=[],  # Should be neutral - no clear document or relational winner
)

# Scenario 3.4: Duality View FALSE POSITIVE - Low Volume
ADMIN_CONFIG_SCHEMA = SchemaScenario(
    name="admin_config_low_volume",
    description="Admin configuration with balanced OLTP/Analytics but very low volume",
    tables=[
        TableMetadata(
            name="ADMIN_CONFIG",
            schema="SYSTEM",
            num_rows=500,
            avg_row_len=200,
            columns=[
                ColumnMetadata(name="CONFIG_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="CONFIG_KEY", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="CONFIG_VALUE", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="CATEGORY", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(name="LAST_UPDATED", data_type="DATE", nullable=False),
            ],
        ),
    ],
    expected_patterns=["DUALITY_VIEW_OPPORTUNITY"],  # Will detect but LOW severity
)

# Scenario 3.5: Selective LOB Update with High Selectivity (Clear POSITIVE)
PRODUCT_CATALOG_LOB_SCHEMA = SchemaScenario(
    name="product_catalog_lob_cliff",
    description="Product catalog with large image metadata and selective price updates",
    tables=[
        TableMetadata(
            name="PRODUCTS",
            schema="INVENTORY",
            num_rows=500000,
            avg_row_len=12500,
            columns=[
                ColumnMetadata(name="PRODUCT_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="NAME", data_type="VARCHAR2", nullable=False),
                ColumnMetadata(
                    name="IMAGE_METADATA", data_type="CLOB", nullable=False, avg_size=12288
                ),
                ColumnMetadata(name="PRICE", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="STOCK", data_type="NUMBER", nullable=False),
            ],
        ),
    ],
    expected_patterns=["LOB_CLIFF"],  # Should detect with HIGH severity
)

# Scenario 3.6: Join with Many Columns
ORDERS_PREFERENCES_SCHEMA = SchemaScenario(
    name="orders_customer_preferences",
    description="Orders join to customer preferences fetching many columns",
    tables=[
        TableMetadata(
            name="ORDERS",
            schema="SALES",
            num_rows=1000000,
            avg_row_len=100,
            columns=[
                ColumnMetadata(name="ORDER_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="CUSTOMER_ID", data_type="NUMBER", nullable=False),
                ColumnMetadata(name="ORDER_DATE", data_type="DATE", nullable=False),
                ColumnMetadata(name="TOTAL", data_type="NUMBER", nullable=False),
            ],
        ),
        TableMetadata(
            name="CUSTOMER_PREFERENCES",
            schema="SALES",
            num_rows=10000,
            avg_row_len=2000,
            columns=[
                ColumnMetadata(name="CUSTOMER_ID", data_type="NUMBER", nullable=False),
                # 50 preference columns (simulated)
                ColumnMetadata(name="PREF_COMMUNICATION", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="PREF_MARKETING", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="PREF_NEWSLETTER", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="PREF_NOTIFICATIONS", data_type="VARCHAR2", nullable=True),
                ColumnMetadata(name="PREF_PRIVACY", data_type="VARCHAR2", nullable=True),
                # ... (would have 45 more in reality)
            ],
        ),
    ],
    expected_patterns=[],  # Should NOT recommend due to too many columns
)


# All scenarios for easy access
ALL_SCENARIOS = [
    ECOMMERCE_SCHEMA,
    USER_PROFILE_SCHEMA,
    AUDIT_LOG_SCHEMA,
    PRODUCT_CATALOG_SCHEMA,
    DOCUMENT_REPO_SCHEMA,
    ORDERS_VOLATILE_PRODUCTS_SCHEMA,
    EVENT_LOG_SCHEMA,
    ADMIN_CONFIG_SCHEMA,
    PRODUCT_CATALOG_LOB_SCHEMA,
    ORDERS_PREFERENCES_SCHEMA,
]
