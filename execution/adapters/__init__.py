"""
======================================================================

Module:
Execution Adapters

Owner:
Integration Engineer (Engineer 2 + Engineer 3 Integration)

Purpose:
Provides adapters for integrating Engineer 2 (AI Test Generation)
with Engineer 3 (Execution Framework).

Adapters:
- ScriptAdapter: Converts PlaywrightScript to callable
- ExecutionRequestBuilder: Creates ExecutionRequest from metadata
- ResultAdapter: Converts ExecutionResult for Failure Analysis

======================================================================
"""

from execution.adapters.script_adapter import (
    ScriptAdapter,
    create_test_callable,
)
from execution.adapters.execution_request_builder import (
    ExecutionRequestBuilder,
    build_execution_request,
)
from execution.adapters.result_adapter import (
    ResultAdapter,
    adapt_result,
)

__all__ = [
    "ScriptAdapter",
    "create_test_callable",
    "ExecutionRequestBuilder",
    "build_execution_request",
    "ResultAdapter",
    "adapt_result",
]
