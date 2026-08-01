"""
======================================================================

Module:
Execution Runner Interface

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Defines the contract for all execution engines.

Every execution runner (UI, API, Mobile, etc.) must implement
this interface.

This abstraction ensures that the Execution Service remains
independent from the underlying execution technology.

----------------------------------------------------------------------

Dependencies:

- ExecutionRequest
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

This interface is internal to Engineer 3's execution module.

======================================================================
"""

from abc import ABC, abstractmethod

from execution.models.execution_request import ExecutionRequest
from execution.models.execution_result import ExecutionResult


class ExecutionRunner(ABC):
    """
    Base interface for every execution engine.

    Any execution technology must implement this interface.

    Examples
    --------
    - PlaywrightUIRunner
    - PlaywrightAPIRunner
    - SeleniumRunner (future)
    - AppiumRunner (future)
    """

    @abstractmethod
    def execute(
        self,
        request: ExecutionRequest
    ) -> ExecutionResult:
        """
        Execute a test request.

        Parameters
        ----------
        request : ExecutionRequest
            Standard execution request.

        Returns
        -------
        ExecutionResult
            Execution outcome.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_request(
        self,
        request: ExecutionRequest
    ) -> bool:
        """
        Validate the incoming execution request.

        Returns
        -------
        bool
            True if valid.
        """
        raise NotImplementedError

    @abstractmethod
    def cleanup(self) -> None:
        """
        Perform resource cleanup after execution.

        Examples
        --------
        - Close browser
        - Delete temporary files
        - Release execution resources
        """
        raise NotImplementedError