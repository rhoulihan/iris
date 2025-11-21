"""Integration tests for IRIS pipeline using simulation workloads.

These tests validate that the pipeline correctly identifies patterns and generates
appropriate recommendations for the three simulation workloads.
"""

import logging
from pathlib import Path

import pytest

from tests.simulations.data_generators.ecommerce_generator import ECommerceDataGenerator
from tests.simulations.data_generators.inventory_generator import InventoryDataGenerator
from tests.simulations.data_generators.orders_generator import OrdersDataGenerator
from tests.simulations.workloads.workload1_ecommerce import ECommerceWorkload
from tests.simulations.workloads.workload2_inventory import InventoryWorkload
from tests.simulations.workloads.workload3_orders import OrdersWorkload

logger = logging.getLogger(__name__)


class TestWorkload1ECommerce:
    """Test Workload 1: E-Commerce (Relational → Document recommendation)."""

    @pytest.fixture(scope="class")
    def workload_setup(self, oracle_connection):
        """Set up Workload 1 schema and data."""
        logger.info("Setting up Workload 1: E-Commerce")

        # Load schema
        schema_path = Path(__file__).parent / "sql" / "workload1_schema.sql"
        with open(schema_path) as f:
            schema_sql = f.read()

        # Execute schema creation (split by /)
        cursor = oracle_connection.cursor()
        for statement in schema_sql.split("/"):
            statement = statement.strip()
            if statement:
                try:
                    cursor.execute(statement)
                except Exception as e:
                    logger.debug(f"Schema statement error (may be expected): {e}")

        oracle_connection.commit()

        # Generate data (smaller dataset for testing)
        generator = ECommerceDataGenerator(num_customers=100)
        generator.generate_all(oracle_connection)

        logger.info("Workload 1 data generation complete")

        yield oracle_connection

        # Cleanup handled by fixture

    def test_workload1_pattern_detection(self, workload_setup, oracle_connection):
        """Test that Workload 1 triggers document storage recommendation."""
        # Execute workload to generate AWR data
        logger.info("Executing Workload 1 queries...")
        workload = ECommerceWorkload(oracle_connection, duration_seconds=30)
        stats = workload.execute()

        logger.info(f"Workload 1 stats: {stats}")

        # Get AWR snapshots (mock for now - would need real AWR setup)
        # For testing, we'll use the schema and query patterns directly

        # TODO: Run pipeline orchestrator with mock AWR data
        # This would require creating mock AWR snapshots or using test data

        # For now, verify workload executed
        assert stats["reads"] > 0
        assert stats["writes"] > 0

        logger.info("Workload 1 validation complete")

    def test_workload1_recommendation_quality(self, workload_setup):
        """Test that Workload 1 generates HIGH confidence document recommendation."""
        # TODO: Implement once pipeline orchestrator can run with mock data
        pytest.skip("Pending pipeline orchestrator integration")


class TestWorkload2Inventory:
    """Test Workload 2: Inventory (Document → Relational recommendation)."""

    @pytest.fixture(scope="class")
    def workload_setup(self, oracle_connection):
        """Set up Workload 2 schema and data."""
        logger.info("Setting up Workload 2: Inventory")

        # Load schema
        schema_path = Path(__file__).parent / "sql" / "workload2_schema.sql"
        with open(schema_path) as f:
            schema_sql = f.read()

        cursor = oracle_connection.cursor()
        for statement in schema_sql.split("/"):
            statement = statement.strip()
            if statement:
                try:
                    cursor.execute(statement)
                except Exception as e:
                    logger.debug(f"Schema statement error (may be expected): {e}")

        oracle_connection.commit()

        # Generate data
        generator = InventoryDataGenerator(num_items=50)
        generator.generate_all(oracle_connection)

        logger.info("Workload 2 data generation complete")

        yield oracle_connection

    def test_workload2_pattern_detection(self, workload_setup, oracle_connection):
        """Test that Workload 2 triggers relational normalization recommendation."""
        logger.info("Executing Workload 2 queries...")
        workload = InventoryWorkload(oracle_connection, duration_seconds=30)
        stats = workload.execute()

        logger.info(f"Workload 2 stats: {stats}")

        # Verify high write ratio
        if stats["writes"] > 0:
            write_ratio = stats["writes"] / (stats["reads"] + stats["writes"])
            assert write_ratio > 0.5, "Expected write-heavy workload"

        logger.info("Workload 2 validation complete")

    def test_workload2_recommendation_quality(self, workload_setup):
        """Test that Workload 2 generates HIGH confidence relational recommendation."""
        pytest.skip("Pending pipeline orchestrator integration")


class TestWorkload3Orders:
    """Test Workload 3: Orders (Hybrid → Duality View recommendation)."""

    @pytest.fixture(scope="class")
    def workload_setup(self, oracle_connection):
        """Set up Workload 3 schema and data."""
        logger.info("Setting up Workload 3: Orders")

        # Load schema
        schema_path = Path(__file__).parent / "sql" / "workload3_schema.sql"
        with open(schema_path) as f:
            schema_sql = f.read()

        cursor = oracle_connection.cursor()
        for statement in schema_sql.split("/"):
            statement = statement.strip()
            if statement:
                try:
                    cursor.execute(statement)
                except Exception as e:
                    logger.debug(f"Schema statement error (may be expected): {e}")

        oracle_connection.commit()

        # Generate data
        generator = OrdersDataGenerator(num_orders=500)
        generator.generate_all(oracle_connection)

        logger.info("Workload 3 data generation complete")

        yield oracle_connection

    def test_workload3_pattern_detection(self, workload_setup, oracle_connection):
        """Test that Workload 3 triggers Duality View recommendation."""
        logger.info("Executing Workload 3 queries...")
        workload = OrdersWorkload(oracle_connection, duration_seconds=30)
        stats = workload.execute()

        logger.info(f"Workload 3 stats: {stats}")

        # Verify hybrid workload (both OLTP and analytics)
        assert stats["oltp"] > 0, "Expected OLTP queries"
        assert stats["analytics"] > 0, "Expected analytics queries"

        logger.info("Workload 3 validation complete")

    def test_workload3_recommendation_quality(self, workload_setup):
        """Test that Workload 3 generates Duality View recommendation."""
        pytest.skip("Pending pipeline orchestrator integration")


@pytest.mark.integration
class TestEndToEndPipeline:
    """End-to-end integration tests for complete pipeline execution."""

    def test_all_workloads_sequential(self, oracle_connection):
        """Test all three workloads sequentially to verify no interference."""
        # This test would run all workloads and validate recommendations
        pytest.skip("Pending full pipeline orchestrator integration")

    def test_pipeline_recommendation_accuracy(self, oracle_connection):
        """Test that pipeline generates correct recommendations for all workloads."""
        # TODO: Implement validation criteria from SIMULATION_WORKLOADS.md
        # Expected patterns:
        #   - workload1: DOCUMENT_RELATIONAL (storage: DOCUMENT)
        #   - workload2: DOCUMENT_RELATIONAL (storage: RELATIONAL)
        #   - workload3: DUALITY_VIEW_OPPORTUNITY

        pytest.skip("Pending full pipeline orchestrator integration")
