"""把导读渲染成手机优先的中文精读页（GitHub Pages 直接托管）。

样式参考 Claude：暖白纸张底、赭色点缀、衬线标题、宽行距。
桌面端左侧固定目录，移动端变成抽屉，滚动时高亮当前篇。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from config import PAPERS_DIR

STYLE = """
:root{
  --bg:#f7f5f0; --card:#fffdf9; --ink:#1f1e1c; --muted:#6f6a62;
  --line:#e7e1d6; --accent:#c96442; --accent-soft:#f8ede7; --soft:#f3efe7;
  --serif:"Tiempos Text","Iowan Old Style",Georgia,"Songti SC","Noto Serif SC",serif;
  --sans:-apple-system,BlinkMacSystemFont,"Inter","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.85 var(--sans);-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
a{color:inherit}
.shell{max-width:1080px;margin:0 auto;padding:44px 24px 96px;display:grid;grid-template-columns:252px minmax(0,1fr);gap:64px;align-items:start}

/* 左侧目录 */
.sidebar{position:sticky;top:36px}
.brand{display:inline-block;font:600 13px/1.4 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--accent);text-decoration:none}
.side-date{font-family:var(--serif);font-size:19px;line-height:1.4;margin:10px 0 4px}
.side-count{color:var(--muted);font-size:13px;margin:0 0 22px}
.nav{display:flex;flex-direction:column;gap:2px}
.nav a{display:grid;grid-template-columns:22px 1fr;gap:10px;padding:9px 10px 9px 8px;border-radius:9px;text-decoration:none;color:#4d4942;font-size:13.5px;line-height:1.45;border-left:2px solid transparent;transition:background .15s,color .15s}
.nav a:hover{background:var(--soft)}
.nav a .n{color:var(--muted);font-variant-numeric:tabular-nums;font-size:12px;padding-top:1px}
.nav a .t{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.nav a.active{background:var(--accent-soft);color:var(--accent);border-left-color:var(--accent)}
.nav a.active .n{color:var(--accent)}
.side-foot{margin-top:24px;padding-top:16px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}
.side-foot a{color:var(--muted);text-decoration:none}
.side-foot a:hover{color:var(--accent)}

/* 顶部栏（移动端） */
.topbar{display:none;position:sticky;top:0;z-index:30;align-items:center;gap:12px;padding:10px 16px;background:rgba(247,245,240,.92);backdrop-filter:saturate(180%) blur(12px);border-bottom:1px solid var(--line)}
.menu-btn{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:7px 13px;font:600 13px var(--sans)}
.topbar-title{font-family:var(--serif);font-size:15px;color:#3d3933}
.overlay{display:none;position:fixed;inset:0;background:rgba(31,30,28,.32);z-index:20}
.overlay.show{display:block}

/* 内容 */
.hero{padding:2px 2px 10px}
.hero h1{font-family:var(--serif);font-weight:600;font-size:38px;line-height:1.2;letter-spacing:-.015em;margin:6px 0 10px}
.hero p{margin:0;color:var(--muted);font-size:14.5px;line-height:1.7}
.paper{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:30px 32px 24px;margin:28px 0 0;box-shadow:0 1px 2px rgba(60,50,35,.04),0 8px 24px -18px rgba(60,50,35,.22);scroll-margin-top:76px}
.kicker{display:flex;align-items:center;gap:9px;font-size:12px;color:var(--muted)}
.num{display:inline-flex;align-items:center;justify-content:center;width:23px;height:23px;border-radius:50%;background:var(--accent);color:#fff;font-weight:600;font-size:12px}
.badge{background:var(--accent-soft);color:var(--accent);border-radius:999px;padding:3px 10px;font-weight:600;font-size:11.5px}
.date{font-variant-numeric:tabular-nums}
.paper h2{font-family:var(--serif);font-weight:600;font-size:25px;line-height:1.38;letter-spacing:-.01em;margin:12px 0 6px}
.en{color:var(--muted);font-size:13px;line-height:1.6;margin:0 0 20px}
.one-liner{background:var(--accent-soft);border-left:3px solid var(--accent);border-radius:0 12px 12px 0;padding:13px 16px;font-size:17.5px;line-height:1.75;margin:0 0 4px}
.one-liner b,.takeaway b{display:block;font:600 10.5px/1.4 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:var(--accent);margin-bottom:4px}
section{margin:22px 0 0}
section h3{font:600 11.5px/1.4 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:0 0 7px}
section p{margin:0;font-size:16.5px;line-height:1.85}
.result{font-weight:500}
.terms dl{margin:0;display:grid;gap:10px}
.term{display:grid;grid-template-columns:118px 1fr;gap:14px;font-size:15.5px;line-height:1.7}
.term dt{font-weight:600;color:#3d3933}
.term dd{margin:0;color:#5a554d}
.takeaway{margin:24px 0 0;padding:14px 16px;border:1px solid #e3d9c8;border-radius:12px;background:var(--soft);font-size:16px;line-height:1.75}
.checks{margin:4px 0 0;padding-left:20px;font-size:16px;line-height:1.8}
.checks li{margin:3px 0}
details{margin:22px 0 0;font-size:14.5px;color:var(--muted);border-top:1px solid var(--line);padding-top:14px}
details summary{cursor:pointer;font-weight:600;color:#5a554d}
details p{margin:10px 0 0;line-height:1.8}
.paper-foot{margin-top:22px;padding-top:16px;border-top:1px solid var(--line)}
.reading{margin:0;color:var(--muted);font-size:13.5px;line-height:1.7}
.links{margin:12px 0 0;display:flex;gap:10px;flex-wrap:wrap}
.links a{display:inline-block;text-decoration:none;font:600 13px var(--sans);color:var(--accent);border:1px solid #e6cdc2;background:#fff;border-radius:999px;padding:7px 14px}
.links a:hover{background:var(--accent-soft)}
.foot{color:var(--muted);font-size:12.5px;text-align:center;margin:36px 0 0}
.foot a{color:var(--muted)}
.issue-list{list-style:none;padding:0;margin:28px 0 0}
.issue-list li{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:0 0 10px}
.issue-list a{color:var(--ink);text-decoration:none;font-family:var(--serif);font-weight:600;font-size:18px}
.issue-list .meta{display:block;color:var(--muted);font-size:13px;margin-top:2px;font-family:var(--sans)}

@media (max-width:1023px){
  .shell{display:block;padding:0 16px 72px}
  .topbar{display:flex}
  .sidebar{position:fixed;left:0;top:0;bottom:0;width:84%;max-width:330px;background:var(--card);border-right:1px solid var(--line);padding:22px 18px;overflow:auto;z-index:25;transform:translateX(-104%);transition:transform .22s ease;box-shadow:0 0 40px rgba(60,50,35,.14)}
  .sidebar.open{transform:none}
  .hero{padding:22px 2px 6px}
  .hero h1{font-size:30px}
  .paper{padding:22px 20px 18px;border-radius:16px;margin-top:22px}
  .paper h2{font-size:21px}
  .term{grid-template-columns:96px 1fr;gap:10px}
}
@media (prefers-color-scheme:dark){
  :root{--bg:#151412;--card:#1d1b18;--ink:#ece7df;--muted:#a19a8f;--line:#2e2a24;--accent-soft:#3a2822;--soft:#24211c}
  .topbar{background:rgba(21,20,18,.92)}
  .nav a{color:#b9b1a5}
  .nav a.active{color:#e08a68}
  .term dt{color:#ddd6ca}
  .term dd{color:#b9b1a5}
  .reading,details summary{color:#b9b1a5}
  .links a{background:transparent;border-color:#4a352c}
}
"""

SCRIPT = """
(function () {
  var links = Array.prototype.slice.call(document.querySelectorAll('.nav a'));
  var papers = Array.prototype.slice.call(document.querySelectorAll('.paper'));
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var id = '#' + entry.target.id;
        links.forEach(function (link) {
          link.classList.toggle('active', link.getAttribute('href') === id);
        });
      });
    }, { rootMargin: '-15% 0px -70% 0px', threshold: 0 });
    papers.forEach(function (paper) { io.observe(paper); });
  }
  if (links.length) links[0].classList.add('active');

  var sidebar = document.querySelector('.sidebar');
  var overlay = document.querySelector('.overlay');
  var button = document.querySelector('.menu-btn');
  function close() {
    if (!sidebar) return;
    sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('show');
  }
  if (button) {
    button.addEventListener('click', function () {
      sidebar.classList.add('open');
      overlay.classList.add('show');
    });
  }
  if (overlay) overlay.addEventListener('click', close);
  links.forEach(function (link) { link.addEventListener('click', close); });
})();
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


def _short(title: str, limit: int = 26) -> str:
    return title if len(title) <= limit else title[: limit - 1] + "…"


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
    nav = "".join(
        f'<a href="#p{i}"><span class="n">{i:02d}</span><span class="t">{esc(_short(paper.get("title_zh") or paper["title"]))}</span></a>'
        for i, paper in enumerate(papers, 1)
    )
    topics = " · ".join(dict.fromkeys(p.get("topic", "") for p in papers))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#f7f5f0">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>论文精读 · {esc(date_str)}</title>
<style>{STYLE}</style>
</head>
<body>
<header class="topbar">
  <button class="menu-btn" aria-label="打开目录">☰ 目录</button>
  <span class="topbar-title">{esc(format_date(date_str))}</span>
</header>
<div class="overlay"></div>
<div class="shell">
  <aside class="sidebar">
    <a class="brand" href="../">Weekly Papers</a>
    <p class="side-date">{esc(format_date(date_str))}</p>
    <p class="side-count">{len(papers)} 篇 · {esc(topics)}</p>
    <nav class="nav">{nav}</nav>
    <div class="side-foot"><a href="../">← 往期</a></div>
  </aside>
  <main class="content">
    <div class="hero">
      <h1>{len(papers)} 篇值得看的论文</h1>
      <p>先看人话版，再决定要不要读原文。</p>
    </div>
    {cards}
    <p class="foot">内容由 LLM 依据论文生成，数字与结论请以原文为准</p>
  </main>
</div>
<script>{SCRIPT}</script>
</body>
</html>"""


def save_issue(
    papers: List[Dict],
    briefs: Dict[str, Dict],
    date_str: str,
    base_dir: Optional[Path] = None,
) -> Path:
    """写 papers/{date}/index.html、papers.json、briefs.json，返回页面路径。"""
    base = base_dir or PAPERS_DIR
    out_dir = base / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "briefs.json").write_text(
        json.dumps(briefs, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "papers.json").write_text(
        json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8"
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
<meta name="theme-color" content="#f7f5f0">
<title>论文精读 · 往期</title>
<style>{STYLE}</style>
</head>
<body>
<div class="shell" style="display:block;max-width:720px">
  <div class="hero"><span class="brand">Weekly Papers</span><h1>往期</h1><p>每周一更新，共 {len(issues)} 期。</p></div>
  <ul class="issue-list">{''.join(items) or '<li>还没有任何一期。</li>'}</ul>
</div>
</body>
</html>""",
        encoding="utf-8",
    )
    print(f"[reader] 已生成往期索引 {page}")
    return page
