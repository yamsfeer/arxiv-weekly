"""
通过 Server酱（sct.ftqq.com）推送论文摘要到微信
Server酱 API 文档：https://sct.ftqq.com/
"""
import os
import requests
from datetime import datetime
from typing import List, Dict

SERVERCHAN_API = "https://sctapi.ftqq.com/{sendkey}.send"


def _popularity_label(paper: Dict) -> str:
    citations = paper.get("citations", 0)
    influential = paper.get("influential_citations", 0)
    if citations == 0:
        return "新论文·暂无引用"
    label = f"被引 {citations} 次"
    if influential:
        label += f"（高影响 {influential} 次）"
    return label


def _paper_block(index: int, paper: Dict) -> str:
    """生成单篇论文的 Markdown 块"""
    popularity = _popularity_label(paper)
    authors = "、".join(paper.get("authors", []))
    title_zh = paper.get("title_zh", paper["title"])
    abstract_zh = paper.get("abstract_zh", paper["abstract"])

    return (
        f"### {index}. [{title_zh}]({paper['url']})\n\n"
        f"*{paper['title']}*\n\n"
        f"> {paper['topic']} · {paper['published']} · {popularity}\n\n"
        f"{abstract_zh}\n\n"
        f"作者：{authors}\n\n"
        "---\n\n"
    )


def build_markdown(papers: List[Dict]) -> str:
    date_str = datetime.now().strftime("%Y年%m月%d日")
    blocks = "".join(_paper_block(i + 1, p) for i, p in enumerate(papers))
    footer = "*由 GitHub Actions + DeepSeek 自动生成 · 数据来源：arxiv & Semantic Scholar*"
    return f"**{date_str} · 共 {len(papers)} 篇**\n\n---\n\n{blocks}{footer}"


def send_email(papers: List[Dict]):
    """函数名保持不变，实际通过 Server酱 推送到微信"""
    sendkey = os.environ.get("SERVERCHAN_SENDKEY")
    if not sendkey:
        raise ValueError("环境变量 SERVERCHAN_SENDKEY 未设置")

    date_str = datetime.now().strftime("%Y/%m/%d")
    title = f"📚 每周论文推荐 {date_str}（{len(papers)} 篇）"
    desp = build_markdown(papers)

    url = SERVERCHAN_API.format(sendkey=sendkey)
    print(f"[wechat] 正在推送到微信...")

    resp = requests.post(url, data={"title": title, "desp": desp}, timeout=15)
    resp.raise_for_status()

    result = resp.json()
    if result.get("data", {}).get("errno") == 0 or result.get("code") == 0:
        print("[wechat] 推送成功")
    else:
        print(f"[wechat] 推送返回：{result}")
