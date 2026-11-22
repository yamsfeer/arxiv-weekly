"""飞书卡片构建与通道选择。"""
import json

import feishu


def sample(pid="2611.00001", topic="Web 前后端开发", abstract="摘要内容"):
    return {
        "id": pid,
        "title": "A Test Paper About Browsers",
        "title_zh": "一篇关于浏览器的测试论文",
        "abstract_zh": abstract,
        "url": f"https://arxiv.org/abs/{pid}",
        "pdf": f"https://arxiv.org/pdf/{pid}",
        "published": "2026-11-06",
        "topic": topic,
        "categories": ["cs.SE"],
        "authors": ["Alice", "Bob"],
        "citations": 0,
        "influential_citations": 0,
    }


def test_cards_are_single_when_short():
    cards = feishu.build_cards([sample(), sample("2611.00002")], "2026-11-09")
    assert len(cards) == 1
    assert "2 篇" in cards[0]["header"]["title"]["content"]


def test_card_contains_chinese_title_link_and_abstract():
    card = feishu.build_cards([sample()], "2026-11-09")[0]
    body = json.dumps(card, ensure_ascii=False)
    assert "一篇关于浏览器的测试论文" in body
    assert "https://arxiv.org/abs/2611.00001" in body
    assert "摘要内容" in body


def test_archive_button_only_on_last_card():
    papers = [sample(f"2611.{i:05d}", abstract="很长的摘要" * 60) for i in range(30)]
    cards = feishu.build_cards(papers, "2026-11-09", archive_url="https://example.com/a.md")

    assert len(cards) > 1
    for card in cards:
        # 飞书单条消息上限 30KB，留足余量
        assert len(json.dumps(card, ensure_ascii=False).encode("utf-8")) < 30_000

    def has_button(card):
        return any(el.get("tag") == "action" for el in card["elements"])

    assert not has_button(cards[0])
    assert has_button(cards[-1])


def test_sign_matches_reference_vector():
    # 参考值由 openssl 独立计算，用来锁住签名算法
    assert feishu._sign("mysecret", "1700000000") == "Jp33/xXhCipDEpjyHvEyc7mRSyXWHbNz6J8+C3qQKNo="


def test_empty_card_is_grey_and_mentions_no_papers():
    card = feishu.build_empty_card("2026-11-09")
    assert card["header"]["template"] == "grey"
    assert "没有抓到新的论文" in json.dumps(card, ensure_ascii=False)


def test_test_card_is_marked_as_test():
    card = feishu.build_test_card()
    assert "测试" in card["header"]["title"]["content"]


def test_channel_prefers_app_when_fully_configured(monkeypatch):
    for key in ("FEISHU_WEBHOOK", "FEISHU_WEBHOOK_SECRET", "FEISHU_CHANNEL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("FEISHU_APP_ID", "cli_x")
    monkeypatch.setenv("FEISHU_APP_SECRET", "secret")
    monkeypatch.setenv("FEISHU_RECEIVE_ID", "me@example.com")

    channel = feishu.channel_config()
    assert channel["type"] == "app"
    assert channel["receive_id_type"] == "email"


def test_channel_uses_webhook_when_only_webhook_configured(monkeypatch):
    for key in ("FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_RECEIVE_ID", "FEISHU_CHANNEL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("FEISHU_WEBHOOK", "https://open.feishu.cn/open-apis/bot/v2/hook/xxx")

    channel = feishu.channel_config()
    assert channel == {
        "type": "webhook",
        "webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
        "secret": None,
    }


def test_channel_none_without_config(monkeypatch):
    for key in (
        "FEISHU_APP_ID",
        "FEISHU_APP_SECRET",
        "FEISHU_RECEIVE_ID",
        "FEISHU_WEBHOOK",
        "FEISHU_CHANNEL",
    ):
        monkeypatch.delenv(key, raising=False)
    assert feishu.channel_config() is None


def test_github_archive_url_uses_actions_env(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "yamsfeer/arxiv-weekly")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    assert (
        feishu.github_archive_url("2026-11-09")
        == "https://github.com/yamsfeer/arxiv-weekly/blob/main/papers/2026-11-09.md"
    )


def test_github_archive_url_absent_outside_actions(monkeypatch):
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    assert feishu.github_archive_url("2026-11-09") is None


def test_send_card_via_app_gets_token_then_posts_message(monkeypatch):
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        if "tenant_access_token" in url:
            return {"tenant_access_token": "t-123"}
        return {"code": 0}

    monkeypatch.setattr(feishu, "_request", fake_request)
    channel = {
        "type": "app",
        "app_id": "cli_x",
        "app_secret": "sec",
        "receive_id": "me@example.com",
        "receive_id_type": "email",
    }

    feishu.send_card(feishu.build_test_card(), channel)

    assert len(calls) == 2
    method, url, kwargs = calls[1]
    assert method == "POST"
    assert url.endswith("/im/v1/messages")
    assert kwargs["params"] == {"receive_id_type": "email"}
    assert kwargs["headers"]["Authorization"] == "Bearer t-123"
    assert kwargs["json"]["receive_id"] == "me@example.com"
    assert kwargs["json"]["msg_type"] == "interactive"
    # content 必须是卡片 JSON 的字符串形式（飞书要求）
    sent_card = json.loads(kwargs["json"]["content"])
    assert sent_card["header"]["title"]["content"]


def test_feishu_error_includes_hint(monkeypatch):
    class FakeResp:
        status_code = 200
        text = ""

        def json(self):
            return {"code": 19021, "msg": "sign match fail"}

    monkeypatch.setattr(feishu.requests, "request", lambda *a, **k: FakeResp())

    import pytest

    with pytest.raises(feishu.FeishuError) as excinfo:
        feishu._request("POST", "https://example.com/hook")
    assert "19021" in str(excinfo.value)
    assert "签名" in str(excinfo.value)
