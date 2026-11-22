"""论文筛选：按话题配额轮转，再用分数补满；cap 话题只做替补。

配额回答"每周每个方向至少几篇"，cap 回答"某个方向最多几篇、且只在分数够高时进来"。
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, Iterable, List, Optional

from arxiv_fetcher import TOPICS
from quality import score_paper

# 替补话题要比被替换的论文高这么多分，才值得挤掉它
REPLACE_MARGIN = 5.0


def default_quotas() -> Dict[str, int]:
    return {t["name"]: int(t.get("quota", 0)) for t in TOPICS if t.get("quota")}


def default_caps() -> Dict[str, int]:
    return {t["name"]: int(t["cap"]) for t in TOPICS if t.get("cap")}


def _sort_key(paper: Dict):
    return (score_paper(paper), paper.get("published", ""))


def _topic_order() -> Dict[str, int]:
    return {t["name"]: i for i, t in enumerate(TOPICS)}


def select_papers(
    papers: Iterable[Dict],
    quotas: Optional[Dict[str, int]] = None,
    caps: Optional[Dict[str, int]] = None,
    max_papers: int = 10,
    seen_ids: Iterable[str] = (),
) -> List[Dict]:
    quotas = default_quotas() if quotas is None else quotas
    caps = default_caps() if caps is None else caps

    seen = set(seen_ids)
    buckets: Dict[str, List[Dict]] = {}
    for paper in papers:
        if paper["id"] in seen:
            continue
        buckets.setdefault(paper["topic"], []).append(paper)
    for bucket in buckets.values():
        bucket.sort(key=_sort_key, reverse=True)

    order = list(quotas) + [t for t in caps if t not in quotas]
    selected: List[Dict] = []

    # 轮转：每个主方向各取一篇，直到配额用满或选满
    while len(selected) < max_papers:
        progressed = False
        for topic in quotas:
            if len(selected) >= max_papers:
                break
            taken = sum(1 for p in selected if p["topic"] == topic)
            bucket = buckets.get(topic) or []
            if taken >= quotas[topic] or not bucket:
                continue
            selected.append(bucket.pop(0))
            progressed = True
        if not progressed:
            break

    # 补满：跨话题按分数取，cap 话题受上限约束
    if len(selected) < max_papers:
        remaining = sorted(
            (p for bucket in buckets.values() for p in bucket),
            key=_sort_key,
            reverse=True,
        )
        counts = Counter(p["topic"] for p in selected)
        for paper in remaining:
            if len(selected) >= max_papers:
                break
            topic = paper["topic"]
            if topic in caps and counts[topic] >= caps[topic]:
                continue
            selected.append(paper)
            counts[topic] += 1

    # 替补：cap 话题里最强的一篇，若能明显赢过最弱的一篇就换进来
    counts = Counter(p["topic"] for p in selected)
    for topic, cap in caps.items():
        if cap <= 0 or counts.get(topic, 0) >= cap:
            continue
        bucket = buckets.get(topic) or []
        if not bucket:
            continue
        best = bucket[0]
        # 不顶掉某个方向唯一的一篇，避免把 Web 挤成 0
        replaceable = [p for p in selected if counts[p["topic"]] > 1]
        if not replaceable:
            continue
        weakest = min(replaceable, key=score_paper)
        if score_paper(best) > score_paper(weakest) + REPLACE_MARGIN:
            selected.remove(weakest)
            selected.append(best)
            counts[weakest["topic"]] -= 1
            counts[topic] += 1

    topic_rank = _topic_order()
    selected.sort(key=lambda p: (topic_rank.get(p["topic"], len(order)), -score_paper(p)))
    return selected[:max_papers]
