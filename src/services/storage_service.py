"""
Storage Service - Handles all data persistence operations
"""
import os
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import aiofiles
import logging

logger = logging.getLogger(__name__)


class StorageService:
    """Manages data storage for the compliance platform"""

    def __init__(self, storage_path: str = "./data"):
        self.storage_path = Path(storage_path)
        self.documents = {}
        self.policies = {}
        self.reports = {}
        self.activities = []

    async def initialize(self):
        """Initialize storage directories"""
        try:
            # Create necessary directories
            (self.storage_path / "documents").mkdir(parents=True, exist_ok=True)
            (self.storage_path / "policies").mkdir(parents=True, exist_ok=True)
            (self.storage_path / "reports").mkdir(parents=True, exist_ok=True)
            (self.storage_path / "metadata").mkdir(parents=True, exist_ok=True)

            # Load existing data
            await self._load_metadata()

            logger.info("Storage service initialized")
        except Exception as e:
            logger.error(f"Storage initialization failed: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        # Save any pending data
        await self._save_metadata()

    async def check_health(self) -> str:
        """Check storage health"""
        try:
            # Check if directories exist
            if self.storage_path.exists():
                return "operational"
            return "degraded"
        except:
            return "error"

    async def save_document(
        self,
        filename: str,
        content: bytes,
        doc_type: str
    ) -> str:
        """Save a document to storage"""
        doc_id = f"DOC-{uuid.uuid4().hex[:8]}"

        try:
            # Save file
            file_path = self.storage_path / "documents" / f"{doc_id}_{filename}"
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)

            # Save metadata
            self.documents[doc_id] = {
                "id": doc_id,
                "filename": filename,
                "doc_type": doc_type,
                "file_path": str(file_path),
                "upload_date": datetime.now().isoformat(),
                "status": "uploaded",
                "size": len(content)
            }

            # Add activity
            self._add_activity(
                "document_uploaded",
                f"Document {filename} uploaded",
                {"doc_id": doc_id}
            )

            await self._save_metadata()
            return doc_id

        except Exception as e:
            logger.error(f"Failed to save document: {str(e)}")
            raise

    async def list_documents(
        self,
        doc_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """List documents with optional filtering"""
        docs = list(self.documents.values())

        # Apply filters
        if doc_type:
            docs = [d for d in docs if d.get("doc_type") == doc_type]
        if status:
            docs = [d for d in docs if d.get("status") == status]

        # Sort by upload date (newest first)
        docs.sort(key=lambda x: x.get("upload_date", ""), reverse=True)

        return docs[:limit]

    async def create_policy(
        self,
        name: str,
        content: str,
        version: str
    ) -> str:
        """Create a new policy"""
        policy_id = f"POL-{uuid.uuid4().hex[:8]}"

        self.policies[policy_id] = {
            "id": policy_id,
            "name": name,
            "content": content,
            "version": version,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }

        self._add_activity(
            "policy_created",
            f"Policy '{name}' created",
            {"policy_id": policy_id}
        )

        await self._save_metadata()
        return policy_id

    async def list_policies(self) -> List[Dict]:
        """List all policies"""
        policies = list(self.policies.values())
        policies.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return policies

    async def list_reports(
        self,
        report_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List reports with optional filtering"""
        reports = list(self.reports.values())

        if report_type:
            reports = [r for r in reports if r.get("type") == report_type]

        reports.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return reports[:limit]

    async def get_report(self, report_id: str) -> Optional[Dict]:
        """Get a specific report"""
        return self.reports.get(report_id)

    async def get_recent_activities(self, limit: int = 10) -> List[Dict]:
        """Get recent system activities"""
        return self.activities[-limit:][::-1]  # Return newest first

    def _add_activity(self, activity_type: str, title: str, metadata: Dict = None):
        """Add an activity to the log"""
        activity = {
            "id": str(uuid.uuid4()),
            "type": activity_type,
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.activities.append(activity)

        # Keep only last 1000 activities
        if len(self.activities) > 1000:
            self.activities = self.activities[-1000:]

    async def _save_metadata(self):
        """Save metadata to disk"""
        try:
            metadata = {
                "documents": self.documents,
                "policies": self.policies,
                "reports": self.reports,
                "activities": self.activities[-100:]  # Save only recent activities
            }

            metadata_file = self.storage_path / "metadata" / "storage.json"
            async with aiofiles.open(metadata_file, 'w') as f:
                await f.write(json.dumps(metadata, indent=2))

        except Exception as e:
            logger.error(f"Failed to save metadata: {str(e)}")

    async def _load_metadata(self):
        """Load metadata from disk"""
        try:
            metadata_file = self.storage_path / "metadata" / "storage.json"

            if metadata_file.exists():
                async with aiofiles.open(metadata_file, 'r') as f:
                    content = await f.read()
                    metadata = json.loads(content)

                    self.documents = metadata.get("documents", {})
                    self.policies = metadata.get("policies", {})
                    self.reports = metadata.get("reports", {})
                    self.activities = metadata.get("activities", [])

        except Exception as e:
            logger.error(f"Failed to load metadata: {str(e)}")
            # Continue with empty data