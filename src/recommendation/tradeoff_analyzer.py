"""Tradeoff analyzer for evaluating competing optimizations.

This module analyzes tradeoffs between optimizations, detects conflicts,
and performs frequency-weighted impact analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.recommendation.cost_models import CostEstimate
from src.recommendation.models import TableMetadata, WorkloadFeatures


@dataclass
class QueryFrequencyProfile:
    """Frequency distribution of queries by pattern."""

    query_type: str  # "SELECT", "INSERT", "UPDATE", "DELETE"
    daily_executions: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    percentage_of_workload: float  # 0.0-1.0


@dataclass
class OptimizationConflict:
    """Detected conflict between two optimizations."""

    pattern_a_id: str
    pattern_b_id: str
    conflict_type: str  # "INCOMPATIBLE", "OVERLAPPING", "CASCADING"
    affected_objects: List[str]  # Tables/columns affected by both
    description: str
    resolution_strategy: str  # "DUALITY_VIEW", "PRIORITIZE_A", "PRIORITIZE_B", "REJECT_BOTH"
    rationale: str


@dataclass
class TradeoffAnalysis:
    """Analysis of gains vs costs for an optimization."""

    pattern_id: str
    high_frequency_queries: List[QueryFrequencyProfile]  # Queries that benefit
    low_frequency_queries: List[QueryFrequencyProfile]  # Queries that degrade

    # Frequency-weighted metrics
    weighted_improvement_pct: float  # Positive number
    weighted_degradation_pct: float  # Positive number (cost)
    net_benefit_score: float  # improvement - degradation

    # Break-even analysis
    overhead_justified: bool
    break_even_threshold: float  # Minimum improvement needed to justify overhead

    recommendation: str  # "APPROVE", "REJECT", "CONDITIONAL"
    conditions: List[str] = field(default_factory=list)  # Conditions if "CONDITIONAL"


class TradeoffAnalyzer:
    """Analyzer for optimization tradeoffs and conflicts."""

    def __init__(self):
        """Initialize tradeoff analyzer."""
        pass

    def analyze(
        self,
        cost_estimates: List[CostEstimate],
        workload: WorkloadFeatures,
    ) -> Dict[str, TradeoffAnalysis]:
        """Analyze tradeoffs for all cost estimates.

        Args:
            cost_estimates: List of cost estimates from Cost Calculator
            workload: Workload features

        Returns:
            Dictionary mapping pattern_id to TradeoffAnalysis
        """
        analyses = {}

        for estimate in cost_estimates:
            analysis = self._analyze_single(estimate, workload)
            analyses[estimate.pattern_id] = analysis

        return analyses

    def _analyze_single(
        self,
        estimate: CostEstimate,
        workload: WorkloadFeatures,
    ) -> TradeoffAnalysis:
        """Analyze tradeoffs for a single optimization.

        Args:
            estimate: Cost estimate to analyze
            workload: Workload features

        Returns:
            TradeoffAnalysis for this optimization
        """
        # Placeholder implementation
        return TradeoffAnalysis(
            pattern_id=estimate.pattern_id,
            high_frequency_queries=[],
            low_frequency_queries=[],
            weighted_improvement_pct=0.0,
            weighted_degradation_pct=0.0,
            net_benefit_score=0.0,
            overhead_justified=False,
            break_even_threshold=0.0,
            recommendation="APPROVE",
            conditions=[],
        )

    def detect_conflicts(
        self,
        cost_estimates: List[CostEstimate],
        table_metadata: Dict[str, TableMetadata],
    ) -> List[OptimizationConflict]:
        """Detect conflicts between optimizations.

        Args:
            cost_estimates: List of cost estimates
            table_metadata: Dictionary of table metadata

        Returns:
            List of detected conflicts
        """
        conflicts = []

        # Check all pairs for conflicts
        for i, est_a in enumerate(cost_estimates):
            for est_b in cost_estimates[i + 1 :]:
                conflict = self._check_conflict(est_a, est_b, table_metadata)
                if conflict:
                    conflicts.append(conflict)

        return conflicts

    def _check_conflict(
        self,
        est_a: CostEstimate,
        est_b: CostEstimate,
        metadata: Dict[str, TableMetadata],
    ) -> Optional[OptimizationConflict]:
        """Check if two estimates conflict.

        Args:
            est_a: First cost estimate
            est_b: Second cost estimate
            metadata: Table metadata

        Returns:
            OptimizationConflict if conflict detected, None otherwise
        """
        # Get affected tables
        tables_a = set(self._get_affected_tables(est_a))
        tables_b = set(self._get_affected_tables(est_b))

        # Check for overlap
        overlap = tables_a & tables_b
        if not overlap:
            return None  # No conflict if no overlap

        # Check if patterns are incompatible
        if self._is_incompatible(est_a.pattern_type, est_b.pattern_type):
            return OptimizationConflict(
                pattern_a_id=est_a.pattern_id,
                pattern_b_id=est_b.pattern_id,
                conflict_type="INCOMPATIBLE",
                affected_objects=list(overlap),
                description=f"Cannot apply both {est_a.pattern_type} and {est_b.pattern_type}",
                resolution_strategy=self._resolve_incompatibility(est_a, est_b),
                rationale=f"Patterns {est_a.pattern_type} and {est_b.pattern_type} have conflicting goals",
            )

        return None

    def _get_affected_tables(self, estimate: CostEstimate) -> List[str]:
        """Extract table names from affected objects.

        Args:
            estimate: Cost estimate

        Returns:
            List of table names
        """
        tables = []
        for obj in estimate.affected_objects:
            # Handle "TABLE.COLUMN" or just "TABLE"
            table = obj.split(".")[0]
            if table not in tables:
                tables.append(table)
        return tables

    def _is_incompatible(self, pattern_a: str, pattern_b: str) -> bool:
        """Check if two pattern types are incompatible.

        Args:
            pattern_a: First pattern type
            pattern_b: Second pattern type

        Returns:
            True if incompatible, False otherwise
        """
        INCOMPATIBLE_PAIRS = {
            frozenset(["DOCUMENT_CANDIDATE", "EXPENSIVE_JOIN"]),  # Document vs relational
            frozenset(["LOB_CLIFF", "DOCUMENT_CANDIDATE"]),  # LOB split conflicts with document
        }

        pair = frozenset([pattern_a, pattern_b])
        return pair in INCOMPATIBLE_PAIRS

    def _resolve_incompatibility(
        self,
        est_a: CostEstimate,
        est_b: CostEstimate,
    ) -> str:
        """Determine resolution strategy for incompatible patterns.

        Args:
            est_a: First cost estimate
            est_b: Second cost estimate

        Returns:
            Resolution strategy string
        """
        # Document vs relational conflict -> suggest Duality View
        if {est_a.pattern_type, est_b.pattern_type} == {
            "DOCUMENT_CANDIDATE",
            "EXPENSIVE_JOIN",
        }:
            return "DUALITY_VIEW"

        # Otherwise prioritize based on ROI
        if (est_a.priority_score or 0) > (est_b.priority_score or 0):
            return "PRIORITIZE_A"
        else:
            return "PRIORITIZE_B"
