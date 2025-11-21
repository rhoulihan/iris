"""Pipeline orchestrator for end-to-end recommendation generation.

This module coordinates the complete workflow from AWR data collection through
pattern detection, cost analysis, tradeoff evaluation, and recommendation generation.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, List, Optional

from src.data.awr_collector import AWRCollector
from src.data.feature_engineer import FeatureEngineer
from src.data.query_parser import QueryParser
from src.data.schema_collector import SchemaCollector
from src.data.workload_compressor import WorkloadCompressor
from src.pipeline.converters import dict_to_query_pattern, dict_to_table_metadata
from src.recommendation.cost_calculator import CostCalculatorFactory
from src.recommendation.models import QueryPattern, SchemaMetadata, TableMetadata, WorkloadFeatures
from src.recommendation.pattern_detector import (
    DocumentRelationalClassifier,
    DualityViewOpportunityFinder,
    JoinDimensionAnalyzer,
    LOBCliffDetector,
)
from src.recommendation.recommendation_engine import RecommendationEngine, SchemaRecommendation
from src.recommendation.roi_calculator import ROICalculator
from src.recommendation.tradeoff_analyzer import TradeoffAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution.

    Attributes:
        enable_lob_detection: Enable LOB cliff pattern detection
        enable_join_analysis: Enable join dimension analysis
        enable_document_analysis: Enable document vs relational classification
        enable_duality_view_analysis: Enable duality view opportunity detection
        min_confidence_threshold: Minimum confidence for pattern detection (0.0-1.0)
        min_priority_score: Minimum priority score for recommendations (0-100)
        compress_workload: Enable workload compression (ISUM algorithm)
        max_queries_to_analyze: Maximum queries to analyze (for performance)
    """

    enable_lob_detection: bool = True
    enable_join_analysis: bool = True
    enable_document_analysis: bool = True
    enable_duality_view_analysis: bool = True
    min_confidence_threshold: float = 0.3
    min_priority_score: float = 40.0
    compress_workload: bool = True
    max_queries_to_analyze: int = 10000


@dataclass
class PipelineResult:
    """Result of pipeline execution.

    Attributes:
        patterns_detected: Total number of patterns detected
        recommendations_generated: Total number of recommendations generated
        high_priority_count: Number of HIGH priority recommendations
        medium_priority_count: Number of MEDIUM priority recommendations
        low_priority_count: Number of LOW priority recommendations
        total_annual_savings: Total estimated annual savings across all recommendations
        execution_time_seconds: Total pipeline execution time
        recommendations: List of generated recommendations
        errors: List of errors encountered during execution
    """

    patterns_detected: int
    recommendations_generated: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    total_annual_savings: float
    execution_time_seconds: float
    recommendations: List[SchemaRecommendation] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class PipelineOrchestrator:
    """Orchestrates end-to-end recommendation pipeline.

    This class coordinates all pipeline stages from data collection through
    recommendation generation. It handles:
    - AWR data collection
    - SQL parsing and workload compression
    - Feature engineering
    - Schema metadata collection
    - Pattern detection (LOB, Join, Document, Duality View)
    - Cost/benefit analysis
    - Tradeoff evaluation
    - Recommendation generation

    Example:
        >>> import oracledb
        >>> conn = oracledb.connect(user="iris_user", password="pwd", dsn="localhost/FREEPDB1")
        >>> orchestrator = PipelineOrchestrator(connection=conn)
        >>> result = orchestrator.run(begin_snapshot_id=100, end_snapshot_id=101)
        >>> print(f"Generated {result.recommendations_generated} recommendations")
        >>> print(f"Estimated annual savings: ${result.total_annual_savings:,.2f}")
    """

    def __init__(
        self,
        connection: Any,
        config: Optional[PipelineConfig] = None,
    ):
        """Initialize pipeline orchestrator.

        Args:
            connection: Oracle database connection
            config: Pipeline configuration (defaults to PipelineConfig())

        Raises:
            ValueError: If connection is None
        """
        if connection is None:
            raise ValueError("Database connection required")

        self.connection = connection
        self.config = config or PipelineConfig()

        # Initialize components
        self._awr_collector = AWRCollector(connection)
        self._query_parser = QueryParser()
        self._workload_compressor = WorkloadCompressor()
        self._feature_engineer = FeatureEngineer()
        self._schema_collector = SchemaCollector(connection)
        self._roi_calculator = ROICalculator()
        self._tradeoff_analyzer = TradeoffAnalyzer()
        self._recommendation_engine = RecommendationEngine()

        logger.info("Pipeline orchestrator initialized")

    def run(
        self,
        begin_snapshot_id: int,
        end_snapshot_id: int,
        schemas: Optional[List[str]] = None,
    ) -> PipelineResult:
        """Execute complete recommendation pipeline.

        Args:
            begin_snapshot_id: AWR snapshot ID to start analysis
            end_snapshot_id: AWR snapshot ID to end analysis
            schemas: List of database schemas to analyze (default: all accessible schemas)

        Returns:
            PipelineResult with recommendations and execution metrics

        Raises:
            RuntimeError: If pipeline execution fails
        """
        start_time = time.time()
        errors: List[str] = []

        try:
            logger.info(f"Starting pipeline for snapshots {begin_snapshot_id}-{end_snapshot_id}")

            # Stage 1: Data Collection
            logger.info("Stage 1: Collecting AWR data and schema metadata")
            workload, tables = self._collect_data(begin_snapshot_id, end_snapshot_id, schemas)

            if not workload or not workload.queries:
                logger.warning("No workload data collected - returning empty result")
                return PipelineResult(
                    patterns_detected=0,
                    recommendations_generated=0,
                    high_priority_count=0,
                    medium_priority_count=0,
                    low_priority_count=0,
                    total_annual_savings=0.0,
                    execution_time_seconds=time.time() - start_time,
                    recommendations=[],
                    errors=["No workload data available"],
                )

            # Stage 2: Feature Engineering
            logger.info("Stage 2: Feature engineering")
            workload = self._engineer_features(workload)

            # Stage 3: Pattern Detection
            logger.info("Stage 3: Pattern detection")
            patterns = self._detect_patterns(tables, workload)

            if not patterns:
                logger.info("No patterns detected - returning empty result")
                return PipelineResult(
                    patterns_detected=0,
                    recommendations_generated=0,
                    high_priority_count=0,
                    medium_priority_count=0,
                    low_priority_count=0,
                    total_annual_savings=0.0,
                    execution_time_seconds=time.time() - start_time,
                    recommendations=[],
                    errors=[],
                )

            # Stage 4: Cost/Benefit Analysis
            logger.info("Stage 4: Cost/benefit analysis")
            table_metadata = {table.name: table for table in tables}
            cost_estimates = self._calculate_costs(patterns, table_metadata, workload)

            # Stage 5: Tradeoff Analysis
            logger.info("Stage 5: Tradeoff analysis")
            tradeoff_analyses = self._analyze_tradeoffs(cost_estimates, workload)

            # Stage 6: Recommendation Generation
            logger.info("Stage 6: Recommendation generation")
            recommendations = self._generate_recommendations(
                patterns, cost_estimates, tradeoff_analyses, table_metadata, workload
            )

            # Filter recommendations
            recommendations = self._filter_recommendations(recommendations)

            # Calculate metrics
            execution_time = time.time() - start_time
            result = self._build_result(recommendations, len(patterns), execution_time, errors)

            logger.info(
                f"Pipeline complete: {result.recommendations_generated} recommendations, "
                f"${result.total_annual_savings:,.2f} annual savings, "
                f"{execution_time:.2f}s"
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            raise

    def _collect_data(
        self,
        begin_snapshot_id: int,
        end_snapshot_id: int,
        schemas: Optional[List[str]],
    ) -> tuple[Optional[WorkloadFeatures], List[TableMetadata]]:
        """Stage 1: Collect AWR data and schema metadata.

        Args:
            begin_snapshot_id: Begin AWR snapshot ID
            end_snapshot_id: End AWR snapshot ID
            schemas: List of schemas to analyze

        Returns:
            Tuple of (workload_features, table_metadata)
        """
        try:
            # Collect SQL statistics from AWR
            sql_stats = self._awr_collector.get_sql_statistics(
                begin_snap=begin_snapshot_id,
                end_snap=end_snapshot_id,
            )

            if not sql_stats:
                logger.warning("No SQL statistics found in AWR snapshots")
                return None, []

            # Limit queries to analyze
            sql_stats_to_process = sql_stats[: self.config.max_queries_to_analyze]

            # Compress workload if enabled (before parsing)
            if self.config.compress_workload and sql_stats_to_process:
                compressed_result = self._workload_compressor.compress(sql_stats_to_process)
                sql_stats_to_process = compressed_result.get(
                    "compressed_queries", sql_stats_to_process
                )
                logger.info(
                    f"Compressed workload: {len(sql_stats)} → {len(sql_stats_to_process)} queries"
                )

            # Parse queries and build workload using converters
            queries: List[QueryPattern] = []
            for stat in sql_stats_to_process:
                try:
                    # Parse SQL to get query features
                    parsed_dict = self._query_parser.parse(stat.get("sql_text", ""))

                    # Convert to QueryPattern using converter
                    query_pattern = dict_to_query_pattern(
                        parsed_dict,
                        sql_id=stat.get("sql_id", f"query_{len(queries)}"),
                    )

                    # Enrich with AWR statistics
                    query_pattern.executions = int(stat.get("executions", 1))
                    query_pattern.avg_elapsed_time_ms = float(
                        stat.get("elapsed_time_total", 0)
                    ) / max(query_pattern.executions, 1)

                    queries.append(query_pattern)
                except Exception as e:
                    logger.debug(f"Failed to parse/convert query: {e}")
                    continue

            # Build workload features
            workload = WorkloadFeatures(
                queries=queries,
                total_executions=sum(q.executions for q in queries),
                unique_patterns=len(queries),
            )

            # Collect schema metadata using converters
            tables: List[TableMetadata] = []
            if schemas:
                for schema in schemas:
                    try:
                        # Get tables as dicts from schema_collector
                        table_dicts = self._schema_collector.get_tables(schema)

                        # Convert each dict to TableMetadata
                        for table_dict in table_dicts:
                            try:
                                table_metadata = dict_to_table_metadata(table_dict)
                                tables.append(table_metadata)
                            except Exception as e:
                                logger.debug(f"Failed to convert table metadata: {e}")
                                continue
                    except Exception as e:
                        logger.warning(f"Failed to collect schema {schema}: {e}")
                        continue

            logger.info(f"Collected {len(queries)} queries and {len(tables)} tables")

            return workload, tables

        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            raise

    def _engineer_features(self, workload: WorkloadFeatures) -> WorkloadFeatures:
        """Stage 2: Engineer features from workload.

        Args:
            workload: Raw workload features

        Returns:
            Enhanced workload features
        """
        # Feature engineering is already done during parsing
        # This stage is a placeholder for future enhancements
        return workload

    def _detect_patterns(self, tables: List[TableMetadata], workload: WorkloadFeatures) -> List:
        """Stage 3: Detect anti-patterns.

        Args:
            tables: Table metadata
            workload: Workload features

        Returns:
            List of detected patterns
        """
        all_patterns: List = []

        # Create SchemaMetadata for detectors that need it
        schema = SchemaMetadata(tables={table.name: table for table in tables})

        # LOB Cliff Detection
        if self.config.enable_lob_detection and tables:
            try:
                detector = LOBCliffDetector()
                patterns = detector.detect(tables, workload)
                all_patterns.extend(patterns)
                logger.info(f"Detected {len(patterns)} LOB cliff patterns")
            except Exception as e:
                logger.warning(f"LOB cliff detection failed: {e}")

        # Join Dimension Analysis - uses analyze(workload, schema)
        if self.config.enable_join_analysis:
            try:
                analyzer = JoinDimensionAnalyzer()
                patterns = analyzer.analyze(workload, schema)
                all_patterns.extend(patterns)
                logger.info(f"Detected {len(patterns)} expensive join patterns")
            except Exception as e:
                logger.warning(f"Join analysis failed: {e}")

        # Document vs Relational Classification - uses classify(tables, workload, schema)
        if self.config.enable_document_analysis and tables:
            try:
                classifier = DocumentRelationalClassifier()
                patterns = classifier.classify(tables, workload, schema)
                all_patterns.extend(patterns)
                logger.info(f"Detected {len(patterns)} document/relational patterns")
            except Exception as e:
                logger.warning(f"Document classification failed: {e}")

        # Duality View Opportunity Detection - uses find_opportunities(tables, workload)
        if self.config.enable_duality_view_analysis and tables:
            try:
                finder = DualityViewOpportunityFinder()
                patterns = finder.find_opportunities(tables, workload)
                all_patterns.extend(patterns)
                logger.info(f"Detected {len(patterns)} duality view opportunities")
            except Exception as e:
                logger.warning(f"Duality view detection failed: {e}")

        # Filter by confidence
        all_patterns = [
            p for p in all_patterns if p.confidence >= self.config.min_confidence_threshold
        ]

        logger.info(f"Total patterns detected: {len(all_patterns)}")

        return all_patterns

    def _calculate_costs(self, patterns: List, table_metadata: dict, workload: WorkloadFeatures):
        """Stage 4: Calculate costs and ROI.

        Args:
            patterns: Detected patterns
            table_metadata: Table metadata dictionary
            workload: Workload features

        Returns:
            List of cost estimates with ROI
        """
        cost_estimates = CostCalculatorFactory.calculate_all(patterns, table_metadata, workload)

        # Enrich with ROI and priority
        enriched_estimates = []
        for estimate in cost_estimates:
            enriched = self._roi_calculator.enrich_estimate(estimate)
            enriched_estimates.append(enriched)

        return enriched_estimates

    def _analyze_tradeoffs(self, cost_estimates: List, workload: WorkloadFeatures):
        """Stage 5: Analyze tradeoffs.

        Args:
            cost_estimates: Cost estimates with ROI
            workload: Workload features

        Returns:
            Dictionary of tradeoff analyses by pattern ID
        """
        return self._tradeoff_analyzer.analyze(cost_estimates, workload)

    def _generate_recommendations(
        self,
        patterns: List,
        cost_estimates: List,
        tradeoff_analyses: dict,
        table_metadata: dict,
        workload: WorkloadFeatures,
    ) -> List[SchemaRecommendation]:
        """Stage 6: Generate recommendations.

        Args:
            patterns: Detected patterns
            cost_estimates: Cost estimates with ROI
            tradeoff_analyses: Tradeoff analyses
            table_metadata: Table metadata
            workload: Workload features

        Returns:
            List of schema recommendations
        """
        # Build cost estimate lookup
        cost_lookup = {est.pattern_id: est for est in cost_estimates}

        recommendations = []
        for pattern in patterns:
            cost_estimate = cost_lookup.get(pattern.pattern_id)
            if not cost_estimate:
                continue

            tradeoff = tradeoff_analyses.get(pattern.pattern_id)
            if not tradeoff:
                continue

            # Get table for this pattern
            table_name = (
                pattern.affected_objects[0].split(".")[0] if pattern.affected_objects else None
            )
            table = table_metadata.get(table_name) if table_name else None

            if not table:
                logger.warning(f"No table metadata for pattern {pattern.pattern_id}")
                continue

            # Generate recommendation
            recommendation = self._recommendation_engine.generate_recommendation(
                pattern=pattern,
                cost_estimate=cost_estimate,
                tradeoff_analysis=tradeoff,
                conflicts=[],
                table=table,
                workload=workload,
            )

            if recommendation:
                recommendations.append(recommendation)

        return recommendations

    def _filter_recommendations(
        self, recommendations: List[SchemaRecommendation]
    ) -> List[SchemaRecommendation]:
        """Filter recommendations based on config thresholds.

        Args:
            recommendations: List of recommendations

        Returns:
            Filtered list of recommendations
        """
        filtered = [
            rec
            for rec in recommendations
            if rec.priority in ["HIGH", "MEDIUM", "LOW"]
            # Add more filters based on config if needed
        ]

        # Sort by priority
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        filtered.sort(key=lambda r: priority_order.get(r.priority, 3))

        return filtered

    def _build_result(
        self,
        recommendations: List[SchemaRecommendation],
        patterns_detected: int,
        execution_time: float,
        errors: List[str],
    ) -> PipelineResult:
        """Build pipeline result from recommendations.

        Args:
            recommendations: Generated recommendations
            patterns_detected: Total patterns detected
            execution_time: Pipeline execution time
            errors: List of errors

        Returns:
            PipelineResult
        """
        high_count = sum(1 for r in recommendations if r.priority == "HIGH")
        medium_count = sum(1 for r in recommendations if r.priority == "MEDIUM")
        low_count = sum(1 for r in recommendations if r.priority == "LOW")

        total_savings = sum(r.annual_savings for r in recommendations)

        return PipelineResult(
            patterns_detected=patterns_detected,
            recommendations_generated=len(recommendations),
            high_priority_count=high_count,
            medium_priority_count=medium_count,
            low_priority_count=low_count,
            total_annual_savings=total_savings,
            execution_time_seconds=execution_time,
            recommendations=recommendations,
            errors=errors,
        )
