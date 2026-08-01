"""
======================================================================

Module:
Script Provider Interface

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Defines the contract for supplying executable test scripts to the
execution engine.

The execution engine must never know where the script originated.

Possible providers include:
- Engineer 2 Generated Scripts
- Manual Scripts
- Git Repository
- Database
- Cloud Storage

----------------------------------------------------------------------

Dependencies:
- ExecutionRequest

----------------------------------------------------------------------

TODO:
None

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:

ENGINEER 2

Engineer 2's output will eventually be adapted into an
ExecutionRequest before reaching the execution engine.

======================================================================
"""

from abc import ABC, abstractmethod

from execution.models.execution_request import ExecutionRequest


class ScriptProvider(ABC):
    """
    Base interface for providing executable test scripts.
    """

    @abstractmethod
    def get_request(self) -> ExecutionRequest:
        """
        Return a standardized execution request.

        Returns
        -------
        ExecutionRequest
            Valid execution request.
        """
        raise NotImplementedError