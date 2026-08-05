"""
Integration and unit tests for the Agentic AI Test Automation Platform.

This module contains comprehensive tests that verify:
- Database connectivity and DBAssertionHelper queries
- Document parsing and RAG pipeline functionality
- Agent workflows (RequirementAgent, TestScenarioAgent, PlaywrightScriptAgent)
- Playwright execution with artifact generation (screenshots, traces, videos)
- LangGraph orchestration end-to-end workflow

Run tests with:
    pytest tests/ -v
    
For coverage:
    pytest tests/ --cov=. --cov-report=html
"""

import os
import pytest
from pathlib import Path
from database.assertions import DBAssertionHelper
from ingestion.parser import DocumentParser
from rag.pipeline import RAGPipeline
from agents.requirement_agent import RequirementAgent
from agents.test_scenario_agent import TestScenarioAgent
from agents.script_agent import PlaywrightScriptAgent
from agents.failure_agent import FailureAnalysisAgent
from agents.self_healing_agent import SelfHealingAgent
from execution.runner import execution_runner
from orchestration.graph import orchestrator

def test_database_connection_and_assertions():
    """Verify PostgreSQL database tables and DBAssertionHelper read-only queries."""
    res_status = DBAssertionHelper.assert_claim_status("CLM-1002", "APPROVED")
    assert res_status["success"] is True, f"Claim status assertion failed: {res_status['message']}"

    res_payout = DBAssertionHelper.assert_payout_created("CLM-1002", 5800.50)
    assert res_payout["success"] is True, f"Payout assertion failed: {res_payout['message']}"

def test_document_parser_and_rag_pipeline():
    """Verify parsing BRD document and ingesting into RAG pipeline."""
    brd_path = "docs/claims_brd.md"
    assert Path(brd_path).exists()

    parsed = DocumentParser.parse_file(brd_path)
    assert parsed.title != ""
    assert len(parsed.workflows) > 0

    rag = RAGPipeline()
    rag.ingest_document(parsed.document_name, parsed.raw_text)
    context = rag.retrieve_context("approve claim payout")
    assert len(context) > 0

def test_agents_and_script_generation():
    """Verify RequirementAgent, TestScenarioAgent, and PlaywrightScriptAgent."""
    parsed = DocumentParser.parse_file("docs/claims_brd.md")
    req_agent = RequirementAgent()
    analysis = req_agent.process_requirement(parsed)
    assert "workflows" in analysis

    scenario_agent = TestScenarioAgent()
    scenarios = scenario_agent.generate_scenarios(analysis)
    assert len(scenarios) > 0

    script_agent = PlaywrightScriptAgent()
    script = script_agent.generate_script(scenarios[0])
    assert Path(script.file_path).exists()
    assert "def test_" in script.script_code

def test_playwright_artifacts_tracing_and_runner():
    """Verify Playwright UI execution generates screenshot, trace, and video paths."""
    sc_agent = TestScenarioAgent()
    scenarios = sc_agent.generate_scenarios({})
    ui_scenarios = [s for s in scenarios if s.test_type == "UI"]
    assert len(ui_scenarios) > 0

    script_agent = PlaywrightScriptAgent()
    script = script_agent.generate_script(ui_scenarios[0])

    result = execution_runner.run_test(script.file_path, test_type="UI")
    assert result.run_id != ""
    assert hasattr(result, "screenshot_path")
    assert hasattr(result, "trace_path")
    assert hasattr(result, "video_path")

def test_orchestrator_langgraph_loop():
    """Verify LangGraph workflow execution end-to-end."""
    parsed = DocumentParser.parse_file("docs/claims_brd.md")
    req_agent = RequirementAgent()
    analysis = req_agent.process_requirement(parsed)

    result = orchestrator.run_workflow(analysis)
    assert "execution_results" in result
