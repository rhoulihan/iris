"""Cost model definitions for IRIS recommendation engine.

This module defines data structures for cost estimation and ROI calculation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.recommendation.models import DetectedPattern, TableMetadata, WorkloadFeatures


@dataclass
class CostConfiguration:
    """Configurable cost parameters for different environments.

    All costs are in USD. Defaults are based on typical cloud database pricing.
    """

    # I/O costs ($/KB)
    cost_per_kb_read: float = 0.0001  # $0.0001 per KB read
    cost_per_kb_write: float = 0.0002  # $0.0002 per KB write

    # CPU costs
    cpu_cost_per_row: float = 0.000001  # $0.000001 per row processed

    # Storage costs ($/GB/day)
    cost_per_gb_per_day: float = 0.03  # $0.03 per GB per day

    # Network costs
    network_cost_per_kb: float = 0.00005  # $0.00005 per KB transferred

    # Implementation costs (labor)
    hourly_rate: float = 150.0  # $150/hour developer rate

    # Time estimates (hours) - used to calculate implementation cost
    schema_change_hours: float = 8.0  # 1 day for schema change
    migration_hours: float = 16.0  # 2 days for data migration
    app_change_hours: float = 40.0  # 5 days for app changes
    testing_hours: float = 16.0  # 2 days for testing

    # Risk factors
    risk_multiplier: float = 1.2  # 20% buffer for risks

    def __post_init__(self):
        """Validate cost configuration."""
        if self.cost_per_kb_read < 0:
            raise ValueError("cost_per_kb_read must be non-negative")
        if self.cost_per_kb_write < 0:
            raise ValueError("cost_per_kb_write must be non-negative")
        if self.hourly_rate <= 0:
            raise ValueError("hourly_rate must be positive")


@dataclass
class CostBreakdown:
    """Detailed breakdown of cost components."""

    # I/O costs
    read_cost: float = 0.0
    write_cost: float = 0.0

    # CPU costs
    cpu_cost: float = 0.0

    # Storage costs
    storage_cost: float = 0.0

    # Network costs
    network_cost: float = 0.0

    # Other pattern-specific costs
    other_costs: Dict[str, float] = field(default_factory=dict)

    @property
    def total_cost(self) -> float:
        """Calculate total cost from all components."""
        return (
            self.read_cost
            + self.write_cost
            + self.cpu_cost
            + self.storage_cost
            + self.network_cost
            + sum(self.other_costs.values())
        )


@dataclass
class CostEstimate:
    """Cost estimate for a detected pattern.

    Includes current cost, optimized cost, implementation cost, and ROI metrics.
    """

    pattern_id: str
    pattern_type: str
    affected_objects: List[str]

    # Cost breakdown
    current_cost_per_day: float  # Cost with anti-pattern ($/day)
    optimized_cost_per_day: float  # Cost after optimization ($/day)
    implementation_cost: float  # One-time implementation cost ($)

    # Detailed breakdowns
    current_cost_breakdown: Optional[CostBreakdown] = None
    optimized_cost_breakdown: Optional[CostBreakdown] = None

    # Savings and ROI (calculated properties, can be overridden)
    annual_savings: Optional[float] = None
    net_benefit: Optional[float] = None
    roi_percentage: Optional[float] = None
    payback_period_days: Optional[int] = None

    # Priority
    priority_score: Optional[float] = None  # 0-100 composite score
    priority_tier: Optional[str] = None  # HIGH, MEDIUM, LOW

    # Metadata
    assumptions: List[str] = field(default_factory=list)
    confidence: float = 0.7  # Confidence in estimate (0-1)

    def __post_init__(self):
        """Calculate derived fields if not provided."""
        # Calculate savings
        daily_savings = self.current_cost_per_day - self.optimized_cost_per_day

        if self.annual_savings is None:
            self.annual_savings = daily_savings * 365

        if self.net_benefit is None:
            self.net_benefit = self.annual_savings - self.implementation_cost

        if self.roi_percentage is None and self.implementation_cost > 0:
            self.roi_percentage = (self.net_benefit / self.implementation_cost) * 100

        if self.payback_period_days is None and daily_savings > 0:
            self.payback_period_days = int(self.implementation_cost / daily_savings)

    @property
    def is_cost_effective(self) -> bool:
        """Check if optimization is cost-effective (positive ROI)."""
        return self.net_benefit > 0 if self.net_benefit else False

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "affected_objects": self.affected_objects,
            "costs": {
                "current_per_day": round(self.current_cost_per_day, 2),
                "optimized_per_day": round(self.optimized_cost_per_day, 2),
                "implementation": round(self.implementation_cost, 2),
            },
            "savings": {
                "annual": round(self.annual_savings, 2) if self.annual_savings else 0,
                "net_benefit": round(self.net_benefit, 2) if self.net_benefit else 0,
            },
            "roi": {
                "percentage": round(self.roi_percentage, 2) if self.roi_percentage else 0,
                "payback_days": self.payback_period_days or 0,
            },
            "priority": {
                "score": round(self.priority_score, 2) if self.priority_score else 0,
                "tier": self.priority_tier or "UNKNOWN",
            },
            "confidence": round(self.confidence, 2),
            "assumptions": self.assumptions,
        }


@dataclass
class CostCalculationInput:
    """Input data for cost calculation."""

    pattern: DetectedPattern  # Detected pattern from Pattern Detector
    table_metadata: TableMetadata  # Schema information
    workload: WorkloadFeatures  # Query patterns
    cost_config: CostConfiguration = field(default_factory=CostConfiguration)

    def __post_init__(self):
        """Validate input."""
        if not self.pattern:
            raise ValueError("pattern is required")
        if not self.table_metadata:
            raise ValueError("table_metadata is required")
        if not self.workload:
            raise ValueError("workload is required")


@dataclass
class ImplementationCostEstimate:
    """Estimate of implementation effort and cost."""

    schema_changes_hours: float = 0.0
    migration_hours: float = 0.0
    app_changes_hours: float = 0.0
    testing_hours: float = 0.0

    risk_factor: float = 1.0  # Multiplier for risk (1.0 = no risk, 1.5 = 50% buffer)

    @property
    def total_hours(self) -> float:
        """Calculate total hours before risk adjustment."""
        return (
            self.schema_changes_hours
            + self.migration_hours
            + self.app_changes_hours
            + self.testing_hours
        )

    def calculate_cost(self, hourly_rate: float) -> float:
        """Calculate total implementation cost including risk buffer."""
        return self.total_hours * hourly_rate * self.risk_factor


# Default configuration instance
DEFAULT_COST_CONFIG = CostConfiguration()
