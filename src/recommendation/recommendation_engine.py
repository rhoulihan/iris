"""Recommendation engine for generating actionable schema optimization recommendations.

This module integrates pattern detection, cost analysis, and tradeoff analysis to generate
comprehensive recommendations with implementation SQL, rollback plans, and testing strategies.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.recommendation.cost_models import CostEstimate
from src.recommendation.models import DetectedPattern
from src.recommendation.tradeoff_analyzer import OptimizationConflict, TradeoffAnalysis


@dataclass
class Rationale:
    """Rationale for a recommendation."""

    pattern_detected: str  # What pattern was detected
    current_cost: str  # Current cost/problem
    expected_benefit: str  # Expected improvement


@dataclass
class Implementation:
    """Implementation details for a recommendation."""

    sql: str  # Implementation SQL (placeholder for now, LLM will enhance later)
    rollback_plan: str  # How to rollback this change
    testing_approach: str  # How to test before production


@dataclass
class Tradeoff:
    """A tradeoff associated with a recommendation."""

    description: str  # What is the cost/overhead
    justified_by: str  # Why it's acceptable


@dataclass
class Alternative:
    """Alternative approach to consider."""

    approach: str  # Description of alternative
    pros: List[str]  # Advantages
    cons: List[str]  # Disadvantages


@dataclass
class SchemaRecommendation:
    """Complete schema optimization recommendation."""

    recommendation_id: str
    pattern_id: str
    type: str  # Pattern type (LOB_CLIFF, EXPENSIVE_JOIN, etc.)
    priority: str  # HIGH, MEDIUM, LOW
    target_objects: List[str]  # Affected tables/columns
    description: str  # Human-readable description

    rationale: Rationale
    implementation: Implementation

    estimated_improvement_pct: float
    estimated_cost: float
    annual_savings: float
    roi_percentage: float

    tradeoffs: List[Tradeoff] = field(default_factory=list)
    alternatives: List[Alternative] = field(default_factory=list)


class RecommendationEngine:
    """Engine for generating schema optimization recommendations."""

    def __init__(self):
        """Initialize recommendation engine."""
        self._recommendation_counter = 0

    def generate_recommendation(
        self,
        pattern: DetectedPattern,
        cost_estimate: Optional[CostEstimate],
        tradeoff_analysis: TradeoffAnalysis,
        conflicts: List[OptimizationConflict],
    ) -> Optional[SchemaRecommendation]:
        """Generate a single recommendation.

        Args:
            pattern: Detected pattern
            cost_estimate: Cost estimate for pattern (optional)
            tradeoff_analysis: Tradeoff analysis
            conflicts: List of conflicts affecting this pattern

        Returns:
            SchemaRecommendation if approved, None if rejected
        """
        # Reject if tradeoff analysis recommends rejection
        if tradeoff_analysis.recommendation == "REJECT":
            return None

        # Require cost estimate
        if cost_estimate is None:
            return None

        # Generate recommendation ID
        self._recommendation_counter += 1
        rec_id = f"REC-{self._recommendation_counter:03d}"

        # Build rationale
        rationale = self._build_rationale(pattern, cost_estimate, tradeoff_analysis)

        # Build implementation (placeholder SQL for now)
        implementation = self._build_implementation(pattern, cost_estimate)

        # Build tradeoffs
        tradeoffs = self._build_tradeoffs(pattern, cost_estimate, tradeoff_analysis, conflicts)

        # Build alternatives
        alternatives = self._build_alternatives(pattern, conflicts)

        # Create recommendation
        recommendation = SchemaRecommendation(
            recommendation_id=rec_id,
            pattern_id=pattern.pattern_id,
            type=pattern.pattern_type,
            priority=cost_estimate.priority_tier or "MEDIUM",  # Default to MEDIUM if not set
            target_objects=pattern.affected_objects.copy(),
            description=pattern.description,
            rationale=rationale,
            implementation=implementation,
            estimated_improvement_pct=self._calculate_improvement_pct(cost_estimate),
            estimated_cost=cost_estimate.implementation_cost,
            annual_savings=cost_estimate.annual_savings or 0.0,  # Default to 0 if not calculated
            roi_percentage=cost_estimate.roi_percentage or 0.0,  # Default to 0 if not calculated
            tradeoffs=tradeoffs,
            alternatives=alternatives,
        )

        return recommendation

    def generate_recommendations(
        self,
        patterns: List[DetectedPattern],
        cost_estimates: Dict[str, CostEstimate],
        tradeoff_analyses: Dict[str, TradeoffAnalysis],
        conflicts: List[OptimizationConflict],
    ) -> List[SchemaRecommendation]:
        """Generate recommendations for multiple patterns.

        Args:
            patterns: List of detected patterns
            cost_estimates: Dictionary mapping pattern_id to cost estimate
            tradeoff_analyses: Dictionary mapping pattern_id to tradeoff analysis
            conflicts: List of all conflicts

        Returns:
            List of recommendations sorted by priority score (highest first)
        """
        recommendations = []

        for pattern in patterns:
            # Get associated data
            cost_estimate = cost_estimates.get(pattern.pattern_id)
            tradeoff = tradeoff_analyses.get(pattern.pattern_id)

            if cost_estimate is None or tradeoff is None:
                continue  # Skip patterns without complete analysis

            # Get conflicts affecting this pattern
            pattern_conflicts = [
                c
                for c in conflicts
                if c.pattern_a_id == pattern.pattern_id or c.pattern_b_id == pattern.pattern_id
            ]

            # Generate recommendation
            recommendation = self.generate_recommendation(
                pattern, cost_estimate, tradeoff, pattern_conflicts
            )

            if recommendation:
                recommendations.append(recommendation)

        # Sort by priority score (HIGH > MEDIUM > LOW)
        priority_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 0), reverse=True)

        return recommendations

    def _build_rationale(
        self,
        pattern: DetectedPattern,
        cost_estimate: CostEstimate,
        tradeoff: TradeoffAnalysis,
    ) -> Rationale:
        """Build rationale for recommendation."""
        # Pattern-specific rationale
        if pattern.pattern_type == "LOB_CLIFF":
            return Rationale(
                pattern_detected=f"{pattern.description} - Risk score based on document size, update frequency, and selectivity",
                current_cost=f"Current cost: ${cost_estimate.current_cost_per_day:.2f}/day with LOB chaining and write amplification",
                expected_benefit=f"Expected savings: ${cost_estimate.annual_savings:,.0f}/year ({self._calculate_improvement_pct(cost_estimate):.1f}% improvement)",
            )

        elif pattern.pattern_type == "EXPENSIVE_JOIN":
            return Rationale(
                pattern_detected=f"{pattern.description} - High join frequency detected in workload",
                current_cost=f"Current cost: ${cost_estimate.current_cost_per_day:.2f}/day from repeated joins",
                expected_benefit=f"Expected savings: ${cost_estimate.annual_savings:,.0f}/year through denormalization",
            )

        elif pattern.pattern_type == "DOCUMENT_CANDIDATE":
            return Rationale(
                pattern_detected=f"{pattern.description} - High SELECT * and object access patterns",
                current_cost=f"Current cost: ${cost_estimate.current_cost_per_day:.2f}/day from relational overhead",
                expected_benefit=f"Expected savings: ${cost_estimate.annual_savings:,.0f}/year with JSON storage",
            )

        elif pattern.pattern_type == "DUALITY_VIEW_OPPORTUNITY":
            return Rationale(
                pattern_detected=f"{pattern.description} - Mixed OLTP and Analytics workload",
                current_cost=f"Current cost: ${cost_estimate.current_cost_per_day:.2f}/day from format conversions",
                expected_benefit=f"Expected savings: ${cost_estimate.annual_savings:,.0f}/year with dual access",
            )

        else:
            # Generic rationale
            return Rationale(
                pattern_detected=pattern.description,
                current_cost=f"${cost_estimate.current_cost_per_day:.2f}/day",
                expected_benefit=f"${cost_estimate.annual_savings:,.0f}/year savings",
            )

    def _build_implementation(
        self, pattern: DetectedPattern, cost_estimate: CostEstimate
    ) -> Implementation:
        """Build implementation details (placeholder SQL for now)."""
        # Pattern-specific implementation guidance
        if pattern.pattern_type == "LOB_CLIFF":
            table_col = pattern.affected_objects[0]  # Format: "TABLE.COLUMN"
            if "." in table_col:
                table, column = table_col.split(".", 1)
                sql = f"-- Placeholder: Split {column} from {table}\n-- CREATE TABLE {table}_{column} ..."
                rollback = f"-- Placeholder: Merge {column} back into {table}\n-- DROP TABLE {table}_{column};"
            else:
                sql = "-- Placeholder: LOB optimization SQL"
                rollback = "-- Placeholder: Rollback SQL"

            testing = "1. Create in test environment\n2. Shadow testing with production workload\n3. Monitor I/O metrics for 1 week"

        elif pattern.pattern_type == "EXPENSIVE_JOIN":
            tables = pattern.affected_objects
            sql = f"-- Placeholder: Denormalize {' JOIN '.join(tables)}\n-- ALTER TABLE ... ADD COLUMN ..."
            rollback = (
                "-- Placeholder: Remove denormalized columns\n-- ALTER TABLE ... DROP COLUMN ..."
            )
            testing = "1. Test in dev environment\n2. Compare query performance\n3. Validate data consistency"

        elif pattern.pattern_type == "DOCUMENT_CANDIDATE":
            table = pattern.affected_objects[0]
            sql = f"-- Placeholder: Convert {table} to JSON collection\n-- CREATE TABLE {table}_json ..."
            rollback = f"-- Placeholder: Revert to relational\n-- DROP TABLE {table}_json;"
            testing = "1. Parallel run with both schemas\n2. Compare application performance\n3. Validate JSON structure"

        elif pattern.pattern_type == "DUALITY_VIEW_OPPORTUNITY":
            table = pattern.affected_objects[0]
            sql = f"-- Placeholder: Create Duality View for {table}\n-- CREATE JSON RELATIONAL DUALITY VIEW {table}_dv AS ..."
            rollback = f"-- Placeholder: Drop Duality View\n-- DROP VIEW {table}_dv;"
            testing = "1. Create view in test\n2. Route 10% of traffic to view\n3. Monitor performance for both OLTP and Analytics"

        else:
            sql = "-- Placeholder: Implementation SQL will be generated by LLM"
            rollback = "-- Placeholder: Rollback plan"
            testing = "Test in non-production environment first"

        return Implementation(sql=sql, rollback_plan=rollback, testing_approach=testing)

    def _build_tradeoffs(
        self,
        pattern: DetectedPattern,
        cost_estimate: CostEstimate,
        tradeoff: TradeoffAnalysis,
        conflicts: List[OptimizationConflict],
    ) -> List[Tradeoff]:
        """Build list of tradeoffs."""
        tradeoffs = []

        # Add overhead tradeoff if applicable
        if tradeoff.weighted_degradation_pct > 0:
            tradeoffs.append(
                Tradeoff(
                    description=f"{tradeoff.weighted_degradation_pct:.1f}% performance degradation on low-frequency queries",
                    justified_by=f"{tradeoff.weighted_improvement_pct:.1f}% improvement on high-frequency queries (net benefit: {tradeoff.net_benefit_score:.1f})",
                )
            )

        # Add implementation cost tradeoff
        if cost_estimate.implementation_cost > 0:
            tradeoffs.append(
                Tradeoff(
                    description=f"${cost_estimate.implementation_cost:,.0f} implementation cost",
                    justified_by=f"Payback in {cost_estimate.payback_period_days:.1f} days with {cost_estimate.roi_percentage:.1f}% ROI",
                )
            )

        # Add conflict-related tradeoffs
        for conflict in conflicts:
            if conflict.resolution_strategy in ["PRIORITIZE_A", "PRIORITIZE_B"]:
                tradeoffs.append(
                    Tradeoff(
                        description=f"Conflicts with {conflict.pattern_b_id if conflict.pattern_a_id == pattern.pattern_id else conflict.pattern_a_id}",
                        justified_by=f"Higher priority: {conflict.rationale}",
                    )
                )

        return tradeoffs

    def _build_alternatives(
        self, pattern: DetectedPattern, conflicts: List[OptimizationConflict]
    ) -> List[Alternative]:
        """Build list of alternative approaches."""
        alternatives = []

        # Check if Duality View is suggested as conflict resolution
        for conflict in conflicts:
            if conflict.resolution_strategy == "DUALITY_VIEW":
                alternatives.append(
                    Alternative(
                        approach="Use JSON Duality View to support both patterns",
                        pros=[
                            "Supports both OLTP and Analytics access",
                            "No application changes needed",
                            "ACID guarantees maintained",
                        ],
                        cons=[
                            "View maintenance overhead",
                            "Requires Oracle 23ai",
                            "Increased storage (dual representation)",
                        ],
                    )
                )
                break  # Only add once

        # Pattern-specific alternatives
        if pattern.pattern_type == "LOB_CLIFF":
            alternatives.append(
                Alternative(
                    approach="Keep LOB inline but increase CHUNK size",
                    pros=["Simpler implementation", "No schema change"],
                    cons=["Doesn't fully eliminate LOB cliffs", "Storage overhead"],
                )
            )

        elif pattern.pattern_type == "EXPENSIVE_JOIN":
            alternatives.append(
                Alternative(
                    approach="Use materialized view instead of denormalization",
                    pros=["No schema change", "Easier to rollback"],
                    cons=["Refresh overhead", "Potential data staleness"],
                )
            )

        elif pattern.pattern_type == "DOCUMENT_CANDIDATE":
            alternatives.append(
                Alternative(
                    approach="Add JSON column to relational table (hybrid)",
                    pros=["Gradual migration", "Supports both access patterns"],
                    cons=["Application complexity", "Data duplication"],
                )
            )

        return alternatives

    def _calculate_improvement_pct(self, cost_estimate: CostEstimate) -> float:
        """Calculate percentage improvement."""
        if cost_estimate.current_cost_per_day == 0:
            return 0.0
        improvement = cost_estimate.current_cost_per_day - cost_estimate.optimized_cost_per_day
        return (improvement / cost_estimate.current_cost_per_day) * 100.0
