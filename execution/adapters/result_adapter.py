"""
======================================================================

Module:
Execution Result Adapter

Owner:
Integration Engineer (Engineer 2 + Engineer 3 Integration)

Purpose:
Converts Engineer 3's ExecutionResult into formats consumable by
Engineer 2's Failure Analysis Agent.

This adapter bridges the gap between:
- Engineer 3: Structured ExecutionResult with ArtifactBundle
- Engineer 2: Failure Analysis Agent expects stdout/stderr strings

----------------------------------------------------------------------

BACKWARD COMPATIBILITY:

This is a new adapter that does not modify existing models.
It provides convenient extraction methods for converting
ExecutionResult into formats needed by Engineer 2.

----------------------------------------------------------------------

INTEGRATION:
Used by orchestration/loop.py reflect_node.

======================================================================
"""

from typing import Optional
from execution.models.execution_result import ExecutionResult
from execution.models.artifact_bundle import ArtifactBundle
from execution.models.artifact import Artifact
from execution.enums import ExecutionStatus


class ResultAdapter:
    """
    Adapts ExecutionResult for use by Engineer 2 components.
    
    Provides methods to extract:
    - stdout/stderr for Failure Analysis
    - Artifact information for debugging
    - Pass/fail status for LangGraph routing
    """
    
    @staticmethod
    def to_stdout_stderr(result: ExecutionResult) -> tuple[str, str]:
        """
        Convert ExecutionResult to stdout/stderr format expected by
        Failure Analysis Agent.
        
        Parameters
        ----------
        result:
            The execution result from ExecutionService.
            
        Returns
        -------
        tuple[str, str]
            (stdout, stderr) strings for failure analysis.
        """
        # Build a stdout-like summary
        stdout_lines = [
            f"Execution ID: {result.run_id}",
            f"Status: {result.status.value}",
            f"Started: {result.started_at.isoformat()}",
            f"Completed: {result.completed_at.isoformat()}",
            "",
        ]
        
        # Add artifact information
        if result.artifacts:
            stdout_lines.append("Artifacts Collected:")
            stdout_lines.extend(ResultAdapter._format_artifacts(result.artifacts))
            stdout_lines.append("")
        
        stdout = "\n".join(stdout_lines)
        
        # Build stderr from error information
        stderr_lines = []
        
        if result.error_message:
            stderr_lines.append(f"Error: {result.error_message}")
        
        if result.stack_trace:
            stderr_lines.append("")
            stderr_lines.append("Stack Trace:")
            stderr_lines.append(result.stack_trace)
        
        stderr = "\n".join(stderr_lines)
        
        return stdout, stderr
    
    @staticmethod
    def _format_artifacts(artifacts: ArtifactBundle) -> list[str]:
        """Format artifact bundle for stdout output."""
        lines = []
        
        if artifacts.screenshots:
            lines.append(f"  Screenshots: {len(artifacts.screenshots)}")
            for s in artifacts.screenshots:
                lines.append(f"    - {s.name} ({s.size_bytes} bytes)")
        
        if artifacts.traces:
            lines.append(f"  Traces: {len(artifacts.traces)}")
            for t in artifacts.traces:
                lines.append(f"    - {t.name} ({t.size_bytes} bytes)")
        
        if artifacts.videos:
            lines.append(f"  Videos: {len(artifacts.videos)}")
            for v in artifacts.videos:
                lines.append(f"    - {v.name} ({v.size_bytes} bytes)")
        
        if artifacts.logs:
            lines.append(f"  Logs: {len(artifacts.logs)}")
            for l in artifacts.logs:
                lines.append(f"    - {l.name} ({l.size_bytes} bytes)")
        
        return lines
    
    @staticmethod
    def is_passed(result: ExecutionResult) -> bool:
        """
        Check if execution passed.
        
        Parameters
        ----------
        result:
            The execution result.
            
        Returns
        -------
        bool
            True if execution passed, False otherwise.
        """
        return result.status == ExecutionStatus.PASSED
    
    @staticmethod
    def get_error_summary(result: ExecutionResult) -> Optional[str]:
        """
        Get a human-readable error summary.
        
        Parameters
        ----------
        result:
            The execution result.
            
        Returns
        -------
        str | None
            Error summary if execution failed, None otherwise.
        """
        if result.status == ExecutionStatus.PASSED:
            return None
        
        parts = [f"Status: {result.status.value}"]
        
        if result.error_message:
            parts.append(f"Error: {result.error_message}")
        
        return " | ".join(parts)
    
    @staticmethod
    def get_screenshot_paths(result: ExecutionResult) -> list[str]:
        """
        Get paths to collected screenshots.
        
        Useful for debugging and failure analysis.
        
        Parameters
        ----------
        result:
            The execution result.
            
        Returns
        -------
        list[str]
            List of screenshot file paths.
        """
        if not result.artifacts:
            return []
        
        return [str(s.path) for s in result.artifacts.screenshots]
    
    @staticmethod
    def get_trace_paths(result: ExecutionResult) -> list[str]:
        """
        Get paths to collected trace files.
        
        Parameters
        ----------
        result:
            The execution result.
            
        Returns
        -------
        list[str]
            List of trace file paths.
        """
        if not result.artifacts:
            return []
        
        return [str(t.path) for t in result.artifacts.traces]
    
    @staticmethod
    def to_failure_analysis_input(
        result: ExecutionResult,
        script_code: str
    ) -> dict:
        """
        Convert ExecutionResult to input format for Failure Analysis Agent.
        
        Parameters
        ----------
        result:
            The execution result.
            
        script_code:
            The original script code (from PlaywrightScript.code).
            
        Returns
        -------
        dict
            Dictionary with script_code, stdout, stderr for analyze_failure().
        """
        stdout, stderr = ResultAdapter.to_stdout_stderr(result)
        
        return {
            "script_code": script_code,
            "stdout": stdout,
            "stderr": stderr,
            "execution_result": result,  # Include full result for reference
        }


def adapt_result(result: ExecutionResult) -> ResultAdapter:
    """
    Convenience function to get a ResultAdapter instance.
    
    Parameters
    ----------
    result:
        The execution result to adapt.
        
    Returns
    -------
    ResultAdapter
    """
    return ResultAdapter()
