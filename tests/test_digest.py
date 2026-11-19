"""归档 Markdown 渲染与 id 规范化。"""
from ids import normalize_id, title_key
from digest import archive_markdown, format_date, topic_summary


def paper(pid="2611.00001", topic="Web 前后端开发"):
    return {
        "id": pid,
        "title": "A Test Paper",
        "title_zh": "测试论文",
        "abstract_zh": "中文摘要",
        "abstract": "English abstract",
        "url": f"https://arxiv.org/abs/{pid}",
        "pdf": f"https://arxiv.org/pdf/{pid}",
        "published": "2026-11-06",
        "topic": topic,
        "categories": ["cs.SE"],
        "authors": ["Alice"],
        "citations": 0,
        "influential_citations": 0,
    }


def test_format_date_without_leading_zeros():
    assert format_date("2026-11-09") == "2026年11月9日"


def test_archive_markdown_has_title_abstract_and_links():
    text = archive_markdown([paper()], "2026-11-09")
    assert "# 📚 每周论文精选 · 2026年11月9日" in text
    assert "## 1. 测试论文" in text
    assert "**[A Test Paper](https://arxiv.org/abs/2611.00001)**" in text
    assert "中文摘要" in text
    assert "https://arxiv.org/abs/2611.00001" in text
    assert "[PDF](https://arxiv.org/pdf/2611.00001)" in text


def test_archive_markdown_counts_topics():
    papers = [paper("1"), paper("2"), paper("3", "计算机图形学与游戏")]
    assert topic_summary(papers) == "Web 前后端开发 2 · 计算机图形学与游戏 1"


def test_normalize_id_strips_version():
    assert normalize_id("2611.09693v1") == "2611.09693"
    assert normalize_id("2611.09693v12") == "2611.09693"
    assert normalize_id("2611.09693") == "2611.09693"
    # 老式 id 里带字母 v 也不能被误伤
    assert normalize_id("hep-th/9901001v2") == "hep-th/9901001"


def test_title_key_ignores_case_and_punctuation():
    assert title_key("Deep Learning: A Survey!") == title_key("deep learning a survey")
