#!/usr/bin/env python3
"""novel-to-comic 成品页自动质检门禁（QA Gate）

用途：交付前一条命令跑完 7 项机械检查，替代人工逐页目检的重复劳动。
用法：
    python3 tools/qa_check.py <集目录>            # 检查 P*.png 成品
    python3 tools/qa_check.py <集目录> --json     # 输出 JSON（给脚本消费）
    python3 tools/qa_check.py <集目录> -v         # 附每页统计明细

退出码：0 = 全部通过；1 = 有 ERROR 级问题（必须修）；2 = 仅 WARN（人工确认）

检查项（与人工目检清单一一对应）：
  1. 命名与尺寸规范   P0x_*.png（排除 _预览3x4/_浮字 等中间件）；宽高一致、9:16
  2. 黑条/空白带检查   分隔条必须为业内漫画白条（新规：禁黑条）：
                       近黑均匀条带=ERROR（残留黑缝）；>120px 超宽白带=WARN（疑似空白区）
  3. 页边白边         左右白列 / 底部白行 → 应拉伸铺满或涂黑
  4. 水印残留         右下角亮笔画像素计数
  5. 相邻页撞图       32×32 灰度相关系数 >0.93 → 疑似同构图重复
  6. 气泡体检         亮斑+黑边轮廓识别气泡 → 内部墨色占比判空泡/糊死
  7. 画风离群         每页 mean L / mean S 离群（>1.5σ）→ 提示核对是否同集漂移
"""
import argparse
import json
import os
import re
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

SKIP_PAT = re.compile(r"(_预览3x4|_浮字|_底图|预览)")

# ---------- 单项检查 ----------


def check_name_size(path, name, warn):
    ok = True
    if SKIP_PAT.search(name):
        return True, None
    if not re.match(r"^P\d{2}[_\-].*\.png$", name):
        warn.append(f"命名不合规范（应 P0x_短名.png）：{name}")
        ok = False
    return ok, None


def check_gutters(gray, name, black_thr=45, white_thr=242, min_band=6,
                  max_band=220, wide_white=120, margin=6, uniform=8.0):
    """分隔条检查（新规：分隔条=统一白条，禁黑条；页内禁空白区）。

    返回 (黑条列表, 超宽白带列表)：
      黑条    = 整行/整列近黑且均匀（带内 std<uniform=8）的条带 → ERROR。
                均匀度判据排除夜景/黑袍等暗内容（std≈13-14）。
      超宽白带 = >wide_white 的近白条带 → WARN（分隔条实测 36~60px，更宽
                的白带更可能是未铺满的空白区）。
    """
    h, w = gray.shape

    def scan(prof, img, mode):
        out = []
        i = margin
        n = len(prof)
        while i < n - margin:
            hit = prof[i] < black_thr if mode == "black" else prof[i] > white_thr
            if hit:
                j = i
                while j < n - margin:
                    p = prof[j] < black_thr if mode == "black" else prof[j] > white_thr
                    if not p:
                        break
                    j += 1
                if i > margin and min_band <= j - i <= max_band:
                    if mode == "black" and float(img[i:j, :].std()) >= uniform:
                        i = j + 1
                        continue
                    out.append((int(i), int(j)))
                i = j + 1
            else:
                i += 1
        return out

    black = [("行", a, b) for a, b in scan(gray.mean(axis=1), gray, "black")]
    black += [("列", a, b) for a, b in scan(gray.mean(axis=0), gray.T, "black")]
    white = [("行", a, b) for a, b in scan(gray.mean(axis=1), gray, "white")
             if b - a > wide_white]
    white += [("列", a, b) for a, b in scan(gray.mean(axis=0), gray.T, "white")
              if b - a > wide_white]
    return black, white


def check_page_edges(gray, name, thr=246):
    """页边白边：左右列白 / 底部行白（>6px）→ 返回描述列表"""
    h, w = gray.shape
    out = []
    cm = gray.mean(axis=0)
    rm = gray.mean(axis=1)
    left = 0
    while left < w and cm[left] > thr:
        left += 1
    if left > 6:
        out.append(f"左缘白边 {left}px")
    right = 0
    while right < w and cm[w - 1 - right] > thr:
        right += 1
    if right > 6:
        out.append(f"右缘白边 {right}px")
    bot = 0
    while bot < h and rm[h - 1 - bot] > thr:
        bot += 1
    if bot > 6:
        out.append(f"底部白尾 {bot}px（应拉伸铺满）")
    return out


def check_watermark(gray):
    """水印文字检测：只看精确文字区（0.795w..w, 0.958h..h），
    且要求「文字状笔画」——亮像素聚成多个小连通域（每块 <400px、块数 >=4）。
    自然亮纹理（草地高光/衣袍反光）是大块平滑区域，不会命中。"""
    h, w = gray.shape
    reg = gray[int(0.958 * h):, int(0.795 * w):]
    bright = reg > 205
    total = int(bright.sum())
    if total < 120:
        return 0
    lab, n = ndimage.label(bright)
    if n == 0:
        return 0
    sizes = ndimage.sum(bright, lab, range(1, n + 1))
    small = int((sizes < 400).sum())
    if small >= 4:                      # 多个小笔画块 = 文字特征
        return total
    return 0


def check_dup_pages(grays):
    """相邻页灰度相关系数 >0.93 → 疑似撞图"""
    sigs = []
    for g in grays:
        small = np.asarray(Image.fromarray(g).resize((32, 32), Image.BOX), dtype=np.float32)
        small = (small - small.mean()) / (small.std() + 1e-6)
        sigs.append(small.ravel())
    out = []
    for i in range(len(sigs) - 1):
        c = float(np.dot(sigs[i], sigs[i + 1]) / len(sigs[i]))
        if c > 0.93:
            out.append((i, i + 1, round(c, 3)))
    return out, [round(float(np.dot(sigs[i], sigs[i + 1]) / len(sigs[i])), 3) for i in range(len(sigs) - 1)]


def check_bubbles(gray):
    """识别气泡（亮斑 + 墨线轮廓）并体检内部墨色占比。
    返回 (候选数, 空泡列表, 糊死列表)；坐标为 page 像素 bbox。"""
    h, w = gray.shape
    area_page = h * w
    bright = gray > 232
    lab, n = ndimage.label(bright)
    if n == 0:
        return 0, [], []
    empty, dead = [], []
    cand = 0
    for sl in ndimage.find_objects(lab):
        y0, y1 = sl[0].start, sl[0].stop
        x0, x1 = sl[1].start, sl[1].stop
        bw, bh = x1 - x0, y1 - y0
        area = bw * bh
        if not (0.002 * area_page <= area <= 0.06 * area_page):
            continue
        if not (0.45 <= bw / max(bh, 1) <= 2.4):
            continue
        if min(bw, bh) < 40:            # 太小的亮斑（火星/高光）过滤
            continue
        sub = gray[y0:y1, x0:x1]
        fill = (sub > 232).mean()
        if fill < 0.55:                 # 亮斑填充率低 → 不是泡面
            continue
        # 判定「有黑墨线轮廓」：bbox 四周 6px 环带里暗像素占比
        ring = np.concatenate([
            sub[:6, :].ravel(), sub[-6:, :].ravel(),
            sub[:, :6].ravel(), sub[:, -6:].ravel()])
        if (ring < 110).mean() < 0.25:
            continue
        cand += 1
        # 内部墨色（字）占比：只统计泡面内区
        inner = sub[10:-10, 10:-10]
        ink = (inner < 100).mean()
        if ink < 0.005:
            empty.append((int(x0), int(y0), int(x1), int(y1), round(float(ink), 4)))
        elif ink > 0.5:
            dead.append((int(x0), int(y0), int(x1), int(y1), round(float(ink), 4)))
    return cand, empty, dead


def check_style_outliers(gray, sat):
    """mean L / mean S 离群（同集内 >1.5σ）"""
    L = np.array([g.mean() for g in gray], dtype=np.float32)
    S = np.array([s.mean() for s in sat], dtype=np.float32)
    out = []
    for tag, arr in (("亮度", L), ("饱和", S)):
        mu, sd = arr.mean(), arr.std()
        for i, v in enumerate(arr):
            if sd > 1e-3 and abs(v - mu) > 1.5 * sd:
                out.append((i, tag, round(float(v), 1), round(float(mu), 1)))
    return out


# ---------- 主流程 ----------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    files = sorted(f for f in os.listdir(args.dir)
                   if f.lower().endswith(".png") and f.startswith("P"))
    if not files:
        print(f"[ERROR] {args.dir} 下没有 P*.png", file=sys.stderr)
        return 1

    pages, grays, sats, names = [], [], [], []
    for f in files:
        if SKIP_PAT.search(f):
            continue
        im = Image.open(os.path.join(args.dir, f)).convert("RGB")
        g = np.asarray(im.convert("L"), dtype=np.float32)
        hsv = np.asarray(im.convert("HSV"), dtype=np.float32)
        pages.append((f, im.size, g))
        grays.append(g)
        sats.append(hsv[:, :, 1])
        names.append(f)

    report = {"dir": args.dir, "pages": [], "errors": [], "warnings": []}

    # 1 命名/尺寸
    sizes = set()
    for f, size, g in pages:
        if not re.match(r"^P\d{2}[_\-].*\.png$", f):
            report["errors"].append(f"{f}：命名不合规范（应 P0x_短名.png）")
        sizes.add(size)
    if len(sizes) > 1:
        report["errors"].append(f"同集尺寸不一致：{sorted(sizes)}")
    for s in sizes:
        if abs(s[0] / s[1] - 9 / 16) > 0.02:
            report["warnings"].append(f"尺寸 {s} 非 9:16")

    # 2/3/4 逐页
    for f, size, g in pages:
        row = {"file": f, "size": size}
        black, wide_white = check_gutters(g, f)
        if black:
            report["errors"].append(f"{f}：黑条残留 {black}（新规：分隔条应为白条）")
        if wide_white:
            report["warnings"].append(f"{f}：超宽白带（疑似空白区，非分隔条宽度）{wide_white}")
        row["gutters"] = black
        edge = check_page_edges(g, f)
        if edge:
            report["warnings"].append(f"{f}：{'、'.join(edge)}")
        row["edges"] = edge
        wm = check_watermark(g)
        row["wm_px"] = wm
        if wm > 0:
            report["warnings"].append(
                f"{f}：右下亮笔画异常（{wm}px，水印残留或亮纹理，裁角部图人工确认 10 秒）")
        cand, empty, dead = check_bubbles(g)
        row.update(bubbles=cand, empty=empty, dead=dead)
        if empty:
            report["errors"].append(f"{f}：疑似空泡 {empty}（墨色占比过低）")
        if dead:
            report["errors"].append(f"{f}：疑似泡内糊死 {dead}")
        report["pages"].append(row)

    # 5 撞图
    if len(grays) >= 2:
        dup, allc = check_dup_pages(grays)
        report["adjacent_corr"] = allc
        for i, j, c in dup:
            report["warnings"].append(
                f"{names[i]} ↔ {names[j]} 相关系数 {c}（疑似撞图，人工确认）")

    # 7 画风离群
    for i, tag, v, mu in check_style_outliers(grays, sats):
        report["warnings"].append(f"{names[i]}：{tag} {v} 偏离全集均值 {mu}（核对画风漂移）")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"== QA {args.dir} ==")
        print(f"页数 {len(pages)}  尺寸 {sorted(sizes)}")
        for p in report["pages"]:
            flag = []
            if p["wm_px"] > 0:
                flag.append("角部?")
            if p["empty"]:
                flag.append("空泡?")
            if p["dead"]:
                flag.append("糊死?")
            if p["gutters"]:
                flag.append("黑条")
            if p["edges"]:
                flag.append("白边")
            extra = f"  泡{p['bubbles']}" if p["bubbles"] else ""
            print(f"  {p['file']:28s} {p['size']}{extra} {' '.join(flag)}")
            if args.verbose and p["empty"]:
                print(f"      空泡 bbox: {p['empty']}")
        print()
        for e in report["errors"]:
            print(f"[ERROR] {e}")
        for w_ in report["warnings"]:
            print(f"[WARN ] {w_}")
        if not report["errors"] and not report["warnings"]:
            print("✅ 全部检查通过")
    return 1 if report["errors"] else (2 if report["warnings"] else 0)


if __name__ == "__main__":
    sys.exit(main())
