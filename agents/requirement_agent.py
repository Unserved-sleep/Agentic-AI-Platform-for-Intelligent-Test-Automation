import json
from typing import Dict, Any
from shared.schemas import ParsedRequirement
from agents.llm_client import llm_client
from prompts.system_prompts import REQUIREMENT_AGENT_PROMPT
from database.persistence import DBPersistenceHelper
from shared.logger import get_logger

logger = get_logger("agents.requirement_agent")

class RequirementAgent:
    """Ingests requirements and builds structured domain context."""

    def process_requirement(self, requirement: ParsedRequirement, rag_pipeline: Any = None) -> Dict[str, Any]:
        document_name = requirement.document_name
        source = requirement.document_name
        print(f"Current document: {document_name}")
        print(f"Analysis source: {source}")
        print(f"[DEBUG RequirementAgent] Processing document: {document_name}")

        # Persist Document to PostgreSQL
        try:
            DBPersistenceHelper.save_document(
                filename=document_name,
                title=requirement.title,
                raw_text=requirement.raw_text,
                summary=requirement.summary
            )
        except Exception as e:
            logger.warning(f"Failed to persist document '{document_name}' into PostgreSQL: {e}")

        rag_context = ""
        if rag_pipeline:
            rag_context = rag_pipeline.retrieve_context(
                query="overview domain actors workflows coverage rules api endpoints",
                top_k=10,
                doc_id=document_name
            )

        context_to_use = rag_context if rag_context else requirement.raw_text[:4000]

        prompt = f"""
Document Title: {requirement.title}
File Name: {document_name}
Summary: {requirement.summary}

Extracted Context from Document:
{context_to_use}

Extracted Statements from Parser:
Workflows / Key Sections: {requirement.workflows[:10]}
Validations / Rules: {requirement.validations[:10]}
Parsed API Endpoints: {requirement.api_endpoints}

Analyze ONLY the above document context for '{document_name}'.
Do NOT use information from previous documents, sample BRDs, prior conversations, or external assumptions.
If this document is an Insurance Policy or non-software document:
- Identify policy parties/actors (Insurer, Insured, Claimant, etc.)
- Identify coverage sections/workflows (Section I Loss/Damage, Section II Third Party, etc.)
- Identify conditions, deductibles, IDV, exclusions, period of insurance under validations
- Set "api_endpoints": [] (empty list) unless explicit HTTP endpoints (e.g. GET /api/v1/...) exist in the document context.
"""
        llm_response = llm_client.generate(prompt, system_prompt=REQUIREMENT_AGENT_PROMPT)
        
        parsed_json = self._try_parse_json(llm_response)
        
        if parsed_json:
            logger.info(f"Parsed structured domain analysis from LLM for {document_name}")
            
            # Combine deterministic parser APIs with LLM APIs to ensure complete coverage
            llm_apis = parsed_json.get("api_endpoints", [])
            merged_apis = list(requirement.api_endpoints)
            for api in llm_apis:
                if not any(e["method"] == api["method"] and e["endpoint"] == api["endpoint"] for e in merged_apis):
                    merged_apis.append(api)

            return {
                "title": parsed_json.get("title") or requirement.title,
                "document_name": document_name,
                "domain_type": parsed_json.get("domain_type", "Document Analysis"),
                "actors": parsed_json.get("actors") if (isinstance(parsed_json.get("actors"), list) and parsed_json.get("actors")) else requirement.actors,
                "workflows": parsed_json.get("workflows") if (isinstance(parsed_json.get("workflows"), list) and parsed_json.get("workflows")) else requirement.workflows,
                "validations": parsed_json.get("validations") if (isinstance(parsed_json.get("validations"), list) and parsed_json.get("validations")) else requirement.validations,
                "api_endpoints": merged_apis,
                "llm_analysis": parsed_json.get("llm_analysis") or llm_response or requirement.summary
            }

        # Dynamic fallback from parsed requirement
        return {
            "title": requirement.title,
            "document_name": document_name,
            "domain_type": "Document Analysis",
            "actors": requirement.actors,
            "workflows": requirement.workflows,
            "validations": requirement.validations,
            "api_endpoints": requirement.api_endpoints,
            "llm_analysis": llm_response or requirement.summary
        }

    def _try_parse_json(self, text: str) -> Dict[str, Any]:
        if not text:
            return {}
        try:
            cleaned = text.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            data = json.loads(cleaned)
            if isinstance(data, dict):
                # Sanitize API endpoints
                raw_apis = data.get("api_endpoints", [])
                valid_apis = []
                if isinstance(raw_apis, list):
                    valid_methods = {"GET", "POST", "PUT", "PATCH", "DELETE"}
                    for item in raw_apis:
                        if isinstance(item, dict):
                            m = str(item.get("method", "")).upper()
                            ep = str(item.get("endpoint", "")).strip(".,;:`')\"")
                            if m in valid_methods and ep.startswith("/") and len(ep) > 1:
                                valid_apis.append({"method": m, "endpoint": ep})
                data["api_endpoints"] = valid_apis
                return data
        except Exception as e:
            logger.warning(f"Could not parse RequirementAgent response as JSON: {e}")
        return {}

