# Claude for Financial Services 技能包（第三方，只读参考）

这个目录是 Anthropic 官方金融技能包的**只读快照**，放进仓库是为了方便逐条阅读、grep、和自己的方法论对照。
**不要在这里改动**——升级插件不会同步这里，改了也不会生效。要改就复制到 `docs/` 下写成自己的版本。

## 来源

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/anthropics/financial-services |
| commit | `69cbc81467a5dced793eee03dec4658aa24ef856`（2026-08-24） |
| 快照日期 | 2026-08-30 |
| 许可证 | Apache-2.0，见 [LICENSE](LICENSE) |
| 插件版本 | financial-analysis 0.1.1 / equity-research 0.1.2 |

真正被 Claude Code 加载的副本在 `~/.claude/plugins/cache/claude-for-financial-services/`，
由项目级 `.claude/settings.json` 声明启用。这里的拷贝只供人阅读。

## 目录结构

每个插件下：

- `skills/<name>/SKILL.md` —— 真正的内容（工作流、检查清单、错误清单）
- `skills/<name>/references/` —— 分任务的长文档
- `skills/<name>/scripts/` —— 配套 Python 脚本
- `commands/<x>.md` —— 斜杠命令入口，通常只是「去加载某个 skill」
- `.mcp.json` —— 11 个数据商 MCP 连接（需各自订阅，A 股覆盖差）
- `hooks/hooks.json` —— 空占位

## 技能索引

### financial-analysis（估值与建模）

| skill | 行数 | 命令 | 说明 |
|---|---:|---|---|
| [dcf-model](financial-analysis/skills/dcf-model/SKILL.md) | 1263 | `/dcf` | DCF 全流程，10 步 + 错误清单 + 敏感性表规范 |
| [comps-analysis](financial-analysis/skills/comps-analysis/SKILL.md) | 661 | `/comps` | 可比公司分析，含分行业指标与红旗清单 |
| [3-statement-model](financial-analysis/skills/3-statement-model/SKILL.md) | 408 | `/3-statement-model` | 三表模型模板填充 |
| [competitive-analysis](financial-analysis/skills/competitive-analysis/SKILL.md) | 279 | `/competitive-analysis` | 竞争格局与市场定位 |
| [lbo-model](financial-analysis/skills/lbo-model/SKILL.md) | 274 | `/lbo` | LBO 模型 |
| [audit-xls](financial-analysis/skills/audit-xls/SKILL.md) | 156 | `/debug-model` | 模型审计：公式错误、平衡表勾稽、逻辑自检 |
| [deck-refresh](financial-analysis/skills/deck-refresh/SKILL.md) | 111 | — | 用新数据刷新既有材料 |
| [ib-check-deck](financial-analysis/skills/ib-check-deck/SKILL.md) | 78 | — | 材料交付前的数字一致性核对 |
| [clean-data-xls](financial-analysis/skills/clean-data-xls/SKILL.md) | 50 | — | 脏数据清洗 |
| [ppt-template-creator](financial-analysis/skills/ppt-template-creator/SKILL.md) | 254 | `/ppt-template` | 从 PPT 模板生成可复用 skill |
| [pptx-author](financial-analysis/skills/pptx-author/SKILL.md) | 43 | — | 无 Office 环境下生成 .pptx |
| [xlsx-author](financial-analysis/skills/xlsx-author/SKILL.md) | 42 | — | 无 Office 环境下生成 .xlsx |
| [skill-creator](financial-analysis/skills/skill-creator/SKILL.md) | 356 | — | 写 skill 的方法论（通用，非金融） |

### equity-research（股票研究）

| skill | 行数 | 命令 | 说明 |
|---|---:|---|---|
| [initiating-coverage](equity-research/skills/initiating-coverage/SKILL.md) | 783 | `/initiate` | 首次覆盖报告，5 个任务分步执行 |
| [earnings-analysis](equity-research/skills/earnings-analysis/SKILL.md) | 228 | `/earnings` | 季报点评，8-12 页 |
| [idea-generation](equity-research/skills/idea-generation/SKILL.md) | 114 | `/screen` | 选股筛选与想法来源 |
| [model-update](equity-research/skills/model-update/SKILL.md) | 95 | `/model-update` | 用新数据更新模型 |
| [morning-note](equity-research/skills/morning-note/SKILL.md) | 89 | `/morning-note` | 晨会纪要 |
| [sector-overview](equity-research/skills/sector-overview/SKILL.md) | 88 | `/sector` | 行业格局报告，6 步框架 |
| [catalyst-calendar](equity-research/skills/catalyst-calendar/SKILL.md) | 84 | `/catalysts` | 催化剂日历 |
| [earnings-preview](equity-research/skills/earnings-preview/SKILL.md) | 73 | `/earnings-preview` | 业绩前瞻情景 |
| [thesis-tracker](equity-research/skills/thesis-tracker/SKILL.md) | 67 | `/thesis` | 投资逻辑跟踪 |

## 先读哪几篇

按对本仓库的价值排序：

1. **dcf-model 第 717-757 行**——「常见错误」四类清单（WACC / 增长假设 / 终值 / 现金流），
   纯方法论，与数据源无关，最值得和 `docs/AUDIT-CHECKLIST.md` 逐条对照。
2. **dcf-model 第 273-313 行**——终值计算，含「终值应占 EV 的 50-70%，>75% 说明过度依赖终值」这条量化红线。
3. **sector-overview**——只有 88 行，是行业研究的骨架清单，可直接照着填。
4. **comps-analysis Section 10**（第 558 行起）——可比公司的红旗清单：数据质量、估值、可比性三类。

## 口径提醒

这套是美股投行范式，搬到 A 股要换锚：

- 估值主锚是 EV/EBITDA，不是 A 股常用的 PE/PB
- CAPM 用 10Y **美国国债**做无风险利率
- 永续增长率锚**美国** GDP，且默认标的是「成熟稳定」型，与光通信的强周期性不符
- 产出全是 Excel（openpyxl / Office JS），与本仓库 Python + JSON 快照的工作流是两套
- `.mcp.json` 里的 11 个数据商（FactSet / Daloopa / Morningstar / S&P Global 等）均需付费订阅，且 A 股覆盖有限
