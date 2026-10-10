#!/usr/bin/env python3
"""novel-to-comic 集成品 mock 样张生成器

生成 3 张 1080×1920 (9:16) 的 mock 集成品样张：
- mock_P01_封面.png：P01 封面（含 Logo 浮动标题板）
- mock_P02_铺垫.png：典型文戏铺垫页（含因果链气泡）
- mock_P05_钩子.png：典型末页（含关注条）

这些样张使用通用占位文字（"主角"、"配角"、"场景名"等），
不绑定任何特定小说/角色/场景，作为 novel-to-comic 方法论
的视觉演示用。

依赖：bubble_lib.py（已包含 5 类气泡 + 旁白 + 浮字）
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 复用 bubble_lib 公共库
import sys
sys.path.insert(0, str(Path(__file__).parent))
from bubble_lib import (
    bubble, mental_bubble, narration, loc_box, float_word,
    remove_watermark, white_gutters,
)

HERE = Path(__file__).parent
OUT_DIR = HERE.parent / "tools" / "_page_samples"
OUT_DIR.mkdir(exist_ok=True)

W, H = 1080, 1920

# 通用字体（从 bubble_lib 默认）
FONT_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]
def font(size):
    for fp in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(fp, size)
        except OSError:
            continue
    return ImageFont.load_default()


# 模拟底色：占位场景（不绑定任何 IP）
SCENE_BG = {
    "forest":      (88, 124, 96),    # 树林绿
    "mountain":    (108, 92, 76),    # 山脊棕
    "city":        (140, 138, 134),  # 城郭灰青
}


def draw_placeholder_scene(im, scene="forest"):
    """画一张占位场景底图（不绑 IP）"""
    d = ImageDraw.Draw(im)
    bg = SCENE_BG.get(scene, (128, 128, 128))
    d.rectangle([0, 0, W, H], fill=bg)

    ft = font(40)
    # 顶部天/底部地 分层（占位构图）
    for y in range(0, H, 60):
        c = (max(0, bg[0]-30), max(0, bg[1]-30), max(0, bg[2]-30))
        d.line([0, y, W, y], fill=c, width=1)

    # 三个占位人物剪影
    d.ellipse([150, 800, 350, 1000], fill=(40, 40, 40))   # 左中
    d.ellipse([430, 900, 630, 1100], fill=(60, 60, 60))  # 中右
    d.ellipse([750, 700, 950, 900], fill=(40, 40, 40))   # 右中

    # 占位文字
    d.text((40, 40), "[ 占位场景图 - 真实出图由 ImageGen 生成 ]",
           font=font(28), fill=(220, 220, 220))


def mock_p01_cover():
    """P01 封面：含 Logo 浮动标题板"""
    im = Image.new("RGB", (W, H), (60, 70, 90))
    d = ImageDraw.Draw(im)
    draw_placeholder_scene(im, "mountain")

    # 浮动标题板（Logo + 集号）
    # 面板 y240–624 全宽
    d.rectangle([0, 240, W, 624], fill=(255, 215, 0))   # 金色面板
    d.rectangle([0, 240, W, 268], fill=(40, 30, 0))     # 上边深色
    d.rectangle([0, 596, W, 624], fill=(40, 30, 0))     # 下边深色
    d.text((40, 260), "<项目名>", font=font(72), fill=(40, 30, 0))
    d.text((40, 360), "第<N>集 · <短名>", font=font(78), fill=(40, 30, 0))
    d.text((40, 480), "<结果前置句>", font=font(48), fill=(80, 50, 0))

    # 主视觉占位
    d.ellipse([340, 1100, 740, 1500], fill=(180, 100, 50))
    d.text((40, 1500), "[ 主视觉：角色 + 动作 + 结果 ]", font=font(28), fill=(220, 220, 220))

    # 浮字（拟声）
    float_word(d, 700, 1300, "<轰！>", size=120)

    # 署名（占位）
    d.text((40, H - 50), "原著：<原著>", font=font(24), fill=(220, 220, 220))

    white_gutters(im)
    out = OUT_DIR / "mock_P01_封面.png"
    im.save(out, optimize=True)
    print(f"[OK] {out}")


def mock_p02_setup():
    """P02 铺垫页：典型文戏，含因果链气泡"""
    im = Image.new("RGB", (W, H), (88, 124, 96))
    d = ImageDraw.Draw(im)
    draw_placeholder_scene(im, "forest")

    # 地点框（仅左上角）
    loc_box(d, 80, 80, "<场景名>", size=34)

    # 对白泡（中心，文戏）
    bubble(d, 540, 400, 700, 200, ["<角色A>", "「<台词>」"], size=42, tail=(300, 700))

    # 旁白框（顶部）
    narration(d, 80, 200, ["<旁白>"], size=32, style="box")

    # 第二组对话
    bubble(d, 540, 900, 600, 180, ["<角色B>", "「<台词>」"], size=38, tail=(760, 1100))

    # 心里话
    mental_bubble(d, 540, 1400, 700, 180, ["<角色A>", "（<心里话>）"], size=36, tail=(300, 1600))

    white_gutters(im)
    out = OUT_DIR / "mock_P02_铺垫.png"
    im.save(out, optimize=True)
    print(f"[OK] {out}")


def mock_p05_hook():
    """P05 末页：含钩子 + 关注条"""
    im = Image.new("RGB", (W, H), (108, 92, 76))
    d = ImageDraw.Draw(im)
    draw_placeholder_scene(im, "city")

    loc_box(d, 80, 80, "<场景名>", size=34)

    # 高潮对白
    burst_bubble = __import__("bubble_lib").burst_bubble
    burst_bubble(d, 540, 700, 800, 250, ["<喊声！>"], size=56, tail=(240, 1200), tail_len=64)

    # 浮字（拟声）
    float_word(d, 200, 1100, "<轰！！>", size=140)

    # 末页关注条（底部）
    narration(d, 60, H - 110, ["关注<项目名>", "下集更精彩"], size=44, style="box")

    white_gutters(im)
    out = OUT_DIR / "mock_P05_钩子.png"
    im.save(out, optimize=True)
    print(f"[OK] {out}")


if __name__ == "__main__":
    mock_p01_cover()
    mock_p02_setup()
    mock_p05_hook()
    print(f"\n样张已生成到：{OUT_DIR}")