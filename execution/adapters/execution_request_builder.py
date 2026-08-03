"""
======================================================================

Module:
Execution Request Builder

Owner:
Integration Engineer (Engineer 2 + Engineer 3 Integration)

Purpose:
Builds ExecutionRequest objects from Engineer 2's PlaywrightScript
metadata.

This adapter handles the mapping between:
- Engineer 2: TestLevel enum (UI, API_CONTRACT, API_BACKEND)
- Engineer 3: ExecutionType enum (UI, API, HYBRID)

----------------------------------------------------------------------

BACKWARD COMPATIBILITY:

This is a new adapter that does not modify existing models.
It provides a convenient factory for creating ExecutionRequest
objects from Engineer 2 outputs.

----------------------------------------------------------------------

INTEGRATION:
Used by orchestration/loop.py execute_node.

======================================================================
"""

import uuid
from datetime import datetime
from typing import Optional

from models.playwright_script import PlaywrightScript
from models.test_scenario import TestScenario, TestLevel
from execution.models.execution_request import ExecutionRequest
from execution.enums import ExecutionType, BrowserType


# Mapping from Engineer 2 TestLevel to Engineer 3 ExecutionType
TEST_LEVEL_TO_EXECUTION_TYPE = {
    TestLevel.UI: ExecutionType.UI,
    TestLevel.API_CONTRACT: ExecutionType.API,
    TestLevel.API_BACKEND: ExecutionType.API,
}


class ExecutionRequestBuilder:
    """
    Builds ExecutionRequest objects from Engineer 2 metadata.
    
    This builder encapsulates the logic for:
    - Generating unique run IDs
    - Mapping test levels to execution types
    - Setting sensible defaults for execution configuration
    """
    
    def __init__(
        self,
        default_browser: BrowserType = BrowserType.CHROMIUM,
        default_headless: bool = True,
        default_timeout: int = 300,
        default_retries: int = 0
    ):
        """
        Initialize the request builder with defaults.
        
        Parameters
        ----------
        default_browser:
            Default browser engine to use.
            
        default_headless:
            Default headless mode setting.
            
        default_timeout:
            Default execution timeout in seconds.
            
        default_retries:
            Default number of retry attempts.
        """
        self.default_browser = default_browser
        self.default_headless = default_headless
        self.default_timeout = default_timeout
        self.default_retries = default_retries
    
    def build(
        self,
        script: PlaywrightScript,
        scenario: Optional[TestScenario] = None,
        run_id: Optional[str] = None,
        browser_type: Optional[BrowserType] = None,
        headless: Optional[bool] = None,
        timeout: Optional[int] = None,
        metadata: Optional[dict] = None,
        tags: Optional[list[str]] = None
    ) -> ExecutionRequest:
        """
        Build an ExecutionRequest from a PlaywrightScript.
        
        Parameters
        ----------
        script:
            The generated Playwright script.
            
        scenario:
            Optional source TestScenario for additional metadata.
            
        run_id:
            Unique execution identifier. If not provided, one is generated.
            
        browser_type:
            Browser engine to use. Defaults to Chromium.
            
        headless:
            Run in headless mode. Defaults to True.
            
        timeout:
            Execution timeout in seconds.
            
        metadata:
            Additional execution metadata.
            
        tags:
            Execution tags.
            
        Returns
        -------
        ExecutionRequest
            A configured execution request ready for ExecutionService.
        """
        # Generate run_id if not provided
        if run_id is None:
            run_id = self._generate_run_id(script.scenario_id)
        
        # Determine execution type from script
        execution_type = TEST_LEVEL_TO_EXECUTION_TYPE.get(
            script.test_level,
            ExecutionType.UI  # Default to UI if unknown
        )
        
        # Build metadata
        combined_metadata = {
            "scenario_id": script.scenario_id,
            "script_file": script.file_name,
            "test_level": script.test_level.value,
            "created_at": script.created_at.isoformat() if script.created_at else None,
        }
        
        if scenario:
            combined_metadata.update({
                "scenario_title": scenario.title,
                "scenario_category": scenario.category.value,
                "scenario_subcategory": scenario.subcategory.value,
                "scenario_priority": scenario.priority.value,
            })
        
        if metadata:
            combined_metadata.update(metadata)
        
        # Build tags
        combined_tags = []
        if scenario:
            combined_tags.extend([
                scenario.category.value,
                scenario.subcategory.value,
                scenario.priority.value,
            ])
        if tags:
            combined_tags.extend(tags)
        
        return ExecutionRequest(
            run_id=run_id,
            execution_type=execution_type,
            browser_type=browser_type or self.default_browser,
            headless=headless if headless is not None else self.default_headless,
            timeout=timeout or self.default_timeout,
            retries=self.default_retries,
            metadata=combined_metadata,
            tags=combined_tags,
        )
    
    def _generate_run_id(self, scenario_id: str) -> str:
        """
        Generate a unique run ID.
        
        Format: {scenario_id}_{timestamp}_{uuid}
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{scenario_id}_{timestamp}_{unique_id}"


def build_execution_request(
    script: PlaywrightScript,
    scenario: Optional[TestScenario] = None,
    **kwargs
) -> ExecutionRequest:
    """
    Convenience function to build an ExecutionRequest.
    
    Parameters
    ----------
    script:
        The generated Playwright script.
        
    scenario:
        Optional source TestScenario.
        
    **kwargs:
        Additional parameters passed to ExecutionRequestBuilder.build().
        
    Returns
    -------
    ExecutionRequest
    """
    builder = ExecutionRequestBuilder()
    return builder.build(script=script, scenario=scenario, **kwargs)
