# Claude 金融技能包（第三方快照 + 自学课程）

这个目录是 Anthropic 官方金融技能包的**只读快照**，加上一份把它当教材用的自学课程。

- `financial-analysis/`、`equity-research/` 两个子目录是**原样拷贝，不要改**——升级插件不会同步这里，改了也不生效。要改就复制到 `docs/` 下写成自己的版本。
- 这份 README 是自己写的，随便改。

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

`initiating-coverage` 的 6 个 references 文件另有 4500 行，是整个快照里最厚的一块：

| 文件 | 行数 | 内容 |
|---|---:|---|
| [task5-report-assembly.md](equity-research/skills/initiating-coverage/references/task5-report-assembly.md) | 1340 | 报告写作 |
| [task4-chart-generation.md](equity-research/skills/initiating-coverage/references/task4-chart-generation.md) | 920 | 25-35 张图表规格 |
| [task3-valuation.md](equity-research/skills/initiating-coverage/references/task3-valuation.md) | 698 | 估值执行 |
| [task2-financial-modeling.md](equity-research/skills/initiating-coverage/references/task2-financial-modeling.md) | 665 | 建模执行 |
| [task1-company-research.md](equity-research/skills/initiating-coverage/references/task1-company-research.md) | 456 | 公司调研 |
| [valuation-methodologies.md](equity-research/skills/initiating-coverage/references/valuation-methodologies.md) | 421 | **DCF / 可比 / 先例交易 三法教程** |

---

# 自学课程

## 怎么用这份课程

三条规矩：

1. **给的是锚点，不是摘要。** 每个模块只写「读哪个文件的哪几行 / 为什么读 / 读完做什么」。原文就在旁边，不要指望这里复述。
2. **练习落在你已有的文件上。** 中天科技和长飞光纤的数据你已经攒了大半年，别为了做练习另找标的。
3. **行号可信。** 这是冻结快照，`git` 里锁死了 commit，行号不会漂。

## 先划掉：你已经领先的部分

这四件事上材料没有比你现在做的更好的，别在上面花时间：

| 你已有的 | 材料里的对应物 | 判断 |
|---|---|---|
| [docs/yofc/09](../../docs/yofc/09-FOUR-BROKER-METHOD-COMPARISON.md)、[10](../../docs/yofc/10-FOUR-BROKER-INDUSTRY-COMPARISON.md) 四券商方法对比 | **没有** | 材料从不教「横向对比多家卖方的方法差异」。这是你自己长出来的功夫 |
| [lab/reverse.py](../../lab/reverse.py) + [FIVE-NUMBERS.md](../../docs/FIVE-NUMBERS.md)「反向 DCF 的正确读法」 | **没有** | 22 个 skill、13656 行里，reverse DCF 出现 **0 次**。你在这一点上超前于这份材料 |
| [docs/AUDIT-CHECKLIST.md](../../docs/AUDIT-CHECKLIST.md) 的「六道快速门 + 深入清单」两层结构 | audit-xls | 你的分层设计更好；它胜在 §3f/§3g 的具体 bug 清单（见课 D3） |
| ztt/yofc 的 Python + JSON 快照工作流 | openpyxl / Office JS 出 Excel | 两条路，各自成立，不必改 |

材料真正能给你的，是**「一份机构报告该有哪些部分、每部分多少字、哪些数字必须交叉验证」**这种交付纪律，以及几张现成的错误清单。

---

## A. 公司分析

主教材：[task1-company-research.md](equity-research/skills/initiating-coverage/references/task1-company-research.md)（456 行）

### A1 · 生意怎么赚钱

**读** `task1-company-research.md:87-111`（Step 2 Business Model Analysis）

四问：收入流怎么拆（卖什么、怎么定价、谁付钱、单笔多大）、客户分层（含**前十大客户集中度**）、渠道打法、单位经济（毛利率、留存、回收期）。

**为什么** 光纤光缆的定价机制是集采招标，「怎么定价」这一栏对中天和长飞的答案完全不同于材料默认的订阅制。照着填一遍，会逼出你平时跳过的问题。

**练习** 给中天科技填这四问，和 [docs/ztt/README.md](../../docs/ztt/README.md) 里已有的业务描述对照，看漏了哪一栏。

### A2 · 管理层与治理

**读** `task1-company-research.md:113-141`（Step 3）

每位高管 300-400 字：现任职责、前 2-3 段履历、可验证的成绩、任期。外加治理四项：董事会独立性、关键董事背景、**内部人持股比例**、薪酬结构。

**为什么** 这是国内散户投研最常整块跳过的一段，而它恰恰是判断「管理层承诺的产能扩张会不会兑现」的唯一依据。

**练习** 只做 CEO + CFO 两个人，各 300 字，来源限定在年报和公告。

### A3 · 竞争情报

**读** `task1-company-research.md:142-168`（Step 4）+ [competitive-analysis](financial-analysis/skills/competitive-analysis/SKILL.md)`:183-224`（Step 6 竞争者深挖、Step 7 对比矩阵）

竞争者要分三类：直接、间接（替代方案）、新兴（颠覆者）。**先去 10-K 看公司自己列的竞争对手名单**——A 股对应的是年报「行业竞争格局」章节。每家两张表：定量指标表 + 定性表（业务一句话 / 2-3 条优势 / 2-3 条劣势 / 当前战略）。

Step 7 的对比矩阵用 `●●● $160B` 这种写法——**评级后面必须跟实际数字**，只打点不给数是材料明令禁止的。

**练习** 中天 vs 长飞 vs 亨通，三家做 Step 6 的两张表 + Step 7 的对比矩阵。

### A4 · 风险清单

**读** `task1-company-research.md:195-230`（Step 6）

8-12 条风险，强制分四类配额：公司特有 4-6 条、行业 3-4 条、财务 2-3 条、宏观 2-3 条。每条 50-100 字，且要求「量化影响 + 判断概率 + 写出缓释因素」。

**为什么** 配额制是这一段的价值所在。不设配额，人只会写自己想得起来的那类风险——通常全是行业风险。

**练习** 给中天写满 12 条，检查你能不能凑够「财务风险」那 2-3 条。凑不出来说明三张表还没读透。

### A5 · 交付规格

**读** `task1-company-research.md:342-420`（Output Format）

9 个章节，每章明确字数：公司概览 800-1200、历史 800-1200、管理层 1000-1400、产品 700-1000、客户与渠道 500-700、行业 800-1200、竞争 700-1000、TAM 500-700、风险 600-900。

**当模板用就行**，不用真写 6000-8000 字。价值在于它告诉你各部分的**相对权重**——管理层那一章的篇幅居然和行业一样多。

---

## B. 行业分析

主教材：[sector-overview](equity-research/skills/sector-overview/SKILL.md)（88 行，全文都值得读）

### B1 · 行业骨架

**读** `sector-overview/SKILL.md` 全文

6 步：定范围 → 市场概览（规模/结构/趋势）→ 竞争格局 → 估值定位 → 投资含义 → 输出。

三条自带的警告值得抄进自己的清单：市场规模数据必须标出处；**区分 TAM 吹嘘和现实可及市场**；行业报告老化极快，必须标日期。

**练习** 照 6 步给「国内光纤光缆」写一份，深度取「5-10 页」档。Step 4「估值定位」直接引用你 [docs/yofc/10](../../docs/yofc/10-FOUR-BROKER-INDUSTRY-COMPARISON.md) 里的四券商行业判断。

### B2 · 行业指标先于一切

**读** `competitive-analysis/SKILL.md:109-136`（Step 0 行业定义性指标、Step 1 市场背景、Step 2 行业经济学）

Step 0 是整个 skill 里最该先做的一步：**这个行业到底靠哪 3-5 个指标运转？**表里给了 SaaS / 支付 / 市场平台 / 零售 / 物流五个样例。

Step 1 给了正反例，值得逐字看：

> 对：「嵌入式支付 2024 年 800-1000 亿美元，20-25% CAGR（麦肯锡 2024）」
> 错：「该市场规模庞大且增长迅速」

**练习** 写出光纤光缆的 3-5 个定义性指标。参考方向：集采中标价、光纤预制棒自给率、产能利用率、海外收入占比、单位光纤成本。写完拿去和 [docs/ztt/02-INDEPENDENT-VALUATION-WORKBENCH.md](../../docs/ztt/02-INDEPENDENT-VALUATION-WORKBENCH.md) 用的指标比对。

### B3 · 格局可视化与护城河

**读** `competitive-analysis/SKILL.md:163-182`（Step 4 分组、Step 5 可视化选型）+ `:225-252`（Step 9 综合）

Step 4 给了四种分组视角：按商业模式 / 按客户分层 / 按竞争姿态 / 按出身（在位者 vs 颠覆者）。Step 5 给了选型表：两个主导因素用 2×2、多因素用雷达、自然聚类用分层图、**垂直行业用价值链图**。

Step 9 的护城河四分类要求逐项打 强/中/弱：网络效应、转换成本、规模经济、无形资产（品牌/专有数据/牌照/专利）。

**练习** 给中天、长飞、亨通三家各打四项护城河评分，写明理由。这一项直接可以并进 [docs/ztt/02-INDEPENDENT-VALUATION-WORKBENCH.md](../../docs/ztt/02-INDEPENDENT-VALUATION-WORKBENCH.md)。

---

## C. 产业分析（材料最薄的一门，先看清楚缺口）

**先说结论：这 13656 行里，产业链分析基本是空的。** 全文搜 value chain 只有 4 处命中，每处一行：

| 位置 | 全部内容 |
|---|---|
| `competitive-analysis/SKILL.md:133` | 「垂直结构行业 —— 价值链分层，每层的典型利润率」 |
| `competitive-analysis/SKILL.md:178` | 选型表里一行：「价值链图 / 垂直行业」 |
| `sector-overview/SKILL.md:28` | 「价值链地图 —— 价值在哪里沉淀？」 |
| `idea-generation/SKILL.md:69` | 「拆解价值链 —— 谁直接受益、谁间接受益」 |

对「光棒 → 光纤 → 光缆」这条链、以及中天和长飞在链上位置的差异，材料给不出任何操作步骤。**这是你要自己补的一门。**

### C1 · 唯一有牙齿的一段

**读** [idea-generation](equity-research/skills/idea-generation/SKILL.md)`:64-73`（Step 3 主题扫描）

五步，是全部材料里唯一带方法的产业链思路：

1. 定义主题（如「AI 基建投资加速至 2026」）
2. **拆解价值链——谁直接受益、谁间接受益**
3. 区分纯正标的 vs 多元化标的
4. 判断哪些名字已经 priced in、哪些还没被认知
5. **找市场还没和主题连起来的二阶受益者**

注意它出现在一个**选股** skill 里，不是行业 skill 里。它的落点是「找票」，不是「理解产业」——你要借的是第 2、5 步的思路。

**练习** 以「800G 光模块放量」为主题跑一遍五步，看能不能推到光棒环节的二阶受益者。

### C2 · 用一层利润率把链条量化

**读** `competitive-analysis/SKILL.md:130-136`（Step 2 行业经济学）

只有 5 行，但给了三种行业结构对应的三种拆法：**垂直结构**看价值链分层 + 每层典型利润率；**平台/网络**看生态参与方与价值流向；**分散型**看整合动力与规模带来的利润率差。

光纤光缆是典型的垂直结构，所以走第一种：给「预制棒 / 拉丝 / 成缆 / 工程」每一层标出典型毛利率区间，就是一张最朴素但最有用的产业链图。

**练习** 画这张四层图，每层标毛利率。数据从中天、长飞、亨通、法尔胜的分部数据里凑。做完对照 [docs/ztt/03-FIBER-TO-ZTT-VALUATION-20260830.md](../../docs/ztt/03-FIBER-TO-ZTT-VALUATION-20260830.md)——你那份「从长飞到中天」的推演本质上就是产业链内的横向映射，材料里没有对应物。

### C3 · 缺口清单（自己补）

材料完全没有覆盖，但对光通信必需的：

- **纵向一体化程度如何影响估值**——中天与长飞的棒纤缆一体化率不同，材料没有任何框架处理
- **集采招标机制**下的价格传导与议价权分配
- **产能周期**：扩产决策 → 投产 → 价格下行的滞后结构
- **上游依赖**：四氯化硅、氦气等原料的供给约束

这四条建议写进你自己的 `docs/` 而不是等材料。

---

## D. 估值

主教材：[valuation-methodologies.md](equity-research/skills/initiating-coverage/references/valuation-methodologies.md)（421 行）——**整个快照里最好的一份文档**，三法教程齐全且互相咬合。

### D1 · 三法教程

**读** `valuation-methodologies.md` 全文，重点三段：

| 段落 | 行 | 内容 |
|---|---|---|
| DCF | 14-158 | 8 步流程 + 敏感性 + **149 行起的常见陷阱** |
| 可比公司 | 159-260 | 选样 → 取数 → 算倍数 → 选倍数 → 套用 + 溢价折价分析 |
| 先例交易 | 261-355 | 交易筛选、控制权溢价、倍数调整 |

**为什么** 比 `dcf-model/SKILL.md` 更适合学：那一份 1263 行里大半是 openpyxl/Office JS 的建表规范，这一份是纯方法。

### D2 · 三法怎么合成一个数（最值钱的一段）

**读** `valuation-methodologies.md:356-412`（Valuation Reconciliation）

三件事，材料里别处都没有：

**加权**：DCF 40-60%、可比 25-40%、先例交易 15-25%。且给了调权规则——对预测的信心越高 DCF 权重越高；成熟公司偏可比、成长公司偏 DCF；行业在整合期则抬高先例交易权重。

**区间而非点**：熊 38-40 / 基准 42-46 / 牛 48-52，目标价取基准中值。

**五道交叉验证**（`:402`）：与历史倍数比、与同业比（溢价折价说得通吗）、**市场现价隐含的增长是多少**、从现价到目标价的 IRR、总市值绝对数说不说得通。

**练习** 拿 [docs/yofc/09](../../docs/yofc/09-FOUR-BROKER-METHOD-COMPARISON.md) 里四家券商对长飞的方法，逐家标出他们隐含的三法权重，看有没有人落在 40-60 / 25-40 / 15-25 这个区间外，以及为什么。这是把你已有的对比工作再深一层的最快路径。

### D3 · 错误清单（最实用，直接并进自己的审计表）

**读** 三处，都很短：

1. [dcf-model](financial-analysis/skills/dcf-model/SKILL.md)`:717-757` —— TOP 5 错误 + 四类细分（WACC / 增长假设 / 终值 / 现金流投影）
2. [audit-xls](financial-analysis/skills/audit-xls/SKILL.md)`:89-99`（§3f 逻辑合理性）+ `:100-130`（§3g 分模型类型的 bug，DCF 那 5 条尤其值得记）
3. [comps-analysis](financial-analysis/skills/comps-analysis/SKILL.md)`:558-577`（Section 11 红旗清单，三类）

几条能直接变成断言的量化红线：

| 红线 | 出处 |
|---|---|
| 终值应占 EV 的 50-70%；>75% 黄旗；>80% 说明过度依赖终值 | `dcf-model:273-313`、`audit-xls:89` |
| 永续增长率 < WACC，且不得超过无风险利率或长期 GDP 增速 | `dcf-model:283-290` |
| FCF 必须是无杠杆的——含利息费用是常见错误 | `audit-xls:102` |
| 终值必须折现回来；折现期别搞错（期中 vs 期末） | `audit-xls:101-103` |
| WACC 用市值不用账面价值 | `dcf-model:728` |
| 税盾不得重复计算 | `audit-xls:105` |
| 营业费用按收入算，不按毛利算 | `dcf-model:704` |

**练习** 拿 [docs/ztt/ztt_datahub_20260830_valuation.py](../../docs/ztt/ztt_datahub_20260830_valuation.py) 的输出，逐条过上面 7 条红线。终值占比那条如果 [tests/test_ztt_datahub_valuation.py](../../tests/test_ztt_datahub_valuation.py) 还没断言，加一个。然后把这张表里 [docs/AUDIT-CHECKLIST.md](../../docs/AUDIT-CHECKLIST.md) 没有的条目补进去。

### D4 · 敏感性表的正确做法

**读** `dcf-model/SKILL.md:57-66`（Sensitivity Tables 约束）+ `:358-371`（Step 10）

一条设计规则值得学：**行列数取奇数（5×5 或 7×7），保证有真正的中心格；中心格的行列表头必须正好等于模型的实际假设，于是中心格算出的股价必须等于模型基准股价**——这是检验整张表建对没建对的自检机制。

**练习** 你的 Python 模型出敏感性表时，加一条断言：中心格 == 基准输出。

### D5 · 三表勾稽

**读** [audit-xls](financial-analysis/skills/audit-xls/SKILL.md)`:55-88`（§3b 资产负债表、§3c 现金流量表、§3d 利润表）+ [3-statement-model](financial-analysis/skills/3-statement-model/SKILL.md)`:298-330`（核心勾稽 + 符号约定）

必须恒成立的几条：资产 = 负债 + 权益（每期）；期初留存 + 净利 − 分红 = 期末留存；现金流量表期末现金 = 资产负债表现金（每期）；CFO+CFI+CFF = Δ现金；现金流量表的 D&A = 利润表的 D&A；资本开支与 PP&E 滚动一致。

**一条排序原则**：先看平不平。不平之前，下游一切结论都不可信。

---

## E. 持续跟踪（做完一轮之后）

三个小 skill，合起来是「覆盖一家公司之后怎么维护」：

| skill | 行数 | 拿它做什么 |
|---|---:|---|
| [thesis-tracker](equity-research/skills/thesis-tracker/SKILL.md) | 67 | 投资逻辑的记分卡：3-5 根支柱 + 每根的原始预期 / 当前状态 / 趋势 |
| [catalyst-calendar](equity-research/skills/catalyst-calendar/SKILL.md) | 84 | 催化剂日历：财报、投资者日、集采招标、锁定期解禁 |
| [model-update](equity-research/skills/model-update/SKILL.md) | 95 | 财报后更新模型：实际 vs 预估的差异表，再改前瞻 |

thesis-tracker 里有两句话值得单独抄下来：

> 一个逻辑必须是可证伪的——如果没有任何事能推翻它，那它不是逻辑。
>
> 追踪反证的严格程度，要和追踪正面证据一样。

**练习** 给中天写一份 thesis：一句话核心逻辑、3-5 根支柱、3-5 条会推翻它的风险、目标价、止损触发条件。这是把 [docs/ztt/](../../docs/ztt/) 那三份文档收口成一个可跟踪对象的动作。

---

## 六周推进顺序

| 周 | 内容 | 产出 |
|---|---|---|
| 1 | D1 + D2（三法教程 + 合成加权） | 给四券商标出隐含权重，接到 docs/yofc/09 |
| 2 | D3 + D4 + D5（错误清单、敏感性、勾稽） | 7 条红线跑一遍中天模型，补进 AUDIT-CHECKLIST |
| 3 | B1 + B2（行业骨架 + 定义性指标） | 光纤光缆行业 5-10 页 |
| 4 | C1 + C2 + C3（产业链，自己补缺口） | 四层价值链图 + 毛利率；缺口清单写进 docs/ |
| 5 | A1-A4（公司分析四段） | 中天：业务四问 + 高管两人 + 三家对比 + 12 条风险 |
| 6 | B3 + E（护城河评分 + thesis 收口） | 三家护城河评分表 + 中天 thesis 记分卡 |

估值放最前面，因为那是材料质量最高、和你现有工作衔接最紧的一门；产业分析放中间，因为那门主要靠自己写，需要前面两周攒的手感。

---

## 三个盲区（材料给不了，别指望）

### 1. 周期性

`dcf-model:1177-1181`「Cyclical Companies」只有 4 行：跨周期建模、按中周期正常化利润率、考虑谷底与峰值情景、调整 beta。方向对，但**没有任何操作步骤**。而光纤光缆是强周期——集采价格三年一轮——材料默认的「成熟稳定」档（`:1170`，3-5 年预测期、GDP+1-3% 增速、WACC 7-9%）套上去会系统性高估。这一块只能自己建。

### 2. A 股口径

- 估值主锚是 EV/EBITDA，不是 A 股常用的 PE/PB
- CAPM 用 10Y **美国**国债做无风险利率
- 永续增长率锚**美国** GDP
- 数据源假设是 SEC EDGAR 的 10-K/10-Q，不是巨潮资讯
- `.mcp.json` 里 11 个数据商（FactSet / Daloopa / Morningstar / S&P Global 等）均需付费订阅，A 股覆盖有限

### 3. 反向 DCF

全部 13656 行里出现 **0 次**。你的 [lab/reverse.py](../../lab/reverse.py) 和 [FIVE-NUMBERS.md](../../docs/FIVE-NUMBERS.md)「反向 DCF 的正确读法」在这一点上走在材料前面——它只教「算出一个目标价」，不教「从现价反推市场在假设什么」。

唯一沾边的是 `valuation-methodologies.md:407` 那半句「市场现价隐含的增长是多少」，被列为五道交叉验证之一。这是整套材料对反向思路的全部着墨。
