"""质量与时效：启发式信号 + LLM 相关性/扎实度打分。

只用关键词命中挑论文，会把"标题里恰好有 web"的水论文也选进来。这里加三层：
1. 启发式：arXiv comment 里的录用信息、代码链接、引用速度、新鲜度
2. 预筛：每个话题先按关键词+引用取前 N 篇，控制 LLM 成本
3. LLM 打分：按读者画像评"相关性"和"扎实度"，低质量/纯增量工作会被压下去
"""
from __future__ import annotations

import json
import re
from datetime import date
from typing import Dict, Iterable, List, Optional

from config import now

# 读者画像：想调整口味改这里就行，不用动查询式
INTEREST_PROFILE = (
    "读者是一名全栈 / 独立开发者。日常做 AI 编程工具与 agent、Web 应用"
    "（Next.js / Fastify / 小程序）、开发者效率工具，也会做 Godot 游戏原型。"
    "他关心能落地的工程方法、可复现的结果、新的开发范式；"
    "不关心纯理论、纯图形学算法，也不关心医疗、生物、材料等垂直领域应用。"
)

QUALITY_RUBRIC = (
    "质量分看论文本身是否扎实：是否有真实新意、技术贡献是否明确、实验是否充分、"
    "是否可复现（有代码/数据/公开基准）。换数据集、换模型、微小增量、纯综述类工作打低分。"
)

BATCH_SIZE = 12
MAX_TOKENS_HINT = 1500  # 摘要太长时截断，控制成本

_ACCEPTED = re.compile(
    r"(accepted|to appear|to be published|camera[- ]ready|\boral\b|\bspotlight\b|best paper)",
    re.IGNORECASE,
)
_CODE_LINK = re.compile(r"(github\.com|gitlab\.com|huggingface\.co|code is available|code:)",
                        re.IGNORECASE)


def days_old(published: str, today: Optional[date] = None) -> int:
    try:
        pub = date.fromisoformat(published)
    except (TypeError, ValueError):
        return 21
    return max(((today or now().date()) - pub).days, 0)


def _recency_bonus(days: int) -> float:
    if days <= 7:
        return 3.0
    if days <= 14:
        return 2.0
    if days <= 21:
        return 1.0
    return 0.0


def annotate(papers: Iterable[Dict], today: Optional[date] = None) -> List[Dict]:
    """给每篇论文补上启发式信号（原地更新并返回）。"""
    today = today or now().date()
    for paper in papers:
        days = days_old(paper.get("published", ""), today)
        paper["days_old"] = days
        comment = (paper.get("comment") or "") + " " + (paper.get("journal_ref") or "")
        paper["accepted_bonus"] = 8.0 if _ACCEPTED.search(comment) else 0.0
        text = (paper.get("title", "") + " " + paper.get("abstract", "")).lower()
        paper["code_bonus"] = 2.0 if _CODE_LINK.search(text) else 0.0
        # 引用速度：按月归一化，最多加 5 分
        citations = paper.get("citations", 0) or 0
        months = max(days / 30.0, 0.5)
        paper["citation_rate_bonus"] = min(citations / months * 0.25, 5.0)
        paper["recency_bonus"] = _recency_bonus(days)
    return list(papers)


def _rank_key(paper: Dict):
    return (paper.get("relevance", 0), paper.get("citations", 0), paper.get("published", ""))


def preselect(papers: List[Dict], per_topic: int = 15) -> List[Dict]:
    """每个话题先取关键词相关度最高的若干篇，只把这一批送去 LLM 打分。"""
    buckets: Dict[str, List[Dict]] = {}
    for paper in papers:
        buckets.setdefault(paper["topic"], []).append(paper)

    picked: List[Dict] = []
    for bucket in buckets.values():
        bucket.sort(key=_rank_key, reverse=True)
        picked.extend(bucket[:per_topic])
    return picked


def get_client(api_key: Optional[str] = None):
    from openai import OpenAI

    from config import DEEPSEEK_BASE_URL

    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def _score_batch(client, papers: List[Dict], model: str) -> Dict[str, Dict]:
    payload = json.dumps(
        [
            {
                "id": p["id"],
                "title": p["title"],
                "abstract": p["abstract"][:MAX_TOKENS_HINT],
                "comment": p.get("comment", ""),
                "citations": p.get("citations", 0),
            }
            for p in papers
        ],
        ensure_ascii=False,
    )
    prompt = (
        "你是论文筛选助手，为下面这位读者挑选每周必读的论文。\n"
        f"读者画像：{INTEREST_PROFILE}\n\n"
        "对每篇论文打两个 0-100 的分：\n"
        "1) relevance：与读者画像的相关程度（能落地、和他在做的事有关才算高）\n"
        f"2) quality：{QUALITY_RUBRIC}\n\n"
        "同时给一句 30 字以内的中文理由（reason）。\n"
        '返回 JSON：{"scores":[{"id":"...","relevance":0,"quality":0,"reason":"..."}]}\n\n'
        f"论文列表：\n{payload}"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2,
        timeout=180,
    )
    result = json.loads(response.choices[0].message.content)
    scores = result.get("scores") if isinstance(result, dict) else result
    if not isinstance(scores, list):
        return {}

    out: Dict[str, Dict] = {}
    for item in scores:
        if not isinstance(item, dict) or "id" not in item:
            continue
        out[str(item["id"])] = {
            "llm_relevance": float(item.get("relevance") or 0),
            "llm_quality": float(item.get("quality") or 0),
            "llm_reason": str(item.get("reason") or "").strip(),
        }
    return out


def llm_scoring(papers: List[Dict], client=None) -> Dict[str, Dict]:
    """批量打分；没有 key 或失败时返回空 dict，流程继续用启发式排序。"""
    if not papers or client is None:
        return {}

    from config import DEEPSEEK_MODEL

    scores: Dict[str, Dict] = {}
    for i in range(0, len(papers), BATCH_SIZE):
        batch = papers[i : i + BATCH_SIZE]
        try:
            scores.update(_score_batch(client, batch, DEEPSEEK_MODEL))
        except Exception as exc:  # 打分失败不是致命错误
            print(f"  [quality] 批次 {i // BATCH_SIZE + 1} 打分失败：{exc}")
    print(f"[quality] LLM 打分完成 {len(scores)}/{len(papers)} 篇")
    return scores


def apply_scores(papers: List[Dict], scores: Dict[str, Dict]) -> List[Dict]:
    for paper in papers:
        paper.update(scores.get(paper["id"], {}))
    return papers


def score_paper(paper: Dict) -> float:
    """最终排序分：LLM 为主，启发式为辅。没有 LLM 分数时退化成关键词+引用。"""
    rel = paper.get("llm_relevance")
    quality = paper.get("llm_quality")
    if rel is not None and quality is not None:
        base = 0.45 * float(rel) + 0.40 * float(quality)
        base += 0.15 * min(paper.get("relevance", 0) * 4, 100)
    else:
        base = min(paper.get("relevance", 0) * 8, 70) + min(paper.get("citations", 0), 25)

    base += paper.get("accepted_bonus", 0)
    base += paper.get("code_bonus", 0)
    base += paper.get("citation_rate_bonus", 0)
    base += paper.get("recency_bonus", 0)
    return base
