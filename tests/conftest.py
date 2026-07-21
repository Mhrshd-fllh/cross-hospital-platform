import asyncio
import os
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import pool

# Set environment variables for testing
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("MLFLOW_MODEL_URI", "mock://model")
os.environ.setdefault("MINIO_ENDPOINT_URL_INTERNAL", "http://localhost:9000")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("MINIO_ENDPOINT_URL_LOCAL", "http://localhost:9000")
os.environ.setdefault("MLFLOW_TRACKING_PORT", "5000")
os.environ.setdefault("MLFLOW_S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("MLFLOW_S3_IGNORE_TLS", "false")
os.environ.setdefault("DATABASE_URL_INTERNAL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("RUNNING_IN_DOCKER", "false")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def async_engine():
    """Create an async SQLite engine for testing."""
    engine = create_async_engine(
        os.getenv("DATABASE_URL"),
        connect_args={"check_same_thread": False},
        poolclass=pool.StaticPool,
    )
    async with engine.begin() as conn:
        # Import models to create tables
        from backend.app.core.database import Base
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(async_engine):
    """Provide a transactional scope around a series of operations."""
    async_session = sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        async with session.begin():
            yield session
        await session.close()

# Override the get_db dependency in the app
@pytest.fixture(autouse=True)
def override_get_db(db_session):
    from fastapi import Depends
    from backend.app.main import app
    from backend.app.core.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()