import os
import re
from pathlib import Path
from typing import Dict, Any, List
import PyPDF2
import docx
from shared.schemas import ParsedRequirement
from shared.logger import get_logger

logger = get_logger("ingestion.parser")

class DocumentParser:
    """Parses PDF, DOCX, TXT, and Markdown requirement documents."""

    @staticmethod
    def parse_file(file_path: str) -> ParsedRequirement:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        if ext == ".pdf":
            raw_text = DocumentParser._extract_pdf(path)
        elif ext in [".docx", ".doc"]:
            raw_text = DocumentParser._extract_docx(path)
        else:
            raw_text = path.read_text(encoding="utf-8", errors="ignore")

        return DocumentParser._parse_text(path.name, raw_text)

    @staticmethod
    def _extract_pdf(path: Path) -> str:
        text = ""
        try:
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        except Exception as e:
            logger.error(f"Error reading PDF {path}: {e}")
        return text

    @staticmethod
    def _extract_docx(path: Path) -> str:
        text = ""
        try:
            doc = docx.Document(path)
            for p in doc.paragraphs:
                text += p.text + "\n"
        except Exception as e:
            logger.error(f"Error reading DOCX {path}: {e}")
        return text

    @staticmethod
    def _parse_text(filename: str, raw_text: str) -> ParsedRequirement:
        print(f"[DEBUG INGESTION] Current document: {filename}")
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        title = filename
        for line in lines:
            if line.startswith("# ") or line.startswith("Project:") or line.startswith("Title:"):
                title = line.replace("#", "").replace("Project:", "").replace("Title:", "").strip()
                break

        # Section-aware splitting
        sections: Dict[str, List[str]] = {}
        current_section = "GENERAL"
        sections[current_section] = []

        header_patterns = [
            (r'User Roles|Actors|Roles', "ACTORS"),
            (r'Business Workflows|Workflows|Use Cases', "WORKFLOWS"),
            (r'Business Validation|Validation Rules|Validations|Business Rules', "VALIDATIONS"),
            (r'API Requirements|API Specifications|API Endpoints|API Spec', "APIS"),
            (r'Expected Request Payload|Database Requirements|Test Automation', "OTHER")
        ]

        for line in lines:
            is_header = False
            for pat, sec_key in header_patterns:
                if (line.startswith("#") or re.match(r'^\d+\.', line)) and re.search(pat, line, re.IGNORECASE):
                    current_section = sec_key
                    sections[current_section] = []
                    is_header = True
                    break
            if not is_header:
                sections[current_section].append(line)

        # 1. ACTORS EXTRACTION
        actors = []
        if "ACTORS" in sections:
            sec_lines = sections["ACTORS"]
            for line in sec_lines:
                clean_l = line.strip(" \t\r\n\x7f\x00*-#`")
                if not clean_l or clean_l.lower() in ["actor", "responsibilities", "user roles & actors", "actors", "role", "description"]:
                    continue
                # Match clean actor lists/lines e.g. "- **Policyholder**: Submits claims..."
                m_actor = re.match(r'^[\*\-]?\s*\**([A-Za-z\s]+)\**\s*[:\-]', clean_l)
                if m_actor:
                    actor_name = m_actor.group(1).strip()
                    if len(actor_name) < 40 and actor_name not in actors and actor_name.lower() not in ["input fields", "actor"]:
                        actors.append(actor_name)
                elif len(clean_l) < 40 and not clean_l.endswith(".") and not any(verb in clean_l.lower() for verb in ["portal", "application", "is an enterprise", "submit motor", "view approved"]):
                    if clean_l not in actors:
                        actors.append(clean_l)
        
        # Fallback for general non-sectioned documents
        if not actors:
            for line in lines:
                clean_l = line.strip(" \t\r\n\x7f\x00*-#`")
                m_actor = re.match(r'^[\*\-]?\s*\**([A-Za-z\s]+)\**\s*[:\-]', clean_l)
                if m_actor:
                    actor_name = m_actor.group(1).strip()
                    if actor_name.lower() in ["policyholder", "claims adjuster", "finance manager", "insured", "insurer", "claimant"] and actor_name not in actors:
                        actors.append(actor_name)

        # 2. WORKFLOW EXTRACTION
        workflows = []
        if "WORKFLOWS" in sections:
            sec_lines = sections["WORKFLOWS"]
            for line in sec_lines:
                m = re.match(r'^[\*\-]?\s*\**\s*(BRD-WF-\d+|WF-\d+|WORKFLOW-\d+)\s*[:\-]\s*(.+?)\**$', line, re.IGNORECASE)
                if m:
                    wf_str = f"{m.group(1).upper()}: {m.group(2).strip('* ')}"
                    if wf_str not in workflows:
                        workflows.append(wf_str)

        # Fallback for general workflows
        if not workflows:
            for line in lines:
                m = re.match(r'^[\*\-]?\s*\**\s*(BRD-WF-\d+|WF-\d+|WORKFLOW-\d+|SECTION\s+[IVXLCDM]+)\s*[:\-]?\s*(.+?)\**$', line, re.IGNORECASE)
                if m:
                    wf_str = f"{m.group(1).upper()}: {m.group(2).strip('* ')}"
                    if wf_str not in workflows:
                        workflows.append(wf_str)

        # 3. VALIDATION EXTRACTION
        validations = []
        sec_lines_for_val = sections["VALIDATIONS"] if "VALIDATIONS" in sections else lines
        
        # Multi-line line joining for validations
        joined_val_lines = []
        curr_val = ""
        for l in sec_lines_for_val:
            clean_l = l.strip(" \t\r\n\x7f\x00*-#`")
            if re.search(r'\b(VAL-\d+|VR-\d+|RULE-\d+)\b', clean_l, re.IGNORECASE):
                if curr_val:
                    joined_val_lines.append(curr_val)
                curr_val = clean_l
            else:
                if curr_val:
                    curr_val += " " + clean_l
                else:
                    curr_val = clean_l
        if curr_val:
            joined_val_lines.append(curr_val)

        for jl in joined_val_lines:
            m = re.search(r'\b(VAL-\d+|VR-\d+|RULE-\d+)\s*[:\.]?\s*(.+)', jl, re.IGNORECASE)
            if m:
                val_str = f"{m.group(1).upper()}: {m.group(2).strip()}"
                if val_str not in validations:
                    validations.append(val_str)

        # 4. API ENDPOINTS EXTRACTION
        api_endpoints = []
        methods = {"GET", "POST", "PUT", "PATCH", "DELETE"}

        for i, line in enumerate(lines):
            # Inline method + endpoint
            m = re.search(r'\b(GET|POST|PUT|PATCH|DELETE)\s+(/api/[^\s`\'"<>]+|/[^\s`\'"<>]+)', line, re.IGNORECASE)
            if m:
                method = m.group(1).upper()
                ep = m.group(2).rstrip(".,;:)\"")
                if method in methods and ep.startswith("/") and len(ep) > 1:
                    if not any(e["method"] == method and e["endpoint"] == ep for e in api_endpoints):
                        api_endpoints.append({"method": method, "endpoint": ep})
                continue

            # Multi-line table layout: Method on line i, Endpoint on line i+1
            if line.upper() in methods and i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.startswith("/"):
                    method = line.upper()
                    ep = next_line.split()[0].rstrip(".,;:)\"")
                    if ep.startswith("/") and len(ep) > 1:
                        if not any(e["method"] == method and e["endpoint"] == ep for e in api_endpoints):
                            api_endpoints.append({"method": method, "endpoint": ep})

        summary = f"Parsed document '{filename}' containing {len(lines)} lines, {len(workflows)} key workflows, {len(validations)} validations, and {len(api_endpoints)} API endpoints."

        return ParsedRequirement(
            document_name=filename,
            title=title,
            summary=summary,
            actors=actors,
            workflows=workflows,
            validations=validations,
            api_endpoints=api_endpoints,
            raw_text=raw_text
        )

