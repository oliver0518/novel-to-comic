#!/usr/bin/env python3
"""novel-to-comic 漫画页气泡绘制公共库（方案A：画面/文字分离，文字全部后期 PIL 叠）。

定位：**纯函数库**——不含任何集目录、底图路径，也永不写成品文件。
单页脚本自己定义本集目录/底图路径，import 本库后逐个调用。

⚠ 铁律：任何生成成品的代码必须写在单页脚本里，本库的 __main__ 只渲染
样式样张（`tools/_bubble_samples_overview.png`）。历史事故：apply_plan_a.py
的模块级示例块曾让任何 import 都用旧底图重跑 P07、覆盖成品。

直接运行本文件可重新生成样式样张：
    python3 bubble_lib.py

调用示例（单页脚本）：
    from bubble_lib import bubble, mental_bubble, narration, loc_box, float_word
    from bubble_lib import remove_watermark, white_gutters
    d = ImageDraw.Draw(im)
    bubble(d, 540, 200, 600, 150, ['你好', '世界'], size=36, tail=(300, 350))
    loc_box(d, 80, 80, '神手谷·药庐', size=34)
    narration(d, 100, 100, ['次日清晨'], size=28, style='box')
    float_word(d, 500, 800, '火弹！', size=92)
    remove_watermark(im)
    white_gutters(im)
"""
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------- 全局默认（可用参数覆盖） ----------
_FONT_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
]
FONT = _FONT_CANDIDATES[0]
INK = (28, 26, 24)                # 墨色描边/文字
PAPER = (255, 255, 255)
NARRATION_PAPER = (252, 250, 244)
WM = (855, 1838, 1080, 1918)      # 1080×1920 右下「AI生成」水印区域


def f(size, font_path=None):
    """取字体；首选 STHeiti，缺失时按候选链自动降级。"""
    path = font_path or FONT
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        for cand in _FONT_CANDIDATES:
            try:
                return ImageFont.truetype(cand, size)
            except OSError:
                continue
    raise RuntimeError("找不到可用中文字体，请检查 _FONT_CANDIDATES")


def remove_watermark(im, wm=None):
    """右下「AI生成」水印清除 v3（2026-09-16）。

    病史：v1 羽化 mask 写反（中心透明）→ 水印中心从未盖掉；v2 修 mask 后，
    水印文字贴着图像底/右边缘，而羽化圈在区域外缘是透明的 → 边缘一圈永远漏。
    v3：双源混合补丁（水平克隆+垂直翻转各50%）**不透明整贴**，再只对区域
    上/左两条缝线做 4px 局部虚化（贴图像边缘的两条边不需要融合——没有内容了）。

    wm=None 时按图像尺寸相对定位（兼容 1072/1080 宽）；严禁 AI 擦除（会连中文一起擦）。
    """
    if wm is None:
        W, H = im.size
        wm = (int(0.785 * W), int(0.950 * H), W, H)
    x0, y0, x1, y1 = wm
    x1, y1 = min(x1, im.size[0]), min(y1, im.size[1])
    w, h = x1 - x0, y1 - y0
    sx1 = x0
    sx0 = max(0, sx1 - w)
    patch_h = im.crop((sx0, y0, sx1, y1)).transpose(Image.FLIP_LEFT_RIGHT)
    if patch_h.size[0] < w:
        need = w - patch_h.size[0]
        extra = im.crop((sx1, y0, min(im.size[0], sx1 + need), y1)).transpose(Image.FLIP_LEFT_RIGHT)
        canvas = Image.new("RGB", (w, h))
        canvas.paste(patch_h, (0, 0))
        canvas.paste(extra, (patch_h.size[0], 0))
        patch_h = canvas
    patch_v = im.crop((x0, max(0, y0 - h), x1, y0)).transpose(Image.FLIP_TOP_BOTTOM)
    patch = patch_h if patch_v.size != patch_h.size else Image.blend(patch_h, patch_v, 0.5)
    patch = patch.filter(ImageFilter.GaussianBlur(1.2))
    im.paste(patch, (x0, y0))                      # 不透明整贴，边缘零泄漏
    d = ImageDraw.Draw(im)                          # 仅上/左缝线局部虚化
    seam = im.crop((x0 - 4, y0 - 4, x0 + 6, y1)).filter(ImageFilter.GaussianBlur(2))
    im.paste(seam, (x0 - 4, y0 - 4))
    seam2 = im.crop((x0 - 4, y0 - 4, x1, y0 + 6)).filter(ImageFilter.GaussianBlur(2))
    im.paste(seam2, (x0 - 4, y0 - 4))
    return im


def hard_cover_wm_bottom(im):
    """页底水印残带硬盖 v2：同行水平克隆整贴 + 上缝线虚化（v1 羽化 mask 已废弃）。"""
    w, h = im.size
    if h != 1920:
        return im
    x0 = int(0.76 * w)
    sw = w - x0
    src_ = im.crop((x0 - sw, 1898, x0, 1920)).transpose(Image.FLIP_LEFT_RIGHT)
    src_ = src_.filter(ImageFilter.GaussianBlur(1.0))
    im.paste(src_, (x0, 1898))
    seam = im.crop((x0 - 4, 1894, x0 + 6, 1908)).filter(ImageFilter.GaussianBlur(2))
    im.paste(seam, (x0 - 4, 1894))
    return im


def white_gutters(im, black_thr=45, white_thr=242, max_band=220, margin=6,
                  uniform=8.0, fill=(255, 255, 255)):
    """分格分隔条统一白条化（2026-09-16 Oliver 新规：业内漫画分隔条=白条，禁黑条）。

    两步：
      1) 黑条→白条：整行/整列近黑且**均匀**的带（历史脚本涂的 (12,12,12) 黑缝）
         改刷纯白。带内像素 std < uniform 才动——夜景/黑袍等内容虽有暗行但纹理
         方差大，不会被误伤（35 集夜戏实测判据）。
      2) 白缝规整：生成残留的近白缝带统一刷纯白，成为干净完整的分隔白条
         （同时吸收紧贴黑条旁的细白发丝线）。

    只动 6~max_band 宽的整行/整列条带、页边 margin 内不动；返回改动清单
    [("行", y0, y1, "黑→白"|"白规整"), ...]。参考基准：海贼王1189 分隔条
    实测白条 40~60px、均亮 230~254。
    """
    DARK_MAX, BAND_MIN = 12, 6
    import numpy as np

    d = ImageDraw.Draw(im)
    changed = []

    def _scan(a, mode):
        h, w = a.shape
        prof = a.mean(axis=1)
        out = []
        y = margin
        while y < h - margin:
            hit = prof[y] < black_thr if mode == "black" else prof[y] > white_thr
            if hit:
                y2 = y
                lim = h - margin
                while y2 < lim:
                    p = prof[y2] < black_thr if mode == "black" else prof[y2] > white_thr
                    if not p:
                        break
                    y2 += 1
                if y > margin and 6 <= y2 - y <= max_band:
                    if mode != "black" or float(a[y:y2, :].std()) < uniform:
                        out.append((y, y2))
                y = y2 + 1
            else:
                y += 1
        return out

    # 1) 黑条 → 白条
    a = np.asarray(im.convert("L"), dtype=np.float32)
    for y0, y1 in _scan(a, "black"):
        d.rectangle([0, y0, im.size[0] - 1, y1 - 1], fill=fill)
        changed.append(("行", y0, y1, "黑→白"))
    a = np.asarray(im.convert("L"), dtype=np.float32)
    for x0, x1 in _scan(a.T, "black"):
        d.rectangle([x0, 0, x1 - 1, im.size[1] - 1], fill=fill)
        changed.append(("列", x0, x1, "黑→白"))

    # 2) 白缝规整为纯白
    a = np.asarray(im.convert("L"), dtype=np.float32)
    for y0, y1 in _scan(a, "white"):
        d.rectangle([0, y0, im.size[0] - 1, y1 - 1], fill=fill)
        changed.append(("行", y0, y1, "白规整"))
    a = np.asarray(im.convert("L"), dtype=np.float32)
    for x0, x1 in _scan(a.T, "white"):
        d.rectangle([x0, 0, x1 - 1, im.size[1] - 1], fill=fill)
        changed.append(("列", x0, x1, "白规整"))

    # 3) 白带边缘夹线吸收（2026-09-16 P05/P10 实证）：模型自画的 4~8px 分格框线、
    #    缝边过渡灰行，紧贴白带但不够黑/太窄，逃过第 1 步 → 成了「白条里一根黑线」。
    #    对每条白带向两侧吸收 ≤12px 的非白段并整段刷白。
    a = np.asarray(im.convert("L"), dtype=np.float32)

    def _absorb(prof, n):
        res = []
        i = margin
        while i < n - margin:
            if prof[i] > white_thr:
                j = i
                while j < n - margin and prof[j] > white_thr:
                    j += 1
                if BAND_MIN <= j - i <= max_band:
                    lo, hi = i, j
                    k = j
                    while k < n - margin and prof[k] <= white_thr and k - j < DARK_MAX:
                        k += 1
                    hi = max(hi, k)
                    m = i
                    while m > margin and prof[m - 1] <= white_thr and i - (m - 1) < DARK_MAX:
                        m -= 1
                    lo = min(lo, m)
                    if (lo, hi) != (i, j):
                        res.append((lo, hi))
                i = j
            else:
                i += 1
        return res

    for y0, y1 in _absorb(a.mean(axis=1), a.shape[0]):
        d.rectangle([0, y0, im.size[0] - 1, y1 - 1], fill=fill)
        changed.append(("行", y0, y1, "夹线吸收"))
    a = np.asarray(im.convert("L"), dtype=np.float32)
    for x0, x1 in _absorb(a.mean(axis=0), a.shape[1]):
        d.rectangle([x0, 0, x1 - 1, im.size[1] - 1], fill=fill)
        changed.append(("列", x0, x1, "夹线吸收"))
    return changed


def shrink_band(im, y0, y1, target=48):
    """超宽分隔带收窄到标准分隔条宽度（2026-09-16 白条新规配套）。

    模型偶尔在两格间留出 100~200px 的空白带（旧规涂黑=超厚黑条，新规刷白=空白区，
    都不合规）。本函数把它收窄为 target 宽：带内保留上 target//2 行，其余从下一段
    内容垂直拉伸补齐，页高不变。返回新带位 (y0, y1)。
    注意：调用后位于带下方的浮字/气泡 y 坐标要按拉伸比例重算。
    """
    w, h = im.size
    band = y1 - y0
    if band <= target or y1 >= h:
        return y0, y1
    keep_top = target // 2
    bottom_src = im.crop((0, y1 - (target - keep_top), w, h))
    dst_h = h - (y0 + keep_top)
    bottom = bottom_src.resize((w, dst_h), Image.LANCZOS)
    im.paste(bottom, (0, y0 + keep_top))
    return y0, y0 + target


def _blob_pts(cx, cy, rx, ry, wob=0.05, seed=1, n=64):
    """海贼王式手绘团块轮廓：椭圆半径叠加 2/3/5 次低频谐波扰动，
    得到闭合平滑、有轻微起伏的不规则 blob（不是完美椭圆）。
    seed 由坐标派生 → 同一泡坐标固定，形状稳定可复现。"""
    s = abs(int(cx * 7 + cy * 13 + rx * 3 + ry)) % (2**31) + seed
    import random
    rnd = random.Random(s)
    phases = [rnd.uniform(0, 2 * math.pi) for _ in range(3)]
    amps = [wob * rnd.uniform(0.6, 1.0) for _ in range(3)]
    freqs = [2, 3, 5]
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        m = 1 + sum(amps[k] * math.sin(freqs[k] * a + phases[k]) for k in range(3))
        pts.append((cx + rx * m * math.cos(a), cy + ry * m * math.sin(a)))
    return pts


def _thick_poly(d, pts, fill=(255, 255, 255), width=5, outline=INK):
    """填充多边形 + 加粗描边（PIL polygon 的 outline 不支持宽线）。"""
    d.polygon(pts, fill=fill)
    for i in range(len(pts)):
        d.line([pts[i], pts[(i + 1) % len(pts)]], fill=outline, width=width)


def _tail_pts(cx, cy, bw, bh, tail, tail_len=34, base_ratio=0.09):
    tx, ty = tail
    ang = math.atan2(ty - cy, tx - cx)
    ux, uy = math.cos(ang), math.sin(ang)
    rx, ry = bw / 2, bh / 2
    t_edge = 1.0 / math.sqrt((ux / rx) ** 2 + (uy / ry) ** 2 + 1e-9)
    w = max(13, bw * base_ratio)
    bx, by = cx + t_edge * 0.82 * ux, cy + t_edge * 0.82 * uy
    tipx, tipy = cx + (t_edge + tail_len) * ux, cy + (t_edge + tail_len) * uy
    return [
        (bx - uy * w, by + ux * w),
        (bx + uy * w, by - ux * w),
        (tipx, tipy),
    ], ((bx - uy * w * 0.92, by + ux * w * 0.92), (bx + uy * w * 0.92, by - ux * w * 0.92))


def _tail_tip(cx, cy, bw, bh, tail, tail_len):
    tx, ty = tail
    ang = math.atan2(ty - cy, tx - cx)
    ux, uy = math.cos(ang), math.sin(ang)
    rx, ry = bw / 2, bh / 2
    t_edge = 1.0 / math.sqrt((ux / rx) ** 2 + (uy / ry) ** 2 + 1e-9)
    return (cx + (t_edge + tail_len) * ux, cy + (t_edge + tail_len) * uy)


def _merge_tail_into_outline(pts, cx, cy, bw, bh, tail, tail_len=34, skip=None):
    """把尾巴并入泡框轮廓：整只泡只填充/描边一次，避免三角尾巴贴上去的分离感。"""
    if not tail:
        return pts
    tx, ty = tail
    target = math.atan2(ty - cy, tx - cx)

    def angle_delta(p):
        a = math.atan2(p[1] - cy, p[0] - cx)
        return abs(math.atan2(math.sin(a - target), math.cos(a - target)))

    n = len(pts)
    i = min(range(n), key=lambda idx: angle_delta(pts[idx]))
    k = skip if skip is not None else max(2, int(n * 0.035))
    tip = _tail_tip(cx, cy, bw, bh, tail, tail_len)
    start = (i + k) % n
    end = (i - k) % n
    merged = []
    j = start
    while True:
        merged.append(pts[j])
        if j == end:
            break
        j = (j + 1) % n
    merged.append(tip)
    return merged


def _draw_tail(d, cx, cy, bw, bh, tail, tail_len, width=6, fill=PAPER):
    pts, bridge = _tail_pts(cx, cy, bw, bh, tail, tail_len)
    d.polygon(pts, fill=fill)
    d.line([pts[0], pts[2], pts[1]], fill=INK, width=width, joint="curve")
    d.line(bridge, fill=fill, width=width + 2)


def _draw_centered_lines(d, cx, cy, lines, size, fill=INK, leading=1.25, font_path=None):
    ft = f(size)
    y = cy - len(lines) * size * 1.25 / 2 + size * 0.12
    for ln in lines:
        s = d.textbbox((0, 0), ln, font=ft)
        d.text((cx - (s[2] - s[0]) / 2 - s[0], y), ln, font=ft, fill=fill)
        y += size * leading


def _speech_bubble(d, cx, cy, bw, bh, lines, size, tail=None, tail_len=34, wob=0.035, width=6):
    """手绘对白泡：接近海贼王常见圆泡，但轮廓不是完美椭圆。"""
    pts = _blob_pts(cx, cy, bw / 2, bh / 2, wob=wob, n=84)
    pts = _merge_tail_into_outline(pts, cx, cy, bw, bh, tail, tail_len)
    _thick_poly(d, pts, fill=PAPER, width=width)
    _draw_centered_lines(d, cx, cy, lines, size)


def _ellipse_bubble(d, cx, cy, bw, bh, lines, size, tail=None, tail_len=34):
    """旧名兼容：现在走手绘对白泡。"""
    _speech_bubble(d, cx, cy, bw, bh, lines, size, tail, tail_len)


def _cloud_pts(cx, cy, rx, ry, bumps=16, amp=0.075):
    """连续外凸的云泡轮廓。半径只向外鼓，不向内尖缩。"""
    pts = []
    n = bumps * 12
    for i in range(n):
        a = 2 * math.pi * i / n
        m = 1 + amp * (0.5 + 0.5 * math.sin(bumps * a))
        pts.append((cx + rx * m * math.cos(a), cy + ry * m * math.sin(a)))
    return pts


def cloud_bubble(d, cx, cy, bw, bh, lines, size=30, tail=None, tail_len=34):
    """心声/恍惚/烟云场景：规整云状泡，边缘连续凸圆。"""
    pts = _cloud_pts(cx, cy, bw / 2, bh / 2)
    pts = _merge_tail_into_outline(pts, cx, cy, bw, bh, tail, tail_len)
    _thick_poly(d, pts, fill=PAPER, width=6)
    _draw_centered_lines(d, cx, cy, lines, size)


def jagged_bubble(d, cx, cy, bw, bh, lines, size=32, spikes=18, inner=0.78, tail=None, tail_len=42):
    """惊呼/战斗喊声：粗黑锯齿泡。"""
    pts = []
    for i in range(spikes * 2):
        a = 2 * math.pi * i / (spikes * 2)
        r = 1.0 if i % 2 == 0 else inner
        pts.append((cx + bw / 2 * r * math.cos(a), cy + bh / 2 * r * math.sin(a)))
    pts = _merge_tail_into_outline(pts, cx, cy, bw, bh, tail, tail_len, skip=1)
    _thick_poly(d, pts, fill=PAPER, width=7)
    _draw_centered_lines(d, cx, cy, lines, size)


def shaky_bubble(d, cx, cy, bw, bh, lines, size=30, tail=None, tail_len=34):
    """吃惊/发颤/语气不稳：双层不规则轮廓。"""
    outer = _blob_pts(cx, cy, bw / 2, bh / 2, wob=0.07, seed=9, n=80)
    inner = _blob_pts(cx, cy, bw / 2 - 8, bh / 2 - 8, wob=0.055, seed=19, n=80)
    outer = _merge_tail_into_outline(outer, cx, cy, bw, bh, tail, tail_len)
    inner = _merge_tail_into_outline(inner, cx, cy, bw - 16, bh - 16, tail, max(8, tail_len - 12))
    d.polygon(outer, fill=PAPER)
    for pts, width in ((outer, 4), (inner, 2)):
        for i in range(len(pts)):
            d.line([pts[i], pts[(i + 1) % len(pts)]], fill=INK, width=width)
    _draw_centered_lines(d, cx, cy, lines, size)


def whisper_bubble(d, cx, cy, bw, bh, lines, size=24, tail=None, tail_len=24):
    """小声/远处对白：细线小泡，留白更轻。"""
    pts = _blob_pts(cx, cy, bw / 2, bh / 2, wob=0.025, seed=5, n=72)
    pts = _merge_tail_into_outline(pts, cx, cy, bw, bh, tail, tail_len)
    _thick_poly(d, pts, fill=PAPER, width=3)
    _draw_centered_lines(d, cx, cy, lines, size, leading=1.18)


def bubble(d, cx, cy, bw, bh, lines, size=36, tail=None, tail_len=34):
    """对白泡：手绘圆泡 + 小尾巴指向说话人。"""
    _speech_bubble(d, cx, cy, bw, bh, lines, size, tail, tail_len)


def mental_bubble(d, cx, cy, bw, bh, lines, size=30, tail=None):
    """心里话泡：云状泡 + 小尾巴指向人物。"""
    cloud_bubble(d, cx, cy, bw, bh, lines, size=size, tail=tail, tail_len=34)


def burst_bubble(d, cx, cy, bw, bh, lines, size=30, spikes=14, inner=0.80, tail=None, tail_len=40):
    """呐喊泡：粗黑锯齿泡。"""
    jagged_bubble(d, cx, cy, bw, bh, lines, size=size, spikes=spikes, inner=inner, tail=tail, tail_len=tail_len)


def narration(d, x, y, lines, size=26, vertical=False, pad=12, style="box"):
    """旁白/解说框：米白底黑框。vertical=True 时逐字竖排。
    style="box" 为普通矩形；style="tag" 为章节/场景窄条；style="rough" 为手绘边。
    返回框 bbox (x0, y0, x1, y1)，便于继续排版。"""
    ft = f(size)
    rows = [c for ln in lines for c in ln] if vertical else list(lines)
    widths = [d.textbbox((0, 0), r, font=ft) for r in rows]
    w = max(s[2] - s[0] for s in widths) + pad * 2
    if not vertical:
        w = max(w, 60)
    h = len(rows) * size * 1.28 + pad * 1.6
    if style == "rough":
        pts = _blob_pts(x + w / 2, y + h / 2, w / 2, h / 2, wob=0.045, seed=23, n=56)
        _thick_poly(d, pts, fill=NARRATION_PAPER, width=5)
    else:
        line_w = 5 if style == "tag" else 6
        d.rectangle((x, y, x + w, y + h), fill=NARRATION_PAPER, outline=INK, width=line_w)
    cy = y + pad * 0.8
    for r, s in zip(rows, widths):
        d.text((x + (w - (s[2] - s[0])) / 2 - s[0], cy), r, font=ft, fill=INK)
        cy += size * 1.28
    return (x, y, x + w, y + h)


def loc_box(d, x, y, text, size=34):
    """地点框：米底黑框，一般放页面左上角，整页只放一次。"""
    ft = f(size)
    s = d.textbbox((0, 0), text, font=ft)
    w, h = s[2] - s[0] + 28, s[3] - s[1] + 18
    d.rectangle((x, y, x + w, y + h), fill=(252, 250, 244), outline=INK, width=6)
    d.text((x + 14 - s[0], y + 9 - s[1]), text, font=ft, fill=INK)


def float_word(d, x, y, text, size=92):
    """浮字/拟声词/招式名：金字 + 深色重描边。（旋转/斜置待补）"""
    ft = f(size)
    for ox in range(-6, 7, 2):
        for oy in range(-6, 7, 2):
            d.text((x + ox, y + oy), text, font=ft, fill=(45, 28, 8))
    d.text((x, y), text, font=ft, fill=(235, 185, 55))


# ============================================================
# 样式样张（仅 __main__，可随时重生成；不写任何成品）
# ============================================================
if __name__ == "__main__":
    import os

    here = os.path.dirname(os.path.abspath(__file__))
    sample_dir = os.path.join(here, "_bubble_samples")
    os.makedirs(sample_dir, exist_ok=True)

    def bg(title):
        im = Image.new("RGB", (1080, 720), (188, 182, 170))
        d = ImageDraw.Draw(im)
        # 做三格漫画底纹，测试泡框在复杂边线上的可读性。
        d.rectangle((36, 82, 520, 666), fill=(236, 236, 232), outline=INK, width=5)
        d.rectangle((560, 82, 1044, 360), fill=(224, 224, 218), outline=INK, width=5)
        d.rectangle((560, 390, 1044, 666), fill=(232, 232, 226), outline=INK, width=5)
        for x in range(70, 500, 36):
            d.line((x, 110, x + 120, 640), fill=(170, 170, 164), width=2)
        ft = f(34)
        d.text((40, 28), title, font=ft, fill=INK)
        return im, d

    samples = []

    im, d = bg("01_手绘对白泡")
    bubble(d, 350, 220, 330, 120, ["接下来", "看我来"], size=36, tail=(245, 355))
    samples.append(("01_手绘对白泡.png", im))

    im, d = bg("02_心声云状泡")
    mental_bubble(d, 330, 255, 360, 132, ["原来……", "还有这种灵气"], size=32, tail=(470, 420))
    samples.append(("02_心声云状泡.png", im))

    im, d = bg("03_爆发喊声泡")
    burst_bubble(d, 330, 250, 360, 150, ["快躲开！"], size=42, spikes=18, inner=0.70, tail=(520, 340), tail_len=62)
    samples.append(("03_爆发喊声泡.png", im))

    im, d = bg("04_发颤惊疑泡")
    shaky_bubble(d, 760, 210, 330, 122, ["等等……", "那是什么？"], size=31, tail=(610, 310))
    samples.append(("04_发颤惊疑泡.png", im))

    im, d = bg("05_小声远处泡")
    whisper_bubble(d, 775, 500, 260, 92, ["小声些", "有人"], size=28, tail=(900, 610))
    samples.append(("05_小声远处泡.png", im))

    im, d = bg("06_横排旁白框")
    narration(d, 92, 120, ["数日前", "山谷外忽起怪风"], size=31, pad=16)
    samples.append(("06_横排旁白框.png", im))

    im, d = bg("07_竖排旁白框")
    narration(d, 860, 112, ["神手谷", "入夜"], size=32, vertical=True, pad=15)
    samples.append(("07_竖排旁白框.png", im))

    im, d = bg("08_场景窄条旁白")
    narration(d, 80, 96, ["同一时刻"], size=30, pad=13, style="tag")
    narration(d, 650, 420, ["谷外小路"], size=30, pad=13, style="tag")
    samples.append(("08_场景窄条旁白.png", im))

    im, d = bg("09_手绘边旁白")
    narration(d, 116, 130, ["那道青光", "只闪了一瞬"], size=30, pad=18, style="rough")
    samples.append(("09_手绘边旁白.png", im))

    for name, im in samples:
        im.save(os.path.join(sample_dir, name), optimize=True)

    im = Image.new("RGB", (1080, 960), (168, 158, 142))
    d = ImageDraw.Draw(im)
    loc_box(d, 30, 30, "气泡样式总览（业内漫画参考）")
    bubble(d, 250, 150, 270, 104, ["对白泡", "手绘圆"], size=31, tail=(360, 230))
    mental_bubble(d, 620, 150, 300, 112, ["心声泡", "云状边"], size=30, tail=(735, 230))
    burst_bubble(d, 930, 150, 240, 108, ["喊声！"], size=34, tail=(990, 240))
    shaky_bubble(d, 250, 430, 270, 110, ["惊疑……", "发颤"], size=30, tail=(370, 500))
    whisper_bubble(d, 615, 430, 260, 94, ["小声", "远处"], size=28, tail=(735, 500))
    narration(d, 820, 360, ["竖排", "旁白"], size=29, vertical=True)
    narration(d, 80, 660, ["横排旁白框", "用于时间/叙述切换"], size=29)
    narration(d, 555, 660, ["场景窄条"], size=29, style="tag")
    narration(d, 740, 640, ["手绘边", "旁白"], size=28, style="rough")
    float_word(d, 390, 800, "轰！！", size=92)
    out = os.path.join(here, "_bubble_samples_overview.png")
    im.save(out, optimize=True)
    print("总览样张已生成:", out)
    print("单项测试图目录:", sample_dir)
