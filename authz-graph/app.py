import json
import os
import time
from typing import Any

import httpx
import jwt
import redis
from fastapi import FastAPI, Request, Response

app = FastAPI(title="envoy-ext-authz-graph")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
ENTRA_TENANT_ID = os.getenv("ENTRA_TENANT_ID", "common")
GRAPH_TIMEOUT_SECONDS = float(os.getenv("GRAPH_TIMEOUT_SECONDS", "5"))

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
_jwks_cache: dict[str, Any] = {"keys": [], "loaded_at": 0.0}


def _extract_bearer(proxy_authorization: str | None) -> str | None:
    if not proxy_authorization:
        return None
    parts = proxy_authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


async def _load_jwks() -> dict[str, Any]:
    if time.time() - _jwks_cache["loaded_at"] < 3600 and _jwks_cache["keys"]:
        return _jwks_cache
    url = f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/discovery/v2.0/keys"
    async with httpx.AsyncClient(timeout=GRAPH_TIMEOUT_SECONDS) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        payload = resp.json()
        _jwks_cache["keys"] = payload.get("keys", [])
        _jwks_cache["loaded_at"] = time.time()
    return _jwks_cache


async def _validate_token(token: str) -> dict[str, Any]:
    unverified = jwt.get_unverified_header(token)
    kid = unverified.get("kid")
    jwks = await _load_jwks()
    key = next((k for k in jwks["keys"] if k.get("kid") == kid), None)
    if not key:
        raise ValueError("Unable to match kid in JWKS")

    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
    return jwt.decode(
        token,
        key=public_key,
        algorithms=["RS256"],
        options={"verify_aud": False},
    )


async def _graph_language(token: str) -> str:
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://graph.microsoft.com/v1.0/me?$select=preferredLanguage"
    async with httpx.AsyncClient(timeout=GRAPH_TIMEOUT_SECONDS) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        payload = resp.json()
    lang = payload.get("preferredLanguage") or "en-US"
    return lang


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/check")
async def check(request: Request) -> Response:
    token = _extract_bearer(request.headers.get("proxy-authorization"))
    if not token:
        return Response(status_code=401)

    try:
        claims = await _validate_token(token)
        oid = claims.get("oid") or claims.get("sub")
        if not oid:
            return Response(status_code=403)

        cache_key = f"user_lang:{oid}"
        lang = redis_client.get(cache_key)
        if not lang:
            lang = await _graph_language(token)
            redis_client.setex(cache_key, CACHE_TTL_SECONDS, lang)

        return Response(status_code=200, headers={"x-user-lang": lang})
    except Exception:
        return Response(status_code=403)
