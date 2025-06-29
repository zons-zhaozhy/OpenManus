"""Timeout configuration for OpenManus flows and agents"""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class TimeoutConfig(BaseModel):
    """Configuration for timeouts in the system"""

    # Individual step timeout (seconds)
    step_timeout: int = Field(default=60, description="Timeout for individual steps")

    # Total execution timeout (seconds)
    total_timeout: int = Field(default=90, description="Total execution timeout")

    # Maximum iterations
    max_iterations: int = Field(default=10, description="Maximum number of iterations")

    # Retry settings
    max_retries: int = Field(default=3, description="Maximum number of retries")
    retry_delay: float = Field(
        default=1.0, description="Delay between retries in seconds"
    )

    # Progressive timeout settings
    enable_progressive_timeout: bool = Field(
        default=True, description="Enable progressive timeout strategy"
    )
    progressive_timeout_factor: float = Field(
        default=1.5, description="Factor to increase timeout progressively"
    )

    # Recovery settings
    recovery_timeout: int = Field(
        default=30, description="Timeout for recovery operations"
    )

    class Config:
        """Pydantic config"""

        validate_assignment = True

    def get_step_timeout(self, attempt: int = 1) -> int:
        """Get timeout for a step, considering progressive strategy"""
        if not self.enable_progressive_timeout or attempt <= 1:
            return self.step_timeout

        # Increase timeout progressively with each attempt
        progressive_timeout = int(
            self.step_timeout * (self.progressive_timeout_factor ** (attempt - 1))
        )

        # Cap at total timeout
        return min(progressive_timeout, self.total_timeout)


# Default configuration
default_timeout_config = TimeoutConfig()

# Per-flow timeout configurations
flow_timeout_configs: Dict[str, TimeoutConfig] = {
    "planning": TimeoutConfig(
        step_timeout=60,
        total_timeout=90,
        max_iterations=10,
    ),
    "requirements": TimeoutConfig(
        step_timeout=120,  # Requirements analysis needs more time
        total_timeout=180,
        max_iterations=15,
    ),
}


def get_timeout_config(flow_type: Optional[str] = None) -> TimeoutConfig:
    """Get timeout configuration for a specific flow type"""
    if flow_type and flow_type in flow_timeout_configs:
        return flow_timeout_configs[flow_type]
    return default_timeout_config
