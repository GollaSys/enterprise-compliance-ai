"""
Pydantic schemas for request/response models
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class RegulationType(str, Enum):
    GDPR = "GDPR"
    SOX = "SOX"
    FINRA = "FINRA"
    SEC = "SEC"
    HIPAA = "HIPAA"
    PCI_DSS = "PCI_DSS"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class ComplianceRequest(BaseModel):
    regulation_type: RegulationType
    document_ids: List[str]
    policy_ids: Optional[List[str]] = None
    include_evidence: bool = True
    generate_report: bool = True


class ComplianceResponse(BaseModel):
    compliance_id: str
    status: str
    message: str
    estimated_time: Optional[int] = None


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str


class ReportRequest(BaseModel):
    report_type: str = Field(..., description="Type of report (executive, technical, audit)")
    period: str = Field(..., description="Reporting period (Q1, Q2, Q3, Q4, Annual)")
    filters: Optional[Dict[str, Any]] = None
    include_charts: bool = True
    format: str = "pdf"


class ReportResponse(BaseModel):
    report_id: str
    status: str
    message: str
    download_url: Optional[str] = None


class AgentStatus(BaseModel):
    agent_id: str
    name: str
    status: str
    tasks_completed: int
    last_active: Optional[datetime] = None


class DashboardMetrics(BaseModel):
    overall_compliance: float
    active_risks: int
    open_gaps: int
    audit_readiness: float
    trends: Dict[str, List[Dict]]
    risk_distribution: Dict[str, int]
    regulatory_status: List[Dict]


class Gap(BaseModel):
    id: str
    description: str
    severity: str
    regulation: str
    remediation: str
    estimated_cost: Optional[float] = None
    timeline: Optional[str] = None


class Risk(BaseModel):
    id: str
    level: RiskLevel
    score: float
    description: str
    mitigation: str
    status: str = "open"
    owner: Optional[str] = None


class Policy(BaseModel):
    id: str
    name: str
    version: str
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: str = "active"
    coverage: List[str] = []


class Evidence(BaseModel):
    id: str
    type: str
    source: str
    timestamp: datetime
    content: Optional[str] = None
    validation_status: str = "pending"
    hash: Optional[str] = None


class ComplianceResult(BaseModel):
    compliance_id: str
    regulation_type: RegulationType
    compliance_score: float
    gaps: List[Gap]
    risks: List[Risk]
    evidence_summary: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    executive_summary: str


class ValidationResult(BaseModel):
    evidence_id: str
    validation_status: str
    completeness: float
    accuracy: float
    matched_requirements: List[str]
    issues: List[str]


class GapAnalysisResult(BaseModel):
    gaps: List[Gap]
    coverage_score: float
    total_gaps: int
    critical_gaps: int
    remediation_plan: Optional[Dict] = None


class RiskAssessment(BaseModel):
    assessments: List[Dict[str, Any]]
    total_risk_score: float
    recommended_priority: str
    mitigation_timeline: str
    estimated_budget: float