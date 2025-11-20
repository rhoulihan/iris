"""Unit tests for tradeoff analyzer."""

from src.recommendation.cost_models import CostEstimate
from src.recommendation.models import ColumnMetadata, TableMetadata, WorkloadFeatures
from src.recommendation.tradeoff_analyzer import (
    OptimizationConflict,
    QueryFrequencyProfile,
    TradeoffAnalysis,
    TradeoffAnalyzer,
)


# Test fixtures
def create_table_metadata(name: str = "TEST_TABLE") -> TableMetadata:
    """Create a test TableMetadata instance."""
    return TableMetadata(
        name=name,
        schema="TEST_SCHEMA",
        num_rows=1000,
        avg_row_len=100,
        columns=[
            ColumnMetadata(
                name="id",
                data_type="NUMBER",
                nullable=False,
            )
        ],
    )


def create_workload_features() -> WorkloadFeatures:
    """Create a test WorkloadFeatures instance."""
    return WorkloadFeatures(
        queries=[],
        total_executions=1000,
        unique_patterns=10,
    )


class TestQueryFrequencyProfile:
    """Test QueryFrequencyProfile data model."""

    def test_create_profile(self):
        """Test creating a query frequency profile."""
        profile = QueryFrequencyProfile(
            query_type="SELECT",
            daily_executions=1000,
            avg_response_time_ms=50.0,
            p95_response_time_ms=150.0,
            percentage_of_workload=0.65,
        )

        assert profile.query_type == "SELECT"
        assert profile.daily_executions == 1000
        assert profile.percentage_of_workload == 0.65


class TestOptimizationConflict:
    """Test OptimizationConflict data model."""

    def test_create_conflict(self):
        """Test creating an optimization conflict."""
        conflict = OptimizationConflict(
            pattern_a_id="PAT-001",
            pattern_b_id="PAT-002",
            conflict_type="INCOMPATIBLE",
            affected_objects=["CUSTOMERS"],
            description="Cannot apply both document and relational optimization",
            resolution_strategy="DUALITY_VIEW",
            rationale="Use Duality View to support both access patterns",
        )

        assert conflict.conflict_type == "INCOMPATIBLE"
        assert conflict.resolution_strategy == "DUALITY_VIEW"
        assert "CUSTOMERS" in conflict.affected_objects


class TestTradeoffAnalysis:
    """Test TradeoffAnalysis data model."""

    def test_create_analysis(self):
        """Test creating a tradeoff analysis."""
        high_freq = QueryFrequencyProfile(
            query_type="SELECT",
            daily_executions=1000,
            avg_response_time_ms=100.0,
            p95_response_time_ms=200.0,
            percentage_of_workload=0.8,
        )

        analysis = TradeoffAnalysis(
            pattern_id="PAT-001",
            high_frequency_queries=[high_freq],
            low_frequency_queries=[],
            weighted_improvement_pct=45.0,
            weighted_degradation_pct=2.0,
            net_benefit_score=43.0,
            overhead_justified=True,
            break_even_threshold=5.0,
            recommendation="APPROVE",
            conditions=[],
        )

        assert analysis.net_benefit_score == 43.0
        assert analysis.overhead_justified is True
        assert analysis.recommendation == "APPROVE"


class TestConflictDetection:
    """Test conflict detection between optimizations."""

    def test_detect_document_vs_relational_conflict(self):
        """Should detect conflict between document and relational patterns."""
        analyzer = TradeoffAnalyzer()

        doc_estimate = CostEstimate(
            pattern_id="PAT-001",
            pattern_type="DOCUMENT_CANDIDATE",
            affected_objects=["CUSTOMERS"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=60.0,
            implementation_cost=5000.0,
        )

        join_estimate = CostEstimate(
            pattern_id="PAT-002",
            pattern_type="EXPENSIVE_JOIN",
            affected_objects=["CUSTOMERS", "ORDERS"],
            current_cost_per_day=200.0,
            optimized_cost_per_day=80.0,
            implementation_cost=8000.0,
        )

        conflicts = analyzer.detect_conflicts(
            [doc_estimate, join_estimate],
            {"CUSTOMERS": create_table_metadata("CUSTOMERS")},
        )

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "INCOMPATIBLE"
        assert conflicts[0].resolution_strategy == "DUALITY_VIEW"
        assert "CUSTOMERS" in conflicts[0].affected_objects

    def test_detect_lob_vs_document_conflict(self):
        """Should detect conflict between LOB and document patterns."""
        analyzer = TradeoffAnalyzer()

        lob_estimate = CostEstimate(
            pattern_id="PAT-003",
            pattern_type="LOB_CLIFF",
            affected_objects=["PRODUCTS.description"],
            current_cost_per_day=150.0,
            optimized_cost_per_day=50.0,
            implementation_cost=3000.0,
        )

        doc_estimate = CostEstimate(
            pattern_id="PAT-004",
            pattern_type="DOCUMENT_CANDIDATE",
            affected_objects=["PRODUCTS"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=60.0,
            implementation_cost=5000.0,
        )

        conflicts = analyzer.detect_conflicts(
            [lob_estimate, doc_estimate],
            {"PRODUCTS": create_table_metadata("PRODUCTS")},
        )

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "INCOMPATIBLE"

    def test_no_conflict_different_tables(self):
        """Should not detect conflict when tables don't overlap."""
        analyzer = TradeoffAnalyzer()

        estimate1 = CostEstimate(
            pattern_id="PAT-005",
            pattern_type="LOB_CLIFF",
            affected_objects=["TABLE_A.col1"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=60.0,
            implementation_cost=5000.0,
        )

        estimate2 = CostEstimate(
            pattern_id="PAT-006",
            pattern_type="EXPENSIVE_JOIN",
            affected_objects=["TABLE_B", "TABLE_C"],
            current_cost_per_day=200.0,
            optimized_cost_per_day=80.0,
            implementation_cost=8000.0,
        )

        conflicts = analyzer.detect_conflicts(
            [estimate1, estimate2],
            {},
        )

        assert len(conflicts) == 0

    def test_no_conflict_compatible_patterns(self):
        """Should not detect conflict for compatible pattern types."""
        analyzer = TradeoffAnalyzer()

        # Two LOB optimizations on same table (compatible)
        estimate1 = CostEstimate(
            pattern_id="PAT-007",
            pattern_type="LOB_CLIFF",
            affected_objects=["AUDIT.payload"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=60.0,
            implementation_cost=5000.0,
        )

        estimate2 = CostEstimate(
            pattern_id="PAT-008",
            pattern_type="LOB_CLIFF",
            affected_objects=["AUDIT.metadata"],
            current_cost_per_day=80.0,
            optimized_cost_per_day=30.0,
            implementation_cost=4000.0,
        )

        conflicts = analyzer.detect_conflicts(
            [estimate1, estimate2],
            {"AUDIT": create_table_metadata("AUDIT")},
        )

        # Same pattern type is compatible
        assert len(conflicts) == 0

    def test_resolution_strategy_prioritize_by_score(self):
        """Should prioritize higher-scoring pattern when no Duality View."""
        analyzer = TradeoffAnalyzer()

        # LOB cliff with high priority
        high_priority = CostEstimate(
            pattern_id="PAT-009",
            pattern_type="LOB_CLIFF",
            affected_objects=["DATA.payload"],
            current_cost_per_day=200.0,
            optimized_cost_per_day=50.0,
            implementation_cost=3000.0,
            priority_score=85.0,
        )

        # Document candidate with lower priority
        low_priority = CostEstimate(
            pattern_id="PAT-010",
            pattern_type="DOCUMENT_CANDIDATE",
            affected_objects=["DATA"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=70.0,
            implementation_cost=5000.0,
            priority_score=55.0,
        )

        conflicts = analyzer.detect_conflicts(
            [high_priority, low_priority],
            {"DATA": create_table_metadata("DATA")},
        )

        assert len(conflicts) == 1
        assert conflicts[0].resolution_strategy == "PRIORITIZE_A"


class TestAffectedTablesExtraction:
    """Test extraction of affected tables from cost estimates."""

    def test_extract_table_from_table_column(self):
        """Should extract table name from 'TABLE.COLUMN' format."""
        analyzer = TradeoffAnalyzer()

        estimate = CostEstimate(
            pattern_id="PAT-011",
            pattern_type="LOB_CLIFF",
            affected_objects=["CUSTOMERS.profile", "CUSTOMERS.preferences"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=60.0,
            implementation_cost=5000.0,
        )

        tables = analyzer._get_affected_tables(estimate)

        assert tables == ["CUSTOMERS"]

    def test_extract_multiple_tables(self):
        """Should extract multiple table names."""
        analyzer = TradeoffAnalyzer()

        estimate = CostEstimate(
            pattern_id="PAT-012",
            pattern_type="EXPENSIVE_JOIN",
            affected_objects=["ORDERS", "CUSTOMERS", "PRODUCTS"],
            current_cost_per_day=200.0,
            optimized_cost_per_day=80.0,
            implementation_cost=8000.0,
        )

        tables = analyzer._get_affected_tables(estimate)

        assert set(tables) == {"ORDERS", "CUSTOMERS", "PRODUCTS"}

    def test_deduplicate_tables(self):
        """Should deduplicate table names."""
        analyzer = TradeoffAnalyzer()

        estimate = CostEstimate(
            pattern_id="PAT-013",
            pattern_type="LOB_CLIFF",
            affected_objects=["AUDIT.col1", "AUDIT.col2", "AUDIT.col3"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=60.0,
            implementation_cost=5000.0,
        )

        tables = analyzer._get_affected_tables(estimate)

        assert tables == ["AUDIT"]


class TestIncompatibilityCheck:
    """Test pattern incompatibility checking."""

    def test_document_vs_join_incompatible(self):
        """Document and expensive join patterns are incompatible."""
        analyzer = TradeoffAnalyzer()

        assert analyzer._is_incompatible("DOCUMENT_CANDIDATE", "EXPENSIVE_JOIN")
        assert analyzer._is_incompatible("EXPENSIVE_JOIN", "DOCUMENT_CANDIDATE")

    def test_lob_vs_document_incompatible(self):
        """LOB cliff and document candidate are incompatible."""
        analyzer = TradeoffAnalyzer()

        assert analyzer._is_incompatible("LOB_CLIFF", "DOCUMENT_CANDIDATE")
        assert analyzer._is_incompatible("DOCUMENT_CANDIDATE", "LOB_CLIFF")

    def test_same_pattern_compatible(self):
        """Same pattern types are compatible."""
        analyzer = TradeoffAnalyzer()

        assert not analyzer._is_incompatible("LOB_CLIFF", "LOB_CLIFF")
        assert not analyzer._is_incompatible("EXPENSIVE_JOIN", "EXPENSIVE_JOIN")

    def test_lob_vs_join_compatible(self):
        """LOB cliff and expensive join are compatible."""
        analyzer = TradeoffAnalyzer()

        assert not analyzer._is_incompatible("LOB_CLIFF", "EXPENSIVE_JOIN")

    def test_duality_patterns_compatible(self):
        """Duality view patterns are compatible with most patterns."""
        analyzer = TradeoffAnalyzer()

        assert not analyzer._is_incompatible("DUALITY_VIEW_OPPORTUNITY", "EXPENSIVE_JOIN")
        assert not analyzer._is_incompatible("DUALITY_VIEW_OPPORTUNITY", "LOB_CLIFF")


class TestTradeoffAnalyzer:
    """Test main TradeoffAnalyzer functionality."""

    def test_analyze_single_estimate(self):
        """Should analyze tradeoffs for a single estimate."""
        analyzer = TradeoffAnalyzer()

        estimate = CostEstimate(
            pattern_id="PAT-014",
            pattern_type="LOB_CLIFF",
            affected_objects=["AUDIT.payload"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=40.0,
            implementation_cost=5000.0,
        )

        workload = create_workload_features()

        analyses = analyzer.analyze([estimate], workload)

        assert "PAT-014" in analyses
        assert isinstance(analyses["PAT-014"], TradeoffAnalysis)
        assert analyses["PAT-014"].pattern_id == "PAT-014"

    def test_analyze_multiple_estimates(self):
        """Should analyze tradeoffs for multiple estimates."""
        analyzer = TradeoffAnalyzer()

        estimate1 = CostEstimate(
            pattern_id="PAT-015",
            pattern_type="LOB_CLIFF",
            affected_objects=["TABLE_A.col1"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=60.0,
            implementation_cost=5000.0,
        )

        estimate2 = CostEstimate(
            pattern_id="PAT-016",
            pattern_type="EXPENSIVE_JOIN",
            affected_objects=["TABLE_B", "TABLE_C"],
            current_cost_per_day=200.0,
            optimized_cost_per_day=80.0,
            implementation_cost=8000.0,
        )

        workload = create_workload_features()

        analyses = analyzer.analyze([estimate1, estimate2], workload)

        assert len(analyses) == 2
        assert "PAT-015" in analyses
        assert "PAT-016" in analyses

    def test_detect_multiple_conflicts(self):
        """Should detect multiple conflicts in a set of estimates."""
        analyzer = TradeoffAnalyzer()

        # Conflict 1: CUSTOMERS table (document vs join)
        estimate1 = CostEstimate(
            pattern_id="PAT-017",
            pattern_type="DOCUMENT_CANDIDATE",
            affected_objects=["CUSTOMERS"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=60.0,
            implementation_cost=5000.0,
        )

        estimate2 = CostEstimate(
            pattern_id="PAT-018",
            pattern_type="EXPENSIVE_JOIN",
            affected_objects=["CUSTOMERS", "ORDERS"],
            current_cost_per_day=200.0,
            optimized_cost_per_day=80.0,
            implementation_cost=8000.0,
        )

        # Conflict 2: PRODUCTS table (LOB vs document)
        estimate3 = CostEstimate(
            pattern_id="PAT-019",
            pattern_type="LOB_CLIFF",
            affected_objects=["PRODUCTS.description"],
            current_cost_per_day=150.0,
            optimized_cost_per_day=50.0,
            implementation_cost=3000.0,
        )

        estimate4 = CostEstimate(
            pattern_id="PAT-020",
            pattern_type="DOCUMENT_CANDIDATE",
            affected_objects=["PRODUCTS"],
            current_cost_per_day=120.0,
            optimized_cost_per_day=70.0,
            implementation_cost=6000.0,
        )

        conflicts = analyzer.detect_conflicts(
            [estimate1, estimate2, estimate3, estimate4],
            {
                "CUSTOMERS": create_table_metadata("CUSTOMERS"),
                "PRODUCTS": create_table_metadata("PRODUCTS"),
            },
        )

        assert len(conflicts) == 2
        conflict_tables = {tuple(sorted(c.affected_objects)) for c in conflicts}
        assert ("CUSTOMERS",) in conflict_tables
        assert ("PRODUCTS",) in conflict_tables


class TestEdgeCases:
    """Test edge cases in tradeoff analysis."""

    def test_empty_estimates_list(self):
        """Should handle empty estimates list."""
        analyzer = TradeoffAnalyzer()

        workload = create_workload_features()
        analyses = analyzer.analyze([], workload)

        assert analyses == {}

    def test_empty_conflicts_list(self):
        """Should handle no conflicts gracefully."""
        analyzer = TradeoffAnalyzer()

        # Single estimate - no conflicts possible
        estimate = CostEstimate(
            pattern_id="PAT-021",
            pattern_type="LOB_CLIFF",
            affected_objects=["TABLE_A.col1"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=60.0,
            implementation_cost=5000.0,
        )

        conflicts = analyzer.detect_conflicts([estimate], {})

        assert conflicts == []

    def test_estimate_without_priority_score(self):
        """Should handle estimates without priority scores."""
        analyzer = TradeoffAnalyzer()

        # Estimates without priority_score set
        estimate1 = CostEstimate(
            pattern_id="PAT-022",
            pattern_type="LOB_CLIFF",
            affected_objects=["DATA.payload"],
            current_cost_per_day=100.0,
            optimized_cost_per_day=60.0,
            implementation_cost=5000.0,
        )

        estimate2 = CostEstimate(
            pattern_id="PAT-023",
            pattern_type="DOCUMENT_CANDIDATE",
            affected_objects=["DATA"],
            current_cost_per_day=80.0,
            optimized_cost_per_day=50.0,
            implementation_cost=4000.0,
        )

        conflicts = analyzer.detect_conflicts(
            [estimate1, estimate2],
            {"DATA": create_table_metadata("DATA")},
        )

        # Should still detect conflict and choose a resolution strategy
        assert len(conflicts) == 1
        assert conflicts[0].resolution_strategy in [
            "PRIORITIZE_A",
            "PRIORITIZE_B",
            "DUALITY_VIEW",
        ]
