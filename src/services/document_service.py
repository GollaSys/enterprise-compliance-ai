from typing import List, Dict, Any, Optional
import os
import json
from datetime import datetime
from pathlib import Path
import structlog
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = structlog.get_logger()


class DocumentService:
    def __init__(self, storage_path: str = "./data/documents"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.storage_path / "metadata"
        self.metadata_path.mkdir(exist_ok=True)
        self.logger = logger.bind(service="DocumentService")
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        doc_type: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        try:
            doc_id = self._generate_doc_id(filename)
            file_path = self.storage_path / doc_id

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._save_file,
                file_path,
                file_content
            )

            doc_hash = hashlib.sha256(file_content).hexdigest()

            doc_metadata = {
                "id": doc_id,
                "filename": filename,
                "doc_type": doc_type,
                "upload_date": datetime.now().isoformat(),
                "file_size": len(file_content),
                "hash": doc_hash,
                "status": "pending_processing",
                **(metadata or {})
            }

            await self._save_metadata(doc_id, doc_metadata)

            self.logger.info(
                f"Document uploaded",
                doc_id=doc_id,
                filename=filename,
                doc_type=doc_type
            )

            return doc_metadata
        except Exception as e:
            self.logger.error(f"Document upload failed: {str(e)}")
            raise

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        try:
            metadata = await self._load_metadata(doc_id)
            if not metadata:
                return None

            file_path = self.storage_path / doc_id
            if not file_path.exists():
                self.logger.warning(f"Document file missing", doc_id=doc_id)
                return None

            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                self.executor,
                self._read_file,
                file_path
            )

            return {
                **metadata,
                "content": content
            }
        except Exception as e:
            self.logger.error(f"Document retrieval failed: {str(e)}")
            return None

    async def list_documents(
        self,
        doc_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        try:
            all_docs = []

            for metadata_file in self.metadata_path.glob("*.json"):
                metadata = await self._load_metadata(metadata_file.stem)

                if doc_type and metadata.get("doc_type") != doc_type:
                    continue
                if status and metadata.get("status") != status:
                    continue

                all_docs.append(metadata)

            all_docs.sort(key=lambda x: x.get("upload_date", ""), reverse=True)

            return all_docs[offset:offset + limit]
        except Exception as e:
            self.logger.error(f"Document listing failed: {str(e)}")
            return []

    async def update_document_status(
        self,
        doc_id: str,
        status: str,
        processing_results: Optional[Dict] = None
    ) -> bool:
        try:
            metadata = await self._load_metadata(doc_id)
            if not metadata:
                return False

            metadata["status"] = status
            metadata["last_updated"] = datetime.now().isoformat()

            if processing_results:
                metadata["processing_results"] = processing_results

            await self._save_metadata(doc_id, metadata)

            self.logger.info(
                f"Document status updated",
                doc_id=doc_id,
                status=status
            )

            return True
        except Exception as e:
            self.logger.error(f"Status update failed: {str(e)}")
            return False

    async def delete_document(self, doc_id: str) -> bool:
        try:
            file_path = self.storage_path / doc_id
            metadata_path = self.metadata_path / f"{doc_id}.json"

            if file_path.exists():
                file_path.unlink()

            if metadata_path.exists():
                metadata_path.unlink()

            self.logger.info(f"Document deleted", doc_id=doc_id)
            return True
        except Exception as e:
            self.logger.error(f"Document deletion failed: {str(e)}")
            return False

    async def search_documents(self, query: str) -> List[Dict[str, Any]]:
        try:
            results = []
            query_lower = query.lower()

            for metadata_file in self.metadata_path.glob("*.json"):
                metadata = await self._load_metadata(metadata_file.stem)

                if (query_lower in metadata.get("filename", "").lower() or
                    query_lower in metadata.get("doc_type", "").lower() or
                    query_lower in str(metadata.get("metadata", {})).lower()):

                    results.append(metadata)

            return results
        except Exception as e:
            self.logger.error(f"Document search failed: {str(e)}")
            return []

    async def get_document_stats(self) -> Dict[str, Any]:
        try:
            total_docs = 0
            docs_by_type = {}
            docs_by_status = {}
            total_size = 0

            for metadata_file in self.metadata_path.glob("*.json"):
                metadata = await self._load_metadata(metadata_file.stem)

                total_docs += 1
                doc_type = metadata.get("doc_type", "unknown")
                status = metadata.get("status", "unknown")

                docs_by_type[doc_type] = docs_by_type.get(doc_type, 0) + 1
                docs_by_status[status] = docs_by_status.get(status, 0) + 1
                total_size += metadata.get("file_size", 0)

            return {
                "total_documents": total_docs,
                "documents_by_type": docs_by_type,
                "documents_by_status": docs_by_status,
                "total_storage_size": total_size,
                "average_document_size": total_size / total_docs if total_docs > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Stats generation failed: {str(e)}")
            return {}

    def _generate_doc_id(self, filename: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        return f"{timestamp}_{filename_hash}"

    def _save_file(self, path: Path, content: bytes) -> None:
        with open(path, "wb") as f:
            f.write(content)

    def _read_file(self, path: Path) -> bytes:
        with open(path, "rb") as f:
            return f.read()

    async def _save_metadata(self, doc_id: str, metadata: Dict) -> None:
        metadata_file = self.metadata_path / f"{doc_id}.json"
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._write_json,
            metadata_file,
            metadata
        )

    async def _load_metadata(self, doc_id: str) -> Optional[Dict]:
        metadata_file = self.metadata_path / f"{doc_id}.json"
        if not metadata_file.exists():
            return None

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._read_json,
            metadata_file
        )

    def _write_json(self, path: Path, data: Dict) -> None:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _read_json(self, path: Path) -> Dict:
        with open(path, "r") as f:
            return json.load(f)