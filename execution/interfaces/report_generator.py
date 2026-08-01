"""
======================================================================

Module:
Report Generator Interface

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Defines the contract for generating execution reports.

Implementations may generate reports in HTML, PDF, JSON,
or any future format.

----------------------------------------------------------------------

Dependencies:
- ExecutionResult

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

from execution.models.execution_result import ExecutionResult


class ReportGenerator(ABC):
    """
    Base interface for execution report generation.
    """

    @abstractmethod
    def generate(
        self,
        result: ExecutionResult
    ) -> str:
        """
        Generate a report from an execution result.

        Parameters
        ----------
        result : ExecutionResult
            Completed execution result.

        Returns
        -------
        str
            Path to the generated report.
        """
        raise NotImplementedError