from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Float, JSON, Boolean, Integer, ForeignKey
from datetime import datetime
import uuid
from src.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

class ComplianceAnalysis(Base):
    __tablename__ = "compliance_analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String, default="pending")
    compliance_score = Column(Float, default=0.0)
    regulation_type = Column(String)
    results = Column(JSON)
    metadata = Column(JSON)

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    doc_type = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")
    file_path = Column(String)
    metadata = Column(JSON)

class Policy(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    version = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String, default="active")
    content = Column(JSON)
    metadata = Column(JSON)

class Risk(Base):
    __tablename__ = "risks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    identified_at = Column(DateTime, default=datetime.utcnow)
    risk_level = Column(String)
    risk_score = Column(Float)
    description = Column(String)
    mitigation_status = Column(String, default="open")
    metadata = Column(JSON)

class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    generated_at = Column(DateTime, default=datetime.utcnow)
    report_type = Column(String)
    period = Column(String)
    content = Column(JSON)
    metadata = Column(JSON)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session