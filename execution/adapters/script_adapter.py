"""
======================================================================

Module:
Script Execution Adapter

Owner:
Integration Engineer (Engineer 2 + Engineer 3 Integration)

Purpose:
Converts Engineer 2's generated Playwright scripts (string code)
into callable objects that can be executed by Engineer 3's
ExecutionService.

This adapter bridges the gap between:
- Engineer 2: Generates Python code as strings
- Engineer 3: Expects Python callables accepting Page objects

----------------------------------------------------------------------

BACKWARD COMPATIBILITY:

The existing callable-based ExecutionService API remains unchanged.
This adapter provides a NEW way to execute script files without
breaking existing functionality.

----------------------------------------------------------------------

INTEGRATION:
Used by orchestration/loop.py execute_node.

======================================================================
"""

import importlib.util
import sys
import tempfile
import os
from pathlib import Path
from typing import Callable, Optional
from playwright.sync_api import Page

from models.playwright_script import PlaywrightScript


class ScriptAdapter:
    """
    Converts PlaywrightScript (string code) into a callable
    that can be executed by ExecutionService.
    
    Strategy:
    1. Write script to temporary file
    2. Dynamically import the module
    3. Extract test function(s)
    4. Return a callable wrapper
    """
    
    def __init__(self, script_output_dir: str = "execution/generated_tests"):
        """
        Initialize the script adapter.
        
        Parameters
        ----------
        script_output_dir:
            Directory where generated scripts are stored.
        """
        self.script_output_dir = Path(script_output_dir)
        self.script_output_dir.mkdir(parents=True, exist_ok=True)
    
    def to_callable(
        self,
        script: PlaywrightScript,
        save_to_disk: bool = True
    ) -> Callable[[Page], None]:
        """
        Convert a PlaywrightScript into a callable that accepts a Page.
        
        Parameters
        ----------
        script:
            The generated Playwright script (contains code string).
            
        save_to_disk:
            If True, saves the script to disk before importing.
            If False, uses a temporary file.
            
        Returns
        -------
        Callable[[Page], None]
            A function that accepts a Playwright Page and executes the test.
        """
        # Determine file path
        if save_to_disk:
            script_path = self.script_output_dir / script.file_name
            # Save the script
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script.code)
        else:
            # Create temporary file
            script_path = Path(tempfile.mktemp(suffix='.py'))
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script.code)
        
        # Dynamically import the module
        module_name = script.file_name.replace('.py', '')
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {script_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            # Clean up on import error
            if not save_to_disk and script_path.exists():
                script_path.unlink()
            raise RuntimeError(f"Failed to load generated script: {e}") from e
        
        # Extract test functions
        test_functions = self._extract_test_functions(module)
        
        if not test_functions:
            raise ValueError(f"No test functions found in {script.file_name}")
        
        # Create a wrapper that runs all test functions
        return self._create_wrapper(test_functions, script_path, save_to_disk)
    
    def _extract_test_functions(self, module) -> list[Callable]:
        """
        Extract all test functions from a module.
        
        Test functions are those that:
        - Start with 'test_'
        - Are callable
        """
        test_functions = []
        
        for name in dir(module):
            if name.startswith('test_'):
                obj = getattr(module, name)
                if callable(obj):
                    test_functions.append(obj)
        
        return test_functions
    
    def _create_wrapper(
        self,
        test_functions: list[Callable],
        script_path: Path,
        cleanup: bool
    ) -> Callable[[Page], None]:
        """
        Create a wrapper function that executes all test functions.
        
        The wrapper accepts a Page object and runs each test function
        in sequence.
        """
        def wrapper(page: Page) -> None:
            """
            Execute all test functions with the given Page.
            
            Parameters
            ----------
            page:
                Playwright Page object provided by ExecutionService.
            """
            errors = []
            
            for test_func in test_functions:
                try:
                    # Check if the test function expects a 'page' or 'request' parameter
                    # Most generated scripts use pytest fixtures, so we need to handle this
                    
                    # For UI tests: pass the page directly
                    # For API tests: the function might use 'request' fixture
                    
                    # Simple approach: try calling with page parameter
                    import inspect
                    sig = inspect.signature(test_func)
                    params = list(sig.parameters.keys())
                    
                    if 'page' in params:
                        # UI test - pass page
                        test_func(page=page)
                    elif 'request' in params:
                        # API test - we need to provide an APIRequestContext
                        # This requires the context from the page
                        context = page.context
                        request_context = context.request
                        test_func(request=request_context)
                    elif len(params) == 0:
                        # No parameters - just call it
                        test_func()
                    else:
                        # Try calling with page as first positional arg
                        test_func(page)
                        
                except Exception as e:
                    errors.append(f"{test_func.__name__}: {str(e)}")
            
            # Clean up temporary file if needed
            if cleanup and script_path.exists() and not str(script_path).startswith('execution'):
                script_path.unlink()
            
            # If any test failed, raise the first error
            if errors:
                raise RuntimeError(f"Test execution failed: {'; '.join(errors)}")
        
        return wrapper


def create_test_callable(
    script: PlaywrightScript,
    script_dir: str = "execution/generated_tests"
) -> Callable[[Page], None]:
    """
    Convenience function to create a callable from a PlaywrightScript.
    
    Parameters
    ----------
    script:
        The generated Playwright script.
        
    script_dir:
        Directory to save the script.
        
    Returns
    -------
    Callable[[Page], None]
        A function that can be passed to ExecutionService.
    """
    adapter = ScriptAdapter(script_output_dir=script_dir)
    return adapter.to_callable(script, save_to_disk=True)
