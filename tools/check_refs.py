#!/usr/bin/env python3
"""novel-to-comic 全项目「文档/脚本里引用的文件路径」存在性校验

用途：目录结构改过之后（挪目录、改文件名、清旧文件），文档里的路径引用极易失效，
      而失效的锁脸挂图路径会直接导致出图用错参考图。交付/交接前跑一遍。

用法：
    python3 tools/check_refs.py                    # 扫描全仓库
    python3 tools/check_refs.py <子目录>            # 只扫指定子目录
    python3 tools/check_refs.py -v                 # 列出每处引用的来源与行号
    python3 tools/check_refs.py --ext .py          # 只扫指定扩展名的载体文件

退出码：0 = 全部引用有效；1 = 存在失效引用

判定规则：
  - 载体文件：.md / .mdc / .py / .txt（跳过 .git、__pycache__、_分件_* 等）
  - 被检引用：形如 `某顶层目录/.../文件名.扩展名` 的仓库相对路径
  - URL（http/https 链接）先整段剔除，避免把外链当本地路径
  - 顶层目录白名单 = 仓库内实际存在的顶层目录，避免把普通斜杠文本误判为路径
  - 历史日志（memory/YYYY-MM-DD.md）跳过；前瞻引用走白名单
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CARRIER_EXTS_DEFAULT = {".md", ".mdc", ".py", ".txt"}
TARGET_EXTS = "png|jpe?g|webp|mp4|md|mdc|py|json|txt"

SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules"}

# 历史日志（memory/YYYY-MM-DD.md）是 append-only 的历史记录，
# 里面写的是「当时」的路径，随目录结构变化而失效属正常，不参与校验。
# 但 MEMORY.md（现行约定）要查。
DAILY_LOG = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")

# 占位符路径（模板写法），不是真实引用
PLACEHOLDER = re.compile(r"\.\.\.|<|>|(?<![A-Za-z])(?:NN|XX|YY|ZZ)(?![A-Za-z])")

# 把路径从正文里切出来的分隔符
SPLIT_CHARS = re.compile(r"[\s\"'`()\[\]{}<>|（）「」『』【】，,;；:：*]")
# 先剔除 URL
URL_RE = re.compile(r"https?://\S+")
# 候选路径：含 `/`、以目标扩展名结尾
CANDIDATE = re.compile(rf"[A-Za-z0-9_\u4e00-\u9fff][A-Za-z0-9_\u4e00-\u9fff./\-]*\.(?:{TARGET_EXTS})")


def top_level_names() -> set[str]:
    return {p.name for p in ROOT.iterdir() if p.is_dir()}


def is_skipped(path: Path) -> bool:
    try:
        parts = path.relative_to(ROOT).parts
    except ValueError:
        return False
    if any(p in SKIP_DIRS or p.startswith("_分件_") for p in parts):
        return True
    # 跳过历史日志（保留 MEMORY.md）
    if "memory" in parts and DAILY_LOG.match(path.name):
        return True
    return False


def iter_carriers(targets: list[Path], exts: set[str]):
    for target in targets:
        if target.is_file():
            if target.suffix.lower() in exts:
                yield target
            continue
        for p in sorted(target.rglob("*")):
            if p.is_file() and p.suffix.lower() in exts and not is_skipped(p):
                yield p


def collect(carriers, tl: set[str]):
    """返回 [(raw, carrier, lineno)]"""
    found: list[tuple[str, Path, int]] = []
    for carrier in carriers:
        try:
            text = carrier.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = carrier.relative_to(ROOT)
        for lineno, line in enumerate(text.splitlines(), 1):
            line = URL_RE.sub(" ", line)          # 剔除外链
            for token in SPLIT_CHARS.split(line):
                for m in CANDIDATE.finditer(token):
                    raw = m.group(0)
                    # 必须是仓库相对路径：不以 / ./ ../ 开头，且首段是真实顶层目录
                    if raw.startswith(("/", "./", "../")):
                        continue
                    if "/" not in raw:
                        continue
                    if raw.split("/")[0] not in tl:
                        continue
                    if PLACEHOLDER.search(raw):
                        continue
                    found.append((raw, rel, lineno))
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description="校验文档/脚本里的文件路径引用是否有效")
    ap.add_argument("paths", nargs="*", help="要扫描的目录或文件（默认全仓库）")
    ap.add_argument("-v", "--verbose", action="store_true", help="列出每处引用的来源与行号")
    ap.add_argument("--ext", action="append", default=None,
                    help="只扫描该扩展名的载体文件，可重复，如 --ext .py")
    args = ap.parse_args()

    exts = ({e if e.startswith(".") else "." + e for e in args.ext}
            if args.ext else CARRIER_EXTS_DEFAULT)
    targets = [Path(p).resolve() if Path(p).is_absolute() else (ROOT / p).resolve()
               for p in (args.paths or [ROOT])]

    refs = collect(iter_carriers(targets, exts), top_level_names())

    # 前瞻引用白名单：明确「计划中、尚未创建」的文件，不算失效
    forward_file = ROOT / "tools" / "check_refs_forward.txt"
    if not forward_file.exists() and forward_file.parent.is_dir():
        # 首次运行自动落一个空白模板——否则本脚本帮助文本里提到的这个路径
        # 会被自己判成失效引用，新项目一上来就误报
        forward_file.write_text(
            "# check_refs.py 前瞻引用白名单\n"
            "#\n"
            "# 用法：每行写一个「仓库相对路径」——该文件确实被文档引用，但计划中、尚未创建，\n"
            "#       因此不算断链。空行与 # 之后的内容忽略。\n"
            "# 注意：只放真的还没到创建时点的文件。已过期的引用应该直接去改文档。\n",
            encoding="utf-8",
        )
        print("· 已创建 tools/check_refs_forward.txt（空白白名单模板）\n")

    forward: set[str] = set()
    if forward_file.exists():
        for line in forward_file.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                forward.add(line)

    missing = [(raw, src, ln) for raw, src, ln in refs
               if not (ROOT / raw).exists() and raw not in forward]

    if missing:
        print(f"✗ {len(missing)} 处失效引用 / 共检查 {len(refs)} 处：\n")
        for raw, src, ln in missing:
            print(f"  缺失  {raw}")
            print(f"        由 {src}:{ln} 引用")
        print("\n修法：把引用改指向新路径；若文件是被误删的，用系统 trash 可恢复；")
        print("      若确属「计划中尚未创建」，加进 tools/check_refs_forward.txt。")
        return 1

    nfwd = sum(1 for raw, _, _ in refs if raw in forward)
    print(f"✓ 全部引用有效：{len(refs)} 处，0 缺失"
          + (f"（其中前瞻引用 {nfwd} 处，已在 check_refs_forward.txt 声明）" if nfwd else ""))
    if args.verbose:
        by_src: dict[Path, int] = {}
        for _, src, _ in refs:
            by_src[src] = by_src.get(src, 0) + 1
        for src, n in sorted(by_src.items(), key=lambda kv: -kv[1]):
            print(f"    {n:>4} 处  {src}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
