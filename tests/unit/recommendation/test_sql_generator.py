"""Unit tests for LLM-powered SQL generator."""

from unittest.mock import MagicMock, patch

import pytest

from src.recommendation.models import DetectedPattern, TableMetadata, WorkloadFeatures
from src.recommendation.sql_generator import GeneratedSQL, SQLGenerationError, SQLGenerator


# Test fixtures
def create_lob_pattern() -> DetectedPattern:
    """Create a test LOB cliff pattern."""
    return DetectedPattern(
        pattern_id="PAT-LOB-001",
        pattern_type="LOB_CLIFF",
        severity="HIGH",
        confidence=0.85,
        affected_objects=["PRODUCTS.description"],
        description="Large CLOB with frequent small updates",
        metrics={"document_size_kb": 50, "update_frequency": 200},
        recommendation_hint="Split LOB into separate table",
    )


def create_table_metadata() -> TableMetadata:
    """Create test table metadata."""
    from src.recommendation.models import ColumnMetadata

    return TableMetadata(
        name="PRODUCTS",
        schema="APP",
        num_rows=100000,
        avg_row_len=5000,
        columns=[
            ColumnMetadata(name="product_id", data_type="NUMBER", nullable=False),
            ColumnMetadata(name="name", data_type="VARCHAR2", nullable=False),
            ColumnMetadata(name="description", data_type="CLOB", nullable=True, avg_size=50000),
        ],
    )


def create_workload_features() -> WorkloadFeatures:
    """Create test workload features."""
    return WorkloadFeatures(
        queries=[],
        total_executions=1000,
        unique_patterns=10,
    )


class TestGeneratedSQL:
    """Test GeneratedSQL data model."""

    def test_create_generated_sql(self):
        """Test creating a GeneratedSQL instance."""
        sql = GeneratedSQL(
            implementation_sql="CREATE TABLE ...",
            rollback_sql="DROP TABLE ...",
            testing_steps="1. Test in dev\n2. Monitor performance",
            llm_reasoning="Split CLOB to avoid LOB chaining",
        )

        assert "CREATE TABLE" in sql.implementation_sql
        assert "DROP TABLE" in sql.rollback_sql
        assert "Test in dev" in sql.testing_steps
        assert "LOB chaining" in sql.llm_reasoning


class TestSQLGeneratorInitialization:
    """Test SQLGenerator initialization."""

    def test_create_generator_with_mock_client(self):
        """Test creating SQL generator with mock LLM client."""
        mock_client = MagicMock()
        generator = SQLGenerator(llm_client=mock_client)

        assert generator is not None
        assert generator.llm_client == mock_client

    def test_create_generator_without_client(self):
        """Test creating SQL generator without client (should create default)."""
        with patch("src.recommendation.sql_generator.ClaudeClient") as MockClient:
            generator = SQLGenerator()
            assert generator is not None
            MockClient.assert_called_once()


class TestLOBCliffSQLGeneration:
    """Test SQL generation for LOB cliff patterns."""

    def test_generate_lob_split_sql(self):
        """Should generate SQL to split LOB into separate table."""
        mock_client = MagicMock()
        mock_response = """
IMPLEMENTATION SQL:
```sql
CREATE TABLE products_description (
    product_id NUMBER NOT NULL,
    description CLOB,
    CONSTRAINT fk_prod_desc FOREIGN KEY (product_id) REFERENCES products(product_id)
);
```

ROLLBACK SQL:
```sql
DROP TABLE products_description;
```

TESTING STEPS:
1. Create in test environment
2. Shadow testing with production workload

REASONING:
Splitting the CLOB eliminates LOB chaining on frequent updates.
"""
        mock_client.send_message.return_value = {"text": mock_response}

        generator = SQLGenerator(llm_client=mock_client)
        pattern = create_lob_pattern()
        table = create_table_metadata()
        workload = create_workload_features()

        result = generator.generate_sql(pattern, table, workload)

        assert result is not None
        assert "CREATE TABLE products_description" in result.implementation_sql
        assert "DROP TABLE products_description" in result.rollback_sql
        assert "Shadow testing" in result.testing_steps
        assert "LOB chaining" in result.llm_reasoning


class TestPromptGeneration:
    """Test prompt generation for different patterns."""

    def test_generate_lob_prompt(self):
        """Should generate appropriate prompt for LOB cliff pattern."""
        generator = SQLGenerator(llm_client=MagicMock())
        pattern = create_lob_pattern()
        table = create_table_metadata()
        workload = create_workload_features()

        prompt = generator._build_prompt(pattern, table, workload)

        assert "LOB" in prompt or "CLOB" in prompt
        assert "PRODUCTS" in prompt
        assert "description" in prompt
        assert "Oracle" in prompt

    def test_generate_join_prompt(self):
        """Should generate appropriate prompt for expensive join pattern."""
        generator = SQLGenerator(llm_client=MagicMock())
        pattern = DetectedPattern(
            pattern_id="PAT-JOIN-001",
            pattern_type="EXPENSIVE_JOIN",
            severity="MEDIUM",
            confidence=0.75,
            affected_objects=["ORDERS", "CUSTOMERS"],
            description="Frequent join",
            metrics={"join_frequency": 1000},
            recommendation_hint="Denormalize",
        )
        table = create_table_metadata()
        workload = create_workload_features()

        prompt = generator._build_prompt(pattern, table, workload)

        assert "denormaliz" in prompt.lower()
        assert "ORDERS" in prompt or "CUSTOMERS" in prompt
        assert "Oracle" in prompt

    def test_generate_document_prompt(self):
        """Should generate appropriate prompt for document candidate pattern."""
        generator = SQLGenerator(llm_client=MagicMock())
        pattern = DetectedPattern(
            pattern_id="PAT-DOC-001",
            pattern_type="DOCUMENT_CANDIDATE",
            severity="MEDIUM",
            confidence=0.70,
            affected_objects=["USER_PROFILES"],
            description="Document-like access",
            metrics={"select_star_pct": 0.8},
            recommendation_hint="Convert to JSON",
        )
        table = create_table_metadata()
        workload = create_workload_features()

        prompt = generator._build_prompt(pattern, table, workload)

        assert "JSON" in prompt
        assert "relational" in prompt.lower()
        assert "Oracle" in prompt

    def test_generate_duality_view_prompt(self):
        """Should generate appropriate prompt for duality view pattern."""
        generator = SQLGenerator(llm_client=MagicMock())
        pattern = DetectedPattern(
            pattern_id="PAT-DV-001",
            pattern_type="DUALITY_VIEW_OPPORTUNITY",
            severity="MEDIUM",
            confidence=0.75,
            affected_objects=["ORDERS"],
            description="Mixed workload",
            metrics={"oltp_pct": 0.6, "analytics_pct": 0.4},
            recommendation_hint="Create Duality View",
        )
        table = create_table_metadata()
        workload = create_workload_features()

        prompt = generator._build_prompt(pattern, table, workload)

        assert "DUALITY VIEW" in prompt or "Duality View" in prompt
        assert "JSON" in prompt
        assert "Oracle 23ai" in prompt

    def test_generate_generic_prompt(self):
        """Should generate generic prompt for unknown pattern types."""
        generator = SQLGenerator(llm_client=MagicMock())
        pattern = DetectedPattern(
            pattern_id="PAT-UNK-001",
            pattern_type="UNKNOWN_PATTERN",
            severity="LOW",
            confidence=0.50,
            affected_objects=["TABLE1"],
            description="Unknown pattern",
            metrics={},
            recommendation_hint="Optimize",
        )
        table = create_table_metadata()
        workload = create_workload_features()

        prompt = generator._build_prompt(pattern, table, workload)

        assert "Oracle" in prompt
        assert "UNKNOWN_PATTERN" in prompt
        assert "TABLE1" in prompt


class TestErrorHandling:
    """Test error handling in SQL generation."""

    def test_llm_timeout_raises_error(self):
        """Should raise error on LLM timeout."""
        mock_client = MagicMock()
        mock_client.send_message.side_effect = TimeoutError("LLM timeout")

        generator = SQLGenerator(llm_client=mock_client)
        pattern = create_lob_pattern()
        table = create_table_metadata()
        workload = create_workload_features()

        with pytest.raises(SQLGenerationError) as exc_info:
            generator.generate_sql(pattern, table, workload)
        assert "timeout" in str(exc_info.value).lower()

    def test_invalid_response_raises_error(self):
        """Should raise error on invalid LLM response."""
        mock_client = MagicMock()
        mock_client.send_message.return_value = {"text": "Invalid response without SQL blocks"}

        generator = SQLGenerator(llm_client=mock_client)
        pattern = create_lob_pattern()
        table = create_table_metadata()
        workload = create_workload_features()

        with pytest.raises(SQLGenerationError) as exc_info:
            generator.generate_sql(pattern, table, workload)
        assert "parse" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()


class TestSQLCleaning:
    """Test SQL syntax validation and cleaning."""

    def test_cleans_sql_code_blocks(self):
        """Should remove markdown code blocks from SQL."""
        mock_client = MagicMock()
        mock_response = """
IMPLEMENTATION SQL:
```sql
CREATE TABLE products_description (product_id NUMBER);
```

ROLLBACK SQL:
```sql
DROP TABLE products_description;
```

TESTING STEPS:
Test it

REASONING:
Because
"""
        mock_client.send_message.return_value = {"text": mock_response}

        generator = SQLGenerator(llm_client=mock_client)
        pattern = create_lob_pattern()
        table = create_table_metadata()
        workload = create_workload_features()

        result = generator.generate_sql(pattern, table, workload)

        # Should have extracted SQL from code blocks
        assert "```" not in result.implementation_sql
        assert "```" not in result.rollback_sql
        assert "CREATE TABLE products_description" in result.implementation_sql
