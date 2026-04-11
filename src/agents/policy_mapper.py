from typing import Dict, List, Any, Optional
from crewai import Task
from src.agents.base_agent import BaseComplianceAgent, make_crewai_tool
from src.services.rag_service import RAGService


class PolicyMapperAgent(BaseComplianceAgent):
    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service

        tools = [
            make_crewai_tool("map_policy_to_regulation", "Map internal policies to regulatory requirements", self._map_policy),
            make_crewai_tool("identify_policy_gaps", "Identify gaps between policies and regulations", self._identify_gaps),
            make_crewai_tool("generate_policy_recommendations", "Generate policy improvement recommendations", self._generate_recommendations),
        ]

        super().__init__(
            name="Policy Mapper",
            role="Policy Compliance Mapping Specialist",
            goal="Map internal organizational policies to regulatory controls and identify coverage gaps",
            backstory="""You are an expert in policy analysis with deep understanding of how
            internal policies should align with regulatory requirements. You have extensive
            experience in gap analysis, control mapping, and policy optimization across
            multiple regulatory frameworks.""",
            tools=tools,
        )

    def create_task(self, policies: List[Dict], regulations: List[Dict], **kwargs) -> Task:
        return Task(
            description=f"""Map the provided internal policies to regulatory requirements.
            Perform comprehensive analysis including:
            1. Direct policy-to-regulation mappings
            2. Coverage assessment for each regulatory requirement
            3. Gap identification and risk assessment
            4. Overlapping or redundant policy identification
            5. Policy effectiveness scoring
            6. Recommendations for policy improvements""",
            agent=self.agent,
            expected_output="Detailed mapping matrix with gap analysis and recommendations",
            tools=self.tools,
        )

    def _map_policy(self, policy: Dict, regulations: List[Dict]) -> Dict[str, Any]:
        try:
            mapping = {
                "policy_id": policy.get("id"),
                "policy_name": policy.get("name"),
                "mapped_regulations": [],
                "coverage_score": 0.0,
                "gaps": [],
                "strengths": []
            }

            policy_embeddings = self.rag_service.get_embeddings(policy.get("content", ""))

            for regulation in regulations:
                reg_embeddings = self.rag_service.get_embeddings(regulation.get("content", ""))

                similarity_score = self._calculate_similarity(policy_embeddings, reg_embeddings)

                if similarity_score > 0.7:
                    mapping["mapped_regulations"].append({
                        "regulation_id": regulation.get("id"),
                        "regulation_name": regulation.get("name"),
                        "similarity_score": similarity_score,
                        "coverage_areas": self._extract_coverage_areas(policy, regulation)
                    })

            mapping["coverage_score"] = self._calculate_coverage_score(mapping["mapped_regulations"])

            return mapping
        except Exception as e:
            self.logger.error(f"Policy mapping failed: {str(e)}")
            return {}

    def _identify_gaps(self, policies: List[Dict], regulations: List[Dict]) -> List[Dict]:
        try:
            gaps = []

            for regulation in regulations:
                covered = False
                partial_coverage = []

                for policy in policies:
                    mapping = self._map_policy(policy, [regulation])
                    if mapping.get("mapped_regulations"):
                        if mapping["coverage_score"] >= 0.8:
                            covered = True
                            break
                        elif mapping["coverage_score"] >= 0.5:
                            partial_coverage.append({
                                "policy": policy.get("name"),
                                "coverage": mapping["coverage_score"]
                            })

                if not covered:
                    gaps.append({
                        "regulation": regulation.get("name"),
                        "requirement": regulation.get("requirement"),
                        "gap_type": "uncovered" if not partial_coverage else "partial",
                        "partial_coverage": partial_coverage,
                        "risk_level": self._assess_gap_risk(regulation),
                        "remediation_priority": self._calculate_priority(regulation)
                    })

            return sorted(gaps, key=lambda x: x["remediation_priority"], reverse=True)
        except Exception as e:
            self.logger.error(f"Gap identification failed: {str(e)}")
            return []

    def _generate_recommendations(self, gaps: List[Dict], existing_policies: List[Dict]) -> List[Dict]:
        try:
            recommendations = []

            for gap in gaps:
                if gap["gap_type"] == "uncovered":
                    recommendations.append({
                        "type": "new_policy",
                        "regulation": gap["regulation"],
                        "recommendation": f"Create new policy to address {gap['regulation']}",
                        "priority": gap["remediation_priority"],
                        "suggested_content": self._generate_policy_template(gap),
                        "estimated_effort": "high"
                    })
                elif gap["gap_type"] == "partial":
                    recommendations.append({
                        "type": "policy_update",
                        "regulation": gap["regulation"],
                        "affected_policies": gap["partial_coverage"],
                        "recommendation": f"Enhance existing policies to fully cover {gap['regulation']}",
                        "priority": gap["remediation_priority"],
                        "suggested_amendments": self._generate_amendments(gap, existing_policies),
                        "estimated_effort": "medium"
                    })

            return recommendations
        except Exception as e:
            self.logger.error(f"Recommendation generation failed: {str(e)}")
            return []

    def _calculate_similarity(self, emb1, emb2) -> float:
        import numpy as np
        return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))

    def _extract_coverage_areas(self, policy: Dict, regulation: Dict) -> List[str]:
        return ["Data Protection", "Access Control", "Audit Trails", "Reporting"]

    def _calculate_coverage_score(self, mapped_regulations: List[Dict]) -> float:
        if not mapped_regulations:
            return 0.0
        scores = [m.get("similarity_score", 0) for m in mapped_regulations]
        return sum(scores) / len(scores)

    def _assess_gap_risk(self, regulation: Dict) -> str:
        penalties = regulation.get("penalties", {})
        if penalties.get("max_fine", 0) > 1000000:
            return "high"
        elif penalties.get("max_fine", 0) > 100000:
            return "medium"
        return "low"

    def _calculate_priority(self, regulation: Dict) -> int:
        risk_scores = {"high": 3, "medium": 2, "low": 1}
        base_score = risk_scores.get(self._assess_gap_risk(regulation), 1)
        if regulation.get("enforcement_date"):
            base_score += 2
        return base_score

    def _generate_policy_template(self, gap: Dict) -> str:
        return f"""Policy Template for {gap['regulation']}
        1. Purpose and Scope
        2. Regulatory Requirements
        3. Control Objectives
        4. Implementation Procedures
        5. Monitoring and Reporting
        6. Roles and Responsibilities"""

    def _generate_amendments(self, gap: Dict, policies: List[Dict]) -> List[Dict]:
        return [{"policy": p["name"], "amendment": "Add specific controls"} for p in gap.get("partial_coverage", [])]