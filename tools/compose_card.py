#!/usr/bin/env python3
"""novel-to-comic 角色卡拼装脚本（参考实现）

本脚本是一个**参考实现**，展示如何把 5 张分件源图（主肖像、三视图、微表情、
服饰图鉴、装备图鉴）拼装成一张完整的写实人物卡。

**项目落地的写法**：每个项目的角色数、布局、色板都不一样，**建议你
复制这个文件到你的项目 `_工具/` 下**，按 `templates/character-card.md`
的配置定义你的角色字典，然后改 `compose_char_card()` 调用。

依赖：
    pip install Pillow

用法（参考）：
    python3 compose_card.py <角色名>
    # 角色字典 CHARS 在文件底部定义
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---- 配置 ----
ROOT = Path(__file__).resolve().parent.parent
FONT_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
]


def font(size: int) -> ImageFont.FreeTypeFont:
    """取字体（按候选链自动降级）"""
    for fp in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(fp, size)
        except OSError:
            continue
    raise RuntimeError("找不到可用中文字体")


def detect_figure_span(ref_img: Image.Image | None = None) -> tuple[int, int, int, int]:
    """动态检测人物垂直范围（用于生成身高刻度线）

    默认：返回中间 80% 区域。可以通过传入参考图动态采样四角背景色。
    """
    if ref_img is None:
        return (50, 200, 800, 1500)   # 示意值
    w, h = ref_img.size
    return (int(0.05 * w), int(0.05 * h), int(0.95 * w), int(0.95 * h))


def compose_char_card(char_cfg: dict, out_dir: Path) -> Path:
    """拼装一张角色卡（写实版）

    char_cfg: 符合 templates/character-card.md 配置的字典
    out_dir: 输出目录
    """
    parts_dir = ROOT / char_cfg["parts"]
    out_path = out_dir / char_cfg["out"]
    out_dir.mkdir(parents=True, exist_ok=True)

    # 画布尺寸
    W, H = 1920, 1080
    canvas = Image.new("RGB", (W, H), (240, 237, 231))
    draw = ImageDraw.Draw(canvas)

    # 1. 标题
    ft = font(48)
    draw.text((40, 20), char_cfg["title"], font=ft, fill=(28, 26, 24))

    # 2. 副标题
    ft = font(28)
    draw.text((40, 80), char_cfg.get("subtitle", ""), font=ft, fill=(80, 80, 80))

    # 3. 大肖像
    bust_path = parts_dir / char_cfg["bust"]
    if bust_path.exists():
        bust = Image.open(bust_path).convert("RGB")
        bust = bust.resize((560, 720), Image.LANCZOS)
        canvas.paste(bust, (40, 140))

    # 4. 三视图（横版 3 列）
    turn_path = parts_dir / char_cfg["turn"]
    if turn_path.exists():
        turn = Image.open(turn_path).convert("RGB")
        turn = turn.resize((1100, 400), Image.LANCZOS)
        canvas.paste(turn, (620, 140))

    # 5. 资料栏 + 性格
    ft = font(22)
    x, y = 620, 560
    info_pairs = char_cfg.get("info_pairs", [])
    for k, v in info_pairs[:6]:
        draw.text((x, y), f"{k}：{v}", font=ft, fill=(40, 40, 40))
        y += 36
    y += 12
    draw.text((x, y), f"性格：{char_cfg.get('traits', '')}", font=ft, fill=(40, 40, 40))

    # 6. 微表情（横版 2×3）
    expr_path = parts_dir / char_cfg["expr"]
    if expr_path.exists():
        expr = Image.open(expr_path).convert("RGB")
        expr = expr.resize((1100, 240), Image.LANCZOS)
        canvas.paste(expr, (620, 800))

    # 7. 服饰 + 装备图鉴（并排）
    acc_path = parts_dir / char_cfg["acc"]
    eq_path = parts_dir / char_cfg["eq"]
    if acc_path.exists():
        acc = Image.open(acc_path).convert("RGB")
        acc = acc.resize((540, 240), Image.LANCZOS)
        canvas.paste(acc, (40, 880))
    if eq_path.exists():
        eq = Image.open(eq_path).convert("RGB")
        eq = eq.resize((540, 240), Image.LANCZOS)
        canvas.paste(eq, (620, 880))

    # 8. 页脚
    ft = font(16)
    draw.text((40, H - 30), char_cfg.get("foot", ""), font=ft, fill=(120, 120, 120))

    canvas.save(out_path, optimize=True)
    return out_path


# ---- 角色字典（按需补充）----
CHARS: dict[str, dict] = {
    # "<角色名>": { ... 配置 ... }
}


def main():
    if len(sys.argv) < 2:
        print("用法：python3 compose_card.py <角色名>")
        print(f"已配置角色：{list(CHARS.keys())}")
        sys.exit(1)
    char_name = sys.argv[1]
    if char_name not in CHARS:
        print(f"[ERROR] 角色 {char_name} 未在 CHARS 中定义")
        sys.exit(1)

    char_cfg = CHARS[char_name]
    out = compose_char_card(char_cfg, ROOT / "角色定妆照" / char_name)
    print(f"[OK] {out}")


if __name__ == "__main__":
    main()