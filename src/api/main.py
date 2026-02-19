from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our services and agents
from src.services.orchestrator import ComplianceOrchestrator
from src.services.storage_service import StorageService
from src.models.schemas import (
    ComplianceRequest, ComplianceResponse,
    DocumentUploadResponse, ReportRequest, ReportResponse,
    AgentStatus, DashboardMetrics
)

# Initialize services
storage_service = StorageService()
orchestrator = ComplianceOrchestrator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Compliance AI Platform...")
    # Initialize services
    await storage_service.initialize()
    await orchestrator.initialize()
    yield
    # Cleanup
    logger.info("Shutting down Compliance AI Platform...")
    await storage_service.cleanup()

app = FastAPI(
    title="Enterprise Compliance AI Platform",
    description="AI-powered multi-agent compliance platform using CrewAI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health and Status Endpoints
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
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "database": await storage_service.check_health(),
            "agents": orchestrator.get_status(),
            "vector_store": "operational"
        },
        "timestamp": datetime.now().isoformat()
    }

# Dashboard Endpoints
@app.get("/api/v1/dashboard/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """Get real-time dashboard metrics"""
    metrics = await orchestrator.get_metrics()
    return metrics

@app.get("/api/v1/dashboard/activities")
async def get_recent_activities():
    """Get recent system activities"""
    activities = await storage_service.get_recent_activities(limit=10)
    return {"activities": activities}

# Document Management Endpoints
@app.post("/api/v1/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = "general",
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Upload and process compliance documents"""
    try:
        # Validate file
        if file.size > 100 * 1024 * 1024:  # 100MB limit
            raise HTTPException(status_code=413, detail="File too large")

        # Save document
        content = await file.read()
        doc_id = await storage_service.save_document(
            filename=file.filename,
            content=content,
            doc_type=doc_type
        )

        # Process in background
        background_tasks.add_task(
            orchestrator.process_document,
            doc_id,
            content,
            doc_type
        )

        return DocumentUploadResponse(
            document_id=doc_id,
            filename=file.filename,
            status="processing",
            message="Document uploaded and processing started"
        )
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/documents")
async def list_documents(
    doc_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """List all documents with optional filtering"""
    documents = await storage_service.list_documents(
        doc_type=doc_type,
        status=status,
        limit=limit
    )
    return {"documents": documents, "total": len(documents)}

# Compliance Analysis Endpoints
@app.post("/api/v1/compliance/analyze", response_model=ComplianceResponse)
async def analyze_compliance(
    request: ComplianceRequest,
    background_tasks: BackgroundTasks
):
    """Run comprehensive compliance analysis using AI agents"""
    try:
        # Create analysis job
        analysis_id = await orchestrator.create_analysis(
            regulation_type=request.regulation_type,
            document_ids=request.document_ids,
            policy_ids=request.policy_ids
        )

        # Run analysis in background
        background_tasks.add_task(
            orchestrator.run_compliance_analysis,
            analysis_id,
            request.dict()
        )

        return ComplianceResponse(
            compliance_id=analysis_id,
            status="processing",
            message="Compliance analysis initiated",
            estimated_time=120  # seconds
        )
    except Exception as e:
        logger.error(f"Compliance analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/compliance/status/{compliance_id}")
async def get_compliance_status(compliance_id: str):
    """Get status of compliance analysis"""
    status = await orchestrator.get_analysis_status(compliance_id)
    if not status:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return status

@app.get("/api/v1/compliance/results/{compliance_id}")
async def get_compliance_results(compliance_id: str):
    """Get detailed results of compliance analysis"""
    results = await orchestrator.get_analysis_results(compliance_id)
    if not results:
        raise HTTPException(status_code=404, detail="Results not found")
    return results

# Policy Management Endpoints
@app.get("/api/v1/policies")
async def list_policies():
    """List all organizational policies"""
    policies = await storage_service.list_policies()
    return {"policies": policies}

@app.post("/api/v1/policies")
async def create_policy(
    name: str,
    content: str,
    version: str = "1.0"
):
    """Create a new policy"""
    policy_id = await storage_service.create_policy(
        name=name,
        content=content,
        version=version
    )
    return {"policy_id": policy_id, "status": "created"}

# Risk Assessment Endpoints
@app.get("/api/v1/risks")
async def list_risks(
    level: Optional[str] = None,
    status: Optional[str] = "open"
):
    """List identified risks"""
    risks = await orchestrator.get_risks(level=level, status=status)
    return {"risks": risks, "total": len(risks)}

@app.post("/api/v1/risks/assess")
async def assess_risks(gap_ids: List[str]):
    """Assess risks for identified gaps"""
    risk_assessment = await orchestrator.assess_risks(gap_ids)
    return risk_assessment

# Agent Management Endpoints
@app.get("/api/v1/agents/status", response_model=List[AgentStatus])
async def get_agents_status():
    """Get status of all AI agents"""
    return orchestrator.get_agents_status()

@app.post("/api/v1/agents/{agent_name}/execute")
async def execute_agent_task(
    agent_name: str,
    task_data: Dict[str, Any]
):
    """Execute a specific task with an agent"""
    try:
        result = await orchestrator.execute_agent_task(agent_name, task_data)
        return {"status": "completed", "result": result}
    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Report Generation Endpoints
@app.post("/api/v1/reports/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks
):
    """Generate compliance reports"""
    try:
        report_id = await orchestrator.create_report(
            report_type=request.report_type,
            period=request.period,
            filters=request.filters
        )

        background_tasks.add_task(
            orchestrator.generate_report,
            report_id,
            request.dict()
        )

        return ReportResponse(
            report_id=report_id,
            status="generating",
            message="Report generation started"
        )
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/reports")
async def list_reports(
    report_type: Optional[str] = None,
    limit: int = 50
):
    """List generated reports"""
    reports = await storage_service.list_reports(
        report_type=report_type,
        limit=limit
    )
    return {"reports": reports}

@app.get("/api/v1/reports/{report_id}")
async def get_report(report_id: str):
    """Get specific report details"""
    report = await storage_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

# Regulation Management
@app.get("/api/v1/regulations")
async def list_regulations():
    """List supported regulations"""
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

# Evidence Validation
@app.post("/api/v1/evidence/validate")
async def validate_evidence(
    evidence_ids: List[str],
    requirements: List[str]
):
    """Validate evidence against requirements"""
    validation_results = await orchestrator.validate_evidence(
        evidence_ids=evidence_ids,
        requirements=requirements
    )
    return validation_results

# Gap Analysis
@app.post("/api/v1/gaps/analyze")
async def analyze_gaps(
    regulation_ids: List[str],
    policy_ids: List[str]
):
    """Perform gap analysis between regulations and policies"""
    gaps = await orchestrator.analyze_gaps(
        regulation_ids=regulation_ids,
        policy_ids=policy_ids
    )
    return gaps

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )