from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Enterprise Compliance AI Platform",
    description="AI-powered compliance platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory stores
documents_store: List[Dict] = []
compliance_analyses: Dict[str, Dict] = {}
reports_store: List[Dict] = []
policies_store: List[Dict] = []
risks_store: List[Dict] = [
    {"id": "RISK-001", "level": "high", "description": "Data breach risk", "status": "open", "score": 7.5},
    {"id": "RISK-002", "level": "medium", "description": "Access control gap", "status": "open", "score": 5.2},
    {"id": "RISK-003", "level": "critical", "description": "Unencrypted PII storage", "status": "open", "score": 9.1},
]


# --- Request Models ---

class ComplianceRequest(BaseModel):
    regulation_type: str
    document_ids: List[str] = []
    policy_ids: List[str] = []
    include_evidence: bool = False
    generate_report: bool = False


class ReportRequest(BaseModel):
    report_type: str
    period: str
    include_charts: bool = False
    format: str = "pdf"
    filters: Optional[Dict[str, Any]] = None


class EvidenceValidationRequest(BaseModel):
    evidence_ids: List[str]
    requirements: List[str]


class GapAnalysisRequest(BaseModel):
    regulation_ids: List[str]
    policy_ids: List[str]


# --- Health & Root ---

@app.get("/")
async def root():
    return {
        "name": "Enterprise Compliance AI Platform",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "Multi-agent compliance analysis",
            "Document processing",
            "Risk assessment",
            "Executive reporting",
            "Real-time monitoring"
        ]
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "database": "operational",
            "agents": "operational",
            "vector_store": "operational"
        },
        "timestamp": datetime.now().isoformat()
    }


# --- Dashboard ---

@app.get("/api/v1/dashboard/metrics")
async def get_dashboard_metrics():
    return {
        "overall_compliance": 92,
        "active_risks": 50,
        "open_gaps": 15,
        "audit_readiness": 87,
        "trends": {
            "compliance": [
                {"month": "Jan", "score": 78},
                {"month": "Feb", "score": 82},
                {"month": "Mar", "score": 85},
                {"month": "Apr", "score": 87},
                {"month": "May", "score": 89},
                {"month": "Jun", "score": 92}
            ]
        },
        "risk_distribution": {
            "critical": 3,
            "high": 8,
            "medium": 15,
            "low": 24
        }
    }


@app.get("/api/v1/dashboard/activities")
async def get_recent_activities():
    return {
        "activities": [
            {
                "id": "1",
                "type": "audit_completed",
                "title": "GDPR Audit Completed",
                "timestamp": datetime.now().isoformat(),
                "severity": "success"
            },
            {
                "id": "2",
                "type": "risk_identified",
                "title": "New Risk Identified",
                "timestamp": datetime.now().isoformat(),
                "severity": "warning"
            }
        ]
    }


# --- Documents ---

@app.post("/api/v1/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = "general"
):
    doc_id = f"DOC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"

    document = {
        "id": doc_id,
        "filename": file.filename,
        "doc_type": doc_type,
        "upload_date": datetime.now().isoformat(),
        "status": "processed",
        "size": file.size if hasattr(file, 'size') and file.size else 0
    }

    documents_store.append(document)

    return {
        "document_id": doc_id,
        "filename": file.filename,
        "status": "processing",
        "message": "Document uploaded and processing started"
    }


@app.get("/api/v1/documents")
async def list_documents(
    doc_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    filtered = documents_store
    if doc_type:
        filtered = [d for d in filtered if d.get("doc_type") == doc_type]
    if status:
        filtered = [d for d in filtered if d.get("status") == status]
    return {
        "documents": filtered[:limit],
        "total": len(filtered[:limit])
    }


# --- Compliance ---

@app.post("/api/v1/compliance/analyze")
async def analyze_compliance(request: ComplianceRequest):
    analysis_id = f"COMP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"

    analysis = {
        "compliance_id": analysis_id,
        "status": "completed",
        "regulation_type": request.regulation_type,
        "results": {
            "compliance_score": 92.5,
            "gaps": [
                {"id": "GAP-001", "description": "Missing data retention policy", "severity": "medium"},
                {"id": "GAP-002", "description": "Incomplete audit trails", "severity": "high"}
            ],
            "risks": [
                {"id": "RISK-001", "level": "high", "score": 7.5},
                {"id": "RISK-002", "level": "medium", "score": 5.2}
            ],
            "recommendations": [
                {"priority": "high", "action": "Update data retention policy"},
                {"priority": "medium", "action": "Implement automated audit logging"}
            ]
        }
    }

    compliance_analyses[analysis_id] = analysis
    return analysis


@app.get("/api/v1/compliance/status/{compliance_id}")
async def get_compliance_status(compliance_id: str):
    analysis = compliance_analyses.get(compliance_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {
        "compliance_id": compliance_id,
        "status": analysis["status"],
        "progress": 100
    }


@app.get("/api/v1/compliance/results/{compliance_id}")
async def get_compliance_results(compliance_id: str):
    analysis = compliance_analyses.get(compliance_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Results not found")
    return analysis


@app.get("/api/v1/compliance/regulations")
async def list_compliance_regulations():
    return {
        "regulations": [
            {"id": "GDPR", "name": "General Data Protection Regulation", "jurisdiction": "EU"},
            {"id": "SOX", "name": "Sarbanes-Oxley Act", "jurisdiction": "US"},
            {"id": "FINRA", "name": "Financial Industry Regulatory Authority", "jurisdiction": "US"}
        ]
    }


# --- Regulations (full version) ---

@app.get("/api/v1/regulations")
async def list_regulations():
    return {
        "regulations": [
            {
                "id": "GDPR",
                "name": "General Data Protection Regulation",
                "jurisdiction": "EU",
                "requirements": 127,
                "last_updated": "2024-01-15"
            },
            {
                "id": "SOX",
                "name": "Sarbanes-Oxley Act",
                "jurisdiction": "US",
                "requirements": 89,
                "last_updated": "2024-01-10"
            },
            {
                "id": "FINRA",
                "name": "Financial Industry Regulatory Authority",
                "jurisdiction": "US",
                "requirements": 156,
                "last_updated": "2024-01-12"
            },
            {
                "id": "SEC",
                "name": "Securities and Exchange Commission",
                "jurisdiction": "US",
                "requirements": 203,
                "last_updated": "2024-01-08"
            }
        ]
    }


# --- Policies ---

@app.get("/api/v1/policies")
async def list_policies():
    return {"policies": policies_store}


@app.post("/api/v1/policies")
async def create_policy(
    name: str,
    content: str,
    version: str = "1.0"
):
    policy_id = f"POL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"
    policy = {
        "policy_id": policy_id,
        "name": name,
        "content": content,
        "version": version,
        "created_at": datetime.now().isoformat(),
        "status": "active"
    }
    policies_store.append(policy)
    return {"policy_id": policy_id, "status": "created"}


# --- Risks ---

@app.get("/api/v1/risks")
async def list_risks(
    level: Optional[str] = None,
    status: Optional[str] = "open"
):
    filtered = risks_store
    if level:
        filtered = [r for r in filtered if r.get("level") == level]
    if status:
        filtered = [r for r in filtered if r.get("status") == status]
    return {"risks": filtered, "total": len(filtered)}


@app.post("/api/v1/risks/assess")
async def assess_risks(gap_ids: List[str]):
    assessments = []
    total_score = 0.0
    for gap_id in gap_ids:
        score = 7.5 if "001" in gap_id else 5.2
        total_score += score
        assessments.append({
            "gap_id": gap_id,
            "risk_level": "high" if score > 6 else "medium",
            "risk_score": score,
            "impact": "significant",
            "likelihood": "probable",
            "mitigation": f"Address {gap_id} within 30 days"
        })
    return {
        "assessments": assessments,
        "total_risk_score": round(total_score, 1),
        "overall_risk_level": "high" if total_score > 10 else "medium"
    }


# --- Evidence ---

@app.post("/api/v1/evidence/validate")
async def validate_evidence(request: EvidenceValidationRequest):
    validations = []
    for eid in request.evidence_ids:
        validations.append({
            "evidence_id": eid,
            "status": "valid",
            "completeness": 0.85,
            "accuracy": 0.92,
            "timeliness": "current"
        })
    return {
        "validations": validations,
        "total_validated": len(validations),
        "overall_validity": "satisfactory"
    }


# --- Gap Analysis ---

@app.post("/api/v1/gaps/analyze")
async def analyze_gaps(request: GapAnalysisRequest):
    gaps = []
    for reg_id in request.regulation_ids:
        gaps.append({
            "regulation_id": reg_id,
            "gap_id": f"GAP-{reg_id}-001",
            "description": f"Missing controls for {reg_id} requirement 4.2",
            "severity": "high" if reg_id == "GDPR" else "medium",
            "remediation": f"Implement {reg_id} control framework"
        })
    critical_count = sum(1 for g in gaps if g["severity"] == "high")
    return {
        "gaps": gaps,
        "total_gaps": len(gaps),
        "critical_gaps": critical_count,
        "coverage_score": 78.5
    }


# --- Agents ---

@app.get("/api/v1/agents/status")
async def get_agents_status():
    return [
        {"name": "Regulatory Analyst", "status": "active", "tasks_completed": 42},
        {"name": "Policy Mapper", "status": "active", "tasks_completed": 38},
        {"name": "Evidence Validator", "status": "active", "tasks_completed": 56},
        {"name": "Risk Scorer", "status": "active", "tasks_completed": 29},
        {"name": "Executive Reporter", "status": "active", "tasks_completed": 15}
    ]


@app.post("/api/v1/agents/{agent_name}/execute")
async def execute_agent_task(agent_name: str, task_data: Dict[str, Any]):
    return {
        "status": "completed",
        "agent": agent_name,
        "result": {
            "task_type": task_data.get("task_type", "analyze"),
            "findings": [
                {"id": "F-001", "description": "Sample finding", "severity": "medium"}
            ],
            "summary": f"Agent {agent_name} completed analysis successfully"
        }
    }


# --- Reports ---

@app.post("/api/v1/reports/generate")
async def generate_report(request: ReportRequest):
    report_id = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"

    report = {
        "report_id": report_id,
        "type": request.report_type,
        "period": request.period,
        "generated_at": datetime.now().isoformat(),
        "status": "completed",
        "message": "Report generation started",
        "content": {
            "executive_summary": "Compliance status is strong with 92% overall compliance.",
            "key_findings": ["GDPR compliance at 95%", "SOX compliance improved by 10%"],
            "recommendations": ["Strengthen access controls", "Update privacy policies"]
        }
    }

    reports_store.append(report)
    return report


@app.get("/api/v1/reports")
async def list_reports(
    report_type: Optional[str] = None,
    limit: int = 50
):
    filtered = reports_store
    if report_type:
        filtered = [r for r in filtered if r.get("type") == report_type]
    return {
        "reports": filtered[:limit],
        "total": len(filtered[:limit])
    }


@app.get("/api/v1/reports/{report_id}")
async def get_report(report_id: str):
    report = next((r for r in reports_store if r["report_id"] == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
