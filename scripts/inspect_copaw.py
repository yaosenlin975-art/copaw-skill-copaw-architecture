#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CoPaw 构造自检脚本（默认只读）

- 默认：仅输出到 stdout（Markdown + JSON 摘要区块）
- 写入文件：必须显式开启 --write，并遵守：
  1) 写入前校验（JSON 必须可解析）
  2) 原文件同目录备份：<file>.bak.<timestamp>
  3) 临时文件 + 原子替换（避免写一半损坏）

注意：
- 默认会对常见敏感字段做脱敏（token/secret/api_key/password 等 key 名匹配）。
  这是额外安全保护，不改变你与用户约定的"写入边界"。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


SENSITIVE_KEY_RE = re.compile(
    r"(token|secret|api[_-]?key|password|access[_-]?token|private[_-]?key|client[_-]?secret)",
    re.IGNORECASE,
)


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def safe_read_text(path: Path, max_bytes: int = 256_000) -> str:
    # 只读小片段，避免意外读取超大文件
    with path.open("rb") as f:
        data = f.read(max_bytes)
    return data.decode("utf-8", errors="replace")


def safe_read_json(path: Path, max_bytes: int = 1_000_000) -> Any:
    text = safe_read_text(path, max_bytes=max_bytes)
    return json.loads(text)


def redact(obj: Any) -> Any:
    """对 dict 中疑似敏感字段脱敏（递归）。"""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if SENSITIVE_KEY_RE.search(str(k)):
                out[k] = "***REDACTED***"
            else:
                out[k] = redact(v)
        return out
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj


def list_dir(path: Path) -> List[Dict[str, Any]]:
    if not path.exists() or not path.is_dir():
        return []
    items: List[Dict[str, Any]] = []
    for p in sorted(path.iterdir(), key=lambda x: x.name):
        try:
            st = p.stat()
            items.append(
                {
                    "name": p.name,
                    "type": "dir" if p.is_dir() else "file",
                    "size": st.st_size,
                    "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
                }
            )
        except FileNotFoundError:
            continue
    return items


def tree(path: Path, max_depth: int = 3, _depth: int = 0) -> List[str]:
    """生成简易树（只列目录名与文件名，不读文件内容）。"""
    if not path.exists():
        return [f"{path} (missing)"]
    lines: List[str] = []
    prefix = "  " * _depth
    name = path.name if _depth > 0 else str(path)
    lines.append(f"{prefix}- {name}/" if path.is_dir() else f"{prefix}- {name}")
    if not path.is_dir() or _depth >= max_depth:
        return lines
    try:
        children = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
    except PermissionError:
        lines.append(f"{prefix}  - <permission denied>")
        return lines
    for child in children:
        lines.extend(tree(child, max_depth=max_depth, _depth=_depth + 1))
    return lines


def atomic_write_bytes(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + f".tmp.{os.getpid()}")
    with tmp.open("wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, target)


def backup_same_dir(target: Path) -> Optional[Path]:
    if not target.exists():
        return None
    ts = utc_ts()
    bak = target.with_name(target.name + f".bak.{ts}")
    shutil.copy2(target, bak)
    return bak


def validate_json_bytes(data: bytes) -> None:
    # 必须是合法 JSON
    json.loads(data.decode("utf-8"))


def validate_md_bytes(data: bytes) -> None:
    text = data.decode("utf-8", errors="replace").strip()
    if not text:
        raise ValueError("Markdown 为空")
    # 简单结构校验：必须包含标题
    if not text.startswith("# "):
        raise ValueError("Markdown 缺少顶层标题（应以 '# ' 开头）")


def summarize_workspace(ws_dir: Path, redact_secrets: bool) -> Dict[str, Any]:
    out: Dict[str, Any] = {"name": ws_dir.name, "path": str(ws_dir)}
    agent_json = ws_dir / "agent.json"
    skill_json = ws_dir / "skill.json"

    if agent_json.exists():
        try:
            agent = safe_read_json(agent_json)
            agent = redact(agent) if redact_secrets else agent
            out["agent"] = {
                "id": agent.get("id"),
                "name": agent.get("name"),
                "description": agent.get("description"),
            }
            # 仅输出 channel 是否启用的概览，不输出 token 等字段
            channels = agent.get("channels", {})
            enabled = []
            for ch_name, ch_cfg in channels.items():
                if isinstance(ch_cfg, dict) and ch_cfg.get("enabled") is True:
                    enabled.append(ch_name)
            out["channels_enabled"] = enabled
        except Exception as e:
            out["agent_error"] = f"读取 agent.json 失败：{e}"
    else:
        out["agent_missing"] = True

    if skill_json.exists():
        try:
            skills = safe_read_json(skill_json)
            skills = redact(skills) if redact_secrets else skills
            # 兼容：skills 字段可能存在于 skills 下
            skills_map = skills.get("skills", {}) if isinstance(skills, dict) else {}
            enabled_skills = []
            for s_name, s_cfg in skills_map.items():
                if isinstance(s_cfg, dict) and s_cfg.get("enabled") is True:
                    enabled_skills.append(s_name)
            out["skills_enabled"] = sorted(enabled_skills)
        except Exception as e:
            out["skill_error"] = f"读取 skill.json 失败：{e}"
    else:
        out["skill_missing"] = True

    ws_skills_dir = ws_dir / "skills"
    if ws_skills_dir.exists() and ws_skills_dir.is_dir():
        out["skills_dir"] = [x.name for x in sorted(ws_skills_dir.iterdir()) if x.is_dir()]

    # 关键模板文件存在性
    key_files = ["AGENTS.md", "MEMORY.md", "PROFILE.md", "SOUL.md", "BOOTSTRAP.md", "HEARTBEAT.md"]
    out["key_files"] = {fn: (ws_dir / fn).exists() for fn in key_files}
    return out


def build_report(copaw_dir: Path, copaw_secret_dir: Path, redact_secrets: bool) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "paths": {"copaw_dir": str(copaw_dir), "copaw_secret_dir": str(copaw_secret_dir)},
        "exists": {"copaw_dir": copaw_dir.exists(), "copaw_secret_dir": copaw_secret_dir.exists()},
    }

    # ~/.copaw 顶层
    if copaw_dir.exists():
        report["copaw_dir_entries"] = list_dir(copaw_dir)
        report["copaw_tree"] = tree(copaw_dir, max_depth=2)

        # skill_pool
        sp = copaw_dir / "skill_pool"
        report["skill_pool"] = {
            "exists": sp.exists(),
            "entries": list_dir(sp),
        }
        sp_manifest = sp / "skill.json"
        if sp_manifest.exists():
            try:
                spj = safe_read_json(sp_manifest)
                spj = redact(spj) if redact_secrets else spj
                # 只抽取 skill 名称与 description
                skills = spj.get("skills", {}) if isinstance(spj, dict) else {}
                report["skill_pool"]["skills"] = sorted(list(skills.keys()))
            except Exception as e:
                report["skill_pool"]["manifest_error"] = str(e)

        # workspaces
        ws_root = copaw_dir / "workspaces"
        workspaces: List[Dict[str, Any]] = []
        if ws_root.exists() and ws_root.is_dir():
            for ws_dir in sorted(ws_root.iterdir(), key=lambda p: p.name):
                if ws_dir.is_dir():
                    workspaces.append(summarize_workspace(ws_dir, redact_secrets=redact_secrets))
        report["workspaces"] = workspaces

        # global key files
        report["global_files"] = {
            "config.json": (copaw_dir / "config.json").exists(),
            "HEARTBEAT.md": (copaw_dir / "HEARTBEAT.md").exists(),
        }

    # ~/.copaw.secret（只列结构，不读内容）
    if copaw_secret_dir.exists():
        report["copaw_secret_tree"] = tree(copaw_secret_dir, max_depth=3)
        providers = copaw_secret_dir / "providers"
        report["secret_providers"] = {
            "exists": providers.exists(),
            "entries": list_dir(providers),
        }
        if providers.exists():
            # builtin/custom 下只列文件名与大小
            for sub in ["builtin", "custom"]:
                p = providers / sub
                report["secret_providers"][sub] = {"exists": p.exists(), "entries": list_dir(p)}

    return report


def render_markdown(report: Dict[str, Any]) -> str:
    paths = report.get("paths", {})
    exists = report.get("exists", {})
    lines: List[str] = []
    lines.append("# CoPaw 构造自检报告")
    lines.append("")
    lines.append(f"- 生成时间（UTC）：`{report.get('generated_at_utc')}`")
    lines.append(f"- copaw_dir：`{paths.get('copaw_dir')}`（exists={exists.get('copaw_dir')}）")
    lines.append(f"- copaw_secret_dir：`{paths.get('copaw_secret_dir')}`（exists={exists.get('copaw_secret_dir')}）")
    lines.append("")

    if exists.get("copaw_dir"):
        lines.append("## ~/.copaw 概览（tree，深度 2）")
        lines.append("```text")
        for l in report.get("copaw_tree", []) or []:
            lines.append(l)
        lines.append("```")
        lines.append("")

        sp = report.get("skill_pool", {}) or {}
        lines.append("## skill_pool")
        lines.append(f"- exists: `{sp.get('exists')}`")
        skills = sp.get("skills")
        if isinstance(skills, list):
            lines.append(f"- skills: {len(skills)}")
            lines.append("")
            for s in skills:
                lines.append(f"  - `{s}`")
        lines.append("")

        lines.append("## workspaces")
        wss = report.get("workspaces", []) or []
        lines.append(f"- count: `{len(wss)}`")
        lines.append("")
        for ws in wss:
            lines.append(f"### workspace: `{ws.get('name')}`")
            agent = ws.get("agent", {}) or {}
            if agent:
                lines.append(f"- agent.id: `{agent.get('id')}`")
                lines.append(f"- agent.name: `{agent.get('name')}`")
            if "channels_enabled" in ws:
                lines.append(f"- channels_enabled: `{ws.get('channels_enabled')}`")
            if "skills_enabled" in ws:
                lines.append(f"- skills_enabled: `{ws.get('skills_enabled')}`")
            if "skills_dir" in ws:
                lines.append(f"- skills_dir: `{ws.get('skills_dir')}`")
            kf = ws.get("key_files", {}) or {}
            if kf:
                lines.append("- key_files:")
                for fn, ok in kf.items():
                    lines.append(f"  - {fn}: {ok}")
            if "agent_error" in ws:
                lines.append(f"- agent_error: {ws.get('agent_error')}")
            if "skill_error" in ws:
                lines.append(f"- skill_error: {ws.get('skill_error')}")
            lines.append("")

    if exists.get("copaw_secret_dir"):
        lines.append("## ~/.copaw.secret 概览（tree，深度 3，仅结构）")
        lines.append("```text")
        for l in report.get("copaw_secret_tree", []) or []:
            lines.append(l)
        lines.append("```")
        lines.append("")

    lines.append("## JSON 摘要（供程序化使用）")
    lines.append("```json")
    lines.append(json.dumps(report, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="CoPaw 构造自检（默认只读）")
    p.add_argument("--copaw-dir", default=str(Path.home() / ".copaw"), help="CoPaw 工作目录（默认 ~/.copaw）")
    p.add_argument(
        "--copaw-secret-dir",
        default=str(Path.home() / ".copaw.secret"),
        help="CoPaw secret 目录（默认 ~/.copaw.secret）",
    )
    p.add_argument("--no-redact", action="store_true", help="关闭敏感字段脱敏（不推荐，可能泄露 token/secret）")

    # 写入输出（必须显式 --write）
    p.add_argument("--write", action="store_true", help="允许写入输出文件（必须先征得用户同意）")
    p.add_argument("--output-md", default="", help="将 Markdown 报告写入指定路径（需要 --write）")
    p.add_argument("--output-json", default="", help="将 JSON 摘要写入指定路径（需要 --write）")

    args = p.parse_args(argv)

    copaw_dir = Path(args.copaw_dir).expanduser()
    copaw_secret_dir = Path(args.copaw_secret_dir).expanduser()
    redact_secrets = not args.no_redact

    report = build_report(copaw_dir, copaw_secret_dir, redact_secrets=redact_secrets)
    md = render_markdown(report)

    # stdout 永远输出
    sys.stdout.write(md)
    if not md.endswith("\n"):
        sys.stdout.write("\n")

    # 可选写入
    wants_write = bool(args.output_md or args.output_json)
    if wants_write and not args.write:
        sys.stderr.write("检测到 --output-* 参数，但未提供 --write；为安全起见拒绝写入。\n")
        return 2

    if args.write:
        # Markdown
        if args.output_md:
            out_md = Path(args.output_md).expanduser()
            data = md.encode("utf-8")
            validate_md_bytes(data)
            backup_same_dir(out_md)
            atomic_write_bytes(out_md, data)
            # 写后再校验
            validate_md_bytes(out_md.read_bytes())

        # JSON
        if args.output_json:
            out_json = Path(args.output_json).expanduser()
            data = json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8")
            validate_json_bytes(data)
            backup_same_dir(out_json)
            atomic_write_bytes(out_json, data)
            # 写后再校验
            validate_json_bytes(out_json.read_bytes())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
