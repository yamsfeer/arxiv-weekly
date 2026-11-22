"""已推送论文的记录：id -> 最后一次出现的日期。

老版本是一个纯 id 列表，只增不减（已经 2400+ 条）。现在带日期，并按保留天数清理。
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Iterable, Optional

from config import SEEN_IDS_FILE, SEEN_RETAIN_DAYS, today_str
from ids import normalize_id


def _normalize(seen: Dict[str, str]) -> Dict[str, str]:
    """统一 id 格式（去版本号），顺手合并重复键并保留较新的日期。"""
    out: Dict[str, str] = {}
    for paper_id, last_seen in (seen or {}).items():
        key = normalize_id(str(paper_id))
        if not key:
            continue
        value = str(last_seen)
        out[key] = max(out[key], value) if key in out else value
    return out


def _parse_day(value: str) -> Optional[date]:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def prune(seen: Dict[str, str], retain_days: int = SEEN_RETAIN_DAYS, today: str | None = None) -> Dict[str, str]:
    """丢掉太久没再出现的 id。返回新 dict，不修改入参。"""
    today_day = _parse_day(today or today_str()) or date.today()
    cutoff = today_day - timedelta(days=retain_days)
    kept = {}
    for paper_id, last_seen in (seen or {}).items():
        last_day = _parse_day(last_seen)
        if last_day is None or last_day >= cutoff:
            kept[paper_id] = last_seen
    return kept


def load(path: Path = SEEN_IDS_FILE) -> Dict[str, str]:
    """读取记录，兼容老版本的字符串列表格式。"""
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[store] 读取 {path} 失败，按空记录处理：{exc}")
        return {}

    today = today_str()
    if isinstance(raw, list):
        return _normalize({str(item): today for item in raw if item})
    if isinstance(raw, dict):
        return _normalize({str(k): str(v) for k, v in raw.items() if k})
    print(f"[store] {path} 格式不认识，按空记录处理")
    return {}


def save(seen: Dict[str, str], path: Path = SEEN_IDS_FILE) -> Dict[str, str]:
    """清理过期记录后写盘，返回真正保存的内容。"""
    pruned = prune(_normalize(seen))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(sorted(pruned.items())), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return pruned


def mark(seen: Dict[str, str], paper_ids: Iterable[str], day: str | None = None) -> Dict[str, str]:
    """把一批 id 标记为"今天见过"（原地更新并返回）。"""
    seen_day = day or today_str()
    for paper_id in paper_ids:
        key = normalize_id(str(paper_id))
        if key:
            seen[key] = seen_day
    return seen
