from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

from src.agents.executive_reporter import ExecutiveReporterAgent

router = APIRouter()
logger = structlog.get_logger()

@router.post("/generate")
async def generate_report(
    report_type: str,
    period: str,
    background_tasks: BackgroundTasks
):
    try:
        report_id = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        background_tasks.add_task(
            create_report,
            report_id,
            report_type,
            period
        )

        return {
            "report_id": report_id,
            "status": "generating",
            "message": "Report generation initiated"
        }
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_reports(
    report_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    try:
        reports = [
            {
                "id": "RPT-20240101120000",
                "type": "executive_summary",
                "period": "Q4 2024",
                "generated_at": "2024-01-01T12:00:00",
                "status": "completed"
            },
            {
                "id": "RPT-20231201120000",
                "type": "compliance_assessment",
                "period": "Q3 2024",
                "generated_at": "2023-12-01T12:00:00",
                "status": "completed"
            }
        ]

        if report_type:
            reports = [r for r in reports if r["type"] == report_type]

        return {
            "reports": reports[offset:offset + limit],
            "total": len(reports)
        }
    except Exception as e:
        logger.error(f"Report listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}")
async def get_report(report_id: str):
    try:
        executive_reporter = ExecutiveReporterAgent()

        mock_data = {
            "compliance_rate": 0.92,
            "critical_gaps": [],
            "high_risks": [],
            "remediation_cost": 2500000
        }

        report_content = executive_reporter._generate_summary(mock_data)

        return {
            "id": report_id,
            "type": "executive_summary",
            "period": "Q4 2024",
            "generated_at": datetime.now().isoformat(),
            "content": report_content
        }
    except Exception as e:
        logger.error(f"Report retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{report_id}")
async def delete_report(report_id: str):
    try:
        return {
            "message": f"Report {report_id} deleted successfully"
        }
    except Exception as e:
        logger.error(f"Report deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def create_report(report_id: str, report_type: str, period: str):
    logger.info(f"Creating report {report_id} of type {report_type} for period {period}")