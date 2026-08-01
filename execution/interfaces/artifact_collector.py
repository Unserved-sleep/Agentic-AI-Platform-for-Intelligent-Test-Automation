"""
======================================================================

Module:
Artifact Collector Interface

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Defines the contract for collecting execution artifacts.

Artifacts include screenshots, traces, videos, logs,
reports, and any additional execution outputs.

----------------------------------------------------------------------

Dependencies:
- ArtifactBundle

----------------------------------------------------------------------

TODO:
None

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
None

======================================================================
"""

from abc import ABC, abstractmethod

from execution.models.artifact_bundle import ArtifactBundle


class ArtifactCollector(ABC):
    """
    Base interface for collecting execution artifacts.
    """

    @abstractmethod
    def collect(self) -> ArtifactBundle:
        """
        Collect all execution artifacts.

        Returns
        -------
        ArtifactBundle
            Collection of execution artifacts.
        """
        raise NotImplementedError

    @abstractmethod
    def cleanup(self) -> None:
        """
        Remove temporary execution artifacts.

        This should NOT delete permanent reports or logs.
        """
        raise NotImplementedError