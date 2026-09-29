from app.auth import create_access_token
from app.config import JWT_SECRET
import jwt

def test_token_contains_username():
    token = create_access_token("test-user")
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    assert payload["sub"] == "test-user"
    assert "exp" in payload
