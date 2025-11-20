"""Unit tests for cost model data structures."""

import pytest

from src.recommendation.cost_models import (
    CostBreakdown,
    CostConfiguration,
    CostEstimate,
    ImplementationCostEstimate,
)


class TestCostConfiguration:
    """Test CostConfiguration data structure."""

    def test_default_configuration(self):
        """Test default cost configuration values."""
        config = CostConfiguration()

        assert config.cost_per_kb_read == 0.0001
        assert config.cost_per_kb_write == 0.0002
        assert config.cpu_cost_per_row == 0.000001
        assert config.cost_per_gb_per_day == 0.03
        assert config.hourly_rate == 150.0
        assert config.risk_multiplier == 1.2

    def test_custom_configuration(self):
        """Test custom cost configuration."""
        config = CostConfiguration(
            cost_per_kb_read=0.0002,
            cost_per_kb_write=0.0004,
            hourly_rate=200.0,
            risk_multiplier=1.5,
        )

        assert config.cost_per_kb_read == 0.0002
        assert config.cost_per_kb_write == 0.0004
        assert config.hourly_rate == 200.0
        assert config.risk_multiplier == 1.5

    def test_negative_read_cost_raises_error(self):
        """Test that negative read cost raises ValueError."""
        with pytest.raises(ValueError, match="cost_per_kb_read must be non-negative"):
            CostConfiguration(cost_per_kb_read=-0.0001)

    def test_negative_write_cost_raises_error(self):
        """Test that negative write cost raises ValueError."""
        with pytest.raises(ValueError, match="cost_per_kb_write must be non-negative"):
            CostConfiguration(cost_per_kb_write=-0.0002)

    def test_zero_hourly_rate_raises_error(self):
        """Test that zero or negative hourly rate raises ValueError."""
        with pytest.raises(ValueError, match="hourly_rate must be positive"):
            CostConfiguration(hourly_rate=0.0)

        with pytest.raises(ValueError, match="hourly_rate must be positive"):
            CostConfiguration(hourly_rate=-150.0)


class TestCostBreakdown:
    """Test CostBreakdown data structure."""

    def test_default_breakdown(self):
        """Test default cost breakdown (all zeros)."""
        breakdown = CostBreakdown()

        assert breakdown.read_cost == 0.0
        assert breakdown.write_cost == 0.0
        assert breakdown.cpu_cost == 0.0
        assert breakdown.storage_cost == 0.0
        assert breakdown.network_cost == 0.0
        assert breakdown.total_cost == 0.0

    def test_breakdown_with_costs(self):
        """Test cost breakdown with various cost components."""
        breakdown = CostBreakdown(
            read_cost=10.0,
            write_cost=5.0,
            cpu_cost=2.5,
            storage_cost=1.0,
            network_cost=0.5,
        )

        assert breakdown.read_cost == 10.0
        assert breakdown.write_cost == 5.0
        assert breakdown.cpu_cost == 2.5
        assert breakdown.storage_cost == 1.0
        assert breakdown.network_cost == 0.5
        assert breakdown.total_cost == 19.0

    def test_breakdown_with_other_costs(self):
        """Test cost breakdown with other costs dictionary."""
        breakdown = CostBreakdown(
            read_cost=10.0,
            write_cost=5.0,
            other_costs={"chain_overhead": 3.0, "index_maintenance": 2.0},
        )

        assert breakdown.other_costs["chain_overhead"] == 3.0
        assert breakdown.other_costs["index_maintenance"] == 2.0
        assert breakdown.total_cost == 20.0  # 10 + 5 + 3 + 2

    def test_total_cost_calculation(self):
        """Test that total cost is calculated correctly."""
        breakdown = CostBreakdown(
            read_cost=100.0,
            write_cost=50.0,
            cpu_cost=25.0,
            storage_cost=10.0,
            network_cost=5.0,
            other_costs={"misc": 10.0},
        )

        assert breakdown.total_cost == 200.0


class TestCostEstimate:
    """Test CostEstimate data structure."""

    def test_basic_cost_estimate(self):
        """Test basic cost estimate with automatic calculations."""
        estimate = CostEstimate(
            pattern_id="test_001",
            pattern_type="LOB_CLIFF",
            affected_objects=["TABLE1.COL1"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=40.0,
            implementation_cost=5000.0,
        )

        # Check automatic calculations
        assert estimate.annual_savings == 60.0 * 365  # (100 - 40) * 365 = 21,900
        assert estimate.net_benefit == 21900.0 - 5000.0  # 16,900
        assert estimate.roi_percentage == (16900.0 / 5000.0) * 100  # 338%
        assert estimate.payback_period_days == int(5000.0 / 60.0)  # 83 days

    def test_cost_estimate_with_manual_values(self):
        """Test cost estimate with manually provided calculated values."""
        estimate = CostEstimate(
            pattern_id="test_002",
            pattern_type="EXPENSIVE_JOIN",
            affected_objects=["ORDERS", "CUSTOMERS"],
            current_cost_per_day=1000.0,
            optimized_cost_per_day=100.0,
            implementation_cost=10000.0,
            annual_savings=328500.0,  # Manual value
            net_benefit=318500.0,  # Manual value
            roi_percentage=3185.0,  # Manual value
            payback_period_days=11,  # Manual value
        )

        # Check that manual values are preserved
        assert estimate.annual_savings == 328500.0
        assert estimate.net_benefit == 318500.0
        assert estimate.roi_percentage == 3185.0
        assert estimate.payback_period_days == 11

    def test_cost_estimate_zero_implementation_cost(self):
        """Test cost estimate with zero implementation cost."""
        estimate = CostEstimate(
            pattern_id="test_003",
            pattern_type="DUALITY_VIEW",
            affected_objects=["PRODUCTS"],
            current_cost_per_day=50.0,
            optimized_cost_per_day=25.0,
            implementation_cost=0.0,
        )

        # ROI should be infinite or very high with zero implementation cost
        # Our implementation avoids division by zero
        assert estimate.annual_savings == 25.0 * 365
        assert estimate.net_benefit == 25.0 * 365

    def test_cost_estimate_negative_savings(self):
        """Test cost estimate where optimization costs more (negative savings)."""
        estimate = CostEstimate(
            pattern_id="test_004",
            pattern_type="DOCUMENT_CANDIDATE",
            affected_objects=["USER_PROFILES"],
            current_cost_per_day=50.0,
            optimized_cost_per_day=75.0,  # More expensive!
            implementation_cost=5000.0,
        )

        # Negative savings
        assert estimate.annual_savings == -25.0 * 365  # -9,125
        assert estimate.net_benefit == -9125.0 - 5000.0  # -14,125
        assert estimate.roi_percentage < 0  # Negative ROI

    def test_is_cost_effective_property(self):
        """Test is_cost_effective property."""
        # Cost-effective case
        estimate1 = CostEstimate(
            pattern_id="test_005",
            pattern_type="LOB_CLIFF",
            affected_objects=["TABLE1"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=40.0,
            implementation_cost=1000.0,
        )
        assert estimate1.is_cost_effective is True

        # Not cost-effective case
        estimate2 = CostEstimate(
            pattern_id="test_006",
            pattern_type="LOB_CLIFF",
            affected_objects=["TABLE2"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=40.0,
            implementation_cost=50000.0,  # Very high implementation cost
        )
        assert estimate2.is_cost_effective is False

    def test_to_dict_serialization(self):
        """Test to_dict method for JSON serialization."""
        estimate = CostEstimate(
            pattern_id="test_007",
            pattern_type="LOB_CLIFF",
            affected_objects=["AUDIT_LOGS.PAYLOAD"],
            current_cost_per_day=13.80,
            optimized_cost_per_day=5.64,
            implementation_cost=3500.0,
            confidence=0.85,
            assumptions=["Assumes 30% read improvement", "5% update selectivity"],
        )

        result = estimate.to_dict()

        assert result["pattern_id"] == "test_007"
        assert result["pattern_type"] == "LOB_CLIFF"
        assert result["affected_objects"] == ["AUDIT_LOGS.PAYLOAD"]
        assert result["costs"]["current_per_day"] == 13.80
        assert result["costs"]["optimized_per_day"] == 5.64
        assert result["costs"]["implementation"] == 3500.0
        assert result["confidence"] == 0.85
        assert len(result["assumptions"]) == 2

    def test_to_dict_with_priority(self):
        """Test to_dict with priority scoring."""
        estimate = CostEstimate(
            pattern_id="test_008",
            pattern_type="EXPENSIVE_JOIN",
            affected_objects=["ORDERS", "CUSTOMERS"],
            current_cost_per_day=1000.0,
            optimized_cost_per_day=100.0,
            implementation_cost=8000.0,
            priority_score=95.5,
            priority_tier="HIGH",
        )

        result = estimate.to_dict()

        assert result["priority"]["score"] == 95.5
        assert result["priority"]["tier"] == "HIGH"

    def test_payback_period_zero_savings(self):
        """Test payback period calculation when there are no savings."""
        estimate = CostEstimate(
            pattern_id="test_009",
            pattern_type="LOB_CLIFF",
            affected_objects=["TABLE1"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=100.0,  # No change
            implementation_cost=5000.0,
        )

        # With zero daily savings, payback period cannot be calculated
        # Our implementation should handle this gracefully
        assert estimate.annual_savings == 0.0
        # Payback period should be None or very large
        assert estimate.payback_period_days is None or estimate.payback_period_days > 1000000


class TestImplementationCostEstimate:
    """Test ImplementationCostEstimate data structure."""

    def test_default_implementation_cost(self):
        """Test default implementation cost estimate."""
        impl_cost = ImplementationCostEstimate()

        assert impl_cost.schema_changes_hours == 0.0
        assert impl_cost.migration_hours == 0.0
        assert impl_cost.app_changes_hours == 0.0
        assert impl_cost.testing_hours == 0.0
        assert impl_cost.risk_factor == 1.0
        assert impl_cost.total_hours == 0.0

    def test_implementation_cost_calculation(self):
        """Test implementation cost calculation."""
        impl_cost = ImplementationCostEstimate(
            schema_changes_hours=8.0,
            migration_hours=16.0,
            app_changes_hours=40.0,
            testing_hours=16.0,
            risk_factor=1.2,
        )

        assert impl_cost.total_hours == 80.0  # 8 + 16 + 40 + 16
        total_cost = impl_cost.calculate_cost(hourly_rate=150.0)
        assert total_cost == 80.0 * 150.0 * 1.2  # $14,400

    def test_implementation_cost_no_risk(self):
        """Test implementation cost with no risk factor."""
        impl_cost = ImplementationCostEstimate(
            schema_changes_hours=10.0,
            migration_hours=20.0,
            risk_factor=1.0,  # No risk buffer
        )

        total_cost = impl_cost.calculate_cost(hourly_rate=200.0)
        assert total_cost == 30.0 * 200.0  # $6,000

    def test_implementation_cost_high_risk(self):
        """Test implementation cost with high risk factor."""
        impl_cost = ImplementationCostEstimate(
            schema_changes_hours=20.0,
            app_changes_hours=80.0,
            testing_hours=20.0,
            risk_factor=1.5,  # 50% risk buffer
        )

        total_cost = impl_cost.calculate_cost(hourly_rate=150.0)
        assert total_cost == 120.0 * 150.0 * 1.5  # $27,000


class TestCostEstimateEdgeCases:
    """Test edge cases for cost estimation."""

    def test_very_small_costs(self):
        """Test cost estimate with very small costs."""
        estimate = CostEstimate(
            pattern_id="test_010",
            pattern_type="LOB_CLIFF",
            affected_objects=["TABLE1"],
            current_cost_per_day=0.01,
            optimized_cost_per_day=0.005,
            implementation_cost=100.0,
        )

        assert estimate.annual_savings == pytest.approx(0.005 * 365, rel=1e-6)
        assert estimate.is_cost_effective is False  # $1.83/year savings vs $100 impl

    def test_very_large_costs(self):
        """Test cost estimate with very large costs."""
        estimate = CostEstimate(
            pattern_id="test_011",
            pattern_type="EXPENSIVE_JOIN",
            affected_objects=["ORDERS", "CUSTOMERS"],
            current_cost_per_day=10000.0,
            optimized_cost_per_day=1000.0,
            implementation_cost=50000.0,
        )

        assert estimate.annual_savings == 9000.0 * 365  # $3,285,000
        assert estimate.net_benefit > 3000000.0
        assert estimate.is_cost_effective is True

    def test_equal_current_and_optimized_costs(self):
        """Test when current and optimized costs are equal."""
        estimate = CostEstimate(
            pattern_id="test_012",
            pattern_type="LOB_CLIFF",
            affected_objects=["TABLE1"],
            current_cost_per_day=50.0,
            optimized_cost_per_day=50.0,
            implementation_cost=1000.0,
        )

        assert estimate.annual_savings == 0.0
        assert estimate.net_benefit == -1000.0
        assert estimate.is_cost_effective is False
