#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan.py —— 抓包结果扫描器：帮助定位「承载角色数据的接口」

在 mitmproxy_addon.py 产出 dump/ 目录（含 index.jsonl）之后运行本工具，
按 host+path 聚合展示流量，并尝试解析 JSON 响应的顶层字段，
辅助用户判断哪个接口包含 角色 / 蓝图 / 加点 / 模块 / 指挥值 数据。

用法示例
--------
    python3 scan.py                          # 扫描 ./dump
    python3 scan.py ./dump --top 20          # 只看前 20 组
    python3 scan.py ./dump --grep role       # 只看 URL/字段 含 role 的
    python3 scan.py ./dump --json            # 机器可读输出
    python3 scan.py --help

说明
----
- 仅做本地文件扫描，不联网、不访问游戏。
- 字段名/接口路径的最终确认仍需用户抓包判断；本工具的"疑似"提示只是启发式。
"""

import argparse
import json
import os
import sys
from collections import defaultdict

# 启发式关键词：用于提示"疑似承载角色数据"的接口。
# 待用户抓包确认 —— 不同渠道/版本的字段命名可能不同，可自行增删。
ROLE_HINTS = (
    "role", "player", "character", "profile", "account", "user",
    "blueprint", "ship", "fleet", "warship", "vessel",
    "currency", "resource", "asset", "item", "bag", "inventory", "warehouse",
    "module", "skill", "level", "points", "uid", "nickname", "power",
    "command", "metal", "crystal", "deuterium",
)

DEFAULT_INDEX_NAME = "index.jsonl"
BODY_READ_LIMIT = 2_000_000  # 单文件最多读取字节，避免超大文件拖慢


def _log_err(msg: str) -> None:
    print(f"[scan] {msg}", file=sys.stderr)


def resolve_index_path(dump_dir: str, explicit: str = None) -> str:
    if explicit:
        return explicit
    return os.path.join(dump_dir, DEFAULT_INDEX_NAME)


def load_index(index_path: str) -> list:
    if not os.path.exists(index_path):
        _log_err(f"未找到索引文件：{index_path}")
        _log_err("请先运行 mitmproxy -s mitmproxy_addon.py 抓包，或将 --dump 指向正确目录。")
        return []
    entries = []
    with open(index_path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    entries.append(obj)
            except json.JSONDecodeError as exc:
                _log_err(f"index.jsonl 第 {lineno} 行解析失败，已跳过：{exc}")
    return entries


def _read_body(dump_dir: str, entry: dict) -> str:
    """读取响应的可读文本（若为二进制预览则返回空）。"""
    if entry.get("resp_binary"):
        return ""
    fname = entry.get("resp_file")
    if not fname:
        return ""
    path = os.path.join(dump_dir, fname)
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "rb") as fh:
            raw = fh.read(BODY_READ_LIMIT)
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _top_level_fields(text: str, limit: int = 25):
    """尝试解析 JSON，返回 (ok, fields, kind)。kind: object/array/None"""
    text = (text or "").strip()
    if not text or text[0] not in "{[":
        return (False, [], None)
    try:
        data = json.loads(text)
    except Exception:
        return (False, [], None)
    if isinstance(data, dict):
        return (True, sorted(data.keys())[:limit], "object")
    if isinstance(data, list):
        # 若为数组，取首个元素（若为对象）的字段
        if data and isinstance(data[0], dict):
            return (True, sorted(data[0].keys())[:limit], "array-of-object")
        return (True, [], "array")
    return (True, [], None)


def _entry_text(entry: dict, body_cache: dict, dump_dir: str) -> str:
    """拼出用于 --grep 匹配的文本。"""
    eid = entry.get("id")
    body = ""
    if eid in body_cache:
        body = body_cache[eid]
    parts = [
        str(entry.get("url", "")),
        str(entry.get("host", "")),
        str(entry.get("path", "")),
        str(entry.get("method", "")),
        str(entry.get("content_type", "")),
        str(entry.get("channel", "")),
    ]
    return " ".join(parts) + " " + body


def aggregate(entries: list, dump_dir: str, grep_terms, show_fields: bool, fields_limit: int):
    groups = {}
    body_cache = {}
    grep_terms = [g.lower() for g in (grep_terms or [])]

    matched_entries = []
    for entry in entries:
        if grep_terms:
            eid = entry.get("id")
            if eid not in body_cache:
                body_cache[eid] = _read_body(dump_dir, entry)
            haystack = _entry_text(entry, body_cache, dump_dir).lower()
            if not any(term in haystack for term in grep_terms):
                continue
        matched_entries.append(entry)

        key = (str(entry.get("host", "")), str(entry.get("path", "")))
        g = groups.setdefault(
            key,
            {
                "host": key[0],
                "path": key[1],
                "count": 0,
                "total_size": 0,
                "statuses": defaultdict(int),
                "content_types": defaultdict(int),
                "json_count": 0,
                "channels": set(),
                "sample_url": "",
                "entries": [],
                "fields": set(),
                "field_kinds": set(),
            },
        )
        g["count"] += 1
        g["total_size"] += int(entry.get("resp_size", 0) or 0)
        g["statuses"][int(entry.get("status", 0) or 0)] += 1
        ct = str(entry.get("content_type", "") or "")
        if ct:
            g["content_types"][ct.split(";")[0].strip()] += 1
        if entry.get("resp_is_json"):
            g["json_count"] += 1
        if entry.get("channel"):
            g["channels"].add(str(entry.get("channel")))
        if not g["sample_url"]:
            g["sample_url"] = str(entry.get("url", ""))
        g["entries"].append(entry)

        # 字段探测：每个分组最多解析少量 JSON 响应
        if show_fields and entry.get("resp_is_json") and len(g["fields"]) < fields_limit:
            eid = entry.get("id")
            if eid not in body_cache:
                body_cache[eid] = _read_body(dump_dir, entry)
            ok, fields, kind = _top_level_fields(body_cache.get(eid, ""), fields_limit)
            if ok:
                g["fields"].update(fields)
                if kind:
                    g["field_kinds"].add(kind)

    result = []
    for g in groups.values():
        hint = _is_role_like(g)
        result.append(
            {
                "host": g["host"],
                "path": g["path"],
                "count": g["count"],
                "avg_size": int(g["total_size"] / g["count"]) if g["count"] else 0,
                "max_size": max(
                    (int(e.get("resp_size", 0) or 0) for e in g["entries"]), default=0
                ),
                "statuses": dict(g["statuses"]),
                "content_types": dict(g["content_types"]),
                "json_count": g["json_count"],
                "channels": sorted(g["channels"]),
                "sample_url": g["sample_url"],
                "fields": sorted(g["fields"])[:fields_limit],
                "field_kinds": sorted(g["field_kinds"]),
                "role_like": hint,
            }
        )

    # 排序：疑似角色数据优先，其次出现次数多的优先
    result.sort(key=lambda x: (not x["role_like"], -x["count"]))
    return result, len(matched_entries)


def _is_role_like(g) -> bool:
    haystack = (g["path"] + " " + " ".join(g["fields"])).lower()
    return any(h in haystack for h in ROLE_HINTS)


def print_table(groups, total_matched: int, show_fields: bool):
    if not groups:
        print("没有匹配的流量。")
        return
    print(f"共 {total_matched} 条流量，聚合为 {len(groups)} 组接口：\n")
    for i, g in enumerate(groups, 1):
        flag = "★疑似角色数据" if g["role_like"] else ""
        print(f"[{i}] {g['host']}{g['path']}  {flag}")
        print(
            f"    次数={g['count']}  平均响应={g['avg_size']}B  最大={g['max_size']}B  "
            f"JSON命中={g['json_count']}  渠道={g['channels'] or '-'}"
        )
        cts = ", ".join(f"{k}×{v}" for k, v in g["content_types"].items()) or "-"
        print(f"    content-type: {cts}")
        if show_fields and g["fields"]:
            kinds = ",".join(g["field_kinds"]) or "?"
            fields = ", ".join(g["fields"])
            print(f"    顶层字段({kinds}): {fields}")
        print(f"    示例URL: {g['sample_url']}")
        print()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="scan.py",
        description="扫描 mitmproxy dump 目录，聚合接口并探测 JSON 顶层字段，定位角色数据接口。",
        epilog="提示：先用 --grep 缩小范围，再用 --top 查看出现最多的接口。",
    )
    parser.add_argument(
        "dump_dir", nargs="?", default="dump", help="dump 目录（默认 ./dump）"
    )
    parser.add_argument(
        "--index", default=None,
        help="直接指定 index.jsonl 路径（默认 <dump_dir>/index.jsonl）",
    )
    parser.add_argument(
        "-g", "--grep", action="append", default=[],
        help="按关键字过滤（可多次；匹配 URL/host/path/method/content-type/响应体，大小写不敏感）",
    )
    parser.add_argument(
        "--top", type=int, default=30, help="最多展示前 N 组接口（默认 30）",
    )
    parser.add_argument(
        "--json", action="store_true", help="以 JSON 格式输出结果",
    )
    parser.add_argument(
        "--no-fields", action="store_true",
        help="不解析/展示 JSON 顶层字段",
    )
    parser.add_argument(
        "--fields-limit", type=int, default=25,
        help="每组最多展示的顶层字段数（默认 25）",
    )
    args = parser.parse_args(argv)

    index_path = resolve_index_path(args.dump_dir, args.index)
    entries = load_index(index_path)
    if not entries:
        # 无数据时给出友好退出码
        return 1

    groups, total_matched = aggregate(
        entries,
        args.dump_dir,
        args.grep,
        show_fields=not args.no_fields,
        fields_limit=args.fields_limit,
    )
    if args.top and args.top > 0:
        groups = groups[: args.top]

    if args.json:
        print(
            json.dumps(
                {
                    "index": index_path,
                    "total_entries": len(entries),
                    "matched_entries": total_matched,
                    "groups": groups,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print_table(groups, total_matched, show_fields=not args.no_fields)
    return 0


if __name__ == "__main__":
    sys.exit(main())
