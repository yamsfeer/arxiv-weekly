"""飞书推送：交互式卡片 + 两种通道（群自定义机器人 webhook / 自建应用私聊）。

卡片在飞书里可以直接读中文标题、摘要和原文链接，聊天记录不会像微信第三方工具
那样过期清空；每张卡片底部还有指向仓库归档的按钮，作为长期存档。
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Dict, List, Optional

import requests

from digest import card_paper_markdown, format_date, topic_summary

API_BASE = "https://open.feishu.cn/open-apis"
MAX_CARD_BYTES = 18_000  # 飞书单条消息上限 30KB，留足余量
RETRIES = 3

# 常见错误码的中文提示，省得对着文档查
ERROR_HINTS = {
    19001: "卡片 JSON 结构不合法",
    19021: "webhook 签名校验失败，检查 FEISHU_WEBHOOK_SECRET",
    19024: "webhook 已失效或被删除",
    9499: "请求参数错误",
    10003: "app_id / app_secret 不正确",
    99991663: "tenant_access_token 无效或已过期",
    11232: "机器人不在目标群里，或没有发消息权限",
    230002: "机器人不在该会话中",
}


class FeishuError(RuntimeError):
    def __init__(self, code: int, message: str):
        hint = ERROR_HINTS.get(code, "")
        detail = f"（{hint}）" if hint else ""
        super().__init__(f"飞书接口返回 {code}：{message}{detail}")
        self.code = code


# --------------------------------------------------------------------------- 卡片


def _estimate_bytes(obj) -> int:
    return len(json.dumps(obj, ensure_ascii=False).encode("utf-8"))


def _split_blocks(blocks: List[str], max_bytes: int = MAX_CARD_BYTES) -> List[List[str]]:
    """按实际序列化大小把论文块分到多张卡片里，避免超长被飞书拒收。"""
    groups: List[List[str]] = []
    current: List[str] = []
    for block in blocks:
        trial = current + [block]
        if current and _estimate_bytes(trial) > max_bytes:
            groups.append(current)
            current = [block]
        else:
            current = trial
    if current or not groups:
        groups.append(current)
    return groups


def _card(title: str, blocks: List[str], part: int, total_parts: int,
          archive_url: Optional[str], summary: Optional[str], color: str) -> Dict:
    elements: List[Dict] = []
    if total_parts > 1:
        elements.append({"tag": "markdown", "content": f"**第 {part}/{total_parts} 部分**"})
    if part == 1 and summary:
        elements += [{"tag": "markdown", "content": summary}, {"tag": "hr"}]

    for block in blocks:
        elements.append({"tag": "markdown", "content": block})
        elements.append({"tag": "hr"})

    if archive_url:
        elements.append(
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "📖 查看完整归档"},
                        "type": "primary",
                        "url": archive_url,
                    }
                ],
            }
        )
    elements.append(
        {
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": "GitHub Actions · DeepSeek 自动生成 · 数据来源 arXiv / Semantic Scholar",
                }
            ],
        }
    )
    return {
        "config": {"wide_screen_mode": True, "enable_forward": True},
        "header": {"template": color, "title": {"tag": "plain_text", "content": title}},
        "elements": elements,
    }


def build_cards(papers: List[Dict], date_str: str, archive_url: Optional[str] = None) -> List[Dict]:
    """生成 1~N 张卡片；论文少的时候就是一张。"""
    title = f"📚 每周论文精选 · {format_date(date_str)} · {len(papers)} 篇"
    blocks = [card_paper_markdown(paper, i) for i, paper in enumerate(papers, 1)]
    groups = _split_blocks(blocks)
    summary = f"共 **{len(papers)}** 篇 · {topic_summary(papers)}"
    return [
        _card(title, group, part, len(groups), archive_url if part == len(groups) else None, summary, "blue")
        for part, group in enumerate(groups, 1)
    ]


def build_empty_card(date_str: str, archive_url: Optional[str] = None) -> Dict:
    return _card(
        f"📚 每周论文精选 · {format_date(date_str)}",
        [],
        1,
        1,
        archive_url,
        "本周没有抓到新的论文（可能正处于假期或 arXiv 未更新）。",
        "grey",
    )


def build_test_card() -> Dict:
    sample = {
        "id": "2611.00000",
        "title": "Feishu Delivery Test for arxiv-weekly",
        "title_zh": "arxiv-weekly 飞书推送测试",
        "abstract_zh": "如果你在飞书里看到这张卡片，说明 webhook（或自建应用）已经配置成功，"
        "每周一的论文精选会以同样的卡片形式送达，可以直接点标题读原文。",
        "url": "https://arxiv.org/abs/2611.00000",
        "published": "2026-11-09",
        "topic": "系统通知",
        "categories": [],
        "authors": ["arxiv-weekly"],
        "citations": 0,
        "influential_citations": 0,
    }
    return _card(
        "✅ 飞书推送测试",
        [card_paper_markdown(sample, 1)],
        1,
        1,
        None,
        "这条是手动触发的测试消息，收到即表示配置正确。",
        "turquoise",
    )


# --------------------------------------------------------------------------- 通道


def channel_config() -> Optional[Dict]:
    """按环境变量判断用哪个通道，返回 None 表示没配置。"""
    forced = os.environ.get("FEISHU_CHANNEL", "").strip().lower()
    app_id = os.environ.get("FEISHU_APP_ID", "").strip()
    app_secret = os.environ.get("FEISHU_APP_SECRET", "").strip()
    receive_id = os.environ.get("FEISHU_RECEIVE_ID", "").strip()
    webhook = os.environ.get("FEISHU_WEBHOOK", "").strip()
    webhook_secret = os.environ.get("FEISHU_WEBHOOK_SECRET", "").strip()

    app_ready = bool(app_id and app_secret and receive_id)
    if forced == "app" or (forced != "webhook" and app_ready):
        if not app_ready:
            return None
        return {
            "type": "app",
            "app_id": app_id,
            "app_secret": app_secret,
            "receive_id": receive_id,
            "receive_id_type": os.environ.get("FEISHU_RECEIVE_ID_TYPE", "email").strip() or "email",
        }
    if webhook:
        return {"type": "webhook", "webhook": webhook, "secret": webhook_secret or None}
    return None


def _sign(secret: str, timestamp: str) -> str:
    """飞书自定义机器人签名：以 "timestamp\\nsecret" 为密钥对空串做 HMAC-SHA256。"""
    key = f"{timestamp}\n{secret}".encode("utf-8")
    digest = hmac.new(key, b"", hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def _request(method: str, url: str, **kwargs) -> Dict:
    last_error = ""
    for attempt in range(1, RETRIES + 1):
        try:
            resp = requests.request(method, url, timeout=20, **kwargs)
        except requests.RequestException as exc:
            last_error = f"网络错误：{exc}"
        else:
            if resp.status_code in (429, 500, 502, 503, 504):
                last_error = f"HTTP {resp.status_code}"
            else:
                try:
                    data = resp.json()
                except ValueError:
                    raise RuntimeError(f"飞书返回了非 JSON 内容：{resp.status_code} {resp.text[:200]}")
                code = data.get("code", data.get("StatusCode", 0))
                if code not in (0, None):
                    raise FeishuError(int(code), str(data.get("msg") or data.get("StatusMessage") or ""))
                return data
        if attempt < RETRIES:
            time.sleep(2 * attempt)
    raise RuntimeError(f"调用飞书接口失败（已重试 {RETRIES} 次）：{last_error}")


def _send_webhook(card: Dict, webhook: str, secret: Optional[str] = None) -> None:
    payload: Dict = {"msg_type": "interactive", "card": card}
    if secret:
        timestamp = str(int(time.time()))
        payload["timestamp"] = timestamp
        payload["sign"] = _sign(secret, timestamp)
    _request("POST", webhook, json=payload)


def _tenant_token(app_id: str, app_secret: str) -> str:
    data = _request(
        "POST",
        f"{API_BASE}/auth/v3/tenant_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret},
    )
    token = data.get("tenant_access_token")
    if not token:
        raise RuntimeError(f"没能拿到 tenant_access_token：{data}")
    return token


def _send_app(card: Dict, channel: Dict) -> None:
    token = _tenant_token(channel["app_id"], channel["app_secret"])
    _request(
        "POST",
        f"{API_BASE}/im/v1/messages",
        params={"receive_id_type": channel["receive_id_type"]},
        headers={"Authorization": f"Bearer {token}"},
        json={
            "receive_id": channel["receive_id"],
            "msg_type": "interactive",
            "content": json.dumps(card, ensure_ascii=False),
        },
    )


def send_card(card: Dict, channel: Optional[Dict] = None) -> None:
    channel = channel or channel_config()
    if not channel:
        raise RuntimeError(
            "没有配置飞书推送：请设置 FEISHU_WEBHOOK，"
            "或 FEISHU_APP_ID + FEISHU_APP_SECRET + FEISHU_RECEIVE_ID"
        )
    if channel["type"] == "app":
        _send_app(card, channel)
    else:
        _send_webhook(card, channel["webhook"], channel.get("secret"))


def send_digest(
    papers: List[Dict],
    date_str: str,
    archive_url: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    cards = build_cards(papers, date_str, archive_url)
    if dry_run:
        print("[feishu] dry-run，卡片 JSON 如下（未发送）：")
        print(json.dumps(cards, ensure_ascii=False, indent=2))
        return
    channel = channel_config()
    if channel is None:
        raise RuntimeError(
            "没有配置飞书推送：请设置 FEISHU_WEBHOOK，"
            "或 FEISHU_APP_ID + FEISHU_APP_SECRET + FEISHU_RECEIVE_ID"
        )
    for i, card in enumerate(cards, 1):
        send_card(card, channel)
        print(f"[feishu] 已发送卡片 {i}/{len(cards)}（通道：{channel['type']}）")


def send_empty_notice(date_str: str, archive_url: Optional[str] = None, dry_run: bool = False) -> None:
    card = build_empty_card(date_str, archive_url)
    if dry_run:
        print(json.dumps(card, ensure_ascii=False, indent=2))
        return
    send_card(card)
    print("[feishu] 已发送「本周无新论文」通知")


def send_test(dry_run: bool = False) -> None:
    card = build_test_card()
    if dry_run:
        print(json.dumps(card, ensure_ascii=False, indent=2))
        return
    send_card(card)
    print("[feishu] 测试卡片已发送，去飞书看一眼")


def github_archive_url(date_str: str) -> Optional[str]:
    """仓库里这一期的归档链接，作为卡片底部的长期存档入口。"""
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not repo:
        return None
    branch = os.environ.get("GITHUB_REF_NAME", "").strip() or "main"
    return f"https://github.com/{repo}/blob/{branch}/papers/{date_str}.md"
