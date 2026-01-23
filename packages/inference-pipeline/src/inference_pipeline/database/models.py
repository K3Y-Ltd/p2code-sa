import enum

from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum


Base = declarative_base()


class StatusEnum(enum.Enum):
    """
    Enum for the status of a software attestation
    """

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class InferenceResult(Base):
    __tablename__ = "inference_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sa_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    stix_report = Column(JSON, nullable=False)
    application_area = Column(Integer, nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)
