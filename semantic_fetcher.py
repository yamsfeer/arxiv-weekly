"""
通过 Semantic Scholar API 补充引用数量（免费，无需 Key）
新论文引用数可能为 0，属正常情况
"""
import time
import requests
from typing import List, Dict

SEMANTIC_API = "https://api.semanticscholar.org/graph/v1/paper/arXiv:{}"
FIELDS = "citationCount,influentialCitationCount"
REQUEST_DELAY = 0.6  # Semantic Scholar 限速约 100 req/s，保守一点


def get_citation_count(arxiv_id: str) -> Dict:
    """查询单篇论文的引用数"""
    # 去掉版本号：2506.13832v1 -> 2506.13832
    clean_id = arxiv_id.split("v")[0]
    url = SEMANTIC_API.format(clean_id)
    try:
        resp = requests.get(url, params={"fields": FIELDS}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "citations": data.get("citationCount") or 0,
                "influential_citations": data.get("influentialCitationCount") or 0,
            }
        elif resp.status_code == 404:
            return {"citations": 0, "influential_citations": 0}
        else:
            print(f"  Semantic Scholar 返回 {resp.status_code}，跳过 {clean_id}")
    except Exception as e:
        print(f"  Semantic Scholar 请求失败 {clean_id}：{e}")

    return {"citations": 0, "influential_citations": 0}


def enrich_citations(papers: List[Dict]) -> List[Dict]:
    """批量补充引用数据"""
    print(f"[semantic] 正在查询 {len(papers)} 篇论文的引用数...")
    for paper in papers:
        citation_data = get_citation_count(paper["id"])
        paper.update(citation_data)
        time.sleep(REQUEST_DELAY)
    print("[semantic] 引用数查询完成")
    return papers
