"""Unit tests for SQL query parser.

This module tests the QueryParser class which extracts features and patterns
from Oracle SQL statements for analysis and optimization.
"""

import pytest


# Test data fixtures
@pytest.fixture
def simple_select_query():
    """Provide a simple SELECT query."""
    return "SELECT * FROM users WHERE age > 25"


@pytest.fixture
def complex_join_query():
    """Provide a complex query with multiple joins."""
    return """
        SELECT u.user_id, u.username, o.order_id, p.product_name
        FROM users u
        INNER JOIN orders o ON u.user_id = o.user_id
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN products p ON oi.product_id = p.product_id
        WHERE u.age > :min_age
        AND o.order_date >= :start_date
        ORDER BY o.order_date DESC
    """


@pytest.fixture
def subquery_example():
    """Provide a query with subqueries."""
    return """
        SELECT user_id, username
        FROM users
        WHERE user_id IN (
            SELECT DISTINCT user_id
            FROM orders
            WHERE total_amount > 1000
        )
        AND created_date > (SELECT MAX(created_date) - 30 FROM user_activity)
    """


@pytest.fixture
def aggregation_query():
    """Provide a query with aggregations."""
    return """
        SELECT department, COUNT(*) as emp_count, AVG(salary) as avg_salary
        FROM employees
        WHERE hire_date >= '2020-01-01'
        GROUP BY department
        HAVING COUNT(*) > 5
        ORDER BY avg_salary DESC
    """


@pytest.fixture
def bind_variable_query():
    """Provide a query with Oracle bind variables."""
    return "SELECT * FROM products WHERE category = :category AND price < :max_price"


@pytest.fixture
def literal_query():
    """Provide a query with literals to normalize."""
    return "SELECT * FROM users WHERE username = 'john_doe' AND age = 30"


class TestQueryParserInitialization:
    """Test QueryParser initialization."""

    @pytest.mark.unit
    def test_parser_initialization(self):
        """Test that QueryParser can be initialized."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        assert parser is not None

    @pytest.mark.unit
    def test_parser_with_empty_query(self):
        """Test that parser handles empty query string."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse("")
        assert result is not None
        assert result["query_type"] is None


class TestQueryTypeDetection:
    """Test query type detection."""

    @pytest.mark.unit
    def test_detect_select_query(self, simple_select_query):
        """Test detection of SELECT query type."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(simple_select_query)
        assert result["query_type"] == "SELECT"

    @pytest.mark.unit
    def test_detect_insert_query(self):
        """Test detection of INSERT query type."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse("INSERT INTO users (name, age) VALUES ('Alice', 25)")
        assert result["query_type"] == "INSERT"

    @pytest.mark.unit
    def test_detect_update_query(self):
        """Test detection of UPDATE query type."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse("UPDATE users SET age = 26 WHERE user_id = 1")
        assert result["query_type"] == "UPDATE"

    @pytest.mark.unit
    def test_detect_delete_query(self):
        """Test detection of DELETE query type."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse("DELETE FROM users WHERE user_id = 1")
        assert result["query_type"] == "DELETE"


class TestTableExtraction:
    """Test table name extraction."""

    @pytest.mark.unit
    def test_extract_single_table(self, simple_select_query):
        """Test extraction of single table name."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(simple_select_query)
        assert "users" in result["tables"]
        assert len(result["tables"]) == 1

    @pytest.mark.unit
    def test_extract_multiple_tables(self, complex_join_query):
        """Test extraction of multiple table names from joins."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(complex_join_query)
        assert "users" in result["tables"]
        assert "orders" in result["tables"]
        assert "order_items" in result["tables"]
        assert "products" in result["tables"]
        assert len(result["tables"]) == 4

    @pytest.mark.unit
    def test_extract_tables_with_aliases(self, complex_join_query):
        """Test that table aliases are resolved to actual table names."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(complex_join_query)
        # Should extract actual table names, not aliases (u, o, oi, p)
        assert "users" in result["tables"]
        assert "u" not in result["tables"]


class TestJoinDetection:
    """Test JOIN detection and classification."""

    @pytest.mark.unit
    def test_detect_inner_join(self, complex_join_query):
        """Test detection of INNER JOIN."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(complex_join_query)
        assert result["join_count"] >= 1
        assert "INNER" in str(result["join_types"])

    @pytest.mark.unit
    def test_detect_left_join(self, complex_join_query):
        """Test detection of LEFT JOIN."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(complex_join_query)
        assert "LEFT" in str(result["join_types"])

    @pytest.mark.unit
    def test_count_joins(self, complex_join_query):
        """Test counting number of joins in query."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(complex_join_query)
        assert result["join_count"] == 3


class TestComplexityMetrics:
    """Test query complexity metric calculation."""

    @pytest.mark.unit
    def test_table_count_metric(self, complex_join_query):
        """Test table count metric."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(complex_join_query)
        assert result["complexity"]["table_count"] == 4

    @pytest.mark.unit
    def test_has_subquery_metric(self, subquery_example):
        """Test subquery detection metric."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(subquery_example)
        assert result["complexity"]["has_subquery"] is True

    @pytest.mark.unit
    def test_no_subquery_metric(self, simple_select_query):
        """Test subquery detection on simple query."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(simple_select_query)
        assert result["complexity"]["has_subquery"] is False

    @pytest.mark.unit
    def test_has_aggregation_metric(self, aggregation_query):
        """Test aggregation function detection."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(aggregation_query)
        assert result["complexity"]["has_aggregation"] is True

    @pytest.mark.unit
    def test_has_group_by_metric(self, aggregation_query):
        """Test GROUP BY clause detection."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(aggregation_query)
        assert result["complexity"]["has_group_by"] is True

    @pytest.mark.unit
    def test_has_order_by_metric(self, aggregation_query):
        """Test ORDER BY clause detection."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(aggregation_query)
        assert result["complexity"]["has_order_by"] is True


class TestBindVariableExtraction:
    """Test bind variable extraction."""

    @pytest.mark.unit
    def test_extract_oracle_bind_variables(self, bind_variable_query):
        """Test extraction of Oracle-style bind variables (:name)."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(bind_variable_query)
        assert ":category" in result["bind_variables"] or "category" in result["bind_variables"]
        assert ":max_price" in result["bind_variables"] or "max_price" in result["bind_variables"]

    @pytest.mark.unit
    def test_bind_variable_count(self, complex_join_query):
        """Test counting bind variables."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(complex_join_query)
        # Query has :min_age and :start_date
        assert len(result["bind_variables"]) == 2


class TestQueryNormalization:
    """Test query normalization and signature generation."""

    @pytest.mark.unit
    def test_normalize_literals(self, literal_query):
        """Test that literals are replaced with placeholders."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(literal_query)
        normalized = result["normalized"]

        # Should not contain the literal values
        assert "john_doe" not in normalized
        assert "30" not in normalized or normalized.count("30") == 0

    @pytest.mark.unit
    def test_generate_query_signature(self, simple_select_query):
        """Test query signature generation."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(simple_select_query)
        assert "signature" in result
        assert result["signature"] is not None
        assert len(result["signature"]) > 0

    @pytest.mark.unit
    def test_same_signature_for_similar_queries(self):
        """Test that similar queries produce the same signature."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()

        query1 = "SELECT * FROM users WHERE age > 25"
        query2 = "SELECT * FROM users WHERE age > 30"

        result1 = parser.parse(query1)
        result2 = parser.parse(query2)

        # Should have same signature as structure is identical
        assert result1["signature"] == result2["signature"]


class TestFunctionExtraction:
    """Test extraction of SQL functions."""

    @pytest.mark.unit
    def test_extract_aggregate_functions(self, aggregation_query):
        """Test extraction of aggregate functions like COUNT, AVG."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse(aggregation_query)

        functions = result.get("functions", [])
        assert "COUNT" in [f.upper() for f in functions]
        assert "AVG" in [f.upper() for f in functions]

    @pytest.mark.unit
    def test_extract_scalar_functions(self):
        """Test extraction of scalar functions like UPPER, SUBSTR."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        query = "SELECT UPPER(username), SUBSTR(email, 1, 10) FROM users"
        result = parser.parse(query)

        functions = result.get("functions", [])
        assert "UPPER" in [f.upper() for f in functions]
        assert "SUBSTR" in [f.upper() for f in functions]


class TestErrorHandling:
    """Test error handling for invalid queries."""

    @pytest.mark.unit
    def test_handle_invalid_sql(self):
        """Test handling of syntactically invalid SQL."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()
        result = parser.parse("SELECT FROM WHERE")

        # Should not crash, should return a result with minimal info
        assert result is not None

    @pytest.mark.unit
    def test_handle_none_query(self):
        """Test handling of None as query input."""
        from src.data.query_parser import QueryParser

        parser = QueryParser()

        with pytest.raises(ValueError, match="Query string cannot be None"):
            parser.parse(None)
