"""精读页渲染：锚点、转义、文件落盘与往期索引。"""
import json

from reader import render_issue, save_issue, save_index


def paper(pid="2611.00001", title_zh="测试论文 <script>", topic="AI 编码 / 编程代理"):
    return {
        "id": pid,
        "title": "A Test Paper",
        "title_zh": title_zh,
        "abstract_zh": "中文摘要",
        "abstract": "English abstract",
        "url": f"https://arxiv.org/abs/{pid}",
        "pdf": f"https://arxiv.org/pdf/{pid}",
        "published": "2026-11-19",
        "topic": topic,
        "categories": ["cs.SE"],
        "authors": ["Alice"],
    }


def brief():
    return {
        "one_liner": "一句话",
        "background": "背景",
        "why": "为什么",
        "how": "怎么做。类比：像做菜。",
        "results": "结果 12%",
        "terms": [{"term": "术语", "plain": "大白话"}],
        "takeaway": "只记一件事",
        "self_check": ["问题一", "问题二"],
        "reading": "扫读即可",
    }


def test_render_contains_anchor_and_sections():
    html = render_issue([paper()], {"2611.00001": brief()}, "2026-11-19")
    assert 'id="p1"' in html
    assert "一句话" in html
    assert "它要解决什么" in html
    assert "如果只记一件事" in html
    assert "https://arxiv.org/abs/2611.00001" in html
    assert "2026 / 11 / 19" in html


def test_render_escapes_html():
    html = render_issue([paper(title_zh="<script>alert(1)</script>")], {}, "2026-11-19")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_save_issue_writes_page_and_briefs(tmp_path):
    page = save_issue([paper()], {"2611.00001": brief()}, "2026-11-19", base_dir=tmp_path)
    assert page.exists()
    assert (tmp_path / "2026-11-19" / "briefs.json").exists()
    assert json.loads((tmp_path / "2026-11-19" / "briefs.json").read_text(encoding="utf-8"))[
        "2611.00001"
    ]["one_liner"] == "一句话"


def test_save_index_lists_issues_newest_first(tmp_path):
    for date in ["2026-11-12", "2026-11-19"]:
        save_issue([paper()], {"2611.00001": brief()}, date, base_dir=tmp_path)
    page = save_index(base_dir=tmp_path)

    html = page.read_text(encoding="utf-8")
    assert html.index("2026-11-19/") < html.index("2026-11-12/")
    assert "2 期" in html


def test_render_has_sidebar_nav_and_drawer():
    papers = [paper("2611.00001"), paper("2611.00002", title_zh="第二篇")]
    html = render_issue(papers, {}, "2026-11-19")

    assert 'class="sidebar"' in html
    assert 'class="nav"' in html
    assert 'href="#p1"' in html
    assert 'href="#p2"' in html
    assert 'class="menu-btn"' in html
    assert "IntersectionObserver" in html


def test_save_issue_writes_papers_json(tmp_path):
    save_issue([paper()], {"2611.00001": brief()}, "2026-11-19", base_dir=tmp_path)
    data = json.loads((tmp_path / "2026-11-19" / "papers.json").read_text(encoding="utf-8"))
    assert data[0]["id"] == "2611.00001"
