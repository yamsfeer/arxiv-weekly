"""arXiv id 与标题的规范化：去重、和 seen_ids 比对都以这里为准。"""
from __future__ import annotations

import re

_VERSION_SUFFIX = re.compile(r"v\d+$")
_NON_ALNUM = re.compile(r"[^a-z0-9\u4e00-\u9fff]+")


def normalize_id(raw_id: str) -> str:
    """去掉 arXiv id 的版本号：2611.09693v2 -> 2611.09693。

    同一篇论文重新提交会变成 v2/v3，带着版本号去重会反复推送同一篇。
    """
    return _VERSION_SUFFIX.sub("", str(raw_id).strip())


def title_key(title: str) -> str:
    """跨话题去重用的标题指纹（忽略大小写、标点、空白）。"""
    return _NON_ALNUM.sub("", title.lower())[:100]
