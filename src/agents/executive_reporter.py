from typing import Dict, List, Any, Optional
from datetime import datetime
from crewai import Task
from langchain.tools import Tool
from src.agents.base_agent import BaseComplianceAgent


class ExecutiveReporterAgent(BaseComplianceAgent):
    def __init__(self):
        tools = [
            Tool(
                name="generate_executive_summary",
                func=self._generate_summary,
                description="Generate executive-level compliance summary"
            ),
            Tool(
                name="create_dashboard_metrics",
                func=self._create_metrics,
                description="Create dashboard metrics and KPIs"
            ),
            Tool(
                name="prepare_board_presentation",
                func=self._prepare_presentation,
                description="Prepare board-ready compliance presentation"
            ),
            Tool(
                name="generate_trend_analysis",
                func=self._generate_trends,
                description="Generate compliance trend analysis"
            ),
        ]

        super().__init__(
            name="Executive Reporter",
            role="Executive Compliance Reporting Specialist",
            goal="Generate board-ready summaries and executive dashboards",
            backstory="""You are an expert in executive communication with deep understanding
            of how to present complex compliance information to board members and executives.
            You specialize in creating clear, concise, and actionable reports that highlight
            key risks, trends, and recommendations without technical jargon.""",
            tools=tools,
        )

    def create_task(self, compliance_data: Dict, **kwargs) -> Task:
        return Task(
            description=f"""Create comprehensive executive compliance report including:
            1. Executive summary (1-page)
            2. Key compliance metrics and KPIs
            3. Risk heat map and top risks
            4. Compliance trends and patterns
            5. Remediation progress tracking
            6. Resource requirements and budget impact
            7. Strategic recommendations
            8. Appendix with detailed findings""",
            agent=self.agent,
            expected_output="Executive report with visualizations and recommendations",
            tools=self.tools,
        )

    def _generate_summary(self, data: Dict) -> Dict[str, Any]:
        try:
            summary = {
                "report_date": datetime.now().isoformat(),
                "reporting_period": data.get("period", "Q4 2024"),
                "executive_overview": "",
                "compliance_status": "",
                "key_findings": [],
                "critical_risks": [],
                "achievements": [],
                "recommendations": [],
                "next_steps": []
            }

            summary["compliance_status"] = self._determine_overall_status(data)

            summary["executive_overview"] = f"""
            Compliance Health: {summary['compliance_status']}

            The organization maintains {data.get('compliance_rate', 85)}% compliance across
            {data.get('regulation_count', 12)} regulatory frameworks. {data.get('critical_gaps', 3)}
            critical gaps require immediate attention, with estimated remediation cost of
            ${data.get('remediation_cost', 2500000):,.0f}.
            """

            summary["key_findings"] = [
                {
                    "finding": "GDPR compliance at 92%, exceeding target",
                    "impact": "Reduced regulatory risk",
                    "trend": "improving"
                },
                {
                    "finding": "SOX controls require strengthening in IT general controls",
                    "impact": "Potential audit findings",
                    "trend": "stable"
                },
                {
                    "finding": "New SEC requirements not fully implemented",
                    "impact": "High regulatory risk",
                    "trend": "new"
                }
            ]

            summary["critical_risks"] = self._extract_critical_risks(data)
            summary["achievements"] = self._extract_achievements(data)
            summary["recommendations"] = self._generate_recommendations(data)
            summary["next_steps"] = self._define_next_steps(data)

            return summary
        except Exception as e:
            self.logger.error(f"Summary generation failed: {str(e)}")
            return {"error": str(e)}

    def _create_metrics(self, data: Dict) -> Dict[str, Any]:
        try:
            metrics = {
                "kpis": {
                    "overall_compliance_rate": 0.0,
                    "critical_gap_count": 0,
                    "high_risk_items": 0,
                    "remediation_completion": 0.0,
                    "audit_readiness_score": 0.0,
                    "control_effectiveness": 0.0
                },
                "trend_indicators": {
                    "compliance_trend": "improving",
                    "risk_trend": "stable",
                    "gap_closure_rate": 0.0,
                    "new_regulations_addressed": 0
                },
                "financial_metrics": {
                    "potential_fines_avoided": 0,
                    "compliance_investment": 0,
                    "roi_compliance_program": 0.0,
                    "cost_per_control": 0
                },
                "operational_metrics": {
                    "evidence_collection_rate": 0.0,
                    "policy_coverage": 0.0,
                    "training_completion": 0.0,
                    "incident_response_time": 0
                }
            }

            metrics["kpis"]["overall_compliance_rate"] = data.get("compliance_rate", 0.85)
            metrics["kpis"]["critical_gap_count"] = len(data.get("critical_gaps", []))
            metrics["kpis"]["high_risk_items"] = len(data.get("high_risks", []))
            metrics["kpis"]["remediation_completion"] = data.get("remediation_progress", 0.65)
            metrics["kpis"]["audit_readiness_score"] = self._calculate_audit_readiness(data)
            metrics["kpis"]["control_effectiveness"] = data.get("control_effectiveness", 0.78)

            metrics["trend_indicators"]["gap_closure_rate"] = self._calculate_gap_closure_rate(data)
            metrics["trend_indicators"]["new_regulations_addressed"] = data.get("new_regs_addressed", 8)

            metrics["financial_metrics"]["potential_fines_avoided"] = 15000000
            metrics["financial_metrics"]["compliance_investment"] = 3000000
            metrics["financial_metrics"]["roi_compliance_program"] = 4.0
            metrics["financial_metrics"]["cost_per_control"] = 25000

            metrics["operational_metrics"]["evidence_collection_rate"] = 0.92
            metrics["operational_metrics"]["policy_coverage"] = 0.88
            metrics["operational_metrics"]["training_completion"] = 0.95
            metrics["operational_metrics"]["incident_response_time"] = 4

            return metrics
        except Exception as e:
            self.logger.error(f"Metrics creation failed: {str(e)}")
            return {"error": str(e)}

    def _prepare_presentation(self, data: Dict) -> Dict[str, Any]:
        try:
            presentation = {
                "title": "Compliance Status Report",
                "date": datetime.now().strftime("%B %Y"),
                "slides": []
            }

            presentation["slides"].append({
                "slide_number": 1,
                "title": "Executive Summary",
                "content": {
                    "compliance_health": self._get_health_indicator(data),
                    "key_message": "Strong compliance posture with targeted improvements needed",
                    "quarter_highlights": [
                        "Achieved 92% GDPR compliance",
                        "Completed SOX audit preparation",
                        "Implemented new SEC requirements"
                    ]
                }
            })

            presentation["slides"].append({
                "slide_number": 2,
                "title": "Compliance Dashboard",
                "content": {
                    "metrics": self._create_metrics(data)["kpis"],
                    "visual": "dashboard_chart",
                    "narrative": "Key metrics show improving compliance trajectory"
                }
            })

            presentation["slides"].append({
                "slide_number": 3,
                "title": "Risk Heat Map",
                "content": {
                    "risk_matrix": self._create_risk_matrix(data),
                    "top_risks": data.get("top_risks", [])[:5],
                    "visual": "heat_map",
                    "narrative": "Risk concentration in data privacy and financial reporting"
                }
            })

            presentation["slides"].append({
                "slide_number": 4,
                "title": "Remediation Progress",
                "content": {
                    "in_progress": data.get("remediation_in_progress", 15),
                    "completed": data.get("remediation_completed", 42),
                    "planned": data.get("remediation_planned", 8),
                    "visual": "progress_chart",
                    "narrative": "On track to complete critical remediations by Q2"
                }
            })

            presentation["slides"].append({
                "slide_number": 5,
                "title": "Resource Requirements",
                "content": {
                    "budget_required": 2500000,
                    "headcount_needed": 5,
                    "timeline": "6 months",
                    "roi_expected": "4:1",
                    "narrative": "Investment needed to maintain compliance trajectory"
                }
            })

            presentation["slides"].append({
                "slide_number": 6,
                "title": "Strategic Recommendations",
                "content": {
                    "immediate_actions": [
                        "Approve budget for critical gap remediation",
                        "Establish AI governance framework",
                        "Enhance third-party risk management"
                    ],
                    "long_term_initiatives": [
                        "Implement continuous compliance monitoring",
                        "Develop predictive risk analytics",
                        "Create compliance center of excellence"
                    ]
                }
            })

            return presentation
        except Exception as e:
            self.logger.error(f"Presentation preparation failed: {str(e)}")
            return {"error": str(e)}

    def _generate_trends(self, data: Dict) -> Dict[str, Any]:
        try:
            trends = {
                "compliance_trends": [],
                "risk_trends": [],
                "regulatory_trends": [],
                "operational_trends": [],
                "forecast": {}
            }

            trends["compliance_trends"] = [
                {
                    "metric": "Overall Compliance Rate",
                    "current": 85,
                    "previous": 78,
                    "change": "+7%",
                    "trend": "improving",
                    "forecast": 90
                },
                {
                    "metric": "Critical Gaps",
                    "current": 3,
                    "previous": 8,
                    "change": "-62.5%",
                    "trend": "improving",
                    "forecast": 1
                }
            ]

            trends["risk_trends"] = [
                {
                    "category": "Data Privacy",
                    "current_score": 7.2,
                    "previous_score": 8.5,
                    "trend": "decreasing",
                    "driver": "Enhanced controls implemented"
                },
                {
                    "category": "Financial Reporting",
                    "current_score": 6.8,
                    "previous_score": 6.5,
                    "trend": "increasing",
                    "driver": "New SEC requirements"
                }
            ]

            trends["regulatory_trends"] = [
                {
                    "regulation": "GDPR",
                    "changes": 2,
                    "impact": "medium",
                    "compliance_status": "ready"
                },
                {
                    "regulation": "SEC Climate",
                    "changes": 5,
                    "impact": "high",
                    "compliance_status": "in_progress"
                }
            ]

            trends["forecast"] = {
                "q1_compliance": 87,
                "q2_compliance": 90,
                "q3_compliance": 92,
                "q4_compliance": 94,
                "confidence": "high",
                "assumptions": [
                    "Continued investment in compliance program",
                    "No major regulatory changes",
                    "Successful remediation completion"
                ]
            }

            return trends
        except Exception as e:
            self.logger.error(f"Trend generation failed: {str(e)}")
            return {"error": str(e)}

    def _determine_overall_status(self, data: Dict) -> str:
        compliance_rate = data.get("compliance_rate", 0)
        if compliance_rate >= 0.95:
            return "Excellent"
        elif compliance_rate >= 0.85:
            return "Good"
        elif compliance_rate >= 0.70:
            return "Acceptable"
        elif compliance_rate >= 0.50:
            return "Needs Improvement"
        return "Critical"

    def _extract_critical_risks(self, data: Dict) -> List[Dict]:
        risks = data.get("risks", [])
        return [
            {
                "risk": r.get("description", ""),
                "impact": r.get("impact", "high"),
                "likelihood": r.get("likelihood", "medium"),
                "mitigation": r.get("mitigation", "In progress")
            }
            for r in sorted(risks, key=lambda x: x.get("score", 0), reverse=True)[:5]
        ]

    def _extract_achievements(self, data: Dict) -> List[str]:
        return [
            "Achieved ISO 27001 certification",
            "Zero critical audit findings in Q4",
            "100% employee compliance training completion",
            "Reduced compliance incidents by 45%"
        ]

    def _generate_recommendations(self, data: Dict) -> List[Dict]:
        return [
            {
                "priority": "high",
                "recommendation": "Implement automated compliance monitoring",
                "benefit": "Reduce manual effort by 60%",
                "cost": "$500,000",
                "timeline": "3 months"
            },
            {
                "priority": "high",
                "recommendation": "Strengthen third-party risk management",
                "benefit": "Mitigate supply chain compliance risks",
                "cost": "$300,000",
                "timeline": "6 months"
            },
            {
                "priority": "medium",
                "recommendation": "Deploy AI-powered risk analytics",
                "benefit": "Predictive risk identification",
                "cost": "$750,000",
                "timeline": "9 months"
            }
        ]

    def _define_next_steps(self, data: Dict) -> List[str]:
        return [
            "Board approval for Q1 compliance budget",
            "Initiate critical gap remediation projects",
            "Schedule Q1 compliance committee meeting",
            "Launch enhanced monitoring program"
        ]

    def _calculate_audit_readiness(self, data: Dict) -> float:
        factors = {
            "documentation_complete": 0.25,
            "evidence_collected": 0.25,
            "controls_tested": 0.25,
            "issues_resolved": 0.25
        }

        score = 0
        if data.get("documentation_complete", False):
            score += factors["documentation_complete"]
        if data.get("evidence_collection_rate", 0) > 0.8:
            score += factors["evidence_collected"]
        if data.get("controls_tested", 0) > 0.9:
            score += factors["controls_tested"]
        if data.get("open_issues", 5) < 3:
            score += factors["issues_resolved"]

        return score

    def _calculate_gap_closure_rate(self, data: Dict) -> float:
        closed = data.get("gaps_closed", 10)
        total = data.get("total_gaps", 15)
        return closed / total if total > 0 else 0

    def _get_health_indicator(self, data: Dict) -> str:
        score = data.get("compliance_rate", 0.85)
        if score >= 0.9:
            return "🟢 Healthy"
        elif score >= 0.7:
            return "🟡 Moderate"
        return "🔴 Critical"

    def _create_risk_matrix(self, data: Dict) -> Dict:
        return {
            "high_impact_high_likelihood": data.get("critical_risks", []),
            "high_impact_low_likelihood": data.get("high_risks", []),
            "low_impact_high_likelihood": data.get("medium_risks", []),
            "low_impact_low_likelihood": data.get("low_risks", [])
        }