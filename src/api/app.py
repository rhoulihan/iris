"""IRIS REST API application."""

import logging
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.cli.config import DatabaseConfig
from src.pipeline.orchestrator import PipelineConfig
from src.services.analysis_service import AnalysisNotFoundError, AnalysisService, AnalysisSession

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IRIS API",
    description="Intelligent Recommendation and Inference System for Oracle Database",
    version="1.0.0",
)

# Global service instance (simplified for API usage)
_services: Dict[str, AnalysisService] = {}


# Request/Response Models
class DatabaseConfigModel(BaseModel):
    """Database configuration model."""

    host: str = Field(..., description="Database host")
    port: int = Field(1521, description="Database port")
    service: str = Field(..., description="Oracle service name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")


class AnalyzeRequest(BaseModel):
    """Request model for analyze endpoint."""

    database: DatabaseConfigModel
    min_confidence: Optional[float] = Field(0.6, description="Minimum confidence threshold")


class AnalysisSessionResponse(BaseModel):
    """Response model for analysis session."""

    analysis_id: str
    created_at: str
    status: str
    patterns_detected: Optional[int] = None
    recommendations_generated: Optional[int] = None
    high_priority_count: Optional[int] = None
    medium_priority_count: Optional[int] = None
    low_priority_count: Optional[int] = None
    total_annual_savings: Optional[float] = None
    execution_time_seconds: Optional[float] = None
    error: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Response model for recommendation."""

    recommendation_id: str
    type: str
    priority: str
    description: str
    target_objects: List[str]
    estimated_improvement_pct: float
    annual_savings: float
    roi_percentage: float


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "iris-api"}


@app.post("/api/v1/analyze", response_model=AnalysisSessionResponse)
def analyze(request: AnalyzeRequest) -> AnalysisSessionResponse:
    """Run analysis on Oracle database.

    Args:
        request: Analysis request with database configuration

    Returns:
        Analysis session with results

    Raises:
        HTTPException: If analysis fails
    """
    try:
        # Create database config
        db_config = DatabaseConfig(
            host=request.database.host,
            port=request.database.port,
            service=request.database.service,
            username=request.database.username,
            password=request.database.password,
        )

        # Create pipeline config
        pipeline_config = PipelineConfig(
            min_confidence_threshold=request.min_confidence or 0.6,
        )

        # Create service and run analysis
        service = AnalysisService(db_config, pipeline_config)
        session = service.run_analysis()

        # Store service for later use
        _services[session.analysis_id] = service

        # Convert to response model
        return _session_to_response(session)

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sessions/{analysis_id}", response_model=AnalysisSessionResponse)
def get_session(analysis_id: str) -> AnalysisSessionResponse:
    """Get analysis session by ID.

    Args:
        analysis_id: Analysis session identifier

    Returns:
        Analysis session details

    Raises:
        HTTPException: If session not found
    """
    try:
        service = _services.get(analysis_id)
        if not service:
            raise HTTPException(status_code=404, detail=f"Session not found: {analysis_id}")

        session = service.get_session(analysis_id)
        return _session_to_response(session)

    except AnalysisNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sessions", response_model=List[AnalysisSessionResponse])
def list_sessions() -> List[AnalysisSessionResponse]:
    """List all analysis sessions.

    Returns:
        List of analysis sessions
    """
    try:
        sessions = []
        for service in _services.values():
            sessions.extend(service.list_sessions())

        return [_session_to_response(s) for s in sessions]

    except Exception as e:
        logger.error(f"Failed to list sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/recommendations/{analysis_id}", response_model=List[RecommendationResponse])
def get_recommendations(
    analysis_id: str,
    priority: Optional[str] = None,
    pattern_type: Optional[str] = None,
) -> List[RecommendationResponse]:
    """Get recommendations for analysis session.

    Args:
        analysis_id: Analysis session identifier
        priority: Filter by priority (HIGH, MEDIUM, LOW)
        pattern_type: Filter by pattern type

    Returns:
        List of recommendations

    Raises:
        HTTPException: If session not found
    """
    try:
        service = _services.get(analysis_id)
        if not service:
            raise HTTPException(status_code=404, detail=f"Session not found: {analysis_id}")

        recs = service.get_recommendations(
            analysis_id, priority=priority, pattern_type=pattern_type
        )

        return [_recommendation_to_response(r) for r in recs]

    except AnalysisNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/v1/recommendations/{analysis_id}/{recommendation_id}",
    response_model=RecommendationResponse,
)
def get_recommendation(analysis_id: str, recommendation_id: str) -> RecommendationResponse:
    """Get specific recommendation.

    Args:
        analysis_id: Analysis session identifier
        recommendation_id: Recommendation identifier

    Returns:
        Recommendation details

    Raises:
        HTTPException: If session or recommendation not found
    """
    try:
        service = _services.get(analysis_id)
        if not service:
            raise HTTPException(status_code=404, detail=f"Session not found: {analysis_id}")

        rec = service.get_recommendation(analysis_id, recommendation_id)
        return _recommendation_to_response(rec)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AnalysisNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get recommendation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
def _session_to_response(session: AnalysisSession) -> AnalysisSessionResponse:
    """Convert AnalysisSession to response model."""
    response = AnalysisSessionResponse(
        analysis_id=session.analysis_id,
        created_at=session.created_at.isoformat(),
        status=session.status,
        error=session.error,
    )

    if session.result:
        response.patterns_detected = session.result.patterns_detected
        response.recommendations_generated = session.result.recommendations_generated
        response.high_priority_count = session.result.high_priority_count
        response.medium_priority_count = session.result.medium_priority_count
        response.low_priority_count = session.result.low_priority_count
        response.total_annual_savings = session.result.total_annual_savings
        response.execution_time_seconds = session.result.execution_time_seconds

    return response


def _recommendation_to_response(rec) -> RecommendationResponse:
    """Convert SchemaRecommendation to response model."""
    return RecommendationResponse(
        recommendation_id=rec.recommendation_id,
        type=rec.type,
        priority=rec.priority,
        description=rec.description,
        target_objects=rec.target_objects,
        estimated_improvement_pct=rec.estimated_improvement_pct,
        annual_savings=rec.annual_savings,
        roi_percentage=rec.roi_percentage,
    )
