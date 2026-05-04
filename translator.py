"""
使用 DeepSeek API 将论文标题和摘要翻译成中文
"""
import os
import json
from typing import List, Dict
from openai import OpenAI

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-v4-flash"
BATCH_SIZE = 5  # 每批翻译的论文数


def get_client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("环境变量 DEEPSEEK_API_KEY 未设置")
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def translate_batch(client: OpenAI, papers: List[Dict]) -> List[Dict]:
    """翻译一批论文，返回带 id/title_zh/abstract_zh 的列表"""
    payload = json.dumps(
        [{"id": p["id"], "title": p["title"], "abstract": p["abstract"]} for p in papers],
        ensure_ascii=False,
    )
    prompt = (
        "请将以下学术论文的标题（title）和摘要（abstract）翻译成中文，"
        "保持学术准确性，中文摘要控制在 150 字以内，简洁清晰。\n\n"
        "返回 JSON 格式，结构为：\n"
        '{"papers": [{"id": "...", "title_zh": "...", "abstract_zh": "..."}]}\n\n'
        f"论文列表：\n{payload}"
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    content = response.choices[0].message.content
    result = json.loads(content)

    # 兼容不同的返回结构
    if isinstance(result, list):
        return result
    if "papers" in result:
        return result["papers"]
    # fallback：取第一个列表值
    for v in result.values():
        if isinstance(v, list):
            return v
    return []


def translate_papers(papers: List[Dict]) -> List[Dict]:
    """翻译所有论文，失败时保留英文原文"""
    client = get_client()
    translated: Dict[str, Dict] = {}

    for i in range(0, len(papers), BATCH_SIZE):
        batch = papers[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(papers) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"[translate] 翻译批次 {batch_num}/{total_batches}...")

        try:
            results = translate_batch(client, batch)
            for item in results:
                if "id" in item:
                    translated[item["id"]] = item
        except Exception as e:
            print(f"  批次 {batch_num} 翻译失败：{e}，保留英文原文")

    for paper in papers:
        t = translated.get(paper["id"], {})
        paper["title_zh"] = t.get("title_zh") or paper["title"]
        paper["abstract_zh"] = t.get("abstract_zh") or paper["abstract"]

    print(f"[translate] 翻译完成，成功 {len(translated)}/{len(papers)} 篇")
    return papers
