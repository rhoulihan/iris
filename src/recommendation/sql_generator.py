"""LLM-powered SQL generator for Oracle 23ai schema optimizations.

This module uses Claude to generate production-ready DDL for implementing
schema optimization recommendations.
"""

import re
from dataclasses import dataclass
from typing import Optional

from src.llm.claude_client import ClaudeClient
from src.recommendation.models import DetectedPattern, TableMetadata, WorkloadFeatures


class SQLGenerationError(Exception):
    """Raised when SQL generation fails."""

    pass


@dataclass
class GeneratedSQL:
    """Generated SQL for a schema optimization."""

    implementation_sql: str  # DDL to implement the optimization
    rollback_sql: str  # DDL to rollback the change
    testing_steps: str  # Testing approach
    llm_reasoning: str  # LLM's reasoning for this approach


class SQLGenerator:
    """Generator for Oracle 23ai DDL using Claude LLM."""

    def __init__(self, llm_client: Optional[ClaudeClient] = None):
        """Initialize SQL generator.

        Args:
            llm_client: Optional Claude client. If None, creates default client.
        """
        self.llm_client = llm_client or ClaudeClient()

    def generate_sql(
        self,
        pattern: DetectedPattern,
        table: TableMetadata,
        workload: WorkloadFeatures,
    ) -> GeneratedSQL:
        """Generate SQL for implementing a pattern optimization.

        Args:
            pattern: Detected anti-pattern
            table: Table metadata for context
            workload: Workload features for context

        Returns:
            GeneratedSQL with implementation, rollback, testing, and reasoning

        Raises:
            SQLGenerationError: If generation or parsing fails
        """
        try:
            # Build prompt based on pattern type
            prompt = self._build_prompt(pattern, table, workload)

            # Generate SQL using Claude
            response = self.llm_client.send_message(
                message=prompt,
                max_tokens=4096,
                temperature=0.7,  # Lower temperature for more consistent SQL generation
            )

            # Parse response text
            generated = self._parse_response(response["text"])

            return generated

        except TimeoutError as e:
            raise SQLGenerationError(f"LLM timeout: {e}") from e
        except Exception as e:
            raise SQLGenerationError(f"SQL generation failed: {e}") from e

    def _build_prompt(
        self,
        pattern: DetectedPattern,
        table: TableMetadata,
        workload: WorkloadFeatures,
    ) -> str:
        """Build Claude prompt for SQL generation.

        Args:
            pattern: Detected pattern
            table: Table metadata
            workload: Workload features

        Returns:
            Prompt string for Claude
        """
        # Pattern-specific prompts
        if pattern.pattern_type == "LOB_CLIFF":
            return self._build_lob_prompt(pattern, table, workload)
        elif pattern.pattern_type == "EXPENSIVE_JOIN":
            return self._build_join_prompt(pattern, table, workload)
        elif pattern.pattern_type == "DOCUMENT_CANDIDATE":
            return self._build_document_prompt(pattern, table, workload)
        elif pattern.pattern_type == "DUALITY_VIEW_OPPORTUNITY":
            return self._build_duality_view_prompt(pattern, table, workload)
        else:
            return self._build_generic_prompt(pattern, table, workload)

    def _build_lob_prompt(
        self,
        pattern: DetectedPattern,
        table: TableMetadata,
        workload: WorkloadFeatures,
    ) -> str:
        """Build prompt for LOB cliff optimization."""
        affected_column = pattern.affected_objects[0].split(".")[-1]

        return f"""You are an Oracle database expert. Generate production-ready DDL for optimizing a LOB cliff anti-pattern.

CONTEXT:
- Table: {table.name}
- Schema: {table.schema}
- Rows: {table.num_rows:,}
- Problem: LOB column "{affected_column}" causing LOB chaining and write amplification
- Update frequency: {pattern.metrics.get('update_frequency', 'N/A')} per day
- Document size: {pattern.metrics.get('document_size_kb', 'N/A')} KB

REQUIREMENT:
Generate Oracle DDL to split the LOB column into a separate table to eliminate LOB chaining on updates to other columns.

RESPONSE FORMAT:
IMPLEMENTATION SQL:
```sql
-- Your implementation DDL here
```

ROLLBACK SQL:
```sql
-- Your rollback DDL here
```

TESTING STEPS:
1. Step one
2. Step two
etc.

REASONING:
Brief explanation of why this approach works and expected benefits.

IMPORTANT:
- Use Oracle 23ai syntax
- Include foreign key constraints
- Include data migration SQL
- Make rollback safe (no data loss)
- Be specific about table/column names
"""

    def _build_join_prompt(
        self,
        pattern: DetectedPattern,
        table: TableMetadata,
        workload: WorkloadFeatures,
    ) -> str:
        """Build prompt for join denormalization."""
        tables = pattern.affected_objects
        join_frequency = pattern.metrics.get("join_frequency", "N/A")

        return f"""You are an Oracle database expert. Generate production-ready DDL for denormalization optimization.

CONTEXT:
- Tables: {', '.join(tables)}
- Join frequency: {join_frequency} per day
- Problem: Expensive joins causing performance issues

REQUIREMENT:
Generate Oracle DDL to denormalize frequently joined data. Include:
1. ALTER TABLE to add denormalized columns
2. UPDATE to populate existing data
3. Trigger or other mechanism to maintain consistency

RESPONSE FORMAT:
IMPLEMENTATION SQL:
```sql
-- Your implementation DDL here
```

ROLLBACK SQL:
```sql
-- Your rollback DDL here
```

TESTING STEPS:
1. Step one
2. Step two
etc.

REASONING:
Brief explanation of tradeoffs and expected benefits.

IMPORTANT:
- Use Oracle 23ai syntax
- Maintain data consistency
- Consider update overhead from triggers
- Make rollback safe
"""

    def _build_document_prompt(
        self,
        pattern: DetectedPattern,
        table: TableMetadata,
        workload: WorkloadFeatures,
    ) -> str:
        """Build prompt for document storage optimization."""
        table_name = pattern.affected_objects[0]

        return f"""You are an Oracle database expert. Generate production-ready DDL for converting relational to JSON.

CONTEXT:
- Table: {table_name}
- SELECT * percentage: {pattern.metrics.get('select_star_pct', 0.0) * 100:.0f}%
- Problem: Relational schema with object-like access patterns

REQUIREMENT:
Generate Oracle DDL to convert this relational table to JSON storage format. The solution should:
1. Create new JSON collection table
2. Migrate data using JSON_OBJECT
3. Preserve all existing data

RESPONSE FORMAT:
IMPLEMENTATION SQL:
```sql
-- Your implementation DDL here
```

ROLLBACK SQL:
```sql
-- Your rollback DDL here
```

TESTING STEPS:
1. Step one
2. Step two
etc.

REASONING:
Brief explanation of benefits and schema flexibility gains.

IMPORTANT:
- Use Oracle 23ai JSON features
- Use JSON_OBJECT for migration
- Make migration reversible
- Validate JSON structure
"""

    def _build_duality_view_prompt(
        self,
        pattern: DetectedPattern,
        table: TableMetadata,
        workload: WorkloadFeatures,
    ) -> str:
        """Build prompt for JSON Duality View creation."""
        table_name = pattern.affected_objects[0]
        oltp_pct = pattern.metrics.get("oltp_pct", 0.0) * 100
        analytics_pct = pattern.metrics.get("analytics_pct", 0.0) * 100

        return f"""You are an Oracle 23ai database expert. Generate production-ready DDL for JSON Duality View.

CONTEXT:
- Table: {table_name}
- OLTP workload: {oltp_pct:.0f}% (document-style access)
- Analytics workload: {analytics_pct:.0f}% (relational queries)
- Problem: Mixed access patterns requiring both document and relational views

REQUIREMENT:
Generate Oracle 23ai JSON Duality View DDL that:
1. Provides JSON view for OLTP applications
2. Maintains relational access for analytics
3. Automatically syncs changes bidirectionally
4. Uses CREATE JSON RELATIONAL DUALITY VIEW syntax

RESPONSE FORMAT:
IMPLEMENTATION SQL:
```sql
-- Your Duality View DDL here
```

ROLLBACK SQL:
```sql
-- Your rollback DDL here
```

TESTING STEPS:
1. Step one
2. Step two
etc.

REASONING:
Brief explanation of why Duality View is optimal for this workload mix.

IMPORTANT:
- Use Oracle 23ai JSON RELATIONAL DUALITY VIEW syntax
- Include proper JSON structure
- Make it production-ready
- Include any necessary grants
"""

    def _build_generic_prompt(
        self,
        pattern: DetectedPattern,
        table: TableMetadata,
        workload: WorkloadFeatures,
    ) -> str:
        """Build generic prompt for unknown pattern types."""
        return f"""You are an Oracle database expert. Generate DDL for schema optimization.

CONTEXT:
- Pattern: {pattern.pattern_type}
- Affected objects: {', '.join(pattern.affected_objects)}
- Description: {pattern.description}

REQUIREMENT:
Generate appropriate Oracle DDL for this optimization.

RESPONSE FORMAT:
IMPLEMENTATION SQL:
```sql
-- Implementation DDL
```

ROLLBACK SQL:
```sql
-- Rollback DDL
```

TESTING STEPS:
Testing approach

REASONING:
Your reasoning
"""

    def _parse_response(self, response: str) -> GeneratedSQL:
        """Parse Claude's response to extract SQL components.

        Args:
            response: Raw response from Claude

        Returns:
            GeneratedSQL with extracted components

        Raises:
            SQLGenerationError: If response cannot be parsed
        """
        try:
            # Extract sections
            implementation_sql = self._extract_section(
                response, "IMPLEMENTATION SQL:", "ROLLBACK SQL:"
            )
            rollback_sql = self._extract_section(response, "ROLLBACK SQL:", "TESTING STEPS:")
            testing_steps = self._extract_section(response, "TESTING STEPS:", "REASONING:")
            reasoning = self._extract_section(response, "REASONING:", None)

            # Clean SQL (remove code block markers)
            implementation_sql = self._clean_sql(implementation_sql)
            rollback_sql = self._clean_sql(rollback_sql)

            # Validate we got something
            if not implementation_sql or not rollback_sql:
                raise SQLGenerationError("Invalid response: missing implementation or rollback SQL")

            return GeneratedSQL(
                implementation_sql=implementation_sql.strip(),
                rollback_sql=rollback_sql.strip(),
                testing_steps=testing_steps.strip(),
                llm_reasoning=reasoning.strip(),
            )

        except Exception as e:
            raise SQLGenerationError(f"Failed to parse LLM response: {e}") from e

    def _extract_section(self, text: str, start_marker: str, end_marker: Optional[str]) -> str:
        """Extract a section between two markers.

        Args:
            text: Full text
            start_marker: Section start marker
            end_marker: Section end marker (None for end of text)

        Returns:
            Extracted section text
        """
        start_idx = text.find(start_marker)
        if start_idx == -1:
            return ""

        start_idx += len(start_marker)

        if end_marker:
            end_idx = text.find(end_marker, start_idx)
            if end_idx == -1:
                return text[start_idx:].strip()
            return text[start_idx:end_idx].strip()
        else:
            return text[start_idx:].strip()

    def _clean_sql(self, sql: str) -> str:
        """Clean SQL by removing markdown code blocks.

        Args:
            sql: SQL with possible markdown

        Returns:
            Clean SQL
        """
        # Remove ```sql and ``` markers
        sql = re.sub(r"```sql\s*", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"```\s*", "", sql)
        return sql.strip()
