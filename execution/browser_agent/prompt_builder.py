from execution.browser_agent.inspection_summary import InspectionSummary


class PromptBuilder:
    """
    Builds an LLM-ready prompt from a browser inspection.

    This prompt is consumed by the Playwright generation
    agent to generate robust automation scripts using
    real page context.
    """

    @staticmethod
    def build(
        requirement: str,
        inspection: InspectionSummary,
    ) -> str:

        return f"""
You are an expert Playwright automation engineer.

Generate Python Playwright code that satisfies the requirement.

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
{PromptBuilder._format_list(inspection.buttons)}

Inputs:
{PromptBuilder._format_list(inspection.inputs)}

Forms:
{PromptBuilder._format_list(inspection.forms)}

Links:
{PromptBuilder._format_list(inspection.links)}

Console Errors:
{PromptBuilder._format_list(inspection.console_errors)}

Network Failures:
{PromptBuilder._format_list(inspection.failed_requests)}

DOM Excerpt:
{inspection.dom_excerpt}

==============================
Instructions
==============================

Generate Playwright Python.

Prefer:

- page.get_by_role()
- page.get_by_label()
- page.get_by_placeholder()

Avoid:

- brittle XPath
- hard-coded waits
- unnecessary CSS selectors

Return only valid Python.
""".strip()

    @staticmethod
    def _format_list(values: list[str]) -> str:

        if not values:
            return "None"

        return "\n".join(
            f"- {value}"
            for value in values
        )