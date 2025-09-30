"""
User Business Logic Services.

Demonstrates separation of business logic from routes:
- CRUD operations
- Database interaction with async sessions
- Error handling
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func

from .models import User
from .schemas import UserCreate, UserUpdate


class UserService:
    """Service for user-related business logic."""

    @staticmethod
    async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            session: Database session
            user_data: User creation data

        Returns:
            Created user

        Raises:
            ValueError: If user with email or username already exists
        """
        # Check if user with email already exists
        result = await session.execute(select(User).where(User.email == user_data.email))
        if result.scalars().first():
            raise ValueError(f"User with email {user_data.email} already exists")

        # Check if user with username already exists
        result = await session.execute(select(User).where(User.username == user_data.username))
        if result.scalars().first():
            raise ValueError(f"User with username {user_data.username} already exists")

        # Create new user
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
        )

        session.add(user)
        await session.flush()
        await session.refresh(user)

        return user

    @staticmethod
    async def get_user(session: AsyncSession, user_id: int) -> User | None:
        """
        Get user by ID.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
        """
        Get user by email.

        Args:
            session: Database session
            email: User email

        Returns:
            User if found, None otherwise
        """
        result = await session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    @staticmethod
    async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
        """
        Get user by username.

        Args:
            session: Database session
            username: Username

        Returns:
            User if found, None otherwise
        """
        result = await session.execute(select(User).where(User.username == username))
        return result.scalars().first()

    @staticmethod
    async def list_users(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[User], int]:
        """
        List users with pagination.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (users list, total count)
        """
        # Get total count
        count_result = await session.execute(select(func.count(User.id)))
        total = count_result.scalar_one()

        # Get paginated results
        result = await session.execute(
            select(User)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        users = result.scalars().all()

        return list(users), total

    @staticmethod
    async def update_user(
        session: AsyncSession,
        user_id: int,
        user_data: UserUpdate,
    ) -> User | None:
        """
        Update user.

        Args:
            session: Database session
            user_id: User ID
            user_data: User update data

        Returns:
            Updated user if found, None otherwise
        """
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if not user:
            return None

        # Update fields
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        user.updated_at = datetime.utcnow()

        await session.flush()
        await session.refresh(user)

        return user

    @staticmethod
    async def delete_user(session: AsyncSession, user_id: int) -> bool:
        """
        Delete user.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            True if user was deleted, False if not found
        """
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if not user:
            return False

        await session.delete(user)
        await session.flush()

        return True
