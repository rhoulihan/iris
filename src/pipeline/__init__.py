"""Pipeline orchestration for IRIS recommendation engine.

This module provides the PipelineOrchestrator class which coordinates the end-to-end
workflow from AWR data collection to recommendation generation.
"""

from src.pipeline.orchestrator import PipelineConfig, PipelineOrchestrator, PipelineResult

__all__ = ["PipelineOrchestrator", "PipelineConfig", "PipelineResult"]
