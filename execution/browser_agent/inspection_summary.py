from dataclasses import dataclass, field

from execution.browser_agent.inspectors.dom_inspector import DOMInspector
from execution.browser_agent.page_context import PageSnapshot





@dataclass
class InspectionSummary:
    url: str
    title: str

    buttons: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    forms: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)

    console_errors: list[str] = field(default_factory=list)
    failed_requests: list[str] = field(default_factory=list)

    dom_excerpt: str = ""


class InspectionSummaryBuilder:

    @staticmethod
    def from_snapshot(snapshot: PageSnapshot) -> InspectionSummary:
        """
        Build an AI-friendly summary from a PageSnapshot.
        """

        browser = snapshot.browser_state
        dom_snapshot = snapshot.dom_snapshot

        # Parse the DOM into structured elements
        dom = DOMInspector.inspect(dom_snapshot.html)

        # Console errors only
        console_errors = [
            log.message
            for log in snapshot.console_logs
            if log.level.upper() == "ERROR"
        ]

        # Network failures
        failed_requests = snapshot.network_events.failed_urls()

        return InspectionSummary(
            url=browser.current_url,
            title=browser.title,

            buttons=dom.buttons,
            inputs=dom.inputs,
            forms=dom.forms,
            links=dom.links,

            console_errors=console_errors,
            failed_requests=failed_requests,

            # Keep the HTML excerpt small for AI prompts
            dom_excerpt=(dom_snapshot.html or "")[:3000],
        )