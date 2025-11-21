"""End-to-end integration tests for complete recommendation pipeline.

This module tests the complete data flow from pattern detection through cost
analysis, tradeoff analysis, and recommendation generation with SQL.

Pipeline flow:
    Pattern Detection → Cost Calculation → Tradeoff Analysis →
    Recommendation Engine → SQL Generation
"""

from unittest.mock import MagicMock

import pytest

from src.recommendation.cost_calculator import CostCalculatorFactory
from src.recommendation.pattern_detector import LOBCliffDetector
from src.recommendation.recommendation_engine import RecommendationEngine
from src.recommendation.roi_calculator import ROICalculator
from src.recommendation.sql_generator import SQLGenerator
from src.recommendation.tradeoff_analyzer import TradeoffAnalyzer
from tests.integration.workloads import ALL_SCENARIOS, ALL_WORKLOADS, generate_workload


class TestCompletePipelineEndToEnd:
    """Test complete pipeline with real workload scenarios."""

    def test_lob_cliff_end_to_end_with_sql_generation(self):
        """Test complete flow from LOB detection to SQL generation.

        This test validates the entire pipeline:
        1. Pattern Detection (LOB Cliff)
        2. Cost Calculation
        3. ROI & Priority Scoring
        4. Tradeoff Analysis
        5. Recommendation Generation (with placeholder SQL)
        6. Recommendation Generation (with mocked LLM SQL)
        """
        # Step 1: Get scenario and generate workload
        schema_config = next(s for s in ALL_SCENARIOS if s.name == "product_catalog_lob_cliff")
        workload_config = next(w for w in ALL_WORKLOADS if w.name == "product_catalog_lob_cliff")
        workload = generate_workload(workload_config)

        # Step 2: Detect patterns
        detector = LOBCliffDetector()
        patterns = detector.detect(schema_config.tables, workload)

        assert len(patterns) >= 1, "Should detect at least one LOB cliff pattern"
        pattern = patterns[0]
        assert pattern.pattern_type == "LOB_CLIFF"

        # Step 3: Calculate costs
        table_metadata = {table.name: table for table in schema_config.tables}
        cost_estimates = CostCalculatorFactory.calculate_all([pattern], table_metadata, workload)

        assert len(cost_estimates) > 0, "Should calculate cost for pattern"
        cost_estimate = cost_estimates[0]

        assert cost_estimate is not None
        assert cost_estimate.current_cost_per_day > 0
        assert cost_estimate.annual_savings > 0

        # Calculate ROI and priority
        roi_calculator = ROICalculator()
        cost_estimate = roi_calculator.enrich_estimate(cost_estimate)

        assert cost_estimate.priority_tier in ["HIGH", "MEDIUM", "LOW"]
        assert cost_estimate.priority_score is not None

        # Step 4: Tradeoff analysis
        analyzer = TradeoffAnalyzer()
        tradeoff_analyses = analyzer.analyze([cost_estimate], workload)

        assert cost_estimate.pattern_id in tradeoff_analyses
        tradeoff = tradeoff_analyses[cost_estimate.pattern_id]

        assert tradeoff is not None
        assert tradeoff.recommendation in ["APPROVE", "REJECT", "CONDITIONAL"]

        # Skip if rejected
        if tradeoff.recommendation == "REJECT":
            pytest.skip("Pattern rejected by tradeoff analysis")

        # Step 5: Generate recommendation (without LLM first)
        engine = RecommendationEngine()
        recommendation = engine.generate_recommendation(
            pattern=pattern,
            cost_estimate=cost_estimate,
            tradeoff_analysis=tradeoff,
            conflicts=[],
            table=schema_config.tables[0],
            workload=workload,
        )

        assert recommendation is not None
        assert recommendation.recommendation_id.startswith("REC-")
        assert recommendation.pattern_id == pattern.pattern_id
        assert recommendation.type == "LOB_CLIFF"
        assert recommendation.priority in ["HIGH", "MEDIUM", "LOW"]
        assert len(recommendation.target_objects) > 0
        assert "Placeholder" in recommendation.implementation.sql
        assert recommendation.estimated_improvement_pct > 0
        assert recommendation.annual_savings > 0

        # Step 6: Generate recommendation with mocked LLM SQL generation
        mock_llm_client = MagicMock()
        mock_llm_response = """
IMPLEMENTATION SQL:
```sql
CREATE TABLE products_description (
    product_id NUMBER NOT NULL,
    description CLOB,
    CONSTRAINT fk_prod_desc FOREIGN KEY (product_id) REFERENCES products(product_id)
);

INSERT INTO products_description (product_id, description)
SELECT product_id, description FROM products;

ALTER TABLE products DROP COLUMN description;
```

ROLLBACK SQL:
```sql
ALTER TABLE products ADD (description CLOB);
UPDATE products p SET description = (SELECT description FROM products_description pd WHERE pd.product_id = p.product_id);
DROP TABLE products_description;
```

TESTING STEPS:
1. Create products_description table in test environment
2. Migrate 10% of data and run shadow testing
3. Monitor I/O metrics for LOB chaining reduction
4. Compare write amplification before/after
5. Full migration after 1 week validation

REASONING:
Splitting the CLOB column into a separate table eliminates LOB chaining on updates
to other product columns. This reduces write amplification from 5x to 1x for typical
product updates (price, inventory, etc.). The foreign key maintains referential
integrity, and the separate table is only accessed when description is needed.
"""
        mock_llm_client.send_message.return_value = {"text": mock_llm_response}

        sql_generator = SQLGenerator(llm_client=mock_llm_client)
        engine_with_llm = RecommendationEngine(sql_generator=sql_generator)

        recommendation_with_sql = engine_with_llm.generate_recommendation(
            pattern=pattern,
            cost_estimate=cost_estimate,
            tradeoff_analysis=tradeoff,
            conflicts=[],
            table=schema_config.tables[0],
            workload=workload,
        )

        assert recommendation_with_sql is not None
        assert "CREATE TABLE products_description" in recommendation_with_sql.implementation.sql
        assert (
            "DROP TABLE products_description"
            in recommendation_with_sql.implementation.rollback_plan
        )
        assert "shadow testing" in recommendation_with_sql.implementation.testing_approach.lower()
        assert "Placeholder" not in recommendation_with_sql.implementation.sql

        # Verify LLM was called
        mock_llm_client.send_message.assert_called_once()
        call_args = mock_llm_client.send_message.call_args
        assert "Oracle" in call_args[1]["message"]
        assert "CLOB" in call_args[1]["message"] or "LOB" in call_args[1]["message"]

    def test_empty_patterns_generates_no_recommendations(self):
        """Test that empty pattern list produces no recommendations."""
        patterns = []
        cost_estimates = {}
        tradeoff_analyses = {}
        conflicts = []

        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(
            patterns=patterns,
            cost_estimates=cost_estimates,
            tradeoff_analyses=tradeoff_analyses,
            conflicts=conflicts,
        )

        assert len(recommendations) == 0, "No patterns should produce no recommendations"
