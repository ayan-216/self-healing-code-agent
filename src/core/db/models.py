from datetime import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.core.db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    clone_url = Column(String, nullable=False)
    default_branch = Column(String, default="main")
    created_at = Column(DateTime, default=datetime.utcnow)

    audits = relationship("AuditSession", back_populates="repository", cascade="all, delete-orphan")


class AuditSession(Base):
    __tablename__ = "audit_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    status = Column(String, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    commit_sha = Column(String, nullable=True)
    target_branch = Column(String, default="main")
    retry_count = Column(Integer, default=0)
    pr_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    repository = relationship("Repository", back_populates="audits")
    issues = relationship("DetectedIssue", back_populates="audit_session", cascade="all, delete-orphan")
    attempts = relationship("RepairAttempt", back_populates="audit_session", cascade="all, delete-orphan")
    execution_logs = relationship("ExecutionLog", back_populates="audit_session", cascade="all, delete-orphan")
    metric = relationship("PlatformMetric", back_populates="audit_session", uselist=False, cascade="all, delete-orphan")


class DetectedIssue(Base):
    __tablename__ = "detected_issues"

    id = Column(String, primary_key=True, default=generate_uuid)
    audit_session_id = Column(String, ForeignKey("audit_sessions.id"), nullable=False)
    issue_type = Column(String, nullable=False)  # LINT, SECURITY, BUG, AST_ERROR
    file_path = Column(String, nullable=False)
    line_number = Column(Integer, nullable=True)
    severity = Column(String, default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    tool = Column(String, nullable=False)  # flake8, bandit, pylint, ast
    description = Column(Text, nullable=False)
    snippet = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    audit_session = relationship("AuditSession", back_populates="issues")


class RepairAttempt(Base):
    __tablename__ = "repair_attempts"

    id = Column(String, primary_key=True, default=generate_uuid)
    audit_session_id = Column(String, ForeignKey("audit_sessions.id"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    root_cause_explanation = Column(Text, nullable=True)
    repair_plan = Column(JSON, nullable=True)
    patch_diff = Column(Text, nullable=True)
    validation_status = Column(String, default="PENDING")  # APPROVED, REJECTED, PENDING
    reflection_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    audit_session = relationship("AuditSession", back_populates="attempts")


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    audit_session_id = Column(String, ForeignKey("audit_sessions.id"), nullable=False)
    agent_name = Column(String, nullable=False)
    level = Column(String, default="INFO")
    message = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    audit_session = relationship("AuditSession", back_populates="execution_logs")


class MemoryRecord(Base):
    __tablename__ = "memory_records"

    id = Column(String, primary_key=True, default=generate_uuid)
    issue_signature = Column(String, nullable=False)
    repository_name = Column(String, nullable=False)
    repair_pattern = Column(Text, nullable=False)
    status = Column(String, nullable=False)  # SUCCESS, FAILURE
    vector_id = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PlatformMetric(Base):
    __tablename__ = "platform_metrics"

    id = Column(String, primary_key=True, default=generate_uuid)
    audit_session_id = Column(String, ForeignKey("audit_sessions.id"), nullable=False)
    execution_time_seconds = Column(Float, default=0.0)
    token_usage = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    validation_passed = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    audit_session = relationship("AuditSession", back_populates="metric")
