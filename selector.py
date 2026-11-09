"""论文筛选：先去重，再按话题配额轮转挑选，最后用分数补满。

配额是为了解决 "计算机图形学每周占 7 篇、Web 只有 1 篇" 的问题（Issue #1）。
"""
from __future__ import annotations

from typing import Dict, Iterable, List

from arxiv_fetcher import TOPICS


def score_paper(paper: Dict) -> float:
    """相关度为主，引用为辅：新论文引用基本都是 0，只按引用排会退化成按时间排。"""
    return (
        paper.get("relevance", 0) * 10.0
        + paper.get("citations", 0) * 1.0
        + paper.get("influential_citations", 0) * 5.0
    )


def _sort_key(paper: Dict):
    return (score_paper(paper), paper.get("published", ""))


def select_papers(
    papers: Iterable[Dict],
    quotas: Dict[str, int] | None = None,
    max_papers: int = 10,
    seen_ids: Iterable[str] = (),
) -> List[Dict]:
    """按话题配额挑选，返回展示顺序的论文列表。

    - 每个话题至少 quota 篇（候选不够时就用完为止）
    - 轮转分配，保证话题之间不会互相饿死
    - 还有空位就按分数补满
    """
    if quotas is None:
        quotas = {t["name"]: t["quota"] for t in TOPICS}

    seen = set(seen_ids)
    buckets: Dict[str, List[Dict]] = {name: [] for name in quotas}
    for paper in papers:
        if paper["id"] in seen:
            continue
        buckets.setdefault(paper["topic"], []).append(paper)

    for bucket in buckets.values():
        bucket.sort(key=_sort_key, reverse=True)

    order = list(quotas)
    selected: List[Dict] = []

    # 轮转：每一轮每个话题各取一篇，直到配额用满或选满 max_papers
    while len(selected) < max_papers:
        progressed = False
        for topic in order:
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

    # 补满剩余名额（跨话题按分数）
    if len(selected) < max_papers:
        remaining = sorted(
            (p for bucket in buckets.values() for p in bucket),
            key=_sort_key,
            reverse=True,
        )
        selected.extend(remaining[: max_papers - len(selected)])

    # 展示按话题分组，组内按分数从高到低
    topic_rank = {name: i for i, name in enumerate(order)}
    selected.sort(key=lambda p: (topic_rank.get(p["topic"], len(order)), -score_paper(p)))
    return selected
