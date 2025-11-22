"""Tests for IRIS REST API."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.pipeline.orchestrator import PipelineResult
from src.services.analysis_service import AnalysisSession


@pytest.fixture
def mock_analysis_session() -> AnalysisSession:
    """Provide mock analysis session."""
    result = PipelineResult(
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
    session = AnalysisSession(
        analysis_id="ANALYSIS-2025-11-21-001", status="completed", result=result
    )
    return session


@pytest.fixture
def client() -> TestClient:
    """Provide test client for API."""
    from src.api.app import app

    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    """Health endpoint should return status."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_analyze_endpoint(client: TestClient, mock_analysis_session: AnalysisSession) -> None:
    """Analyze endpoint should run analysis and return session."""
    with patch("src.api.app.AnalysisService") as MockService:
        mock_service = Mock()
        mock_service.run_analysis.return_value = mock_analysis_session
        MockService.return_value = mock_service

        response = client.post(
            "/api/v1/analyze",
            json={
                "database": {
                    "host": "localhost",
                    "port": 1521,
                    "service": "FREEPDB1",
                    "username": "testuser",
                    "password": "testpass",
                }
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == "ANALYSIS-2025-11-21-001"
        assert data["status"] == "completed"


def test_get_session_endpoint(client: TestClient, mock_analysis_session: AnalysisSession) -> None:
    """Get session endpoint should return session details."""
    from src.api.app import _services

    with patch("src.api.app.AnalysisService") as MockService:
        mock_service = Mock()
        mock_service.get_session.return_value = mock_analysis_session
        MockService.return_value = mock_service

        # Add service to global dict
        _services["ANALYSIS-2025-11-21-001"] = mock_service

        response = client.get("/api/v1/sessions/ANALYSIS-2025-11-21-001")

        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == "ANALYSIS-2025-11-21-001"

        # Clean up
        _services.clear()


def test_list_sessions_endpoint(client: TestClient, mock_analysis_session: AnalysisSession) -> None:
    """List sessions endpoint should return all sessions."""
    from src.api.app import _services

    with patch("src.api.app.AnalysisService") as MockService:
        mock_service = Mock()
        mock_service.list_sessions.return_value = [mock_analysis_session]
        MockService.return_value = mock_service

        # Add service to global dict
        _services["ANALYSIS-2025-11-21-001"] = mock_service

        response = client.get("/api/v1/sessions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["analysis_id"] == "ANALYSIS-2025-11-21-001"

        # Clean up
        _services.clear()


def test_get_recommendations_endpoint(
    client: TestClient, mock_analysis_session: AnalysisSession
) -> None:
    """Get recommendations endpoint should return recommendations."""
    from src.api.app import _services

    with patch("src.api.app.AnalysisService") as MockService:
        mock_service = Mock()
        mock_service.get_recommendations.return_value = []
        MockService.return_value = mock_service

        # Add service to global dict
        _services["ANALYSIS-2025-11-21-001"] = mock_service

        response = client.get("/api/v1/recommendations/ANALYSIS-2025-11-21-001")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Clean up
        _services.clear()


def test_get_recommendation_endpoint(
    client: TestClient, mock_analysis_session: AnalysisSession
) -> None:
    """Get specific recommendation endpoint should return recommendation details."""
    from src.recommendation.recommendation_engine import (
        Implementation,
        Rationale,
        SchemaRecommendation,
    )

    recommendation = SchemaRecommendation(
        recommendation_id="REC-001",
        pattern_id="PAT-001",
        type="LOB_CLIFF",
        priority="HIGH",
        target_objects=["PRODUCT_REVIEWS"],
        description="Convert LOB columns to JSON",
        rationale=Rationale(
            pattern_detected="LOB cliff pattern",
            current_cost="High I/O cost",
            expected_benefit="65% improvement",
        ),
        implementation=Implementation(
            sql="CREATE TABLE...",
            rollback_plan="DROP TABLE...",
            testing_approach="Shadow mode",
        ),
        estimated_improvement_pct=65.0,
        estimated_cost=1000.0,
        annual_savings=25000.0,
        roi_percentage=2400.0,
    )

    from src.api.app import _services

    with patch("src.api.app.AnalysisService") as MockService:
        mock_service = Mock()
        mock_service.get_recommendation.return_value = recommendation
        MockService.return_value = mock_service

        # Add service to global dict
        _services["ANALYSIS-2025-11-21-001"] = mock_service

        response = client.get("/api/v1/recommendations/ANALYSIS-2025-11-21-001/REC-001")

        assert response.status_code == 200
        data = response.json()
        assert data["recommendation_id"] == "REC-001"
        assert data["type"] == "LOB_CLIFF"

        # Clean up
        _services.clear()


def test_analyze_endpoint_invalid_input(client: TestClient) -> None:
    """Analyze endpoint should validate input."""
    response = client.post("/api/v1/analyze", json={})

    assert response.status_code == 422  # Validation error
