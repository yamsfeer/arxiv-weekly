"""全局配置：时区、路径、抓取窗口、推送渠道。

所有可以在不改代码的情况下调整的开关都放在这里，统一从环境变量读取。
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# 全部时间按北京时间计算（GitHub Actions 的容器是 UTC，不能直接用 datetime.now()）
TZ = ZoneInfo("Asia/Shanghai")

DATA_DIR = Path("data")
PAPERS_DIR = Path("papers")
SEEN_IDS_FILE = DATA_DIR / "seen_ids.json"


def now() -> datetime:
    return datetime.now(TZ)


def today_str() -> str:
    return now().strftime("%Y-%m-%d")


def env_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise SystemExit(f"环境变量 {name} 必须是整数，当前值：{raw!r}")
    if value < minimum:
        raise SystemExit(f"环境变量 {name} 不能小于 {minimum}，当前值：{value}")
    return value


# 每次推送篇数
MAX_PAPERS = env_int("MAX_PAPERS", 10)
# 抓取窗口：向前回溯天数（放宽一点，覆盖周末与假期）
DAYS_BACK = env_int("DAYS_BACK", 10)
# 每个话题最多抓多少条候选
MAX_PER_TOPIC = env_int("MAX_PER_TOPIC", 50)
# seen_ids 保留天数，过期的自动清掉，避免文件无限膨胀
SEEN_RETAIN_DAYS = env_int("SEEN_RETAIN_DAYS", 120)

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash").strip()
