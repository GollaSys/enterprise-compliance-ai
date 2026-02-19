from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import structlog

from src.agents.regulatory_analyst import RegulatoryAnalystAgent
from src.agents.policy_mapper import PolicyMapperAgent
from src.agents.evidence_validator import EvidenceValidatorAgent
from src.agents.risk_scorer import RiskScorerAgent
from src.agents.executive_reporter import ExecutiveReporterAgent
from src.services.rag_service import RAGService
from src.services.document_service import DocumentService

router = APIRouter()
logger = structlog.get_logger()

class ComplianceRequest(BaseModel):
    regulation_type: str
    document_ids: List[str]
    policy_ids: Optional[List[str]] = None
    evidence_ids: Optional[List[str]] = None

class ComplianceResponse(BaseModel):
    compliance_id: str
    status: str
    compliance_score: float
    gaps: List[Dict]
    risks: List[Dict]
    recommendations: List[Dict]

class GapAnalysisRequest(BaseModel):
    regulation_ids: List[str]
    policy_ids: List[str]

class RiskAssessmentRequest(BaseModel):
    gap_ids: List[str]
    context: Dict[str, Any]

@router.post("/analyze", response_model=ComplianceResponse)
async def analyze_compliance(
    request: ComplianceRequest,
    background_tasks: BackgroundTasks
):
    try:
        rag_service = RAGService()
        doc_service = DocumentService()

        regulatory_agent = RegulatoryAnalystAgent(doc_service, rag_service)

        compliance_id = f"COMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        background_tasks.add_task(
            run_compliance_analysis,
            compliance_id,
            request.dict()
        )

        return ComplianceResponse(
            compliance_id=compliance_id,
            status="processing",
            compliance_score=0.0,
            gaps=[],
            risks=[],
            recommendations=[]
        )
    except Exception as e:
        logger.error(f"Compliance analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{compliance_id}")
async def get_compliance_status(compliance_id: str):
    try:
        return {
            "compliance_id": compliance_id,
            "status": "completed",
            "completion_time": datetime.now().isoformat(),
            "results_available": True
        }
    except Exception as e:
        logger.error(f"Status retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gaps/analyze")
async def analyze_gaps(request: GapAnalysisRequest):
    try:
        rag_service = RAGService()
        policy_mapper = PolicyMapperAgent(rag_service)

        mock_policies = [{"id": p_id, "name": f"Policy {p_id}", "content": "Policy content"} for p_id in request.policy_ids]
        mock_regulations = [{"id": r_id, "name": f"Regulation {r_id}", "content": "Regulation content"} for r_id in request.regulation_ids]

        task = policy_mapper.create_task(mock_policies, mock_regulations)

        gaps = policy_mapper._identify_gaps(mock_policies, mock_regulations)

        return {
            "gap_count": len(gaps),
            "gaps": gaps,
            "coverage_summary": {
                "fully_covered": 5,
                "partially_covered": 3,
                "uncovered": len(gaps)
            }
        }
    except Exception as e:
        logger.error(f"Gap analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evidence/validate")
async def validate_evidence(evidence_ids: List[str]):
    try:
        validator = EvidenceValidatorAgent()

        validation_results = []
        for evidence_id in evidence_ids:
            mock_evidence = {
                "id": evidence_id,
                "type": "audit_log",
                "timestamp": datetime.now().isoformat(),
                "content": "Evidence content"
            }

            result = validator._assess_quality(mock_evidence)
            validation_results.append({
                "evidence_id": evidence_id,
                "validation_result": result
            })

        return {
            "validated_count": len(validation_results),
            "results": validation_results
        }
    except Exception as e:
        logger.error(f"Evidence validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/risks/assess")
async def assess_risks(request: RiskAssessmentRequest):
    try:
        risk_scorer = RiskScorerAgent()

        risk_results = []
        for gap_id in request.gap_ids:
            mock_gap = {
                "id": gap_id,
                "description": f"Gap {gap_id}",
                "regulation_type": "GDPR"
            }

            score = risk_scorer._calculate_risk_score(mock_gap, request.context)
            risk_results.append(score)

        risk_matrix = risk_scorer._generate_risk_matrix(risk_results)

        return {
            "risk_count": len(risk_results),
            "risk_scores": risk_results,
            "risk_matrix": risk_matrix
        }
    except Exception as e:
        logger.error(f"Risk assessment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regulations")
async def list_regulations():
    return {
        "regulations": [
            {"id": "REG-001", "name": "GDPR", "jurisdiction": "EU", "status": "active"},
            {"id": "REG-002", "name": "SOX", "jurisdiction": "US", "status": "active"},
            {"id": "REG-003", "name": "FINRA", "jurisdiction": "US", "status": "active"},
            {"id": "REG-004", "name": "SEC", "jurisdiction": "US", "status": "active"}
        ]
    }

@router.get("/policies")
async def list_policies():
    return {
        "policies": [
            {"id": "POL-001", "name": "Data Protection Policy", "version": "2.0", "status": "active"},
            {"id": "POL-002", "name": "Access Control Policy", "version": "1.5", "status": "active"},
            {"id": "POL-003", "name": "Incident Response Policy", "version": "3.1", "status": "active"},
            {"id": "POL-004", "name": "Business Continuity Policy", "version": "2.2", "status": "active"}
        ]
    }

async def run_compliance_analysis(compliance_id: str, request_data: Dict):
    logger.info(f"Running compliance analysis", compliance_id=compliance_id)