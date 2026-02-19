from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import structlog
from crewai import Crew

from src.agents.regulatory_analyst import RegulatoryAnalystAgent
from src.agents.policy_mapper import PolicyMapperAgent
from src.agents.evidence_validator import EvidenceValidatorAgent
from src.agents.risk_scorer import RiskScorerAgent
from src.agents.executive_reporter import ExecutiveReporterAgent
from src.services.rag_service import RAGService
from src.services.document_service import DocumentService

router = APIRouter()
logger = structlog.get_logger()

@router.get("/status")
async def get_agents_status():
    try:
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
    except Exception as e:
        logger.error(f"Agent status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_agent_task(agent_name: str, task_data: Dict[str, Any]):
    try:
        rag_service = RAGService()
        doc_service = DocumentService()

        agent_map = {
            "regulatory_analyst": RegulatoryAnalystAgent(doc_service, rag_service),
            "policy_mapper": PolicyMapperAgent(rag_service),
            "evidence_validator": EvidenceValidatorAgent(),
            "risk_scorer": RiskScorerAgent(),
            "executive_reporter": ExecutiveReporterAgent()
        }

        agent = agent_map.get(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

        logger.info(f"Executing task for agent: {agent_name}")

        return {
            "agent": agent_name,
            "status": "task_completed",
            "result": {"message": f"Task executed by {agent_name}"}
        }
    except Exception as e:
        logger.error(f"Agent task execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_agent_metrics():
    try:
        return {
            "total_tasks": 180,
            "completed_tasks": 165,
            "failed_tasks": 5,
            "pending_tasks": 10,
            "average_completion_time": 4.2,
            "success_rate": 0.97
        }
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))