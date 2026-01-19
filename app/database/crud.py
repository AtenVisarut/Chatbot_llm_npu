"""
Database CRUD Operations Module
Create, Read, Update, Delete operations for database models
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.database.models import (
    Base,
    Diagnosis,
    DiagnosisStatistics,
    Feedback,
    User,
)
from app.models import DiagnosisResult

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseCRUD:
    """
    Database CRUD operations handler.

    Provides async database operations for:
    - User management
    - Diagnosis storage and retrieval
    - Feedback collection
    - Statistics aggregation
    """

    def __init__(self, database_url: str | None = None):
        """
        Initialize database connection.

        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url or settings.database_url

        # Convert sync URL to async if needed
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace(
                "postgresql://", "postgresql+asyncpg://"
            )

        self.engine = create_async_engine(
            self.database_url,
            echo=settings.debug,
            pool_size=5,
            max_overflow=10
        )

        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def create_tables(self) -> None:
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

    async def drop_tables(self) -> None:
        """Drop all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped")

    async def close(self) -> None:
        """Close database connection."""
        await self.engine.dispose()
        logger.info("Database connection closed")

    # ==================== User Operations ====================

    async def get_or_create_user(
        self,
        line_user_id: str,
        display_name: str | None = None
    ) -> User:
        """
        Get existing user or create new one.

        Args:
            line_user_id: LINE user ID
            display_name: User's display name

        Returns:
            User object
        """
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.line_user_id == line_user_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.last_active_at = datetime.utcnow()
                if display_name:
                    user.display_name = display_name
                await session.commit()
                return user

            user = User(
                line_user_id=line_user_id,
                display_name=display_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            logger.info(f"Created new user: {line_user_id}")
            return user

    async def get_user(self, line_user_id: str) -> User | None:
        """
        Get user by LINE user ID.

        Args:
            line_user_id: LINE user ID

        Returns:
            User object or None
        """
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.line_user_id == line_user_id)
            )
            return result.scalar_one_or_none()

    async def update_user_diagnosis_count(self, user_id: int) -> None:
        """
        Increment user's diagnosis count.

        Args:
            user_id: User's database ID
        """
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.total_diagnoses += 1
                await session.commit()

    # ==================== Diagnosis Operations ====================

    async def save_diagnosis(
        self,
        line_user_id: str,
        plant_type: str,
        diagnosis_result: DiagnosisResult,
        image_data: bytes | None = None,
        region: str | None = None,
        additional_info: str | None = None,
        processing_time_ms: int | None = None
    ) -> Diagnosis:
        """
        Save diagnosis result to database.

        Args:
            line_user_id: LINE user ID
            plant_type: Type of plant
            diagnosis_result: Diagnosis result from Gemini
            image_data: Original image data for hashing
            region: Thai region
            additional_info: Additional info from user
            processing_time_ms: Processing time in milliseconds

        Returns:
            Diagnosis object
        """
        async with self.async_session() as session:
            # Get or create user
            user = await self.get_or_create_user(line_user_id)

            # Generate image hash if provided
            image_hash = None
            if image_data:
                image_hash = hashlib.md5(image_data).hexdigest()

            # Create diagnosis record
            diagnosis = Diagnosis(
                user_id=user.id,
                image_hash=image_hash,
                plant_type=plant_type,
                region=region,
                additional_info=additional_info,
                disease_name_th=diagnosis_result.disease_name_th,
                disease_name_en=diagnosis_result.disease_name_en,
                pathogen_type=diagnosis_result.pathogen_type,
                confidence_level=diagnosis_result.confidence_level,
                severity=diagnosis_result.disease_characteristics.severity
                if hasattr(diagnosis_result.disease_characteristics, "severity")
                else None,
                diagnosis_result=diagnosis_result.model_dump(),
                processing_time_ms=processing_time_ms,
                model_version=settings.gemini_model
            )

            session.add(diagnosis)
            await session.commit()
            await session.refresh(diagnosis)

            # Update user diagnosis count
            user.total_diagnoses += 1
            await session.commit()

            logger.info(
                f"Saved diagnosis {diagnosis.id} for user {line_user_id}: "
                f"{diagnosis_result.disease_name_th}"
            )

            return diagnosis

    async def get_user_diagnoses(
        self,
        line_user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> list[Diagnosis]:
        """
        Get user's diagnosis history.

        Args:
            line_user_id: LINE user ID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of Diagnosis objects
        """
        async with self.async_session() as session:
            result = await session.execute(
                select(Diagnosis)
                .join(User)
                .where(User.line_user_id == line_user_id)
                .order_by(Diagnosis.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())

    async def get_diagnosis_by_id(self, diagnosis_id: int) -> Diagnosis | None:
        """
        Get diagnosis by ID.

        Args:
            diagnosis_id: Diagnosis database ID

        Returns:
            Diagnosis object or None
        """
        async with self.async_session() as session:
            result = await session.execute(
                select(Diagnosis).where(Diagnosis.id == diagnosis_id)
            )
            return result.scalar_one_or_none()

    # ==================== Feedback Operations ====================

    async def save_feedback(
        self,
        diagnosis_id: int,
        line_user_id: str,
        rating: int | None = None,
        is_accurate: bool | None = None,
        comment: str | None = None,
        correct_disease: str | None = None
    ) -> Feedback:
        """
        Save user feedback for a diagnosis.

        Args:
            diagnosis_id: Diagnosis database ID
            line_user_id: LINE user ID
            rating: Rating 1-5
            is_accurate: Whether diagnosis was accurate
            comment: User comment
            correct_disease: Correct disease name if inaccurate

        Returns:
            Feedback object
        """
        async with self.async_session() as session:
            user = await self.get_or_create_user(line_user_id)

            feedback = Feedback(
                diagnosis_id=diagnosis_id,
                user_id=user.id,
                rating=rating,
                is_accurate=is_accurate,
                comment=comment,
                correct_disease=correct_disease
            )

            session.add(feedback)
            await session.commit()
            await session.refresh(feedback)

            logger.info(
                f"Saved feedback for diagnosis {diagnosis_id}: "
                f"rating={rating}, accurate={is_accurate}"
            )

            return feedback

    # ==================== Statistics Operations ====================

    async def get_daily_statistics(
        self,
        date: datetime | None = None
    ) -> dict[str, Any]:
        """
        Get statistics for a specific date.

        Args:
            date: Date to get statistics for (default: today)

        Returns:
            Dictionary with statistics
        """
        if date is None:
            date = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        async with self.async_session() as session:
            # Get diagnosis count
            result = await session.execute(
                select(func.count(Diagnosis.id))
                .where(
                    and_(
                        Diagnosis.created_at >= date,
                        Diagnosis.created_at < date + timedelta(days=1)
                    )
                )
            )
            total_diagnoses = result.scalar() or 0

            # Get unique users
            result = await session.execute(
                select(func.count(func.distinct(Diagnosis.user_id)))
                .where(
                    and_(
                        Diagnosis.created_at >= date,
                        Diagnosis.created_at < date + timedelta(days=1)
                    )
                )
            )
            unique_users = result.scalar() or 0

            # Get average confidence
            result = await session.execute(
                select(func.avg(Diagnosis.confidence_level))
                .where(
                    and_(
                        Diagnosis.created_at >= date,
                        Diagnosis.created_at < date + timedelta(days=1)
                    )
                )
            )
            avg_confidence = result.scalar()

            return {
                "date": date.isoformat(),
                "total_diagnoses": total_diagnoses,
                "unique_users": unique_users,
                "avg_confidence": round(avg_confidence, 2) if avg_confidence else None
            }

    async def get_disease_distribution(
        self,
        days: int = 30
    ) -> list[dict[str, Any]]:
        """
        Get disease distribution over recent days.

        Args:
            days: Number of days to analyze

        Returns:
            List of disease counts
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        async with self.async_session() as session:
            result = await session.execute(
                select(
                    Diagnosis.disease_name_th,
                    func.count(Diagnosis.id).label("count")
                )
                .where(Diagnosis.created_at >= start_date)
                .group_by(Diagnosis.disease_name_th)
                .order_by(func.count(Diagnosis.id).desc())
                .limit(10)
            )

            return [
                {"disease": row[0], "count": row[1]}
                for row in result.all()
            ]

    # ==================== Health Check ====================

    async def health_check(self) -> bool:
        """
        Check database connection health.

        Returns:
            True if healthy, False otherwise
        """
        try:
            async with self.async_session() as session:
                await session.execute(select(1))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database instance
db = DatabaseCRUD()
