"""Feature Engineer for IRIS project.

This module provides the FeatureEngineer class for extracting features from
compressed workload data to prepare for LLM analysis.
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Extracts features from compressed workload data for LLM analysis.

    This class takes compressed workload data (output from WorkloadCompressor)
    and extracts aggregate features, statistics, and insights suitable for
    consumption by the LLM-based index recommendation system.

    Example:
        >>> engineer = FeatureEngineer()
        >>> compressed_data = {
        ...     "groups": [...],
        ...     "total_queries": 100,
        ...     "total_executions": 5000,
        ...     "unique_patterns": 10,
        ...     "compression_ratio": 10.0
        ... }
        >>> features = engineer.extract_features(compressed_data)
        >>> print(features["performance_metrics"]["avg_elapsed_time_ms"])
        25.5
    """

    def __init__(self):
        """Initialize FeatureEngineer."""
        logger.debug("FeatureEngineer initialized")

    def extract_features(
        self, workload_data: Optional[Dict[str, Any]], top_n: int = 10
    ) -> Dict[str, Any]:
        """Extract features from compressed workload data.

        Args:
            workload_data: Compressed workload data from WorkloadCompressor containing:
                - groups: List of query groups with aggregated statistics
                - total_queries: Total number of queries before compression
                - total_executions: Total executions across all queries
                - unique_patterns: Number of unique query patterns
                - compression_ratio: Ratio of queries to patterns
            top_n: Number of top queries to include in results (default: 10)

        Returns:
            Dictionary containing extracted features:
                - total_patterns: Number of unique query patterns
                - total_executions: Total query executions
                - compression_ratio: Compression ratio achieved
                - query_type_distribution: Distribution of query types by pattern count
                - query_type_by_executions: Distribution of query types by execution count
                - performance_metrics: Aggregate performance metrics
                - complexity_metrics: Average query complexity metrics
                - top_queries_by_executions: Top N queries by execution count
                - top_queries_by_elapsed_time: Top N queries by elapsed time
                - io_metrics: I/O related metrics
                - summary: Human-readable summary for LLM

        Raises:
            ValueError: If workload_data is None
        """
        if workload_data is None:
            raise ValueError("Workload data cannot be None")

        groups = workload_data.get("groups", [])
        total_executions = workload_data.get("total_executions", 0)

        if not groups:
            return self._empty_result()

        # Extract various feature categories
        query_type_dist = self._extract_query_type_distribution(groups)
        query_type_exec = self._extract_query_type_by_executions(groups)
        performance = self._extract_performance_metrics(groups, total_executions)
        complexity = self._extract_complexity_metrics(groups)
        io_metrics = self._extract_io_metrics(groups, total_executions)
        top_by_exec = self._extract_top_queries(groups, "total_executions", top_n)
        top_by_time = self._extract_top_queries(groups, "total_elapsed_time_ms", top_n)
        summary = self._generate_summary(workload_data, query_type_dist, performance)

        return {
            "total_patterns": workload_data.get("unique_patterns", 0),
            "total_executions": total_executions,
            "compression_ratio": workload_data.get("compression_ratio", 0.0),
            "query_type_distribution": query_type_dist,
            "query_type_by_executions": query_type_exec,
            "performance_metrics": performance,
            "complexity_metrics": complexity,
            "top_queries_by_executions": top_by_exec,
            "top_queries_by_elapsed_time": top_by_time,
            "io_metrics": io_metrics,
            "summary": summary,
        }

    def _extract_query_type_distribution(self, groups: List[Dict[str, Any]]) -> Dict[str, int]:
        """Extract query type distribution by pattern count.

        Args:
            groups: List of query groups

        Returns:
            Dictionary mapping query type to pattern count
        """
        distribution: Dict[str, int] = defaultdict(int)
        for group in groups:
            query_type = group.get("query_type", "UNKNOWN")
            distribution[query_type] += 1
        return dict(distribution)

    def _extract_query_type_by_executions(self, groups: List[Dict[str, Any]]) -> Dict[str, int]:
        """Extract query type distribution by execution count.

        Args:
            groups: List of query groups

        Returns:
            Dictionary mapping query type to total execution count
        """
        distribution: Dict[str, int] = defaultdict(int)
        for group in groups:
            query_type = group.get("query_type", "UNKNOWN")
            executions = group.get("total_executions", 0)
            distribution[query_type] += executions
        return dict(distribution)

    def _extract_performance_metrics(
        self, groups: List[Dict[str, Any]], total_executions: int
    ) -> Dict[str, float]:
        """Extract aggregate performance metrics.

        Args:
            groups: List of query groups
            total_executions: Total execution count

        Returns:
            Dictionary containing performance metrics
        """
        total_elapsed = sum(g.get("total_elapsed_time_ms", 0.0) for g in groups)
        total_cpu = sum(g.get("total_cpu_time_ms", 0.0) for g in groups)
        total_disk_reads = sum(g.get("total_disk_reads", 0) for g in groups)
        total_buffer_gets = sum(g.get("total_buffer_gets", 0) for g in groups)

        avg_elapsed = total_elapsed / total_executions if total_executions > 0 else 0.0
        avg_cpu = total_cpu / total_executions if total_executions > 0 else 0.0

        return {
            "avg_elapsed_time_ms": avg_elapsed,
            "avg_cpu_time_ms": avg_cpu,
            "total_disk_reads": total_disk_reads,
            "total_buffer_gets": total_buffer_gets,
            "total_elapsed_time_ms": total_elapsed,
            "total_cpu_time_ms": total_cpu,
        }

    def _extract_complexity_metrics(self, groups: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract average complexity metrics.

        Args:
            groups: List of query groups

        Returns:
            Dictionary containing average complexity metrics
        """
        if not groups:
            return {
                "avg_tables_per_query": 0.0,
                "avg_joins_per_query": 0.0,
                "avg_functions_per_query": 0.0,
            }

        total_tables = 0
        total_joins = 0
        total_functions = 0

        for group in groups:
            complexity = group.get("complexity", {})
            total_tables += complexity.get("table_count", 0)
            total_joins += complexity.get("join_count", 0)
            total_functions += complexity.get("function_count", 0)

        num_groups = len(groups)
        return {
            "avg_tables_per_query": total_tables / num_groups,
            "avg_joins_per_query": total_joins / num_groups,
            "avg_functions_per_query": total_functions / num_groups,
        }

    def _extract_io_metrics(
        self, groups: List[Dict[str, Any]], total_executions: int
    ) -> Dict[str, float]:
        """Extract I/O related metrics.

        Args:
            groups: List of query groups
            total_executions: Total execution count

        Returns:
            Dictionary containing I/O metrics
        """
        total_disk_reads = sum(g.get("total_disk_reads", 0) for g in groups)
        total_buffer_gets = sum(g.get("total_buffer_gets", 0) for g in groups)

        avg_disk_reads = total_disk_reads / total_executions if total_executions > 0 else 0.0
        avg_buffer_gets = total_buffer_gets / total_executions if total_executions > 0 else 0.0

        # Buffer hit ratio = (buffer_gets - disk_reads) / buffer_gets
        buffer_hit_ratio = 0.0
        if total_buffer_gets > 0:
            buffer_hit_ratio = (total_buffer_gets - total_disk_reads) / total_buffer_gets

        return {
            "avg_disk_reads_per_execution": avg_disk_reads,
            "avg_buffer_gets_per_execution": avg_buffer_gets,
            "buffer_hit_ratio": buffer_hit_ratio,
        }

    def _extract_top_queries(
        self, groups: List[Dict[str, Any]], sort_key: str, top_n: int
    ) -> List[Dict[str, Any]]:
        """Extract top N queries sorted by specified metric.

        Args:
            groups: List of query groups
            sort_key: Key to sort by (e.g., "total_executions")
            top_n: Number of top queries to return

        Returns:
            List of top N query groups
        """
        sorted_groups = sorted(groups, key=lambda g: g.get(sort_key, 0), reverse=True)
        return sorted_groups[:top_n]

    def _generate_summary(
        self,
        workload_data: Dict[str, Any],
        query_type_dist: Dict[str, int],
        performance: Dict[str, float],
    ) -> str:
        """Generate human-readable summary for LLM.

        Args:
            workload_data: Original workload data
            query_type_dist: Query type distribution
            performance: Performance metrics

        Returns:
            Human-readable summary string
        """
        total_patterns = workload_data.get("unique_patterns", 0)
        total_executions = workload_data.get("total_executions", 0)
        compression_ratio = workload_data.get("compression_ratio", 0.0)

        # Format query type distribution
        query_types = ", ".join(
            f"{count} {qtype}" for qtype, count in sorted(query_type_dist.items())
        )

        summary = (
            f"Workload Analysis Summary:\n"
            f"- Total unique query patterns: {total_patterns}\n"
            f"- Total executions: {total_executions}\n"
            f"- Compression ratio: {compression_ratio:.2f}x\n"
            f"- Query type distribution: {query_types}\n"
            f"- Average elapsed time per execution: {performance['avg_elapsed_time_ms']:.2f}ms\n"
            f"- Average CPU time per execution: {performance['avg_cpu_time_ms']:.2f}ms"
        )

        return summary

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure.

        Returns:
            Dictionary with empty/zero values
        """
        return {
            "total_patterns": 0,
            "total_executions": 0,
            "compression_ratio": 0.0,
            "query_type_distribution": {},
            "query_type_by_executions": {},
            "performance_metrics": {
                "avg_elapsed_time_ms": 0.0,
                "avg_cpu_time_ms": 0.0,
                "total_disk_reads": 0,
                "total_buffer_gets": 0,
                "total_elapsed_time_ms": 0.0,
                "total_cpu_time_ms": 0.0,
            },
            "complexity_metrics": {
                "avg_tables_per_query": 0.0,
                "avg_joins_per_query": 0.0,
                "avg_functions_per_query": 0.0,
            },
            "top_queries_by_executions": [],
            "top_queries_by_elapsed_time": [],
            "io_metrics": {
                "avg_disk_reads_per_execution": 0.0,
                "avg_buffer_gets_per_execution": 0.0,
                "buffer_hit_ratio": 0.0,
            },
            "summary": "Workload Analysis Summary:\n- No query patterns found",
        }
