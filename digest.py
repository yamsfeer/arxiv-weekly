"""渲染层：归档 Markdown 与飞书卡片文案都从同一份论文数据生成，避免两处格式漂移。"""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional


def format_date(date_str: str) -> str:
    """2026-11-09 -> 2026年11月9日"""
    try:
        d = date.fromisoformat(date_str)
    except ValueError:
        return date_str
    return f"{d.year}年{d.month}月{d.day}日"


def citation_label(paper: Dict) -> str:
    citations = paper.get("citations", 0)
    influential = paper.get("influential_citations", 0)
    if not citations:
        return "🆕 新论文"
    label = f"📊 被引 {citations} 次"
    if influential:
        label += f"（高影响 {influential}）"
    return label


def topic_summary(papers: List[Dict]) -> str:
    """按话题统计，例如「Web 前后端开发 3 · 图形学 3 · …」，保持首次出现顺序。"""
    counts: Dict[str, int] = {}
    for paper in papers:
        counts[paper["topic"]] = counts.get(paper["topic"], 0) + 1
    return " · ".join(f"{topic} {count}" for topic, count in counts.items())


def paper_view(paper: Dict, index: int) -> Dict[str, str]:
    """把一篇论文摊平成渲染需要的字段。"""
    authors = paper.get("authors") or []
    meta = [paper["topic"], paper.get("published", ""), citation_label(paper)]
    if paper.get("categories"):
        meta.append(" / ".join(paper["categories"]))
    return {
        "index": str(index),
        "title_zh": paper.get("title_zh") or paper["title"],
        "title": paper["title"],
        "url": paper["url"],
        "pdf": paper.get("pdf") or paper["url"],
        "arxiv_id": paper["id"],
        "meta": " · ".join(part for part in meta if part),
        "abstract": paper.get("abstract_zh") or paper["abstract"],
        "authors": "、".join(authors),
    }


def archive_markdown(papers: List[Dict], date_str: str, repo_url: Optional[str] = None) -> str:
    """生成 papers/YYYY-MM-DD.md 的内容。"""
    lines = [
        f"# 📚 每周论文精选 · {format_date(date_str)}",
        "",
        f"> 共 {len(papers)} 篇 · {topic_summary(papers)}",
        "",
    ]

    for i, paper in enumerate(papers, 1):
        view = paper_view(paper, i)
        lines += [
            f"## {i}. {view['title_zh']}",
            "",
            f"**[{view['title']}]({view['url']})**",
            "",
            f"{view['meta']}",
            "",
            view["abstract"],
            "",
        ]
        if view["authors"]:
            lines += [f"✍️ {view['authors']}", ""]
        lines += [
            f"[arXiv:{view['arxiv_id']}]({view['url']}) · [PDF]({view['pdf']})",
            "",
            "---",
            "",
        ]

    footer = "由 GitHub Actions + DeepSeek 自动生成 · 数据来源 arXiv & Semantic Scholar"
    if repo_url:
        footer = f"[{footer}]({repo_url})"
    lines.append(f"*{footer}*")
    return "\n".join(lines).rstrip() + "\n"


def card_paper_markdown(paper: Dict, index: int) -> str:
    """飞书卡片里单篇论文的 lark_md 片段。"""
    view = paper_view(paper, index)
    return (
        f"**[{view['index']}. {view['title_zh']}]({view['url']})**\n"
        f"*{view['title']}*\n"
        f"{view['meta']}\n\n"
        f"{view['abstract']}"
    )


def plain_text(papers: List[Dict], date_str: str) -> str:
    """纯文本版，用于日志排查或不支持卡片的环境。"""
    lines = [f"每周论文精选 · {format_date(date_str)}（{len(papers)} 篇）", ""]
    for i, paper in enumerate(papers, 1):
        view = paper_view(paper, i)
        lines += [
            f"{i}. {view['title_zh']}",
            f"   {view['title']}",
            f"   {view['meta']}",
            f"   {view['url']}",
            "",
        ]
    return "\n".join(lines)
