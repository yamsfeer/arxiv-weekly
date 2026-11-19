"""主入口：抓取 → 去重 → 补引用 → 质量打分 → 精选 → 翻译 → 归档 → 推送飞书 → 记录。

用法：
    python main.py                  # 正式跑一次
    python main.py --dry-run        # 只抓取/精选/翻译，打印卡片不发送、不写文件
    python main.py --test-push      # 只发一张测试卡片，验证飞书配置
"""
from __future__ import annotations

import argparse
import os
import sys

import feishu
import store
from arxiv_fetcher import fetch_papers
from config import MAX_PAPERS, today_str
from digest import plain_text, topic_summary
from paper_saver import save_papers
from quality import annotate, apply_scores, get_client, llm_scoring, preselect
from selector import select_papers
from semantic_fetcher import enrich_citations
from translator import translate_papers

# 每个话题先取多少篇送去 LLM 打分（控制成本）
PRESELECT_PER_TOPIC = 15


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="arXiv 每周论文精选 → 飞书")
    parser.add_argument("--dry-run", action="store_true", help="不推送、不写文件，只打印结果与卡片 JSON")
    parser.add_argument("--test-push", action="store_true", help="发一张测试卡片，验证飞书配置")
    parser.add_argument("--max-papers", type=int, default=None, help=f"本次推送篇数（默认 {MAX_PAPERS}）")
    parser.add_argument("--no-translate", action="store_true", help="跳过翻译，直接用英文原文")
    return parser.parse_args(argv)


def run(args) -> int:
    date_str = today_str()
    archive_url = feishu.github_archive_url(date_str)

    if args.test_push:
        feishu.send_test(dry_run=args.dry_run)
        return 0

    max_papers = args.max_papers or MAX_PAPERS
    seen = store.load()
    print(f"已记录论文数：{len(seen)}")

    papers = fetch_papers()
    candidates = [p for p in papers if p["id"] not in seen]
    print(f"\n未见过的论文：{len(candidates)} 篇\n")

    if not candidates:
        print("本周没有新论文。")
        if not args.dry_run:
            feishu.send_empty_notice(date_str, archive_url)
        return 0

    enrich_citations(candidates)
    annotate(candidates)

    # 每个话题先按关键词取前 N 篇，再交给 LLM 评相关度和扎实度
    pool = preselect(candidates, per_topic=PRESELECT_PER_TOPIC)
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    scores = llm_scoring(pool, get_client(api_key)) if api_key else {}
    if not api_key:
        print("[quality] 没有 DEEPSEEK_API_KEY，跳过 LLM 打分，按关键词+引用排序")
    apply_scores(pool, scores)

    selected = select_papers(pool, max_papers=max_papers)
    print(f"\n精选 {len(selected)} 篇（{topic_summary(selected)}）：\n{plain_text(selected, date_str)}")

    has_key = bool(api_key)
    skip_translate = args.no_translate or not has_key
    if not has_key and not args.no_translate:
        print("[translate] 没有 DEEPSEEK_API_KEY，跳过翻译，保留英文原文")
    selected = translate_papers(selected, skip=skip_translate)

    if args.dry_run:
        from digest import archive_markdown

        print("\n[dry-run] 归档内容如下：\n")
        print(archive_markdown(selected, date_str, archive_url))
        feishu.send_digest(selected, date_str, archive_url, dry_run=True)
        return 0

    # 先落盘归档，这样卡片里的归档链接点开就是本期内容
    save_papers(selected, date_str)
    feishu.send_digest(selected, date_str, archive_url)

    # 只把真正推送过的记为已读：没选中的论文下周还能再竞争一次
    seen = store.save(store.mark(seen, [p["id"] for p in selected]))
    print(f"\n已更新 seen_ids，共记录 {len(seen)} 篇")
    print("\n✅ 完成\n")
    return 0


def main(argv=None) -> int:
    args = parse_args(argv)
    print(f"\n{'=' * 50}")
    print(f"arxiv-weekly 开始运行：{today_str()}")
    print(f"{'=' * 50}\n")
    try:
        return run(args)
    except Exception as exc:
        print(f"\n❌ 运行出错：{exc}", file=sys.stderr)
        if os.environ.get("DEBUG"):
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
