from typing import List, Dict, Any, Optional
import os
import structlog
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import chromadb
from chromadb.config import Settings

logger = structlog.get_logger()


class RAGService:
    def __init__(self, collection_name: str = "compliance_docs"):
        self.collection_name = collection_name
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        self.chroma_client = chromadb.Client(Settings(
            chroma_server_host=os.getenv("CHROMA_HOST", "localhost"),
            chroma_server_http_port=int(os.getenv("CHROMA_PORT", "8000")),
            anonymized_telemetry=False
        ))

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        self._initialize_collection()
        self.logger = logger.bind(service="RAGService")

    def _initialize_collection(self):
        try:
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Compliance documents and regulations"}
            )
            self.vector_store = Chroma(
                client=self.chroma_client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )
            self.logger.info(f"Initialized collection: {self.collection_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize collection: {str(e)}")
            raise

    def ingest_document(self, content: str, metadata: Dict[str, Any]) -> List[str]:
        try:
            chunks = self.text_splitter.split_text(content)

            documents = [
                Document(
                    page_content=chunk,
                    metadata={
                        **metadata,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                )
                for i, chunk in enumerate(chunks)
            ]

            ids = self.vector_store.add_documents(documents)

            self.logger.info(
                f"Ingested document",
                doc_id=metadata.get("doc_id"),
                chunks=len(chunks)
            )

            return ids
        except Exception as e:
            self.logger.error(f"Document ingestion failed: {str(e)}")
            raise

    def semantic_search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        try:
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=top_k,
                filter=filters
            )

            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                    "source": doc.metadata.get("source", "unknown")
                })

            self.logger.info(
                f"Search completed",
                query=query[:50],
                results=len(formatted_results)
            )

            return formatted_results
        except Exception as e:
            self.logger.error(f"Semantic search failed: {str(e)}")
            return []

    def extract_entities(
        self,
        text: str,
        entity_types: List[str]
    ) -> List[Dict[str, Any]]:
        entities = []

        entity_patterns = {
            "requirement": ["shall", "must", "required", "mandatory"],
            "obligation": ["obligated", "responsible", "duty", "liable"],
            "control": ["control", "measure", "safeguard", "protection"],
            "deadline": ["by", "before", "within", "no later than"]
        }

        for entity_type in entity_types:
            if entity_type in entity_patterns:
                patterns = entity_patterns[entity_type]
                for pattern in patterns:
                    if pattern.lower() in text.lower():
                        start_idx = text.lower().find(pattern.lower())
                        end_idx = min(start_idx + 200, len(text))

                        entities.append({
                            "type": entity_type,
                            "text": text[start_idx:end_idx],
                            "pattern": pattern,
                            "position": start_idx
                        })

        return entities

    def get_embeddings(self, text: str) -> List[float]:
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {str(e)}")
            return []

    def update_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        try:
            self.collection.delete(ids=[doc_id])

            new_ids = self.ingest_document(content, metadata)

            self.logger.info(f"Updated document", doc_id=doc_id)
            return bool(new_ids)
        except Exception as e:
            self.logger.error(f"Document update failed: {str(e)}")
            return False

    def delete_document(self, doc_id: str) -> bool:
        try:
            self.collection.delete(ids=[doc_id])
            self.logger.info(f"Deleted document", doc_id=doc_id)
            return True
        except Exception as e:
            self.logger.error(f"Document deletion failed: {str(e)}")
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        try:
            count = self.collection.count()

            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "embedding_model": "text-embedding-ada-002",
                "chunk_size": self.text_splitter.chunk_size
            }
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {str(e)}")
            return {}