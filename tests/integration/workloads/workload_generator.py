"""Synthetic workload generator for IRIS testing.

This module generates realistic SQL workloads and synthetic AWR-style data
for testing the end-to-end recommendation pipeline.
"""

from dataclasses import dataclass
from typing import List

from src.recommendation.models import JoinInfo, QueryPattern, WorkloadFeatures


@dataclass
class WorkloadConfig:
    """Configuration for generating a synthetic workload.

    Attributes:
        name: Workload name
        description: What this workload represents
        query_patterns: Query patterns to generate
        total_executions: Total query executions in snapshot period
        duration_hours: Snapshot duration in hours
    """

    name: str
    description: str
    query_patterns: List["QueryPatternConfig"]
    total_executions: int
    duration_hours: float = 1.0


@dataclass
class QueryPatternConfig:
    """Configuration for a single query pattern.

    Attributes:
        sql_template: SQL query template
        query_type: Query type (SELECT, INSERT, UPDATE, DELETE)
        tables: Tables accessed by this query
        executions_percentage: Percentage of total executions
        avg_elapsed_time_ms: Average elapsed time in milliseconds
        join_count: Number of joins
        joins: Join information (if applicable)
    """

    sql_template: str
    query_type: str
    tables: List[str]
    executions_percentage: float
    avg_elapsed_time_ms: float
    join_count: int = 0
    joins: List[JoinInfo] = None


def generate_workload(config: WorkloadConfig) -> WorkloadFeatures:
    """Generate synthetic workload from configuration.

    Args:
        config: Workload configuration

    Returns:
        WorkloadFeatures with generated query patterns
    """
    queries: List[QueryPattern] = []
    query_id_counter = 1

    for pattern_config in config.query_patterns:
        executions = int(config.total_executions * pattern_config.executions_percentage / 100)

        if executions == 0:
            continue

        query = QueryPattern(
            query_id=f"sql_{query_id_counter:06d}",
            sql_text=pattern_config.sql_template,
            query_type=pattern_config.query_type,
            executions=executions,
            avg_elapsed_time_ms=pattern_config.avg_elapsed_time_ms,
            tables=pattern_config.tables,
            join_count=pattern_config.join_count,
            joins=pattern_config.joins or [],
        )
        queries.append(query)
        query_id_counter += 1

    return WorkloadFeatures(
        queries=queries,
        total_executions=config.total_executions,
        unique_patterns=len(queries),
    )


# ============================================================================
# Scenario 1.1: E-Commerce with Expensive Joins
# ============================================================================

ECOMMERCE_WORKLOAD = WorkloadConfig(
    name="ecommerce_expensive_joins",
    description="80% of queries join orders to customers for name and tier",
    total_executions=10000,
    query_patterns=[
        # Main pattern: Expensive join to fetch customer name and tier
        QueryPatternConfig(
            sql_template=(
                "SELECT o.ORDER_ID, o.ORDER_DATE, o.TOTAL_AMOUNT, "
                "c.CUSTOMER_NAME, c.CUSTOMER_TIER "
                "FROM ORDERS o JOIN CUSTOMERS c ON o.CUSTOMER_ID = c.CUSTOMER_ID "
                "WHERE o.ORDER_STATUS = 'PENDING'"
            ),
            query_type="SELECT",
            tables=["ORDERS", "CUSTOMERS"],
            executions_percentage=80.0,
            avg_elapsed_time_ms=15.0,
            join_count=1,
            joins=[
                JoinInfo(
                    left_table="ORDERS",
                    right_table="CUSTOMERS",
                    columns_fetched=["CUSTOMER_NAME", "CUSTOMER_TIER"],
                    join_type="INNER",
                )
            ],
        ),
        # Other queries (inserts, updates)
        QueryPatternConfig(
            sql_template="INSERT INTO ORDERS VALUES (:1, :2, :3, :4, :5, :6)",
            query_type="INSERT",
            tables=["ORDERS"],
            executions_percentage=15.0,
            avg_elapsed_time_ms=2.0,
        ),
        QueryPatternConfig(
            sql_template="UPDATE ORDERS SET ORDER_STATUS = :1 WHERE ORDER_ID = :2",
            query_type="UPDATE",
            tables=["ORDERS"],
            executions_percentage=5.0,
            avg_elapsed_time_ms=3.0,
        ),
    ],
)

# ============================================================================
# Scenario 1.2: Document Storage Anti-Pattern
# ============================================================================

USER_PROFILE_WORKLOAD = WorkloadConfig(
    name="user_profiles_document_candidate",
    description="90% SELECT * queries indicating object access pattern",
    total_executions=20000,
    query_patterns=[
        # SELECT * - object access pattern
        QueryPatternConfig(
            sql_template="SELECT * FROM USER_PROFILES WHERE USER_ID = :1",
            query_type="SELECT",
            tables=["USER_PROFILES"],
            executions_percentage=90.0,
            avg_elapsed_time_ms=2.0,
        ),
        # Multi-column updates
        QueryPatternConfig(
            sql_template=(
                "UPDATE USER_PROFILES SET AVATAR_URL = :1, BIO = :2, "
                "LOCATION = :3, TIMEZONE = :4 WHERE USER_ID = :5"
            ),
            query_type="UPDATE",
            tables=["USER_PROFILES"],
            executions_percentage=7.0,
            avg_elapsed_time_ms=4.0,
        ),
        # Single column read
        QueryPatternConfig(
            sql_template="SELECT EMAIL FROM USER_PROFILES WHERE USERNAME = :1",
            query_type="SELECT",
            tables=["USER_PROFILES"],
            executions_percentage=3.0,
            avg_elapsed_time_ms=1.5,
        ),
    ],
)

# ============================================================================
# Scenario 1.3: LOB Cliff Anti-Pattern
# ============================================================================

AUDIT_LOG_WORKLOAD = WorkloadConfig(
    name="audit_logs_lob_cliff",
    description="Frequent small updates to status field in large JSON documents",
    total_executions=15000,
    query_patterns=[
        # Small selective updates to STATUS field within large PAYLOAD
        QueryPatternConfig(
            sql_template="UPDATE AUDIT_LOGS SET STATUS = :1 WHERE LOG_ID = :2",
            query_type="UPDATE",
            tables=["AUDIT_LOGS"],
            executions_percentage=35.0,  # 500/day equivalent in 1-hour snapshot
            avg_elapsed_time_ms=3.0,
        ),
        # Insert full audit log entries
        QueryPatternConfig(
            sql_template=(
                "INSERT INTO AUDIT_LOGS (LOG_ID, TIMESTAMP, USER_ID, "
                "ACTION_TYPE, STATUS, PAYLOAD, IP_ADDRESS) VALUES (:1, :2, :3, :4, :5, :6, :7)"
            ),
            query_type="INSERT",
            tables=["AUDIT_LOGS"],
            executions_percentage=40.0,
            avg_elapsed_time_ms=5.0,
        ),
        # Read queries
        QueryPatternConfig(
            sql_template="SELECT * FROM AUDIT_LOGS WHERE USER_ID = :1 AND TIMESTAMP > :2",
            query_type="SELECT",
            tables=["AUDIT_LOGS"],
            executions_percentage=25.0,
            avg_elapsed_time_ms=8.0,
        ),
    ],
)

# ============================================================================
# Scenario 1.4: Duality View Opportunity
# ============================================================================

PRODUCT_CATALOG_WORKLOAD = WorkloadConfig(
    name="product_catalog_duality",
    description="Balanced OLTP and Analytics access patterns",
    total_executions=10000,
    query_patterns=[
        # OLTP: Insert new products
        QueryPatternConfig(
            sql_template=(
                "INSERT INTO PRODUCTS (PRODUCT_ID, SKU, NAME, DESCRIPTION, "
                "CATEGORY, PRICE, STOCK_QUANTITY, SUPPLIER_ID, CREATED_DATE, LAST_UPDATED) "
                "VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)"
            ),
            query_type="INSERT",
            tables=["PRODUCTS"],
            executions_percentage=20.0,
            avg_elapsed_time_ms=2.0,
        ),
        # OLTP: Update stock
        QueryPatternConfig(
            sql_template="UPDATE PRODUCTS SET STOCK_QUANTITY = :1 WHERE PRODUCT_ID = :2",
            query_type="UPDATE",
            tables=["PRODUCTS"],
            executions_percentage=15.0,
            avg_elapsed_time_ms=1.5,
        ),
        # OLTP: Simple SELECT by ID
        QueryPatternConfig(
            sql_template="SELECT * FROM PRODUCTS WHERE PRODUCT_ID = :1",
            query_type="SELECT",
            tables=["PRODUCTS"],
            executions_percentage=5.0,
            avg_elapsed_time_ms=1.0,
        ),
        # Analytics: Aggregates by category
        QueryPatternConfig(
            sql_template=(
                "SELECT CATEGORY, COUNT(*), AVG(PRICE), SUM(STOCK_QUANTITY) "
                "FROM PRODUCTS GROUP BY CATEGORY"
            ),
            query_type="SELECT",
            tables=["PRODUCTS"],
            executions_percentage=25.0,
            avg_elapsed_time_ms=50.0,
        ),
        # Analytics: Price analysis
        QueryPatternConfig(
            sql_template="SELECT AVG(PRICE), MAX(PRICE), MIN(PRICE) FROM PRODUCTS WHERE CATEGORY = :1",
            query_type="SELECT",
            tables=["PRODUCTS"],
            executions_percentage=10.0,
            avg_elapsed_time_ms=30.0,
        ),
        # Other reads
        QueryPatternConfig(
            sql_template="SELECT NAME, PRICE FROM PRODUCTS WHERE CATEGORY = :1",
            query_type="SELECT",
            tables=["PRODUCTS"],
            executions_percentage=25.0,
            avg_elapsed_time_ms=10.0,
        ),
    ],
)

# ============================================================================
# Scenario 3.1: LOB Cliff FALSE POSITIVE - Cached Read-Heavy
# ============================================================================

DOCUMENT_REPO_WORKLOAD = WorkloadConfig(
    name="document_repo_cached_reads",
    description="Large documents with infrequent updates but heavy reads",
    total_executions=50000,
    query_patterns=[
        # Very infrequent updates (10/day = 0.02% of 50,000)
        QueryPatternConfig(
            sql_template="UPDATE DOCUMENTS SET VERSION = :1 WHERE DOCUMENT_ID = :2",
            query_type="UPDATE",
            tables=["DOCUMENTS"],
            executions_percentage=0.02,  # Only 10 updates in entire snapshot
            avg_elapsed_time_ms=5.0,
        ),
        # Heavy read load
        QueryPatternConfig(
            sql_template="SELECT * FROM DOCUMENTS WHERE DOCUMENT_ID = :1",
            query_type="SELECT",
            tables=["DOCUMENTS"],
            executions_percentage=99.98,
            avg_elapsed_time_ms=0.5,  # Fast due to caching
        ),
    ],
)

# ============================================================================
# Scenario 3.2: Join Denormalization FALSE POSITIVE - Volatile Dimension
# ============================================================================

ORDERS_VOLATILE_PRODUCTS_WORKLOAD = WorkloadConfig(
    name="orders_volatile_products",
    description="Frequent join but product prices update frequently",
    total_executions=20000,
    query_patterns=[
        # Expensive join (70% of queries)
        QueryPatternConfig(
            sql_template=(
                "SELECT o.ORDER_ID, o.QUANTITY, p.PRODUCT_NAME, p.CURRENT_PRICE "
                "FROM ORDERS o JOIN PRODUCTS p ON o.PRODUCT_ID = p.PRODUCT_ID "
                "WHERE o.CUSTOMER_ID = :1"
            ),
            query_type="SELECT",
            tables=["ORDERS", "PRODUCTS"],
            executions_percentage=70.0,
            avg_elapsed_time_ms=20.0,
            join_count=1,
            joins=[
                JoinInfo(
                    left_table="ORDERS",
                    right_table="PRODUCTS",
                    columns_fetched=["PRODUCT_NAME", "CURRENT_PRICE"],
                    join_type="INNER",
                )
            ],
        ),
        # Frequent product price updates (25% = 500/day)
        QueryPatternConfig(
            sql_template="UPDATE PRODUCTS SET CURRENT_PRICE = :1 WHERE PRODUCT_ID = :2",
            query_type="UPDATE",
            tables=["PRODUCTS"],
            executions_percentage=25.0,
            avg_elapsed_time_ms=2.0,
        ),
        # Other queries
        QueryPatternConfig(
            sql_template="INSERT INTO ORDERS VALUES (:1, :2, :3, :4, :5)",
            query_type="INSERT",
            tables=["ORDERS"],
            executions_percentage=5.0,
            avg_elapsed_time_ms=2.0,
        ),
    ],
)

# ============================================================================
# Scenario 3.3: Document Storage FALSE POSITIVE - Mixed Access
# ============================================================================

EVENT_LOG_WORKLOAD = WorkloadConfig(
    name="event_logs_mixed_access",
    description="Mixed object access and aggregations - neutral case",
    total_executions=30000,
    query_patterns=[
        # SELECT * (40%)
        QueryPatternConfig(
            sql_template="SELECT * FROM EVENT_LOGS WHERE EVENT_ID = :1",
            query_type="SELECT",
            tables=["EVENT_LOGS"],
            executions_percentage=40.0,
            avg_elapsed_time_ms=2.0,
        ),
        # Aggregates (45%)
        QueryPatternConfig(
            sql_template="SELECT EVENT_TYPE, COUNT(*) FROM EVENT_LOGS GROUP BY EVENT_TYPE",
            query_type="SELECT",
            tables=["EVENT_LOGS"],
            executions_percentage=30.0,
            avg_elapsed_time_ms=100.0,
        ),
        QueryPatternConfig(
            sql_template="SELECT COUNT(*), AVG(1) FROM EVENT_LOGS WHERE COUNTRY = :1",
            query_type="SELECT",
            tables=["EVENT_LOGS"],
            executions_percentage=15.0,
            avg_elapsed_time_ms=80.0,
        ),
        # Inserts
        QueryPatternConfig(
            sql_template=(
                "INSERT INTO EVENT_LOGS (EVENT_ID, EVENT_TYPE, USER_ID, SESSION_ID, "
                "TIMESTAMP, PROPERTIES, DEVICE_TYPE, COUNTRY) VALUES (:1, :2, :3, :4, :5, :6, :7, :8)"
            ),
            query_type="INSERT",
            tables=["EVENT_LOGS"],
            executions_percentage=15.0,
            avg_elapsed_time_ms=3.0,
        ),
    ],
)

# ============================================================================
# Scenario 3.4: Duality View FALSE POSITIVE - Low Volume
# ============================================================================

ADMIN_CONFIG_WORKLOAD = WorkloadConfig(
    name="admin_config_low_volume",
    description="Balanced OLTP/Analytics but very low volume",
    total_executions=50,  # Very low volume
    query_patterns=[
        # OLTP updates (30%)
        QueryPatternConfig(
            sql_template="UPDATE ADMIN_CONFIG SET CONFIG_VALUE = :1 WHERE CONFIG_KEY = :2",
            query_type="UPDATE",
            tables=["ADMIN_CONFIG"],
            executions_percentage=30.0,
            avg_elapsed_time_ms=1.0,
        ),
        # Analytics aggregates (25%)
        QueryPatternConfig(
            sql_template="SELECT CATEGORY, COUNT(*) FROM ADMIN_CONFIG GROUP BY CATEGORY",
            query_type="SELECT",
            tables=["ADMIN_CONFIG"],
            executions_percentage=25.0,
            avg_elapsed_time_ms=5.0,
        ),
        # Simple reads (45%)
        QueryPatternConfig(
            sql_template="SELECT CONFIG_VALUE FROM ADMIN_CONFIG WHERE CONFIG_KEY = :1",
            query_type="SELECT",
            tables=["ADMIN_CONFIG"],
            executions_percentage=45.0,
            avg_elapsed_time_ms=0.5,
        ),
    ],
)

# ============================================================================
# Scenario 3.5: Selective LOB Update with High Selectivity
# ============================================================================

PRODUCT_CATALOG_LOB_WORKLOAD = WorkloadConfig(
    name="product_catalog_lob_cliff",
    description="Large image metadata with selective price updates",
    total_executions=15000,
    query_patterns=[
        # Small selective updates to PRICE field (200/day = ~8 per hour = ~13%)
        QueryPatternConfig(
            sql_template="UPDATE PRODUCTS SET PRICE = :1 WHERE PRODUCT_ID = :2",
            query_type="UPDATE",
            tables=["PRODUCTS"],
            executions_percentage=13.3,  # 200/day equivalent
            avg_elapsed_time_ms=2.0,
        ),
        # Read IMAGE_METADATA
        QueryPatternConfig(
            sql_template="SELECT IMAGE_METADATA FROM PRODUCTS WHERE PRODUCT_ID = :1",
            query_type="SELECT",
            tables=["PRODUCTS"],
            executions_percentage=70.0,
            avg_elapsed_time_ms=5.0,
        ),
        # Inserts
        QueryPatternConfig(
            sql_template=(
                "INSERT INTO PRODUCTS (PRODUCT_ID, NAME, IMAGE_METADATA, PRICE, STOCK) "
                "VALUES (:1, :2, :3, :4, :5)"
            ),
            query_type="INSERT",
            tables=["PRODUCTS"],
            executions_percentage=16.7,
            avg_elapsed_time_ms=8.0,
        ),
    ],
)

# ============================================================================
# Scenario 3.6: Join with Many Columns
# ============================================================================

ORDERS_PREFERENCES_WORKLOAD = WorkloadConfig(
    name="orders_customer_preferences",
    description="Join fetching many columns from customer preferences",
    total_executions=10000,
    query_patterns=[
        # Join fetching 15 columns (exceeds 5-column threshold)
        QueryPatternConfig(
            sql_template=(
                "SELECT o.ORDER_ID, p.PREF_COMMUNICATION, p.PREF_MARKETING, "
                "p.PREF_NEWSLETTER, p.PREF_NOTIFICATIONS, p.PREF_PRIVACY "
                "FROM ORDERS o JOIN CUSTOMER_PREFERENCES p ON o.CUSTOMER_ID = p.CUSTOMER_ID "
                "WHERE o.ORDER_DATE > :1"
            ),
            query_type="SELECT",
            tables=["ORDERS", "CUSTOMER_PREFERENCES"],
            executions_percentage=60.0,
            avg_elapsed_time_ms=25.0,
            join_count=1,
            joins=[
                JoinInfo(
                    left_table="ORDERS",
                    right_table="CUSTOMER_PREFERENCES",
                    columns_fetched=[
                        "PREF_COMMUNICATION",
                        "PREF_MARKETING",
                        "PREF_NEWSLETTER",
                        "PREF_NOTIFICATIONS",
                        "PREF_PRIVACY",
                        "PREF_LANGUAGE",
                        "PREF_TIMEZONE",
                        "PREF_CURRENCY",
                        "PREF_EMAIL_FREQ",
                        "PREF_SMS_OPT_IN",
                        "PREF_PUSH_NOTIF",
                        "PREF_DATA_SHARING",
                        "PREF_ANALYTICS",
                        "PREF_THIRD_PARTY",
                        "PREF_RECOMMENDATIONS",
                    ],
                    join_type="INNER",
                )
            ],
        ),
        # Other queries
        QueryPatternConfig(
            sql_template="INSERT INTO ORDERS VALUES (:1, :2, :3, :4)",
            query_type="INSERT",
            tables=["ORDERS"],
            executions_percentage=30.0,
            avg_elapsed_time_ms=2.0,
        ),
        QueryPatternConfig(
            sql_template="SELECT * FROM ORDERS WHERE ORDER_ID = :1",
            query_type="SELECT",
            tables=["ORDERS"],
            executions_percentage=10.0,
            avg_elapsed_time_ms=1.0,
        ),
    ],
)


# All workloads for easy access
ALL_WORKLOADS = [
    ECOMMERCE_WORKLOAD,
    USER_PROFILE_WORKLOAD,
    AUDIT_LOG_WORKLOAD,
    PRODUCT_CATALOG_WORKLOAD,
    DOCUMENT_REPO_WORKLOAD,
    ORDERS_VOLATILE_PRODUCTS_WORKLOAD,
    EVENT_LOG_WORKLOAD,
    ADMIN_CONFIG_WORKLOAD,
    PRODUCT_CATALOG_LOB_WORKLOAD,
    ORDERS_PREFERENCES_WORKLOAD,
]
