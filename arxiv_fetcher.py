"""
从 arxiv API 按话题抓取最近的论文
"""
import arxiv
from datetime import datetime, timedelta, timezone
from typing import List, Dict

# 向前回溯天数（适当宽松，避免漏掉周末提交的论文）
DAYS_BACK = 10
MAX_PER_TOPIC = 30

TOPIC_QUERIES = [
    {
        "name": "Web 前后端开发",
        "query": (
            '(ti:web OR ti:frontend OR ti:backend OR ti:"REST API" '
            'OR ti:"web application" OR ti:microservice OR ti:"WebAssembly" '
            'OR ti:"WebGPU") AND (cat:cs.SE OR cat:cs.NI OR cat:cs.PL)'
        ),
    },
    {
        "name": "计算机图形学与游戏",
        "query": "cat:cs.GR",
    },
    {
        "name": "AI 辅助软件开发",
        "query": (
            '(ti:"code generation" OR ti:"code completion" '
            'OR ti:"coding assistant" OR ti:"program synthesis" '
            'OR ti:"automated debugging" OR ti:"software engineering") '
            'AND (cat:cs.SE OR cat:cs.PL OR cat:cs.AI)'
        ),
    },
    {
        "name": "AI 应用开发",
        "query": (
            '(ti:"AI agent" OR ti:"LLM agent" OR ti:"retrieval augmented" '
            'OR ti:RAG OR ti:"tool use" OR ti:"function calling" '
            'OR ti:"agentic" OR ti:"AI application") '
            'AND (cat:cs.AI OR cat:cs.IR OR cat:cs.HC)'
        ),
    },
]


def fetch_papers() -> List[Dict]:
    """抓取所有话题的论文，合并去重后返回"""
    client = arxiv.Client(num_retries=3, delay_seconds=3)
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)
    seen_in_run: set = set()
    all_papers: List[Dict] = []

    for topic in TOPIC_QUERIES:
        print(f"[arxiv] 正在抓取：{topic['name']}")
        search = arxiv.Search(
            query=topic["query"],
            max_results=MAX_PER_TOPIC,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        try:
            results = list(client.results(search))
        except Exception as e:
            print(f"  抓取失败：{e}")
            continue

        count = 0
        for result in results:
            if result.published < cutoff:
                continue

            paper_id = result.get_short_id()
            if paper_id in seen_in_run:
                continue
            seen_in_run.add(paper_id)

            all_papers.append({
                "id": paper_id,
                "title": result.title.strip(),
                "abstract": result.summary.replace("\n", " ").strip(),
                "published": result.published.strftime("%Y-%m-%d"),
                "authors": [a.name for a in result.authors[:3]],
                "url": result.entry_id,
                "topic": topic["name"],
                "citations": 0,
                "influential_citations": 0,
            })
            count += 1

        print(f"  获取到 {count} 篇（{DAYS_BACK} 天内）")

    print(f"[arxiv] 合计 {len(all_papers)} 篇去重后的论文")
    return all_papers
