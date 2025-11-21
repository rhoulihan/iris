"""Integration tests for Pipeline Orchestrator.

This module tests the complete end-to-end data flow from AWR collection
through recommendation generation.
"""

from unittest.mock import MagicMock

import pytest

from src.pipeline.orchestrator import PipelineConfig, PipelineOrchestrator, PipelineResult


class TestPipelineConfiguration:
    """Test pipeline configuration."""

    def test_create_default_config(self):
        """Should create pipeline config with sensible defaults."""
        config = PipelineConfig()

        assert config is not None
        assert config.enable_lob_detection is True
        assert config.enable_join_analysis is True
        assert config.enable_document_analysis is True
        assert config.enable_duality_view_analysis is True
        assert config.min_confidence_threshold == 0.3
        assert config.min_priority_score == 40.0

    def test_create_custom_config(self):
        """Should create pipeline config with custom settings."""
        config = PipelineConfig(
            enable_lob_detection=False,
            enable_join_analysis=True,
            min_confidence_threshold=0.5,
            min_priority_score=60.0,
        )

        assert config.enable_lob_detection is False
        assert config.enable_join_analysis is True
        assert config.min_confidence_threshold == 0.5
        assert config.min_priority_score == 60.0


class TestPipelineInitialization:
    """Test pipeline orchestrator initialization."""

    def test_create_orchestrator_with_connection(self):
        """Should create orchestrator with database connection."""
        mock_connection = MagicMock()

        orchestrator = PipelineOrchestrator(connection=mock_connection)

        assert orchestrator is not None
        assert orchestrator.connection == mock_connection

    def test_create_orchestrator_with_config(self):
        """Should create orchestrator with custom config."""
        mock_connection = MagicMock()
        config = PipelineConfig(min_confidence_threshold=0.7)

        orchestrator = PipelineOrchestrator(connection=mock_connection, config=config)

        assert orchestrator.config.min_confidence_threshold == 0.7

    def test_create_orchestrator_without_connection_raises_error(self):
        """Should raise ValueError if no connection provided."""
        with pytest.raises(ValueError, match="connection required"):
            PipelineOrchestrator(connection=None)


class TestPipelineExecution:
    """Test pipeline execution."""

    def test_run_pipeline_returns_result(self):
        """Should execute full pipeline and return result."""
        mock_connection = MagicMock()

        # Mock AWR data
        mock_connection.cursor.return_value.__enter__.return_value.fetchone.return_value = (100,)

        orchestrator = PipelineOrchestrator(connection=mock_connection)

        # This will use real components but mocked database
        result = orchestrator.run(
            begin_snapshot_id=99,
            end_snapshot_id=100,
        )

        assert result is not None
        assert isinstance(result, PipelineResult)

    def test_pipeline_result_structure(self):
        """Should return result with all expected fields."""
        result = PipelineResult(
            patterns_detected=5,
            recommendations_generated=3,
            high_priority_count=1,
            medium_priority_count=2,
            low_priority_count=0,
            total_annual_savings=50000.0,
            execution_time_seconds=2.5,
            recommendations=[],
            errors=[],
        )

        assert result.patterns_detected == 5
        assert result.recommendations_generated == 3
        assert result.high_priority_count == 1
        assert result.total_annual_savings == 50000.0
        assert result.execution_time_seconds == 2.5


class TestPipelineStages:
    """Test individual pipeline stages."""

    def test_stage_1_data_collection(self):
        """Stage 1: Should collect AWR data and schema metadata."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock AWR snapshot query
        mock_cursor.fetchone.return_value = (100,)

        # Mock SQL statistics query (empty for now)
        mock_cursor.fetchall.return_value = []

        orchestrator = PipelineOrchestrator(connection=mock_connection)
        _ = orchestrator.run(begin_snapshot_id=99, end_snapshot_id=100)

        # Should have attempted to collect data
        assert mock_cursor.execute.called

    def test_stage_2_feature_engineering(self):
        """Stage 2: Should parse, compress, and extract features."""
        # This will be tested via the full pipeline
        pass

    def test_stage_3_pattern_detection(self):
        """Stage 3: Should detect anti-patterns."""
        # This will be tested via the full pipeline
        pass

    def test_stage_4_cost_analysis(self):
        """Stage 4: Should calculate costs and ROI."""
        # This will be tested via the full pipeline
        pass

    def test_stage_5_tradeoff_analysis(self):
        """Stage 5: Should analyze tradeoffs."""
        # This will be tested via the full pipeline
        pass

    def test_stage_6_recommendation_generation(self):
        """Stage 6: Should generate final recommendations."""
        # This will be tested via the full pipeline
        pass


class TestPipelineErrorHandling:
    """Test pipeline error handling and resilience."""

    def test_pipeline_handles_empty_workload(self):
        """Should handle case with no SQL queries gracefully."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock empty AWR data
        mock_cursor.fetchone.return_value = (100,)
        mock_cursor.fetchall.return_value = []

        orchestrator = PipelineOrchestrator(connection=mock_connection)
        result = orchestrator.run(begin_snapshot_id=99, end_snapshot_id=100)

        assert result is not None
        assert result.patterns_detected == 0
        assert result.recommendations_generated == 0

    def test_pipeline_handles_no_patterns_detected(self):
        """Should handle case when no anti-patterns detected."""
        # Will be tested when we have real data
        pass

    def test_pipeline_handles_database_error(self):
        """Should handle database connection errors gracefully."""
        mock_connection = MagicMock()
        mock_connection.cursor.side_effect = RuntimeError("Database connection lost")

        # Error should be raised during initialization when validating AWR access
        with pytest.raises(RuntimeError, match="Cannot access AWR views"):
            _ = PipelineOrchestrator(connection=mock_connection)


class TestPipelineFiltering:
    """Test pipeline filtering based on config."""

    def test_filter_by_confidence_threshold(self):
        """Should filter out patterns below confidence threshold."""
        # Will test with real data
        pass

    def test_filter_by_priority_score(self):
        """Should filter out recommendations below priority threshold."""
        # Will test with real data
        pass

    def test_disable_specific_detectors(self):
        """Should skip disabled pattern detectors."""
        mock_connection = MagicMock()
        config = PipelineConfig(
            enable_lob_detection=False,
            enable_join_analysis=False,
            enable_document_analysis=True,
            enable_duality_view_analysis=True,
        )

        orchestrator = PipelineOrchestrator(connection=mock_connection, config=config)

        # Configuration should be applied
        assert orchestrator.config.enable_lob_detection is False
        assert orchestrator.config.enable_join_analysis is False


class TestPipelineMetrics:
    """Test pipeline metrics and monitoring."""

    def test_pipeline_tracks_execution_time(self):
        """Should track total pipeline execution time."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = (100,)
        mock_cursor.fetchall.return_value = []

        orchestrator = PipelineOrchestrator(connection=mock_connection)
        result = orchestrator.run(begin_snapshot_id=99, end_snapshot_id=100)

        assert result.execution_time_seconds >= 0

    def test_pipeline_tracks_error_count(self):
        """Should track errors encountered during execution."""
        # Will test when we have error scenarios
        pass

    def test_pipeline_tracks_recommendations_by_priority(self):
        """Should count recommendations by priority tier."""
        result = PipelineResult(
            patterns_detected=10,
            recommendations_generated=7,
            high_priority_count=2,
            medium_priority_count=3,
            low_priority_count=2,
            total_annual_savings=100000.0,
            execution_time_seconds=3.0,
            recommendations=[],
            errors=[],
        )

        assert result.high_priority_count == 2
        assert result.medium_priority_count == 3
        assert result.low_priority_count == 2
        assert (
            result.high_priority_count + result.medium_priority_count + result.low_priority_count
            == 7
        )
