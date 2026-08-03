"""
======================================================================

Module:
Artifact Bundle Model

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Represents all artifacts generated during a single execution.

Bundles screenshots, traces, logs, videos and reports into
one object that can be passed throughout the execution
pipeline.

----------------------------------------------------------------------

TODO:
Support HAR files and performance metrics.

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
None

======================================================================
"""

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from execution.models.artifact import Artifact

if TYPE_CHECKING:
    # Avoid circular imports at module-load time; only used in type hints.
    from execution.collectors.console_log_collector import ConsoleLogEntry
    from execution.collectors.network_collector import NetworkEventBundle


class ArtifactBundle(BaseModel):
    """
    Collection of artifacts produced by one execution.

    New fields added without breaking existing usage:
    - console_logs   — List of ConsoleLogEntry objects
    - network_events — NetworkEventBundle (requests / responses / failures)
    """

    model_config = ConfigDict(
        validate_assignment=True,
        # Relax to 'ignore' so older callers that do not pass the new
        # fields do not receive validation errors.
        extra="ignore",
        arbitrary_types_allowed=True,
    )

    screenshots: list[Artifact] = Field(
        default_factory=list,
        description="Execution screenshots.",
    )

    traces: list[Artifact] = Field(
        default_factory=list,
        description="Execution trace files.",
    )

    videos: list[Artifact] = Field(
        default_factory=list,
        description="Execution recordings.",
    )

    logs: list[Artifact] = Field(
        default_factory=list,
        description="Execution log artifact files.",
    )

    reports: list[Artifact] = Field(
        default_factory=list,
        description="Generated execution reports.",
    )

    # ------------------------------------------------------------------
    # New fields — Phase 5 / Phase 6
    # ------------------------------------------------------------------

    console_logs: list[Any] = Field(
        default_factory=list,
        description=(
            "Browser console log entries captured by "
            "ConsoleLogCollector. Each item is a ConsoleLogEntry."
        ),
    )

    network_events: Any = Field(
        default=None,
        description=(
            "Network activity captured by NetworkCollector. "
            "Value is a NetworkEventBundle or None when not collected."
        ),
    )
