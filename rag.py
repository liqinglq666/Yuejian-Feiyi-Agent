from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SUPPORTED_EXTENSIONS = {".md", ".txt"}


class KnowledgeBaseError(RuntimeError):
    pass


def read_text_file(path: Path) -> str:
    last_error: Exception | None = None
    for encoding in ("utf-8", "utf-8-sig", "gbk", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except (UnicodeDecodeError, OSError) as exc:
            last_error = exc

    logger.error("Knowledge file unreadable: %s", path, exc_info=last_error)
    raise KnowledgeBaseError(f"知识库文件读取失败：{path.name}") from last_error


@lru_cache(maxsize=1)
def load_knowledge_base() -> str:
    if not DATA_DIR.exists():
        raise KnowledgeBaseError("知识库目录不存在，请检查 data 目录。")

    texts: list[str] = []
    files = [
        path
        for path in sorted(DATA_DIR.rglob("*"))
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    if not files:
        raise KnowledgeBaseError("知识库目录中没有可用的 Markdown 或 TXT 文件。")

    for path in files:
        content = read_text_file(path).strip()
        if not content:
            continue
        relative_path = path.relative_to(BASE_DIR).as_posix()
        texts.append(f"\n\n# 来源文件：{relative_path}\n\n{content}")

    if not texts:
        raise KnowledgeBaseError("知识库文件为空，RAG 已停止。")
    return "\n".join(texts).strip()


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_into_chunks(text: str, max_chars: int = 900, overlap: int = 120) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []

    chunks: list[str] = []
    current = ""
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        if len(current) + len(paragraph) + 2 <= max_chars:
            current = f"{current}\n\n{paragraph}".strip()
            continue

        if current:
            chunks.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
            continue

        start = 0
        while start < len(paragraph):
            end = start + max_chars
            chunks.append(paragraph[start:end])
            start = max(start + 1, end - overlap)
        current = ""

    if current:
        chunks.append(current)
    return chunks


@lru_cache(maxsize=1)
def get_knowledge_chunks() -> list[str]:
    chunks = split_into_chunks(load_knowledge_base())
    if not chunks:
        raise KnowledgeBaseError("知识库切分结果为空，RAG 已停止。")
    return chunks


def extract_keywords(query: str) -> list[str]:
    query = query.strip().lower()
    stopwords = {
        "我", "想", "请", "帮我", "一个", "一下", "可以", "需要", "生成",
        "介绍", "广东", "岭南", "非遗", "文化", "的", "了", "和", "与", "或",
        "在", "有", "是", "吗", "呢", "吧", "用", "给", "做", "写",
    }
    keywords: set[str] = {
        word.lower()
        for word in re.findall(r"[a-zA-Z0-9_]+", query)
        if len(word) >= 2
    }

    for block in re.findall(r"[\u4e00-\u9fff]+", query):
        if len(block) <= 1:
            continue
        if block not in stopwords and len(block) <= 12:
            keywords.add(block)
        for size in (2, 3, 4):
            for index in range(max(0, len(block) - size + 1)):
                token = block[index:index + size]
                if token not in stopwords:
                    keywords.add(token)

    domain_terms = [
        "粤剧", "醒狮", "广绣", "龙舟", "潮汕", "工夫茶", "英歌舞",
        "佛山", "陶塑", "石湾", "陈家祠", "永庆坊", "西关", "骑楼",
        "灰塑", "木雕", "砖雕", "广州", "深圳", "珠海", "江门",
        "梅州", "潮州", "汕头", "研学", "路线", "任务卡",
        "小红书", "短视频", "脚本", "亲子", "拍照", "导览",
    ]
    for term in domain_terms:
        if term.lower() in query:
            keywords.add(term.lower())
    return sorted(keywords, key=len, reverse=True)


def score_chunk(chunk: str, keywords: list[str]) -> float:
    if not chunk or not keywords:
        return 0.0

    text = chunk.lower()
    score = 0.0
    for keyword in keywords:
        count = text.count(keyword)
        if count:
            score += count * (1.0 + min(len(keyword), 8) / 4)
    if chunk.strip().startswith("#"):
        score *= 1.15
    return score


def retrieve_context(
    query: str,
    top_k: int = 4,
    max_total_chars: int = 2800,
) -> str:
    chunks = get_knowledge_chunks()
    keywords = extract_keywords(query)
    if not keywords:
        return ""

    scored = sorted(
        ((score_chunk(chunk, keywords), chunk) for chunk in chunks),
        key=lambda item: item[0],
        reverse=True,
    )
    candidates = [chunk for score, chunk in scored[:top_k] if score > 0]
    if not candidates:
        return ""

    selected: list[str] = []
    total_chars = 0
    for chunk in candidates:
        if total_chars + len(chunk) > max_total_chars:
            remaining = max_total_chars - total_chars
            if remaining > 300:
                selected.append(chunk[:remaining])
            break
        selected.append(chunk)
        total_chars += len(chunk)
    return "\n\n---\n\n".join(selected).strip()


def clear_cache() -> None:
    load_knowledge_base.cache_clear()
    get_knowledge_chunks.cache_clear()


if __name__ == "__main__":
    print(retrieve_context("广州一天非遗路线，想看粤剧、醒狮和岭南建筑"))
