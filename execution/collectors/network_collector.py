"""
======================================================================

Module:
Network Collector

Owner:
Engineer 3 – Browser Automation, Frontend & DevOps

Purpose:
Captures HTTP network activity emitted by a Playwright
page during test execution.

Three event categories are collected:
- NetworkRequest   — outgoing HTTP requests
- NetworkResponse  — server responses (status, headers)
- NetworkFailure   — requests that failed at the network layer

Each entry is a typed, frozen Pydantic model. No Playwright
objects are retained after capture.

Integration
-----------
NetworkCollector is attached to a Playwright Page *before*
execution via ``attach(page)``.  Playwright fires ``request``,
``response``, and ``requestfailed`` events; each fires the
corresponding handler which creates the typed entry.

After execution, ``collect()`` returns a ``NetworkEventBundle``
containing all three lists. ``clear()`` resets the collector
for reuse across tests.

----------------------------------------------------------------------

TODO:
Support HAR file export.
Capture request/response body payloads (opt-in, large data).

----------------------------------------------------------------------

DUMMY:
None

----------------------------------------------------------------------

INTEGRATION:
Used by ArtifactCollector.
Optionally injected into PlaywrightUIRunner and
PlaywrightAPIRunner via RunnerFactory.

======================================================================
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class NetworkRequest(BaseModel):
    """
    Represents a single outgoing HTTP request captured
    during execution.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC time the request was captured.",
    )

    method: str = Field(
        ...,
        description="HTTP method (GET, POST, PUT, …).",
    )

    url: str = Field(
        ...,
        description="Full request URL.",
    )

    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Request headers.",
    )

    resource_type: str = Field(
        default="",
        description=(
            "Playwright resource type: document, script, "
            "fetch, xhr, image, …"
        ),
    )


class NetworkResponse(BaseModel):
    """
    Represents a single HTTP response captured during
    execution.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC time the response was captured.",
    )

    url: str = Field(
        ...,
        description="URL of the request that produced this response.",
    )

    status_code: int = Field(
        ...,
        description="HTTP status code (200, 404, 500, …).",
    )

    status_text: str = Field(
        default="",
        description="HTTP status text (OK, Not Found, …).",
    )

    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Response headers.",
    )

    ok: bool = Field(
        ...,
        description="True when status_code is in [200, 299].",
    )


class NetworkFailure(BaseModel):
    """
    Represents an HTTP request that failed at the network
    layer (DNS, timeout, SSL, …).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC time the failure was captured.",
    )

    url: str = Field(
        ...,
        description="URL of the failed request.",
    )

    failure_text: str = Field(
        default="",
        description="Playwright failure text describing the error.",
    )

    method: str = Field(
        default="",
        description="HTTP method of the failed request.",
    )


class NetworkEventBundle(BaseModel):
    """
    Aggregates all network events captured during one
    execution.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    requests: list[NetworkRequest] = Field(
        default_factory=list,
        description="All outgoing requests captured.",
    )

    responses: list[NetworkResponse] = Field(
        default_factory=list,
        description="All responses captured.",
    )

    failures: list[NetworkFailure] = Field(
        default_factory=list,
        description="All failed requests captured.",
    )

    @property
    def total_requests(self) -> int:
        """Total number of outgoing requests."""
        return len(self.requests)

    @property
    def total_failures(self) -> int:
        """Total number of failed requests."""
        return len(self.failures)

    def failed_urls(self) -> list[str]:
        """Return the URLs of all failed requests."""
        return [f.url for f in self.failures]

    def responses_with_status(
        self,
        status_code: int,
    ) -> list[NetworkResponse]:
        """
        Return all responses matching *status_code*.

        Parameters
        ----------
        status_code:
            HTTP status code to filter by.

        Returns
        -------
        list[NetworkResponse]
        """
        return [r for r in self.responses if r.status_code == status_code]

    def has_failures(self) -> bool:
        """Return True if any network failures were captured."""
        return len(self.failures) > 0


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------


def _safe_headers(raw_headers: Any) -> dict[str, str]:
    """
    Safely convert Playwright header objects to a plain dict.

    Playwright may return a dict or a list of dicts depending on
    the API version. This normalises to ``{name: value}``.

    Parameters
    ----------
    raw_headers:
        Raw headers from a Playwright Request or Response.

    Returns
    -------
    dict[str, str]
    """
    try:
        if isinstance(raw_headers, dict):
            return {k: str(v) for k, v in raw_headers.items()}

        # Playwright headers() returns a plain dict in sync API.
        return {}

    except Exception:
        return {}


class NetworkCollector:
    """
    Listens to Playwright network events on a Page and
    buffers them as typed models.

    Typical usage
    -------------
    ::

        collector = NetworkCollector()

        # Before test execution
        collector.attach(page)

        # … run the test …

        # After test execution
        bundle = collector.collect()   # NetworkEventBundle

        # Reset for next test
        collector.clear()
    """

    def __init__(self) -> None:
        self._requests: list[NetworkRequest] = []
        self._responses: list[NetworkResponse] = []
        self._failures: list[NetworkFailure] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def attach(self, page: Any) -> None:
        """
        Register Playwright network event listeners on *page*.

        Must be called before the test function starts.

        Parameters
        ----------
        page:
            An active ``playwright.sync_api.Page`` instance.
        """
        page.on("request", self._on_request)
        page.on("response", self._on_response)
        page.on("requestfailed", self._on_request_failed)

    # ------------------------------------------------------------------
    # Internal handlers
    # ------------------------------------------------------------------

    def _on_request(self, request: Any) -> None:
        """
        Handle a Playwright ``request`` event.

        Parameters
        ----------
        request:
            Playwright Request object.
        """
        try:
            entry = NetworkRequest(
                method=request.method,
                url=request.url,
                headers=_safe_headers(request.headers),
                resource_type=getattr(request, "resource_type", ""),
            )
            self._requests.append(entry)
        except Exception:
            pass

    def _on_response(self, response: Any) -> None:
        """
        Handle a Playwright ``response`` event.

        Parameters
        ----------
        response:
            Playwright Response object.
        """
        try:
            status = response.status
            entry = NetworkResponse(
                url=response.url,
                status_code=status,
                status_text=getattr(response, "status_text", ""),
                headers=_safe_headers(response.headers),
                ok=200 <= status < 300,
            )
            self._responses.append(entry)
        except Exception:
            pass

    def _on_request_failed(self, request: Any) -> None:
        """
        Handle a Playwright ``requestfailed`` event.

        Parameters
        ----------
        request:
            Playwright Request object for the failed request.
        """
        try:
            failure_text = ""
            failure = getattr(request, "failure", None)
            if failure is not None:
                failure_text = str(failure)

            entry = NetworkFailure(
                url=request.url,
                method=request.method,
                failure_text=failure_text,
            )
            self._failures.append(entry)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def collect(self) -> NetworkEventBundle:
        """
        Return a ``NetworkEventBundle`` containing copies of
        all captured events.

        Returns
        -------
        NetworkEventBundle
        """
        return NetworkEventBundle(
            requests=list(self._requests),
            responses=list(self._responses),
            failures=list(self._failures),
        )

    def clear(self) -> None:
        """
        Remove all buffered network events.
        """
        self._requests.clear()
        self._responses.clear()
        self._failures.clear()

    def request_count(self) -> int:
        """Return the number of captured requests."""
        return len(self._requests)

    def response_count(self) -> int:
        """Return the number of captured responses."""
        return len(self._responses)

    def failure_count(self) -> int:
        """Return the number of captured failures."""
        return len(self._failures)
