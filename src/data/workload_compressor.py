"""Workload Compressor for IRIS project.

This module provides the WorkloadCompressor class for deduplicating and aggregating
SQL workload data to reduce volume for efficient LLM processing.
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

from src.data.query_parser import QueryParser

logger = logging.getLogger(__name__)


class WorkloadCompressor:
    """Compresses SQL workload data by grouping similar queries.

    This class deduplicates SQL queries by grouping them based on their structural
    signature (ignoring literal values), and aggregates their execution statistics.
    This reduces the volume of data that needs to be processed by the LLM while
    preserving essential workload characteristics.

    Example:
        >>> compressor = WorkloadCompressor()
        >>> workload = [
        ...     {"sql_id": "a", "sql_text": "SELECT * FROM users WHERE id = 1", "executions": 100},
        ...     {"sql_id": "b", "sql_text": "SELECT * FROM users WHERE id = 2", "executions": 50},
        ... ]
        >>> result = compressor.compress(workload)
        >>> print(result["unique_patterns"])
        1
        >>> print(result["compression_ratio"])
        2.0
    """

    def __init__(self):
        """Initialize WorkloadCompressor with QueryParser."""
        self.parser = QueryParser()
        logger.debug("WorkloadCompressor initialized")

    def compress(self, workload_data: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Compress workload by grouping similar queries.

        Args:
            workload_data: List of SQL statistics from AWR collector, each containing:
                - sql_id: SQL identifier
                - sql_text: SQL statement text
                - executions: Number of executions
                - elapsed_time_ms: Total elapsed time
                - cpu_time_ms: Total CPU time
                - disk_reads: Total disk reads
                - buffer_gets: Total buffer gets
                - rows_processed: Total rows processed
                - avg_elapsed_time_ms: Average elapsed time per execution
                - avg_cpu_time_ms: Average CPU time per execution

        Returns:
            Dictionary containing compressed workload:
                - groups: List of query groups with aggregated statistics
                - total_queries: Total number of input queries
                - total_executions: Total executions across all queries
                - unique_patterns: Number of unique query patterns
                - compression_ratio: Ratio of input queries to unique patterns

        Raises:
            ValueError: If workload_data is None
        """
        if workload_data is None:
            raise ValueError("Workload data cannot be None")

        if not workload_data:
            return self._empty_result()

        # Group queries by signature
        groups_dict: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "sql_ids": [],
                "representative_sql": None,
                "query_type": None,
                "complexity": {},
                "total_executions": 0,
                "total_elapsed_time_ms": 0.0,
                "total_cpu_time_ms": 0.0,
                "total_disk_reads": 0,
                "total_buffer_gets": 0,
                "total_rows_processed": 0,
            }
        )

        total_queries = 0
        total_executions = 0

        for query_stat in workload_data:
            sql_text = query_stat.get("sql_text")
            if not sql_text:
                logger.debug(f"Skipping query {query_stat.get('sql_id')}: no SQL text")
                continue

            # Parse query to get signature and metadata
            parsed = self.parser.parse(sql_text)
            signature = parsed["signature"]

            # Initialize group on first occurrence
            group = groups_dict[signature]
            if group["representative_sql"] is None:
                group["representative_sql"] = sql_text
                group["query_type"] = parsed["query_type"]
                group["complexity"] = parsed["complexity"]
                group["signature"] = signature

            # Aggregate statistics
            group["sql_ids"].append(query_stat.get("sql_id", "unknown"))
            group["total_executions"] += query_stat.get("executions", 0)
            group["total_elapsed_time_ms"] += query_stat.get("elapsed_time_ms", 0.0)
            group["total_cpu_time_ms"] += query_stat.get("cpu_time_ms", 0.0)
            group["total_disk_reads"] += query_stat.get("disk_reads", 0)
            group["total_buffer_gets"] += query_stat.get("buffer_gets", 0)
            group["total_rows_processed"] += query_stat.get("rows_processed", 0)

            total_queries += 1
            total_executions += query_stat.get("executions", 0)

        # Convert groups dict to list and calculate averages
        groups_list = []
        for _signature, group in groups_dict.items():
            group["query_count"] = len(group["sql_ids"])

            # Calculate averages
            if group["total_executions"] > 0:
                group["avg_elapsed_time_ms"] = (
                    group["total_elapsed_time_ms"] / group["total_executions"]
                )
                group["avg_cpu_time_ms"] = group["total_cpu_time_ms"] / group["total_executions"]
            else:
                group["avg_elapsed_time_ms"] = 0.0
                group["avg_cpu_time_ms"] = 0.0

            groups_list.append(group)

        # Sort groups by total executions (most frequent first)
        groups_list.sort(key=lambda g: g["total_executions"], reverse=True)

        unique_patterns = len(groups_list)
        compression_ratio = total_queries / unique_patterns if unique_patterns > 0 else 0.0

        result = {
            "groups": groups_list,
            "total_queries": total_queries,
            "total_executions": total_executions,
            "unique_patterns": unique_patterns,
            "compression_ratio": compression_ratio,
        }

        logger.info(
            f"Compressed {total_queries} queries into {unique_patterns} patterns "
            f"(ratio: {compression_ratio:.2f})"
        )

        return result

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure."""
        return {
            "groups": [],
            "total_queries": 0,
            "total_executions": 0,
            "unique_patterns": 0,
            "compression_ratio": 0.0,
        }
