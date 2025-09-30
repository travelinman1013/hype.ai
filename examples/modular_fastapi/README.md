# Modular FastAPI Application Pattern

This directory demonstrates best practices for building modular FastAPI applications with SQLModel and async patterns.

## When to Use This Pattern

Use this pattern when you need to:
- Build a scalable FastAPI application with multiple domain modules
- Separate concerns: routes, business logic, database models, and API schemas
- Use async SQLAlchemy with SQLModel for database operations
- Implement dependency injection for database sessions
- Configure middleware (CORS, error handling)
- Manage application lifecycle (startup/shutdown events)

## Directory Structure

```
modular_fastapi/
├── main.py              # FastAPI app initialization and configuration
├── config.py            # Settings with Pydantic BaseSettings
├── database.py          # Database engine, session factory, dependencies
├── users/               # Example domain module
│   ├── __init__.py
│   ├── models.py        # SQLModel database models
│   ├── schemas.py       # Pydantic request/response models
│   ├── routes.py        # FastAPI router with endpoints
│   └── services.py      # Business logic layer
└── README.md            # This file
```

## Pattern Components

### 1. `main.py` - Application Entry Point

**Purpose**: Initialize FastAPI app, configure middleware, include routers.

**Key Features**:
- Lifespan context manager for startup/shutdown events
- CORS middleware configuration
- Global exception handler
- Health check endpoint
- Router inclusion from domain modules

**Usage**:
```bash
# Run the application
uvicorn main:app --reload

# Or use the built-in runner
python main.py
```

### 2. `config.py` - Configuration Management

**Purpose**: Type-safe configuration using Pydantic Settings.

**Key Features**:
- Environment variable loading with `python-dotenv`
- Validation and default values
- Type hints for all settings
- Support for multiple configuration sources (.env file, environment variables)

**Usage**:
```python
from config import settings

# Access settings anywhere in the application
database_url = settings.database_url
debug_mode = settings.debug
```

**Environment Variables**:
```bash
# .env file or environment variables
APP_DATABASE_URL=sqlite+aiosqlite:///./example.db
APP_DEBUG=true
APP_SECRET_KEY=your-secret-key
```

### 3. `database.py` - Database Setup

**Purpose**: Configure async database engine and session factory.

**Key Features**:
- Async SQLAlchemy engine
- Session factory with proper cleanup
- FastAPI dependency for session injection
- Table creation function

**Usage**:
```python
from database import get_session
from sqlalchemy.ext.asyncio import AsyncSession

@app.get("/items")
async def get_items(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Item))
    return result.scalars().all()
```

### 4. Domain Modules (e.g., `users/`)

Each domain module follows a consistent structure:

#### `models.py` - Database Models

SQLModel models representing database tables:
```python
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
```

#### `schemas.py` - API Schemas

Pydantic models for request/response validation:
```python
class UserCreate(BaseModel):
    email: EmailStr
    username: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
```

#### `services.py` - Business Logic

Service layer with database operations:
```python
class UserService:
    @staticmethod
    async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
        # Validation logic
        # Database operations
        # Return result
```

#### `routes.py` - API Endpoints

FastAPI router with endpoints:
```python
router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    return await UserService.create_user(session, user_data)
```

## Architecture Principles

### 1. Separation of Concerns

Each file has a specific responsibility:
- **models.py**: Database schema (how data is stored)
- **schemas.py**: API contract (how data is sent/received)
- **services.py**: Business logic (what operations are performed)
- **routes.py**: HTTP layer (how to access operations)

### 2. Dependency Injection

Use FastAPI's dependency injection for:
- Database sessions
- Authentication
- Configuration
- Shared resources

```python
@app.get("/items")
async def get_items(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # session and current_user are automatically injected
```

### 3. Async All the Way

- Use `async def` for all handlers
- Use `AsyncSession` for database operations
- Use `httpx.AsyncClient` for HTTP requests
- Use `async with` for context managers

### 4. Type Safety

- Type hints on all functions
- Pydantic models for validation
- SQLModel for database type safety

## Common Patterns

### 1. Adding a New Module

```bash
# Create module directory
mkdir new_module

# Create module files
touch new_module/__init__.py
touch new_module/models.py
touch new_module/schemas.py
touch new_module/services.py
touch new_module/routes.py
```

Update `main.py`:
```python
from new_module.routes import router as new_module_router

app.include_router(new_module_router, prefix="/new-module", tags=["new-module"])
```

Update `database.py` to import models:
```python
async def create_db_and_tables():
    async with engine.begin() as conn:
        from users.models import User
        from new_module.models import NewModel  # Add this

        await conn.run_sync(SQLModel.metadata.create_all)
```

### 2. Pagination Pattern

```python
# In routes.py
@router.get("/", response_model=ListResponse)
async def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    skip = (page - 1) * page_size
    items, total = await ItemService.list_items(session, skip=skip, limit=page_size)

    return ListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
```

### 3. Error Handling Pattern

```python
# In services.py
async def get_item(session: AsyncSession, item_id: int) -> Item:
    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalars().first()

    if not item:
        raise ValueError(f"Item {item_id} not found")

    return item

# In routes.py
@router.get("/{item_id}")
async def get_item(item_id: int, session: AsyncSession = Depends(get_session)):
    try:
        return await ItemService.get_item(session, item_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### 4. Transaction Pattern

```python
async def update_with_transaction(session: AsyncSession, user_id: int):
    # All operations use the same session
    user = await UserService.get_user(session, user_id)
    user.updated_at = datetime.utcnow()

    # If any operation fails, entire transaction rolls back
    await session.flush()
    await session.refresh(user)

    # Commit happens automatically in get_session dependency
    return user
```

## Testing

### Unit Testing Services

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

@pytest.fixture
async def test_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session_maker = sessionmaker(engine, class_=AsyncSession)

    async with async_session_maker() as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_create_user(test_session):
    user_data = UserCreate(email="test@example.com", username="testuser")
    user = await UserService.create_user(test_session, user_data)

    assert user.id is not None
    assert user.email == "test@example.com"
```

### Integration Testing Routes

```python
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_create_user_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/users/",
            json={"email": "test@example.com", "username": "testuser"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
```

## Running the Example

### 1. Install Dependencies

```bash
pip install fastapi[all] sqlmodel uvicorn[standard] python-dotenv pydantic-settings
```

### 2. Create .env File

```bash
echo "APP_DATABASE_URL=sqlite+aiosqlite:///./example.db" > .env
echo "APP_DEBUG=true" >> .env
```

### 3. Run the Application

```bash
uvicorn main:app --reload
```

### 4. Access the API

- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 5. Test Endpoints

```bash
# Create a user
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "username": "testuser", "full_name": "Test User"}'

# List users
curl http://localhost:8000/users/

# Get specific user
curl http://localhost:8000/users/1

# Update user
curl -X PUT http://localhost:8000/users/1 \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Updated Name"}'

# Delete user
curl -X DELETE http://localhost:8000/users/1
```

## Best Practices

### ✅ DO

- Separate database models (SQLModel) from API schemas (Pydantic)
- Use dependency injection for database sessions
- Keep business logic in services, not routes
- Use type hints everywhere
- Use async/await consistently
- Handle errors in services, catch in routes
- Use Pydantic for validation
- Use context managers for resource cleanup

### ❌ DON'T

- Mix database models and API schemas
- Create database connections manually in routes
- Put business logic in routes
- Use sync database operations in async code
- Ignore type hints
- Let exceptions bubble up without handling
- Skip validation
- Leave resources open (files, connections, clients)

## Related Patterns

- **Async API Client**: See `examples/api_client/` for HTTP client patterns
- **HypeAI Application**: See `src/hypeai/` for a complete implementation using these patterns

## Dependencies

```
fastapi[all]>=0.104.0
sqlmodel>=0.0.14
uvicorn[standard]>=0.24.0
python-dotenv>=1.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
```
