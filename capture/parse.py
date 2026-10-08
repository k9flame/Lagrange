#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse.py —— 把抓包响应按 mapping.yaml 归一化为「标准角色数据模型」

对应契约：/workspace/shared/data-model.md
样例：    /workspace/shared/character.sample.json

用法示例
--------
    # 1) 用抓到的响应 JSON 解析为 character.json
    python3 parse.py --input resp.json --mapping mapping.yaml \
        --channel official --out out/character.json --validate

    # 2) 用样例数据跑通链路（无需真实抓包，供 Demo 前端联调）
    python3 parse.py --from-sample --out out/character.json --validate
    python3 parse.py --from-sample ../shared/character.sample.json --out out/character.json

    # 3) 只看帮助
    python3 parse.py --help

说明
----
- 不联网、不访问游戏。
- mapping.yaml 中的字段路径默认留空（待用户抓包确认）；未配置/找不到的字段
  会：把 meta.completeness 对应分组置 false、键名写入 meta.missingFields，
  并对缺失项使用安全默认值（字符串 ""、数值 0、数组 []），保证不崩溃且结构合法。
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

_HERE = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_MAPPING = os.path.join(_HERE, "mapping.yaml")
_DEFAULT_CHANNELS = os.path.join(_HERE, "channels.yaml")
_DEFAULT_SAMPLE = os.path.normpath(
    os.path.join(_HERE, "..", "shared", "character.sample.json")
)
_CST = timezone(timedelta(hours=8))

# ---------------------------------------------------------------------------
# 标准模型：默认值与必填项
# ---------------------------------------------------------------------------
ROLE_REQUIRED = ["uid", "nickname", "level", "serverName"]
ROLE_OPTIONAL = ["unionName", "power", "updatedAt"]
CURRENCY_REQUIRED = ["metal", "crystal", "deuterium", "commandPoints", "commandLimit"]
CURRENCY_OPTIONAL = ["blueprintPoints"]

ROLE_STR_FIELDS = {"uid", "nickname", "serverName", "unionName", "updatedAt"}
ROLE_NUM_FIELDS = {"level", "power"}
CURRENCY_NUM_FIELDS = set(CURRENCY_REQUIRED) | set(CURRENCY_OPTIONAL)

BLUEPRINT_STR_FIELDS = [
    "id", "name", "alias", "shipClass", "rarity",
    "subModel", "defaultPosition",
]
BLUEPRINT_BOOL_FIELDS = ["owned", "locked"]
BLUEPRINT_NUM_FIELDS = ["level", "pointsAllocated", "pointsTotal"]
MODULE_FIELDS = {"slot": "", "name": "", "unlocked": False}
MODULE_BOOL_FIELDS = {"unlocked"}
SKILL_FIELDS = {"system": "", "name": "", "level": 0, "max": 0}
SKILL_NUM_FIELDS = {"level", "max"}

POSITION_ENUM = ("前排", "中排", "后排")


# ---------------------------------------------------------------------------
# 路径工具：支持 a.b / a[0].b / a[].b（数组通配）
# ---------------------------------------------------------------------------
def _steps(path: str):
    steps = []
    for part in str(path).split("."):
        if not part:
            continue
        m = re.match(r"^([^\[\]]*)", part)
        name = m.group(1) if m else ""
        rest = part[len(name):]
        if name:
            steps.append(("key", name))
        for idx in re.findall(r"\[([^\]]*)\]", rest):
            if idx == "":
                steps.append(("each", None))
            else:
                try:
                    steps.append(("index", int(idx)))
                except ValueError:
                    pass
    return steps


def extract(data, path: str):
    """按路径取值，返回 (found: bool, value)。数组通配会展开为列表。"""
    if not path:
        return (False, None)
    current = [data]
    for kind, val in _steps(path):
        nxt = []
        for node in current:
            if node is None:
                continue
            if kind == "key":
                if isinstance(node, dict) and val in node:
                    nxt.append(node[val])
            elif kind == "index":
                if isinstance(node, list) and 0 <= val < len(node):
                    nxt.append(node[val])
            elif kind == "each":
                if isinstance(node, list):
                    nxt.extend(node)
        current = nxt
        if not current:
            return (False, None)
    if len(current) == 1:
        return (True, current[0])
    return (True, current)


def to_int(value, default=0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return default
        try:
            return int(float(s))
        except ValueError:
            return default
    return default


def to_bool(value, default=False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        s = value.strip().lower()
        if s in ("1", "true", "yes", "y", "on", "是"):
            return True
        if s in ("0", "false", "no", "n", "off", "否"):
            return False
    return default


def to_str(value, default="") -> str:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


# ---------------------------------------------------------------------------
# 配置读取
# ---------------------------------------------------------------------------
def load_yaml(path: str):
    try:
        import yaml
    except Exception:
        print(
            "[parse] 未安装 PyYAML，无法读取配置文件；请先 pip install -r requirements.txt。",
            file=sys.stderr,
        )
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        print(f"[parse] 未找到配置文件：{path}", file=sys.stderr)
    except Exception as exc:
        print(f"[parse] 读取配置文件失败：{path} ({exc})", file=sys.stderr)
    return {}


def channel_display_name(channel: str, channels_path: str) -> str:
    data = load_yaml(channels_path)
    channels = data.get("channels") if isinstance(data, dict) else None
    if isinstance(channels, dict):
        cfg = channels.get(channel)
        if isinstance(cfg, dict) and cfg.get("displayName"):
            return str(cfg["displayName"])
    return channel


# ---------------------------------------------------------------------------
# 归一化
# ---------------------------------------------------------------------------
def build_skeleton():
    return {
        "meta": {
            "channel": "",
            "channelName": "",
            "source": "",
            "capturedAt": "",
            "protocolNote": "",
            "completeness": {},
            "missingFields": [],
        },
        "role": {k: (0 if k in ROLE_NUM_FIELDS else "") for k in ROLE_REQUIRED + ROLE_OPTIONAL},
        "currencies": {k: 0 for k in CURRENCY_REQUIRED + CURRENCY_OPTIONAL},
        "blueprints": [],
    }


def _coerce_blueprint_scalar(field: str, value):
    if field in BLUEPRINT_BOOL_FIELDS:
        return to_bool(value)
    if field in BLUEPRINT_NUM_FIELDS:
        return to_int(value)
    return to_str(value)


def _build_nested(items, field_map, defaults, numeric_fields, bool_fields):
    rows = []
    for obj in items:
        row = {}
        for mkey, default in defaults.items():
            src = field_map.get(mkey, "")
            found, val = extract(obj, src) if src else (False, None)
            if not found:
                row[mkey] = default
                continue
            if mkey in bool_fields:
                row[mkey] = to_bool(val, default)
            elif mkey in numeric_fields:
                row[mkey] = to_int(val, default)
            else:
                row[mkey] = to_str(val, default)
        rows.append(row)
    return rows


def normalize(source_data: dict, mapping: dict, channel: str, channels_path: str,
              source: str, captured_at: str):
    out = build_skeleton()
    missing = set()

    map_cfg = mapping.get("map") if isinstance(mapping.get("map"), dict) else {}

    # ---- meta ----
    out["meta"]["channel"] = channel or "unknown"
    out["meta"]["channelName"] = channel_display_name(out["meta"]["channel"], channels_path) \
        if channel else ""
    out["meta"]["source"] = source
    out["meta"]["capturedAt"] = captured_at
    out["meta"]["protocolNote"] = (
        "由 parse.py 依据 mapping.yaml 归一化；未配置字段见 missingFields（待用户抓包确认）"
    )

    # ---- role / currencies ----
    for model_path, src_path in map_cfg.items():
        if not isinstance(model_path, str):
            continue
        if model_path.startswith("meta."):
            continue  # meta 由工具生成（映射保留但此处不覆盖渠道信息）
        if not (model_path.startswith("role.") or model_path.startswith("currencies.")):
            continue
        section, field = model_path.split(".", 1)
        if section == "role" and field not in out["role"]:
            continue
        if section == "currencies" and field not in out["currencies"]:
            continue
        found, value = extract(source_data, str(src_path)) if src_path else (False, None)
        if not found:
            missing.add(model_path)
            continue
        if section == "role":
            out["role"][field] = to_int(value) if field in ROLE_NUM_FIELDS else to_str(value)
        else:
            out["currencies"][field] = to_int(value)

    # ---- blueprints ----
    bp_cfg = mapping.get("blueprints") if isinstance(mapping.get("blueprints"), dict) else {}
    bp_root = bp_cfg.get("root", "") if isinstance(bp_cfg, dict) else ""
    fields = bp_cfg.get("fields") if isinstance(bp_cfg.get("fields"), dict) else {}

    scalar_fields = {}
    modules_cfg = {"root": "", "fields": {}}
    skills_cfg = {"root": "", "fields": {}}
    for key, val in fields.items():
        if not isinstance(key, str):
            continue
        if key == "modules.root":
            modules_cfg["root"] = val
        elif key.startswith("modules.fields."):
            modules_cfg["fields"][key[len("modules.fields."):]] = val
        elif key == "skills.root":
            skills_cfg["root"] = val
        elif key.startswith("skills.fields."):
            skills_cfg["fields"][key[len("skills.fields."):]] = val
        else:
            scalar_fields[key] = val

    bp_items = []
    root_found, root_value = extract(source_data, str(bp_root)) if bp_root else (False, None)
    if root_found and isinstance(root_value, list):
        bp_items = [x for x in root_value if isinstance(x, dict)]
    elif root_found and root_value is not None:
        # 找到但不是数组：记录并退化为空数组
        missing.add("blueprints")
    else:
        missing.add("blueprints")

    built = []
    for obj in bp_items:
        bp = {}
        for field, default in [(f, "" if f not in BLUEPRINT_NUM_FIELDS else 0)
                               for f in BLUEPRINT_STR_FIELDS]:
            src = scalar_fields.get(field, "")
            found, val = extract(obj, str(src)) if src else (False, None)
            if not found:
                bp[field] = default
                missing.add(f"blueprints[].{field}")
            else:
                bp[field] = _coerce_blueprint_scalar(field, val)
        for field in BLUEPRINT_BOOL_FIELDS + BLUEPRINT_NUM_FIELDS:
            src = scalar_fields.get(field, "")
            found, val = extract(obj, str(src)) if src else (False, None)
            if not found:
                bp[field] = False if field in BLUEPRINT_BOOL_FIELDS else 0
                missing.add(f"blueprints[].{field}")
            else:
                bp[field] = _coerce_blueprint_scalar(field, val)

        # 嵌套：modules
        mod_root = modules_cfg["root"]
        m_found, m_val = extract(obj, str(mod_root)) if mod_root else (False, None)
        if m_found and isinstance(m_val, list):
            bp["modules"] = _build_nested(
                [x for x in m_val if isinstance(x, dict)],
                modules_cfg["fields"], MODULE_FIELDS,
                numeric_fields=set(), bool_fields=MODULE_BOOL_FIELDS,
            )
        else:
            bp["modules"] = []
            missing.add("blueprints[].modules")

        # 嵌套：skills
        s_root = skills_cfg["root"]
        s_found, s_val = extract(obj, str(s_root)) if s_root else (False, None)
        if s_found and isinstance(s_val, list):
            bp["skills"] = _build_nested(
                [x for x in s_val if isinstance(x, dict)],
                skills_cfg["fields"], SKILL_FIELDS,
                numeric_fields=SKILL_NUM_FIELDS, bool_fields=set(),
            )
        else:
            bp["skills"] = []
            missing.add("blueprints[].skills")

        built.append(bp)
    out["blueprints"] = built

    # ---- completeness ----
    # role：uid/nickname/serverName 非空且 level 有值（>0）视为完整
    role_ok = (
        all(out["role"].get(f) not in ("", None) for f in ["uid", "nickname", "serverName"])
        and "role.level" not in missing
        and out["role"].get("level", 0) > 0
    )
    currencies_ok = all(
        (f"currencies.{f}" not in missing) for f in CURRENCY_REQUIRED
    )
    blueprints_ok = len(out["blueprints"]) > 0
    points_ok = any(
        bp.get("pointsTotal", 0) > 0 or bp.get("pointsAllocated", 0) > 0
        for bp in out["blueprints"]
    )
    modules_ok = any(bp.get("modules") for bp in out["blueprints"])
    skills_ok = any(bp.get("skills") for bp in out["blueprints"])

    out["meta"]["completeness"] = {
        "role": bool(role_ok),
        "currencies": bool(currencies_ok),
        "blueprints": bool(blueprints_ok),
        "points": bool(points_ok),
        "modules": bool(modules_ok),
        "skills": bool(skills_ok),
    }
    # 缺省可选字段也计入 missingFields，便于前端提示"可手动补录"
    for f in ROLE_OPTIONAL:
        if out["role"].get(f) in ("", None) and f"role.{f}" not in map_cfg:
            missing.add(f"role.{f}")
    for f in CURRENCY_OPTIONAL:
        if f"currencies.{f}" not in map_cfg:
            missing.add(f"currencies.{f}")

    out["meta"]["missingFields"] = sorted(missing)
    return out


# ---------------------------------------------------------------------------
# 校验
# ---------------------------------------------------------------------------
def _is_int(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def validate_output(data) -> list:
    errors = []
    if not isinstance(data, dict):
        return ["根节点必须是 JSON 对象"]

    meta = data.get("meta")
    if not isinstance(meta, dict):
        errors.append("meta 缺失或类型错误")
    else:
        for key in ("channel", "channelName", "source", "capturedAt"):
            if not isinstance(meta.get(key), str):
                errors.append(f"meta.{key} 缺失或非字符串")
        if not isinstance(meta.get("completeness"), dict):
            errors.append("meta.completeness 缺失或非对象")
        if not isinstance(meta.get("missingFields"), list):
            errors.append("meta.missingFields 缺失或非数组")

    role = data.get("role")
    if not isinstance(role, dict):
        errors.append("role 缺失或类型错误")
    else:
        for key in ROLE_REQUIRED:
            if key in ROLE_NUM_FIELDS:
                if not _is_int(role.get(key)):
                    errors.append(f"role.{key} 缺失或非整数")
            elif not isinstance(role.get(key), str):
                errors.append(f"role.{key} 缺失或非字符串")
        for key in ROLE_OPTIONAL:
            if key in role and role[key] is not None:
                if key in ROLE_NUM_FIELDS and not _is_int(role[key]):
                    errors.append(f"role.{key} 应为整数")
                if key not in ROLE_NUM_FIELDS and not isinstance(role[key], str):
                    errors.append(f"role.{key} 应为字符串")

    currencies = data.get("currencies")
    if not isinstance(currencies, dict):
        errors.append("currencies 缺失或类型错误")
    else:
        for key in CURRENCY_REQUIRED:
            if not _is_int(currencies.get(key)):
                errors.append(f"currencies.{key} 缺失或非整数")
        if "blueprintPoints" in currencies and not _is_int(currencies["blueprintPoints"]):
            errors.append("currencies.blueprintPoints 应为整数")

    blueprints = data.get("blueprints")
    if not isinstance(blueprints, list):
        errors.append("blueprints 缺失或非数组")
    else:
        for i, bp in enumerate(blueprints):
            prefix = f"blueprints[{i}]"
            if not isinstance(bp, dict):
                errors.append(f"{prefix} 应为对象")
                continue
            for key in ["id", "name", "shipClass", "rarity", "subModel", "defaultPosition"]:
                if not isinstance(bp.get(key), str):
                    errors.append(f"{prefix}.{key} 缺失或非字符串")
            for key in BLUEPRINT_BOOL_FIELDS:
                if not isinstance(bp.get(key), bool):
                    errors.append(f"{prefix}.{key} 缺失或非布尔")
            for key in BLUEPRINT_NUM_FIELDS:
                if not _is_int(bp.get(key)):
                    errors.append(f"{prefix}.{key} 缺失或非整数")
            if bp.get("defaultPosition") not in POSITION_ENUM:
                errors.append(
                    f"{prefix}.defaultPosition 取值应为 {POSITION_ENUM} 之一"
                )
            if not isinstance(bp.get("modules"), list):
                errors.append(f"{prefix}.modules 缺失或非数组")
            else:
                for j, mod in enumerate(bp["modules"]):
                    mp = f"{prefix}.modules[{j}]"
                    if not isinstance(mod, dict):
                        errors.append(f"{mp} 应为对象")
                        continue
                    if not isinstance(mod.get("slot"), str) or not isinstance(mod.get("name"), str):
                        errors.append(f"{mp} 需含字符串 slot/name")
                    if not isinstance(mod.get("unlocked"), bool):
                        errors.append(f"{mp}.unlocked 应为布尔")
            if not isinstance(bp.get("skills"), list):
                errors.append(f"{prefix}.skills 缺失或非数组")
            else:
                for j, sk in enumerate(bp["skills"]):
                    sp = f"{prefix}.skills[{j}]"
                    if not isinstance(sk, dict):
                        errors.append(f"{sp} 应为对象")
                        continue
                    if not isinstance(sk.get("system"), str) or not isinstance(sk.get("name"), str):
                        errors.append(f"{sp} 需含字符串 system/name")
                    if not _is_int(sk.get("level")) or not _is_int(sk.get("max")):
                        errors.append(f"{sp}.level/max 应为整数")
    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _default_captured_at() -> str:
    return datetime.now(_CST).isoformat(timespec="seconds")


def write_out(data, out_path):
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if out_path:
        parent = os.path.dirname(os.path.abspath(out_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"[parse] 已写出：{out_path}")
    else:
        print(text)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="parse.py",
        description="按 mapping.yaml 把抓包响应归一化为标准角色数据模型（见 shared/data-model.md）。",
        epilog="示例：python3 parse.py --from-sample --out out/character.json --validate",
    )
    parser.add_argument("--input", help="原始响应 JSON 文件路径（抓包得到的响应体）")
    parser.add_argument(
        "--from-sample", nargs="?", const=_DEFAULT_SAMPLE, default=None,
        metavar="PATH",
        help="原样读取样例数据并输出（默认 ../shared/character.sample.json），用于无真实数据联调",
    )
    parser.add_argument("--mapping", default=_DEFAULT_MAPPING, help="字段映射文件（默认 ./mapping.yaml）")
    parser.add_argument("--channels", default=_DEFAULT_CHANNELS, help="渠道配置（默认 ./channels.yaml）")
    parser.add_argument(
        "--channel", default="", help="渠道标识（如 official / bili），用于 meta.channel/channelName",
    )
    parser.add_argument(
        "--source", default="mitmproxy",
        help="meta.source 取值（默认 mitmproxy；样例模式固定为 sample）",
    )
    parser.add_argument("--captured-at", default="", help="meta.capturedAt（ISO8601，默认当前时间）")
    parser.add_argument("--out", default="", help="输出文件路径（省略则打印到 stdout）")
    parser.add_argument(
        "--validate", action="store_true",
        help="对输出结果做结构校验（符合共享模型必填结构）",
    )
    args = parser.parse_args(argv)

    if not args.input and args.from_sample is None:
        parser.error("请提供 --input <response.json> 或 --from-sample [PATH]")

    # ---- 样例模式：原样输出，仅便于校验/联调 ----
    if args.from_sample is not None:
        sample_path = args.from_sample
        if not os.path.exists(sample_path):
            print(f"[parse] 样例文件不存在：{sample_path}", file=sys.stderr)
            return 1
        try:
            with open(sample_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:
            print(f"[parse] 样例文件解析失败：{exc}", file=sys.stderr)
            return 1
        print(f"[parse] 样例模式（原样输出）：{sample_path}")
    else:
        if not os.path.exists(args.input):
            print(f"[parse] 输入文件不存在：{args.input}", file=sys.stderr)
            return 1
        try:
            with open(args.input, "r", encoding="utf-8") as fh:
                source_data = json.load(fh)
        except Exception as exc:
            print(f"[parse] 输入文件不是合法 JSON：{exc}", file=sys.stderr)
            return 1
        mapping = load_yaml(args.mapping)
        if not mapping:
            print(
                "[parse] 映射为空或读取失败，将输出全空骨架（所有 completeness=false）。",
                file=sys.stderr,
            )
        data = normalize(
            source_data,
            mapping,
            channel=args.channel,
            channels_path=args.channels,
            source=args.source or "mitmproxy",
            captured_at=args.captured_at or _default_captured_at(),
        )

    write_out(data, args.out)

    if args.validate:
        errors = validate_output(data)
        if errors:
            print("[validate] 校验未通过，问题如下：", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            return 1
        print("[validate] 校验通过：结构符合共享数据模型（shared/data-model.md）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
