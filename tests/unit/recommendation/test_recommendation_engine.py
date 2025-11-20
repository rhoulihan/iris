"""Unit tests for recommendation engine core."""

from src.recommendation.cost_models import CostEstimate
from src.recommendation.models import DetectedPattern, WorkloadFeatures
from src.recommendation.recommendation_engine import (
    Alternative,
    Implementation,
    Rationale,
    RecommendationEngine,
    SchemaRecommendation,
    Tradeoff,
)
from src.recommendation.tradeoff_analyzer import OptimizationConflict, TradeoffAnalysis


# Test fixtures
def create_lob_pattern() -> DetectedPattern:
    """Create a test LOB cliff pattern."""
    return DetectedPattern(
        pattern_id="PAT-LOB-001",
        pattern_type="LOB_CLIFF",
        severity="HIGH",
        confidence=0.85,
        affected_objects=["PRODUCTS.description"],
        description="Large CLOB with frequent small updates",
        metrics={"document_size_kb": 50, "update_frequency": 200},
        recommendation_hint="Split LOB into separate table",
    )


def create_join_pattern() -> DetectedPattern:
    """Create a test expensive join pattern."""
    return DetectedPattern(
        pattern_id="PAT-JOIN-001",
        pattern_type="EXPENSIVE_JOIN",
        severity="MEDIUM",
        confidence=0.75,
        affected_objects=["CUSTOMERS", "ORDERS"],
        description="Frequent join with high row count",
        metrics={"join_frequency": 500, "rows_joined": 100000},
        recommendation_hint="Consider denormalization",
    )


def create_document_pattern() -> DetectedPattern:
    """Create a test document candidate pattern."""
    return DetectedPattern(
        pattern_id="PAT-DOC-001",
        pattern_type="DOCUMENT_CANDIDATE",
        severity="MEDIUM",
        confidence=0.70,
        affected_objects=["USER_PREFERENCES"],
        description="Relational table suitable for JSON storage",
        metrics={"select_star_pct": 0.8, "flexibility_score": 0.7},
        recommendation_hint="Convert to JSON collection",
    )


def create_duality_pattern() -> DetectedPattern:
    """Create a test duality view pattern."""
    return DetectedPattern(
        pattern_id="PAT-DV-001",
        pattern_type="DUALITY_VIEW_OPPORTUNITY",
        severity="HIGH",
        confidence=0.90,
        affected_objects=["CUSTOMERS"],
        description="Mixed OLTP and Analytics access",
        metrics={"oltp_pct": 0.70, "analytics_pct": 0.25},
        recommendation_hint="Create JSON Duality View",
    )


def create_cost_estimate(pattern: DetectedPattern) -> CostEstimate:
    """Create a test cost estimate for a pattern."""
    return CostEstimate(
        pattern_id=pattern.pattern_id,
        pattern_type=pattern.pattern_type,
        affected_objects=pattern.affected_objects,
        current_cost_per_day=1000.0,
        optimized_cost_per_day=400.0,
        implementation_cost=5000.0,
        annual_savings=219000.0,
        roi_percentage=4280.0,
        payback_period_days=8,
        priority_score=75.5,
        priority_tier="HIGH",
    )


def create_tradeoff_analysis(pattern_id: str) -> TradeoffAnalysis:
    """Create a test tradeoff analysis."""
    return TradeoffAnalysis(
        pattern_id=pattern_id,
        high_frequency_queries=[],
        low_frequency_queries=[],
        weighted_improvement_pct=45.0,
        weighted_degradation_pct=2.0,
        net_benefit_score=43.0,
        overhead_justified=True,
        break_even_threshold=5.0,
        recommendation="APPROVE",
        conditions=[],
    )


def create_workload_features() -> WorkloadFeatures:
    """Create a test WorkloadFeatures instance."""
    return WorkloadFeatures(
        queries=[],
        total_executions=1000,
        unique_patterns=10,
    )


class TestSchemaRecommendation:
    """Test SchemaRecommendation data model."""

    def test_create_recommendation(self):
        """Test creating a schema recommendation."""
        recommendation = SchemaRecommendation(
            recommendation_id="REC-001",
            pattern_id="PAT-001",
            type="LOB_CLIFF",
            priority="HIGH",
            target_objects=["PRODUCTS.description"],
            description="Split large CLOB to avoid LOB cliffs",
            rationale=Rationale(
                pattern_detected="Large CLOB with frequent updates",
                current_cost="High I/O cost from LOB chaining",
                expected_benefit="60% reduction in I/O overhead",
            ),
            implementation=Implementation(
                sql="CREATE TABLE products_description ...",
                rollback_plan="DROP TABLE products_description; ALTER TABLE ...",
                testing_approach="Shadow testing for 1 week",
            ),
            estimated_improvement_pct=60.0,
            estimated_cost=5000.0,
            annual_savings=219000.0,
            roi_percentage=4280.0,
            tradeoffs=[],
            alternatives=[],
        )

        assert recommendation.recommendation_id == "REC-001"
        assert recommendation.type == "LOB_CLIFF"
        assert recommendation.priority == "HIGH"


class TestRationale:
    """Test Rationale data model."""

    def test_create_rationale(self):
        """Test creating a rationale."""
        rationale = Rationale(
            pattern_detected="High-frequency join",
            current_cost="1000ms avg query time",
            expected_benefit="70% improvement with denormalization",
        )

        assert rationale.pattern_detected == "High-frequency join"
        assert "1000ms" in rationale.current_cost


class TestImplementation:
    """Test Implementation data model."""

    def test_create_implementation(self):
        """Test creating an implementation."""
        impl = Implementation(
            sql="CREATE INDEX idx_customers_email ON customers(email)",
            rollback_plan="DROP INDEX idx_customers_email",
            testing_approach="Create in test environment first",
        )

        assert "CREATE INDEX" in impl.sql
        assert "DROP INDEX" in impl.rollback_plan


class TestTradeoff:
    """Test Tradeoff data model."""

    def test_create_tradeoff(self):
        """Test creating a tradeoff."""
        tradeoff = Tradeoff(
            description="2% storage overhead",
            justified_by="60% query performance improvement",
        )

        assert "storage overhead" in tradeoff.description
        assert "60%" in tradeoff.justified_by


class TestAlternative:
    """Test Alternative data model."""

    def test_create_alternative(self):
        """Test creating an alternative approach."""
        alternative = Alternative(
            approach="Use materialized view instead",
            pros=["Simpler implementation", "Easier rollback"],
            cons=["Refresh overhead", "Data staleness"],
        )

        assert alternative.approach == "Use materialized view instead"
        assert len(alternative.pros) == 2
        assert len(alternative.cons) == 2


class TestRecommendationEngineInitialization:
    """Test RecommendationEngine initialization."""

    def test_create_engine(self):
        """Test creating a recommendation engine."""
        engine = RecommendationEngine()
        assert engine is not None


class TestLOBRecommendationGeneration:
    """Test recommendation generation for LOB cliff patterns."""

    def test_generate_lob_recommendation(self):
        """Should generate recommendation for LOB cliff pattern."""
        engine = RecommendationEngine()
        pattern = create_lob_pattern()
        cost_estimate = create_cost_estimate(pattern)
        tradeoff = create_tradeoff_analysis(pattern.pattern_id)

        recommendation = engine.generate_recommendation(
            pattern=pattern,
            cost_estimate=cost_estimate,
            tradeoff_analysis=tradeoff,
            conflicts=[],
        )

        assert recommendation is not None
        assert recommendation.type == "LOB_CLIFF"
        assert recommendation.pattern_id == pattern.pattern_id
        assert recommendation.priority == "HIGH"
        assert len(recommendation.target_objects) == 1
        assert "PRODUCTS.description" in recommendation.target_objects

    def test_lob_recommendation_includes_rationale(self):
        """LOB recommendation should include detailed rationale."""
        engine = RecommendationEngine()
        pattern = create_lob_pattern()
        cost_estimate = create_cost_estimate(pattern)
        tradeoff = create_tradeoff_analysis(pattern.pattern_id)

        recommendation = engine.generate_recommendation(pattern, cost_estimate, tradeoff, [])

        assert recommendation.rationale is not None
        assert len(recommendation.rationale.pattern_detected) > 0
        assert len(recommendation.rationale.current_cost) > 0
        assert len(recommendation.rationale.expected_benefit) > 0

    def test_lob_recommendation_includes_implementation(self):
        """LOB recommendation should include implementation details."""
        engine = RecommendationEngine()
        pattern = create_lob_pattern()
        cost_estimate = create_cost_estimate(pattern)
        tradeoff = create_tradeoff_analysis(pattern.pattern_id)

        recommendation = engine.generate_recommendation(pattern, cost_estimate, tradeoff, [])

        assert recommendation.implementation is not None
        assert len(recommendation.implementation.sql) > 0
        assert len(recommendation.implementation.rollback_plan) > 0
        assert len(recommendation.implementation.testing_approach) > 0


class TestJoinRecommendationGeneration:
    """Test recommendation generation for expensive join patterns."""

    def test_generate_join_recommendation(self):
        """Should generate recommendation for expensive join pattern."""
        engine = RecommendationEngine()
        pattern = create_join_pattern()
        cost_estimate = create_cost_estimate(pattern)
        tradeoff = create_tradeoff_analysis(pattern.pattern_id)

        recommendation = engine.generate_recommendation(pattern, cost_estimate, tradeoff, [])

        assert recommendation is not None
        assert recommendation.type == "EXPENSIVE_JOIN"
        assert recommendation.pattern_id == pattern.pattern_id
        assert "CUSTOMERS" in recommendation.target_objects
        assert "ORDERS" in recommendation.target_objects


class TestDocumentRecommendationGeneration:
    """Test recommendation generation for document candidate patterns."""

    def test_generate_document_recommendation(self):
        """Should generate recommendation for document candidate pattern."""
        engine = RecommendationEngine()
        pattern = create_document_pattern()
        cost_estimate = create_cost_estimate(pattern)
        tradeoff = create_tradeoff_analysis(pattern.pattern_id)

        recommendation = engine.generate_recommendation(pattern, cost_estimate, tradeoff, [])

        assert recommendation is not None
        assert recommendation.type == "DOCUMENT_CANDIDATE"
        assert "USER_PREFERENCES" in recommendation.target_objects


class TestDualityViewRecommendationGeneration:
    """Test recommendation generation for duality view patterns."""

    def test_generate_duality_view_recommendation(self):
        """Should generate recommendation for duality view pattern."""
        engine = RecommendationEngine()
        pattern = create_duality_pattern()
        cost_estimate = create_cost_estimate(pattern)
        tradeoff = create_tradeoff_analysis(pattern.pattern_id)

        recommendation = engine.generate_recommendation(pattern, cost_estimate, tradeoff, [])

        assert recommendation is not None
        assert recommendation.type == "DUALITY_VIEW_OPPORTUNITY"
        assert "CUSTOMERS" in recommendation.target_objects


class TestRecommendationWithConflicts:
    """Test recommendation generation with conflicts."""

    def test_recommendation_includes_conflict_warning(self):
        """Should include conflict warnings in recommendation."""
        engine = RecommendationEngine()
        pattern = create_document_pattern()
        cost_estimate = create_cost_estimate(pattern)
        tradeoff = create_tradeoff_analysis(pattern.pattern_id)

        conflict = OptimizationConflict(
            pattern_a_id=pattern.pattern_id,
            pattern_b_id="PAT-JOIN-002",
            conflict_type="INCOMPATIBLE",
            affected_objects=["USER_PREFERENCES"],
            description="Document and join optimization conflict",
            resolution_strategy="DUALITY_VIEW",
            rationale="Use Duality View to support both patterns",
        )

        recommendation = engine.generate_recommendation(
            pattern, cost_estimate, tradeoff, [conflict]
        )

        # Should add conflict as a tradeoff or alternative
        assert len(recommendation.tradeoffs) > 0 or len(recommendation.alternatives) > 0


class TestBulkRecommendationGeneration:
    """Test generating multiple recommendations."""

    def test_generate_multiple_recommendations(self):
        """Should generate recommendations for multiple patterns."""
        engine = RecommendationEngine()

        patterns = [
            create_lob_pattern(),
            create_join_pattern(),
            create_document_pattern(),
        ]

        cost_estimates = {p.pattern_id: create_cost_estimate(p) for p in patterns}

        tradeoff_analyses = {p.pattern_id: create_tradeoff_analysis(p.pattern_id) for p in patterns}

        recommendations = engine.generate_recommendations(
            patterns=patterns,
            cost_estimates=cost_estimates,
            tradeoff_analyses=tradeoff_analyses,
            conflicts=[],
        )

        assert len(recommendations) == 3
        assert all(r.recommendation_id.startswith("REC-") for r in recommendations)

    def test_recommendations_sorted_by_priority(self):
        """Should return recommendations sorted by priority score."""
        engine = RecommendationEngine()

        # Create patterns with different priorities
        pattern_high = create_lob_pattern()
        pattern_med = create_join_pattern()
        pattern_low = create_document_pattern()

        patterns = [pattern_low, pattern_high, pattern_med]

        # Create cost estimates with different priority scores
        cost_high = create_cost_estimate(pattern_high)
        cost_high.priority_score = 85.0
        cost_high.priority_tier = "HIGH"

        cost_med = create_cost_estimate(pattern_med)
        cost_med.priority_score = 55.0
        cost_med.priority_tier = "MEDIUM"

        cost_low = create_cost_estimate(pattern_low)
        cost_low.priority_score = 25.0
        cost_low.priority_tier = "LOW"

        cost_estimates = {
            pattern_high.pattern_id: cost_high,
            pattern_med.pattern_id: cost_med,
            pattern_low.pattern_id: cost_low,
        }

        tradeoff_analyses = {p.pattern_id: create_tradeoff_analysis(p.pattern_id) for p in patterns}

        recommendations = engine.generate_recommendations(
            patterns, cost_estimates, tradeoff_analyses, []
        )

        # Should be sorted HIGH -> MEDIUM -> LOW
        assert recommendations[0].priority == "HIGH"
        assert recommendations[1].priority == "MEDIUM"
        assert recommendations[2].priority == "LOW"


class TestEdgeCases:
    """Test edge cases in recommendation generation."""

    def test_empty_patterns_list(self):
        """Should handle empty patterns list."""
        engine = RecommendationEngine()

        recommendations = engine.generate_recommendations(
            patterns=[],
            cost_estimates={},
            tradeoff_analyses={},
            conflicts=[],
        )

        assert recommendations == []

    def test_pattern_without_cost_estimate(self):
        """Should handle pattern without cost estimate gracefully."""
        engine = RecommendationEngine()
        pattern = create_lob_pattern()
        tradeoff = create_tradeoff_analysis(pattern.pattern_id)

        # Missing cost estimate - should handle gracefully
        try:
            recommendation = engine.generate_recommendation(
                pattern=pattern,
                cost_estimate=None,
                tradeoff_analysis=tradeoff,
                conflicts=[],
            )
            # Should return None or raise appropriate error
            assert recommendation is None
        except ValueError:
            # Or raise ValueError - both acceptable
            pass

    def test_pattern_with_rejected_tradeoff(self):
        """Should not generate recommendation if tradeoff is rejected."""
        engine = RecommendationEngine()
        pattern = create_lob_pattern()
        cost_estimate = create_cost_estimate(pattern)

        # Tradeoff analysis that rejects the optimization
        tradeoff = TradeoffAnalysis(
            pattern_id=pattern.pattern_id,
            high_frequency_queries=[],
            low_frequency_queries=[],
            weighted_improvement_pct=5.0,
            weighted_degradation_pct=25.0,
            net_benefit_score=-20.0,
            overhead_justified=False,
            break_even_threshold=50.0,
            recommendation="REJECT",
            conditions=[],
        )

        recommendation = engine.generate_recommendation(pattern, cost_estimate, tradeoff, [])

        # Should return None for rejected recommendations
        assert recommendation is None
