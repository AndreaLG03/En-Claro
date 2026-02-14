import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models.db import Base, get_db
from app.models.schemas import TextRequest

# Setup in-memory DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_analyze_saves_history(test_db):
    # 1. Analyze text with a user email
    payload = {
        "text": "Hola, esto es una prueba",
        "module": "message",
        "user_email": "test@example.com",
        "user_profile": {"name": "Test User"}
    }
    
    # Mocking Claude to avoid actual API call cost/latency if possible, 
    # but for integration test we might hit it or mock the service.
    # For now, let's assume valid API key or mock `call_claude`.
    
    # We'll mock call_claude to avoid external dependency
    from app.api import routes
    async def mock_call_claude(*args, **kwargs):
        return "Respuesta simulada"
    
    original_call_claude = routes.call_claude
    routes.call_claude = mock_call_claude
    
    try:
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200
        assert response.json()["result"] == "Respuesta simulada"
        
        # 2. Check history
        history_response = client.get("/api/history?email=test@example.com")
        assert history_response.status_code == 200
        history = history_response.json()
        assert len(history) == 1
        assert history[0]["input_text"] == "Hola, esto es una prueba"
        assert history[0]["result_text"] == "Respuesta simulada"
        
    finally:
        routes.call_claude = original_call_claude

def test_premium_restriction(test_db):
    # Non-premium user accessing premium content
    payload = {
        "text": "Roleplay test",
        "module": "roleplay",
        "scenario_context": {"is_premium": True},
        "user_email": "normal@example.com"
    }
    
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 403
    assert "Premium" in response.json()["detail"]

def test_premium_access(test_db):
    # Premium user (hardcoded in routes.py)
    payload = {
        "text": "Roleplay test",
        "module": "roleplay",
        "scenario_context": {"is_premium": True},
        "user_email": "andrealan2003@gmail.com"
    }
    
    # Mock claude again
    from app.api import routes
    async def mock_call_claude(*args, **kwargs):
        return "Respuesta premium"
    
    original_call_claude = routes.call_claude
    routes.call_claude = mock_call_claude
    
    try:
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200
    finally:
        routes.call_claude = original_call_claude
