"""SQL Query Parser for IRIS project.

This module provides the QueryParser class for analyzing Oracle SQL statements,
extracting features, patterns, and complexity metrics for optimization recommendations.
"""

import hashlib
import logging
import re
from typing import Any, Dict, List, Optional

import sqlparse
from sqlparse.sql import Function, Identifier, IdentifierList
from sqlparse.tokens import DML, Keyword

logger = logging.getLogger(__name__)


class QueryParser:
    """Parses SQL queries and extracts features for analysis.

    This class analyzes Oracle SQL statements to extract tables, joins, complexity
    metrics, bind variables, and other features needed for workload analysis and
    optimization recommendations.

    Example:
        >>> parser = QueryParser()
        >>> result = parser.parse("SELECT * FROM users WHERE age > :min_age")
        >>> print(result["query_type"])
        SELECT
        >>> print(result["tables"])
        ['users']
        >>> print(result["bind_variables"])
        [':min_age']
    """

    def __init__(self):
        """Initialize QueryParser."""
        logger.debug("QueryParser initialized")

    def parse(self, query: Optional[str]) -> Dict[str, Any]:
        """Parse SQL query and extract features.

        Args:
            query: SQL query string to parse

        Returns:
            Dictionary containing extracted features:
                - query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
                - tables: List of table names
                - join_count: Number of joins
                - join_types: List of join types (INNER, LEFT, etc.)
                - complexity: Dict of complexity metrics
                - bind_variables: List of bind variables
                - normalized: Normalized query string
                - signature: Query signature hash
                - functions: List of SQL functions used

        Raises:
            ValueError: If query is None
        """
        if query is None:
            raise ValueError("Query string cannot be None")

        if not query or not query.strip():
            return self._empty_result()

        try:
            # Parse the SQL statement
            parsed = sqlparse.parse(query)[0] if sqlparse.parse(query) else None
            if not parsed:
                return self._empty_result()

            result = {
                "query_type": self._extract_query_type(parsed),
                "tables": self._extract_tables(parsed),
                "join_count": self._count_joins(parsed),
                "join_types": self._extract_join_types(parsed),
                "complexity": self._calculate_complexity(parsed, query),
                "bind_variables": self._extract_bind_variables(query),
                "normalized": self._normalize_query(query),
                "signature": self._generate_signature(query),
                "functions": self._extract_functions(parsed),
            }

            logger.debug(f"Parsed query type: {result['query_type']}, tables: {result['tables']}")
            return result

        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            return self._empty_result()

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure."""
        return {
            "query_type": None,
            "tables": [],
            "join_count": 0,
            "join_types": [],
            "complexity": {
                "table_count": 0,
                "has_subquery": False,
                "has_aggregation": False,
                "has_group_by": False,
                "has_order_by": False,
            },
            "bind_variables": [],
            "normalized": "",
            "signature": "",
            "functions": [],
        }

    def _extract_query_type(self, parsed) -> Optional[str]:
        """Extract query type (SELECT, INSERT, UPDATE, DELETE)."""
        for token in parsed.tokens:
            if token.ttype is DML:
                return str(token.value).upper()
        return None

    def _extract_tables(self, parsed) -> List[str]:
        """Extract table names from query."""
        tables = []
        from_seen = False

        for token in parsed.tokens:
            if from_seen:
                # Skip whitespace
                if token.is_whitespace:
                    continue

                if isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        table_name = self._get_real_name(identifier)
                        if table_name:
                            tables.append(table_name)
                    from_seen = False
                elif isinstance(token, Identifier):
                    table_name = self._get_real_name(token)
                    if table_name:
                        tables.append(table_name)
                    from_seen = False
                elif token.ttype is Keyword:
                    # Hit another keyword (WHERE, JOIN, etc.), stop looking for FROM tables
                    from_seen = False

            if token.ttype is Keyword and token.value.upper() == "FROM":
                from_seen = True

        # Also extract tables from JOIN clauses
        tables.extend(self._extract_join_tables(parsed))

        return list(set(tables))  # Remove duplicates

    def _get_real_name(self, identifier) -> Optional[str]:
        """Get real table name from identifier (removing alias)."""
        if isinstance(identifier, Identifier):
            # Get the real name (not alias)
            real_name = identifier.get_real_name()
            return str(real_name) if real_name else None
        return str(identifier).strip()

    def _extract_join_tables(self, parsed) -> List[str]:
        """Extract table names from JOIN clauses."""
        tables = []
        query_str = str(parsed).upper()

        # Find all JOIN patterns
        join_pattern = r"(?:INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+|CROSS\s+)?JOIN\s+(\w+)"
        matches = re.finditer(join_pattern, query_str, re.IGNORECASE)

        for match in matches:
            table_name = match.group(1).lower()
            if table_name:
                tables.append(table_name)

        return tables

    def _count_joins(self, parsed) -> int:
        """Count number of JOIN clauses."""
        query_str = str(parsed).upper()
        return len(re.findall(r"\bJOIN\b", query_str))

    def _extract_join_types(self, parsed) -> List[str]:
        """Extract types of joins (INNER, LEFT, RIGHT, FULL)."""
        join_types = []
        query_str = str(parsed).upper()

        # Find all join type patterns
        patterns = [
            (r"\bINNER\s+JOIN\b", "INNER"),
            (r"\bLEFT\s+(?:OUTER\s+)?JOIN\b", "LEFT"),
            (r"\bRIGHT\s+(?:OUTER\s+)?JOIN\b", "RIGHT"),
            (r"\bFULL\s+(?:OUTER\s+)?JOIN\b", "FULL"),
            (r"\bCROSS\s+JOIN\b", "CROSS"),
        ]

        for pattern, join_type in patterns:
            if re.search(pattern, query_str):
                join_types.append(join_type)

        # If JOIN found without explicit type, it's INNER
        if re.search(r"\bJOIN\b", query_str) and not join_types:
            join_types.append("INNER")

        return join_types

    def _calculate_complexity(self, parsed, query: str) -> Dict[str, Any]:
        """Calculate complexity metrics."""
        query_upper = query.upper()

        return {
            "table_count": len(self._extract_tables(parsed)),
            "has_subquery": self._has_subquery(query),
            "has_aggregation": self._has_aggregation(query_upper),
            "has_group_by": "GROUP BY" in query_upper,
            "has_order_by": "ORDER BY" in query_upper,
        }

    def _has_subquery(self, query: str) -> bool:
        """Detect if query contains subqueries."""
        # Simple detection: look for SELECT within parentheses
        pattern = r"\(\s*SELECT\b"
        return bool(re.search(pattern, query, re.IGNORECASE))

    def _has_aggregation(self, query_upper: str) -> bool:
        """Detect if query uses aggregation functions."""
        agg_functions = ["COUNT(", "SUM(", "AVG(", "MIN(", "MAX(", "STDDEV(", "VARIANCE("]
        return any(func in query_upper for func in agg_functions)

    def _extract_bind_variables(self, query: str) -> List[str]:
        """Extract Oracle-style bind variables (:name)."""
        # Pattern for Oracle bind variables
        pattern = r":(\w+)"
        matches = re.findall(pattern, query)
        return [":" + match for match in matches]

    def _normalize_query(self, query: str) -> str:
        """Normalize query by replacing literals with placeholders."""
        normalized = query

        # Replace string literals
        normalized = re.sub(r"'[^']*'", "?", normalized)

        # Replace numeric literals (but not in function names or keywords)
        # Only replace standalone numbers
        normalized = re.sub(r"\b\d+\b", "?", normalized)

        # Normalize whitespace
        normalized = " ".join(normalized.split())

        return normalized

    def _generate_signature(self, query: str) -> str:
        """Generate a signature hash for the query structure."""
        # Normalize first to get consistent signatures
        normalized = self._normalize_query(query)

        # Create hash of normalized query
        signature = hashlib.md5(normalized.encode("utf-8")).hexdigest()

        return signature

    def _extract_functions(self, parsed) -> List[str]:
        """Extract SQL functions used in query."""
        functions = []

        def extract_from_tokens(tokens):
            for token in tokens:
                if isinstance(token, Function):
                    # Get function name
                    func_name = str(token.get_name())
                    functions.append(func_name)
                elif hasattr(token, "tokens"):
                    # Recursively search in sub-tokens
                    extract_from_tokens(token.tokens)

        extract_from_tokens(parsed.tokens)

        return functions
