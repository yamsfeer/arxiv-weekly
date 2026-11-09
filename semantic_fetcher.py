"""用 Semantic Scholar 批量补充引用数。

旧实现是每篇论文发一次 GET（100 篇 = 100 次请求 + 60 秒 sleep），很容易被 429 限流，
被限流后又静默退化成"0 引用"。现在改成官方 batch 接口，一次最多 500 篇。
"""
from __future__ import annotations

import os
import time
from typing import Dict, Iterable, List

import requests

from ids import normalize_id

BATCH_URL = "https://api.semanticscholar.org/graph/v1/paper/batch"
FIELDS = "citationCount,influentialCitationCount"
BATCH_SIZE = 200  # 官方上限 500，留点余量
RETRIES = 3


def _headers() -> Dict[str, str]:
    """配置了 SEMANTIC_SCHOLAR_API_KEY 就用它，免 key 的公共池经常 429。"""
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    return {"x-api-key": api_key} if api_key else {}


def _empty(paper_ids: Iterable[str]) -> Dict[str, Dict]:
    return {pid: {"citations": 0, "influential_citations": 0} for pid in paper_ids}


def fetch_citations(paper_ids: List[str]) -> Dict[str, Dict]:
    """一次拿一批论文的引用数；失败时返回全 0，不让整个流程失败。"""
    result = _empty(paper_ids)
    if not paper_ids:
        return result

    for start in range(0, len(paper_ids), BATCH_SIZE):
        chunk = paper_ids[start : start + BATCH_SIZE]
        payload = {"ids": [f"ARXIV:{normalize_id(pid)}" for pid in chunk]}

        for attempt in range(1, RETRIES + 1):
            try:
                resp = requests.post(
                    BATCH_URL,
                    params={"fields": FIELDS},
                    json=payload,
                    headers=_headers(),
                    timeout=30,
                )
            except requests.RequestException as exc:
                print(f"[semantic] 请求失败（第 {attempt} 次）：{exc}")
                resp = None

            if resp is not None and resp.status_code == 200:
                data = resp.json()
                # batch 接口按请求顺序返回，找不到的论文是 null
                for paper_id, item in zip(chunk, data):
                    if not item:
                        continue
                    result[paper_id] = {
                        "citations": item.get("citationCount") or 0,
                        "influential_citations": item.get("influentialCitationCount") or 0,
                    }
                break

            status = resp.status_code if resp is not None else "network"
            if attempt < RETRIES:
                # 429 时优先听服务端的 Retry-After
                retry_after = 0
                if resp is not None:
                    try:
                        retry_after = int(resp.headers.get("Retry-After", 0))
                    except (TypeError, ValueError):
                        retry_after = 0
                wait = retry_after or 5 * attempt
                print(f"[semantic] 返回 {status}，{wait}s 后重试")
                time.sleep(wait)
            else:
                print(f"[semantic] 这批 {len(chunk)} 篇查不到引用数，按 0 处理")

    return result


def enrich_citations(papers: List[Dict]) -> List[Dict]:
    """批量补充引用数据（原地更新并返回）。"""
    if not papers:
        return papers
    print(f"[semantic] 正在批量查询 {len(papers)} 篇论文的引用数...")
    citations = fetch_citations([p["id"] for p in papers])
    for paper in papers:
        paper.update(citations.get(paper["id"], {"citations": 0, "influential_citations": 0}))
    found = sum(1 for p in papers if p.get("citations"))
    print(f"[semantic] 完成，{found}/{len(papers)} 篇有引用数据")
    return papers
