"""IRIS AnalysisService - Application layer for pipeline orchestration.

This module provides the high-level service interface for running analyses,
managing sessions, and retrieving recommendations.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import oracledb

from src.cli.config import DatabaseConfig
from src.pipeline.orchestrator import PipelineConfig, PipelineOrchestrator, PipelineResult
from src.recommendation.recommendation_engine import SchemaRecommendation

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""

    pass


class AnalysisNotFoundError(Exception):
    """Raised when analysis session is not found."""

    pass


@dataclass
class AnalysisSession:
    """Represents an analysis session.

    Attributes:
        analysis_id: Unique identifier for the analysis
        created_at: Timestamp when analysis was created
        status: Status of the analysis (pending, running, completed, failed)
        result: Pipeline execution result (None if not completed)
        error: Error message if analysis failed
    """

    analysis_id: str
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    result: Optional[PipelineResult] = None
    error: Optional[str] = None


class AnalysisService:
    """High-level service for running database analyses.

    This service orchestrates the complete IRIS pipeline:
    - Database connection management
    - Pipeline execution
    - Session tracking
    - Recommendation retrieval

    Example:
        >>> from src.cli.config import DatabaseConfig
        >>> from src.pipeline.orchestrator import PipelineConfig
        >>>
        >>> db_config = DatabaseConfig(
        ...     host="localhost",
        ...     port=1521,
        ...     service="FREEPDB1",
        ...     username="iris_user",
        ...     password="password"
        ... )
        >>> pipeline_config = PipelineConfig(min_confidence_threshold=0.6)
        >>>
        >>> service = AnalysisService(db_config, pipeline_config)
        >>> session = service.run_analysis()
        >>> recommendations = service.get_recommendations(session.analysis_id)
    """

    def __init__(
        self,
        db_config: DatabaseConfig,
        pipeline_config: PipelineConfig,
    ) -> None:
        """Initialize AnalysisService.

        Args:
            db_config: Database connection configuration
            pipeline_config: Pipeline execution configuration
        """
        self.db_config = db_config
        self.pipeline_config = pipeline_config
        self._sessions: Dict[str, AnalysisSession] = {}
        self._session_counter = 0

    def run_analysis(
        self,
        begin_snapshot_id: Optional[int] = None,
        end_snapshot_id: Optional[int] = None,
        schemas: Optional[List[str]] = None,
    ) -> AnalysisSession:
        """Run full analysis pipeline.

        Args:
            begin_snapshot_id: AWR snapshot ID to start analysis (optional)
            end_snapshot_id: AWR snapshot ID to end analysis (optional)
            schemas: List of schemas to analyze (optional, defaults to all)

        Returns:
            AnalysisSession with results

        Raises:
            DatabaseConnectionError: If database connection fails
        """
        # Create session
        self._session_counter += 1
        analysis_id = self._generate_analysis_id()
        session = AnalysisSession(analysis_id=analysis_id, status="running")
        self._sessions[analysis_id] = session

        try:
            # Connect to database
            connection = self._connect_to_database()

            try:
                # Run pipeline
                orchestrator = PipelineOrchestrator(connection, self.pipeline_config)

                # Determine snapshot IDs if not provided
                if begin_snapshot_id is None or end_snapshot_id is None:
                    # For now, use mock values - in real implementation,
                    # we would query AWR to get latest snapshots
                    begin_snapshot_id = begin_snapshot_id or 1
                    end_snapshot_id = end_snapshot_id or 2

                result = orchestrator.run(begin_snapshot_id, end_snapshot_id, schemas)

                # Update session
                session.status = "completed"
                session.result = result

            finally:
                connection.close()

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            session.status = "failed"
            session.error = str(e)

            # Re-raise connection errors
            if "connect" in str(e).lower() or "connection" in str(e).lower():
                raise DatabaseConnectionError(str(e)) from e

            raise

        return session

    def get_session(self, analysis_id: str) -> AnalysisSession:
        """Get analysis session by ID.

        Args:
            analysis_id: Unique analysis identifier

        Returns:
            AnalysisSession for the given ID

        Raises:
            AnalysisNotFoundError: If session not found
        """
        if analysis_id not in self._sessions:
            raise AnalysisNotFoundError(f"Analysis session not found: {analysis_id}")

        return self._sessions[analysis_id]

    def list_sessions(self) -> List[AnalysisSession]:
        """List all analysis sessions.

        Returns:
            List of all analysis sessions
        """
        return list(self._sessions.values())

    def get_recommendations(
        self,
        analysis_id: str,
        priority: Optional[str] = None,
        pattern_type: Optional[str] = None,
    ) -> List[SchemaRecommendation]:
        """Get recommendations from analysis session.

        Args:
            analysis_id: Analysis session identifier
            priority: Filter by priority (HIGH, MEDIUM, LOW)
            pattern_type: Filter by pattern type

        Returns:
            List of recommendations matching filters

        Raises:
            AnalysisNotFoundError: If session not found
        """
        session = self.get_session(analysis_id)

        if session.result is None:
            return []

        recommendations = session.result.recommendations

        # Apply filters
        if priority:
            recommendations = [r for r in recommendations if r.priority == priority]

        if pattern_type:
            recommendations = [r for r in recommendations if r.type == pattern_type]

        return recommendations

    def get_recommendation(self, analysis_id: str, recommendation_id: str) -> SchemaRecommendation:
        """Get specific recommendation by ID.

        Args:
            analysis_id: Analysis session identifier
            recommendation_id: Recommendation identifier

        Returns:
            SchemaRecommendation matching the ID

        Raises:
            AnalysisNotFoundError: If session not found
            ValueError: If recommendation not found
        """
        session = self.get_session(analysis_id)

        if session.result is None:
            raise ValueError(
                f"Recommendation not found: {recommendation_id} (analysis not completed)"
            )

        for recommendation in session.result.recommendations:
            if recommendation.recommendation_id == recommendation_id:
                return recommendation

        raise ValueError(f"Recommendation not found: {recommendation_id}")

    def _connect_to_database(self) -> oracledb.Connection:
        """Connect to Oracle database.

        Returns:
            Database connection

        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            connection_params = {
                "user": self.db_config.username,
                "password": self.db_config.password,
                "host": self.db_config.host,
                "port": self.db_config.port,
                "service_name": self.db_config.service,
            }

            connection = oracledb.connect(**connection_params)
            return connection

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e

    def _generate_analysis_id(self) -> str:
        """Generate unique analysis ID.

        Returns:
            Unique analysis identifier in format ANALYSIS-YYYY-MM-DD-NNN
        """
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        return f"ANALYSIS-{date_str}-{self._session_counter:03d}"
