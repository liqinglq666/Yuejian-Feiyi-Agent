from __future__ import annotations

import re
from datetime import datetime
from io import BytesIO

from docx import Document
from docx.document import Document as DocumentObject

from core.models import TaskRequest

_TABLE_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")


def build_markdown(request: TaskRequest, answer: str, sources: str = "") -> str:
    parts = [
        "# 粤见非遗生成结果",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 原始需求",
        request.raw_request.strip(),
        "",
        answer.strip(),
    ]
    if sources.strip():
        parts.extend(["", sources.strip()])
    return "\n".join(parts).strip() + "\n"


def _clean_inline_markdown(text: str) -> str:
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    value = re.sub(r"\*\*(.+?)\*\*", r"\1", value)
    value = re.sub(r"__(.+?)__", r"\1", value)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    return value.strip()


def build_plain_text(request: TaskRequest, answer: str, sources: str = "") -> str:
    markdown = build_markdown(request, answer, sources)
    text = re.sub(r"^#{1,6}\s+", "", markdown, flags=re.MULTILINE)
    return _clean_inline_markdown(text)


def _split_markdown_table_row(line: str) -> list[str]:
    value = line.strip()
    if "|" not in value:
        return []
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    cells = [_clean_inline_markdown(cell) for cell in value.split("|")]
    return cells if len(cells) >= 2 else []


def _is_markdown_table_separator(line: str) -> bool:
    cells = _split_markdown_table_row(line)
    if not cells:
        return False
    return all(_TABLE_SEPARATOR_CELL.fullmatch(cell.replace(" ", "")) for cell in cells)


def _add_markdown_table(
    document: DocumentObject,
    header: list[str],
    rows: list[list[str]],
) -> None:
    table = document.add_table(rows=1, cols=len(header))
    table.style = "Table Grid"
    for index, value in enumerate(header):
        table.rows[0].cells[index].text = value

    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            cells[index].text = value


def _append_answer(document: DocumentObject, answer: str) -> None:
    lines = answer.splitlines()
    index = 0

    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            continue

        header = _split_markdown_table_row(stripped)
        has_table_separator = (
            bool(header)
            and index + 1 < len(lines)
            and _is_markdown_table_separator(lines[index + 1])
        )
        if has_table_separator:
            rows: list[list[str]] = []
            cursor = index + 2
            while cursor < len(lines):
                row = _split_markdown_table_row(lines[cursor])
                if not row or _is_markdown_table_separator(lines[cursor]):
                    break
                if len(row) != len(header):
                    break
                rows.append(row)
                cursor += 1
            _add_markdown_table(document, header, rows)
            index = cursor
            continue

        if stripped.startswith("### "):
            document.add_heading(_clean_inline_markdown(stripped[4:]), level=2)
        elif stripped.startswith("## "):
            document.add_heading(_clean_inline_markdown(stripped[3:]), level=1)
        elif stripped.startswith("- "):
            document.add_paragraph(
                _clean_inline_markdown(stripped[2:]),
                style="List Bullet",
            )
        else:
            document.add_paragraph(_clean_inline_markdown(stripped))
        index += 1


def build_docx(request: TaskRequest, answer: str, sources: str = "") -> bytes:
    document = Document()
    document.add_heading("粤见非遗生成结果", level=0)
    document.add_paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    document.add_heading("原始需求", level=1)
    document.add_paragraph(request.raw_request.strip())

    _append_answer(document, answer)

    if sources.strip():
        document.add_heading("本次检索资料", level=1)
        for line in sources.splitlines():
            stripped = line.strip()
            if stripped.startswith("- "):
                document.add_paragraph(
                    _clean_inline_markdown(stripped[2:]),
                    style="List Bullet",
                )

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()
