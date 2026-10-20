"""Shared, atomic quotas for owner-funded AI calls on serverless instances.

Fail closed without Upstash Redis credentials or on Redis outages.
The Lua script reserves exactly one request across all Vercel instances before
making any chargeable AI call. A failed model request may consume a reservation;
this is intentional to protect the owner's spending budget.
"""
from __future__ import annotations

import hashlib
import ipaddress
import os
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, Request

QUOTA_SCRIPT = """
for i=1,#KEYS do
  local n=tonumber(redis.call('GET', KEYS[i]) or '0')
  if n >= tonumber(ARGV[i]) then return i end
end
for i=1,#KEYS do
  redis.call('INCR', KEYS[i])
  if redis.call('TTL', KEYS[i]) < 0 then
    redis.call('EXPIRE', KEYS[i], tonumber(ARGV[#KEYS+i]))
  end
end
return 0
"""

def _limit(name: str, default: int) -> int:
    try:
        return max(1, min(int(os.getenv(name, str(default))), 100000))
    except ValueError:
        return default

def shared_quota_ready() -> bool:
    return bool(os.getenv("UPSTASH_REDIS_REST_URL", "").strip() and os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip())

def _visitor_fingerprint(request: Request) -> str:
    # Vercel overwrites this header at its edge. Do not trust arbitrary
    # X-Forwarded-For headers in local or non-Vercel deployments.
    raw = request.headers.get("x-vercel-forwarded-for", "") if os.getenv("VERCEL") == "1" else ""
    candidate = raw.split(",", 1)[0].strip() if raw else (request.client.host if request.client else "")
    try:
        candidate = str(ipaddress.ip_address(candidate))
    except ValueError:
        candidate = "unknown"
    salt = os.getenv("PLATFORM_QUOTA_SALT") or os.getenv("OPENAI_API_KEY", "")
    return hashlib.sha256((salt + "|" + candidate).encode("utf-8")).hexdigest()[:24]

def reserve_platform_request(request: Request) -> None:
    if not shared_quota_ready():
        raise HTTPException(status_code=503, detail="平台 AI 暂未开放。你可以在 AI 设置中使用自己的 API。")
    endpoint = os.getenv("UPSTASH_REDIS_REST_URL", "").strip().rstrip("/")
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(".upstash.io") or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise HTTPException(status_code=503, detail="平台额度服务配置异常，请稍后重试。")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()
    visitor = _visitor_fingerprint(request)
    now = int(time.time())
    date = datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y%m%d")
    minute = now // 60
    keys = [
        f"yj:quota:all:day:{date}", f"yj:quota:ip:day:{date}:{visitor}",
        f"yj:quota:all:min:{minute}", f"yj:quota:ip:min:{minute}:{visitor}",
    ]
    limits = [
        _limit("PLATFORM_GLOBAL_DAILY_LIMIT", 60),
        _limit("PLATFORM_IP_DAILY_LIMIT", 5),
        _limit("PLATFORM_GLOBAL_MINUTE_LIMIT", 8),
        _limit("PLATFORM_IP_MINUTE_LIMIT", 2),
    ]
    command = ["EVAL", QUOTA_SCRIPT, str(len(keys)), *keys, *[str(x) for x in limits], "172800", "172800", "180", "180"]
    try:
        with httpx.Client(timeout=4.0, follow_redirects=False) as client:
            result = client.post(endpoint, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json=command)
            result.raise_for_status()
            payload = result.json()
        if "error" in payload:
            raise RuntimeError("quota command failed")
        rejection = int(payload["result"])
    except (httpx.HTTPError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail="平台额度服务暂不可用，请稍后重试或使用自己的 API。") from exc
    if rejection:
        message = "平台今日免费体验额度已用完，请明天再试或使用自己的 API。" if rejection <= 2 else "操作过于频繁，请稍后再试。"
        raise HTTPException(status_code=429, detail=message, headers={"Retry-After": "60" if rejection >= 3 else "3600"})
