from secrets import compare_digest

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.core.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def configured_api_key() -> str | None:
    secret = get_settings().api_key
    value = secret.get_secret_value() if secret is not None else ""
    return value if value.strip() else None


def require_api_key(provided: str | None = Security(api_key_header)) -> None:
    expected = configured_api_key()
    if expected is None:
        return  # Explicitly local/demo mode; production startup rejects this.
    if provided is None or not compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
