"""
User API Routes.

Demonstrates FastAPI router patterns:
- RESTful API endpoints
- Dependency injection
- Request/response validation
- Error handling
"""

from database import get_session
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import UserCreate, UserListResponse, UserResponse, UserUpdate
from .services import UserService

router = APIRouter()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user with the provided email, username, and optional full name",
)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new user.

    Args:
        user_data: User creation data
        session: Database session (injected)

    Returns:
        Created user

    Raises:
        HTTPException: 400 if user already exists
    """
    try:
        user = await UserService.create_user(session, user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/",
    response_model=UserListResponse,
    summary="List users",
    description="Get a paginated list of all users",
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_session),
):
    """
    List users with pagination.

    Args:
        page: Page number (1-indexed)
        page_size: Items per page
        session: Database session (injected)

    Returns:
        Paginated user list
    """
    skip = (page - 1) * page_size
    users, total = await UserService.list_users(session, skip=skip, limit=page_size)

    return UserListResponse(
        users=users,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Get a specific user by their ID",
)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Get user by ID.

    Args:
        user_id: User ID
        session: Database session (injected)

    Returns:
        User

    Raises:
        HTTPException: 404 if user not found
    """
    user = await UserService.get_user(session, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update an existing user's information",
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Update user.

    Args:
        user_id: User ID
        user_data: User update data
        session: Database session (injected)

    Returns:
        Updated user

    Raises:
        HTTPException: 404 if user not found
    """
    user = await UserService.update_user(session, user_id, user_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete a user by their ID",
)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete user.

    Args:
        user_id: User ID
        session: Database session (injected)

    Raises:
        HTTPException: 404 if user not found
    """
    deleted = await UserService.delete_user(session, user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
