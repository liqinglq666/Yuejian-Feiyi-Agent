"""Bounded, real-provider acceptance check; requires a SEPARATE low-budget API key.

Runs the actual FastAPI generate, revise and export endpoints with a real
provider but without the production shared API key or Redis credentials.
Exactly two model streaming calls maximum; no retry, no fallback.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import replace
from urllib.parse import urlparse

from fastapi.testclient import TestClient

from api import main as app_api
from services.llm import stream_chat

ALLOWED = {
    "dashscope.aliyuncs.com": ("https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen3.7-flash"),
    "api.deepseek.com": ("https://api.deepseek.com", "deepseek-v4-flash"),
    "api.openai.com": ("https://api.openai.com/v1", "gpt-5"),
}
MAX_CALLS = 2
MAX_TOKENS = 900


def load_configuration():
    key = os.getenv("YUEJIAN_TEST_API_KEY", "").strip()
    if not key:
        raise ValueError("请先在本地配置独立低额度测试 Key（YUEJIAN_TEST_API_KEY）。")
    if os.getenv("YUEJIAN_TEST_CONFIRM_SEPARATE_KEY") != "YES":
        raise ValueError("请先确认使用独立测试 Key，并在供应商端设置额度上限。")
    base = os.getenv("YUEJIAN_TEST_BASE_URL", ALLOWED["dashscope.aliyuncs.com"][0]).strip()
    hostname = (urlparse(base).hostname or "").lower()
    if urlparse(base).scheme != "https" or hostname not in ALLOWED:
        raise ValueError("仅允许明确列出的可信 HTTPS 模型 API 主机。")
    name = os.getenv("YUEJIAN_TEST_MODEL", ALLOWED[hostname][1]).strip()
    if not name or len(name) > 100:
        raise ValueError("测试模型名称无效。")
    provider = os.getenv("YUEJIAN_TEST_PROVIDER", "阿里云百炼")
    return key, base, name, provider


def frames(payload):
    events = []
    for frame in re.split(r"\r?\n\r?\n", payload):
        if not frame.strip():
            continue
        event = next((s[6:].strip() for s in frame.splitlines() if s.startswith("event:")), "")
        data = [s[5:].lstrip() for s in frame.splitlines() if s.startswith("data:")]
        if event and data:
            events.append((event, json.loads("\n".join(data))))
    return events


def completed(events, label):
    failed = next((v for k, v in events if k == "failure"), None)
    if failed:
        raise ValueError(f"{label}失败：{failed.get('message', '未知错误')}")
    matches = [v for k, v in events if k == "complete"]
    if len(matches) != 1:
        raise ValueError(f"{label}没有收到唯一的 complete 事件。")
    value = matches[0]
    if not value.get("answer", "").strip():
        raise ValueError(f"{label}没有生成正文。")
    if not any(k in {"delta", "snapshot"} for k, _ in events):
        raise ValueError(f"{label}没有流式事件。")
    if value.get("metrics", {}).get("first_token_ms") is None:
        raise ValueError(f"{label}没有首字延迟指标。")
    return value


def main():
    key, base, name, provider = load_configuration()
    os.environ["VERCEL"] = "1"
    calls = 0

    def limited(config, messages, *, temperature):
        nonlocal calls
        if calls >= MAX_CALLS:
            raise RuntimeError("达到模型调用次数上限。")
        calls += 1
        config = replace(config, max_retries=0, timeout_seconds=65.0)
        text = ""
        for part in stream_chat(config, messages, temperature=temperature, max_tokens=MAX_TOKENS):
            text += part
            yield text, False
        yield text, True

    app_api.collect_stream_with_safe_fallback = limited
    client = TestClient(app_api.app, raise_server_exceptions=False)
    req = {
        "scene": "非遗问答", "city": "广州",
        "raw_request": "请介绍广绣的传统文化特色、常见针法和体验注意事项。",
    }
    model = {
        "mode": "user", "provider": provider, "api_key": key,
        "base_url": base, "model_name": name, "temperature": 0.3,
    }
    report = {"model": name, "maximum_provider_calls": MAX_CALLS, "max_tokens_per_call": MAX_TOKENS, "checks": []}
    start = time.monotonic()
    try:
        initial = client.post("/v1/generate", json={"request": req, "model": model}, timeout=90)
        if initial.status_code != 200:
            raise ValueError(f"generate HTTP {initial.status_code}")
        generation = completed(frames(initial.text), "生成")
        if not generation.get("quality", {}).get("official_source_count"):
            raise ValueError("生成结果缺少当前主题对应的官方来源。")
        if "ihchina.cn" not in generation.get("sources", ""):
            raise ValueError("来源链接缺失。")
        report["checks"].append({
            "type": "generate", "passed": True,
            "first_token_ms": generation["metrics"]["first_token_ms"],
            "total_ms": generation["metrics"]["total_ms"],
            "sections_complete": generation["quality"]["sections_complete"],
        })
        revised = client.post("/v1/revise", json={
            "request": req, "model": model,
            "current_answer": generation["answer"][:10000],
            "instruction": "请精炼正文，但保留规定的小标题和具体文化事实的核验提醒。",
        }, timeout=90)
        if revised.status_code != 200:
            raise ValueError(f"revise HTTP {revised.status_code}")
        revision = completed(frames(revised.text), "修改")
        report["checks"].append({
            "type": "revise", "passed": True,
            "first_token_ms": revision["metrics"]["first_token_ms"],
            "total_ms": revision["metrics"]["total_ms"],
            "sections_complete": revision["quality"]["sections_complete"],
        })
        doc = client.post("/v1/export", json={
            "request": req, "answer": revision["answer"],
            "sources": revision["sources"], "format": "md",
        })
        if doc.status_code != 200 or "ihchina.cn" not in doc.text:
            raise ValueError("Markdown 导出未保留可核验来源。")
        report["checks"].append({"type": "export", "passed": True})
        report["status"] = "PASS"
    finally:
        report["actual_provider_calls"] = calls
        report["total_wall_ms"] = round((time.monotonic() - start) * 1000)
        # Never print the key, response payload, or HTTP headers.
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("真实模型验收未通过：" + str(exc), file=sys.stderr)
        sys.exit(1)
