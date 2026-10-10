# 单页叠泡脚本模板

> 这是一份**可直接复用**的单页叠泡脚本模板。每页一个脚本，命名 `apply_pXXX_vN.py`。

---

## 模板

```python
#!/usr/bin/env python3
"""集 N · PXX 单页叠泡脚本（vY）

本脚本：
1. 读取底图 PXX_xxx_底图.png
2. 去水印
3. 按因果链表叠气泡 / 旁白 / 地点框 / 浮字
4. 统一白条化
5. 保存到集目录 PXX_xxx.png

因果链（与 episode-pacing.md 一致）：
- PXX-说话人：「台词」 @ (x, y)
- PXX-说话人：「台词」 @ (x, y)
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

# 公共库只 import，不写成品
from bubble_lib import (
    bubble, mental_bubble, burst_bubble, narration,
    loc_box, float_word, remove_watermark, white_gutters,
)

# ---- 路径配置 ----
ROOT = Path(__file__).resolve().parent.parent  # 项目根
WORKSPACE = ROOT / "<项目>" / "工作区" / "<集名>"
EPISODE = ROOT / "<项目>" / "<集名>"

# 底图与输出
BASE = WORKSPACE / "PXX_<短名>_底图.png"
OUT = EPISODE / "PXX_<短名>.png"

# ---- 中文字体（按 bubble_lib 默认）----
# bubble_lib 已经默认 STHeiti Medium.ttc，无需额外配置

def main():
    # 1. 读底图
    im = Image.open(BASE).convert("RGB")

    # 2. 去水印
    remove_watermark(im)

    # 3. 叠文字
    d = ImageDraw.Draw(im)

    # 3.1 地点框（左上角，整页只放一次）
    loc_box(d, 80, 80, "<场景名>", size=34)

    # 3.2 因果链上的所有对白
    bubble(d, cx, cy, bw, bh, ["台词 1", "台词 2"], size=36, tail=(tx, ty))
    bubble(d, cx, cy, bw, bh, ["台词 1"], size=36, tail=(tx, ty))
    mental_bubble(d, cx, cy, bw, bh, ["心里话……"], size=30, tail=(tx, ty))

    # 3.3 旁白框（如有时）
    narration(d, 100, 100, ["旁白内容"], size=28, style="box")

    # 3.4 浮字 / 拟声词
    float_word(d, 500, 1500, "火弹！", size=92)

    # 4. 统一白条化
    white_gutters(im)

    # 5. 保存到集目录
    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT, optimize=True)
    print(f"[OK] {OUT}")

if __name__ == "__main__":
    main()
```

---

## 调用示例：5 类气泡

```python
from PIL import Image, ImageDraw
from bubble_lib import (
    bubble, mental_bubble, burst_bubble, narration,
    loc_box, float_word, remove_watermark, white_gutters,
)

im = Image.open("P01_底图.png").convert("RGB")
d = ImageDraw.Draw(im)

# 1. 普通对白泡
bubble(d, 540, 200, 600, 150,
       ["接下来", "看我来"], size=36, tail=(300, 350))

# 2. 心里话（云状边）
mental_bubble(d, 540, 600, 500, 130,
              ["原来……", "还有这种灵气"], size=32, tail=(300, 750))

# 3. 厉声呐喊（锯齿爆框）
burst_bubble(d, 540, 1000, 600, 180,
             ["快躲开！"], size=42, spikes=18, inner=0.70,
             tail=(520, 340), tail_len=62)

# 4. 旁白框（横排）
narration(d, 100, 100, ["次日清晨"], size=28, style="box")

# 5. 浮字 / 拟声词（金字 + 重描边）
float_word(d, 500, 1500, "火弹！", size=92)

# 6. 地点框（左上角，整页只放一次）
loc_box(d, 80, 80, "神手谷·药庐", size=34)

# 7. 去水印
remove_watermark(im)

# 8. 统一白条化
white_gutters(im)

im.save("成品.png", optimize=True)
```

---

## 调用函数签名速查

### bubble 系列

```python
bubble(d, cx, cy, bw, bh, lines, size=36, tail=None, tail_len=34)
mental_bubble(d, cx, cy, bw, bh, lines, size=30, tail=None)
burst_bubble(d, cx, cy, bw, bh, lines, size=30, spikes=14, inner=0.80, tail=None, tail_len=40)
shaky_bubble(d, cx, cy, bw, bh, lines, size=30, tail=None, tail_len=34)
whisper_bubble(d, cx, cy, bw, bh, lines, size=24, tail=None, tail_len=24)
```

### 旁白与地点

```python
narration(d, x, y, lines, size=26, vertical=False, pad=12, style="box")
# style: "box" | "tag" | "rough"

loc_box(d, x, y, text, size=34)
```

### 浮字

```python
float_word(d, x, y, text, size=92)
```

### 后期处理

```python
remove_watermark(im)        # 去右下"AI生成"水印
white_gutters(im)           # 统一白条化
shrink_band(im, y0, y1, target=48)  # 超宽分隔带收窄
```

---

## 坐标计算技巧

### 经验值（1080×1920）

| 位置 | 坐标参考 |
|------|---------|
| 顶部 | y=200 |
| 中上 | y=500 |
| 中部 | y=900 |
| 中下 | y=1300 |
| 底部 | y=1700 |
| 死区 | y≥1840 |

### 留出顶栏安全区

P01 顶栏下移到 y240–1680 安全区，**主体构图避开 y240–620**。

### 留出底死区

**底死区约 18%–22%**（y≥1660），关键对白/钩子/主冲突勿入。

---

## 单页脚本的存放位置

**工作区**（不入库）：
```
<项目>/<原著名>/工作区/<集名>/apply_p001_v1.py
<项目>/<原著名>/工作区/<集名>/apply_p002_v1.py
```

**集目录只放成品**：
```
<项目>/<原著名>/<集名>/P01_xxx.png
<项目>/<原著名>/<集名>/P02_xxx.png
```

---

## 重出过的页必须重跑

如果某页因为撞图/撞脸等问题 img2img 重出，分格缝会变。**必须**重跑 `measure_gutters.py` 再核气泡坐标。

```python
# 工作区/measure_gutters.py
"""分格测量：扫底图分格白条，给出气泡坐标建议。"""
# 实现略（按项目需要）
```

---

## 已知坑位

| 坑 | 规避 |
|----|------|
| 模块级叠泡代码被 import 重跑覆盖成品 | PIL 公共库只 import 不写成品；本脚本只 import 不写库 |
| narration() 误用 | 是直接绘制函数，不是干跑。量宽必须用 `probe.textbbox` |
| Edit 偶发"报成功但未落盘" | 每次编辑后用 Grep 复核文件实际内容 |
| float_word 右缘裁字 | x+len(text)×size+描边 ≤ 1072 强制约束 |
| 重出过的页坐标没核 | 重跑 `measure_gutters.py` 再叠泡 |