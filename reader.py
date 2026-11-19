"""把导读渲染成手机优先的中文精读页（GitHub Pages 直接托管）。"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from config import PAPERS_DIR

STYLE = """
:root{--bg:#f5f6f8;--card:#fff;--ink:#17202a;--muted:#63707c;--accent:#1d5cff;--line:#e6eaf0;--soft:#f0f4ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.8 -apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:720px;margin:0 auto;padding:22px 16px 64px}
.hero{padding:8px 4px 18px}
.hero .tag{display:inline-block;font-size:12px;letter-spacing:.08em;color:var(--accent);font-weight:700}
.hero h1{font-size:26px;line-height:1.3;margin:6px 0 6px}
.hero p{margin:0;color:var(--muted);font-size:14px}
.toc{display:flex;gap:8px;overflow-x:auto;padding:4px 0 18px;scrollbar-width:none}
.toc::-webkit-scrollbar{display:none}
.toc a{flex:0 0 auto;font-size:13px;color:var(--muted);text-decoration:none;background:#fff;border:1px solid var(--line);border-radius:999px;padding:7px 12px;white-space:nowrap}
.paper{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px 18px 16px;margin:0 0 18px;box-shadow:0 1px 2px rgba(16,24,40,.04)}
.kicker{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--muted)}
.num{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;background:var(--accent);color:#fff;font-weight:700;font-size:12px}
.badge{background:var(--soft);color:var(--accent);border-radius:999px;padding:2px 8px;font-weight:600}
.paper h2{font-size:21px;line-height:1.45;margin:10px 0 6px}
.en{color:var(--muted);font-size:13px;line-height:1.6;margin:0 0 14px}
.one-liner{background:var(--soft);border-left:3px solid var(--accent);border-radius:0 10px 10px 0;padding:10px 12px;font-size:16px;line-height:1.7;margin:0 0 6px}
.one-liner b,.takeaway b{display:block;font-size:11px;letter-spacing:.12em;color:var(--accent);margin-bottom:2px}
section{margin:16px 0 0}
section h3{font-size:13px;color:var(--muted);margin:0 0 4px;font-weight:700;letter-spacing:.04em}
section p{margin:0;font-size:15.5px}
.result{font-weight:600}
.terms dl{margin:0;display:grid;gap:8px}
.term{display:grid;grid-template-columns:88px 1fr;gap:10px;font-size:15px}
.term dt{font-weight:700;color:var(--ink)}
.term dd{margin:0;color:#3b4652}
.takeaway{margin:16px 0 0;padding:10px 12px;border:1px dashed #c9d6f5;border-radius:10px;background:#fafbff;font-size:15px}
.checks{margin:4px 0 0;padding-left:20px;font-size:15px}
.checks li{margin:2px 0}
details{margin:14px 0 0;font-size:14px;color:var(--muted)}
details summary{cursor:pointer}
.paper-foot{margin-top:16px;padding-top:12px;border-top:1px solid var(--line)}
.reading{margin:0;color:var(--muted);font-size:13px}
.links{margin:8px 0 0;display:flex;gap:16px;flex-wrap:wrap}
.links a{color:var(--accent);text-decoration:none;font-size:14px;font-weight:600}
.foot{color:var(--muted);font-size:12px;text-align:center;margin-top:8px}
.foot a{color:var(--muted)}
.issue-list{list-style:none;padding:0;margin:0}
.issue-list li{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin:0 0 10px}
.issue-list a{color:var(--ink);text-decoration:none;font-weight:700;font-size:16px}
.issue-list .meta{display:block;color:var(--muted);font-size:13px;margin-top:2px}
@media (prefers-color-scheme: dark){
  :root{--bg:#0f1216;--card:#161b22;--ink:#e6edf3;--muted:#8b949e;--line:#232b36;--soft:#1a2333}
  .term dd{color:#c9d1d9}
  .takeaway{background:#141a24;border-color:#2b3a55}
}
"""


def esc(text) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def format_date(date_str: str) -> str:
    try:
        y, m, d = date_str.split("-")
        return f"{y} / {m} / {d}"
    except ValueError:
        return date_str


def _card(index: int, paper: Dict, brief: Dict) -> str:
    terms = brief.get("terms") or []
    terms_html = "".join(
        f'<div class="term"><dt>{esc(t["term"])}</dt><dd>{esc(t["plain"])}</dd></div>'
        for t in terms
    )
    checks = brief.get("self_check") or []
    checks_html = "".join(f"<li>{esc(q)}</li>" for q in checks)
    abstract = paper.get("abstract_zh") or paper.get("abstract", "")

    return f"""
<article class="paper" id="p{index}">
  <header class="paper-head">
    <div class="kicker"><span class="num">{index}</span><span class="badge">{esc(paper.get('topic',''))}</span><span class="date">{esc(paper.get('published',''))}</span></div>
    <h2>{esc(paper.get('title_zh') or paper['title'])}</h2>
    <p class="en">{esc(paper['title'])}</p>
  </header>

  <div class="one-liner"><b>一句话</b>{esc(brief.get('one_liner',''))}</div>

  <section><h3>它要解决什么</h3><p>{esc(brief.get('background',''))}</p></section>
  <section><h3>为什么值得读</h3><p>{esc(brief.get('why',''))}</p></section>
  <section><h3>怎么做的</h3><p>{esc(brief.get('how',''))}</p></section>
  <section><h3>关键结果</h3><p class="result">{esc(brief.get('results',''))}</p></section>

  {f'<section class="terms"><h3>三个术语</h3><dl>{terms_html}</dl></section>' if terms_html else ''}

  <div class="takeaway"><b>如果只记一件事</b>{esc(brief.get('takeaway',''))}</div>

  {f'<section><h3>自测</h3><ol class="checks">{checks_html}</ol></section>' if checks_html else ''}

  <details><summary>展开中文摘要</summary><p>{esc(abstract)}</p></details>

  <footer class="paper-foot">
    <p class="reading">怎么读：{esc(brief.get('reading',''))}</p>
    <p class="links"><a href="{esc(paper['url'])}">arXiv 原文</a><a href="{esc(paper.get('pdf') or paper['url'])}">PDF</a></p>
  </footer>
</article>"""


def render_issue(papers: List[Dict], briefs: Dict[str, Dict], date_str: str) -> str:
    cards = "".join(
        _card(i, paper, briefs.get(paper["id"], {})) for i, paper in enumerate(papers, 1)
    )
    toc = "".join(
        f'<a href="#p{i}">{i}. {esc((paper.get("title_zh") or paper["title"])[:18])}</a>'
        for i, paper in enumerate(papers, 1)
    )
    topics = " · ".join(dict.fromkeys(p.get("topic", "") for p in papers))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#1d5cff">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>论文精读 · {esc(date_str)}</title>
<style>{STYLE}</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <span class="tag">每周论文精读</span>
    <h1>{esc(format_date(date_str))} · {len(papers)} 篇</h1>
    <p>先看人话版，再决定要不要读原文。{esc(topics)}</p>
  </div>
  <nav class="toc">{toc}</nav>
  {cards}
  <p class="foot">内容由 LLM 依据论文生成，数字与结论请以原文为准 · <a href="../">往期</a></p>
</div>
</body>
</html>"""


def save_issue(
    papers: List[Dict],
    briefs: Dict[str, Dict],
    date_str: str,
    base_dir: Optional[Path] = None,
) -> Path:
    """写 papers/{date}/index.html 与 briefs.json，返回页面路径。"""
    base = base_dir or PAPERS_DIR
    out_dir = base / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "briefs.json").write_text(
        json.dumps(briefs, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    page = out_dir / "index.html"
    page.write_text(render_issue(papers, briefs, date_str), encoding="utf-8")
    print(f"[reader] 已生成精读页 {page}")
    return page


def save_index(base_dir: Optional[Path] = None) -> Path:
    """生成 papers/index.html，列出所有期。"""
    base = base_dir or PAPERS_DIR
    issues = sorted(
        (p.parent.name for p in base.glob("*/index.html") if re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.parent.name)),
        reverse=True,
    )
    items = []
    for date_str in issues:
        count = ""
        data_file = base / date_str / "briefs.json"
        if data_file.exists():
            try:
                count = f"{len(json.loads(data_file.read_text(encoding='utf-8')))} 篇"
            except json.JSONDecodeError:
                count = ""
        items.append(
            f'<li><a href="{date_str}/">{esc(date_str)}</a><span class="meta">{esc(count)}</span></li>'
        )

    page = base / "index.html"
    page.write_text(
        f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>论文精读 · 往期</title>
<style>{STYLE}</style>
</head>
<body>
<div class="wrap">
  <div class="hero"><span class="tag">每周论文精读</span><h1>往期</h1><p>每周一更新，共 {len(issues)} 期。</p></div>
  <ul class="issue-list">{''.join(items) or '<li>还没有任何一期。</li>'}</ul>
</div>
</body>
</html>""",
        encoding="utf-8",
    )
    print(f"[reader] 已生成往期索引 {page}")
    return page
