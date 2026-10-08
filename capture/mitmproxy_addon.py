#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mitmproxy_addon.py —— 数据获取可行性验证 Demo 的采集端 addon（只读观察）

用途
----
在用户【本地电脑】上以 mitmproxy 加载本 addon，对手机/模拟器接入的流量做
「只读观察」，把命中的请求/响应落盘到 dump 目录，并维护 index.jsonl，
供后续 scan.py 扫描、定位承载角色数据的接口。

用法（详见 README.md）
--------------------
    # 方式一：命令行脚本模式（推荐先跑交互界面观察）
    mitmproxy -s mitmproxy_addon.py

    # 方式二：mitmdump 无界面模式
    mitmdump -s mitmproxy_addon.py

    # 通过 --set 传参（可选）
    mitmdump -s mitmproxy_addon.py \
        --set capture_dump_dir=./dump \
        --set capture_path_keywords=role,blueprint

    # 也可用环境变量传参（见下方 OPTION/ENV 说明）

安全与合规声明（务必阅读）
------------------------
- 本 addon 仅做【只读观察】：不修改任何请求/响应包、不重放、不注入、不代替玩家操作。
- 账号封禁风险由使用者自行承担；仅用于个人学习与研究。
- cookie / authorization 等敏感头默认脱敏（可用 --set capture_redact=false 关闭）。
- 真实域名/路径必须由用户抓包后确认；本文件不含任何写死的游戏域名。

设计要点
--------
- 对 mitmproxy 的导入做「延迟/安全」处理：未安装 mitmproxy 时 import 本文件不会崩溃
  （便于在本仓库内做语法检查 / --help，沙箱内未安装 mitmproxy）。
- 匹配规则来自 channels.yaml（也支持命令行/环境变量传入关键字）。
- 若规则为空，则记录【全部】流量，方便先"全量抓一遍"再筛选。
- 响应体会解压（gzip/br/deflate）后保存；二进制体只保存长度与前若干字节并标注。
"""

import gzip
import json
import os
import re
import sys
import time
import zlib
from datetime import datetime, timezone, timedelta

# --------------------------------------------------------------------------
# 延迟/安全导入 mitmproxy：未安装时不影响本文件被 import / 编译
# --------------------------------------------------------------------------
try:  # pragma: no cover - 依赖运行环境
    from mitmproxy import http  # noqa: F401  仅用于类型提示，实际按鸭子类型处理
except Exception:  # ImportError 或其它
    http = None  # type: ignore

try:  # pragma: no cover - 依赖运行环境
    from mitmproxy import ctx  # noqa: F401
except Exception:
    ctx = None  # type: ignore

# 本进程所在目录（用于定位默认 channels.yaml）
_HERE = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_CHANNELS = os.path.join(_HERE, "channels.yaml")

# 默认脱敏的敏感头（小写比较）
_SENSITIVE_HEADERS = {
    "cookie",
    "set-cookie",
    "authorization",
    "proxy-authorization",
    "x-token",
    "x-auth-token",
    "token",
    "sign",
    "signature",
}

# 文本类型判定（子串，小写）
_TEXTUAL_HINTS = (
    "application/json",
    "application/xml",
    "application/x-www-form-urlencoded",
    "application/javascript",
    "application/protobuf",  # 可能仍是二进制，下面再做 utf-8 兜底判断
    "text/",
    "json",
    "xml",
    "html",
    "javascript",
)

# 东八区（用于时间戳，便于用户阅读；原始 ts 同时保留 epoch）
_CST = timezone(timedelta(hours=8))


def _now_iso() -> str:
    return datetime.now(_CST).isoformat(timespec="seconds")


def _log(message: str) -> None:
    """统一日志输出：优先用 mitmproxy ctx.log，缺失时退化为 print 到 stderr。"""
    try:
        if ctx is not None:
            ctx.log.info(message)
            return
    except Exception:
        pass
    print("[lagrange-capture] " + message, file=sys.stderr)


def _split_keywords(value) -> list:
    """把 "a,b,c" 或 ['a','b'] 统一成去空白、非空的列表。"""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        items = list(value)
    else:
        items = str(value).split(",")
    return [str(x).strip() for x in items if str(x).strip()]


def _as_bool(value, default=False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "y", "on")


def _load_yaml(path: str):
    """安全读取 YAML；未安装 PyYAML 时返回空，不崩溃。"""
    try:
        import yaml  # 延迟导入
    except Exception:
        _log("未安装 PyYAML，无法读取 channels.yaml，将退化为仅使用关键字/全量模式。")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        _log(f"未找到渠道配置：{path}")
        return {}
    except Exception as exc:
        _log(f"解析渠道配置失败：{path} ({exc})")
        return {}


def _decode_body(raw: bytes, encoding: str) -> bytes:
    """
    解压响应体。mitmproxy 的 get_content() 通常已解码；
    这里再提供一层标准库兜底（gzip/deflate），brotli 依赖 mitmproxy 自带解码。
    """
    if not raw:
        return raw
    enc = (encoding or "").lower()
    try:
        if "gzip" in enc:
            return gzip.decompress(raw)
        if "deflate" in enc:
            try:
                return zlib.decompress(raw)
            except zlib.error:
                return zlib.decompress(raw, -zlib.MAX_WBITS)
    except Exception:
        return raw
    return raw


def _redact_headers(headers, enabled: bool) -> dict:
    """把 headers 转成普通 dict，必要时脱敏敏感头。"""
    out = {}
    try:
        items = headers.items() if hasattr(headers, "items") else dict(headers).items()
    except Exception:
        items = []
    for key, value in items:
        if enabled and str(key).lower() in _SENSITIVE_HEADERS:
            out[str(key)] = "<redacted>"
        else:
            out[str(key)] = str(value)
    return out


def _looks_textual(headers: dict, body: bytes) -> bool:
    ctype = ""
    for key, value in headers.items():
        if str(key).lower() == "content-type":
            ctype = str(value).lower()
            break
    if any(hint in ctype for hint in _TEXTUAL_HINTS):
        # protobuf 等仍可能就是二进制，需通过 utf-8 判定
        if "protobuf" in ctype:
            try:
                body.decode("utf-8")
                return True
            except Exception:
                return False
        return True
    # 无/未知 content-type：尝试 utf-8 判定
    if not body:
        return True
    try:
        body.decode("utf-8")
        return True
    except Exception:
        return False


def _safe_name(text: str, limit: int = 40) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text or "")
    text = text.strip("_")
    return text[:limit] or "root"


class LagrangeDumpAddon:
    """仅用于只读观察的落盘 addon。"""

    def __init__(self):
        self.dump_dir = "dump"
        self.channels_path = _DEFAULT_CHANNELS
        self.host_keywords = []
        self.path_keywords = []
        self.redact = True
        self.max_text_bytes = 2_000_000
        self.preview_bytes = 512
        self.save_all_when_empty = True
        self.channels = {}          # key -> {displayName, hostPatterns, pathKeywords, ...}
        self._counter = 0
        self._index_path = None
        self._ready = False

    # ------------------------------------------------------------------
    # mitmproxy addon 生命周期
    # ------------------------------------------------------------------
    def load(self, loader):
        # 注册可配置项（--set 可用）。类型用内建类型，避免 import mitmproxy.types。
        loader.add_option(
            "capture_dump_dir", str, "dump",
            "抓包落盘目录（默认 ./dump）",
        )
        loader.add_option(
            "capture_channels", str, _DEFAULT_CHANNELS,
            "渠道配置文件路径（默认脚本同目录 channels.yaml）",
        )
        loader.add_option(
            "capture_host_keywords", str, "",
            "额外 host 关键字，逗号分隔（与环境变量 CAPTURE_HOST_KEYWORDS 等价）",
        )
        loader.add_option(
            "capture_path_keywords", str, "",
            "额外 path 关键字，逗号分隔（与环境变量 CAPTURE_PATH_KEYWORDS 等价）",
        )
        loader.add_option(
            "capture_redact", bool, True,
            "是否脱敏 cookie/authorization 等敏感头（默认 true）",
        )
        loader.add_option(
            "capture_max_text_bytes", int, 2_000_000,
            "文本响应体最大保存字节数（超出截断并标注）",
        )
        loader.add_option(
            "capture_preview_bytes", int, 512,
            "二进制响应体预览保存字节数",
        )
        loader.add_option(
            "capture_save_all_when_empty", bool, True,
            "当所有匹配规则为空时，是否记录全部流量（默认 true）",
        )

    def running(self):
        self._apply_settings()
        self._log(
            f"落地目录={self.dump_dir} | 命中规则: host={self.host_keywords} "
            f"path={self.path_keywords} | 脱敏={self.redact} | "
            f"渠道数={len(self.channels)}"
        )
        if not self.host_keywords and not self.path_keywords:
            self._log(
                "当前未配置任何 host/path 匹配规则 —— 将记录全部流量（全量模式）；"
                "抓包后用 scan.py 筛选，再回填 channels.yaml。"
            )

    def _opt(self, name, default=None):
        try:
            if ctx is not None and hasattr(ctx, "options"):
                return getattr(ctx.options, name)
        except Exception:
            pass
        return default

    def _apply_settings(self):
        # 选项优先，其次环境变量
        self.dump_dir = str(
            self._opt("capture_dump_dir", os.environ.get("CAPTURE_DUMP_DIR", "dump"))
            or "dump"
        )
        self.channels_path = str(
            self._opt(
                "capture_channels",
                os.environ.get("CAPTURE_CHANNELS", _DEFAULT_CHANNELS),
            )
            or _DEFAULT_CHANNELS
        )
        self.redact = _as_bool(
            self._opt("capture_redact", os.environ.get("CAPTURE_REDACT", "true")),
            default=True,
        )
        try:
            self.max_text_bytes = int(
                self._opt(
                    "capture_max_text_bytes",
                    os.environ.get("CAPTURE_MAX_TEXT_BYTES", 2_000_000),
                )
            )
        except Exception:
            self.max_text_bytes = 2_000_000
        try:
            self.preview_bytes = int(
                self._opt(
                    "capture_preview_bytes",
                    os.environ.get("CAPTURE_PREVIEW_BYTES", 512),
                )
            )
        except Exception:
            self.preview_bytes = 512
        self.save_all_when_empty = _as_bool(
            self._opt(
                "capture_save_all_when_empty",
                os.environ.get("CAPTURE_SAVE_ALL_WHEN_EMPTY", "true"),
            ),
            default=True,
        )

        # 关键字：选项 + 环境变量 合并
        self.host_keywords = _split_keywords(self._opt("capture_host_keywords")) + \
            _split_keywords(os.environ.get("CAPTURE_HOST_KEYWORDS"))
        self.path_keywords = _split_keywords(self._opt("capture_path_keywords")) + \
            _split_keywords(os.environ.get("CAPTURE_PATH_KEYWORDS"))

        # 读取渠道配置
        self.channels = self._read_channels(self.channels_path)

        # 准备 dump 目录与 index 计数
        os.makedirs(self.dump_dir, exist_ok=True)
        self._index_path = os.path.join(self.dump_dir, "index.jsonl")
        self._counter = self._count_existing()
        self._ready = True

    def _read_channels(self, path: str) -> dict:
        data = _load_yaml(path)
        channels = data.get("channels") if isinstance(data, dict) else None
        if not isinstance(channels, dict):
            return {}
        parsed = {}
        for key, cfg in channels.items():
            if not isinstance(cfg, dict):
                continue
            parsed[str(key)] = {
                "displayName": str(cfg.get("displayName", key)),
                "hostPatterns": _split_keywords(cfg.get("hostPatterns")),
                "pathKeywords": _split_keywords(cfg.get("pathKeywords")),
                "excludeHostPatterns": _split_keywords(cfg.get("excludeHostPatterns")),
                "excludePathKeywords": _split_keywords(cfg.get("excludePathKeywords")),
                "loginNotes": str(cfg.get("loginNotes", "")),
            }
        return parsed

    def _count_existing(self) -> int:
        if not self._index_path or not os.path.exists(self._index_path):
            return 0
        count = 0
        try:
            with open(self._index_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        count += 1
        except Exception:
            # 退化为按文件数估算
            try:
                count = len(os.listdir(self.dump_dir))
            except Exception:
                count = 0
        return count

    # ------------------------------------------------------------------
    # 匹配
    # ------------------------------------------------------------------
    def _channel_for(self, host: str, path: str):
        """返回 (matched_channel_key_or_None, excluded_bool)。"""
        host_l = (host or "").lower()
        path_l = (path or "").lower()
        matched = None
        for key, cfg in self.channels.items():
            # 排除规则优先
            if any(p.lower() in host_l for p in cfg["excludeHostPatterns"]):
                return (None, True)
            if any(k.lower() in path_l for k in cfg["excludePathKeywords"]):
                return (None, True)
            hit = False
            if any(p.lower() in host_l for p in cfg["hostPatterns"]):
                hit = True
            if any(k.lower() in path_l for k in cfg["pathKeywords"]):
                hit = True
            if hit and matched is None:
                matched = key
        return (matched, False)

    def _should_capture(self, host: str, path: str):
        """返回 (capture: bool, channel: str|None)。"""
        channel, excluded = self._channel_for(host, path)
        if excluded and channel is None and self.channels:
            # 命中排除规则且非渠道命中
            if not (self.host_keywords or self.path_keywords):
                # 全量模式仍记录，但标注 excluded
                return (True, channel)
            return (False, None)

        host_l = (host or "").lower()
        path_l = (path or "").lower()

        has_rules = bool(
            self.host_keywords
            or self.path_keywords
            or any(
                cfg["hostPatterns"] or cfg["pathKeywords"]
                for cfg in self.channels.values()
            )
        )
        if not has_rules:
            # 规则为空 -> 记录全部
            return (True, channel)

        if channel is not None:
            return (True, channel)
        if any(k.lower() in host_l for k in self.host_keywords):
            return (True, channel)
        if any(k.lower() in path_l for k in self.path_keywords):
            return (True, channel)
        return (False, None)

    # ------------------------------------------------------------------
    # hooks
    # ------------------------------------------------------------------
    def request(self, flow):
        """请求到达时记录起始时间（只读，不修改 flow）。"""
        try:
            flow.metadata["lagrange_ts"] = time.time()
        except Exception:
            pass

    def response(self, flow):
        """响应到达时落盘（只读，不修改 flow）。"""
        if not self._ready:
            self._apply_settings()
        try:
            self._handle(flow)
        except Exception as exc:  # 保证单条异常不影响整体抓包
            _log(f"处理 flow 失败：{exc!r}")

    # ------------------------------------------------------------------
    # 落盘实现
    # ------------------------------------------------------------------
    def _handle(self, flow):
        req = flow.request
        resp = getattr(flow, "response", None)
        if resp is None:
            return

        host = getattr(req, "host", "") or ""
        path = getattr(req, "path", "") or ""
        should, channel = self._should_capture(host, path)
        if not should:
            return

        self._counter += 1
        fid = f"{self._counter:05d}"

        # 响应体：优先用 mitmproxy 已解码内容
        resp_raw = b""
        resp_encoding = ""
        try:
            resp_raw = resp.get_content() or b""
        except Exception:
            resp_raw = getattr(resp, "content", b"") or b""
        try:
            resp_encoding = str(resp.headers.get("content-encoding", "") or "")
        except Exception:
            resp_encoding = ""
        if resp_encoding and not resp_raw:
            resp_raw = _decode_body(resp_raw, resp_encoding)

        req_raw = b""
        try:
            req_raw = req.get_content() or b""
        except Exception:
            req_raw = getattr(req, "content", b"") or b""

        req_headers = _redact_headers(req.headers, self.redact)
        resp_headers = _redact_headers(resp.headers, self.redact)

        # 写请求体
        req_file = None
        if req_raw:
            req_file = f"{fid}.req.bin"
            self._write_bytes(os.path.join(self.dump_dir, req_file), req_raw)

        # 写响应体（区分文本/二进制）
        resp_file = None
        resp_binary = False
        resp_truncated = False
        resp_saved_bytes = 0
        if resp_raw:
            is_text = _looks_textual(resp_headers, resp_raw)
            if is_text:
                data = resp_raw
                resp_file = f"{fid}.resp.txt"
                if len(data) > self.max_text_bytes:
                    data = data[: self.max_text_bytes]
                    resp_truncated = True
                self._write_bytes(os.path.join(self.dump_dir, resp_file), data)
                resp_saved_bytes = len(data)
            else:
                resp_binary = True
                preview = resp_raw[: self.preview_bytes]
                resp_file = f"{fid}.resp.preview.bin"
                self._write_bytes(os.path.join(self.dump_dir, resp_file), preview)
                resp_saved_bytes = len(preview)
                resp_truncated = True

        # 判断文本响应是否为 JSON
        resp_is_json = False
        if resp_file and not resp_binary:
            try:
                text = resp_raw[: self.max_text_bytes].decode("utf-8").strip()
                if text[:1] in ("{", "["):
                    json.loads(text)
                    resp_is_json = True
            except Exception:
                resp_is_json = False

        entry = {
            "id": fid,
            "ts": _now_iso(),
            "epoch": round(
                float(getattr(flow, "metadata", {}).get("lagrange_ts", time.time())), 3
            ) if hasattr(flow, "metadata") else None,
            "channel": channel,
            "matched": channel is not None
            or bool(self.host_keywords or self.path_keywords),
            "method": getattr(req, "method", "") or "",
            "url": getattr(req, "pretty_url", "") or getattr(req, "url", "") or "",
            "host": host,
            "path": path,
            "status": int(getattr(resp, "status_code", 0) or 0),
            "content_type": resp_headers.get("Content-Type", "")
            or resp_headers.get("content-type", ""),
            "req_size": len(req_raw),
            "resp_size": len(resp_raw),
            "resp_is_json": resp_is_json,
            "resp_binary": resp_binary,
            "resp_truncated": resp_truncated,
            "resp_saved_bytes": resp_saved_bytes,
            "req_file": req_file,
            "resp_file": resp_file,
            "meta_file": f"{fid}.meta.json",
        }

        # 详细元数据（含 headers）
        meta = {
            "id": fid,
            "ts": entry["ts"],
            "channel": channel,
            "method": entry["method"],
            "url": entry["url"],
            "host": host,
            "path": path,
            "request_headers": req_headers,
            "response_headers": resp_headers,
            "status": entry["status"],
            "req_size": entry["req_size"],
            "resp_size": entry["resp_size"],
            "resp_is_json": resp_is_json,
            "resp_binary": resp_binary,
            "resp_truncated": resp_truncated,
            "redacted": self.redact,
            "note": "只读观察落盘；未修改/未重放任何流量",
        }
        with open(
            os.path.join(self.dump_dir, entry["meta_file"]), "w", encoding="utf-8"
        ) as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=2)

        # 追加 index.jsonl
        with open(self._index_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _write_bytes(self, path, data: bytes):
        with open(path, "wb") as fh:
            fh.write(data)


# mitmproxy 约定：模块级 addons 列表
addons = [LagrangeDumpAddon()]
