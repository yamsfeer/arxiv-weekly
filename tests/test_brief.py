"""人话版：字段兜底与模型输出解析。"""
import json
from types import SimpleNamespace

import brief


def paper(pid="2611.00001"):
    return {
        "id": pid,
        "title": "A Test Paper",
        "abstract": "English abstract.",
        "abstract_zh": "这是中文摘要。它有两句话。",
        "categories": ["cs.SE"],
        "comment": "",
    }


class FakeClient:
    class chat:
        class completions:
            @staticmethod
            def create(**kwargs):
                content = json.dumps(
                    {
                        "one_liner": "一句话",
                        "background": "背景",
                        "why": "为什么",
                        "how": "做法。类比：像做菜。",
                        "results": "提升 10%",
                        "terms": [
                            {"term": "A", "plain": "a"},
                            {"term": "B", "plain": "b"},
                            {"term": "C", "plain": "c"},
                            {"term": "D", "plain": "d"},
                        ],
                        "takeaway": "记一件事",
                        "self_check": ["问一", "问二", "问三"],
                        "reading": "扫读",
                    }
                )
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def test_generate_briefs_parses_and_trims():
    briefs = brief.generate_briefs([paper()], client=FakeClient(), use_pdf=False)
    item = briefs["2611.00001"]
    assert item["one_liner"] == "一句话"
    assert len(item["terms"]) == 3
    assert len(item["self_check"]) == 2


def test_fallback_uses_abstract():
    item = brief.fallback_brief(paper())
    assert "中文摘要" in item["background"]
    assert item["one_liner"]
    assert item["how"]


def test_generate_briefs_without_client_returns_fallback():
    briefs = brief.generate_briefs([paper()], client=None, use_pdf=False)
    assert "中文摘要" in briefs["2611.00001"]["background"]


def test_normalize_drops_bad_terms():
    item = brief._normalize({"terms": [{"term": "", "plain": "x"}, {"term": "ok", "plain": "好"}]}, paper())
    assert item["terms"] == [{"term": "ok", "plain": "好"}]
