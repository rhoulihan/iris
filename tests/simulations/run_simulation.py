#!/usr/bin/env python3
"""CLI entry point for running IRIS pipeline simulations.

This script orchestrates the complete simulation workflow:
1. Schema creation
2. Data generation
3. Workload execution
4. Pipeline analysis
5. Recommendation validation

Usage:
    python run_simulation.py --workload 1 --duration 300
    python run_simulation.py --workload all --skip-data-gen
"""

import argparse
import logging
import sys
from pathlib import Path

import oracledb

from src.pipeline.orchestrator import PipelineConfig, PipelineOrchestrator
from tests.simulations.awr_helper import AWRSnapshotHelper
from tests.simulations.data_generators.ecommerce_generator import ECommerceDataGenerator
from tests.simulations.data_generators.inventory_generator import InventoryDataGenerator
from tests.simulations.data_generators.orders_generator import OrdersDataGenerator
from tests.simulations.recommendation_validator import RecommendationValidator
from tests.simulations.workloads.workload1_ecommerce import ECommerceWorkload
from tests.simulations.workloads.workload2_inventory import InventoryWorkload
from tests.simulations.workloads.workload3_orders import OrdersWorkload

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SimulationRunner:
    """Orchestrates simulation workflow."""

    def __init__(self, connection_string: str):
        """Initialize simulation runner.

        Args:
            connection_string: Oracle connection string (user/password@host:port/service)
        """
        self.connection_string = connection_string
        self.connection = None

    def connect(self):
        """Establish database connection."""
        logger.info("Connecting to Oracle database...")

        # Parse connection string (format: user/password@host:port/service)
        try:
            if "@" in self.connection_string:
                creds, dsn = self.connection_string.split("@")
                user, password = creds.split("/")
                self.connection = oracledb.connect(user=user, password=password, dsn=dsn)
            else:
                # Assume DSN only, get user/pass from environment
                import os

                user = os.getenv("ORACLE_USER", "iris_user")
                password = os.getenv("ORACLE_PASSWORD", "IrisUser123!")
                self.connection = oracledb.connect(
                    user=user, password=password, dsn=self.connection_string
                )

            logger.info("Connected successfully")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise

    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from database")

    def create_schema(self, workload_num: int):
        """Create schema for specified workload.

        Args:
            workload_num: Workload number (1, 2, or 3)
        """
        logger.info(f"Creating schema for Workload {workload_num}...")

        schema_file = Path(__file__).parent / "sql" / f"workload{workload_num}_schema.sql"

        with open(schema_file) as f:
            schema_sql = f.read()

        cursor = self.connection.cursor()

        # Remove multi-line comments (/* */) from SQL
        import re

        schema_sql_cleaned = re.sub(r"/\*.*?\*/", "", schema_sql, flags=re.DOTALL)

        # Split on semicolons and process each statement
        for statement in schema_sql_cleaned.split(";"):
            statement = statement.strip()

            # Skip empty statements
            if not statement:
                continue

            # Filter out comment-only lines but keep SQL commands
            lines = statement.split("\n")
            sql_lines = [
                line for line in lines if line.strip() and not line.strip().startswith("--")
            ]

            # Skip if no SQL remains after filtering comments
            if not sql_lines:
                continue

            # Rejoin filtered lines
            clean_statement = "\n".join(sql_lines)

            try:
                cursor.execute(clean_statement)
                logger.debug(f"Executed: {clean_statement[:50]}...")
            except oracledb.DatabaseError as e:
                error_code = e.args[0].code if e.args else None

                # ORA-00942: table or view does not exist (expected for DROP)
                # ORA-02289: sequence does not exist (expected for DROP)
                # ORA-00955: name is already used by an existing object (expected for re-runs)
                # ORA-01408: column list already indexed (UNIQUE creates implicit index)
                if error_code in (942, 2289, 955, 1408):
                    logger.debug(f"Expected error: {e}")
                else:
                    # Re-raise unexpected errors
                    logger.error(f"Unexpected error executing statement: {clean_statement[:100]}")
                    raise

        self.connection.commit()
        logger.info("Schema created successfully")

    def generate_data(self, workload_num: int, scale: str = "small"):
        """Generate data for specified workload.

        Args:
            workload_num: Workload number (1, 2, or 3)
            scale: Data scale (small, medium, large)
        """
        logger.info(f"Generating data for Workload {workload_num} (scale: {scale})...")

        scale_factors = {
            "small": {"w1": 100, "w2": 50, "w3": 500},
            "medium": {"w1": 1000, "w2": 500, "w3": 5000},
            "large": {"w1": 10000, "w2": 5000, "w3": 50000},
        }

        if workload_num == 1:
            generator = ECommerceDataGenerator(num_customers=scale_factors[scale]["w1"])
            generator.generate_all(self.connection)

        elif workload_num == 2:
            generator = InventoryDataGenerator(num_items=scale_factors[scale]["w2"])
            generator.generate_all(self.connection)

        elif workload_num == 3:
            generator = OrdersDataGenerator(num_orders=scale_factors[scale]["w3"])
            generator.generate_all(self.connection)

        logger.info("Data generation complete")

    def execute_workload(self, workload_num: int, duration: int):
        """Execute workload queries.

        Args:
            workload_num: Workload number (1, 2, or 3)
            duration: Duration in seconds

        Returns:
            Workload execution statistics
        """
        logger.info(f"Executing Workload {workload_num} for {duration} seconds...")

        if workload_num == 1:
            workload = ECommerceWorkload(self.connection, duration_seconds=duration)
        elif workload_num == 2:
            workload = InventoryWorkload(self.connection, duration_seconds=duration)
        elif workload_num == 3:
            workload = OrdersWorkload(self.connection, duration_seconds=duration)
        else:
            raise ValueError(f"Invalid workload number: {workload_num}")

        stats = workload.execute()
        logger.info(f"Workload execution complete: {stats}")
        return stats

    def cleanup_workload(self, workload_num: int):
        """Clean up workload schema and data.

        Args:
            workload_num: Workload number (1, 2, or 3)
        """
        logger.info(f"Cleaning up Workload {workload_num}...")

        cleanup_file = Path(__file__).parent / "sql" / "cleanup.sql"

        with open(cleanup_file) as f:
            cleanup_sql = f.read()

        cursor = self.connection.cursor()

        # Split on semicolons and process each statement
        for statement in cleanup_sql.split(";"):
            statement = statement.strip()

            # Skip empty statements
            if not statement:
                continue

            # Filter out comment-only lines but keep SQL commands
            lines = statement.split("\n")
            sql_lines = [
                line for line in lines if line.strip() and not line.strip().startswith("--")
            ]

            # Skip if no SQL remains after filtering comments
            if not sql_lines:
                continue

            # Rejoin filtered lines
            clean_statement = "\n".join(sql_lines)

            try:
                cursor.execute(clean_statement)
                logger.debug(f"Executed: {clean_statement[:50]}...")
            except oracledb.DatabaseError as e:
                error_code = e.args[0].code if e.args else None

                # ORA-00942: table or view does not exist (expected for DROP)
                # ORA-02289: sequence does not exist (expected for DROP)
                if error_code in (942, 2289):
                    logger.debug(f"Expected error dropping object: {e}")
                else:
                    # Log but don't raise for cleanup
                    logger.warning(f"Unexpected error during cleanup: {clean_statement[:100]}: {e}")

        self.connection.commit()
        logger.info("Cleanup complete")

    def run_workload(
        self,
        workload_num: int,
        duration: int,
        scale: str,
        skip_data_gen: bool,
        run_pipeline: bool = True,
    ):
        """Run complete workflow for a single workload.

        Args:
            workload_num: Workload number (1, 2, or 3)
            duration: Workload execution duration in seconds
            scale: Data scale (small, medium, large)
            skip_data_gen: Skip data generation if True
            run_pipeline: Run IRIS pipeline analysis after workload (default: True)

        Returns:
            Dictionary with workload stats and pipeline results (if run_pipeline=True)
        """
        logger.info(f"\n{'=' * 70}")
        logger.info(f"Running Workload {workload_num}")
        logger.info(f"{'=' * 70}\n")

        try:
            # Create schema
            self.create_schema(workload_num)

            # Generate data (unless skipped)
            if not skip_data_gen:
                self.generate_data(workload_num, scale)
            else:
                logger.info("Skipping data generation (--skip-data-gen)")

            # Check AWR availability
            awr_helper = AWRSnapshotHelper(self.connection)
            awr_enabled = awr_helper.check_awr_enabled()

            begin_snap_id = None
            end_snap_id = None
            pipeline_result = None
            validation_result = None

            if run_pipeline and awr_enabled:
                # Create AWR snapshot before workload
                logger.info("Creating AWR snapshot (begin)...")
                begin_snap_id = awr_helper.create_snapshot()
                awr_helper.wait_for_snapshot(begin_snap_id)
                logger.info(f"Begin snapshot ID: {begin_snap_id}")

            # Execute workload
            stats = self.execute_workload(workload_num, duration)

            if run_pipeline and awr_enabled:
                # Create AWR snapshot after workload
                logger.info("Creating AWR snapshot (end)...")
                end_snap_id = awr_helper.create_snapshot()
                awr_helper.wait_for_snapshot(end_snap_id)
                logger.info(f"End snapshot ID: {end_snap_id}")

                # Run pipeline analysis
                logger.info("\nRunning IRIS pipeline analysis...")
                pipeline_result = self.run_pipeline(workload_num, begin_snap_id, end_snap_id)

                # Validate recommendations
                if pipeline_result and pipeline_result.recommendations:
                    logger.info("\nValidating recommendations...")
                    validation_result = self.validate_recommendations(workload_num, pipeline_result)

            elif run_pipeline and not awr_enabled:
                logger.warning("AWR not enabled - skipping pipeline analysis")

            # Print summary
            logger.info(f"\n{'=' * 70}")
            logger.info(f"Workload {workload_num} Complete")
            logger.info(f"{'=' * 70}")
            logger.info(f"Statistics: {stats}")
            if begin_snap_id and end_snap_id:
                logger.info(f"AWR Snapshots: {begin_snap_id} - {end_snap_id}")
            if pipeline_result:
                logger.info(f"Recommendations: {pipeline_result.recommendations_generated}")
                logger.info(f"Annual Savings: ${pipeline_result.total_annual_savings:,.2f}")
            if validation_result:
                logger.info(
                    f"Validation: {'✅ PASSED' if validation_result['passed'] else '❌ FAILED'}"
                )
            logger.info(f"{'=' * 70}\n")

            return {
                "stats": stats,
                "begin_snap_id": begin_snap_id,
                "end_snap_id": end_snap_id,
                "pipeline_result": pipeline_result,
                "validation_result": validation_result,
            }

        except Exception as e:
            logger.error(f"Workload {workload_num} failed: {e}", exc_info=True)
            raise

    def run_pipeline(self, workload_num: int, begin_snap_id: int, end_snap_id: int):
        """Run IRIS pipeline analysis on workload data.

        Args:
            workload_num: Workload number
            begin_snap_id: Begin AWR snapshot ID
            end_snap_id: End AWR snapshot ID

        Returns:
            PipelineResult from orchestrator
        """
        # Configure pipeline based on workload
        if workload_num == 1:
            # E-Commerce: Focus on join analysis and document classification
            config = PipelineConfig(
                enable_lob_detection=False,
                enable_join_analysis=True,
                enable_document_analysis=True,
                enable_duality_view_analysis=False,
                min_confidence_threshold=0.3,
            )
        elif workload_num == 2:
            # Inventory: Focus on document classification
            config = PipelineConfig(
                enable_lob_detection=False,
                enable_join_analysis=False,
                enable_document_analysis=True,
                enable_duality_view_analysis=False,
                min_confidence_threshold=0.3,
            )
        elif workload_num == 3:
            # Orders: Focus on duality view opportunities
            config = PipelineConfig(
                enable_lob_detection=False,
                enable_join_analysis=True,
                enable_document_analysis=False,
                enable_duality_view_analysis=True,
                min_confidence_threshold=0.3,
            )
        else:
            config = PipelineConfig()

        # Run orchestrator
        orchestrator = PipelineOrchestrator(self.connection, config)

        # Get schemas to analyze based on workload
        schemas = self._get_workload_schemas(workload_num)

        result = orchestrator.run(
            begin_snapshot_id=begin_snap_id, end_snapshot_id=end_snap_id, schemas=schemas
        )

        return result

    def validate_recommendations(self, workload_num: int, pipeline_result):
        """Validate pipeline recommendations against expected outcomes.

        Args:
            workload_num: Workload number
            pipeline_result: PipelineResult from orchestrator

        Returns:
            Validation results dictionary
        """
        workload_id = f"workload{workload_num}"
        validator = RecommendationValidator(workload_id)

        results = validator.validate(pipeline_result.recommendations)
        validator.print_results(results)

        return results

    def _get_workload_schemas(self, workload_num: int) -> list:
        """Get schema names for workload.

        Args:
            workload_num: Workload number

        Returns:
            List of schema names
        """
        # Get current user's schema name
        cursor = self.connection.cursor()
        cursor.execute("SELECT USER FROM DUAL")
        schema_name = cursor.fetchone()[0]
        return [schema_name]


def main():
    """Execute simulation runner main entry point."""
    parser = argparse.ArgumentParser(
        description="Run IRIS pipeline simulations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run Workload 1 for 5 minutes with small dataset
  python run_simulation.py --workload 1 --duration 300 --scale small

  # Run all workloads for 10 minutes with medium dataset
  python run_simulation.py --workload all --duration 600 --scale medium

  # Run Workload 2 with existing data (skip generation)
  python run_simulation.py --workload 2 --duration 300 --skip-data-gen

  # Cleanup all workload schemas
  python run_simulation.py --cleanup
        """,
    )

    parser.add_argument(
        "--workload",
        type=str,
        choices=["1", "2", "3", "all"],
        required=False,
        help="Workload to run (1, 2, 3, or all)",
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=300,
        help="Workload execution duration in seconds (default: 300)",
    )

    parser.add_argument(
        "--scale",
        type=str,
        choices=["small", "medium", "large"],
        default="small",
        help="Data scale (default: small)",
    )

    parser.add_argument(
        "--skip-data-gen",
        action="store_true",
        help="Skip data generation (use existing data)",
    )

    parser.add_argument(
        "--skip-pipeline",
        action="store_true",
        help="Skip pipeline analysis (only run workload)",
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Cleanup all workload schemas and exit",
    )

    parser.add_argument(
        "--connection",
        type=str,
        default="localhost:1524/FREEPDB1",
        help="Oracle connection string (default: localhost:1524/FREEPDB1)",
    )

    args = parser.parse_args()

    # Create runner
    runner = SimulationRunner(args.connection)

    try:
        runner.connect()

        if args.cleanup:
            logger.info("Cleaning up all workloads...")
            for wl in [1, 2, 3]:
                runner.cleanup_workload(wl)
            logger.info("Cleanup complete")
            return 0

        if not args.workload:
            parser.error("--workload is required unless using --cleanup")

        # Determine if pipeline should run
        run_pipeline = not args.skip_pipeline

        # Run workload(s)
        if args.workload == "all":
            for wl in [1, 2, 3]:
                runner.run_workload(wl, args.duration, args.scale, args.skip_data_gen, run_pipeline)
        else:
            wl_num = int(args.workload)
            runner.run_workload(wl_num, args.duration, args.scale, args.skip_data_gen, run_pipeline)

        logger.info("\n" + "=" * 70)
        logger.info("All simulations complete!")
        logger.info("=" * 70)

        return 0

    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        return 1

    finally:
        runner.disconnect()


if __name__ == "__main__":
    sys.exit(main())
