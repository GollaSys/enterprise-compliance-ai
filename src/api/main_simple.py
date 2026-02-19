from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
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

# Store data in memory for testing
documents_store = []
compliance_analyses = []
reports_store = []

class ComplianceRequest(BaseModel):
    regulation_type: str
    document_ids: List[str]

@app.get("/")
async def root():
    return {
        "name": "Enterprise Compliance AI Platform",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Dashboard endpoints
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

# Compliance endpoints
@app.post("/api/v1/compliance/analyze")
async def analyze_compliance(request: ComplianceRequest):
    analysis_id = f"COMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    analysis = {
        "compliance_id": analysis_id,
        "status": "completed",
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

    compliance_analyses.append(analysis)
    return analysis

@app.get("/api/v1/compliance/regulations")
async def list_regulations():
    return {
        "regulations": [
            {"id": "GDPR", "name": "General Data Protection Regulation", "jurisdiction": "EU"},
            {"id": "SOX", "name": "Sarbanes-Oxley Act", "jurisdiction": "US"},
            {"id": "FINRA", "name": "Financial Industry Regulatory Authority", "jurisdiction": "US"}
        ]
    }

# Document endpoints
@app.post("/api/v1/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    doc_id = f"DOC-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    document = {
        "id": doc_id,
        "filename": file.filename,
        "upload_date": datetime.now().isoformat(),
        "status": "processed",
        "size": file.size if hasattr(file, 'size') else 0
    }

    documents_store.append(document)

    return {
        "message": "Document uploaded successfully",
        "document": document
    }

@app.get("/api/v1/documents")
async def list_documents():
    return {
        "documents": documents_store,
        "total": len(documents_store)
    }

# Agents endpoints
@app.get("/api/v1/agents/status")
async def get_agents_status():
    return {
        "agents": [
            {"name": "Regulatory Analyst", "status": "active", "tasks_completed": 42},
            {"name": "Policy Mapper", "status": "active", "tasks_completed": 38},
            {"name": "Evidence Validator", "status": "active", "tasks_completed": 56},
            {"name": "Risk Scorer", "status": "active", "tasks_completed": 29},
            {"name": "Executive Reporter", "status": "active", "tasks_completed": 15}
        ],
        "overall_status": "operational"
    }

# Reports endpoints
@app.post("/api/v1/reports/generate")
async def generate_report(report_type: str, period: str):
    report_id = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    report = {
        "id": report_id,
        "type": report_type,
        "period": period,
        "generated_at": datetime.now().isoformat(),
        "status": "completed",
        "content": {
            "executive_summary": "Compliance status is strong with 92% overall compliance.",
            "key_findings": ["GDPR compliance at 95%", "SOX compliance improved by 10%"],
            "recommendations": ["Strengthen access controls", "Update privacy policies"]
        }
    }

    reports_store.append(report)
    return report

@app.get("/api/v1/reports")
async def list_reports():
    return {
        "reports": reports_store,
        "total": len(reports_store)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)