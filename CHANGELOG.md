# Changelog

novel-to-comic 的版本变更记录。

## v1.0.0 · 2026-10-10 · 首次发布

从 5+ 个月的连载实战工程中提炼出的通用方法论与工具集。

### 包含

- **4 份子 skill**：
  - `novel-character-card` —— 角色定妆流水线
  - `novel-scene-card` —— 场景定妆流水线
  - `novel-episode-page` —— 单集出图流水线
  - `novel-qa-gate` —— QA 门禁流水线
- **4 个可复用工具**：
  - `bubble_lib.py` —— 气泡绘制公共库（方案A：画面/文字分离）
  - `qa_check.py` —— 7 项自动质检门禁
  - `check_refs.py` —— 引用断链体检
  - `compose_card.py` —— 角色卡拼装参考实现
- **6 个模板**（`templates/`）：
  - 角色卡配置 / 场景卡配置 / 单集节拍表 / 单页叠泡脚本 / 提示词骨架 / 发布文案
- **7 份文档**（`docs/`）：
  - 项目概览 / 端到端流水线 / 角色定妆体系 / 场景定妆体系 / 单集出图详解 / 发布交付详解 / 经验教训汇总
- **示例**：`examples/README.md` —— 通用落地步骤

### 验证状态

- ✅ `python3 tools/check_refs.py` —— 0 缺失
- ✅ `python3 tools/bubble_lib.py` —— 9 张气泡样张生成成功
- ✅ `python3 tools/qa_check.py --help` —— 命令行参数正确
- ✅ `python3 tools/check_refs.py --help` —— 命令行参数正确

### 已知限制

- 不含具体项目的角色定妆/场景定妆文件——这些是项目私有资产
- 不含 ImageGen 调用代码——本项目只提供提示词骨架，具体生图工具按需对接
- Q 版人物卡的拼装脚本未提供完整实现（每个项目的 Q 版规则不同）

### 计划

- v1.1：增加 Q 版拼卡的完整示例
- v1.1：增加视频漫剧子 skill
- v1.2：增加 Stable Diffusion / Midjourney 的提示词适配指南