"""
LangGraph Orchestration: 5-node state graph for the agent execution loop.
Coordinates Planner -> Generate -> Execute -> Observe -> Repair workflow
with bounded retry logic for self-healing broken test scripts.
"""
from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from agents.requirement_agent import RequirementAgent
from agents.test_scenario_agent import TestScenarioAgent
from agents.script_agent import PlaywrightScriptAgent
from agents.failure_agent import FailureAnalysisAgent
from agents.self_healing_agent import SelfHealingAgent
from execution.runner import execution_runner
from shared.logger import get_logger

logger = get_logger("orchestration.graph")

class AgentState(TypedDict):
    parsed_req: Dict[str, Any]
    scenarios: List[Dict[str, Any]]
    scripts: List[Dict[str, Any]]
    execution_results: List[Dict[str, Any]]
    healing_results: List[Dict[str, Any]]
    retry_count: int
    max_retries: int

class LoopOrchestrator:
    """LangGraph State Graph orchestrating the agent execution loop."""

    def __init__(self):
        self.req_agent = RequirementAgent()
        self.scenario_agent = TestScenarioAgent()
        self.script_agent = PlaywrightScriptAgent()
        self.failure_agent = FailureAnalysisAgent()
        self.healing_agent = SelfHealingAgent()
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(AgentState)

        builder.add_node("planner", self._node_planner)
        builder.add_node("generate", self._node_generate)
        builder.add_node("execute", self._node_execute)
        builder.add_node("observe", self._node_observe)
        builder.add_node("repair", self._node_repair)

        builder.set_entry_point("planner")

        builder.add_edge("planner", "generate")
        builder.add_edge("generate", "execute")
        builder.add_edge("execute", "observe")

        builder.add_conditional_edges(
            "observe",
            self._should_repair,
            {
                "repair": "repair",
                "end": END
            }
        )

        builder.add_edge("repair", "execute")

        return builder.compile()

    def _node_planner(self, state: AgentState) -> Dict[str, Any]:
        logger.info("LangGraph Node [Planner]: Planning test strategy...")
        return {"retry_count": state.get("retry_count", 0)}

    def _node_generate(self, state: AgentState) -> Dict[str, Any]:
        logger.info("LangGraph Node [Generate]: Generating test scenarios and Playwright scripts...")
        req = state.get("parsed_req", {})
        scenarios = self.scenario_agent.generate_scenarios(req)
        
        scripts = []
        for scen in scenarios:
            script_obj = self.script_agent.generate_script(scen)
            scripts.append(script_obj.model_dump())

        return {
            "scenarios": [s.model_dump() for s in scenarios],
            "scripts": scripts
        }

    def _node_execute(self, state: AgentState) -> Dict[str, Any]:
        logger.info("LangGraph Node [Execute]: Executing generated Playwright scripts...")
        scripts = state.get("scripts", [])
        results = []
        for scr in scripts:
            res = execution_runner.run_test(scr["file_path"], test_type=scr["test_type"])
            results.append(res.model_dump())
        return {"execution_results": results}

    def _node_observe(self, state: AgentState) -> Dict[str, Any]:
        logger.info("LangGraph Node [Observe]: Analyzing test execution outcomes...")
        return {}

    def _should_repair(self, state: AgentState) -> str:
        results = state.get("execution_results", [])
        failures = [r for r in results if r["status"] in ["FAILED", "ERROR"]]
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 2)

        if failures and retry_count < max_retries:
            logger.info(f"Failures detected ({len(failures)}). Routing to [Repair] (Attempt {retry_count + 1}/{max_retries})")
            return "repair"
        else:
            logger.info("All tests passed or max retries reached. Routing to [END].")
            return "end"

    def _node_repair(self, state: AgentState) -> Dict[str, Any]:
        logger.info("LangGraph Node [Repair]: Self-Healing broken scripts...")
        results = state.get("execution_results", [])
        failures = [r for r in results if r["status"] in ["FAILED", "ERROR"]]
        healed_list = []

        for fail in failures:
            from shared.schemas import ExecutionResult
            exec_obj = ExecutionResult(**fail)
            healing_res = self.healing_agent.heal_test(exec_obj, execution_runner)
            healed_list.append(healing_res.model_dump())

        return {
            "healing_results": healed_list,
            "retry_count": state.get("retry_count", 0) + 1
        }

    def run_workflow(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        initial_state: AgentState = {
            "parsed_req": req_data,
            "scenarios": [],
            "scripts": [],
            "execution_results": [],
            "healing_results": [],
            "retry_count": 0,
            "max_retries": 2
        }
        return self.graph.invoke(initial_state)

orchestrator = LoopOrchestrator()
