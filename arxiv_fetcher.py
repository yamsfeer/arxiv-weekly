"""从 arXiv API 按话题抓取最近的论文，并打上话题相关度。

话题定义（查询式 + 关键词 + 配额）都在这里，是"关注什么"的唯一事实来源。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List

import arxiv

from config import DAYS_BACK, MAX_PER_TOPIC
from ids import normalize_id, title_key

# 每个话题的 quota 是"至少推几篇"，总和等于默认的 10 篇。
# 顺序即卡片与归档里的展示顺序；Web 放最前，让 web 论文优先归到这个话题。
TOPICS: List[Dict] = [
    {
        "name": "Web 前后端开发",
        "quota": 3,
        "query": (
            '(ti:web OR ti:frontend OR ti:backend OR ti:"REST API" '
            'OR ti:"web application" OR ti:microservice OR ti:"WebAssembly" '
            'OR ti:"WebGPU" OR ti:browser OR abs:"web application" '
            'OR abs:frontend OR abs:backend OR abs:microservice '
            'OR abs:WebAssembly OR abs:WebGPU OR abs:browser) '
            "AND (cat:cs.SE OR cat:cs.PL OR cat:cs.NI OR cat:cs.DC)"
        ),
        "title_keywords": [
            "web", "frontend", "front-end", "backend", "back-end", "browser",
            "webassembly", "wasm", "webgpu", "javascript", "typescript",
            "rest api", "microservice", "http", "css", "html", "web app",
        ],
        "abstract_keywords": [
            "web application", "web framework", "frontend", "backend",
            "browser", "webassembly", "webgpu", "microservice", "rest api",
            "javascript", "typescript",
        ],
    },
    {
        "name": "计算机图形学与游戏",
        "quota": 3,
        "query": "cat:cs.GR",
        "title_keywords": [
            "rendering", "render", "neural rendering", "animation", "character",
            "mesh", "3d", "game", "games", "gaussian splatting", "texture",
            "geometry", "ray tracing", "reconstruction", "avatar", "motion",
        ],
        "abstract_keywords": [
            "rendering", "real-time", "game", "mesh", "animation", "gaussian",
            "nerf", "geometry", "texture",
        ],
    },
    {
        "name": "AI 辅助软件开发",
        "quota": 2,
        "query": (
            '(ti:"code generation" OR ti:"code completion" '
            'OR ti:"coding assistant" OR ti:"program synthesis" '
            'OR ti:"automated debugging" OR ti:"software engineering" '
            'OR ti:"code agent" OR ti:"unit test generation") '
            "AND (cat:cs.SE OR cat:cs.PL OR cat:cs.AI)"
        ),
        "title_keywords": [
            "code generation", "code completion", "coding assistant",
            "program synthesis", "debugging", "software engineering",
            "code agent", "test generation", "pull request", "refactor",
        ],
        "abstract_keywords": [
            "code generation", "code completion", "coding", "debugging",
            "repository", "software engineering", "unit test",
        ],
    },
    {
        "name": "AI 应用开发",
        "quota": 2,
        "query": (
            '(ti:"AI agent" OR ti:"LLM agent" OR ti:"retrieval augmented" '
            'OR ti:RAG OR ti:"tool use" OR ti:"function calling" '
            'OR ti:"agentic" OR ti:"AI application" OR ti:"context engineering") '
            "AND (cat:cs.AI OR cat:cs.IR OR cat:cs.HC)"
        ),
        "title_keywords": [
            "agent", "agentic", "rag", "retrieval", "tool use", "tool calling",
            "function calling", "llm", "mcp", "context", "workflow",
        ],
        "abstract_keywords": [
            "agent", "retrieval augmented", "rag", "tool use", "function calling",
            "llm", "pipeline",
        ],
    },
]


def relevance(paper: Dict, topic: Dict) -> int:
    """标题命中权重 3，摘要命中权重 1。用于同话题内排序，避免只看引用数。"""
    title = paper["title"].lower()
    abstract = paper["abstract"].lower()
    score = sum(3 for kw in topic["title_keywords"] if kw in title)
    score += sum(1 for kw in topic["abstract_keywords"] if kw in abstract)
    return score


def fetch_papers() -> List[Dict]:
    """抓取所有话题的论文，按 id / 标题去重后返回。"""
    client = arxiv.Client(num_retries=3, delay_seconds=3)
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)
    seen_ids: set = set()
    seen_titles: set = set()
    all_papers: List[Dict] = []

    for topic in TOPICS:
        print(f"[arxiv] 正在抓取：{topic['name']}")
        search = arxiv.Search(
            query=topic["query"],
            max_results=MAX_PER_TOPIC,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        try:
            results = list(client.results(search))
        except Exception as exc:  # 单个话题失败不应该让整周推送挂掉
            print(f"  抓取失败：{exc}")
            continue

        count = 0
        for result in results:
            if result.published < cutoff:
                continue

            paper_id = normalize_id(result.get_short_id())
            title = result.title.strip()
            paper_title_key = title_key(title)
            if paper_id in seen_ids or paper_title_key in seen_titles:
                continue
            seen_ids.add(paper_id)
            seen_titles.add(paper_title_key)

            paper = {
                "id": paper_id,
                "title": title,
                "abstract": result.summary.replace("\n", " ").strip(),
                "published": result.published.astimezone(timezone.utc).strftime("%Y-%m-%d"),
                "authors": [a.name for a in result.authors[:3]],
                "url": f"https://arxiv.org/abs/{paper_id}",
                "pdf": f"https://arxiv.org/pdf/{paper_id}",
                "topic": topic["name"],
                "categories": list(result.categories[:3]),
                "citations": 0,
                "influential_citations": 0,
            }
            paper["relevance"] = relevance(paper, topic)
            all_papers.append(paper)
            count += 1

        print(f"  获取到 {count} 篇（{DAYS_BACK} 天内）")

    print(f"[arxiv] 合计 {len(all_papers)} 篇去重后的论文")
    return all_papers
