"""
将每周精选论文保存为 Markdown 文件到 papers/ 目录
"""
from datetime import datetime
from pathlib import Path
from typing import List, Dict

PAPERS_DIR = Path("papers")


def _citation_tag(paper: Dict) -> str:
    citations = paper.get("citations", 0)
    influential = paper.get("influential_citations", 0)
    if citations == 0:
        return "🆕 新论文·暂无引用数据"
    tag = f"📊 被引 **{citations}** 次"
    if influential:
        tag += f"，高影响引用 **{influential}** 次"
    return tag


def build_markdown(papers: List[Dict], date_str: str) -> str:
    lines = [
        f"# 📚 每周论文推荐 · {date_str}",
        "",
        f"> 共 {len(papers)} 篇 · 由 GitHub Actions + DeepSeek 自动生成",
        "",
    ]

    for i, p in enumerate(papers, 1):
        title_zh = p.get("title_zh", p["title"])
        abstract_zh = p.get("abstract_zh", p["abstract"])
        authors = "、".join(p.get("authors", []))
        citation_tag = _citation_tag(p)

        lines += [
            f"## {i}. {title_zh}",
            "",
            f"**原标题：** {p['title']}",
            "",
            f"| 字段 | 内容 |",
            f"|------|------|",
            f"| 话题 | {p['topic']} |",
            f"| 发布时间 | {p['published']} |",
            f"| 流行度 | {citation_tag} |",
            f"| 作者 | {authors} |",
            f"| 链接 | [{p['id']}]({p['url']}) |",
            "",
            "**摘要：**",
            "",
            abstract_zh,
            "",
            "---",
            "",
        ]

    return "\n".join(lines)


def save_papers(papers: List[Dict]) -> Path:
    """保存论文到 papers/YYYY-MM-DD.md，返回文件路径"""
    PAPERS_DIR.mkdir(exist_ok=True)
    date_str = datetime.now().strftime("%Y年%m月%d日")
    filename = datetime.now().strftime("%Y-%m-%d") + ".md"
    filepath = PAPERS_DIR / filename

    content = build_markdown(papers, date_str)
    filepath.write_text(content, encoding="utf-8")
    print(f"[saver] 已保存到 {filepath}")
    return filepath
