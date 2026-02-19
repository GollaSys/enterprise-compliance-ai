from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import structlog
from datetime import datetime, timedelta

router = APIRouter()
logger = structlog.get_logger()

@router.get("/metrics")
async def get_dashboard_metrics():
    try:
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
            },
            "regulatory_status": [
                {"name": "GDPR", "compliance": 92, "target": 95},
                {"name": "SOX", "compliance": 88, "target": 90},
                {"name": "FINRA", "compliance": 94, "target": 95},
                {"name": "SEC", "compliance": 85, "target": 90}
            ]
        }
    except Exception as e:
        logger.error(f"Dashboard metrics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activities")
async def get_recent_activities():
    try:
        return {
            "activities": [
                {
                    "id": "1",
                    "type": "audit_completed",
                    "title": "GDPR Audit Completed",
                    "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "severity": "success"
                },
                {
                    "id": "2",
                    "type": "risk_identified",
                    "title": "New Risk Identified",
                    "timestamp": (datetime.now() - timedelta(hours=5)).isoformat(),
                    "severity": "warning"
                },
                {
                    "id": "3",
                    "type": "policy_review",
                    "title": "Policy Review Scheduled",
                    "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                    "severity": "info"
                },
                {
                    "id": "4",
                    "type": "gap_detected",
                    "title": "Critical Gap Detected",
                    "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                    "severity": "error"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Activities retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_alerts():
    try:
        return {
            "alerts": [
                {
                    "id": "ALT-001",
                    "level": "critical",
                    "title": "SOX Compliance Below Threshold",
                    "description": "Current compliance at 88%, below required 90%",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "id": "ALT-002",
                    "level": "warning",
                    "title": "Policy Review Due",
                    "description": "3 policies require quarterly review",
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "total": 2
        }
    except Exception as e:
        logger.error(f"Alerts retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))