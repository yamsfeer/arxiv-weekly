"""
主入口：每周执行一次，抓取 → 去重 → 补充引用 → 翻译 → 发邮件 → 保存记录
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from arxiv_fetcher import fetch_papers
from semantic_fetcher import enrich_citations
from translator import translate_papers
from email_sender import send_email

SEEN_IDS_FILE = Path("data/seen_ids.json")
MAX_PAPERS = 10  # 每次最多推送篇数


def load_seen_ids() -> set:
    if SEEN_IDS_FILE.exists():
        return set(json.loads(SEEN_IDS_FILE.read_text(encoding="utf-8")))
    return set()


def save_seen_ids(seen_ids: set):
    SEEN_IDS_FILE.parent.mkdir(exist_ok=True)
    SEEN_IDS_FILE.write_text(
        json.dumps(sorted(seen_ids), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def score_paper(paper: Dict) -> float:
    """综合评分：引用数 + 高影响引用，用于排序"""
    return paper.get("citations", 0) * 1.0 + paper.get("influential_citations", 0) * 5.0


def select_new_papers(all_papers: List[Dict], seen_ids: set) -> List[Dict]:
    """过滤已见过的，按评分降序，取前 MAX_PAPERS 篇"""
    new_papers = [p for p in all_papers if p["id"] not in seen_ids]

    # 优先取有引用数据的，其次按提交时间倒序
    new_papers.sort(key=lambda p: (score_paper(p), p["published"]), reverse=True)

    # 尽量保证各话题都有覆盖（每个话题至少 1 篇）
    topic_buckets: Dict[str, List[Dict]] = {}
    for p in new_papers:
        topic_buckets.setdefault(p["topic"], []).append(p)

    selected: List[Dict] = []
    # 先每个话题取 1 篇
    for papers_in_topic in topic_buckets.values():
        if papers_in_topic:
            selected.append(papers_in_topic.pop(0))
        if len(selected) >= MAX_PAPERS:
            break

    # 补足到 MAX_PAPERS
    if len(selected) < MAX_PAPERS:
        remaining = [p for bucket in topic_buckets.values() for p in bucket]
        remaining.sort(key=score_paper, reverse=True)
        selected += remaining[: MAX_PAPERS - len(selected)]

    return selected[:MAX_PAPERS]


def main():
    print(f"\n{'=' * 50}")
    print(f"arxiv-weekly 开始运行：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 50}\n")

    seen_ids = load_seen_ids()
    print(f"已记录论文数：{len(seen_ids)}\n")

    # 1. 抓取 arxiv 论文
    all_papers = fetch_papers()

    # 2. 在补充引用前先做粗筛（节省 API 请求）
    candidate_papers = [p for p in all_papers if p["id"] not in seen_ids]
    print(f"\n未见过的论文：{len(candidate_papers)} 篇\n")

    if not candidate_papers:
        print("本周没有新论文，跳过邮件发送。")
        return

    # 3. 补充引用数（只查候选论文）
    candidate_papers = enrich_citations(candidate_papers)

    # 4. 精选 MAX_PAPERS 篇
    selected = select_new_papers(candidate_papers, seen_ids)
    print(f"\n精选 {len(selected)} 篇论文\n")

    # 5. 翻译标题和摘要
    selected = translate_papers(selected)

    # 6. 推送微信（Server酱）
    send_email(selected)

    # 7. 更新已见记录（保存所有候选，不只是精选，避免下次重复抓取低分论文）
    new_ids = {p["id"] for p in candidate_papers}
    seen_ids.update(new_ids)
    save_seen_ids(seen_ids)
    print(f"\n已更新 seen_ids，共记录 {len(seen_ids)} 篇")
    print("\n✅ 完成\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 运行出错：{e}", file=sys.stderr)
        sys.exit(1)
