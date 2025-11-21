"""Pytest configuration and fixtures for simulation tests."""

import os

import oracledb
import pytest


@pytest.fixture(scope="session")
def oracle_connection_string():
    """Get Oracle connection string from environment or use default.

    Returns:
        Connection string for Oracle database
    """
    # Try environment variables first
    user = os.getenv("ORACLE_USER", "iris_user")
    password = os.getenv("ORACLE_PASSWORD", "IrisUser123!")
    dsn = os.getenv("ORACLE_DSN", "localhost:1524/FREEPDB1")

    return f"{user}/{password}@{dsn}"


@pytest.fixture(scope="session")
def oracle_connection(oracle_connection_string):
    """Create Oracle database connection for tests.

    Yields:
        Oracle database connection

    Note:
        This is a session-scoped fixture, so the connection is reused
        across all tests in the session.
    """
    # Parse connection string
    if "@" in oracle_connection_string:
        creds, dsn = oracle_connection_string.split("@")
        user, password = creds.split("/")
    else:
        raise ValueError(f"Invalid connection string: {oracle_connection_string}")

    # Create connection
    connection = oracledb.connect(user=user, password=password, dsn=dsn)

    yield connection

    # Cleanup
    connection.close()


@pytest.fixture(scope="function")
def clean_workload_schemas(oracle_connection):
    """Clean up workload schemas before and after each test.

    Args:
        oracle_connection: Oracle database connection

    Yields:
        None
    """
    # Cleanup before test
    _cleanup_schemas(oracle_connection)

    yield

    # Cleanup after test
    _cleanup_schemas(oracle_connection)


def _cleanup_schemas(connection):
    """Clean up all workload schemas.

    Args:
        connection: Oracle database connection
    """
    cursor = connection.cursor()

    # Workload 1: E-Commerce
    tables_w1 = [
        "customer_order_history",
        "customer_preferences",
        "customer_addresses",
        "customers",
    ]
    sequences_w1 = ["seq_customer_id", "seq_address_id", "seq_pref_id", "seq_order_id"]

    # Workload 2: Inventory
    tables_w2 = ["inventory_items"]
    sequences_w2 = ["seq_item_id"]

    # Workload 3: Orders
    tables_w3 = ["order_payments", "order_items", "orders"]
    sequences_w3 = ["seq_order_id", "seq_item_id", "seq_payment_id"]

    all_tables = tables_w1 + tables_w2 + tables_w3
    all_sequences = sequences_w1 + sequences_w2 + sequences_w3

    # Drop tables
    for table in all_tables:
        try:
            cursor.execute(f"DROP TABLE {table} CASCADE CONSTRAINTS")
        except Exception:
            pass  # Table may not exist

    # Drop sequences
    for seq in all_sequences:
        try:
            cursor.execute(f"DROP SEQUENCE {seq}")
        except Exception:
            pass  # Sequence may not exist

    connection.commit()


@pytest.fixture
def skip_if_no_awr(oracle_connection):
    """Skip test if AWR is not available.

    Args:
        oracle_connection: Oracle database connection

    Raises:
        pytest.skip: If AWR is not enabled
    """
    cursor = oracle_connection.cursor()

    try:
        # Check if we can access AWR views
        cursor.execute("SELECT COUNT(*) FROM DBA_HIST_SNAPSHOT WHERE ROWNUM = 1")
        cursor.fetchone()

        # Check if statistics_level is appropriate
        cursor.execute(
            """
            SELECT value
            FROM SYS.V_$PARAMETER
            WHERE name = 'statistics_level'
            """
        )

        result = cursor.fetchone()

        if not result or result[0] not in ("TYPICAL", "ALL"):
            pytest.skip(f"AWR not enabled (statistics_level={result[0] if result else 'UNKNOWN'})")

    except Exception as e:
        pytest.skip(f"Cannot access AWR views: {e}")
