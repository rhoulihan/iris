"""Synthetic workload scenarios for IRIS integration testing."""

from tests.integration.workloads.schemas import ALL_SCENARIOS
from tests.integration.workloads.workload_generator import ALL_WORKLOADS, generate_workload

__all__ = ["ALL_SCENARIOS", "ALL_WORKLOADS", "generate_workload"]
