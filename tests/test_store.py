"""seen_ids 存储：老格式迁移、过期清理、写盘格式。"""
import json

import store


def test_load_migrates_legacy_list(tmp_path):
    path = tmp_path / "seen_ids.json"
    path.write_text(json.dumps(["2611.00001", "2611.00002"]), encoding="utf-8")

    seen = store.load(path)

    assert isinstance(seen, dict)
    assert set(seen) == {"2611.00001", "2611.00002"}
    assert all(len(v) == 10 for v in seen.values())


def test_load_missing_file_returns_empty(tmp_path):
    assert store.load(tmp_path / "nope.json") == {}


def test_load_broken_json_returns_empty(tmp_path):
    path = tmp_path / "seen_ids.json"
    path.write_text("{not json", encoding="utf-8")
    assert store.load(path) == {}


def test_prune_drops_old_entries():
    seen = {"old": "2026-01-01", "fresh": "2026-11-01"}
    kept = store.prune(seen, retain_days=120, today="2026-11-09")
    assert kept == {"fresh": "2026-11-01"}


def test_prune_keeps_entries_with_unparseable_date():
    seen = {"weird": "unknown"}
    assert store.prune(seen, retain_days=1, today="2026-11-09") == seen


def test_save_prunes_and_sorts(tmp_path):
    path = tmp_path / "seen_ids.json"
    store.save({"b": "2026-11-09", "a": "2026-11-09", "old": "2025-01-01"}, path)

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert list(raw) == ["a", "b"]  # 已排序、已清理


def test_mark_updates_dates():
    seen = {"a": "2026-01-01"}
    store.mark(seen, ["a", "b"], day="2026-11-09")
    assert seen == {"a": "2026-11-09", "b": "2026-11-09"}


def test_load_strips_arxiv_version_suffixes(tmp_path):
    """老版本存的是带版本号的 id，迁移后必须和新 id 对得上。"""
    path = tmp_path / "seen_ids.json"
    path.write_text(json.dumps(["2611.09693v1", "hep-th/9901001v2"]), encoding="utf-8")

    seen = store.load(path)

    assert set(seen) == {"2611.09693", "hep-th/9901001"}


def test_mark_normalizes_ids():
    seen = {}
    store.mark(seen, ["2611.09693v2"], day="2026-11-09")
    assert seen == {"2611.09693": "2026-11-09"}
