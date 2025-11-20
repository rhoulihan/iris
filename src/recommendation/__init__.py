"""Recommendation engine module for IRIS.

This module provides schema policy recommendation capabilities including
pattern detection, cost calculation, tradeoff analysis, and LLM synthesis.
"""

from src.recommendation.pattern_detector import (
    DocumentRelationalClassifier,
    DualityViewOpportunityFinder,
    JoinDimensionAnalyzer,
    LOBCliffDetector,
)

__all__ = [
    "LOBCliffDetector",
    "JoinDimensionAnalyzer",
    "DocumentRelationalClassifier",
    "DualityViewOpportunityFinder",
]
