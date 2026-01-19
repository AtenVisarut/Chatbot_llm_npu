"""
SQLAlchemy Database Models Module
Database models for storing diagnosis history and user data
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model for storing LINE user information."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    line_user_id = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    total_diagnoses = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    diagnoses = relationship(
        "Diagnosis",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    feedbacks = relationship(
        "Feedback",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_users_created_at", "created_at"),
        Index("ix_users_last_active", "last_active_at"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, line_user_id={self.line_user_id})>"


class Diagnosis(Base):
    """Diagnosis model for storing diagnosis results."""

    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Input data
    image_hash = Column(String(64), nullable=True)
    plant_type = Column(String(50), nullable=False)
    region = Column(String(50), nullable=True)
    additional_info = Column(Text, nullable=True)

    # Diagnosis results
    disease_name_th = Column(String(255), nullable=False)
    disease_name_en = Column(String(255), nullable=True)
    pathogen_type = Column(String(50), nullable=True)
    confidence_level = Column(Integer, nullable=False)
    severity = Column(String(20), nullable=True)

    # Full diagnosis result as JSON
    diagnosis_result = Column(JSON, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    model_version = Column(String(50), nullable=True)

    # Relationships
    user = relationship("User", back_populates="diagnoses")
    feedback = relationship(
        "Feedback",
        back_populates="diagnosis",
        uselist=False,
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_diagnoses_created_at", "created_at"),
        Index("ix_diagnoses_disease", "disease_name_th"),
        Index("ix_diagnoses_plant_type", "plant_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<Diagnosis(id={self.id}, disease={self.disease_name_th}, "
            f"confidence={self.confidence_level}%)>"
        )


class Feedback(Base):
    """Feedback model for storing user feedback on diagnoses."""

    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnosis_id = Column(
        Integer,
        ForeignKey("diagnoses.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Feedback data
    rating = Column(Integer, nullable=True)  # 1-5 stars
    is_accurate = Column(Boolean, nullable=True)
    comment = Column(Text, nullable=True)
    correct_disease = Column(String(255), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    diagnosis = relationship("Diagnosis", back_populates="feedback")
    user = relationship("User", back_populates="feedbacks")

    __table_args__ = (
        Index("ix_feedbacks_created_at", "created_at"),
        Index("ix_feedbacks_rating", "rating"),
    )

    def __repr__(self) -> str:
        return (
            f"<Feedback(id={self.id}, diagnosis_id={self.diagnosis_id}, "
            f"rating={self.rating})>"
        )


class DiagnosisStatistics(Base):
    """Statistics table for aggregated diagnosis data."""

    __tablename__ = "diagnosis_statistics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)

    # Counts
    total_diagnoses = Column(Integer, default=0, nullable=False)
    unique_users = Column(Integer, default=0, nullable=False)

    # By plant type
    rice_diagnoses = Column(Integer, default=0, nullable=False)
    corn_diagnoses = Column(Integer, default=0, nullable=False)
    cassava_diagnoses = Column(Integer, default=0, nullable=False)
    other_diagnoses = Column(Integer, default=0, nullable=False)

    # Accuracy metrics
    avg_confidence = Column(Float, nullable=True)
    accurate_count = Column(Integer, default=0, nullable=False)
    inaccurate_count = Column(Integer, default=0, nullable=False)

    # Performance metrics
    avg_processing_time_ms = Column(Float, nullable=True)
    cache_hits = Column(Integer, default=0, nullable=False)
    api_errors = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<DiagnosisStatistics(date={self.date}, "
            f"total={self.total_diagnoses})>"
        )
