"""选题逻辑：主方向配额、图形学替补、去重与补满。"""
from selector import default_caps, default_quotas, select_papers

QUOTAS = default_quotas()
CAPS = default_caps()


def paper(pid, topic, relevance=0, citations=0, published="2026-11-09", **extra):
    data = {
        "id": pid,
        "topic": topic,
        "relevance": relevance,
        "citations": citations,
        "published": published,
    }
    data.update(extra)
    return data


def test_default_quotas_sum_to_six():
    assert sum(QUOTAS.values()) == 6
    assert QUOTAS["AI 编码 / 编程代理"] == 2
    assert QUOTAS["LLM 应用工程"] == 2
    assert QUOTAS["Web 全栈 / 前端工程"] == 1
    assert QUOTAS["开发者工具 / 测试 / 工程效率"] == 1
    assert "计算机图形学与游戏" not in QUOTAS
    assert CAPS["计算机图形学与游戏"] == 1


def test_every_topic_gets_its_quota_when_supply_is_enough():
    papers = []
    for topic, quota in QUOTAS.items():
        papers += [paper(f"{topic}-{i}", topic, relevance=1) for i in range(6)]

    selected = select_papers(papers, max_papers=6)

    counts = {}
    for p in selected:
        counts[p["topic"]] = counts.get(p["topic"], 0) + 1
    assert counts == QUOTAS


def test_web_keeps_one_slot_even_if_other_topics_score_higher():
    papers = [paper(f"ai{i}", "AI 编码 / 编程代理", relevance=10) for i in range(10)]
    papers += [paper(f"llm{i}", "LLM 应用工程", relevance=10) for i in range(10)]
    papers += [paper("web0", "Web 全栈 / 前端工程", relevance=1)]
    papers += [paper("dev0", "开发者工具 / 测试 / 工程效率", relevance=1)]

    selected = select_papers(papers, max_papers=6)

    assert sum(p["topic"] == "Web 全栈 / 前端工程" for p in selected) == 1


def test_graphics_only_enters_by_beating_a_weak_pick():
    papers = [paper("ai1", "AI 编码 / 编程代理", relevance=10),
              paper("ai2", "AI 编码 / 编程代理", relevance=10),
              paper("llm1", "LLM 应用工程", relevance=10),
              paper("llm2", "LLM 应用工程", relevance=10),
              paper("web1", "Web 全栈 / 前端工程", relevance=10),
              paper("dev1", "开发者工具 / 测试 / 工程效率", relevance=10),
              # 图形学这篇分数很高，应该顶掉一个"有 2 篇"的方向里最弱的那篇
              paper("gr1", "计算机图形学与游戏", relevance=10, citations=40)]

    selected = select_papers(papers, max_papers=6)

    assert len(selected) == 6
    assert sum(p["topic"] == "计算机图形学与游戏" for p in selected) == 1
    # Web 只有 1 篇，不能被顶掉
    assert sum(p["topic"] == "Web 全栈 / 前端工程" for p in selected) == 1


def test_graphics_does_not_enter_when_all_topics_have_one_paper():
    papers = [paper("ai1", "AI 编码 / 编程代理", relevance=1),
              paper("llm1", "LLM 应用工程", relevance=1),
              paper("web1", "Web 全栈 / 前端工程", relevance=1),
              paper("dev1", "开发者工具 / 测试 / 工程效率", relevance=1),
              paper("gr1", "计算机图形学与游戏", relevance=10, citations=40)]

    selected = select_papers(papers, max_papers=4)

    assert sum(p["topic"] == "计算机图形学与游戏" for p in selected) == 0


def test_seen_papers_are_excluded():
    papers = [paper("a", "Web 全栈 / 前端工程", relevance=3),
              paper("b", "Web 全栈 / 前端工程", relevance=2)]
    selected = select_papers(papers, max_papers=1, seen_ids={"a"})
    assert [p["id"] for p in selected] == ["b"]


def test_missing_topic_supply_is_filled_by_best_remaining():
    papers = [paper("web0", "Web 全栈 / 前端工程", relevance=1)]
    papers += [paper(f"ai{i}", "AI 编码 / 编程代理", relevance=10 - i) for i in range(5)]

    selected = select_papers(papers, max_papers=4)

    assert len(selected) == 4
    assert sum(p["topic"] == "Web 全栈 / 前端工程" for p in selected) == 1


def test_within_topic_higher_score_first():
    papers = [
        paper("low", "计算机图形学与游戏", relevance=1),
        paper("high", "计算机图形学与游戏", relevance=9),
    ]
    selected = select_papers(papers, quotas={"计算机图形学与游戏": 2}, caps={}, max_papers=2)
    assert [p["id"] for p in selected] == ["high", "low"]


def test_llm_scores_drive_ranking():
    papers = [
        paper("generic", "AI 编码 / 编程代理", relevance=10, llm_relevance=20, llm_quality=20),
        paper("sharp", "AI 编码 / 编程代理", relevance=1, llm_relevance=95, llm_quality=90),
    ]
    selected = select_papers(papers, quotas={"AI 编码 / 编程代理": 2}, caps={}, max_papers=2)
    assert selected[0]["id"] == "sharp"
