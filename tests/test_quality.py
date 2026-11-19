"""质量信号：录用/代码/引用速度/新鲜度，以及预筛和打分。"""
from datetime import date

from quality import annotate, apply_scores, days_old, preselect, score_paper

TODAY = date(2026, 11, 19)


def paper(pid="2611.00001", topic="AI 编码 / 编程代理", published="2026-11-18", **extra):
    data = {
        "id": pid,
        "topic": topic,
        "title": "A Paper",
        "abstract": "An abstract.",
        "published": published,
        "relevance": 0,
        "citations": 0,
    }
    data.update(extra)
    return data


def test_days_old():
    assert days_old("2026-11-18", TODAY) == 1
    assert days_old("2026-10-01", TODAY) == 49
    assert days_old("bad-date", TODAY) == 21


def test_accepted_comment_gets_bonus():
    papers = annotate([paper(comment="Accepted at NeurIPS 2026")], TODAY)
    assert papers[0]["accepted_bonus"] == 8.0

    plain = annotate([paper(comment="12 pages")], TODAY)
    assert plain[0]["accepted_bonus"] == 0.0


def test_code_link_gets_bonus():
    papers = annotate([paper(abstract="Code: https://github.com/foo/bar")], TODAY)
    assert papers[0]["code_bonus"] == 2.0


def test_recency_buckets():
    papers = annotate(
        [
            paper("a", published="2026-11-18"),
            paper("b", published="2026-11-10"),
            paper("c", published="2026-11-01"),
            paper("d", published="2026-10-20"),
        ],
        TODAY,
    )
    assert [p["recency_bonus"] for p in papers] == [3.0, 2.0, 1.0, 0.0]


def test_citation_rate_is_capped():
    papers = annotate([paper(published="2026-11-18", citations=1000)], TODAY)
    assert papers[0]["citation_rate_bonus"] <= 5.0


def test_preselect_keeps_top_per_topic():
    papers = [paper(f"a{i}", relevance=i) for i in range(10)]
    papers += [paper(f"b{i}", topic="LLM 应用工程", relevance=i) for i in range(10)]

    picked = preselect(papers, per_topic=3)

    per_topic = {}
    for p in picked:
        per_topic[p["topic"]] = per_topic.get(p["topic"], 0) + 1
    assert per_topic == {"AI 编码 / 编程代理": 3, "LLM 应用工程": 3}
    assert min(p["relevance"] for p in picked) == 7


def test_score_prefers_llm_scores():
    generic = paper(relevance=10)
    sharp = paper(relevance=1, llm_relevance=95, llm_quality=90)
    assert score_paper(sharp) > score_paper(generic)


def test_score_falls_back_without_llm_scores():
    low = paper(relevance=1, citations=0)
    high = paper(relevance=5, citations=10)
    assert score_paper(high) > score_paper(low)


def test_apply_scores_attaches_and_ignores_missing():
    papers = [paper("a"), paper("b")]
    apply_scores(papers, {"a": {"llm_relevance": 80, "llm_quality": 70, "llm_reason": "x"}})
    assert papers[0]["llm_relevance"] == 80
    assert "llm_relevance" not in papers[1]


def test_llm_scoring_parses_response(monkeypatch):
    import json
    from types import SimpleNamespace

    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    content = json.dumps(
                        {"scores": [
                            {"id": "2611.00001", "relevance": 88, "quality": 77, "reason": "很相关"},
                            {"id": "2611.00002", "relevance": 10, "quality": 20, "reason": "水"},
                        ]}
                    )
                    return SimpleNamespace(
                        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
                    )

    from quality import llm_scoring

    scores = llm_scoring([paper("2611.00001"), paper("2611.00002")], FakeClient())

    assert scores["2611.00001"]["llm_relevance"] == 88
    assert scores["2611.00001"]["llm_quality"] == 77
    assert scores["2611.00002"]["llm_reason"] == "水"


def test_llm_scoring_without_client_returns_empty():
    from quality import llm_scoring

    assert llm_scoring([paper()], None) == {}
