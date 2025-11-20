"""Cost calculator for pattern detection findings.

This module provides cost estimation for detected anti-patterns and calculates
ROI for recommended optimizations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from src.recommendation.cost_models import (
    CostBreakdown,
    CostCalculationInput,
    CostConfiguration,
    CostEstimate,
    ImplementationCostEstimate,
)
from src.recommendation.models import DetectedPattern


class PatternCostCalculator(ABC):
    """Base class for pattern-specific cost calculators."""

    def __init__(self, cost_config: CostConfiguration | None = None):
        """Initialize cost calculator.

        Args:
            cost_config: Cost configuration parameters. Uses defaults if not provided.
        """
        self.config = cost_config or CostConfiguration()

    @abstractmethod
    def calculate(self, calc_input: CostCalculationInput) -> CostEstimate:
        """Calculate cost estimate for a detected pattern.

        Args:
            calc_input: Input data including pattern, metadata, and workload

        Returns:
            CostEstimate with current cost, optimized cost, and ROI metrics
        """
        pass

    def _estimate_implementation_cost(self, impl_estimate: ImplementationCostEstimate) -> float:
        """Calculate implementation cost from effort estimate.

        Args:
            impl_estimate: Implementation effort estimate

        Returns:
            Total implementation cost in USD
        """
        return impl_estimate.calculate_cost(self.config.hourly_rate)


class LOBCliffCostCalculator(PatternCostCalculator):
    """Cost calculator for LOB Cliff anti-patterns."""

    def calculate(self, calc_input: CostCalculationInput) -> CostEstimate:
        """Calculate cost for LOB Cliff pattern.

        Current Cost:
        - I/O cost reading large LOBs
        - Write amplification (updating entire LOB for small changes)
        - Block chaining overhead

        Optimized Cost:
        - Reduced I/O with SecureFile LOBs or separate tables
        - Write only updated bytes
        - Reduced chaining

        Args:
            calc_input: Cost calculation input

        Returns:
            Cost estimate for LOB cliff optimization
        """
        pattern = calc_input.pattern
        table = calc_input.table_metadata
        _ = calc_input.workload  # Reserved for future workload-based analysis

        # Extract metrics from pattern
        metrics = pattern.metrics
        updates_per_day = metrics.get("updates_per_day", 0)
        avg_doc_size_kb = metrics.get("avg_document_size_kb", 0)
        update_selectivity = metrics.get("update_selectivity", 0.1)

        # Estimate read operations (assuming some reads for each update + additional reads)
        # This is a simplification - in reality we'd analyze query patterns
        reads_per_day = updates_per_day * 2  # Rough estimate: 2 reads per update

        # Calculate current costs
        current_breakdown = CostBreakdown()

        # Read cost: reading entire LOB
        current_breakdown.read_cost = reads_per_day * avg_doc_size_kb * self.config.cost_per_kb_read

        # Write amplification: writing entire LOB even for small updates
        current_breakdown.write_cost = (
            updates_per_day * avg_doc_size_kb * self.config.cost_per_kb_write
        )

        # Block chaining cost (fragmentation from updates)
        chain_overhead_per_update = 0.01  # $0.01 per update for chaining overhead
        current_breakdown.other_costs["chain_overhead"] = (
            updates_per_day * chain_overhead_per_update
        )

        # Calculate optimized costs (SecureFile LOBs or separate table)
        optimized_breakdown = CostBreakdown()

        # Read optimization: 30% improvement with SecureFile LOBs
        read_improvement_factor = 0.7
        optimized_breakdown.read_cost = current_breakdown.read_cost * read_improvement_factor

        # Write optimization: only write updated bytes
        bytes_updated_kb = avg_doc_size_kb * update_selectivity
        optimized_breakdown.write_cost = (
            updates_per_day * bytes_updated_kb * self.config.cost_per_kb_write
        )

        # Reduced chaining with better LOB storage
        optimized_breakdown.other_costs["chain_overhead"] = (
            updates_per_day * chain_overhead_per_update * 0.2  # 80% reduction
        )

        # Calculate implementation cost
        impl_estimate = ImplementationCostEstimate(
            schema_changes_hours=self.config.schema_change_hours,
            migration_hours=self.config.migration_hours,
            app_changes_hours=self.config.app_change_hours * 0.25,  # Minimal app changes
            testing_hours=self.config.testing_hours,
            risk_factor=self.config.risk_multiplier,
        )

        implementation_cost = self._estimate_implementation_cost(impl_estimate)

        # Create cost estimate
        assumptions = [
            f"Assumes {int((1 - read_improvement_factor) * 100)}% read performance improvement with SecureFile LOBs",
            f"Update selectivity: {update_selectivity * 100:.1f}% of document updated",
            f"Estimated {reads_per_day} reads per day based on update patterns",
        ]

        return CostEstimate(
            pattern_id=f"{pattern.pattern_type}_{table.name}",
            pattern_type=pattern.pattern_type,
            affected_objects=[f"{table.name}.{pattern.affected_objects[0]}"],
            current_cost_per_day=current_breakdown.total_cost,
            optimized_cost_per_day=optimized_breakdown.total_cost,
            implementation_cost=implementation_cost,
            current_cost_breakdown=current_breakdown,
            optimized_cost_breakdown=optimized_breakdown,
            assumptions=assumptions,
            confidence=pattern.confidence,
        )


class JoinDenormalizationCostCalculator(PatternCostCalculator):
    """Cost calculator for expensive join patterns."""

    def calculate(self, calc_input: CostCalculationInput) -> CostEstimate:
        """Calculate cost for join denormalization.

        Current Cost:
        - Join CPU cost
        - Join I/O cost
        - Network transfer cost

        Optimized Cost:
        - Direct table access (no join)
        - Update propagation cost (keeping denormalized data in sync)

        Args:
            calc_input: Cost calculation input

        Returns:
            Cost estimate for join denormalization
        """
        pattern = calc_input.pattern
        _ = calc_input.workload  # Reserved for future workload-based analysis

        # Extract metrics
        metrics = pattern.metrics
        join_frequency_per_day = metrics.get("join_frequency_per_day", 0)
        join_cardinality = metrics.get("join_cardinality", 1000)  # Rows processed
        dimension_update_rate = metrics.get("dimension_update_rate", 10)
        num_columns_denormalized = len(metrics.get("columns_accessed", []))

        # Current costs: JOIN operations
        current_breakdown = CostBreakdown()

        # CPU cost for join processing
        current_breakdown.cpu_cost = (
            join_frequency_per_day * join_cardinality * self.config.cpu_cost_per_row
        )

        # I/O cost for reading dimension table
        bytes_per_row = 1  # ~1KB per row estimate
        current_breakdown.read_cost = (
            join_frequency_per_day * join_cardinality * bytes_per_row * self.config.cost_per_kb_read
        )

        # Network cost for transferring joined data
        current_breakdown.network_cost = (
            join_frequency_per_day
            * num_columns_denormalized
            * 0.1  # 0.1KB per column
            * self.config.network_cost_per_kb
        )

        # Optimized costs: Denormalized access
        optimized_breakdown = CostBreakdown()

        # Direct read (no join) - much cheaper
        optimized_breakdown.read_cost = (
            join_frequency_per_day * bytes_per_row * 0.1 * self.config.cost_per_kb_read
        )

        # Update propagation cost - keeping denormalized columns in sync
        # When dimension updates, need to update all fact table rows
        fact_table_rows = join_cardinality * 10  # Estimate fact table size
        optimized_breakdown.write_cost = (
            dimension_update_rate
            * fact_table_rows
            * num_columns_denormalized
            * 0.01  # Small update per row
            * self.config.cost_per_kb_write
        )

        # Implementation cost
        impl_estimate = ImplementationCostEstimate(
            schema_changes_hours=self.config.schema_change_hours,
            migration_hours=self.config.migration_hours * 1.5,  # Data migration needed
            app_changes_hours=self.config.app_change_hours * 0.5,  # Moderate app changes
            testing_hours=self.config.testing_hours * 1.5,  # Extra testing for sync logic
            risk_factor=self.config.risk_multiplier * 1.1,  # Slightly higher risk
        )

        implementation_cost = self._estimate_implementation_cost(impl_estimate)

        assumptions = [
            f"Join processes {join_cardinality} rows on average",
            f"Dimension table updated {dimension_update_rate} times per day",
            f"{num_columns_denormalized} columns will be denormalized",
            "Assumes trigger-based sync for denormalized columns",
        ]

        return CostEstimate(
            pattern_id=f"{pattern.pattern_type}_{'_'.join(pattern.affected_objects)}",
            pattern_type=pattern.pattern_type,
            affected_objects=pattern.affected_objects,
            current_cost_per_day=current_breakdown.total_cost,
            optimized_cost_per_day=optimized_breakdown.total_cost,
            implementation_cost=implementation_cost,
            current_cost_breakdown=current_breakdown,
            optimized_cost_breakdown=optimized_breakdown,
            assumptions=assumptions,
            confidence=pattern.confidence * 0.9,  # Slightly lower confidence
        )


class DocumentStorageCostCalculator(PatternCostCalculator):
    """Cost calculator for document vs relational storage patterns."""

    def calculate(self, calc_input: CostCalculationInput) -> CostEstimate:
        """Calculate cost for migrating to document storage.

        Current Cost (Relational):
        - Wide row fetches
        - Multiple index maintenance
        - Storage for normalized tables

        Optimized Cost (JSON):
        - Document fetches
        - JSON index maintenance
        - JSON collection storage

        Args:
            calc_input: Cost calculation input

        Returns:
            Cost estimate for document storage migration
        """
        pattern = calc_input.pattern
        table = calc_input.table_metadata

        metrics = pattern.metrics
        select_all_percentage = metrics.get("select_all_percentage", 50)
        num_columns = len(table.columns)
        reads_per_day = metrics.get("total_queries", 1000)
        updates_per_day = reads_per_day * 0.1  # Assume 10% updates

        # Current costs: Relational storage
        current_breakdown = CostBreakdown()

        # Cost of reading many columns
        bytes_per_column = 0.1  # 100 bytes per column estimate
        current_breakdown.read_cost = (
            reads_per_day * num_columns * bytes_per_column * self.config.cost_per_kb_read
        )

        # Index maintenance cost (assume 3 indexes)
        num_indexes = 3
        current_breakdown.other_costs["index_maintenance"] = updates_per_day * num_indexes * 0.001

        # Storage cost (normalized tables)
        table_size_gb = table.num_rows * table.avg_row_len / (1024 * 1024 * 1024)
        current_breakdown.storage_cost = table_size_gb * self.config.cost_per_gb_per_day

        # Optimized costs: JSON document storage
        optimized_breakdown = CostBreakdown()

        # JSON document reads (typically larger but fewer round trips)
        json_doc_size_kb = table.avg_row_len / 1024
        optimized_breakdown.read_cost = (
            reads_per_day * json_doc_size_kb * self.config.cost_per_kb_read * 0.8
        )

        # JSON index maintenance (fewer indexes)
        num_json_indexes = 2
        optimized_breakdown.other_costs["json_index_maintenance"] = (
            updates_per_day * num_json_indexes * 0.0008
        )

        # JSON storage (typically more compact)
        json_storage_gb = table_size_gb * 0.8  # 20% savings
        optimized_breakdown.storage_cost = json_storage_gb * self.config.cost_per_gb_per_day

        # Implementation cost (high for document migration)
        impl_estimate = ImplementationCostEstimate(
            schema_changes_hours=self.config.schema_change_hours * 2,  # Significant redesign
            migration_hours=self.config.migration_hours * 3,  # Complex data transformation
            app_changes_hours=self.config.app_change_hours * 2,  # Major app refactoring
            testing_hours=self.config.testing_hours * 2,  # Extensive testing
            risk_factor=self.config.risk_multiplier * 1.3,  # Higher risk
        )

        implementation_cost = self._estimate_implementation_cost(impl_estimate)

        assumptions = [
            f"{select_all_percentage:.1f}% of queries fetch all columns (document-like access)",
            f"JSON storage will be {json_storage_gb:.2f}GB vs {table_size_gb:.2f}GB relational",
            "Application will be refactored to use JSON access patterns",
            "Assumes Oracle JSON data type with JSON indexes",
        ]

        return CostEstimate(
            pattern_id=f"{pattern.pattern_type}_{table.name}",
            pattern_type=pattern.pattern_type,
            affected_objects=[table.name],
            current_cost_per_day=current_breakdown.total_cost,
            optimized_cost_per_day=optimized_breakdown.total_cost,
            implementation_cost=implementation_cost,
            current_cost_breakdown=current_breakdown,
            optimized_cost_breakdown=optimized_breakdown,
            assumptions=assumptions,
            confidence=pattern.confidence * 0.85,  # Lower confidence for major migration
        )


class DualityViewCostCalculator(PatternCostCalculator):
    """Cost calculator for JSON Duality View opportunities."""

    def calculate(self, calc_input: CostCalculationInput) -> CostEstimate:
        """Calculate cost for implementing JSON Duality Views.

        Current Cost (Dual Systems):
        - Redundant storage in RDBMS + NoSQL
        - Sync overhead between systems
        - Operational complexity

        Optimized Cost (Duality Views):
        - Single storage
        - View materialization overhead
        - Simplified operations

        Args:
            calc_input: Cost calculation input

        Returns:
            Cost estimate for duality view implementation
        """
        pattern = calc_input.pattern
        table = calc_input.table_metadata

        metrics = pattern.metrics
        oltp_percentage = metrics.get("oltp_percentage", 40)
        analytics_percentage = metrics.get("analytics_percentage", 30)
        total_queries = metrics.get("total_queries", 1000)

        # Current costs: Maintaining dual systems
        current_breakdown = CostBreakdown()

        # Redundant storage (data stored twice)
        table_size_gb = table.num_rows * table.avg_row_len / (1024 * 1024 * 1024)
        current_breakdown.storage_cost = table_size_gb * 2 * self.config.cost_per_gb_per_day

        # Sync overhead between systems
        updates_per_day = total_queries * 0.2  # Assume 20% updates
        sync_latency_cost = 0.01  # $0.01 per sync operation
        current_breakdown.other_costs["sync_overhead"] = updates_per_day * sync_latency_cost

        # Operational complexity (fixed cost of running two systems)
        current_breakdown.other_costs["operational_overhead"] = 10.0  # $10/day

        # Optimized costs: Single system with duality views
        optimized_breakdown = CostBreakdown()

        # Single storage
        optimized_breakdown.storage_cost = table_size_gb * self.config.cost_per_gb_per_day

        # View materialization overhead (minimal)
        view_overhead_per_query = 0.00001
        optimized_breakdown.other_costs["view_overhead"] = total_queries * view_overhead_per_query

        # Implementation cost (moderate - create views and migrate)
        impl_estimate = ImplementationCostEstimate(
            schema_changes_hours=self.config.schema_change_hours * 0.5,  # Create views
            migration_hours=self.config.migration_hours,  # Migrate from NoSQL
            app_changes_hours=self.config.app_change_hours,  # Update endpoints
            testing_hours=self.config.testing_hours,  # Test new endpoints
            risk_factor=self.config.risk_multiplier,
        )

        implementation_cost = self._estimate_implementation_cost(impl_estimate)

        assumptions = [
            f"{oltp_percentage:.1f}% OLTP workload, {analytics_percentage:.1f}% analytics",
            "Currently maintaining separate NoSQL system for JSON access",
            "Duality views will provide both relational and JSON access",
            f"Will eliminate ${current_breakdown.other_costs.get('operational_overhead', 0)}/day operational overhead",
        ]

        return CostEstimate(
            pattern_id=f"{pattern.pattern_type}_{table.name}",
            pattern_type=pattern.pattern_type,
            affected_objects=[table.name],
            current_cost_per_day=current_breakdown.total_cost,
            optimized_cost_per_day=optimized_breakdown.total_cost,
            implementation_cost=implementation_cost,
            current_cost_breakdown=current_breakdown,
            optimized_cost_breakdown=optimized_breakdown,
            assumptions=assumptions,
            confidence=pattern.confidence,
        )


class CostCalculatorFactory:
    """Factory for creating pattern-specific cost calculators."""

    _calculators: Dict[str, type[PatternCostCalculator]] = {
        "LOB_CLIFF": LOBCliffCostCalculator,
        "EXPENSIVE_JOIN": JoinDenormalizationCostCalculator,
        "DOCUMENT_CANDIDATE": DocumentStorageCostCalculator,
        "DUALITY_VIEW_OPPORTUNITY": DualityViewCostCalculator,
    }

    @classmethod
    def get_calculator(
        cls, pattern_type: str, cost_config: CostConfiguration | None = None
    ) -> PatternCostCalculator:
        """Get appropriate cost calculator for pattern type.

        Args:
            pattern_type: Type of pattern (LOB_CLIFF, EXPENSIVE_JOIN, etc.)
            cost_config: Optional cost configuration

        Returns:
            Pattern-specific cost calculator

        Raises:
            ValueError: If pattern type is not supported
        """
        calculator_class = cls._calculators.get(pattern_type)
        if not calculator_class:
            raise ValueError(f"No cost calculator found for pattern type: {pattern_type}")

        return calculator_class(cost_config)

    @classmethod
    def calculate_all(
        cls,
        patterns: List[DetectedPattern],
        table_metadata: Dict[str, Any],
        workload: Any,
        cost_config: CostConfiguration | None = None,
    ) -> List[CostEstimate]:
        """Calculate costs for all detected patterns.

        Args:
            patterns: List of detected patterns
            table_metadata: Dictionary of table name to TableMetadata
            workload: Workload features
            cost_config: Optional cost configuration

        Returns:
            List of cost estimates for all patterns
        """
        estimates: List[CostEstimate] = []

        for pattern in patterns:
            try:
                # Get table metadata for first affected object
                table_name = pattern.affected_objects[0].split(".")[0]
                table = table_metadata.get(table_name)

                if not table:
                    continue

                # Get calculator
                calculator = cls.get_calculator(pattern.pattern_type, cost_config)

                # Calculate cost
                calc_input = CostCalculationInput(
                    pattern=pattern,
                    table_metadata=table,
                    workload=workload,
                    cost_config=cost_config or CostConfiguration(),
                )

                estimate = calculator.calculate(calc_input)
                estimates.append(estimate)

            except Exception as e:
                # Log error but continue with other patterns
                print(f"Error calculating cost for {pattern.pattern_type}: {e}")
                continue

        return estimates
