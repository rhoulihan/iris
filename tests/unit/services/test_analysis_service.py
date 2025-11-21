"""Tests for IRIS AnalysisService (application layer)."""

from unittest.mock import Mock, patch

import pytest

from src.cli.config import DatabaseConfig
from src.pipeline.orchestrator import PipelineConfig, PipelineResult
from src.recommendation.recommendation_engine import Implementation, Rationale, SchemaRecommendation
from src.services.analysis_service import (
    AnalysisNotFoundError,
    AnalysisService,
    AnalysisSession,
    DatabaseConnectionError,
)


@pytest.fixture
def db_config() -> DatabaseConfig:
    """Provide test database configuration."""
    return DatabaseConfig(
        host="localhost",
        port=1521,
        service="FREEPDB1",
        username="testuser",
        password="testpass",
    )


@pytest.fixture
def pipeline_config() -> PipelineConfig:
    """Provide test pipeline configuration."""
    return PipelineConfig(
        min_confidence_threshold=0.6,
        min_priority_score=50.0,
    )


@pytest.fixture
def mock_pipeline_result() -> PipelineResult:
    """Provide mock pipeline result."""
    return PipelineResult(
        patterns_detected=5,
        recommendations_generated=3,
        high_priority_count=1,
        medium_priority_count=1,
        low_priority_count=1,
        total_annual_savings=50000.0,
        execution_time_seconds=12.5,
        recommendations=[],
        errors=[],
    )


def test_analysis_service_creation_with_config(
    db_config: DatabaseConfig, pipeline_config: PipelineConfig
) -> None:
    """Create AnalysisService with database and pipeline config."""
    service = AnalysisService(db_config, pipeline_config)

    assert service is not None
    assert service.db_config == db_config
    assert service.pipeline_config == pipeline_config


@patch("src.services.analysis_service.oracledb.connect")
def test_run_analysis_creates_session_and_returns_result(
    mock_connect: Mock,
    db_config: DatabaseConfig,
    pipeline_config: PipelineConfig,
    mock_pipeline_result: PipelineResult,
) -> None:
    """run_analysis should execute pipeline and return session with results."""
    # Mock database connection
    mock_connection = Mock()
    mock_connect.return_value = mock_connection

    # Mock orchestrator
    with patch("src.services.analysis_service.PipelineOrchestrator") as MockOrch:
        mock_orchestrator = Mock()
        mock_orchestrator.run.return_value = mock_pipeline_result
        MockOrch.return_value = mock_orchestrator

        service = AnalysisService(db_config, pipeline_config)
        session = service.run_analysis()

        # Verify session was created
        assert isinstance(session, AnalysisSession)
        assert session.analysis_id.startswith("ANALYSIS-")
        assert session.result == mock_pipeline_result
        assert session.status == "completed"


@patch("src.services.analysis_service.oracledb.connect")
def test_run_analysis_handles_connection_failure(
    mock_connect: Mock,
    db_config: DatabaseConfig,
    pipeline_config: PipelineConfig,
) -> None:
    """run_analysis should raise DatabaseConnectionError on connection failure."""
    mock_connect.side_effect = Exception("Connection refused")

    service = AnalysisService(db_config, pipeline_config)

    with pytest.raises(DatabaseConnectionError, match="Connection refused"):
        service.run_analysis()


def test_get_session_returns_existing_session(
    db_config: DatabaseConfig, pipeline_config: PipelineConfig
) -> None:
    """get_session should return previously created session."""
    with patch("src.services.analysis_service.oracledb.connect"):
        with patch("src.services.analysis_service.PipelineOrchestrator"):
            service = AnalysisService(db_config, pipeline_config)
            session = service.run_analysis()

            retrieved_session = service.get_session(session.analysis_id)
            assert retrieved_session == session


def test_get_session_raises_error_for_nonexistent_session(
    db_config: DatabaseConfig, pipeline_config: PipelineConfig
) -> None:
    """get_session should raise AnalysisNotFoundError for invalid ID."""
    service = AnalysisService(db_config, pipeline_config)

    with pytest.raises(AnalysisNotFoundError, match="ANALYSIS-INVALID"):
        service.get_session("ANALYSIS-INVALID")


def test_list_sessions_returns_all_sessions(
    db_config: DatabaseConfig, pipeline_config: PipelineConfig
) -> None:
    """list_sessions should return all analysis sessions."""
    with patch("src.services.analysis_service.oracledb.connect"):
        with patch("src.services.analysis_service.PipelineOrchestrator"):
            service = AnalysisService(db_config, pipeline_config)
            session1 = service.run_analysis()
            session2 = service.run_analysis()

            sessions = service.list_sessions()
            assert len(sessions) == 2
            assert session1 in sessions
            assert session2 in sessions


def test_get_recommendations_from_session(
    db_config: DatabaseConfig,
    pipeline_config: PipelineConfig,
    mock_pipeline_result: PipelineResult,
) -> None:
    """get_recommendations should return recommendations from session."""
    recommendation = SchemaRecommendation(
        recommendation_id="REC-001",
        pattern_id="PAT-001",
        type="LOB_CLIFF",
        priority="HIGH",
        target_objects=["PRODUCT_REVIEWS"],
        description="Convert LOB columns to JSON for better performance",
        rationale=Rationale(
            pattern_detected="LOB cliff pattern",
            current_cost="High I/O cost on LOB updates",
            expected_benefit="65% reduction in write latency",
        ),
        implementation=Implementation(
            sql="CREATE TABLE...",
            rollback_plan="DROP TABLE...",
            testing_approach="Shadow mode testing",
        ),
        estimated_improvement_pct=65.0,
        estimated_cost=1000.0,
        annual_savings=25000.0,
        roi_percentage=2400.0,
    )
    mock_pipeline_result.recommendations = [recommendation]

    with patch("src.services.analysis_service.oracledb.connect"):
        with patch("src.services.analysis_service.PipelineOrchestrator") as MockOrch:
            mock_orchestrator = Mock()
            mock_orchestrator.run.return_value = mock_pipeline_result
            MockOrch.return_value = mock_orchestrator

            service = AnalysisService(db_config, pipeline_config)
            session = service.run_analysis()

            recommendations = service.get_recommendations(session.analysis_id)
            assert len(recommendations) == 1
            assert recommendations[0] == recommendation


def test_get_recommendation_by_id(
    db_config: DatabaseConfig,
    pipeline_config: PipelineConfig,
    mock_pipeline_result: PipelineResult,
) -> None:
    """get_recommendation should return specific recommendation by ID."""
    recommendation = SchemaRecommendation(
        recommendation_id="REC-001",
        pattern_id="PAT-001",
        type="LOB_CLIFF",
        priority="HIGH",
        target_objects=["PRODUCT_REVIEWS"],
        description="Convert LOB columns to JSON for better performance",
        rationale=Rationale(
            pattern_detected="LOB cliff pattern",
            current_cost="High I/O cost on LOB updates",
            expected_benefit="65% reduction in write latency",
        ),
        implementation=Implementation(
            sql="CREATE TABLE...",
            rollback_plan="DROP TABLE...",
            testing_approach="Shadow mode testing",
        ),
        estimated_improvement_pct=65.0,
        estimated_cost=1000.0,
        annual_savings=25000.0,
        roi_percentage=2400.0,
    )
    mock_pipeline_result.recommendations = [recommendation]

    with patch("src.services.analysis_service.oracledb.connect"):
        with patch("src.services.analysis_service.PipelineOrchestrator") as MockOrch:
            mock_orchestrator = Mock()
            mock_orchestrator.run.return_value = mock_pipeline_result
            MockOrch.return_value = mock_orchestrator

            service = AnalysisService(db_config, pipeline_config)
            session = service.run_analysis()

            rec = service.get_recommendation(session.analysis_id, "REC-001")
            assert rec == recommendation


def test_get_recommendation_raises_error_for_nonexistent_id(
    db_config: DatabaseConfig,
    pipeline_config: PipelineConfig,
) -> None:
    """get_recommendation should raise error for invalid recommendation ID."""
    with patch("src.services.analysis_service.oracledb.connect"):
        with patch("src.services.analysis_service.PipelineOrchestrator"):
            service = AnalysisService(db_config, pipeline_config)
            session = service.run_analysis()

            with pytest.raises(ValueError, match="REC-INVALID"):
                service.get_recommendation(session.analysis_id, "REC-INVALID")


def test_filter_recommendations_by_priority(
    db_config: DatabaseConfig,
    pipeline_config: PipelineConfig,
    mock_pipeline_result: PipelineResult,
) -> None:
    """get_recommendations should filter by priority."""
    high_rec = SchemaRecommendation(
        recommendation_id="REC-001",
        pattern_id="PAT-001",
        type="LOB_CLIFF",
        priority="HIGH",
        target_objects=[],
        description="",
        rationale=Rationale(pattern_detected="", current_cost="", expected_benefit=""),
        implementation=Implementation(sql="", rollback_plan="", testing_approach=""),
        estimated_improvement_pct=0.0,
        estimated_cost=0.0,
        annual_savings=25000.0,
        roi_percentage=0.0,
    )
    low_rec = SchemaRecommendation(
        recommendation_id="REC-002",
        pattern_id="PAT-002",
        type="JOIN_DIMENSION",
        priority="LOW",
        target_objects=[],
        description="",
        rationale=Rationale(pattern_detected="", current_cost="", expected_benefit=""),
        implementation=Implementation(sql="", rollback_plan="", testing_approach=""),
        estimated_improvement_pct=0.0,
        estimated_cost=0.0,
        annual_savings=5000.0,
        roi_percentage=0.0,
    )
    mock_pipeline_result.recommendations = [high_rec, low_rec]

    with patch("src.services.analysis_service.oracledb.connect"):
        with patch("src.services.analysis_service.PipelineOrchestrator") as MockOrch:
            mock_orchestrator = Mock()
            mock_orchestrator.run.return_value = mock_pipeline_result
            MockOrch.return_value = mock_orchestrator

            service = AnalysisService(db_config, pipeline_config)
            session = service.run_analysis()

            high_recs = service.get_recommendations(session.analysis_id, priority="HIGH")
            assert len(high_recs) == 1
            assert high_recs[0].recommendation_id == "REC-001"
