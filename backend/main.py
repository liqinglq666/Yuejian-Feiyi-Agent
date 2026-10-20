"""Vercel Services adapter.

The API is mounted at /api to match Next.js same-origin /api/v1 requests.
Core functionality remains in api.main.
"""
from __future__ import annotations

from fastapi import FastAPI

from api.main import app as api_app

app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
app.mount("/api", api_app)
