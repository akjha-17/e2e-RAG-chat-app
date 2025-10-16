# app/auth.py
import logging
from datetime import datetime, timedelta
from jose import jwt, JWTError
import httpx
from cachetools import TTLCache, cached
from typing import Dict, Any, Optional
from .config import AZURE_OPENID_CONFIG, JWKS_CACHE_TTL, AZURE_CLIENT_ID, JWT_SECRET

logger = logging.getLogger(__name__)

# cache JWKS (small cache)
_jwks_cache = TTLCache(maxsize=1, ttl=JWKS_CACHE_TTL)

@cached(_jwks_cache)
def fetch_jwks() -> Dict[str, Any]:
    if not AZURE_OPENID_CONFIG:
        raise RuntimeError("AZURE_OPENID_CONFIG not configured")
    r = httpx.get(AZURE_OPENID_CONFIG, timeout=10)
    r.raise_for_status()
    openid = r.json()
    jwks_uri = openid.get("jwks_uri")
    if not jwks_uri:
        raise RuntimeError("jwks_uri missing from openid config")
    jwks = httpx.get(jwks_uri, timeout=10).json()
    return jwks

def validate_azure_jwt(token: str, audience: Optional[str] = AZURE_CLIENT_ID) -> Dict[str, Any]:
    jwks = fetch_jwks()
    try:
        # jose can accept jwks directly as key set
        claims = jwt.decode(token, jwks, audience=audience, options={"verify_exp": True})
        return claims
    except JWTError as e:
        logger.exception("Azure JWT validation failed")
        raise

def validate_hs256_jwt(token: str, secret: str = JWT_SECRET) -> Dict[str, Any]:
    try:
        claims = jwt.decode(token, secret, algorithms=["HS256"])
        return claims
    except JWTError as e:
        logger.exception("HS256 JWT validation failed")
        raise

def create_access_token(user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create access token for authenticated user"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    # Create JWT payload with user information
    payload = {
        "sub": user_data["username"],
        "preferred_username": user_data["preferred_name"],
        "user_id": user_data["id"],
        "email": user_data["email"],
        "full_name": user_data["full_name"],
        "puid": user_data["puid"],
        "role": user_data["role"],
        "organization": user_data["organization"],
        "roles": ["admin", "user"] if user_data["is_admin"] else ["user"],
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

def verify_token(token: str) -> Dict[str, Any]:
    """
    Development-friendly validator:
    - If AZURE_TENANT configured → validate with JWKS (Azure)
    - Else validate HS256 (local dev)
    """
    if AZURE_OPENID_CONFIG:
        return validate_azure_jwt(token)
    else:
        return validate_hs256_jwt(token)

def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """Extract user information from token"""
    try:
        claims = verify_token(token)
        return {
            "id": claims.get("user_id"),
            "username": claims.get("sub"),
            "preferred_name": claims.get("preferred_username"),
            "email": claims.get("email"),
            "full_name": claims.get("full_name"),
            "puid": claims.get("puid"),
            "role": claims.get("role"),
            "organization": claims.get("organization"),
            "is_admin": "admin" in claims.get("roles", []),
            "roles": claims.get("roles", [])
        }
    except Exception as e:
        logger.error(f"Error extracting user from token: {e}")
        return None

def verify_user(claims: Dict[str, Any]) -> bool:
    """
    Check if the user has user privileges.
    """
    if AZURE_OPENID_CONFIG:
        roles = claims.get("roles", [])
        return "user" in roles
    else:
        roles = claims.get("roles", [])
        return "user" in roles

def verify_admin(claims: Dict[str, Any]) -> bool:
    """
    Check if the user has admin privileges.
    """
    if AZURE_OPENID_CONFIG:
        roles = claims.get("roles", [])
        return "admin" in roles
    else:
        roles = claims.get("roles", [])
        return "admin" in roles
