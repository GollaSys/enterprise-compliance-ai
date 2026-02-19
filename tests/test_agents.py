import pytest
from unittest.mock import Mock, patch
from src.agents.regulatory_analyst import RegulatoryAnalystAgent
from src.agents.policy_mapper import PolicyMapperAgent
from src.agents.evidence_validator import EvidenceValidatorAgent
from src.agents.risk_scorer import RiskScorerAgent
from src.agents.executive_reporter import ExecutiveReporterAgent


class TestRegulatoryAnalystAgent:
    def test_agent_initialization(self):
        mock_doc_service = Mock()
        mock_rag_service = Mock()
        agent = RegulatoryAnalystAgent(mock_doc_service, mock_rag_service)

        assert agent.name == "Regulatory Analyst"
        assert agent.role == "Senior Regulatory Compliance Analyst"
        assert len(agent.tools) == 3

    def test_extract_requirements(self):
        mock_doc_service = Mock()
        mock_rag_service = Mock()
        mock_rag_service.extract_entities.return_value = [
            {"type": "requirement", "text": "Must comply", "section": "1.1"}
        ]

        agent = RegulatoryAnalystAgent(mock_doc_service, mock_rag_service)
        result = agent._extract_requirements("Sample document content")

        assert "requirements" in result
        assert len(result["requirements"]) > 0


class TestPolicyMapperAgent:
    def test_agent_initialization(self):
        mock_rag_service = Mock()
        agent = PolicyMapperAgent(mock_rag_service)

        assert agent.name == "Policy Mapper"
        assert len(agent.tools) == 3

    def test_identify_gaps(self):
        mock_rag_service = Mock()
        agent = PolicyMapperAgent(mock_rag_service)

        policies = [{"id": "1", "name": "Policy 1", "content": "Content"}]
        regulations = [{"id": "1", "name": "Reg 1", "requirement": "Requirement"}]

        gaps = agent._identify_gaps(policies, regulations)
        assert isinstance(gaps, list)


class TestEvidenceValidatorAgent:
    def test_agent_initialization(self):
        agent = EvidenceValidatorAgent()

        assert agent.name == "Evidence Validator"
        assert len(agent.tools) == 4

    def test_assess_quality(self):
        agent = EvidenceValidatorAgent()
        evidence = {
            "id": "123",
            "type": "audit_log",
            "timestamp": "2024-01-01T00:00:00",
            "content": "Sample content"
        }

        result = agent._assess_quality(evidence)

        assert "completeness_score" in result
        assert "accuracy_score" in result
        assert "overall_quality" in result


class TestRiskScorerAgent:
    def test_agent_initialization(self):
        agent = RiskScorerAgent()

        assert agent.name == "Risk Scorer"
        assert len(agent.tools) == 5

    def test_calculate_risk_score(self):
        agent = RiskScorerAgent()
        gap = {
            "id": "gap1",
            "description": "Sample gap",
            "regulation_type": "GDPR"
        }
        context = {"business_criticality": "high"}

        result = agent._calculate_risk_score(gap, context)

        assert "risk_level" in result
        assert "base_risk_score" in result
        assert "adjusted_risk_score" in result


class TestExecutiveReporterAgent:
    def test_agent_initialization(self):
        agent = ExecutiveReporterAgent()

        assert agent.name == "Executive Reporter"
        assert len(agent.tools) == 4

    def test_generate_summary(self):
        agent = ExecutiveReporterAgent()
        data = {
            "compliance_rate": 0.92,
            "critical_gaps": [],
            "regulation_count": 12,
            "remediation_cost": 2500000
        }

        result = agent._generate_summary(data)

        assert "executive_overview" in result
        assert "compliance_status" in result
        assert "key_findings" in result