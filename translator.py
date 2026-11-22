"""使用 DeepSeek API 把论文标题和摘要翻译成中文。"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from openai import OpenAI

from ids import normalize_id
from config import DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

BATCH_SIZE = 5  # 每批翻译的论文数
RETRIES = 2

PROMPT_TEMPLATE = (
    "请将以下学术论文的标题（title）和摘要（abstract）翻译成中文，"
    "保持学术准确性，中文摘要控制在 150 字以内，简洁清晰。\n\n"
    "返回 JSON 格式，结构为：\n"
    '{{"papers": [{{"id": "...", "title_zh": "...", "abstract_zh": "..."}}]}}\n\n'
    "论文列表：\n{payload}"
)


def get_client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("环境变量 DEEPSEEK_API_KEY 未设置")
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def translate_batch(client: OpenAI, papers: List[Dict]) -> List[Dict]:
    """翻译一批论文，返回带 id/title_zh/abstract_zh 的列表。"""
    payload = json.dumps(
        [{"id": p["id"], "title": p["title"], "abstract": p["abstract"]} for p in papers],
        ensure_ascii=False,
    )
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(payload=payload)}],
        response_format={"type": "json_object"},
        temperature=0.3,
        timeout=120,
    )

    result = json.loads(response.choices[0].message.content)

    # 兼容不同的返回结构
    if isinstance(result, list):
        return result
    if "papers" in result:
        return result["papers"]
    for value in result.values():
        if isinstance(value, list):
            return value
    return []


def translate_papers(
    papers: List[Dict],
    client: Optional[OpenAI] = None,
    skip: bool = False,
) -> List[Dict]:
    """翻译所有论文，失败时保留英文原文。"""
    for paper in papers:
        paper["title_zh"] = paper["title"]
        paper["abstract_zh"] = paper["abstract"]
    if not papers or skip:
        return papers

    client = client or get_client()
    translated: Dict[str, Dict] = {}

    for i in range(0, len(papers), BATCH_SIZE):
        batch = papers[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(papers) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"[translate] 翻译批次 {batch_num}/{total_batches}...")

        for attempt in range(1, RETRIES + 1):
            try:
                for item in translate_batch(client, batch):
                    paper_id = normalize_id(str(item.get("id", "")))
                    if paper_id:
                        translated[paper_id] = item
                break
            except Exception as exc:  # 翻译失败不是致命问题，保留英文即可
                print(f"  批次 {batch_num} 第 {attempt} 次翻译失败：{exc}")

    for paper in papers:
        item = translated.get(paper["id"], {})
        paper["title_zh"] = (item.get("title_zh") or "").strip() or paper["title"]
        paper["abstract_zh"] = (item.get("abstract_zh") or "").strip() or paper["abstract"]

    print(f"[translate] 翻译完成，成功 {len(translated)}/{len(papers)} 篇")
    return papers
