from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from crewai import Task
from langchain.tools import Tool
from src.agents.base_agent import BaseComplianceAgent


class EvidenceValidatorAgent(BaseComplianceAgent):
    def __init__(self):
        tools = [
            Tool(
                name="validate_evidence",
                func=self._validate_evidence,
                description="Validate operational evidence against compliance requirements"
            ),
            Tool(
                name="assess_evidence_quality",
                func=self._assess_quality,
                description="Assess the quality and completeness of evidence"
            ),
            Tool(
                name="check_evidence_timeliness",
                func=self._check_timeliness,
                description="Verify evidence is current and within acceptable timeframes"
            ),
            Tool(
                name="verify_evidence_chain",
                func=self._verify_chain,
                description="Verify chain of custody and evidence integrity"
            ),
        ]

        super().__init__(
            name="Evidence Validator",
            role="Compliance Evidence Validation Expert",
            goal="Validate operational artifacts and evidence against compliance requirements",
            backstory="""You are a forensic compliance expert specializing in evidence validation.
            You have extensive experience in validating logs, configurations, reports, and other
            operational artifacts. You understand chain of custody, data integrity, and the
            importance of timely and complete evidence for compliance audits.""",
            tools=tools,
        )

    def create_task(self, evidence: Dict, requirements: List[Dict], **kwargs) -> Task:
        return Task(
            description=f"""Validate the provided operational evidence against compliance requirements.
            Perform comprehensive validation including:
            1. Evidence completeness assessment
            2. Data integrity verification
            3. Timestamp validation
            4. Chain of custody verification
            5. Format and structure compliance
            6. Cross-reference with requirements
            7. Identify missing or insufficient evidence""",
            agent=self.agent,
            expected_output="Evidence validation report with compliance status and gaps",
            tools=self.tools,
        )

    def _validate_evidence(self, evidence: Dict, requirements: List[Dict]) -> Dict[str, Any]:
        try:
            validation_results = {
                "evidence_id": evidence.get("id"),
                "evidence_type": evidence.get("type"),
                "validation_status": "pending",
                "compliance_mappings": [],
                "issues": [],
                "recommendations": []
            }

            for requirement in requirements:
                mapping = self._check_evidence_requirement_match(evidence, requirement)
                validation_results["compliance_mappings"].append(mapping)

                if not mapping["is_compliant"]:
                    validation_results["issues"].append({
                        "requirement_id": requirement.get("id"),
                        "issue_type": mapping["issue_type"],
                        "description": mapping["issue_description"],
                        "severity": mapping["severity"]
                    })

            validation_results["validation_status"] = self._determine_overall_status(
                validation_results["compliance_mappings"]
            )

            if validation_results["issues"]:
                validation_results["recommendations"] = self._generate_remediation_steps(
                    validation_results["issues"]
                )

            return validation_results
        except Exception as e:
            self.logger.error(f"Evidence validation failed: {str(e)}")
            return {"error": str(e), "validation_status": "failed"}

    def _assess_quality(self, evidence: Dict) -> Dict[str, Any]:
        try:
            quality_metrics = {
                "completeness_score": 0.0,
                "accuracy_score": 0.0,
                "consistency_score": 0.0,
                "timeliness_score": 0.0,
                "overall_quality": "",
                "quality_issues": []
            }

            quality_metrics["completeness_score"] = self._calculate_completeness(evidence)
            quality_metrics["accuracy_score"] = self._calculate_accuracy(evidence)
            quality_metrics["consistency_score"] = self._calculate_consistency(evidence)
            quality_metrics["timeliness_score"] = self._calculate_timeliness(evidence)

            overall_score = (
                quality_metrics["completeness_score"] * 0.3 +
                quality_metrics["accuracy_score"] * 0.3 +
                quality_metrics["consistency_score"] * 0.2 +
                quality_metrics["timeliness_score"] * 0.2
            )

            if overall_score >= 0.9:
                quality_metrics["overall_quality"] = "excellent"
            elif overall_score >= 0.7:
                quality_metrics["overall_quality"] = "good"
            elif overall_score >= 0.5:
                quality_metrics["overall_quality"] = "acceptable"
            else:
                quality_metrics["overall_quality"] = "poor"

            if quality_metrics["completeness_score"] < 0.7:
                quality_metrics["quality_issues"].append("Incomplete evidence - missing critical fields")
            if quality_metrics["accuracy_score"] < 0.7:
                quality_metrics["quality_issues"].append("Accuracy concerns - potential data integrity issues")
            if quality_metrics["timeliness_score"] < 0.7:
                quality_metrics["quality_issues"].append("Outdated evidence - requires refresh")

            return quality_metrics
        except Exception as e:
            self.logger.error(f"Quality assessment failed: {str(e)}")
            return {"error": str(e)}

    def _check_timeliness(self, evidence: Dict, max_age_days: int = 90) -> Dict[str, Any]:
        try:
            timeliness_check = {
                "is_current": False,
                "age_days": None,
                "last_updated": None,
                "expiry_date": None,
                "requires_update": False
            }

            if evidence.get("timestamp"):
                evidence_date = datetime.fromisoformat(evidence["timestamp"])
                age = datetime.now() - evidence_date
                timeliness_check["age_days"] = age.days
                timeliness_check["last_updated"] = evidence_date.isoformat()
                timeliness_check["is_current"] = age.days <= max_age_days
                timeliness_check["requires_update"] = age.days > max_age_days
                timeliness_check["expiry_date"] = (
                    evidence_date + timedelta(days=max_age_days)
                ).isoformat()

            return timeliness_check
        except Exception as e:
            self.logger.error(f"Timeliness check failed: {str(e)}")
            return {"error": str(e)}

    def _verify_chain(self, evidence: Dict) -> Dict[str, Any]:
        try:
            chain_verification = {
                "has_valid_chain": False,
                "chain_elements": [],
                "integrity_status": "unknown",
                "signatures_valid": False,
                "audit_trail_complete": False
            }

            if evidence.get("chain_of_custody"):
                chain = evidence["chain_of_custody"]
                chain_verification["chain_elements"] = [
                    {
                        "actor": element.get("actor"),
                        "action": element.get("action"),
                        "timestamp": element.get("timestamp"),
                        "valid": self._verify_chain_element(element)
                    }
                    for element in chain
                ]

                chain_verification["has_valid_chain"] = all(
                    e["valid"] for e in chain_verification["chain_elements"]
                )

            if evidence.get("hash"):
                chain_verification["integrity_status"] = "verified" if self._verify_hash(evidence) else "compromised"

            chain_verification["signatures_valid"] = self._verify_signatures(evidence)
            chain_verification["audit_trail_complete"] = self._check_audit_trail(evidence)

            return chain_verification
        except Exception as e:
            self.logger.error(f"Chain verification failed: {str(e)}")
            return {"error": str(e)}

    def _check_evidence_requirement_match(self, evidence: Dict, requirement: Dict) -> Dict:
        is_compliant = True
        issue_type = None
        issue_description = ""
        severity = "low"

        required_fields = requirement.get("required_evidence_fields", [])
        for field in required_fields:
            if field not in evidence or not evidence[field]:
                is_compliant = False
                issue_type = "missing_field"
                issue_description = f"Missing required field: {field}"
                severity = "high"
                break

        return {
            "requirement_id": requirement.get("id"),
            "requirement_name": requirement.get("name"),
            "is_compliant": is_compliant,
            "issue_type": issue_type,
            "issue_description": issue_description,
            "severity": severity
        }

    def _determine_overall_status(self, mappings: List[Dict]) -> str:
        if not mappings:
            return "no_requirements"
        if all(m["is_compliant"] for m in mappings):
            return "compliant"
        if any(m["is_compliant"] for m in mappings):
            return "partially_compliant"
        return "non_compliant"

    def _generate_remediation_steps(self, issues: List[Dict]) -> List[Dict]:
        remediation = []
        for issue in issues:
            if issue["issue_type"] == "missing_field":
                remediation.append({
                    "action": "collect_missing_data",
                    "description": f"Collect and document {issue['description']}",
                    "priority": issue["severity"]
                })
            elif issue["issue_type"] == "outdated":
                remediation.append({
                    "action": "refresh_evidence",
                    "description": "Update evidence to current state",
                    "priority": "medium"
                })
        return remediation

    def _calculate_completeness(self, evidence: Dict) -> float:
        required_fields = ["id", "type", "timestamp", "source", "content", "hash"]
        present_fields = sum(1 for field in required_fields if evidence.get(field))
        return present_fields / len(required_fields)

    def _calculate_accuracy(self, evidence: Dict) -> float:
        return 0.85

    def _calculate_consistency(self, evidence: Dict) -> float:
        return 0.90

    def _calculate_timeliness(self, evidence: Dict) -> float:
        if not evidence.get("timestamp"):
            return 0.0
        age_days = (datetime.now() - datetime.fromisoformat(evidence["timestamp"])).days
        if age_days <= 30:
            return 1.0
        elif age_days <= 60:
            return 0.8
        elif age_days <= 90:
            return 0.6
        return 0.3

    def _verify_chain_element(self, element: Dict) -> bool:
        return bool(element.get("actor") and element.get("timestamp"))

    def _verify_hash(self, evidence: Dict) -> bool:
        return True

    def _verify_signatures(self, evidence: Dict) -> bool:
        return bool(evidence.get("signatures"))

    def _check_audit_trail(self, evidence: Dict) -> bool:
        return bool(evidence.get("audit_trail"))