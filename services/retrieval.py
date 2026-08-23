from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from core.models import GUANGDONG_CITIES, RetrievalBundle, RetrievedChunk

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = BASE_DIR / "data"
SUPPORTED_EXTENSIONS = {".md", ".txt"}


class KnowledgeBaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class IndexedChunk:
    chunk_id: str
    content: str
    source_path: str
    title: str
    city: str
    category: str
    source_name: str
    source_url: str
    tokens: tuple[str, ...]
    char_ngrams: Counter[str]


@dataclass(frozen=True)
class SearchIndex:
    chunks: tuple[IndexedChunk, ...]
    document_frequency: Counter[str]
    average_length: float


STOPWORDS = {
    "我", "想", "请", "帮我", "一个", "一下", "可以", "需要", "生成", "介绍",
    "广东", "岭南", "非遗", "文化", "的", "了", "和", "与", "或", "在", "有",
    "是", "吗", "呢", "吧", "用", "给", "做", "写", "方案", "输出", "表格",
}

CITY_TERMS = GUANGDONG_CITIES

CATEGORY_TERMS = (
    "传统戏剧", "传统舞蹈", "传统音乐", "传统美术", "传统技艺", "民俗", "曲艺",
    "传统体育", "医药", "文学",
)

DOMAIN_TERMS = (
    "粤剧", "醒狮", "广绣", "龙舟", "潮汕工夫茶", "英歌舞", "石湾陶塑", "香云纱",
    "客家山歌", "灰塑", "木雕", "砖雕", "陈家祠", "永庆坊", "西关", "骑楼",
)


def read_text_file(path: Path) -> str:
    last_error: Exception | None = None
    for encoding in ("utf-8", "utf-8-sig", "gbk", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except (UnicodeDecodeError, OSError) as exc:
            last_error = exc
    raise KnowledgeBaseError(f"知识库文件读取失败：{path.name}") from last_error


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, flags=re.DOTALL)
    if not match:
        return {}, text

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip().strip('"\'')
    return metadata, text[match.end() :]


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_markdown_with_context(
    text: str,
    max_chars: int = 850,
    overlap: int = 100,
) -> list[tuple[str, str, str]]:
    """Split Markdown while retaining its heading hierarchy for metadata inference."""
    text = normalize_text(text)
    if not text:
        return []

    sections: list[tuple[str, str, str]] = []
    heading_stack: dict[int, str] = {}
    current_title = ""
    current_context = ""
    current_lines: list[str] = []

    def flush_section() -> None:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append((current_title, current_context, body))

    for line in text.splitlines():
        heading = re.match(r"^(#{1,4})\s+(.+?)\s*$", line)
        if heading:
            flush_section()
            current_lines.clear()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            heading_stack[level] = title
            for deeper in [key for key in heading_stack if key > level]:
                del heading_stack[deeper]
            current_title = title
            current_context = " / ".join(
                heading_stack[key] for key in sorted(heading_stack) if key <= level
            )
        else:
            current_lines.append(line)
    flush_section()

    chunks: list[tuple[str, str, str]] = []
    for title, context, body in sections:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", body) if part.strip()]
        current = ""
        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}".strip()
            if len(candidate) <= max_chars:
                current = candidate
                continue
            if current:
                chunks.append((title, context, current))
            if len(paragraph) <= max_chars:
                current = paragraph
                continue
            start = 0
            while start < len(paragraph):
                end = min(len(paragraph), start + max_chars)
                chunks.append((title, context, paragraph[start:end]))
                if end == len(paragraph):
                    break
                start = max(start + 1, end - overlap)
            current = ""
        if current:
            chunks.append((title, context, current))
    return chunks


def split_markdown(text: str, max_chars: int = 850, overlap: int = 100) -> list[tuple[str, str]]:
    """Public compatibility helper returning only title and content."""
    return [
        (title, content)
        for title, _context, content in _split_markdown_with_context(text, max_chars, overlap)
    ]


def tokenize(text: str) -> list[str]:
    normalized = text.lower()
    tokens: list[str] = []
    tokens.extend(
        word
        for word in re.findall(r"[a-z0-9_]+", normalized)
        if len(word) >= 2 and word not in STOPWORDS
    )
    for block in re.findall(r"[\u4e00-\u9fff]+", normalized):
        if block not in STOPWORDS and 1 < len(block) <= 16:
            tokens.append(block)
        for size in (2, 3, 4):
            for index in range(max(0, len(block) - size + 1)):
                token = block[index : index + size]
                if token not in STOPWORDS:
                    tokens.append(token)
    for term in DOMAIN_TERMS + CITY_TERMS:
        if term.lower() in normalized:
            tokens.append(term.lower())
    return tokens


def char_ngrams(text: str, size: int = 3) -> Counter[str]:
    compact = re.sub(r"\s+", "", text.lower())
    if len(compact) < size:
        return Counter({compact: 1}) if compact else Counter()
    return Counter(compact[index : index + size] for index in range(len(compact) - size + 1))


def infer_city(text: str) -> str:
    return next((city for city in CITY_TERMS if city in text), "")


def infer_category(text: str) -> str:
    return next((category for category in CATEGORY_TERMS if category in text), "")


def _metadata_value(metadata: dict[str, str], *names: str) -> str:
    for name in names:
        value = metadata.get(name)
        if value:
            return value
    return ""


def _document_signature(data_dir: Path) -> tuple[tuple[str, int, int], ...]:
    if not data_dir.exists():
        return ()
    records: list[tuple[str, int, int]] = []
    for path in sorted(data_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            stat = path.stat()
            records.append((path.as_posix(), stat.st_mtime_ns, stat.st_size))
    return tuple(records)


def build_index(data_dir: Path = DEFAULT_DATA_DIR) -> SearchIndex:
    if not data_dir.exists():
        raise KnowledgeBaseError("知识库目录不存在，请检查 data 目录。")

    files = [
        path
        for path in sorted(data_dir.rglob("*"))
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    if not files:
        raise KnowledgeBaseError("知识库目录中没有 Markdown 或 TXT 文件。")

    indexed: list[IndexedChunk] = []
    for path in files:
        raw = read_text_file(path)
        metadata, body = parse_front_matter(raw)
        default_title = _metadata_value(metadata, "title", "name") or path.stem
        source_path = path.relative_to(data_dir.parent).as_posix()
        fixed_city = _metadata_value(metadata, "city", "城市")
        fixed_category = _metadata_value(metadata, "category", "类别")
        source_name = _metadata_value(metadata, "source_name", "source", "来源")
        source_url = _metadata_value(metadata, "source_url", "url", "链接")

        for position, (heading, context, content) in enumerate(
            _split_markdown_with_context(body), start=1
        ):
            if not content.strip():
                continue
            title = heading or default_title
            context_text = f"{context}\n{title}\n{content}"
            city = fixed_city or infer_city(context_text)
            category = fixed_category or infer_category(context_text)
            digest = hashlib.sha1(
                f"{source_path}:{position}:{context}:{content}".encode()
            ).hexdigest()[:12]
            searchable_text = f"{context} {title} {content}"
            indexed.append(
                IndexedChunk(
                    chunk_id=digest,
                    content=content.strip(),
                    source_path=source_path,
                    title=title,
                    city=city,
                    category=category,
                    source_name=source_name,
                    source_url=source_url,
                    tokens=tuple(tokenize(searchable_text)),
                    char_ngrams=char_ngrams(searchable_text),
                )
            )

    if not indexed:
        raise KnowledgeBaseError("知识库文件为空，无法建立检索索引。")

    document_frequency: Counter[str] = Counter()
    for chunk in indexed:
        document_frequency.update(set(chunk.tokens))
    average_length = sum(len(chunk.tokens) for chunk in indexed) / len(indexed)
    return SearchIndex(tuple(indexed), document_frequency, average_length or 1.0)


@lru_cache(maxsize=4)
def _cached_index(data_dir_text: str, signature: tuple[tuple[str, int, int], ...]) -> SearchIndex:
    del signature
    return build_index(Path(data_dir_text))


def get_index(data_dir: Path = DEFAULT_DATA_DIR) -> SearchIndex:
    resolved = data_dir.resolve()
    return _cached_index(str(resolved), _document_signature(resolved))


def _bm25_score(
    query_tokens: list[str],
    chunk: IndexedChunk,
    index: SearchIndex,
    *,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    if not query_tokens or not chunk.tokens:
        return 0.0
    frequencies = Counter(chunk.tokens)
    length = len(chunk.tokens)
    total_documents = len(index.chunks)
    score = 0.0
    for token in set(query_tokens):
        frequency = frequencies.get(token, 0)
        if not frequency:
            continue
        document_frequency = index.document_frequency.get(token, 0)
        idf = math.log(
            1 + (total_documents - document_frequency + 0.5) / (document_frequency + 0.5)
        )
        denominator = frequency + k1 * (1 - b + b * length / index.average_length)
        score += idf * (frequency * (k1 + 1)) / denominator
    return score


def _cosine(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    common = set(left).intersection(right)
    numerator = sum(left[key] * right[key] for key in common)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def _metadata_boost(query: str, chunk: IndexedChunk) -> float:
    boost = 0.0
    if chunk.city and chunk.city in query:
        boost += 1.0
    if chunk.category and chunk.category in query:
        boost += 0.5
    for term in DOMAIN_TERMS:
        if term in query and (term in chunk.title or term in chunk.content):
            boost += 0.8
    return min(boost, 2.0)


def _normalize_scores(values: list[float]) -> list[float]:
    maximum = max(values, default=0.0)
    if maximum <= 0:
        return [0.0 for _ in values]
    return [value / maximum for value in values]


def _near_duplicate(left: str, right: str) -> bool:
    left_set = set(char_ngrams(left, size=4))
    right_set = set(char_ngrams(right, size=4))
    if not left_set or not right_set:
        return left.strip() == right.strip()
    similarity = len(left_set & right_set) / len(left_set | right_set)
    return similarity >= 0.82


def retrieve(
    query: str,
    *,
    top_k: int = 4,
    max_total_chars: int = 3200,
    data_dir: Path = DEFAULT_DATA_DIR,
) -> RetrievalBundle:
    cleaned_query = query.strip()
    if not cleaned_query:
        return RetrievalBundle(query=query, chunks=(), warnings=("检索查询为空。",))

    index = get_index(data_dir)
    query_tokens = tokenize(cleaned_query)
    query_ngrams = char_ngrams(cleaned_query)

    bm25_values = [_bm25_score(query_tokens, chunk, index) for chunk in index.chunks]
    ngram_values = [_cosine(query_ngrams, chunk.char_ngrams) for chunk in index.chunks]
    metadata_values = [_metadata_boost(cleaned_query, chunk) for chunk in index.chunks]

    bm25_normalized = _normalize_scores(bm25_values)
    metadata_normalized = _normalize_scores(metadata_values)

    ranked: list[tuple[float, IndexedChunk]] = []
    for position, chunk in enumerate(index.chunks):
        score = (
            0.55 * bm25_normalized[position]
            + 0.30 * ngram_values[position]
            + 0.15 * metadata_normalized[position]
        )
        if score > 0.02:
            ranked.append((score, chunk))
    ranked.sort(key=lambda item: item[0], reverse=True)

    selected: list[RetrievedChunk] = []
    total_chars = 0
    for score, chunk in ranked:
        if any(_near_duplicate(chunk.content, existing.content) for existing in selected):
            continue
        remaining = max_total_chars - total_chars
        if remaining <= 250:
            break
        content = chunk.content[:remaining]
        selected.append(
            RetrievedChunk(
                chunk_id=chunk.chunk_id,
                content=content,
                source_path=chunk.source_path,
                title=chunk.title,
                city=chunk.city,
                category=chunk.category,
                source_name=chunk.source_name,
                source_url=chunk.source_url,
                score=round(score, 4),
            )
        )
        total_chars += len(content)
        if len(selected) >= top_k:
            break

    warnings: list[str] = []
    if not selected:
        warnings.append("没有找到高相关知识片段，模型将被要求保守回答。")
    return RetrievalBundle(cleaned_query, tuple(selected), tuple(warnings))


def load_knowledge_base(data_dir: Path = DEFAULT_DATA_DIR) -> str:
    index = get_index(data_dir)
    return "\n\n".join(
        f"# 来源文件：{chunk.source_path}\n\n{chunk.content}" for chunk in index.chunks
    )


def retrieve_context(
    query: str,
    top_k: int = 4,
    max_total_chars: int = 3200,
    data_dir: Path = DEFAULT_DATA_DIR,
) -> str:
    return retrieve(
        query,
        top_k=top_k,
        max_total_chars=max_total_chars,
        data_dir=data_dir,
    ).formatted_context()


def clear_cache() -> None:
    _cached_index.cache_clear()
