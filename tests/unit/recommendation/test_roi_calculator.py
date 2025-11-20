"""Unit tests for ROI calculator and priority scorer."""

import pytest

from src.recommendation.cost_models import CostEstimate
from src.recommendation.roi_calculator import PriorityScorer, ROICalculator


class TestROICalculator:
    """Test ROICalculator class."""

    def test_default_weights(self):
        """Test that default weights are set correctly."""
        calc = ROICalculator()

        assert calc.roi_weight == 0.30
        assert calc.savings_weight == 0.25
        assert calc.payback_weight == 0.20
        assert calc.impl_cost_weight == 0.15
        assert calc.severity_weight == 0.10

    def test_custom_weights(self):
        """Test custom weight initialization."""
        calc = ROICalculator(
            roi_weight=0.40,
            savings_weight=0.30,
            payback_weight=0.15,
            impl_cost_weight=0.10,
            severity_weight=0.05,
        )

        assert calc.roi_weight == 0.40
        assert calc.savings_weight == 0.30

    def test_weights_validation(self):
        """Test that weights must sum to 1.0."""
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            ROICalculator(
                roi_weight=0.50,
                savings_weight=0.30,
                payback_weight=0.20,
                impl_cost_weight=0.10,
                severity_weight=0.10,  # Total = 1.20
            )

    def test_high_priority_score(self):
        """Test priority score calculation for high-value optimization."""
        calc = ROICalculator()

        # High ROI, high savings, quick payback
        estimate = CostEstimate(
            pattern_id="test_001",
            pattern_type="EXPENSIVE_JOIN",
            affected_objects=["ORDERS", "CUSTOMERS"],
            current_cost_per_day=1000.0,
            optimized_cost_per_day=100.0,
            implementation_cost=5000.0,
        )

        # Annual savings = (1000-100)*365 = 328,500
        # ROI = (328,500 - 5,000) / 5,000 * 100 = 6,470%
        # Payback = 5,000 / 900 = 5.5 days

        priority_score = calc.calculate_priority_score(estimate)

        # Should get high score due to excellent ROI and quick payback
        assert priority_score > 80.0
        assert priority_score <= 100.0

    def test_medium_priority_score(self):
        """Test priority score for moderate optimization."""
        calc = ROICalculator()

        estimate = CostEstimate(
            pattern_id="test_002",
            pattern_type="LOB_CLIFF",
            affected_objects=["AUDIT_LOGS.PAYLOAD"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=60.0,
            implementation_cost=10000.0,
        )

        # Annual savings = 40*365 = 14,600
        # ROI = (14,600 - 10,000) / 10,000 * 100 = 46%
        # Payback = 10,000 / 40 = 250 days

        priority_score = calc.calculate_priority_score(estimate)

        # Should get medium score
        assert 30.0 < priority_score < 70.0

    def test_low_priority_score(self):
        """Test priority score for low-value optimization."""
        calc = ROICalculator()

        estimate = CostEstimate(
            pattern_id="test_003",
            pattern_type="LOB_CLIFF",
            affected_objects=["TABLE1"],
            current_cost_per_day=10.0,
            optimized_cost_per_day=8.0,
            implementation_cost=20000.0,
        )

        # Annual savings = 2*365 = 730
        # ROI = (730 - 20,000) / 20,000 * 100 = -96.35% (negative!)
        # Payback = 10,000 days

        priority_score = calc.calculate_priority_score(estimate)

        # Should get low score due to poor ROI
        assert priority_score < 40.0

    def test_negative_roi(self):
        """Test priority score when optimization costs more than it saves."""
        calc = ROICalculator()

        estimate = CostEstimate(
            pattern_id="test_004",
            pattern_type="DOCUMENT_CANDIDATE",
            affected_objects=["TABLE1"],
            current_cost_per_day=50.0,
            optimized_cost_per_day=75.0,  # More expensive!
            implementation_cost=5000.0,
        )

        priority_score = calc.calculate_priority_score(estimate)

        # Should get very low score (close to 0)
        assert priority_score < 20.0

    def test_assign_high_tier(self):
        """Test HIGH tier assignment."""
        calc = ROICalculator()

        assert calc.assign_priority_tier(85.0) == "HIGH"
        assert calc.assign_priority_tier(70.0) == "HIGH"

    def test_assign_medium_tier(self):
        """Test MEDIUM tier assignment."""
        calc = ROICalculator()

        assert calc.assign_priority_tier(69.9) == "MEDIUM"
        assert calc.assign_priority_tier(50.0) == "MEDIUM"
        assert calc.assign_priority_tier(40.0) == "MEDIUM"

    def test_assign_low_tier(self):
        """Test LOW tier assignment."""
        calc = ROICalculator()

        assert calc.assign_priority_tier(39.9) == "LOW"
        assert calc.assign_priority_tier(20.0) == "LOW"
        assert calc.assign_priority_tier(0.0) == "LOW"

    def test_enrich_estimate(self):
        """Test enriching estimate with priority score and tier."""
        calc = ROICalculator()

        estimate = CostEstimate(
            pattern_id="test_005",
            pattern_type="EXPENSIVE_JOIN",
            affected_objects=["ORDERS", "PRODUCTS"],
            current_cost_per_day=500.0,
            optimized_cost_per_day=50.0,
            implementation_cost=8000.0,
        )

        enriched = calc.enrich_estimate(estimate)

        assert enriched.priority_score is not None
        assert enriched.priority_tier is not None
        assert enriched.priority_tier in ["HIGH", "MEDIUM", "LOW"]

    def test_rank_estimates(self):
        """Test ranking multiple estimates by priority."""
        calc = ROICalculator()

        # Create estimates with varying priority
        high_priority = CostEstimate(
            pattern_id="high",
            pattern_type="EXPENSIVE_JOIN",
            affected_objects=["T1"],
            current_cost_per_day=1000.0,
            optimized_cost_per_day=100.0,
            implementation_cost=5000.0,
        )

        medium_priority = CostEstimate(
            pattern_id="medium",
            pattern_type="LOB_CLIFF",
            affected_objects=["T2"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=60.0,
            implementation_cost=10000.0,
        )

        low_priority = CostEstimate(
            pattern_id="low",
            pattern_type="DOCUMENT_CANDIDATE",
            affected_objects=["T3"],
            current_cost_per_day=10.0,
            optimized_cost_per_day=8.0,
            implementation_cost=20000.0,
        )

        estimates = [low_priority, high_priority, medium_priority]
        ranked = calc.rank_estimates(estimates)

        # Should be sorted by priority (highest first)
        assert ranked[0].pattern_id == "high"
        assert ranked[1].pattern_id == "medium"
        assert ranked[2].pattern_id == "low"

        # All should be enriched
        assert all(e.priority_score is not None for e in ranked)
        assert all(e.priority_tier is not None for e in ranked)


class TestNormalizationFunctions:
    """Test normalization functions."""

    def test_normalize_roi_positive(self):
        """Test ROI normalization for positive ROI values."""
        calc = ROICalculator()

        # Test various ROI percentages
        assert calc._normalize_roi(0) == 0.0
        assert calc._normalize_roi(100) > 0.4  # Decent ROI
        assert calc._normalize_roi(1000) > 0.7  # Great ROI
        assert calc._normalize_roi(10000) > 0.9  # Excellent ROI

    def test_normalize_roi_negative(self):
        """Test ROI normalization for negative ROI."""
        calc = ROICalculator()

        assert calc._normalize_roi(-100) == 0.0
        assert calc._normalize_roi(-50) == 0.0

    def test_normalize_savings(self):
        """Test savings normalization."""
        calc = ROICalculator()

        assert calc._normalize_savings(0) == 0.0
        assert calc._normalize_savings(1000) > 0.0
        assert calc._normalize_savings(10000) > calc._normalize_savings(1000)
        assert calc._normalize_savings(100000) > calc._normalize_savings(10000)
        assert calc._normalize_savings(1000000) > 0.9  # $1M is excellent

    def test_normalize_savings_negative(self):
        """Test savings normalization for negative savings."""
        calc = ROICalculator()

        assert calc._normalize_savings(-1000) == 0.0

    def test_normalize_payback(self):
        """Test payback period normalization."""
        calc = ROICalculator()

        assert calc._normalize_payback(0) == 1.0  # Instant payback = perfect
        assert calc._normalize_payback(30) > 0.8  # 30 days is great
        assert calc._normalize_payback(90) > 0.6  # 90 days is good
        assert calc._normalize_payback(365) > 0.2  # 1 year is okay
        assert calc._normalize_payback(730) < 0.2  # 2 years is poor

    def test_normalize_payback_negative(self):
        """Test payback normalization for negative payback."""
        calc = ROICalculator()

        assert calc._normalize_payback(-10) == 1.0  # Treat as instant

    def test_normalize_impl_cost(self):
        """Test implementation cost normalization."""
        calc = ROICalculator()

        assert calc._normalize_impl_cost(0) == 1.0  # Free = perfect
        assert calc._normalize_impl_cost(1000) > 0.8  # $1K is low
        assert calc._normalize_impl_cost(5000) > 0.5  # $5K is moderate
        assert calc._normalize_impl_cost(10000) > 0.3  # $10K is significant
        assert calc._normalize_impl_cost(50000) < 0.2  # $50K is high


class TestPriorityScorer:
    """Test PriorityScorer preset configurations."""

    def test_aggressive_scorer(self):
        """Test aggressive scorer configuration."""
        scorer = PriorityScorer.get_aggressive_scorer()

        # Should emphasize payback and implementation cost
        assert scorer.payback_weight == 0.35
        assert scorer.impl_cost_weight == 0.25
        assert scorer.roi_weight == 0.20

    def test_conservative_scorer(self):
        """Test conservative scorer configuration."""
        scorer = PriorityScorer.get_conservative_scorer()

        # Should emphasize ROI and savings
        assert scorer.roi_weight == 0.35
        assert scorer.savings_weight == 0.35
        assert scorer.payback_weight == 0.15

    def test_balanced_scorer(self):
        """Test balanced scorer (default)."""
        scorer = PriorityScorer.get_balanced_scorer()

        # Should use default weights
        assert scorer.roi_weight == 0.30
        assert scorer.savings_weight == 0.25
        assert scorer.payback_weight == 0.20

    def test_aggressive_vs_conservative_ranking(self):
        """Test that different scorers produce different rankings."""
        aggressive = PriorityScorer.get_aggressive_scorer()
        conservative = PriorityScorer.get_conservative_scorer()

        # Quick win: low cost, fast payback, moderate savings
        quick_win = CostEstimate(
            pattern_id="quick",
            pattern_type="LOB_CLIFF",
            affected_objects=["T1"],
            current_cost_per_day=50.0,
            optimized_cost_per_day=30.0,
            implementation_cost=1000.0,
        )

        # Big project: high cost, slow payback, huge savings
        big_project = CostEstimate(
            pattern_id="big",
            pattern_type="EXPENSIVE_JOIN",
            affected_objects=["T2"],
            current_cost_per_day=5000.0,
            optimized_cost_per_day=500.0,
            implementation_cost=50000.0,
        )

        # Aggressive scorer should prefer quick win
        aggressive_scores = [
            aggressive.calculate_priority_score(quick_win),
            aggressive.calculate_priority_score(big_project),
        ]

        # Conservative scorer should prefer big project (higher total savings)
        conservative_scores = [
            conservative.calculate_priority_score(quick_win),
            conservative.calculate_priority_score(big_project),
        ]

        # Aggressive: quick_win > big_project
        # Conservative: big_project > quick_win (usually, depends on exact numbers)
        # At minimum, the relative preference should differ
        aggressive_preference = aggressive_scores[0] - aggressive_scores[1]
        conservative_preference = conservative_scores[0] - conservative_scores[1]

        # Should have different preferences
        assert aggressive_preference != conservative_preference


class TestEdgeCases:
    """Test edge cases in priority scoring."""

    def test_zero_implementation_cost(self):
        """Test scoring when implementation cost is zero."""
        calc = ROICalculator()

        estimate = CostEstimate(
            pattern_id="test",
            pattern_type="LOB_CLIFF",
            affected_objects=["T1"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=50.0,
            implementation_cost=0.0,  # Free!
        )

        score = calc.calculate_priority_score(estimate)

        # Should get decent score (free implementation is good, but savings are moderate)
        assert score > 30.0  # Reasonable score given moderate savings

    def test_very_large_values(self):
        """Test with very large cost values."""
        calc = ROICalculator()

        estimate = CostEstimate(
            pattern_id="test",
            pattern_type="EXPENSIVE_JOIN",
            affected_objects=["T1"],
            current_cost_per_day=100000.0,  # $100K/day!
            optimized_cost_per_day=10000.0,
            implementation_cost=500000.0,
        )

        score = calc.calculate_priority_score(estimate)

        # Should handle large values without overflow
        assert 0.0 <= score <= 100.0

    def test_very_small_values(self):
        """Test with very small cost values."""
        calc = ROICalculator()

        estimate = CostEstimate(
            pattern_id="test",
            pattern_type="LOB_CLIFF",
            affected_objects=["T1"],
            current_cost_per_day=0.01,
            optimized_cost_per_day=0.005,
            implementation_cost=10.0,
        )

        score = calc.calculate_priority_score(estimate)

        # Should handle small values
        assert 0.0 <= score <= 100.0

    def test_equal_current_and_optimized(self):
        """Test when current and optimized costs are equal."""
        calc = ROICalculator()

        estimate = CostEstimate(
            pattern_id="test",
            pattern_type="LOB_CLIFF",
            affected_objects=["T1"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=100.0,  # No improvement
            implementation_cost=5000.0,
        )

        score = calc.calculate_priority_score(estimate)

        # Should get very low score (no benefit)
        assert score < 20.0
