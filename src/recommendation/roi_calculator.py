"""ROI calculator and priority scorer for cost estimates.

This module provides functionality to calculate priority scores and assign
priority tiers to cost estimates based on multiple factors.
"""

import math
from typing import List

from src.recommendation.cost_models import CostEstimate


class ROICalculator:
    """Calculator for ROI and priority scoring."""

    def __init__(
        self,
        roi_weight: float = 0.30,
        savings_weight: float = 0.25,
        payback_weight: float = 0.20,
        impl_cost_weight: float = 0.15,
        severity_weight: float = 0.10,
    ):
        """Initialize ROI calculator with scoring weights.

        Args:
            roi_weight: Weight for ROI percentage (default: 0.30)
            savings_weight: Weight for annual savings (default: 0.25)
            payback_weight: Weight for payback period (default: 0.20)
            impl_cost_weight: Weight for implementation cost (default: 0.15)
            severity_weight: Weight for pattern severity (default: 0.10)
        """
        self.roi_weight = roi_weight
        self.savings_weight = savings_weight
        self.payback_weight = payback_weight
        self.impl_cost_weight = impl_cost_weight
        self.severity_weight = severity_weight

        # Validate weights sum to 1.0
        total_weight = (
            roi_weight + savings_weight + payback_weight + impl_cost_weight + severity_weight
        )
        if not math.isclose(total_weight, 1.0, rel_tol=1e-5):
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

    def calculate_priority_score(self, estimate: CostEstimate) -> float:
        """Calculate priority score (0-100) for a cost estimate.

        The score is a weighted combination of:
        1. ROI percentage (higher = better)
        2. Annual savings (higher = better)
        3. Payback period (shorter = better)
        4. Implementation cost (lower = better)
        5. Pattern severity (higher = more important)

        Args:
            estimate: Cost estimate to score

        Returns:
            Priority score from 0-100
        """
        # Calculate individual component scores (normalized to 0-1)
        roi_score = self._normalize_roi(estimate.roi_percentage or 0)
        savings_score = self._normalize_savings(estimate.annual_savings or 0)
        payback_score = self._normalize_payback(estimate.payback_period_days or 365)
        impl_score = self._normalize_impl_cost(estimate.implementation_cost)
        severity_score = 0.0  # Default for estimates without severity

        # Calculate weighted sum
        priority = (
            roi_score * self.roi_weight
            + savings_score * self.savings_weight
            + payback_score * self.payback_weight
            + impl_score * self.impl_cost_weight
            + severity_score * self.severity_weight
        ) * 100

        # Clamp to 0-100 range
        return max(0.0, min(100.0, priority))

    def assign_priority_tier(self, priority_score: float) -> str:
        """Assign priority tier based on score.

        Tiers:
        - HIGH: score >= 70
        - MEDIUM: 40 <= score < 70
        - LOW: score < 40

        Args:
            priority_score: Priority score (0-100)

        Returns:
            Priority tier: HIGH, MEDIUM, or LOW
        """
        if priority_score >= 70:
            return "HIGH"
        elif priority_score >= 40:
            return "MEDIUM"
        else:
            return "LOW"

    def enrich_estimate(self, estimate: CostEstimate) -> CostEstimate:
        """Enrich cost estimate with priority score and tier.

        Args:
            estimate: Cost estimate to enrich

        Returns:
            Enriched cost estimate with priority_score and priority_tier set
        """
        priority_score = self.calculate_priority_score(estimate)
        priority_tier = self.assign_priority_tier(priority_score)

        estimate.priority_score = priority_score
        estimate.priority_tier = priority_tier

        return estimate

    def rank_estimates(self, estimates: List[CostEstimate]) -> List[CostEstimate]:
        """Rank cost estimates by priority score.

        Enriches each estimate with priority score/tier and sorts by score descending.

        Args:
            estimates: List of cost estimates to rank

        Returns:
            Sorted list of enriched cost estimates (highest priority first)
        """
        # Enrich all estimates
        enriched = [self.enrich_estimate(est) for est in estimates]

        # Sort by priority score (descending)
        enriched.sort(key=lambda e: (e.priority_score or 0, e.annual_savings or 0), reverse=True)

        return enriched

    # Normalization functions (convert raw values to 0-1 scale)

    def _normalize_roi(self, roi_percentage: float) -> float:
        """Normalize ROI percentage to 0-1 scale.

        Uses logarithmic scaling to handle wide range of ROI values.

        Args:
            roi_percentage: ROI percentage (can be negative)

        Returns:
            Normalized score (0-1)
        """
        if roi_percentage <= 0:
            return 0.0

        # Logarithmic scaling: ROI of 100% = 0.5, 1000% = 0.75, 10000% = 1.0
        # log10(100) = 2, log10(1000) = 3, log10(10000) = 4
        try:
            normalized = math.log10(roi_percentage + 1) / 4.0  # Divide by 4 to scale
            return min(1.0, max(0.0, normalized))
        except (ValueError, OverflowError):
            return 0.0

    def _normalize_savings(self, annual_savings: float) -> float:
        """Normalize annual savings to 0-1 scale.

        Uses logarithmic scaling for savings.

        Args:
            annual_savings: Annual savings in USD

        Returns:
            Normalized score (0-1)
        """
        if annual_savings <= 0:
            return 0.0

        # Logarithmic scaling: $1000 = 0.2, $10000 = 0.4, $100000 = 0.6, $1M = 0.8
        try:
            normalized = math.log10(annual_savings) / 6.0  # Divide by 6 (log10(1M) = 6)
            return min(1.0, max(0.0, normalized))
        except (ValueError, OverflowError):
            return 0.0

    def _normalize_payback(self, payback_days: int) -> float:
        """Normalize payback period to 0-1 scale.

        Shorter payback period = higher score.

        Args:
            payback_days: Payback period in days

        Returns:
            Normalized score (0-1)
        """
        if payback_days <= 0:
            return 1.0  # Instant payback

        # Exponential decay: 30 days = 0.9, 90 days = 0.7, 365 days = 0.3, 730 days = 0.1
        decay_rate = 0.003  # Controls how fast score decreases
        normalized = math.exp(-decay_rate * payback_days)
        return min(1.0, max(0.0, normalized))

    def _normalize_impl_cost(self, implementation_cost: float) -> float:
        """Normalize implementation cost to 0-1 scale.

        Lower implementation cost = higher score.

        Args:
            implementation_cost: Implementation cost in USD

        Returns:
            Normalized score (0-1)
        """
        if implementation_cost <= 0:
            return 1.0  # No cost = perfect score

        # Exponential decay: $1000 = 0.9, $5000 = 0.6, $10000 = 0.4, $50000 = 0.1
        decay_rate = 0.00004  # Controls how fast score decreases
        normalized = math.exp(-decay_rate * implementation_cost)
        return min(1.0, max(0.0, normalized))


class PriorityScorer:
    """High-level priority scoring with preset configurations."""

    @staticmethod
    def get_aggressive_scorer() -> ROICalculator:
        """Get scorer optimized for quick wins.

        Emphasizes low implementation cost and fast payback.

        Returns:
            ROI calculator configured for aggressive scoring
        """
        return ROICalculator(
            roi_weight=0.20,
            savings_weight=0.15,
            payback_weight=0.35,  # High weight on fast payback
            impl_cost_weight=0.25,  # High weight on low cost
            severity_weight=0.05,
        )

    @staticmethod
    def get_conservative_scorer() -> ROICalculator:
        """Get scorer optimized for high-value projects.

        Emphasizes total savings and ROI over quick wins.

        Returns:
            ROI calculator configured for conservative scoring
        """
        return ROICalculator(
            roi_weight=0.35,  # High weight on ROI
            savings_weight=0.35,  # High weight on total savings
            payback_weight=0.15,
            impl_cost_weight=0.10,
            severity_weight=0.05,
        )

    @staticmethod
    def get_balanced_scorer() -> ROICalculator:
        """Get balanced scorer (default weights).

        Returns:
            ROI calculator with default balanced weights
        """
        return ROICalculator()  # Uses default weights


# Default calculator instance
DEFAULT_ROI_CALCULATOR = ROICalculator()
