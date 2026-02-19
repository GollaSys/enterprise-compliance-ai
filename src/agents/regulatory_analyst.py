from typing import Dict, List, Any
from crewai import Task
from langchain.tools import Tool
from src.agents.base_agent import BaseComplianceAgent
from src.services.document_service import DocumentService
from src.services.rag_service import RAGService


class RegulatoryAnalystAgent(BaseComplianceAgent):
    def __init__(self, document_service: DocumentService, rag_service: RAGService):
        self.document_service = document_service
        self.rag_service = rag_service

        tools = [
            Tool(
                name="extract_regulatory_requirements",
                func=self._extract_requirements,
                description="Extract compliance requirements from regulatory documents"
            ),
            Tool(
                name="search_regulations",
                func=self._search_regulations,
                description="Search for specific regulatory clauses and requirements"
            ),
            Tool(
                name="analyze_regulatory_changes",
                func=self._analyze_changes,
                description="Analyze changes in regulatory requirements over time"
            ),
        ]

        super().__init__(
            name="Regulatory Analyst",
            role="Senior Regulatory Compliance Analyst",
            goal="Extract, analyze, and interpret regulatory requirements from various compliance documents including SEC, FINRA, SOX, and GDPR regulations",
            backstory="""You are an expert regulatory analyst with 15+ years of experience in
            financial services compliance. You specialize in interpreting complex regulatory
            frameworks and extracting actionable compliance requirements. You have deep knowledge
            of SEC, FINRA, SOX, GDPR, and other major regulatory frameworks.""",
            tools=tools,
        )

    def create_task(self, document_path: str, regulation_type: str, **kwargs) -> Task:
        return Task(
            description=f"""Analyze the regulatory document at {document_path} for {regulation_type} compliance.
            Extract all relevant compliance requirements, obligations, and control points.
            Structure the output with:
            1. Regulatory citation references
            2. Specific compliance requirements
            3. Control objectives
            4. Implementation timelines
            5. Penalty provisions
            6. Reporting obligations""",
            agent=self.agent,
            expected_output="Structured JSON containing extracted regulatory requirements",
            tools=self.tools,
        )

    def _extract_requirements(self, document_content: str) -> Dict[str, Any]:
        try:
            requirements = self.rag_service.extract_entities(
                document_content,
                entity_types=["requirement", "obligation", "control", "deadline"]
            )

            structured_reqs = {
                "requirements": [],
                "obligations": [],
                "controls": [],
                "deadlines": [],
                "citations": []
            }

            for req in requirements:
                req_type = req.get("type", "requirement")
                if req_type in structured_reqs:
                    structured_reqs[req_type].append({
                        "text": req.get("text"),
                        "section": req.get("section"),
                        "priority": req.get("priority", "medium"),
                        "metadata": req.get("metadata", {})
                    })

            return structured_reqs
        except Exception as e:
            self.logger.error(f"Failed to extract requirements: {str(e)}")
            return {}

    def _search_regulations(self, query: str, regulation_types: List[str] = None) -> List[Dict]:
        try:
            results = self.rag_service.semantic_search(
                query=query,
                filters={"regulation_type": regulation_types} if regulation_types else None,
                top_k=10
            )

            return [{
                "content": r.get("content"),
                "source": r.get("source"),
                "relevance_score": r.get("score"),
                "metadata": r.get("metadata", {})
            } for r in results]
        except Exception as e:
            self.logger.error(f"Regulation search failed: {str(e)}")
            return []

    def _analyze_changes(self, current_doc: str, previous_doc: str) -> Dict[str, Any]:
        try:
            changes = {
                "new_requirements": [],
                "modified_requirements": [],
                "removed_requirements": [],
                "impact_assessment": "",
                "compliance_gaps": []
            }

            current_reqs = self._extract_requirements(current_doc)
            previous_reqs = self._extract_requirements(previous_doc)

            current_set = set(str(r) for r in current_reqs.get("requirements", []))
            previous_set = set(str(r) for r in previous_reqs.get("requirements", []))

            changes["new_requirements"] = list(current_set - previous_set)
            changes["removed_requirements"] = list(previous_set - current_set)

            return changes
        except Exception as e:
            self.logger.error(f"Change analysis failed: {str(e)}")
            return {}