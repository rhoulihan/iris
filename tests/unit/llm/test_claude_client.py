"""Unit tests for Claude API client.

This module tests the ClaudeClient class which provides integration with
Anthropic's Claude API for schema policy analysis.
"""

from unittest.mock import MagicMock, patch

import pytest


# Test data fixtures
@pytest.fixture
def mock_anthropic_client():
    """Provide a mock Anthropic client."""
    with patch("anthropic.Anthropic") as mock_class:
        mock_client = MagicMock()
        mock_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_message_response():
    """Provide sample Claude API message response."""
    response = MagicMock()
    response.id = "msg_123"
    response.model = "claude-sonnet-4-20250514"
    response.role = "assistant"
    response.content = [MagicMock(type="text", text="Sample response from Claude")]
    response.stop_reason = "end_turn"
    response.usage = MagicMock(input_tokens=100, output_tokens=50)
    return response


@pytest.fixture
def sample_error_response():
    """Provide sample error response from API."""
    error = Exception("Rate limit exceeded")
    error.status_code = 429
    return error


class TestClaudeClientInitialization:
    """Test ClaudeClient initialization."""

    @pytest.mark.unit
    def test_client_initialization_with_api_key(self, mock_anthropic_client):
        """Test that ClaudeClient can be initialized with API key."""
        from src.llm.claude_client import ClaudeClient

        client = ClaudeClient(api_key="sk-test-key")
        assert client is not None

    @pytest.mark.unit
    def test_client_initialization_from_env(self, mock_anthropic_client):
        """Test that ClaudeClient can get API key from environment."""
        from src.llm.claude_client import ClaudeClient

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-env-key"}):
            client = ClaudeClient()
            assert client is not None

    @pytest.mark.unit
    def test_client_requires_api_key(self):
        """Test that ClaudeClient raises error without API key."""
        from src.llm.claude_client import ClaudeClient

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                ClaudeClient()

    @pytest.mark.unit
    def test_client_sets_default_model(self, mock_anthropic_client):
        """Test that client sets default model."""
        from src.llm.claude_client import ClaudeClient

        client = ClaudeClient(api_key="sk-test-key")
        assert client.model == "claude-sonnet-4-20250514"

    @pytest.mark.unit
    def test_client_allows_custom_model(self, mock_anthropic_client):
        """Test that client allows custom model specification."""
        from src.llm.claude_client import ClaudeClient

        client = ClaudeClient(api_key="sk-test-key", model="claude-opus-4-20250514")
        assert client.model == "claude-opus-4-20250514"


class TestMessageSending:
    """Test message sending functionality."""

    @pytest.mark.unit
    def test_send_message_basic(self, mock_anthropic_client, sample_message_response):
        """Test sending a basic message."""
        from src.llm.claude_client import ClaudeClient

        mock_anthropic_client.messages.create.return_value = sample_message_response

        client = ClaudeClient(api_key="sk-test-key")
        response = client.send_message("Analyze this workload")

        assert response is not None
        assert "text" in response
        assert response["text"] == "Sample response from Claude"

    @pytest.mark.unit
    def test_send_message_with_system_prompt(self, mock_anthropic_client, sample_message_response):
        """Test sending message with system prompt."""
        from src.llm.claude_client import ClaudeClient

        mock_anthropic_client.messages.create.return_value = sample_message_response

        client = ClaudeClient(api_key="sk-test-key")
        response = client.send_message("Analyze this workload", system="You are a database expert")

        assert response is not None
        # Verify system prompt was passed
        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args[1]["system"] == "You are a database expert"

    @pytest.mark.unit
    def test_send_message_with_max_tokens(self, mock_anthropic_client, sample_message_response):
        """Test sending message with max tokens limit."""
        from src.llm.claude_client import ClaudeClient

        mock_anthropic_client.messages.create.return_value = sample_message_response

        client = ClaudeClient(api_key="sk-test-key")
        response = client.send_message("Analyze this workload", max_tokens=2000)

        assert response is not None
        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args[1]["max_tokens"] == 2000

    @pytest.mark.unit
    def test_send_message_with_temperature(self, mock_anthropic_client, sample_message_response):
        """Test sending message with temperature setting."""
        from src.llm.claude_client import ClaudeClient

        mock_anthropic_client.messages.create.return_value = sample_message_response

        client = ClaudeClient(api_key="sk-test-key")
        response = client.send_message("Analyze this workload", temperature=0.5)

        assert response is not None
        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args[1]["temperature"] == 0.5


class TestTokenTracking:
    """Test token usage tracking."""

    @pytest.mark.unit
    def test_tracks_input_tokens(self, mock_anthropic_client, sample_message_response):
        """Test that client tracks input tokens."""
        from src.llm.claude_client import ClaudeClient

        mock_anthropic_client.messages.create.return_value = sample_message_response

        client = ClaudeClient(api_key="sk-test-key")
        response = client.send_message("Test message")

        assert "usage" in response
        assert response["usage"]["input_tokens"] == 100

    @pytest.mark.unit
    def test_tracks_output_tokens(self, mock_anthropic_client, sample_message_response):
        """Test that client tracks output tokens."""
        from src.llm.claude_client import ClaudeClient

        mock_anthropic_client.messages.create.return_value = sample_message_response

        client = ClaudeClient(api_key="sk-test-key")
        response = client.send_message("Test message")

        assert response["usage"]["output_tokens"] == 50

    @pytest.mark.unit
    def test_cumulative_token_tracking(self, mock_anthropic_client, sample_message_response):
        """Test cumulative token usage tracking."""
        from src.llm.claude_client import ClaudeClient

        mock_anthropic_client.messages.create.return_value = sample_message_response

        client = ClaudeClient(api_key="sk-test-key")
        client.send_message("Message 1")
        client.send_message("Message 2")

        usage = client.get_total_usage()
        assert usage["input_tokens"] == 200  # 100 * 2
        assert usage["output_tokens"] == 100  # 50 * 2


class TestErrorHandling:
    """Test error handling and retry logic."""

    @pytest.mark.unit
    def test_handles_api_error(self, mock_anthropic_client):
        """Test handling of API errors."""
        from src.llm.claude_client import ClaudeClient

        mock_anthropic_client.messages.create.side_effect = Exception("API Error")

        client = ClaudeClient(api_key="sk-test-key")

        with pytest.raises(RuntimeError, match="Failed to send message"):
            client.send_message("Test message")

    @pytest.mark.unit
    def test_retry_on_rate_limit(self, mock_anthropic_client, sample_message_response):
        """Test retry logic on rate limit errors."""
        from src.llm.claude_client import ClaudeClient

        # First call fails with rate limit, second succeeds
        rate_limit_error = Exception("Rate limit exceeded")
        rate_limit_error.status_code = 429
        mock_anthropic_client.messages.create.side_effect = [
            rate_limit_error,
            sample_message_response,
        ]

        client = ClaudeClient(api_key="sk-test-key", max_retries=2)
        response = client.send_message("Test message")

        assert response is not None
        assert mock_anthropic_client.messages.create.call_count == 2

    @pytest.mark.unit
    def test_max_retries_exceeded(self, mock_anthropic_client):
        """Test that client stops after max retries."""
        from src.llm.claude_client import ClaudeClient

        rate_limit_error = Exception("Rate limit exceeded")
        rate_limit_error.status_code = 429
        mock_anthropic_client.messages.create.side_effect = rate_limit_error

        client = ClaudeClient(api_key="sk-test-key", max_retries=2)

        with pytest.raises(RuntimeError, match="Failed to send message"):
            client.send_message("Test message")

        assert mock_anthropic_client.messages.create.call_count == 2

    @pytest.mark.unit
    def test_handles_invalid_response(self, mock_anthropic_client):
        """Test handling of invalid API responses."""
        from src.llm.claude_client import ClaudeClient

        invalid_response = MagicMock()
        invalid_response.content = []  # Empty content
        mock_anthropic_client.messages.create.return_value = invalid_response

        client = ClaudeClient(api_key="sk-test-key")

        with pytest.raises(RuntimeError, match="Invalid response"):
            client.send_message("Test message")


class TestConversationContext:
    """Test conversation context management."""

    @pytest.mark.unit
    def test_send_message_with_context(self, mock_anthropic_client, sample_message_response):
        """Test sending message with conversation context."""
        from src.llm.claude_client import ClaudeClient

        mock_anthropic_client.messages.create.return_value = sample_message_response

        client = ClaudeClient(api_key="sk-test-key")
        context = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"},
        ]
        response = client.send_message("Follow-up message", context=context)

        assert response is not None
        call_args = mock_anthropic_client.messages.create.call_args
        messages = call_args[1]["messages"]
        assert len(messages) == 3  # 2 context + 1 new
        assert messages[0]["content"] == "Previous message"

    @pytest.mark.unit
    def test_conversation_history_tracking(self, mock_anthropic_client, sample_message_response):
        """Test that client tracks conversation history."""
        from src.llm.claude_client import ClaudeClient

        mock_anthropic_client.messages.create.return_value = sample_message_response

        client = ClaudeClient(api_key="sk-test-key")
        client.send_message("Message 1")
        client.send_message("Message 2")

        history = client.get_conversation_history()
        assert len(history) == 4  # 2 user + 2 assistant messages


class TestPromptTemplating:
    """Test prompt template functionality."""

    @pytest.mark.unit
    def test_format_workload_analysis_prompt(self, mock_anthropic_client):
        """Test formatting workload analysis prompt."""
        from src.llm.claude_client import ClaudeClient

        client = ClaudeClient(api_key="sk-test-key")
        workload_data = {"total_queries": 100, "total_executions": 5000}
        schema_data = {"tables": ["users", "orders"]}

        prompt = client.format_workload_analysis_prompt(workload_data, schema_data)

        assert "100" in prompt  # total_queries
        assert "5000" in prompt  # total_executions
        assert "users" in prompt or "orders" in prompt

    @pytest.mark.unit
    def test_format_schema_analysis_prompt(self, mock_anthropic_client):
        """Test formatting schema analysis prompt."""
        from src.llm.claude_client import ClaudeClient

        client = ClaudeClient(api_key="sk-test-key")
        schema_data = {
            "tables": [{"table_name": "users", "num_rows": 100000}],
            "indexes": [{"index_name": "users_pk", "columns": ["user_id"]}],
        }

        prompt = client.format_schema_analysis_prompt(schema_data)

        assert "users" in prompt
        assert "100000" in prompt or "100,000" in prompt


class TestResponseParsing:
    """Test response parsing functionality."""

    @pytest.mark.unit
    def test_parse_recommendation_response(self, mock_anthropic_client):
        """Test parsing recommendation from response."""
        from src.llm.claude_client import ClaudeClient

        client = ClaudeClient(api_key="sk-test-key")
        response_text = """
        Based on the analysis, I recommend:
        1. Create JSON Duality View for CUSTOMERS table
        2. Denormalize order items into orders document
        """

        recommendations = client.parse_recommendations(response_text)

        assert len(recommendations) >= 2
        assert any("CUSTOMERS" in str(r) for r in recommendations)

    @pytest.mark.unit
    def test_extract_sql_from_response(self, mock_anthropic_client):
        """Test extracting SQL statements from response."""
        from src.llm.claude_client import ClaudeClient

        client = ClaudeClient(api_key="sk-test-key")
        response_text = """
        Here's the implementation:
        ```sql
        CREATE JSON RELATIONAL DUALITY VIEW customer_dv AS
        SELECT * FROM customers;
        ```
        """

        sql_statements = client.extract_sql(response_text)

        assert len(sql_statements) == 1
        assert "CREATE JSON RELATIONAL DUALITY VIEW" in sql_statements[0]


class TestConfigurationOptions:
    """Test client configuration options."""

    @pytest.mark.unit
    def test_set_timeout(self, mock_anthropic_client):
        """Test setting request timeout."""
        from src.llm.claude_client import ClaudeClient

        client = ClaudeClient(api_key="sk-test-key", timeout=60)
        assert client.timeout == 60

    @pytest.mark.unit
    def test_set_max_retries(self, mock_anthropic_client):
        """Test setting max retries."""
        from src.llm.claude_client import ClaudeClient

        client = ClaudeClient(api_key="sk-test-key", max_retries=5)
        assert client.max_retries == 5

    @pytest.mark.unit
    def test_set_retry_delay(self, mock_anthropic_client):
        """Test setting retry delay."""
        from src.llm.claude_client import ClaudeClient

        client = ClaudeClient(api_key="sk-test-key", retry_delay=2.0)
        assert client.retry_delay == 2.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_empty_message(self, mock_anthropic_client):
        """Test handling of empty message."""
        from src.llm.claude_client import ClaudeClient

        client = ClaudeClient(api_key="sk-test-key")

        with pytest.raises(ValueError, match="Message cannot be empty"):
            client.send_message("")

    @pytest.mark.unit
    def test_very_long_message(self, mock_anthropic_client, sample_message_response):
        """Test handling of very long messages."""
        from src.llm.claude_client import ClaudeClient

        mock_anthropic_client.messages.create.return_value = sample_message_response

        client = ClaudeClient(api_key="sk-test-key")
        long_message = "A" * 100000  # 100K characters

        response = client.send_message(long_message)
        assert response is not None

    @pytest.mark.unit
    def test_special_characters_in_message(self, mock_anthropic_client, sample_message_response):
        """Test handling of special characters."""
        from src.llm.claude_client import ClaudeClient

        mock_anthropic_client.messages.create.return_value = sample_message_response

        client = ClaudeClient(api_key="sk-test-key")
        message_with_special_chars = 'Test "quotes" and \\backslashes\\ and newlines\n'

        response = client.send_message(message_with_special_chars)
        assert response is not None
