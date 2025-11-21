"""Recommendation validator for simulation workloads.

Validates that pipeline recommendations match expected outcomes for each workload.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from src.recommendation.recommendation_engine import SchemaRecommendation

logger = logging.getLogger(__name__)


@dataclass
class ExpectedRecommendation:
    """Expected recommendation for a workload."""

    workload_name: str
    pattern_type: str
    min_confidence: float
    expected_priority: List[str]  # List of acceptable priorities
    recommendation_keywords: List[str]  # Keywords that should appear in recommendation text
    sql_keywords: Optional[List[str]] = None  # Keywords expected in generated SQL


class RecommendationValidator:
    """Validates pipeline recommendations against expected outcomes."""

    # Expected outcomes for each workload (from SIMULATION_WORKLOADS.md)
    EXPECTED_RECOMMENDATIONS = {
        "workload1": ExpectedRecommendation(
            workload_name="E-Commerce User Profiles",
            pattern_type="DOCUMENT_RELATIONAL",
            min_confidence=0.7,
            expected_priority=["HIGH"],
            recommendation_keywords=[
                "document",
                "json",
                "read-heavy",
                "join",
            ],
            sql_keywords=[
                "JSON",
                "CREATE TABLE",
                "customer",
            ],
        ),
        "workload2": ExpectedRecommendation(
            workload_name="Real-Time Inventory",
            pattern_type="DOCUMENT_RELATIONAL",
            min_confidence=0.7,
            expected_priority=["HIGH"],
            recommendation_keywords=[
                "relational",
                "normalize",
                "write-heavy",
                "update",
            ],
            sql_keywords=[
                "CREATE TABLE",
                "inventory",
                "warehouse",
            ],
        ),
        "workload3": ExpectedRecommendation(
            workload_name="Sales Order System",
            pattern_type="DUALITY_VIEW_OPPORTUNITY",
            min_confidence=0.7,
            expected_priority=["HIGH", "MEDIUM"],
            recommendation_keywords=[
                "duality",
                "view",
                "hybrid",
                "oltp",
                "analytics",
            ],
            sql_keywords=[
                "DUALITY VIEW",
                "JSON RELATIONAL",
                "order",
            ],
        ),
    }

    def __init__(self, workload_id: str):
        """Initialize validator for a specific workload.

        Args:
            workload_id: Workload identifier (workload1, workload2, workload3)
        """
        if workload_id not in self.EXPECTED_RECOMMENDATIONS:
            raise ValueError(f"Unknown workload: {workload_id}")

        self.workload_id = workload_id
        self.expected = self.EXPECTED_RECOMMENDATIONS[workload_id]

    def validate(self, recommendations: List[SchemaRecommendation]) -> dict:
        """Validate recommendations against expected outcomes.

        Args:
            recommendations: List of recommendations from pipeline

        Returns:
            Dictionary with validation results:
            {
                "passed": bool,
                "recommendations_count": int,
                "validations": {
                    "has_recommendations": bool,
                    "pattern_type_match": bool,
                    "confidence_threshold": bool,
                    "priority_acceptable": bool,
                    "keywords_found": bool,
                    "sql_keywords_found": bool (if SQL provided)
                },
                "errors": List[str],
                "warnings": List[str]
            }
        """
        results = {
            "passed": False,
            "recommendations_count": len(recommendations),
            "validations": {},
            "errors": [],
            "warnings": [],
        }

        # Validation 1: Has recommendations
        has_recommendations = len(recommendations) > 0
        results["validations"]["has_recommendations"] = has_recommendations

        if not has_recommendations:
            results["errors"].append("No recommendations generated")
            return results

        # Find highest priority recommendation for this workload
        primary_rec = self._find_primary_recommendation(recommendations)

        if not primary_rec:
            results["errors"].append(
                f"No recommendation found for pattern type {self.expected.pattern_type}"
            )
            return results

        # Validation 2: Pattern type match
        pattern_match = primary_rec.pattern_type == self.expected.pattern_type
        results["validations"]["pattern_type_match"] = pattern_match

        if not pattern_match:
            results["errors"].append(
                f"Pattern type mismatch: expected {self.expected.pattern_type}, "
                f"got {primary_rec.pattern_type}"
            )

        # Validation 3: Confidence threshold
        confidence_ok = primary_rec.confidence >= self.expected.min_confidence
        results["validations"]["confidence_threshold"] = confidence_ok

        if not confidence_ok:
            results["warnings"].append(
                f"Confidence below threshold: {primary_rec.confidence:.2f} < "
                f"{self.expected.min_confidence:.2f}"
            )

        # Validation 4: Priority acceptable
        priority_ok = primary_rec.priority in self.expected.expected_priority
        results["validations"]["priority_acceptable"] = priority_ok

        if not priority_ok:
            results["warnings"].append(
                f"Priority unexpected: {primary_rec.priority} "
                f"(expected one of {self.expected.expected_priority})"
            )

        # Validation 5: Recommendation text keywords
        rec_text = (
            primary_rec.recommendation_text.lower() if primary_rec.recommendation_text else ""
        )
        keywords_found = all(
            keyword.lower() in rec_text for keyword in self.expected.recommendation_keywords
        )
        results["validations"]["keywords_found"] = keywords_found

        if not keywords_found:
            missing = [
                k for k in self.expected.recommendation_keywords if k.lower() not in rec_text
            ]
            results["warnings"].append(f"Missing keywords in recommendation: {missing}")

        # Validation 6: SQL keywords (if SQL provided and expected)
        if primary_rec.implementation_sql and self.expected.sql_keywords:
            sql_text = primary_rec.implementation_sql.lower()
            sql_keywords_ok = all(
                keyword.lower() in sql_text for keyword in self.expected.sql_keywords
            )
            results["validations"]["sql_keywords_found"] = sql_keywords_ok

            if not sql_keywords_ok:
                missing = [k for k in self.expected.sql_keywords if k.lower() not in sql_text]
                results["warnings"].append(f"Missing SQL keywords: {missing}")

        # Overall pass/fail
        critical_validations = [
            results["validations"].get("has_recommendations", False),
            results["validations"].get("pattern_type_match", False),
            results["validations"].get("confidence_threshold", False),
        ]

        results["passed"] = all(critical_validations) and len(results["errors"]) == 0

        return results

    def _find_primary_recommendation(
        self, recommendations: List[SchemaRecommendation]
    ) -> Optional[SchemaRecommendation]:
        """Find the primary recommendation for this workload.

        Args:
            recommendations: List of recommendations

        Returns:
            Primary recommendation or None
        """
        # Filter by pattern type
        matching = [
            rec for rec in recommendations if rec.pattern_type == self.expected.pattern_type
        ]

        if not matching:
            return None

        # Return highest priority
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        matching.sort(key=lambda r: priority_order.get(r.priority, 999))

        return matching[0]

    def print_results(self, results: dict):
        """Print validation results in a readable format.

        Args:
            results: Results from validate()
        """
        logger.info("\n" + "=" * 70)
        logger.info(f"Validation Results: {self.expected.workload_name}")
        logger.info("=" * 70)

        logger.info(f"\nRecommendations Generated: {results['recommendations_count']}")
        logger.info(f"Overall Result: {'✅ PASSED' if results['passed'] else '❌ FAILED'}")

        logger.info("\nValidations:")
        for check, passed in results["validations"].items():
            status = "✅" if passed else "❌"
            logger.info(f"  {status} {check}")

        if results["errors"]:
            logger.error("\nErrors:")
            for error in results["errors"]:
                logger.error(f"  ❌ {error}")

        if results["warnings"]:
            logger.warning("\nWarnings:")
            for warning in results["warnings"]:
                logger.warning(f"  ⚠️  {warning}")

        logger.info("\n" + "=" * 70)
