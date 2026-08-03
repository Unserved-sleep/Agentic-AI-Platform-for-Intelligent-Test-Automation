from execution.browser_agent.inspection_summary import InspectionSummary

class ScenarioPromptBuilder:
    """
    Builds an LLM-ready prompt from a browser inspection.

    This prompt is consumed by the Scenario Agent to generate
    relevant test scenarios based on the live page context.
    """

    @staticmethod
    def build(
        requirement: str,
        inspection: InspectionSummary,
    ) -> str:

        return f"""
You are an expert QA Automation Engineer and Test Architect.

Generate test scenarios that satisfy the requirement.

==============================
Requirement
==============================

{requirement}

==============================
Live Browser Inspection
==============================

Page Title:
{inspection.title}

Current URL:
{inspection.url}

Buttons:
{ScenarioPromptBuilder._format_list(inspection.buttons)}

Inputs:
{ScenarioPromptBuilder._format_list(inspection.inputs)}

Forms:
{ScenarioPromptBuilder._format_list(inspection.forms)}

Links:
{ScenarioPromptBuilder._format_list(inspection.links)}

Console Errors:
{ScenarioPromptBuilder._format_list(inspection.console_errors)}

Network Failures:
{ScenarioPromptBuilder._format_list(inspection.failed_requests)}

DOM Excerpt:
{inspection.dom_excerpt}

==============================
Instructions
==============================

- Generate functional test scenarios only.
- Do NOT generate Playwright or Selenium code.
- Do NOT invent UI elements that are not present in the browser inspection.
- Generate only scenarios relevant to the inspected page.
- Cover positive, negative, boundary, validation, accessibility, security and navigation scenarios wherever applicable.
- Return output matching ScenarioGenerationResult.
""".strip()

    @staticmethod
    def _format_list(values: list[str]) -> str:

        if not values:
            return "None"

        return "\n".join(
            f"- {value}"
            for value in values
        )
