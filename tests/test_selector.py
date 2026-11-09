"""选题逻辑：话题配额、去重、补满。"""
from selector import select_papers

QUOTAS = {
    "Web 前后端开发": 3,
    "计算机图形学与游戏": 3,
    "AI 辅助软件开发": 2,
    "AI 应用开发": 2,
}


def paper(pid, topic, relevance=0, citations=0, published="2026-11-01"):
    return {
        "id": pid,
        "topic": topic,
        "relevance": relevance,
        "citations": citations,
        "published": published,
    }


def test_web_gets_at_least_three_slots_even_if_graphics_has_higher_scores():
    # 图形学论文分数远高于 Web（复现线上 7:1 的分布）
    papers = [paper(f"gr{i}", "计算机图形学与游戏", relevance=10) for i in range(10)]
    papers += [paper(f"web{i}", "Web 前后端开发", relevance=1) for i in range(5)]
    papers += [paper("se1", "AI 辅助软件开发", relevance=5)]
    papers += [paper("app1", "AI 应用开发", relevance=5)]

    selected = select_papers(papers, quotas=QUOTAS, max_papers=10)

    assert len(selected) == 10
    assert sum(p["topic"] == "Web 前后端开发" for p in selected) == 3


def test_every_topic_gets_its_quota_when_supply_is_enough():
    papers = []
    for topic, quota in QUOTAS.items():
        papers += [paper(f"{topic}-{i}", topic, relevance=1) for i in range(6)]

    selected = select_papers(papers, quotas=QUOTAS, max_papers=10)

    counts = {}
    for p in selected:
        counts[p["topic"]] = counts.get(p["topic"], 0) + 1
    assert counts == QUOTAS


def test_seen_papers_are_excluded():
    papers = [paper("a", "Web 前后端开发", relevance=3), paper("b", "Web 前后端开发", relevance=2)]
    selected = select_papers(papers, quotas={"Web 前后端开发": 3}, max_papers=10, seen_ids={"a"})
    assert [p["id"] for p in selected] == ["b"]


def test_missing_topic_supply_is_filled_by_the_best_remaining():
    papers = [paper(f"web{i}", "Web 前后端开发", relevance=1) for i in range(1)]
    papers += [paper(f"gr{i}", "计算机图形学与游戏", relevance=10 - i) for i in range(5)]

    selected = select_papers(papers, quotas=QUOTAS, max_papers=4)

    # Web 只有 1 篇，剩下的名额按分数补给图形学
    assert len(selected) == 4
    assert sum(p["topic"] == "Web 前后端开发" for p in selected) == 1


def test_max_papers_is_respected_and_topics_stay_grouped():
    papers = []
    for topic in QUOTAS:
        papers += [paper(f"{topic}-{i}", topic, relevance=i) for i in range(5)]

    selected = select_papers(papers, quotas=QUOTAS, max_papers=3)

    assert len(selected) == 3
    # 展示顺序按话题分组，Web 在最前
    assert selected[0]["topic"] == "Web 前后端开发"


def test_within_topic_higher_score_first():
    papers = [
        paper("low", "计算机图形学与游戏", relevance=1),
        paper("high", "计算机图形学与游戏", relevance=9),
    ]
    selected = select_papers(papers, quotas={"计算机图形学与游戏": 2}, max_papers=2)
    assert [p["id"] for p in selected] == ["high", "low"]
