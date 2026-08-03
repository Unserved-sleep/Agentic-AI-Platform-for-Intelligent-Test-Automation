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
import subprocess
import sys
import tempfile
import os
from pathlib import Path
from typing import Callable, Optional
from playwright.sync_api import Page

from models.playwright_script import PlaywrightScript
from models.test_scenario import TestLevel


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

        For UI tests: dynamically imports and injects the Playwright Page.
        For API_CONTRACT / API_BACKEND tests: saves the file and runs it
        via subprocess pytest so that all pytest fixtures are properly
        injected.  The wrapper ignores the Page argument in this case.

        Parameters
        ----------
        script:
            The generated Playwright script (contains code string).

        save_to_disk:
            If True, saves the script to disk before importing/running.
            If False, uses a temporary file (UI tests only).

        Returns
        -------
        Callable[[Page], None]
            A function that accepts a Playwright Page and executes the test.
        """
        # Always save to disk – subprocess pytest needs a real file path.
        if save_to_disk:
            script_path = self.script_output_dir / script.file_name
        else:
            script_path = Path(tempfile.mktemp(suffix='.py'))

        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script.code)

        # --- Route: API tests run via subprocess pytest ---
        is_api_test = script.test_level in (TestLevel.API_CONTRACT, TestLevel.API_BACKEND)

        if is_api_test:
            return self._create_subprocess_wrapper(script_path)

        # --- Route: UI tests use dynamic import + page injection ---
        module_name = script.file_name.replace('.py', '')
        spec = importlib.util.spec_from_file_location(module_name, script_path)

        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {script_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            if not save_to_disk and script_path.exists():
                script_path.unlink()
            raise RuntimeError(f"Failed to load generated script: {e}") from e

        test_functions = self._extract_test_functions(module)

        if not test_functions:
            raise ValueError(f"No test functions found in {script.file_name}")

        return self._create_wrapper(test_functions, script_path, save_to_disk)
    
    def _create_subprocess_wrapper(self, script_path: Path) -> Callable[[Page], None]:
        """
        Create a wrapper that runs the test file via subprocess pytest.

        Used for API_CONTRACT and API_BACKEND tests, where pytest fixture
        injection (db_session, api_request_context, etc.) is required and
        cannot be replicated by calling the function directly.

        The returned callable accepts a Page argument (for interface
        compatibility with PlaywrightUIRunner) but ignores it.

        Parameters
        ----------
        script_path:
            Absolute path to the saved test file.

        Returns
        -------
        Callable[[Page], None]
            A wrapper that runs pytest on the file as a subprocess.
        """
        def wrapper(page: Page) -> None:  # noqa: ARG001  (page is unused for API tests)
            python_exe = sys.executable
            cmd = [
                python_exe, "-m", "pytest",
                str(script_path),
                "-v",
                "--tb=short",
                "--no-header",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(Path(script_path).parent.parent.parent),  # project root
            )

            # Print output so it appears in loop logs
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

            if result.returncode != 0:
                output = result.stdout + result.stderr
                raise RuntimeError(
                    f"pytest exited with code {result.returncode}.\n{output}"
                )

        return wrapper

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
        Create a wrapper function that executes all UI test functions.

        This wrapper is only used for UI tests (test_level == UI).
        API tests are handled by _create_subprocess_wrapper instead.

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
            import inspect
            errors = []

            for test_func in test_functions:
                try:
                    sig = inspect.signature(test_func)
                    params = list(sig.parameters.keys())

                    if 'page' in params:
                        test_func(page=page)
                    elif len(params) == 0:
                        test_func()
                    else:
                        # Fallback: pass page as first positional arg
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
