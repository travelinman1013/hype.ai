# Async API Client Pattern

This directory demonstrates best practices for building async HTTP clients in Python using `httpx` and `authlib`.

## When to Use This Pattern

Use this pattern when you need to:
- Make async HTTP requests to external APIs
- Handle OAuth2 authentication with automatic token refresh
- Implement retry logic with exponential backoff
- Properly manage HTTP client lifecycle with context managers
- Handle rate limiting and error responses

## Pattern Components

### 1. `async_client.py` - Base Async Client

**Purpose**: Provides a reusable base class for async HTTP clients with:
- Automatic retry with exponential backoff
- Proper error handling and custom exceptions
- Context manager pattern for resource cleanup
- Support for all HTTP methods (GET, POST, PUT, DELETE)

**Key Features**:
- `AsyncAPIClient`: Base class with retry logic
- `retry_with_backoff`: Decorator for retrying async functions
- Custom exceptions: `APIError`, `RateLimitError`, `TokenExpiredError`
- Automatic handling of 401 (expired token) and 429 (rate limit) responses

**Usage Example**:
```python
from async_client import AsyncAPIClient

async with AsyncAPIClient(base_url="https://api.example.com") as client:
    response = await client.get("/users/me")
    data = response.json()
```

### 2. `token_manager.py` - OAuth2 Token Management

**Purpose**: Manages OAuth2 tokens with automatic refresh before expiration.

**Key Features**:
- `TokenManager`: Full token lifecycle management
- Automatic token refresh based on expiration time
- Thread-safe token operations with asyncio locks
- Integration with Authlib's `AsyncOAuth2Client`
- Optional callback for persisting refreshed tokens

**Usage Example**:
```python
from token_manager import TokenManager

async def save_token(token_dict):
    # Save to database
    await db.save_token(token_dict)

async with TokenManager(
    client_id="your_client_id",
    client_secret="your_client_secret",
    token_endpoint="https://api.example.com/oauth/token",
    update_token=save_token
) as manager:
    # Set initial token
    await manager.set_token(initial_token)

    # Get valid token (auto-refreshes if needed)
    token = await manager.get_valid_token()
```

### 3. `models.py` - Response Models

**Purpose**: Demonstrates Pydantic models for API responses with validation.

**Key Features**:
- Field validation with constraints
- Type hints for all fields
- Custom validators with `@field_validator`
- JSON schema examples with `model_config`

**Usage Example**:
```python
from models import TokenResponse

# Parse and validate API response
token_data = TokenResponse(**response.json())
print(token_data.access_token)
```

## Common Patterns and Best Practices

### 1. Context Manager Pattern

**Always** use `async with` for HTTP clients to ensure proper cleanup:

```python
# ✅ Good
async with AsyncAPIClient(base_url=url) as client:
    response = await client.get("/endpoint")

# ❌ Bad - client never closed
client = AsyncAPIClient(base_url=url)
response = await client.get("/endpoint")
```

### 2. Retry Logic with Exponential Backoff

The `retry_with_backoff` decorator handles transient failures:

```python
@retry_with_backoff(max_retries=3, initial_delay=1.0)
async def fetch_data():
    # Will retry up to 3 times with exponential backoff
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()
```

### 3. Token Refresh Before Expiration

Always check token expiration **before** making API calls:

```python
# TokenManager automatically refreshes tokens 5 minutes before expiration
token = await manager.get_valid_token()

# Use fresh token for API call
headers = {"Authorization": f"Bearer {token}"}
```

### 4. Rate Limit Handling

Handle 429 responses with exponential backoff:

```python
try:
    response = await client.get("/endpoint")
except RateLimitError as e:
    # Wait for specified time before retry
    if e.retry_after:
        await asyncio.sleep(e.retry_after)
    else:
        # Default backoff
        await asyncio.sleep(60)
```

### 5. Error Handling

Use specific exception types for different error scenarios:

```python
try:
    response = await client.get("/endpoint")
except TokenExpiredError:
    # Token expired - refresh it
    await refresh_token()
except RateLimitError as e:
    # Rate limit - wait and retry
    await asyncio.sleep(e.retry_after or 60)
except APIError as e:
    # General API error
    logger.error(f"API error: {e.status_code} {e.message}")
```

## Common Pitfalls

### ❌ Using Sync Client in Async Context

```python
# ❌ Bad - blocks event loop
import requests
response = requests.get("https://api.example.com")

# ✅ Good - uses async
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com")
```

### ❌ Not Handling Token Expiration

```python
# ❌ Bad - token might be expired
headers = {"Authorization": f"Bearer {token}"}
response = await client.get("/endpoint", headers=headers)

# ✅ Good - ensures valid token
token = await token_manager.get_valid_token()
headers = {"Authorization": f"Bearer {token}"}
response = await client.get("/endpoint", headers=headers)
```

### ❌ Ignoring Rate Limits

```python
# ❌ Bad - might hit rate limits
for i in range(1000):
    await client.get("/endpoint")

# ✅ Good - implements rate limiting
from asyncio import Semaphore

rate_limiter = Semaphore(10)  # Max 10 concurrent requests

async def fetch_with_limit(endpoint):
    async with rate_limiter:
        return await client.get(endpoint)

tasks = [fetch_with_limit("/endpoint") for _ in range(1000)]
results = await asyncio.gather(*tasks)
```

### ❌ Not Closing Clients

```python
# ❌ Bad - client never closed
client = httpx.AsyncClient()
response = await client.get("/endpoint")

# ✅ Good - client automatically closed
async with httpx.AsyncClient() as client:
    response = await client.get("/endpoint")
```

## Integration with FastAPI

This pattern integrates well with FastAPI dependency injection:

```python
from fastapi import Depends, FastAPI
from async_client import AsyncAPIClient

app = FastAPI()

async def get_api_client():
    async with AsyncAPIClient(base_url="https://api.example.com") as client:
        yield client

@app.get("/users/{user_id}")
async def get_user(user_id: str, client: AsyncAPIClient = Depends(get_api_client)):
    response = await client.get(f"/users/{user_id}")
    return response.json()
```

## Testing

Mock external API calls using `pytest-mock` or `respx`:

```python
import pytest
from httpx import Response
from async_client import AsyncAPIClient

@pytest.mark.asyncio
async def test_api_client_get(respx_mock):
    # Mock the API response
    respx_mock.get("https://api.example.com/users/123").mock(
        return_value=Response(200, json={"id": "123", "name": "Test User"})
    )

    async with AsyncAPIClient(base_url="https://api.example.com") as client:
        response = await client.get("/users/123")
        data = response.json()

        assert data["id"] == "123"
        assert data["name"] == "Test User"
```

## Dependencies

```
httpx>=0.25.0
authlib>=1.3.0
pydantic>=2.5.0
```

## Related Patterns

- **Modular FastAPI**: See `examples/modular_fastapi/` for integrating this pattern into a FastAPI application
- **Rate Limiting**: See `src/hypeai/music/rate_limiter.py` for advanced rate limiting implementation
