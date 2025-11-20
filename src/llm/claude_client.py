"""Claude API Client for IRIS project.

This module provides the ClaudeClient class for integrating with Anthropic's Claude API
to perform sophisticated schema policy analysis and generate recommendations.
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

import anthropic

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Client for interacting with Claude API for schema policy analysis.

    This class provides methods to send messages to Claude, manage conversation context,
    track token usage, and parse responses for structured recommendations.

    Attributes:
        client: Anthropic client instance
        model: Claude model to use
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds
        conversation_history: List of conversation messages
        total_input_tokens: Cumulative input tokens used
        total_output_tokens: Cumulative output tokens used

    Example:
        >>> client = ClaudeClient(api_key="sk-ant-...")
        >>> response = client.send_message("Analyze this workload", max_tokens=4000)
        >>> print(response["text"])
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TEMPERATURE = 1.0

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 600,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize ClaudeClient.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use (defaults to claude-sonnet-4-20250514)
            timeout: Request timeout in seconds (default: 600)
            max_retries: Maximum retry attempts (default: 3)
            retry_delay: Initial retry delay in seconds (default: 1.0)

        Raises:
            ValueError: If API key is not provided and not in environment
        """
        if api_key is None:
            api_key = os.environ.get("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError("API key required: provide api_key or set ANTHROPIC_API_KEY")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model or self.DEFAULT_MODEL
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Conversation tracking
        self.conversation_history: List[Dict[str, str]] = []

        # Token usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        logger.info(f"ClaudeClient initialized with model {self.model}")

    def send_message(
        self,
        message: str,
        system: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Send a message to Claude and get response.

        Args:
            message: User message to send
            system: Optional system prompt
            context: Optional conversation context (list of message dicts)
            max_tokens: Maximum tokens in response (default: 4096)
            temperature: Temperature for sampling (default: 1.0)

        Returns:
            Dictionary containing:
                - text: Response text
                - model: Model used
                - stop_reason: Why generation stopped
                - usage: Token usage information

        Raises:
            ValueError: If message is empty
            RuntimeError: If API call fails after retries
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        # Build messages list
        messages = []
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": message})

        # Prepare API call parameters
        params = {
            "model": self.model,
            "max_tokens": max_tokens or self.DEFAULT_MAX_TOKENS,
            "messages": messages,
        }

        if system:
            params["system"] = system

        if temperature is not None:
            params["temperature"] = temperature

        # Retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(**params)

                # Validate response
                if not response.content:
                    raise RuntimeError("Invalid response: empty content")

                # Extract text from response
                response_text = ""
                for block in response.content:
                    if block.type == "text":
                        response_text += block.text

                # Track token usage
                if hasattr(response, "usage"):
                    self.total_input_tokens += response.usage.input_tokens
                    self.total_output_tokens += response.usage.output_tokens

                # Track conversation
                self.conversation_history.append({"role": "user", "content": message})
                self.conversation_history.append({"role": "assistant", "content": response_text})

                # Build result
                result = {
                    "text": response_text,
                    "model": response.model,
                    "stop_reason": response.stop_reason,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                }

                logger.info(
                    f"Message sent successfully. Tokens: {response.usage.input_tokens} in, "
                    f"{response.usage.output_tokens} out"
                )
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"API call attempt {attempt + 1} failed: {e}")

                # Check if it's a rate limit error
                is_rate_limit = (
                    hasattr(e, "status_code") and e.status_code == 429
                ) or "rate limit" in str(e).lower()

                if is_rate_limit and attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay * (2**attempt)
                    logger.info(f"Rate limited. Retrying in {delay}s...")
                    time.sleep(delay)
                elif attempt < self.max_retries - 1:
                    # Regular retry
                    time.sleep(self.retry_delay)
                else:
                    break

        # All retries exhausted
        logger.error(f"Failed to send message after {self.max_retries} attempts: {last_error}")
        raise RuntimeError(f"Failed to send message: {last_error}") from last_error

    def get_total_usage(self) -> Dict[str, int]:
        """Get cumulative token usage.

        Returns:
            Dictionary with input_tokens and output_tokens
        """
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
        }

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history.

        Returns:
            List of message dictionaries
        """
        return self.conversation_history.copy()

    def format_workload_analysis_prompt(
        self, workload_data: Dict[str, Any], schema_data: Dict[str, Any]
    ) -> str:
        """Format a prompt for workload analysis.

        Args:
            workload_data: Workload features from FeatureEngineer
            schema_data: Schema metadata from SchemaCollector

        Returns:
            Formatted prompt string
        """
        # Extract key metrics
        total_queries = workload_data.get("total_queries", 0)
        total_executions = workload_data.get("total_executions", 0)
        unique_patterns = workload_data.get("unique_patterns", 0)

        # Extract table information
        tables = schema_data.get("tables", [])
        table_names = []
        for t in tables:
            if isinstance(t, dict):
                table_names.append(t.get("table_name", "unknown"))
            else:
                table_names.append(str(t))

        prompt = f"""# Workload Analysis Request

## Workload Summary
- Total Queries: {total_queries:,}
- Total Executions: {total_executions:,}
- Unique Query Patterns: {unique_patterns}

## Schema Overview
- Tables: {', '.join(table_names[:10])}{'...' if len(table_names) > 10 else ''}

## Workload Details
{json.dumps(workload_data, indent=2)}

## Schema Details
{json.dumps(schema_data, indent=2)}

## Analysis Request
Please analyze this Oracle 23ai database workload and schema to identify:
1. Schema anti-patterns (LOB cliffs, expensive joins, etc.)
2. Opportunities for JSON Duality Views
3. Document vs relational storage recommendations
4. Performance optimization opportunities with tradeoff analysis
"""
        return prompt

    def format_schema_analysis_prompt(self, schema_data: Dict[str, Any]) -> str:
        """Format a prompt for schema analysis.

        Args:
            schema_data: Schema metadata from SchemaCollector

        Returns:
            Formatted prompt string
        """
        tables = schema_data.get("tables", [])
        indexes = schema_data.get("indexes", [])

        prompt = f"""# Schema Analysis Request

## Database Schema Overview
- Tables: {len(tables)}
- Indexes: {len(indexes)}

## Schema Details
{json.dumps(schema_data, indent=2)}

## Analysis Request
Please analyze this Oracle 23ai database schema for:
1. Structural issues and anti-patterns
2. Normalization/denormalization opportunities
3. Index optimization recommendations
4. JSON Duality View candidates
"""
        return prompt

    def parse_recommendations(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse recommendations from Claude's response.

        Args:
            response_text: Response text from Claude

        Returns:
            List of parsed recommendation dictionaries
        """
        recommendations = []

        # Simple parsing: look for numbered lists
        lines = response_text.split("\n")
        current_rec = None

        for line in lines:
            line = line.strip()

            # Detect numbered recommendations (e.g., "1.", "2.", etc.)
            if re.match(r"^\d+\.", line):
                if current_rec:
                    recommendations.append(current_rec)

                current_rec = {
                    "text": line,
                    "type": "recommendation",
                }
            elif current_rec and line:
                current_rec["text"] += " " + line

        if current_rec:
            recommendations.append(current_rec)

        logger.info(f"Parsed {len(recommendations)} recommendations from response")
        return recommendations

    def extract_sql(self, response_text: str) -> List[str]:
        """Extract SQL statements from response.

        Args:
            response_text: Response text from Claude

        Returns:
            List of SQL statements found in response
        """
        sql_statements = []

        # Look for SQL in code blocks (with flexible whitespace)
        sql_pattern = r"```sql\s+(.*?)\s+```"
        matches = re.findall(sql_pattern, response_text, re.DOTALL)

        for match in matches:
            sql_statements.append(match.strip())

        logger.info(f"Extracted {len(sql_statements)} SQL statements from response")
        return sql_statements
