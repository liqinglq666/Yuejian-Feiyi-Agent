from __future__ import annotations

import re


def sanitize_model_output(text: str) -> str:
    if not text:
        return ""

    cleaned = str(text)
    cleaned = re.sub(r"(?i)&lt;\s*br\s*/?\s*&gt;", "；", cleaned)
    cleaned = re.sub(r"(?i)<\s*br\s*/?\s*>", "；", cleaned)
    cleaned = cleaned.replace("&nbsp;", " ").replace("&amp;", "&")
    cleaned = cleaned.replace("&lt;", "<").replace("&gt;", ">")
    cleaned = re.sub(r"^#\s+", "## ", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*；\s*；+\s*", "；", cleaned)

    lines: list[str] = []
    for line in cleaned.splitlines():
        stripped = line.strip()
        if re.fullmatch(r"\d+\s*[.)、．]?", stripped):
            continue
        if re.fullmatch(r"[-*+•]\s*", stripped):
            continue
        lines.append(line.rstrip().replace("• ", "- "))

    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
