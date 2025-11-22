"""End-to-end integration tests for pattern detection pipeline.

This module tests the complete data flow from schema/workload through
pattern detection with realistic synthetic scenarios.
"""

import pytest

from src.recommendation.models import SchemaMetadata
from src.recommendation.pattern_detector import (
    DocumentRelationalClassifier,
    DualityViewOpportunityFinder,
    JoinDimensionAnalyzer,
    LOBCliffDetector,
)
from tests.integration.workloads import ALL_SCENARIOS, ALL_WORKLOADS, generate_workload


class TestEndToEndPatternDetection:
    """End-to-end integration tests for pattern detection."""

    # ========================================================================
    # Scenario 1.1: E-Commerce with Expensive Joins
    # ========================================================================

    def test_ecommerce_expensive_joins_detected(self):
        """Test that expensive joins in e-commerce workload are correctly detected."""
        # Get schema and workload
        schema_config = next(s for s in ALL_SCENARIOS if s.name == "ecommerce_expensive_joins")
        workload_config = next(w for w in ALL_WORKLOADS if w.name == "ecommerce_expensive_joins")

        # Generate workload
        workload = generate_workload(workload_config)

        # Create schema metadata
        schema = SchemaMetadata(tables={table.name: table for table in schema_config.tables})

        # Run Join Dimension Analyzer
        analyzer = JoinDimensionAnalyzer(
            min_join_frequency_percentage=10.0,  # 80% join frequency will exceed this
            max_columns_fetched=5,  # 2 columns fetched is within limit
            max_dimension_rows=1000000,  # 50K customers is within limit
        )

        patterns = analyzer.analyze(workload, schema)

        # Assertions
        assert len(patterns) == 1, "Should detect one expensive join pattern"
        pattern = patterns[0]
        assert pattern.pattern_type == "EXPENSIVE_JOIN"
        assert "ORDERS" in pattern.affected_objects
        assert "CUSTOMERS" in pattern.affected_objects
        assert pattern.severity in ["HIGH", "MEDIUM"]
        assert pattern.confidence >= 0.7  # High join frequency = high confidence
        assert pattern.metrics["join_frequency_percentage"] >= 75.0
        assert len(pattern.metrics["columns_accessed"]) == 2
        assert "CUSTOMER_NAME" in pattern.metrics["columns_accessed"]
        assert "CUSTOMER_TIER" in pattern.metrics["columns_accessed"]
        assert "denormalizing" in pattern.recommendation_hint.lower()

    # ========================================================================
    # Scenario 1.2: Document Storage Anti-Pattern
    # ========================================================================

    def test_user_profiles_document_candidate_detected(self):
        """Test that document storage opportunity is detected for user profiles."""
        schema_config = next(
            s for s in ALL_SCENARIOS if s.name == "user_profiles_document_candidate"
        )
        workload_config = next(
            w for w in ALL_WORKLOADS if w.name == "user_profiles_document_candidate"
        )

        workload = generate_workload(workload_config)
        schema = SchemaMetadata(tables={table.name: table for table in schema_config.tables})

        # Run Document/Relational Classifier
        classifier = DocumentRelationalClassifier(strong_signal_threshold=0.3)

        patterns = classifier.classify(schema_config.tables, workload, schema)

        # Assertions
        assert len(patterns) == 1, "Should detect one document candidate"
        pattern = patterns[0]
        assert pattern.pattern_type == "DOCUMENT_CANDIDATE"
        assert "USER_PROFILES" in pattern.affected_objects
        assert pattern.metrics["select_all_percentage"] >= 85.0  # 90% SELECT *
        assert pattern.metrics["document_score"] > pattern.metrics["relational_score"]
        assert (
            "JSON collection" in pattern.recommendation_hint
            or "document storage" in pattern.recommendation_hint.lower()
        )

    # ========================================================================
    # Scenario 1.3: LOB Cliff Anti-Pattern
    # ========================================================================

    def test_audit_logs_lob_cliff_detected(self):
        """Test that LOB cliff is detected in audit logs with selective updates."""
        schema_config = next(s for s in ALL_SCENARIOS if s.name == "audit_logs_lob_cliff")
        workload_config = next(w for w in ALL_WORKLOADS if w.name == "audit_logs_lob_cliff")

        workload = generate_workload(workload_config)

        # Run LOB Cliff Detector
        detector = LOBCliffDetector(
            large_doc_threshold_bytes=4096,
            high_update_frequency_threshold=100,
            small_update_selectivity_threshold=0.1,
        )

        patterns = detector.detect(schema_config.tables, workload)

        # Assertions
        assert len(patterns) > 0, "Should detect LOB cliff pattern"
        # Find the PAYLOAD column pattern
        payload_pattern = next((p for p in patterns if "PAYLOAD" in p.affected_objects[0]), None)
        assert payload_pattern is not None, "Should detect LOB cliff on PAYLOAD column"
        assert payload_pattern.pattern_type == "LOB_CLIFF"
        assert payload_pattern.metrics["avg_document_size_kb"] > 4.0  # 8KB > 4KB threshold
        assert payload_pattern.metrics["updates_per_day"] >= 100  # High update frequency
        assert payload_pattern.metrics["storage_type"] == "out_of_line"
        assert payload_pattern.metrics["format"] == "TEXT"  # CLOB = TEXT format

    # ========================================================================
    # Scenario 1.4: Duality View Opportunity
    # ========================================================================

    def test_product_catalog_duality_view_detected(self):
        """Test that duality view opportunity is detected for product catalog."""
        schema_config = next(s for s in ALL_SCENARIOS if s.name == "product_catalog_duality")
        workload_config = next(w for w in ALL_WORKLOADS if w.name == "product_catalog_duality")

        workload = generate_workload(workload_config)

        # Run Duality View Finder
        finder = DualityViewOpportunityFinder(
            min_oltp_percentage=10.0,
            min_analytics_percentage=10.0,
        )

        patterns = finder.find_opportunities(schema_config.tables, workload)

        # Assertions
        assert len(patterns) == 1, "Should detect one duality view opportunity"
        pattern = patterns[0]
        assert pattern.pattern_type == "DUALITY_VIEW_OPPORTUNITY"
        assert "CATALOG.PRODUCTS" in pattern.affected_objects
        # 40% OLTP (20% INSERT + 15% UPDATE + 5% simple SELECT)
        assert pattern.metrics["oltp_percentage"] >= 35.0
        # 35% Analytics (25% + 10% aggregates)
        assert pattern.metrics["analytics_percentage"] >= 30.0
        assert pattern.severity in ["HIGH", "MEDIUM"]
        assert "Duality View" in pattern.recommendation_hint

    # ========================================================================
    # Scenario 3.1: LOB Cliff FALSE POSITIVE - Cached Read-Heavy
    # ========================================================================

    def test_document_repo_no_lob_cliff_low_updates(self):
        """Test that LOB cliff is NOT detected when update frequency is low."""
        schema_config = next(s for s in ALL_SCENARIOS if s.name == "document_repo_cached_reads")
        workload_config = next(w for w in ALL_WORKLOADS if w.name == "document_repo_cached_reads")

        workload = generate_workload(workload_config)

        # Run LOB Cliff Detector
        detector = LOBCliffDetector(
            large_doc_threshold_bytes=4096,
            high_update_frequency_threshold=100,  # 10/day is below this
            small_update_selectivity_threshold=0.1,
        )

        # This workload has 10 updates total representing a full day (24 hours)
        # Pass snapshot_duration_hours=24.0 so scaling gives: (10/24)*24 = 10/day
        patterns = detector.detect(schema_config.tables, workload, snapshot_duration_hours=24.0)

        # Assertions: Should NOT detect LOB cliff due to low update frequency
        assert len(patterns) == 0, (
            f"Should NOT detect LOB cliff with only 10 updates/day. "
            f"Found {len(patterns)} patterns: {[p.pattern_type for p in patterns]}"
        )

    # ========================================================================
    # Scenario 3.2: Join Denormalization FALSE POSITIVE - Volatile Dimension
    # ========================================================================

    def test_orders_volatile_products_no_denormalization(self):
        """Test that denormalization is NOT recommended when dimension updates frequently."""
        schema_config = next(s for s in ALL_SCENARIOS if s.name == "orders_volatile_products")
        workload_config = next(w for w in ALL_WORKLOADS if w.name == "orders_volatile_products")

        workload = generate_workload(workload_config)
        schema = SchemaMetadata(tables={table.name: table for table in schema_config.tables})

        # Run Join Dimension Analyzer
        analyzer = JoinDimensionAnalyzer(
            min_join_frequency_percentage=10.0,
            max_columns_fetched=5,
            max_dimension_rows=1000000,
            max_dimension_update_rate=100,  # Products update 500/day = 5x this threshold
        )

        patterns = analyzer.analyze(workload, schema)

        # Assertions: Should NOT recommend denormalization
        # Net benefit should be negative due to high update propagation cost
        assert len(patterns) == 0, (
            f"Should NOT recommend denormalization when dimension updates frequently. "
            f"Found {len(patterns)} patterns"
        )

    # ========================================================================
    # Scenario 3.3: Document Storage FALSE POSITIVE - Mixed Access
    # ========================================================================

    def test_event_logs_neutral_no_recommendation(self):
        """Test that no recommendation is made for mixed access patterns."""
        schema_config = next(s for s in ALL_SCENARIOS if s.name == "event_logs_mixed_access")
        workload_config = next(w for w in ALL_WORKLOADS if w.name == "event_logs_mixed_access")

        workload = generate_workload(workload_config)
        schema = SchemaMetadata(tables={table.name: table for table in schema_config.tables})

        # Run Document/Relational Classifier
        classifier = DocumentRelationalClassifier(strong_signal_threshold=0.3)

        patterns = classifier.classify(schema_config.tables, workload, schema)

        # Assertions: Should be neutral (no clear winner)
        # Net score should be close to 0, below 0.3 threshold
        assert len(patterns) == 0, (
            f"Should NOT recommend storage change for mixed access patterns. "
            f"Found {len(patterns)} patterns"
        )

    # ========================================================================
    # Scenario 3.4: Duality View FALSE POSITIVE - Low Volume
    # ========================================================================

    def test_admin_config_low_volume_duality_view(self):
        """Test duality view detection on low volume table (edge case)."""
        schema_config = next(s for s in ALL_SCENARIOS if s.name == "admin_config_low_volume")
        workload_config = next(w for w in ALL_WORKLOADS if w.name == "admin_config_low_volume")

        workload = generate_workload(workload_config)

        # Run Duality View Finder
        finder = DualityViewOpportunityFinder(
            min_oltp_percentage=10.0,
            min_analytics_percentage=10.0,
        )

        patterns = finder.find_opportunities(schema_config.tables, workload)

        # Assertions: Will detect but should be LOW severity
        # This tests the current behavior - could add volume threshold in future
        if len(patterns) > 0:
            pattern = patterns[0]
            assert pattern.pattern_type == "DUALITY_VIEW_OPPORTUNITY"
            # With only 50 total queries, severity should be LOW or MEDIUM at most
            assert pattern.severity in [
                "LOW",
                "MEDIUM",
            ], f"Low volume table should have LOW/MEDIUM severity, got {pattern.severity}"
            # Duality score should be relatively low
            assert (
                pattern.metrics["duality_score"] < 0.3
            ), "Duality score should be < 0.3 for balanced low-volume table"

    # ========================================================================
    # Scenario 3.5: Selective LOB Update with High Selectivity (Clear POSITIVE)
    # ========================================================================

    def test_product_catalog_lob_cliff_high_severity(self):
        """Test that LOB cliff with all risk factors is detected with HIGH severity."""
        schema_config = next(s for s in ALL_SCENARIOS if s.name == "product_catalog_lob_cliff")
        workload_config = next(w for w in ALL_WORKLOADS if w.name == "product_catalog_lob_cliff")

        workload = generate_workload(workload_config)

        # Run LOB Cliff Detector
        detector = LOBCliffDetector(
            large_doc_threshold_bytes=4096,
            high_update_frequency_threshold=100,
            small_update_selectivity_threshold=0.1,
        )

        # Use 24-hour snapshot for full confidence (no snapshot penalty)
        patterns = detector.detect(schema_config.tables, workload, snapshot_duration_hours=24.0)

        # Assertions
        assert len(patterns) > 0, "Should detect LOB cliff pattern"
        # Find IMAGE_METADATA pattern
        image_pattern = next(
            (p for p in patterns if "IMAGE_METADATA" in p.affected_objects[0]), None
        )
        assert image_pattern is not None, "Should detect LOB cliff on IMAGE_METADATA column"
        assert image_pattern.pattern_type == "LOB_CLIFF"
        assert (
            image_pattern.severity == "HIGH"
        ), f"Should be HIGH severity, got {image_pattern.severity}"
        # Risk score should be >= 0.8 for HIGH severity
        assert (
            image_pattern.confidence >= 0.8
        ), f"Risk score should be >= 0.8, got {image_pattern.confidence}"
        assert image_pattern.metrics["avg_document_size_kb"] > 10.0  # 12KB > 4KB threshold
        assert image_pattern.metrics["updates_per_day"] >= 150  # ~200/day

    # ========================================================================
    # Scenario 3.6: Join with Many Columns
    # ========================================================================

    def test_orders_preferences_too_many_columns_no_recommendation(self):
        """Test that join is NOT recommended for denormalization when too many columns."""
        schema_config = next(s for s in ALL_SCENARIOS if s.name == "orders_customer_preferences")
        workload_config = next(w for w in ALL_WORKLOADS if w.name == "orders_customer_preferences")

        workload = generate_workload(workload_config)
        schema = SchemaMetadata(tables={table.name: table for table in schema_config.tables})

        # Run Join Dimension Analyzer
        analyzer = JoinDimensionAnalyzer(
            min_join_frequency_percentage=10.0,
            max_columns_fetched=5,  # 15 columns exceeds this
            max_dimension_rows=1000000,
        )

        patterns = analyzer.analyze(workload, schema)

        # Assertions: Should NOT recommend due to too many columns
        assert len(patterns) == 0, (
            f"Should NOT recommend denormalization when fetching {5}+ columns. "
            f"Found {len(patterns)} patterns"
        )


# ============================================================================
# Summary Test: Pattern Detection Accuracy
# ============================================================================


class TestPatternDetectionAccuracy:
    """Validate pattern detection accuracy across all scenarios."""

    def test_all_clear_positive_cases(self):
        """Test that all clear positive cases are correctly detected."""
        clear_positive_scenarios = [
            ("ecommerce_expensive_joins", "EXPENSIVE_JOIN"),
            ("user_profiles_document_candidate", "DOCUMENT_CANDIDATE"),
            ("audit_logs_lob_cliff", "LOB_CLIFF"),
            ("product_catalog_duality", "DUALITY_VIEW_OPPORTUNITY"),
            ("product_catalog_lob_cliff", "LOB_CLIFF"),  # Scenario 3.5
        ]

        results = []
        for scenario_name, expected_pattern_type in clear_positive_scenarios:
            schema_config = next(s for s in ALL_SCENARIOS if s.name == scenario_name)
            workload_config = next(w for w in ALL_WORKLOADS if w.name == scenario_name)
            workload = generate_workload(workload_config)
            schema = SchemaMetadata(tables={table.name: table for table in schema_config.tables})

            # Run appropriate detector based on expected pattern
            patterns = []
            if expected_pattern_type == "EXPENSIVE_JOIN":
                analyzer = JoinDimensionAnalyzer()
                patterns = analyzer.analyze(workload, schema)
            elif expected_pattern_type == "DOCUMENT_CANDIDATE":
                classifier = DocumentRelationalClassifier()
                patterns = classifier.classify(schema_config.tables, workload, schema)
            elif expected_pattern_type == "LOB_CLIFF":
                detector = LOBCliffDetector()
                patterns = detector.detect(schema_config.tables, workload)
            elif expected_pattern_type == "DUALITY_VIEW_OPPORTUNITY":
                finder = DualityViewOpportunityFinder()
                patterns = finder.find_opportunities(schema_config.tables, workload)

            detected = any(p.pattern_type == expected_pattern_type for p in patterns)
            results.append((scenario_name, expected_pattern_type, detected))

        # Report results
        failed = [r for r in results if not r[2]]
        if failed:
            failure_msg = "\n".join([f"  - {r[0]}: Expected {r[1]}, not detected" for r in failed])
            pytest.fail(f"Failed to detect patterns in clear positive cases:\n{failure_msg}")

    def test_all_clear_negative_cases(self):
        """Test that false positives are avoided in edge cases."""
        clear_negative_scenarios = [
            ("document_repo_cached_reads", "LOB_CLIFF"),  # Low update frequency
            ("orders_volatile_products", "EXPENSIVE_JOIN"),  # High update propagation cost
            ("event_logs_mixed_access", "DOCUMENT_CANDIDATE"),  # Neutral/mixed access
            ("orders_customer_preferences", "EXPENSIVE_JOIN"),  # Too many columns
        ]

        results = []
        for scenario_name, pattern_type_to_avoid in clear_negative_scenarios:
            schema_config = next(s for s in ALL_SCENARIOS if s.name == scenario_name)
            workload_config = next(w for w in ALL_WORKLOADS if w.name == scenario_name)
            workload = generate_workload(workload_config)
            schema = SchemaMetadata(tables={table.name: table for table in schema_config.tables})

            # Run appropriate detector
            patterns = []
            if pattern_type_to_avoid == "LOB_CLIFF":
                detector = LOBCliffDetector()
                # Pass snapshot_duration_hours=24.0 to indicate this is a full-day snapshot
                patterns = detector.detect(
                    schema_config.tables, workload, snapshot_duration_hours=24.0
                )
            elif pattern_type_to_avoid == "EXPENSIVE_JOIN":
                analyzer = JoinDimensionAnalyzer()
                patterns = analyzer.analyze(workload, schema)
            elif pattern_type_to_avoid == "DOCUMENT_CANDIDATE":
                classifier = DocumentRelationalClassifier()
                patterns = classifier.classify(schema_config.tables, workload, schema)

            # Should NOT detect the pattern
            incorrectly_detected = any(p.pattern_type == pattern_type_to_avoid for p in patterns)
            results.append((scenario_name, pattern_type_to_avoid, not incorrectly_detected))

        # Report results
        failed = [r for r in results if not r[2]]
        if failed:
            failure_msg = "\n".join([f"  - {r[0]}: Incorrectly detected {r[1]}" for r in failed])
            pytest.fail(f"False positives detected:\n{failure_msg}")
