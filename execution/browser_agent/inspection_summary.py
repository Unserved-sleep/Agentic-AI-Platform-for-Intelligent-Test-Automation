from dataclasses import dataclass, field

from execution.browser_agent import PageSnapshot



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
        ...