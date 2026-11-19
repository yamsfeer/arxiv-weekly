"""从 arXiv API 按话题抓取论文，并打上话题相关度。

话题定义（查询式 + 关键词 + 配额）都在这里，是"关注什么"的唯一事实来源。
quota 表示"至少几篇"，cap 表示"最多几篇"（cap 话题只在分数足够高时替补进来）。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List

import arxiv

from config import DAYS_BACK, MAX_PER_TOPIC
from ids import normalize_id, title_key

# 顺序即展示顺序。前四个是主方向，图形学只做替补（最多 1 篇）。
TOPICS: List[Dict] = [
    {
        "name": "AI 编码 / 编程代理",
        "quota": 2,
        "query": (
            '(ti:"coding agent" OR ti:"code agent" OR ti:"software agent" '
            'OR ti:"coding assistant" OR ti:"code generation" OR ti:"program synthesis" '
            'OR ti:"code completion" OR ti:"automated program repair" OR ti:"SWE-bench" '
            'OR ti:"agentic coding" OR abs:"coding agent" OR abs:"code agent" '
            'OR abs:"SWE-bench" OR abs:"agentic coding" OR abs:"repository-level code") '
            "AND (cat:cs.SE OR cat:cs.PL OR cat:cs.AI OR cat:cs.CL)"
        ),
        "title_keywords": [
            "coding agent", "code agent", "agentic coding", "code generation",
            "program synthesis", "code completion", "program repair", "swe-bench",
            "coding assistant", "software agent", "repo",
        ],
        "abstract_keywords": [
            "coding agent", "code agent", "repository-level", "code generation",
            "program synthesis", "swe-bench", "pull request", "unit test",
        ],
    },
    {
        "name": "LLM 应用工程",
        "quota": 2,
        "query": (
            '(ti:"retrieval augmented" OR ti:"retrieval-augmented" OR ti:RAG '
            'OR ti:"tool use" OR ti:"tool calling" OR ti:"function calling" '
            'OR ti:"context engineering" OR ti:"LLM agent" OR ti:"agentic" '
            'OR ti:"LLM application" OR ti:"agent memory" OR ti:"agentic workflow" '
            'OR abs:"retrieval-augmented generation" OR abs:"context engineering" '
            'OR abs:"model context protocol" OR abs:"agentic workflow" '
            'OR abs:"tool calling") '
            "AND (cat:cs.AI OR cat:cs.IR OR cat:cs.CL OR cat:cs.SE)"
        ),
        "title_keywords": [
            "retrieval", "rag", "tool use", "tool calling", "function calling",
            "context engineering", "agent", "agentic", "memory", "workflow",
            "evaluation", "benchmark",
        ],
        "abstract_keywords": [
            "retrieval-augmented", "rag", "tool use", "function calling",
            "context engineering", "agentic", "pipeline", "evaluation",
        ],
    },
    {
        "name": "Web 全栈 / 前端工程",
        "quota": 1,
        "query": (
            '(ti:web OR ti:frontend OR ti:backend OR ti:browser OR ti:WebAssembly '
            'OR ti:WebGPU OR ti:microservice OR ti:"web application" OR ti:"REST API" '
            'OR ti:JavaScript OR ti:TypeScript OR abs:"web framework" '
            'OR abs:"web performance" OR abs:"web application" OR abs:frontend '
            'OR abs:backend OR abs:WebAssembly) '
            "AND (cat:cs.SE OR cat:cs.PL OR cat:cs.NI OR cat:cs.DC)"
        ),
        "title_keywords": [
            "web", "frontend", "front-end", "backend", "back-end", "browser",
            "webassembly", "wasm", "webgpu", "javascript", "typescript",
            "rest api", "microservice", "css", "html", "web app",
        ],
        "abstract_keywords": [
            "web application", "web framework", "frontend", "backend",
            "browser", "webassembly", "webgpu", "microservice", "rest api",
            "javascript", "typescript",
        ],
    },
    {
        "name": "开发者工具 / 测试 / 工程效率",
        "quota": 1,
        "query": (
            '(ti:"developer tool" OR ti:"IDE" OR ti:"code review" OR ti:"unit test" '
            'OR ti:"test generation" OR ti:fuzzing OR ti:debugging OR ti:observability '
            'OR ti:"build system" OR ti:"program analysis" OR ti:"static analysis" '
            'OR ti:"developer productivity" OR ti:"CI/CD" '
            'OR abs:"developer productivity" OR abs:"software testing" '
            'OR abs:"continuous integration" OR abs:"static analysis") '
            "AND (cat:cs.SE OR cat:cs.PL)"
        ),
        "title_keywords": [
            "developer tool", "ide", "code review", "unit test", "test generation",
            "fuzzing", "debugging", "observability", "build system",
            "program analysis", "static analysis", "developer productivity",
            "ci/cd", "compiler",
        ],
        "abstract_keywords": [
            "developer productivity", "software testing", "continuous integration",
            "static analysis", "code review", "debugging",
        ],
    },
    {
        # 可选话题：只有分数明显高于被选中的论文时才替补进来，且最多 1 篇
        "name": "计算机图形学与游戏",
        "quota": 0,
        "cap": 1,
        "query": "cat:cs.GR",
        "title_keywords": [
            "rendering", "render", "animation", "character", "mesh", "3d", "game",
            "games", "gaussian splatting", "texture", "geometry", "ray tracing",
            "reconstruction", "avatar", "motion",
        ],
        "abstract_keywords": [
            "rendering", "real-time", "game", "mesh", "animation", "gaussian",
            "nerf", "geometry", "texture",
        ],
    },
]


def relevance(paper: Dict, topic: Dict) -> int:
    """标题命中权重 3，摘要命中权重 1。用于粗筛，不直接决定最终排序。"""
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
                "primary_category": result.primary_category,
                # 录用信息是"不是水论文"最便宜也最可靠的信号
                "comment": (result.comment or "").strip(),
                "journal_ref": (result.journal_ref or "").strip(),
                "citations": 0,
                "influential_citations": 0,
            }
            paper["relevance"] = relevance(paper, topic)
            all_papers.append(paper)
            count += 1

        print(f"  获取到 {count} 篇（{DAYS_BACK} 天内）")

    print(f"[arxiv] 合计 {len(all_papers)} 篇去重后的论文")
    return all_papers
