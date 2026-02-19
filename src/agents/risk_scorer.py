from typing import Dict, List, Any, Optional
from enum import Enum
from crewai import Task
from langchain.tools import Tool
from src.agents.base_agent import BaseComplianceAgent


class RiskLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class RiskScorerAgent(BaseComplianceAgent):
    def __init__(self):
        tools = [
            Tool(
                name="calculate_risk_score",
                func=self._calculate_risk_score,
                description="Calculate risk scores for compliance gaps"
            ),
            Tool(
                name="assess_impact",
                func=self._assess_impact,
                description="Assess business impact of compliance failures"
            ),
            Tool(
                name="evaluate_likelihood",
                func=self._evaluate_likelihood,
                description="Evaluate likelihood of compliance breaches"
            ),
            Tool(
                name="generate_risk_matrix",
                func=self._generate_risk_matrix,
                description="Generate risk assessment matrix"
            ),
            Tool(
                name="prioritize_remediation",
                func=self._prioritize_remediation,
                description="Prioritize remediation efforts based on risk"
            ),
        ]

        super().__init__(
            name="Risk Scorer",
            role="Compliance Risk Assessment Specialist",
            goal="Score and prioritize compliance gaps using advanced risk models",
            backstory="""You are a risk assessment expert with deep expertise in quantitative
            and qualitative risk analysis. You specialize in compliance risk scoring,
            impact assessment, and remediation prioritization. You use industry-standard
            risk frameworks and have experience with financial, operational, and
            reputational risk assessment.""",
            tools=tools,
        )

    def create_task(self, gaps: List[Dict], context: Dict, **kwargs) -> Task:
        return Task(
            description=f"""Perform comprehensive risk assessment for identified compliance gaps.
            Analysis should include:
            1. Individual gap risk scoring
            2. Cumulative risk assessment
            3. Impact analysis (financial, operational, reputational)
            4. Likelihood evaluation
            5. Risk heat map generation
            6. Remediation prioritization matrix
            7. Risk mitigation recommendations""",
            agent=self.agent,
            expected_output="Risk assessment report with scores, priorities, and recommendations",
            tools=self.tools,
        )

    def _calculate_risk_score(self, gap: Dict, context: Dict) -> Dict[str, Any]:
        try:
            risk_assessment = {
                "gap_id": gap.get("id"),
                "gap_description": gap.get("description"),
                "base_risk_score": 0.0,
                "adjusted_risk_score": 0.0,
                "risk_level": None,
                "risk_factors": {},
                "mitigation_urgency": None
            }

            impact_score = self._calculate_impact_score(gap, context)
            likelihood_score = self._calculate_likelihood_score(gap, context)
            control_effectiveness = self._assess_control_effectiveness(gap, context)

            risk_assessment["risk_factors"] = {
                "impact": impact_score,
                "likelihood": likelihood_score,
                "control_effectiveness": control_effectiveness,
                "regulatory_severity": self._get_regulatory_severity(gap),
                "business_criticality": self._get_business_criticality(gap, context)
            }

            risk_assessment["base_risk_score"] = (
                impact_score * likelihood_score * (1 - control_effectiveness)
            )

            risk_assessment["adjusted_risk_score"] = self._apply_risk_adjustments(
                risk_assessment["base_risk_score"],
                risk_assessment["risk_factors"],
                context
            )

            risk_assessment["risk_level"] = self._determine_risk_level(
                risk_assessment["adjusted_risk_score"]
            )

            risk_assessment["mitigation_urgency"] = self._calculate_urgency(
                risk_assessment["risk_level"],
                gap.get("deadline")
            )

            return risk_assessment
        except Exception as e:
            self.logger.error(f"Risk calculation failed: {str(e)}")
            return {"error": str(e)}

    def _assess_impact(self, gap: Dict) -> Dict[str, Any]:
        try:
            impact_assessment = {
                "financial_impact": {
                    "potential_fine": 0,
                    "revenue_loss": 0,
                    "remediation_cost": 0,
                    "total_financial": 0
                },
                "operational_impact": {
                    "process_disruption": "low",
                    "system_availability": "no_impact",
                    "productivity_loss": 0
                },
                "reputational_impact": {
                    "customer_trust": "minimal",
                    "market_perception": "neutral",
                    "regulatory_standing": "stable"
                },
                "legal_impact": {
                    "litigation_risk": "low",
                    "regulatory_action": "unlikely",
                    "criminal_liability": "none"
                }
            }

            if gap.get("regulation_type") == "GDPR":
                impact_assessment["financial_impact"]["potential_fine"] = self._calculate_gdpr_fine(gap)
            elif gap.get("regulation_type") == "SOX":
                impact_assessment["financial_impact"]["potential_fine"] = self._calculate_sox_penalty(gap)
                impact_assessment["legal_impact"]["criminal_liability"] = "possible"

            impact_assessment["financial_impact"]["remediation_cost"] = self._estimate_remediation_cost(gap)
            impact_assessment["financial_impact"]["total_financial"] = sum(
                impact_assessment["financial_impact"].values()
            )

            return impact_assessment
        except Exception as e:
            self.logger.error(f"Impact assessment failed: {str(e)}")
            return {"error": str(e)}

    def _evaluate_likelihood(self, gap: Dict, historical_data: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            likelihood_evaluation = {
                "occurrence_probability": 0.0,
                "detection_probability": 0.0,
                "exploitation_probability": 0.0,
                "overall_likelihood": 0.0,
                "likelihood_factors": [],
                "historical_incidents": 0
            }

            if historical_data:
                likelihood_evaluation["historical_incidents"] = historical_data.get("incident_count", 0)

            base_probability = 0.3
            if gap.get("exposure_level") == "external":
                base_probability += 0.2
            if gap.get("control_maturity") == "low":
                base_probability += 0.3

            likelihood_evaluation["occurrence_probability"] = min(base_probability, 1.0)

            likelihood_evaluation["detection_probability"] = 0.7 if gap.get("monitoring_enabled") else 0.3

            likelihood_evaluation["exploitation_probability"] = self._calculate_exploitation_probability(gap)

            likelihood_evaluation["overall_likelihood"] = (
                likelihood_evaluation["occurrence_probability"] * 0.4 +
                likelihood_evaluation["exploitation_probability"] * 0.4 +
                (1 - likelihood_evaluation["detection_probability"]) * 0.2
            )

            if likelihood_evaluation["overall_likelihood"] > 0.7:
                likelihood_evaluation["likelihood_factors"].append("High exposure with weak controls")
            if likelihood_evaluation["historical_incidents"] > 0:
                likelihood_evaluation["likelihood_factors"].append(f"Previous incidents: {likelihood_evaluation['historical_incidents']}")

            return likelihood_evaluation
        except Exception as e:
            self.logger.error(f"Likelihood evaluation failed: {str(e)}")
            return {"error": str(e)}

    def _generate_risk_matrix(self, risks: List[Dict]) -> Dict[str, Any]:
        try:
            matrix = {
                "risk_distribution": {
                    "critical": [],
                    "high": [],
                    "medium": [],
                    "low": [],
                    "minimal": []
                },
                "heat_map": [],
                "top_risks": [],
                "risk_trends": {},
                "aggregate_metrics": {}
            }

            for risk in risks:
                level = risk.get("risk_level", "medium")
                matrix["risk_distribution"][level].append({
                    "id": risk.get("gap_id"),
                    "score": risk.get("adjusted_risk_score"),
                    "description": risk.get("gap_description", "")[:100]
                })

            matrix["heat_map"] = self._create_heat_map(risks)

            matrix["top_risks"] = sorted(
                risks,
                key=lambda x: x.get("adjusted_risk_score", 0),
                reverse=True
            )[:10]

            matrix["aggregate_metrics"] = {
                "total_risks": len(risks),
                "critical_count": len(matrix["risk_distribution"]["critical"]),
                "high_count": len(matrix["risk_distribution"]["high"]),
                "average_risk_score": sum(r.get("adjusted_risk_score", 0) for r in risks) / len(risks) if risks else 0,
                "total_exposure": self._calculate_total_exposure(risks)
            }

            return matrix
        except Exception as e:
            self.logger.error(f"Risk matrix generation failed: {str(e)}")
            return {"error": str(e)}

    def _prioritize_remediation(self, risks: List[Dict]) -> List[Dict]:
        try:
            prioritized = []

            for risk in risks:
                priority_score = self._calculate_priority_score(risk)

                prioritized.append({
                    "gap_id": risk.get("gap_id"),
                    "risk_level": risk.get("risk_level"),
                    "priority_score": priority_score,
                    "remediation_timeline": self._get_remediation_timeline(risk),
                    "resource_requirements": self._estimate_resources(risk),
                    "dependencies": self._identify_dependencies(risk),
                    "quick_wins": self._identify_quick_wins(risk)
                })

            return sorted(prioritized, key=lambda x: x["priority_score"], reverse=True)
        except Exception as e:
            self.logger.error(f"Remediation prioritization failed: {str(e)}")
            return []

    def _calculate_impact_score(self, gap: Dict, context: Dict) -> float:
        base_impact = 0.5
        if gap.get("affects_financial_reporting"):
            base_impact += 0.3
        if gap.get("affects_customer_data"):
            base_impact += 0.2
        return min(base_impact, 1.0)

    def _calculate_likelihood_score(self, gap: Dict, context: Dict) -> float:
        return 0.6

    def _assess_control_effectiveness(self, gap: Dict, context: Dict) -> float:
        if gap.get("existing_controls"):
            return 0.7
        return 0.2

    def _get_regulatory_severity(self, gap: Dict) -> str:
        if gap.get("regulation_type") in ["SOX", "GDPR"]:
            return "high"
        return "medium"

    def _get_business_criticality(self, gap: Dict, context: Dict) -> str:
        if gap.get("affects_core_business"):
            return "critical"
        return "moderate"

    def _apply_risk_adjustments(self, base_score: float, factors: Dict, context: Dict) -> float:
        adjusted = base_score
        if factors.get("regulatory_severity") == "high":
            adjusted *= 1.5
        if factors.get("business_criticality") == "critical":
            adjusted *= 1.3
        return min(adjusted, 10.0)

    def _determine_risk_level(self, score: float) -> str:
        if score >= 8:
            return RiskLevel.CRITICAL.value
        elif score >= 6:
            return RiskLevel.HIGH.value
        elif score >= 4:
            return RiskLevel.MEDIUM.value
        elif score >= 2:
            return RiskLevel.LOW.value
        return RiskLevel.MINIMAL.value

    def _calculate_urgency(self, risk_level: str, deadline: Optional[str]) -> str:
        if risk_level == RiskLevel.CRITICAL.value:
            return "immediate"
        elif risk_level == RiskLevel.HIGH.value:
            return "urgent"
        elif deadline:
            return "scheduled"
        return "standard"

    def _calculate_gdpr_fine(self, gap: Dict) -> int:
        return 20000000

    def _calculate_sox_penalty(self, gap: Dict) -> int:
        return 5000000

    def _estimate_remediation_cost(self, gap: Dict) -> int:
        return 100000

    def _calculate_exploitation_probability(self, gap: Dict) -> float:
        return 0.4

    def _create_heat_map(self, risks: List[Dict]) -> List[List[int]]:
        return [[len([r for r in risks if r.get("risk_level") == level]) for level in ["low", "medium", "high", "critical"]]]

    def _calculate_total_exposure(self, risks: List[Dict]) -> float:
        return sum(r.get("adjusted_risk_score", 0) for r in risks)

    def _calculate_priority_score(self, risk: Dict) -> float:
        score = risk.get("adjusted_risk_score", 0)
        if risk.get("mitigation_urgency") == "immediate":
            score *= 2
        return score

    def _get_remediation_timeline(self, risk: Dict) -> str:
        if risk.get("risk_level") == RiskLevel.CRITICAL.value:
            return "30 days"
        elif risk.get("risk_level") == RiskLevel.HIGH.value:
            return "60 days"
        return "90 days"

    def _estimate_resources(self, risk: Dict) -> Dict:
        return {"hours": 100, "team_size": 3, "budget": 50000}

    def _identify_dependencies(self, risk: Dict) -> List[str]:
        return ["Policy update", "System configuration"]

    def _identify_quick_wins(self, risk: Dict) -> List[str]:
        return ["Enable logging", "Update documentation"]