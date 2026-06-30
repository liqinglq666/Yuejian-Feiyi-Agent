"""
rag.py
粤见非遗本地知识库检索模块。

稳定版特点：
1. data 路径基于当前文件位置，避免运行目录变化导致读不到知识库。
2. 默认 top_k=4，max_total_chars=2800，兼顾速度和上下文质量。
3. 没有相关片段时返回空字符串，避免把无关知识强塞给模型。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

SUPPORTED_EXTENSIONS = {
    ".md",
    ".txt",
}


def read_text_file(path: Path) -> str:
    """
    尝试用常见编码读取文本文件。
    """
    encodings = ["utf-8", "utf-8-sig", "gbk", "gb18030"]

    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except Exception:
            continue

    return ""


@lru_cache(maxsize=1)
def load_knowledge_base() -> str:
    """
    读取 data 文件夹下所有 Markdown / TXT 文件。
    """
    if not DATA_DIR.exists():
        return ""

    texts: list[str] = []

    for path in sorted(DATA_DIR.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            content = read_text_file(path).strip()

            if content:
                relative_path = path.relative_to(BASE_DIR).as_posix()
                texts.append(f"\n\n# 来源文件：{relative_path}\n\n{content}")

    return "\n".join(texts).strip()


def normalize_text(text: str) -> str:
    """
    简单清洗文本。
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_into_chunks(
    text: str,
    max_chars: int = 900,
    overlap: int = 120,
) -> list[str]:
    """
    将知识库文本切分为较短片段。
    """
    text = normalize_text(text)

    if not text:
        return []

    paragraphs = re.split(r"\n\s*\n", text)
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        para = para.strip()

        if not para:
            continue

        if len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}".strip()
        else:
            if current:
                chunks.append(current)

            if len(para) <= max_chars:
                current = para
            else:
                start = 0
                while start < len(para):
                    end = start + max_chars
                    chunks.append(para[start:end])
                    start = max(0, end - overlap)

                current = ""

    if current:
        chunks.append(current)

    return chunks


@lru_cache(maxsize=1)
def get_knowledge_chunks() -> list[str]:
    """
    缓存知识库片段。
    """
    kb = load_knowledge_base()
    return split_into_chunks(kb)


def extract_keywords(query: str) -> list[str]:
    """
    从用户问题中提取关键词。
    兼容中文和英文。
    """
    query = query.strip().lower()

    stopwords = {
        "我", "想", "请", "帮我", "一个", "一下", "可以", "需要", "生成",
        "介绍", "广东", "岭南", "非遗", "文化", "的", "了", "和", "与", "或",
        "在", "有", "是", "吗", "呢", "吧", "用", "给", "做", "写",
    }

    keywords: set[str] = set()

    # 英文、数字、拼音词
    for word in re.findall(r"[a-zA-Z0-9_]+", query):
        if len(word) >= 2:
            keywords.add(word.lower())

    # 中文连续片段
    chinese_blocks = re.findall(r"[\u4e00-\u9fff]+", query)

    for block in chinese_blocks:
        if len(block) <= 1:
            continue

        if block not in stopwords and len(block) <= 12:
            keywords.add(block)

        # 加入 2-4 字 ngram，提升中文检索召回
        for n in [2, 3, 4]:
            for i in range(0, max(0, len(block) - n + 1)):
                token = block[i : i + n]

                if token not in stopwords:
                    keywords.add(token)

    # 广东非遗高价值词强化
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
    """
    根据关键词命中情况给片段打分。
    """
    if not chunk or not keywords:
        return 0.0

    text = chunk.lower()
    score = 0.0

    for keyword in keywords:
        if not keyword:
            continue

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
    """
    检索与用户问题最相关的知识片段。
    没有命中时返回空字符串，交给模型进行谨慎回答。
    """
    chunks = get_knowledge_chunks()

    if not chunks:
        return ""

    keywords = extract_keywords(query)

    if not keywords:
        return ""

    scored_chunks: list[tuple[float, str]] = []

    for chunk in chunks:
        score = score_chunk(chunk, keywords)

        if score > 0:
            scored_chunks.append((score, chunk))

    if not scored_chunks:
        return ""

    scored_chunks.sort(key=lambda item: item[0], reverse=True)
    candidate_chunks = [chunk for _, chunk in scored_chunks[:top_k]]

    selected: list[str] = []
    total_chars = 0

    for chunk in candidate_chunks:
        if total_chars + len(chunk) > max_total_chars:
            remaining = max_total_chars - total_chars

            if remaining > 300:
                selected.append(chunk[:remaining])

            break

        selected.append(chunk)
        total_chars += len(chunk)

    return "\n\n---\n\n".join(selected).strip()


def clear_cache() -> None:
    """
    知识库文件更新后，可手动清理缓存。
    """
    load_knowledge_base.cache_clear()
    get_knowledge_chunks.cache_clear()


if __name__ == "__main__":
    q = "广州一天非遗路线，想看粤剧、醒狮和岭南建筑"
    print(retrieve_context(q))
