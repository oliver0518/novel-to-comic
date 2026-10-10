# 05 · 单集出图详解

## 适用形态

每集 5–11 页 9:16 竖版（1080×1920），适合抖音/快手信息流连载。

---

## 铁律（违反必返工）

| # | 规则 | 理由 |
|---|------|------|
| 1 | **画面/文字分离（方案A）**——生图提示词必写「不画任何气泡、旁白、拟声词、文字」 | AI 画的文字空泡、错字率高；后期 AI 擦除会把中文一起擦掉 |
| 2 | **9:16 直出**——ImageGen `size:"1080x1920"` | 旧流程 2:3 → 裁剪留边已作废 |
| 3 | **锁脸 = 双图挂载**——`image1` 往期成品页（画风基准）+ `image2` 角色定妆照，`input_fidelity:"high"` | 单图挂载脸漂移；三图超请求体上限 |
| 4 | **集级设定卡先行**——出图前 5 分钟写一张卡 | 5 大类先验缺陷全堵在出图前 |
| 5 | **白条分隔条**——业内漫画惯例；禁黑条；页顶禁白条 | 黑条是旧流程陋习 |
| 6 | **生图禁画 Logo**——封面 Logo/章节行后期 PIL 叠 | AI 画的 Logo 永远不对 |
| 7 | **PIL 公共库只 import 不写成品** | 模块级示例块会让任何 import 都重跑覆盖成品 |
| 8 | **QA 门禁零 ERROR 才交付** | 漏过的小问题攒多了就成了「为什么这条数据差」的口径 |

每条都有具体踩坑案例，详见 [`docs/07-lessons-learned.md`](07-lessons-learned.md)。

---

## 端到端流程

```
节拍表 → 集级设定卡 → 出底图 → 目检 → 去水印 → 叠文字 → P01 封面顶栏 → QA 门禁 → 交付
  5min     5min        7.5min    10min   1min    15min        3min             5min
```

---

## 提示词骨架（v3 六段锁）

```
[CHARACTER LOCK]
<角色名>脸部最高优先级严格照搬参考图2：
脸型、眉、眼、鼻、唇全部照搬。
禁止美化、禁止换脸、禁止共用配角脸。
ENTIRE FIGURE — face, hairstyle, clothing, body proportions —
MUST exactly copy reference image 2.
禁止横过额头的丝带/头巾。

[ANATOMY LOCK]
EXACTLY TWO legs. EXACTLY TWO arms.
<双臂各自用途：right hand grips saber raised,
              left hand clutches wounded shoulder>
禁止藏手入体。禁止断肢。

[PROPORTION LOCK]
Head proportionate to body. 禁止头身错位。
<角色A> only one head taller than <角色B>.

[LAYOUT]
9:16 竖版漫画分格，海贼王 1189 式不规则格，
2 层为主、3 层最多。禁 4 层+密叠。
构图主体居中或偏左，避开 y240–1680 顶栏安全区。
封面构图：NO large empty black areas,
          ground extends to the bottom edge.

[PROP+NO-TEXT LOCK]
所有道具一律素面禁文字：<道具清单>。
禁止任何文字、气泡、旁白、拟声词、印章、Logo、Watermark。

[SCENE]
<具体场景描述>
<光线、天气、氛围>
<色板关键词>
```

---

## 生图工具选项

不同 AI 生图工具的提示词骨架大致相同，但参数略有差异：

| 工具 | size 参数 | input_fidelity | 备注 |
|------|----------|----------------|------|
| OpenAI ImageGen | `size: "1080x1920"` | `input_fidelity: "high"` | 默认选项 |
| GPT-4o Image-1 | 同上 | 同上 | 推荐 |
| Midjourney | `--ar 9:16` | `--cref` | 风格接近但锁脸差 |
| Stable Diffusion | 直接在 prompt | `IP-Adapter FaceID` | 开源可控 |

---

## 叠泡纪律

- 按分镜阅读顺序（左→右、上→下）交代
- **一句一泡、每格最多一泡**
- 群像场景才允许一格两泡且横向分开、尾巴分别指人
- 每泡必须有字、短句中文
- 引文用直角引号「」，心里话末尾用「……」
- 地点框只放一次（左上角）

### 气泡四型

| 类型 | 函数 | 用途 |
|------|------|------|
| 对白泡 | `bubble()` | 普通对话 |
| 心声泡 | `mental_bubble()` | 心里话、云状边 |
| 喊声泡 | `burst_bubble()` | 厉声呐喊、锯齿爆框 |
| 发颤泡 | `shaky_bubble()` | 吃惊、发颤 |
| 远声泡 | `whisper_bubble()` | 小声、远处 |
| 旁白框 | `narration()` | 旁白、解说、时间跳跃（支持竖排） |
| 地点框 | `loc_box()` | 地点 |
| 浮字 | `float_word()` | 拟声词、招式名 |

---

## 因果链规划表

出图前必写：

```markdown
| 页 | 说话人 | 台词 | 因果位 | 坐标（x, y） |
|----|--------|------|--------|--------------|
| P01 | <角色> | 「<台词>」 | 左下 | (60, 1700) |
| P01 | <旁白> | <旁白> | 顶 | (60, 200) |
| P02 | <角色> | 「<台词>」 | 中右 | (700, 800) |
| ... |
```

---

## 返修决策表

| 缺陷 | 最低成本路径 | 禁用的路径 |
|------|------------|----------|
| 撞脸（配角像主角） | img2img ENTIRE FIGURE + FACE LOCK 提示词 | 整页重出 |
| 脸漂移 | 换更高清的 `image2` 定妆照；PIL 缩 1200px | 加大生图分辨率 |
| 道具带字 | 提示词重写 + ENTIRE FIGURE 返修 | PIL 涂白（必留痕） |
| 白背景 | 提示词加 NO white background | PIL 涂黑 |
| 额头带子 | img2img + REMOVE headband ACROSS THE FOREHEAD | PIL 裁剪 |
| 断肢/藏手 | 提示词加 ANATOMY LOCK 写死双臂各自用途 + 整页重出 | PIL 贴回 |
| 头身错位 | 整页重出 + PROPORTION LOCK | PIL 缩放 |
| 撞图（相邻两页同构图） | 整格重出 + 提示词写不同动作/景别 | 简单改构图 |
| 面具偏白 | PIL 压暗法（L>阈值 亮部乘 0.34 冷色调） | img2img 重绘 |
| 顶栏遮挡 | PIL 整体下移 + 顶部天空延展（**只取纯天空区**） | 整页重出 |

---

## 封面顶栏纪律

### 仅 P01 叠 Logo+集号

P02+ 一律无顶栏。

### 主图 = 叠泡脚本刚生成的浮字成品

脚本 save() 全部写集目录，喂工作区路径会拿到旧副本。

### 封面构图纪律

- 整页满铺，禁大片黑/白空背景
- 提示词明写 `NO large empty black areas`、`ground extends to the bottom edge`
- 重要冲突元素避开 y 240–620（被标题板盖住）
- 封面浮字 y≥640
- float_word 右缘 x+w≤1072（曾裁掉「术」字）

### 抖音封面 3:4 居中裁切

默认顶栏下移进安全区（y240–1680）成浮动标题板、主图整页零裁切，并自动输出 `_预览3x4.png`（发布前必看）。

---

## 工作区结构

```
<项目>/<原著名>/工作区/<集名>/
├── P01_xxx_底图.png          # 无字底图（不入库）
├── P02_xxx_底图.png
├── ...
├── apply_p001_v1.py          # 单页叠泡脚本（不入库）
├── apply_p002_v1.py
├── ...
├── measure_gutters.py        # 分格测量（不入库）
└── generated-images/         # ImageGen 输出（不入库）
```

**集目录只放成品**：`<项目>/<原著名>/<集名>/P01_xxx.png`。

---

## 已知坑位（精选）

| 坑 | 规避 |
|----|------|
| 模型看不到图时「凭印象目检」 | 先再试一次直接 Read 目检（"内容过滤"多为暂时性）；确认不行才退「盲操作法」（亮度图定版面 + 像素量气泡） |
| 模块级叠泡代码被 import 重跑覆盖成品 | PIL 公共库只 import 不写成品 |
| Edit 偶发"报成功但未落盘" | 每次编辑后用 Grep 复核文件实际内容 |
| Bash `grep "a\|b"` 交替模式**静默返回空** | 多模式检索一律用 Grep 工具 |
| 局部返修贴回三条 | img2img 输出会重组构图 → 按特征估缩放+位移羽化贴回 |
| 断肢/藏手型渲染错误 | 提示词加 ANATOMY LOCK + 写死双臂各自用途 |
| 头身错位/撞脸他角 | 整页重出加 PROPORTION LOCK + FACE LOCK img2img 补刀 |

---

## 下一步

- 看发布交付 → [`docs/06-publishing.md`](06-publishing.md)
- 看经验教训 → [`docs/07-lessons-learned.md`](07-lessons-learned.md)
- 模板 → [`templates/`](../templates/)