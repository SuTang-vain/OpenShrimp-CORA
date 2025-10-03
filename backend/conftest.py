"""pytest 配置文件

提供测试所需的 fixtures 和配置
"""

import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.main import app


# 测试配置
@pytest.fixture(scope="session")
def settings():
    """测试设置"""
    return get_settings()


# 数据库相关 fixtures
@pytest.fixture(scope="session")
def test_db_url():
    """测试数据库 URL"""
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def sync_test_db_url():
    """同步测试数据库 URL"""
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine(sync_test_db_url):
    """同步数据库引擎"""
    engine = create_engine(
        sync_test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def async_engine(test_db_url):
    """异步数据库引擎"""
    engine = create_async_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine
    engine.sync_engine.dispose()


@pytest.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """异步数据库会话"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def db_session(engine):
    """同步数据库会话"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# FastAPI 客户端 fixtures
@pytest.fixture
def client(async_session):
    """测试客户端"""
    def override_get_db():
        yield async_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(async_session) -> AsyncGenerator[AsyncClient, None]:
    """异步测试客户端"""
    def override_get_db():
        yield async_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


# 认证相关 fixtures
@pytest.fixture
def mock_user():
    """模拟用户数据"""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
    }


@pytest.fixture
def mock_superuser():
    """模拟超级用户数据"""
    return {
        "id": "test-superuser-id",
        "email": "admin@example.com",
        "username": "admin",
        "full_name": "Admin User",
        "is_active": True,
        "is_superuser": True,
    }


@pytest.fixture
def auth_headers(mock_user):
    """认证头部"""
    # 这里应该生成真实的 JWT token
    # 为了简化，使用模拟 token
    token = "test-jwt-token"
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(mock_superuser):
    """管理员认证头部"""
    token = "test-admin-jwt-token"
    return {"Authorization": f"Bearer {token}"}


# 文件相关 fixtures
@pytest.fixture
def temp_file():
    """临时文件"""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as f:
        f.write("This is a test file content.")
        temp_path = f.name
    
    yield temp_path
    
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def temp_dir():
    """临时目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_pdf_file():
    """示例 PDF 文件"""
    # 创建一个简单的 PDF 文件用于测试
    content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
    
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pdf') as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


# 模拟服务 fixtures
@pytest.fixture
def mock_redis():
    """模拟 Redis 客户端"""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.exists = AsyncMock(return_value=False)
    mock.expire = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_openai_client():
    """模拟 OpenAI 客户端"""
    mock = MagicMock()
    mock.embeddings.create = AsyncMock(return_value=MagicMock(
        data=[MagicMock(embedding=[0.1] * 1536)]
    ))
    mock.chat.completions.create = AsyncMock(return_value=MagicMock(
        choices=[MagicMock(
            message=MagicMock(content="This is a test response")
        )]
    ))
    return mock


@pytest.fixture
def mock_vector_store():
    """模拟向量存储"""
    mock = MagicMock()
    mock.add_documents = AsyncMock(return_value=None)
    mock.similarity_search = AsyncMock(return_value=[])
    mock.similarity_search_with_score = AsyncMock(return_value=[])
    mock.delete = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_document_processor():
    """模拟文档处理器"""
    mock = MagicMock()
    mock.process_document = AsyncMock(return_value={
        "content": "Test document content",
        "metadata": {"title": "Test Document", "pages": 1}
    })
    mock.extract_text = AsyncMock(return_value="Test document content")
    mock.chunk_text = AsyncMock(return_value=[
        {"content": "Chunk 1", "metadata": {"chunk_id": 1}},
        {"content": "Chunk 2", "metadata": {"chunk_id": 2}}
    ])
    return mock


# 测试数据 fixtures
@pytest.fixture
def sample_document_data():
    """示例文档数据"""
    return {
        "title": "Test Document",
        "content": "This is a test document content.",
        "file_type": "text/plain",
        "file_size": 1024,
        "tags": ["test", "document"],
        "metadata": {
            "author": "Test Author",
            "created_at": "2024-01-01T00:00:00Z"
        }
    }


@pytest.fixture
def sample_search_query():
    """示例搜索查询"""
    return {
        "query": "test search query",
        "strategy": "semantic",
        "limit": 10,
        "filters": {
            "file_type": ["text/plain"],
            "tags": ["test"]
        }
    }


# 环境变量 fixtures
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """设置测试环境变量"""
    test_env_vars = {
        "ENVIRONMENT": "test",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/1",
        "SECRET_KEY": "test-secret-key",
        "OPENAI_API_KEY": "test-openai-key",
        "LOG_LEVEL": "DEBUG",
        "TESTING": "true",
    }
    
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)


# 事件循环配置
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# 清理 fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """测试后清理"""
    yield
    # 清理操作
    # 例如：清理临时文件、重置模拟对象等


# 性能测试 fixtures
@pytest.fixture
def benchmark_config():
    """性能测试配置"""
    return {
        "min_rounds": 5,
        "max_time": 1.0,
        "warmup": False,
    }


# 并发测试 fixtures
@pytest.fixture
def concurrent_requests():
    """并发请求数量"""
    return 10


# 错误模拟 fixtures
@pytest.fixture
def mock_network_error():
    """模拟网络错误"""
    from httpx import ConnectError
    return ConnectError("Connection failed")


@pytest.fixture
def mock_database_error():
    """模拟数据库错误"""
    from sqlalchemy.exc import SQLAlchemyError
    return SQLAlchemyError("Database connection failed")


# 日志配置
@pytest.fixture(autouse=True)
def configure_test_logging(caplog):
    """配置测试日志"""
    import logging
    caplog.set_level(logging.DEBUG)
    yield caplog