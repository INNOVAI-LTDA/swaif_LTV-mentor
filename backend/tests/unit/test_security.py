from app.core.security import create_access_token, hash_password, verify_access_token, verify_password


def test_password_hash_and_verify() -> None:
    password = "admin123"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_access_token_roundtrip_and_tamper() -> None:
    token = create_access_token(user_id="usr_1", role="admin", secret="test-secret", ttl_seconds=300)
    payload = verify_access_token(token, secret="test-secret")

    assert payload is not None
    assert payload["sub"] == "usr_1"
    assert payload["role"] == "admin"

    tampered = token + "x"
    assert verify_access_token(tampered, secret="test-secret") is None
