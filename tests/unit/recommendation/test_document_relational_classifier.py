"""Unit tests for Document vs Relational Classifier.

This module tests the DocumentRelationalClassifier class which identifies tables
that should be stored as documents vs relational structures.
"""

import pytest

from src.recommendation.models import (
    ColumnMetadata,
    QueryPattern,
    SchemaMetadata,
    TableMetadata,
    WorkloadFeatures,
)


# Test fixtures
@pytest.fixture
def document_candidate_table():
    """Provide table that looks like a document candidate."""
    return TableMetadata(
        name="USER_PROFILES",
        schema="APP",
        num_rows=100000,
        avg_row_len=800,
        columns=[
            ColumnMetadata(name="USER_ID", data_type="NUMBER", nullable=False, avg_size=8),
            ColumnMetadata(name="USERNAME", data_type="VARCHAR2", nullable=False, avg_size=50),
            ColumnMetadata(name="EMAIL", data_type="VARCHAR2", nullable=False, avg_size=100),
            ColumnMetadata(name="PHONE", data_type="VARCHAR2", nullable=True, avg_size=20),
            ColumnMetadata(name="ADDRESS", data_type="VARCHAR2", nullable=True, avg_size=200),
            ColumnMetadata(name="BIO", data_type="VARCHAR2", nullable=True, avg_size=500),
            ColumnMetadata(name="PREFERENCES", data_type="JSON", nullable=True, avg_size=300),
            ColumnMetadata(name="METADATA", data_type="JSON", nullable=True, avg_size=200),
        ],
    )


@pytest.fixture
def relational_candidate_table():
    """Provide table that looks like a relational candidate."""
    return TableMetadata(
        name="SALES_TRANSACTIONS",
        schema="APP",
        num_rows=5000000,
        avg_row_len=100,
        columns=[
            ColumnMetadata(name="TRANSACTION_ID", data_type="NUMBER", nullable=False, avg_size=8),
            ColumnMetadata(name="CUSTOMER_ID", data_type="NUMBER", nullable=False, avg_size=8),
            ColumnMetadata(name="PRODUCT_ID", data_type="NUMBER", nullable=False, avg_size=8),
            ColumnMetadata(name="AMOUNT", data_type="NUMBER", nullable=False, avg_size=8),
            ColumnMetadata(name="TRANSACTION_DATE", data_type="DATE", nullable=False, avg_size=8),
        ],
    )


@pytest.fixture
def document_access_workload():
    """Provide workload with document-style access patterns."""
    return WorkloadFeatures(
        queries=[
            # SELECT * queries (fetch entire object)
            QueryPattern(
                query_id="select_all_001",
                sql_text="SELECT * FROM user_profiles WHERE user_id = :id",
                query_type="SELECT",
                executions=5000,
                avg_elapsed_time_ms=5.0,
                tables=["USER_PROFILES"],
                join_count=0,
            ),
            QueryPattern(
                query_id="select_all_002",
                sql_text="SELECT * FROM user_profiles WHERE username = :name",
                query_type="SELECT",
                executions=3000,
                avg_elapsed_time_ms=8.0,
                tables=["USER_PROFILES"],
                join_count=0,
            ),
            # Multi-column updates (update entire object)
            QueryPattern(
                query_id="update_multi",
                sql_text="UPDATE user_profiles SET email = :e, phone = :p, address = :a, preferences = :pref WHERE user_id = :id",
                query_type="UPDATE",
                executions=1000,
                avg_elapsed_time_ms=10.0,
                tables=["USER_PROFILES"],
                join_count=0,
            ),
            # Column-specific query (small portion)
            QueryPattern(
                query_id="select_cols",
                sql_text="SELECT username, email FROM user_profiles WHERE user_id = :id",
                query_type="SELECT",
                executions=1000,
                avg_elapsed_time_ms=3.0,
                tables=["USER_PROFILES"],
                join_count=0,
            ),
        ],
        total_executions=10000,
        unique_patterns=4,
    )


@pytest.fixture
def relational_access_workload():
    """Provide workload with relational-style access patterns."""
    return WorkloadFeatures(
        queries=[
            # Aggregate queries
            QueryPattern(
                query_id="agg_001",
                sql_text="SELECT customer_id, SUM(amount) FROM sales_transactions WHERE transaction_date > :date GROUP BY customer_id",
                query_type="SELECT",
                executions=3000,
                avg_elapsed_time_ms=50.0,
                tables=["SALES_TRANSACTIONS"],
                join_count=0,
            ),
            QueryPattern(
                query_id="agg_002",
                sql_text="SELECT product_id, AVG(amount), COUNT(*) FROM sales_transactions GROUP BY product_id",
                query_type="SELECT",
                executions=2000,
                avg_elapsed_time_ms=100.0,
                tables=["SALES_TRANSACTIONS"],
                join_count=0,
            ),
            # Complex joins
            QueryPattern(
                query_id="join_complex",
                sql_text="SELECT st.*, c.name, p.name FROM sales_transactions st JOIN customers c ON st.customer_id = c.customer_id JOIN products p ON st.product_id = p.product_id WHERE st.transaction_date > :date",
                query_type="SELECT",
                executions=2000,
                avg_elapsed_time_ms=80.0,
                tables=["SALES_TRANSACTIONS", "CUSTOMERS", "PRODUCTS"],
                join_count=2,
            ),
            # Column-specific queries
            QueryPattern(
                query_id="select_specific",
                sql_text="SELECT transaction_id, amount FROM sales_transactions WHERE customer_id = :id",
                query_type="SELECT",
                executions=3000,
                avg_elapsed_time_ms=20.0,
                tables=["SALES_TRANSACTIONS"],
                join_count=0,
            ),
        ],
        total_executions=10000,
        unique_patterns=4,
    )


class TestDocumentRelationalClassifierInitialization:
    """Test DocumentRelationalClassifier initialization."""

    @pytest.mark.unit
    def test_classifier_initialization_with_defaults(self):
        """Test that classifier initializes with default thresholds."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        classifier = DocumentRelationalClassifier()

        assert classifier is not None
        assert classifier.strong_signal_threshold == 0.3
        assert classifier.select_all_weight == 0.4
        assert classifier.object_access_weight == 0.3
        assert classifier.schema_flexibility_weight == 0.2
        assert classifier.multi_column_update_weight == 0.1

    @pytest.mark.unit
    def test_classifier_initialization_with_custom_thresholds(self):
        """Test that classifier accepts custom thresholds."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        classifier = DocumentRelationalClassifier(
            strong_signal_threshold=0.4,
            select_all_weight=0.5,
            object_access_weight=0.2,
        )

        assert classifier.strong_signal_threshold == 0.4
        assert classifier.select_all_weight == 0.5
        assert classifier.object_access_weight == 0.2


class TestDocumentCandidateDetection:
    """Test document candidate detection."""

    @pytest.mark.unit
    def test_detects_document_candidate(self, document_candidate_table, document_access_workload):
        """Test detection of document storage candidate."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        schema = SchemaMetadata(tables={"USER_PROFILES": document_candidate_table})

        classifier = DocumentRelationalClassifier()
        patterns = classifier.classify([document_candidate_table], document_access_workload, schema)

        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.pattern_type == "DOCUMENT_CANDIDATE"
        assert pattern.severity == "MEDIUM"
        assert pattern.confidence > 0.3
        assert "USER_PROFILES" in pattern.affected_objects

    @pytest.mark.unit
    def test_no_detection_for_neutral_tables(self, document_candidate_table):
        """Test that tables with neutral access patterns don't trigger detection."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        # Mixed workload with no strong signal
        neutral_workload = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="select_all",
                    sql_text="SELECT * FROM user_profiles WHERE user_id = :id",
                    query_type="SELECT",
                    executions=3000,
                    avg_elapsed_time_ms=5.0,
                    tables=["USER_PROFILES"],
                    join_count=0,
                ),
                QueryPattern(
                    query_id="aggregate",
                    sql_text="SELECT COUNT(*) FROM user_profiles GROUP BY username",
                    query_type="SELECT",
                    executions=3000,
                    avg_elapsed_time_ms=20.0,
                    tables=["USER_PROFILES"],
                    join_count=0,
                ),
            ],
            total_executions=6000,
            unique_patterns=2,
        )

        schema = SchemaMetadata(tables={"USER_PROFILES": document_candidate_table})

        classifier = DocumentRelationalClassifier()
        patterns = classifier.classify([document_candidate_table], neutral_workload, schema)

        # Might detect with low confidence or not at all
        if len(patterns) > 0:
            assert patterns[0].confidence < 0.31  # Allow for floating point imprecision


class TestRelationalCandidateDetection:
    """Test relational candidate detection."""

    @pytest.mark.unit
    def test_detects_relational_candidate(
        self, relational_candidate_table, relational_access_workload
    ):
        """Test detection of relational storage candidate."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        schema = SchemaMetadata(tables={"SALES_TRANSACTIONS": relational_candidate_table})

        classifier = DocumentRelationalClassifier()
        patterns = classifier.classify(
            [relational_candidate_table], relational_access_workload, schema
        )

        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.pattern_type == "RELATIONAL_CANDIDATE"
        assert pattern.severity == "MEDIUM"
        assert pattern.confidence > 0.3
        assert "SALES_TRANSACTIONS" in pattern.affected_objects


class TestDocumentScoring:
    """Test document score calculation."""

    @pytest.mark.unit
    def test_high_select_all_percentage_increases_document_score(self, document_candidate_table):
        """Test that SELECT * queries increase document score."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        # All queries are SELECT *
        workload = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="select_all",
                    sql_text="SELECT * FROM user_profiles WHERE user_id = :id",
                    query_type="SELECT",
                    executions=10000,
                    avg_elapsed_time_ms=5.0,
                    tables=["USER_PROFILES"],
                    join_count=0,
                ),
            ],
            total_executions=10000,
            unique_patterns=1,
        )

        schema = SchemaMetadata(tables={"USER_PROFILES": document_candidate_table})

        classifier = DocumentRelationalClassifier()
        patterns = classifier.classify([document_candidate_table], workload, schema)

        assert len(patterns) == 1
        assert patterns[0].pattern_type == "DOCUMENT_CANDIDATE"
        assert patterns[0].metrics["document_score"] > 0.3

    @pytest.mark.unit
    def test_high_nullable_percentage_increases_document_score(self):
        """Test that many nullable columns increase document score."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        # Table with 80% nullable columns (schema flexibility)
        flexible_table = TableMetadata(
            name="FLEXIBLE_DATA",
            schema="APP",
            num_rows=10000,
            avg_row_len=300,
            columns=[
                ColumnMetadata(name="ID", data_type="NUMBER", nullable=False, avg_size=8),
                ColumnMetadata(name="FIELD1", data_type="VARCHAR2", nullable=True, avg_size=50),
                ColumnMetadata(name="FIELD2", data_type="VARCHAR2", nullable=True, avg_size=50),
                ColumnMetadata(name="FIELD3", data_type="VARCHAR2", nullable=True, avg_size=50),
                ColumnMetadata(name="FIELD4", data_type="VARCHAR2", nullable=True, avg_size=50),
            ],
        )

        workload = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="select",
                    sql_text="SELECT * FROM flexible_data WHERE id = :id",
                    query_type="SELECT",
                    executions=5000,
                    avg_elapsed_time_ms=5.0,
                    tables=["FLEXIBLE_DATA"],
                    join_count=0,
                ),
            ],
            total_executions=5000,
            unique_patterns=1,
        )

        schema = SchemaMetadata(tables={"FLEXIBLE_DATA": flexible_table})

        classifier = DocumentRelationalClassifier()
        patterns = classifier.classify([flexible_table], workload, schema)

        assert len(patterns) >= 1
        doc_pattern = [p for p in patterns if p.pattern_type == "DOCUMENT_CANDIDATE"]
        assert len(doc_pattern) > 0
        assert doc_pattern[0].metrics["nullable_column_percentage"] == 80.0


class TestRelationalScoring:
    """Test relational score calculation."""

    @pytest.mark.unit
    def test_aggregate_queries_increase_relational_score(self, relational_candidate_table):
        """Test that aggregate queries increase relational score."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        # All queries are aggregates
        workload = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="agg",
                    sql_text="SELECT SUM(amount), AVG(amount), COUNT(*) FROM sales_transactions GROUP BY customer_id",
                    query_type="SELECT",
                    executions=10000,
                    avg_elapsed_time_ms=50.0,
                    tables=["SALES_TRANSACTIONS"],
                    join_count=0,
                ),
            ],
            total_executions=10000,
            unique_patterns=1,
        )

        schema = SchemaMetadata(tables={"SALES_TRANSACTIONS": relational_candidate_table})

        classifier = DocumentRelationalClassifier()
        patterns = classifier.classify([relational_candidate_table], workload, schema)

        assert len(patterns) == 1
        assert patterns[0].pattern_type == "RELATIONAL_CANDIDATE"
        assert patterns[0].metrics["aggregate_query_percentage"] == 100.0

    @pytest.mark.unit
    def test_complex_joins_increase_relational_score(self, relational_candidate_table):
        """Test that complex joins increase relational score."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        # All queries have complex joins
        workload = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="join",
                    sql_text="SELECT st.*, c.*, p.* FROM sales_transactions st JOIN customers c ON st.customer_id = c.customer_id JOIN products p ON st.product_id = p.product_id JOIN categories cat ON p.category_id = cat.category_id",
                    query_type="SELECT",
                    executions=10000,
                    avg_elapsed_time_ms=100.0,
                    tables=["SALES_TRANSACTIONS", "CUSTOMERS", "PRODUCTS", "CATEGORIES"],
                    join_count=3,
                ),
            ],
            total_executions=10000,
            unique_patterns=1,
        )

        schema = SchemaMetadata(tables={"SALES_TRANSACTIONS": relational_candidate_table})

        classifier = DocumentRelationalClassifier()
        patterns = classifier.classify([relational_candidate_table], workload, schema)

        assert len(patterns) == 1
        assert patterns[0].pattern_type == "RELATIONAL_CANDIDATE"
        assert patterns[0].metrics["join_query_percentage"] == 100.0


class TestClassifierMetrics:
    """Test metrics calculation."""

    @pytest.mark.unit
    def test_pattern_includes_all_required_metrics(
        self, document_candidate_table, document_access_workload
    ):
        """Test that detected pattern includes all required metrics."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        schema = SchemaMetadata(tables={"USER_PROFILES": document_candidate_table})

        classifier = DocumentRelationalClassifier()
        patterns = classifier.classify([document_candidate_table], document_access_workload, schema)

        assert len(patterns) == 1
        metrics = patterns[0].metrics

        assert "document_score" in metrics
        assert "relational_score" in metrics
        assert "select_all_percentage" in metrics
        assert "nullable_column_percentage" in metrics


class TestClassifierRecommendations:
    """Test recommendation hints."""

    @pytest.mark.unit
    def test_document_recommendation_mentions_json(
        self, document_candidate_table, document_access_workload
    ):
        """Test that document recommendation suggests JSON storage."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        schema = SchemaMetadata(tables={"USER_PROFILES": document_candidate_table})

        classifier = DocumentRelationalClassifier()
        patterns = classifier.classify([document_candidate_table], document_access_workload, schema)

        assert len(patterns) == 1
        hint = patterns[0].recommendation_hint.lower()

        assert any(keyword in hint for keyword in ["json", "document", "collection"])

    @pytest.mark.unit
    def test_relational_recommendation_mentions_normalization(
        self, relational_candidate_table, relational_access_workload
    ):
        """Test that relational recommendation suggests normalization."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        schema = SchemaMetadata(tables={"SALES_TRANSACTIONS": relational_candidate_table})

        classifier = DocumentRelationalClassifier()
        patterns = classifier.classify(
            [relational_candidate_table], relational_access_workload, schema
        )

        assert len(patterns) == 1
        hint = patterns[0].recommendation_hint.lower()

        assert any(keyword in hint for keyword in ["normaliz", "relational", "structure"])


class TestClassifierEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_empty_tables_list(self, document_access_workload):
        """Test handling of empty tables list."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        schema = SchemaMetadata(tables={})

        classifier = DocumentRelationalClassifier()
        patterns = classifier.classify([], document_access_workload, schema)

        assert len(patterns) == 0

    @pytest.mark.unit
    def test_empty_workload(self, document_candidate_table):
        """Test handling of empty workload."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        empty_workload = WorkloadFeatures(queries=[], total_executions=0, unique_patterns=0)

        schema = SchemaMetadata(tables={"USER_PROFILES": document_candidate_table})

        classifier = DocumentRelationalClassifier()
        patterns = classifier.classify([document_candidate_table], empty_workload, schema)

        assert len(patterns) == 0

    @pytest.mark.unit
    def test_table_not_in_workload(self, document_candidate_table):
        """Test handling of table not referenced in workload."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        # Workload for different table
        workload = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="other",
                    sql_text="SELECT * FROM other_table WHERE id = :id",
                    query_type="SELECT",
                    executions=5000,
                    avg_elapsed_time_ms=5.0,
                    tables=["OTHER_TABLE"],
                    join_count=0,
                ),
            ],
            total_executions=5000,
            unique_patterns=1,
        )

        schema = SchemaMetadata(tables={"USER_PROFILES": document_candidate_table})

        classifier = DocumentRelationalClassifier()
        patterns = classifier.classify([document_candidate_table], workload, schema)

        assert len(patterns) == 0

    @pytest.mark.unit
    def test_pattern_id_uniqueness(self, document_candidate_table, relational_candidate_table):
        """Test that each detected pattern has a unique ID."""
        from src.recommendation.pattern_detector import DocumentRelationalClassifier

        # Create workload that accesses both tables differently
        workload = WorkloadFeatures(
            queries=[
                QueryPattern(
                    query_id="doc_access",
                    sql_text="SELECT * FROM user_profiles WHERE user_id = :id",
                    query_type="SELECT",
                    executions=5000,
                    avg_elapsed_time_ms=5.0,
                    tables=["USER_PROFILES"],
                    join_count=0,
                ),
                QueryPattern(
                    query_id="rel_access",
                    sql_text="SELECT SUM(amount) FROM sales_transactions GROUP BY customer_id",
                    query_type="SELECT",
                    executions=5000,
                    avg_elapsed_time_ms=50.0,
                    tables=["SALES_TRANSACTIONS"],
                    join_count=0,
                ),
            ],
            total_executions=10000,
            unique_patterns=2,
        )

        schema = SchemaMetadata(
            tables={
                "USER_PROFILES": document_candidate_table,
                "SALES_TRANSACTIONS": relational_candidate_table,
            }
        )

        classifier = DocumentRelationalClassifier()
        patterns = classifier.classify(
            [document_candidate_table, relational_candidate_table], workload, schema
        )

        pattern_ids = [p.pattern_id for p in patterns]
        assert len(pattern_ids) == len(set(pattern_ids))  # All unique
