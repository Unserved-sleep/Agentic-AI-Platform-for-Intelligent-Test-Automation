"""
Orchestration package for LangGraph workflow management.

Implements a 5-node state graph for autonomous test execution:
1. Planner - Initialize state and retry budget
2. Generate - Create scenarios and scripts via AI agents
3. Execute - Run Playwright tests and collect artifacts
4. Observe - Analyze results and decide on repairs
5. Repair - Self-heal broken scripts and retry

The LoopOrchestrator manages the bounded retry loop (max 2 retries)
with failure analysis and automatic script repair.
"""

from orchestration.graph import orchestrator, LoopOrchestrator

__all__ = ["orchestrator", "LoopOrchestrator"]
