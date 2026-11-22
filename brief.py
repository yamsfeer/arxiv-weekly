"""把论文讲成人话：抓 PDF 全文 → 用 DeepSeek 生成固定字段的导读。

文风参考 wait-what 的思路：先说上下文，短句，一句一个意思，术语先解释再用。
任何一步失败都不影响推送，会退回到基于摘要的简版导读。
"""
from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

import requests

from config import DEEPSEEK_MODEL
from quality import INTEREST_PROFILE

PDF_URL = "https://arxiv.org/pdf/{}"
MAX_CHARS = 24000
TIMEOUT = 60

README_RULES = (
    "你在写「论文人话版」，帮一位开发者快速判断这篇论文值不值得读。\n"
    f"读者画像：{INTEREST_PROFILE}\n\n"
    "写法要求（简化技术英语风格）：\n"
    "1. 短句。一句只说一个意思。用主动语态。\n"
    "2. 先说上下文：这篇要解决什么问题，再说它怎么做。\n"
    "3. 术语第一次出现，用一句大白话解释。不要把术语堆在解释里。\n"
    "4. 不要用「赋能」「范式」「显著提升」「业界首创」这类空话。\n"
    "5. 只写论文里有的东西。数字必须来自原文。不确定就不写。\n"
    "6. 全部用中文。\n"
)

PROMPT_HEADER = (
    README_RULES
    + "\n返回 JSON，字段如下：\n"
    "{\n"
    '  "one_liner": "不超过 40 字，结论先行，说清这篇干了什么",\n'
    '  "background": "2 句，它要解决什么问题",\n'
    '  "why": "2 句，和读者正在做的事有什么关系",\n'
    '  "how": "3-5 句，讲清做法。必须有一句以「类比：」开头的生活化比喻",\n'
    '  "results": "1-2 句，带论文里的具体数字",\n'
    '  "terms": [{"term": "术语", "plain": "一句大白话"}],\n'
    '  "takeaway": "1 句，如果只记一件事",\n'
    '  "self_check": ["问题1", "问题2"],\n'
    '  "reading": "1 句，精读还是扫读，需要什么前置知识"\n'
    "}\n"
    "terms 固定 3 个。self_check 固定 2 个。\n\n"
)


def _build_prompt(paper: Dict, text: str) -> str:
    return (
        PROMPT_HEADER
        + f"论文标题：{paper['title']}\n"
        + f"arXiv 分类：{' / '.join(paper.get('categories') or [])}\n"
        + f"作者备注：{paper.get('comment') or '无'}\n"
        + f"英文摘要：{paper.get('abstract', '')}\n\n"
        + "论文正文（可能被截断）：\n"
        + (text or "（正文不可用，请只依据摘要）")
        + "\n"
    )


EMPTY_BRIEF_KEYS = ("one_liner", "background", "why", "how", "results", "takeaway", "reading")


def pdf_text(paper_id: str) -> str:
    """下载 PDF 并抽出正文；失败返回空串。"""
    try:
        import fitz  # pymupdf
    except ImportError:
        print("[brief] 没装 pymupdf，跳过 PDF 全文")
        return ""

    try:
        resp = requests.get(
            PDF_URL.format(paper_id),
            timeout=TIMEOUT,
            headers={"User-Agent": "arxiv-weekly/1.0 (+https://github.com/yamsfeer/arxiv-weekly)"},
        )
        resp.raise_for_status()
        doc = fitz.open(stream=resp.content, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
    except Exception as exc:
        print(f"[brief] 下载/解析 PDF 失败 {paper_id}：{exc}")
        return ""

    # 参考文献之后的内容对导读没用，直接砍掉
    cut = text.find("\nReferences")
    if cut > 2000:
        text = text[:cut]
    return text[:MAX_CHARS]


def _normalize(raw: Dict, paper: Dict) -> Dict:
    """校验 LLM 输出，缺字段用摘要兜底。"""
    brief = {}
    for key in EMPTY_BRIEF_KEYS:
        value = raw.get(key)
        brief[key] = str(value).strip() if value else ""

    terms = raw.get("terms")
    if not isinstance(terms, list) or not terms:
        terms = []
    brief["terms"] = [
        {"term": str(t.get("term", "")).strip(), "plain": str(t.get("plain", "")).strip()}
        for t in terms
        if isinstance(t, dict) and t.get("term") and t.get("plain")
    ][:3]

    checks = raw.get("self_check")
    brief["self_check"] = [str(q).strip() for q in checks if str(q).strip()][:2] if isinstance(checks, list) else []

    # 关键字段缺失时用摘要兜底，保证页面一定能渲染
    fallback = paper.get("abstract_zh") or paper.get("abstract", "")
    if not brief["one_liner"]:
        brief["one_liner"] = fallback[:60]
    if not brief["background"]:
        brief["background"] = fallback
    if not brief["why"]:
        brief["why"] = "这篇和你的方向相关，值得快速扫一遍。"
    if not brief["how"]:
        brief["how"] = "（本篇的人话版生成不完整，请直接看摘要或原文。）"
    if not brief["results"]:
        brief["results"] = "（原文结果见摘要。）"
    if not brief["takeaway"]:
        brief["takeaway"] = brief["one_liner"]
    if not brief["reading"]:
        brief["reading"] = "建议扫读摘要，再决定是否精读。"
    return brief


def fallback_brief(paper: Dict) -> Dict:
    """完全不调用模型时的兜底导读。"""
    return _normalize({}, paper)


def _generate_one(client, paper: Dict, text: str) -> Dict:
    prompt = _build_prompt(paper, text)
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3,
        timeout=240,
    )
    return json.loads(response.choices[0].message.content)


def generate_briefs(
    papers: List[Dict],
    client=None,
    use_pdf: bool = True,
    workers: int = 3,
) -> Dict[str, Dict]:
    """并发抓 PDF，串行调模型（避免一次打太多请求）。返回 id -> brief。"""
    texts: Dict[str, str] = {}
    if use_pdf and papers:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for paper, text in zip(papers, pool.map(lambda p: pdf_text(p["id"]), papers)):
                texts[paper["id"]] = text
        got = sum(1 for t in texts.values() if t)
        print(f"[brief] PDF 正文抓取 {got}/{len(papers)} 篇")

    briefs: Dict[str, Dict] = {}
    if client is None:
        for paper in papers:
            briefs[paper["id"]] = fallback_brief(paper)
        return briefs

    for i, paper in enumerate(papers, 1):
        try:
            raw = _generate_one(client, paper, texts.get(paper["id"], ""))
            briefs[paper["id"]] = _normalize(raw, paper)
            print(f"[brief] {i}/{len(papers)} 生成完成：{paper['id']}")
        except Exception as exc:
            print(f"[brief] {i}/{len(papers)} 失败，用摘要兜底：{exc}")
            briefs[paper["id"]] = fallback_brief(paper)
    return briefs
