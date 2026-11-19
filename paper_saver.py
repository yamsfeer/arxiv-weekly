"""把每周精选论文写成 Markdown 归档，并维护索引与"最新一期"快捷文件。"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Dict

from config import PAPERS_DIR
from digest import archive_markdown, format_date

LATEST_FILE = "latest.md"
INDEX_FILE = "README.md"
_HEADING = re.compile(r"^## ", re.MULTILINE)
_DATE_FILE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")


def save_papers(papers: List[Dict], date_str: str) -> Path:
    """保存到 papers/YYYY-MM-DD.md，同时刷新 latest.md 与索引。"""
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = PAPERS_DIR / f"{date_str}.md"
    filepath.write_text(archive_markdown(papers, date_str), encoding="utf-8")
    print(f"[saver] 已保存到 {filepath}")

    latest = PAPERS_DIR / LATEST_FILE
    latest.write_text(archive_markdown(papers, date_str), encoding="utf-8")

    write_index()
    return filepath


def _digest_files() -> List[Path]:
    return sorted(
        (p for p in PAPERS_DIR.glob("*.md") if _DATE_FILE.match(p.name)),
        reverse=True,
    )


def write_index(path: Path | None = None) -> Path:
    """重建归档索引，按时间倒序列出每周的篇数与链接。"""
    path = path or PAPERS_DIR / INDEX_FILE
    files = _digest_files()
    lines = [
        "# 论文周报归档",
        "",
        "每周一 09:00（北京时间）自动更新。打开最新一期：[latest.md](latest.md)",
        "",
    ]
    if files:
        latest_date = files[0].stem
        try:
            content = files[0].read_text(encoding="utf-8")
        except OSError:
            content = ""
        count = len(_HEADING.findall(content))
        lines += [
            f"最新一期：**[{format_date(latest_date)}]({files[0].name})** · {count} 篇",
            "",
            "| 日期 | 篇数 | 链接 |",
            "|------|------|------|",
        ]
        for file in files:
            try:
                count = len(_HEADING.findall(file.read_text(encoding="utf-8")))
            except OSError:
                count = 0
            lines.append(f"| {file.stem} | {count} | [{file.stem}]({file.name}) |")
    else:
        lines.append("_还没有任何一期，等待下一次定时任务。_")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path
