from dataclasses import dataclass, field

from bs4 import BeautifulSoup


@dataclass
class DOMInspection:
    buttons: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    forms: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)


class DOMInspector:
    """
    Extracts useful UI elements from raw HTML.

    This class is intentionally lightweight and provides the
    information required by the AI script generation pipeline.
    """

    @staticmethod
    def inspect(html: str) -> DOMInspection:
        """
        Parse HTML and extract common interactive elements.

        Parameters
        ----------
        html:
            Raw page HTML.

        Returns
        -------
        DOMInspection
        """

        if not html:
            return DOMInspection()

        soup = BeautifulSoup(html, "html.parser")

        inspection = DOMInspection()

        # ---------------------------------------------------------
        # Buttons
        # ---------------------------------------------------------
        for button in soup.find_all("button"):

            text = (
                button.get_text(strip=True)
                or button.get("aria-label")
                or button.get("title")
                or button.get("id")
            )

            if text:
                inspection.buttons.append(text)

        # ---------------------------------------------------------
        # Inputs
        # ---------------------------------------------------------
        for element in soup.find_all("input"):

            label = (
                element.get("name")
                or element.get("id")
                or element.get("placeholder")
                or element.get("aria-label")
                or element.get("type")
            )

            if label:
                inspection.inputs.append(label)

        # ---------------------------------------------------------
        # Forms
        # ---------------------------------------------------------
        for form in soup.find_all("form"):

            name = (
                form.get("id")
                or form.get("name")
            )

            if name:
                inspection.forms.append(name)

        # ---------------------------------------------------------
        # Links
        # ---------------------------------------------------------
        for link in soup.find_all("a"):

            text = (
                link.get_text(strip=True)
                or link.get("title")
                or link.get("href")
            )

            if text:
                inspection.links.append(text)

        # ---------------------------------------------------------
        # Labels
        # ---------------------------------------------------------
        for label in soup.find_all("label"):

            text = label.get_text(strip=True)

            if text:
                inspection.labels.append(text)

        # ---------------------------------------------------------
        # Tables
        # ---------------------------------------------------------
        for table in soup.find_all("table"):

            name = (
                table.get("id")
                or " ".join(table.get("class", []))
                or "table"
            )

            inspection.tables.append(name)

        # ---------------------------------------------------------
        # Remove duplicates while preserving order
        # ---------------------------------------------------------
        inspection.buttons = list(dict.fromkeys(inspection.buttons))
        inspection.inputs = list(dict.fromkeys(inspection.inputs))
        inspection.forms = list(dict.fromkeys(inspection.forms))
        inspection.links = list(dict.fromkeys(inspection.links))
        inspection.labels = list(dict.fromkeys(inspection.labels))
        inspection.tables = list(dict.fromkeys(inspection.tables))

        return inspection