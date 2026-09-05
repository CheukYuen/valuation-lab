# 万得 Skill 生态盘点：目录里有什么，本机能用什么

> 调查日期：2026-09-05 ｜ 方法：在独立 git worktree 中重装 `wind-find-finance-skill`
> 读取其 catalog，并对 `wind-alice` 做本地实测。worktree 已销毁，主仓库未被污染。

---

## 一句话结论

`wind-find-finance-skill` 的 catalog 列了 **77 个可装 skill**，但那是一份**购物清单，不是库存清单**——本机实际装了 **3 个**（`wind-mcp-skill`、`wind-alice`、`dcf-model`）。另外 74 个只是名字，不构成当前可用能力。真正**现在就能调**的分析能力，集中在 `wind-alice` 的 **14 个子 Skill** 里。

> 修正：之前口头说过"约 90 个"，那是目测。实际去重后是 77 个（原始表格 78 行，`wind-alice` 在两节各列一次）。

---

## 一、catalog 里到底有什么

### 总量与结构

| 分区 | 数量 | 性质 |
| --- | ---: | --- |
| 数据类（取数 / 查询） | 3 | 数据底座 |
| Avatar 思维框架 | 4 | 人物视角分析框架 |
| 工作流类（决策 / 分析） | 70 | 具体分析任务 |
| **合计（去重）** | **77** | |

**只有 3 个需要额外配置**，其余 74 个装完即用：

| skill | 需要什么 |
| --- | --- |
| `wind-mcp-skill` | API Key |
| `wind-alice` | API Key（与上者共用同一个 `WIND_API_KEY`） |
| `tushare-finance-skill` | 依赖 + Token |

### 本机安装状态：77 选 3

| skill | 状态 |
| --- | --- |
| `wind-mcp-skill` | ✅ 已装，已实测可用 |
| `wind-alice` | ✅ 已装，已实测可用 |
| `dcf-model` | ✅ 已装 |
| 其余 74 个 | ❌ 未装 |

**这个落差是本报告最重要的一条。** catalog 是随 skill 包发布的静态文本快照，列出名字不等于具备能力。看到 `backtest-expert`、`valuation-pricing-framework` 出现在清单里，不代表本机能跑回测或估值框架——它们从未被安装过。

### 数据类（3 个）

| skill | 能力 |
| --- | --- |
| `wind-mcp-skill` | 万得金融数据：A 股 / 港股股票（行情 + 财务）、ETF / 公募基金、公司公告、财经新闻、宏观经济指标 |
| `wind-alice` | Alice 综合分析入口，详见第二节 |
| `tushare-finance-skill` | Tushare Pro：A 股、港股、美股、基金、期货、债券、财务报表与宏观 |

### Avatar 思维框架（4 个）

用人物视角切问题，全部无需配置。

| skill | 视角 |
| --- | --- |
| `avatar-charlie-munger-thinking` | 芒格：逆向思考、激励分析、多学科模型、认知偏误叠加 |
| `avatar-warren-buffett-investing` | 巴菲特：能力圈、护城河、管理层诚信、所有者收益、安全边际 |
| `avatar-nassim-taleb-risk` | 塔勒布：尾部风险、出局风险、利益共担、杠铃策略、脆弱性 |
| `avatar-naval-ravikant-thinking` | 纳瓦尔：特定知识、杠杆、长期复利、职业与人生决策 |

### 工作流类（70 个，按 category 分组）

#### 市场主线  (13)

| skill | 能力 |
| --- | --- |
| `a-share-primary-theme-identification` | A 股市场主线识别(题材周期 / 资金行为) |
| `market-environment-analysis` | 全球市场环境分析(risk-on / risk-off) |
| `theme-detector` | 跨板块主题检测(FINVIZ + 生命周期) |
| `sector_rotation_radar_skill` | 识别板块强弱切换、资金迁移与风格变化，服务市场主线判断 |
| `market_regime_switch_skill` | 判断市场处于进攻、防守、震荡或切换阶段，服务总仓位与风格判断 |
| `institutional_position_shift_skill` | 识别机构持仓变化与共识迁移，服务季报持仓研究 |
| `industry_chain_signal_skill` | 从产业链上下游景气、价格、订单、库存与盈利变化中识别机会与风险 |
| `macro_event_market_impact_skill` | 解读利率、通胀、就业、增长等宏观事件对股市、风格和行业的影响路径 |
| `market_breadth_health_skill` | 判断指数涨跌背后是否有足够市场广度支撑，识别健康扩散、局部抱团或虚弱反弹 |
| `market_sentiment_temperature_skill` | 量化市场情绪冷热、风险偏好与交易拥挤度，辅助仓位和节奏判断 |
| `northbound_capital_flow_skill` | 追踪北向资金或外资偏好的变化、行业流向与风格迁移 |
| `policy_headline_interpreter_skill` | 解读政策新闻对行业、题材和个股的影响路径、受益方向与执行不确定性 |
| `theme_heat_tracker_skill` | 跟踪主题题材热度变化、扩散层级、拥挤程度与持续性 |

#### 个股研究  (11)

| skill | 能力 |
| --- | --- |
| `equity-investment-thesis` | 个股投资逻辑深度研究(券商研究员风格) |
| `bull_bear_case_builder_skill` | 同步搭建看多与看空逻辑，压缩确认偏误并找出核心分歧 |
| `peer_comparison_decision_skill` | 横向比较候选公司质量、成长、估值与催化，辅助二选一 |
| `moat_strength_review_skill` | 评估公司竞争优势是否真实、可持续且能转化为回报 |
| `business_model_decoder_skill` | 把公司如何获客、赚钱、扩张和受限讲清楚 |
| `growth_quality_check_skill` | 拆解公司增长来源，检查盈利含量、现金含量、可持续性与失速风险 |
| `hot_stock_quick_read_skill` | 在极短时间内解释热门股的业务、催化、市场预期、资金关注点与主要风险 |
| `management_quality_check_skill` | 检查管理层背景、激励机制、资本配置、治理质量与潜在红旗信号 |
| `stock_first_look_skill` | 首次接触个股时，快速建立业务、市场关注点、关键指标、估值位置与主要风险认知 |
| `stock_research_memo_writer_skill` | 生成结构化、可分享的个股研究备忘录，沉淀投资逻辑、核心分歧、估值判断与风险 |
| `turnaround_story_validation_skill` | 验证困境公司是否真的出现反转证据，拆解修复路径、时间窗口、失败边界与赔率条件 |

#### 事件/公告/财报文档  (11)

| skill | 能力 |
| --- | --- |
| `major_announcement_impact_skill` | 分析并购、减持、定增等重大公告的核心影响，服务突发事件判断 |
| `conference_call_takeaway_skill` | 提炼业绩会关键信息、管理层表态和警讯，服务会后快速吸收要点 |
| `guidance_change_impact_skill` | 解释业绩指引上修下修的含义、可信度与后续影响 |
| `sec_filing_question_answer_skill` | 从 10-K、10-Q、招股书等长文档中精准答疑，服务监管文件快读 |
| `buyback_program_reviewer_skill` | 判断回购计划的规模、动机、执行约束与真实利好程度 |
| `dividend_change_explainer_skill` | 解读分红提升、削减、暂停或恢复背后的原因、持续性与投资含义 |
| `earnings_calendar_planner_skill` | 按时间轴组织财报季中的重点公司、前后任务、优先级与提醒 |
| `earnings_preview_skill` | 财报前梳理市场预期、关键看点、验证指标、情景推演与风险点 |
| `earnings_reaction_interpreter_skill` | 解读财报发布后的涨跌反应、超预期来源、市场真实分歧与后续观察点 |
| `shareholder_letter_digest_skill` | 总结股东信中的长期战略、经营变化、资本配置与管理层信号 |
| `trading_halt_resume_tracker_skill` | 跟踪停牌、临停、复牌事件的原因、进展、潜在影响与复牌后观察框架 |

#### 交易执行  (10)

| skill | 能力 |
| --- | --- |
| `trade_plan_builder_skill` | 下单前生成包含入场、仓位、止损止盈的完整计划 |
| `stop_loss_discipline_skill` | 设计价格、逻辑、时间三类止损规则与执行动作 |
| `take_profit_ladder_skill` | 为盈利仓设计分层兑现、保本上移与尾仓持有规则 |
| `breakout_trade_execution_skill` | 围绕突破交易制定从观察、触发、跟进到失效处理的落地执行方案 |
| `dip_buy_decision_skill` | 判断下跌或回调中的个股是否值得承接，并给出观察区、试错条件、分批节奏与放弃标准 |
| `failed_breakout_exit_skill` | 识别突破失败、冲高回落与关键位失守后的撤退信号，并给出减仓、止损与重新观察顺序 |
| `premarket_trade_checklist_skill` | 开盘前核查候选交易的催化剂、流动性、计划完整性、环境适配与风险暴露 |
| `price_target_reach_alert_skill` | 当股价接近、触达或穿越目标价时，生成分批处理、继续持有或重新评估建议 |
| `support_break_warning_skill` | 围绕支撑位、压力位、前高前低、趋势线等关键价格位置生成预警与应对提示 |
| `trim_or_hold_decision_skill` | 在持仓明显盈利或短期大涨后，判断应部分兑现还是继续持有 |

#### 选股  (9)

| skill | 能力 |
| --- | --- |
| `breakout_candidate_finder_skill` | 筛选形态成熟、放量待发的突破候选股，并给出触发条件 |
| `pullback_opportunity_finder_skill` | 寻找回调充分但趋势未破坏的候选股，定位低吸观察区 |
| `high_quality_compounder_finder_skill` | 筛选高 ROE、高护城河、可长期复利的核心候选股 |
| `canslim_growth_scan_skill` | 依据 CANSLIM 成长股框架批量筛选业绩、预期、相对强度与供需结构共振的强势标的 |
| `dividend_growth_entry_skill` | 寻找股息持续增长、经营质量稳定且估值回落到合理区间的候选股 |
| `earnings_momentum_setup_skill` | 寻找财报发布后业绩与指引共同强化、量价表现积极、具备继续上行动能的机会股 |
| `pead_opportunity_skill` | 识别财报后漂移行情中值得跟踪的中短线机会，判断预期修正、价格延续与失效边界 |
| `value_dividend_candidate_skill` | 筛选估值具备安全边际、股息有吸引力且分红可持续的收益型股票 |
| `vcp_breakout_scan_skill` | 筛选波动逐级收缩、抛压减弱、结构趋于成熟的突破预备股 |

#### 估值  (3)

| skill | 能力 |
| --- | --- |
| `dcf-model` | DCF 估值建模(WACC + 敏感性分析) |
| `valuation-pricing-framework` | 估值与定价框架(重估空间判断) |
| `valuation_snapshot_skill` | 快速判断个股估值高低、所处分位与重估触发条件 |

#### 复盘/自选股  (3)

| skill | 能力 |
| --- | --- |
| `after_close_watchlist_recap_skill` | 收盘后总结自选股当日表现、驱动因素、强弱分化与次日观察点 |
| `daily_watchlist_morning_brief_skill` | 为自选股生成盘前简报，汇总隔夜公告、新闻、价格变化、事件日程与今日观察重点 |
| `watchlist_news_impact_digest_skill` | 汇总自选股在指定时间窗口内的重要新闻、公告与舆情变化，并判断影响方向 |

#### 盘中异动/交易判断  (3)

| skill | 能力 |
| --- | --- |
| `gap_open_interpreter_skill` | 解读高开、低开、跳空缺口背后的预期差、事件含义与日内风险点 |
| `intraday_abnormal_move_alert_skill` | 识别盘中急拉、急跌、放量、换手突变等异常波动，并解释可能驱动与持续性 |
| `volume_spike_reasoning_skill` | 对股票盘中或日内放量异动进行归因，判断消息驱动、资金行为、情绪扩散或技术性放量 |

#### 交易执行/仓位  (2)

| skill | 能力 |
| --- | --- |
| `position_sizing_decision_skill` | 按风险预算和波动水平给出单笔仓位与分批建议 |
| `add_to_winner_decision_skill` | 判断盈利仓是否适合继续加仓，并给出加仓前提、节奏安排、保护规则与停止扩张边界 |

#### 估值-季报  (1)

| skill | 能力 |
| --- | --- |
| `earnings-analysis` | 季报点评(beat/miss + 估值更新) |

#### 复盘  (1)

| skill | 能力 |
| --- | --- |
| `post-market-debrief` | 盘后复盘(市场全景 / 主线轮动) |

#### 仓位  (1)

| skill | 能力 |
| --- | --- |
| `position-sizer` | 仓位管理(风险 / Kelly / ATR) |

#### 回测  (1)

| skill | 能力 |
| --- | --- |
| `backtest-expert` | 量化策略系统化回测(压力测试) |

#### 市场主线/选股  (1)

| skill | 能力 |
| --- | --- |
| `theme_leader_identification_skill` | 识别热门题材中的龙头、中军和跟随股，判断谁最值得跟踪 |

---

## 二、wind-alice 有什么能力

与 catalog 里那 74 个"名字"不同，本节列的能力**现在就能调用**——已用两次真实往返验证（鉴权、SSE 流式、artifact 解析、退出码全部正常）。

### 它是什么

万得 Alice 专业金融分析 Agent 的命令行客户端：走 A2A 协议 + SSE 流式，把「用户问题 + 指定子 Skill」送到 Alice 服务端，拉回 `agentResult.value`。它**不是本地分析器**，是远端 Agent 的一个瘦客户端。

### 14 个子 Skill

这些子 Skill **不单独安装**，全部由 `wind-alice` 一个包承载。

#### 个股 / 公司研究

| 中文名 | 英文名 | 能力 |
| --- | --- | --- |
| 公司一页纸 | `Company One-Page Investment Memo` | A/港/美股一页纸投资报告：汇总财务、研报观点、公告、新闻，输出公司速览、投资逻辑、催化剂、跟踪指标、估值、风险与操作建议。适用于晨会、投决会、调研前 |
| 上市公司调研问题清单 | `Stock DD List` | 买方视角调研清单：数据驱动的看多/看空摘要 + 3-5 个深度议题的管理层提问 |
| 全球上市公司季报点评 | `Global Share Quarterly Earnings Review` | 卖方研究风格财报点评，「标题 + 五段式正文」一页纸；覆盖 A/港/美/欧，适配本地披露规则，可识别业绩快报场景 |
| 可比公司分析 | `Comps Analysis` | 机构级 Comps：经营指标、估值倍数对比、统计基准分析，输出 Excel + 文字报告 |

#### 选股 / 主题

| 中文名 | 英文名 | 能力 |
| --- | --- | --- |
| 按主题选股 | `Thematic Stock Screening` | 拆解市场交易主线，用关键数据验证逻辑兑现度，筛出真正受益标的，附估值历史分位与交易视角建议 |
| 投资标的创意与筛选 | `Investment Idea Generation` | 全市场机会发掘：量化因子（价值/成长/质量/做空/特殊事件）+ 主题扫描，可指定行业、市值、地区、风格 |

#### 基金

| 中文名 | 英文名 | 能力 |
| --- | --- | --- |
| 基金对比分析 | `Fund Compare` | 多只基金全维度对比：业绩、风险、持仓结构、管理评估；支持客观中立或倾向性分析 |
| 基金筛选与投资建议 | `Fund Screening & Investment Advisory` | 投顾视角：按风险偏好、目标、期限筛基金，产出结构化报告与配置建议，匹配投资者画像 |

#### 宏观 / 债券 / 信用

| 中文名 | 英文名 | 能力 |
| --- | --- | --- |
| 宏观数据解读 | `Macro Data Interpretation` | CPI、PPI、PMI、GDP、社融、外贸、失业率、利率等解读为研究周报式分析 |
| 债券利率走势研判 | `Bond Rate Outlook` | 自适应交易（1-2 周）/ 策略（1-6 月）/ 配置（6 月-2 年）三视角，覆盖宏观、流动性、供需、曲线、技术情绪五维度 |
| 信用分析 | `Credit Analysis` | 主体信用、行业风险、财务健康度、现金流质量、评级对标、违约概率建模，集成 Wind 风险评分 |
| 通胀情景债券轮动策略 | `Inflation Bond Strategy` | 追踪 CPI/PPI 四种通胀拐点信号，做债券/货基切换或 5/7/10 年国债久期轮动，含风险预算优化与历史净值回测 |

#### 战略 / 核查

| 中文名 | 英文名 | 能力 |
| --- | --- | --- |
| 市场规模测算与战略建模 | `Market Sizing & Strategic Modeling` | 市场定义、需求拆解、关键驱动、Top-down/Bottom-up/交叉验证、历史回溯、增长预测、情景与敏感性分析 |
| 事实核验 | `Fact Check` | 粘贴一段含金融数据/公司声明/行业事件的文字，逐点验证并生成结构化核查报告 |

### 调用契约（实测确认）

```bash
cd .agents/skills/wind-alice
node scripts/wind-alice.mjs --prompt "<用户原话>" --skill "<中文或英文 Skill 名>"
node scripts/wind-alice.mjs list-skills     # 列出全部子 Skill（离线，不需要 Key）
```

几条容易踩的规矩：

- **`--skill` 收的是名称，不是 id。** 中文名、英文名、口语别名（`一页纸`、`季报点评`、`comps` 等）都能匹配；英文部分忽略大小写与空格/连字符/下划线。
- **Skill 选择靠 prompt 前缀实现**，不是靠 `selectedSkillIds`。CLI 按问句语言拼 `使用「<中文名>」技能：` 或 `Using "<英文名>" skill:`。
- **必须原样传用户问句**，不要改写、翻译或只提取股票代码——前缀由 CLI 负责拼，问句本身要保持原样。
- **不传 `--skill` 走 auto 路由**，适合普通金融问答。
- **耗时数分钟到十几分钟，且消耗积分。** 中途不要取消或重复发起。
- 产出的附件（一页纸、Comps 的 Excel 等）由 CLI 自动下载到 `.agents/download/`（已加入 `.gitignore`）。
- 密钥：与 `wind-mcp-skill` 共用 `WIND_API_KEY`，已配置在 `~/.wind-aifinmarket/config`，无需 export。

### 定位：兜底，不是首选

按 `wind-mcp-skill` 的规定，Alice 是**最后兜底**——只有当所有专项 Wind 路径都因数据覆盖、字段不可用、口径不匹配而失败，且向用户说明后，才把原始问题转交。不能拿它顶替专项取数。

---

## 三、发现的问题

### catalog 的 `fsi-comps-analysis` 与 CLI 对不上

catalog 的「Alice 子 Skill 索引」把可比公司分析的英文名写成 **`fsi-comps-analysis`**，但 CLI 里：

- `grep` 全部脚本，该字符串出现 **0 次**；
- CLI 的 `KNOWN_SKILLS` 用的是 **`Comps Analysis`**（中文名「可比公司分析」）；
- 别名表只认 `可比分析` 和 `comps`。

按 SKILL.md 描述的行为，未命中的名称会走 `[warn]` 分支、把字面值直接拼进 prompt 前缀提交。**此处未实测**（一次真实调用要花几分钟且消耗积分），所以只能说它会告警并提交一个 Alice 可能不认识的前缀，不能断言它一定失败。

**建议**：子 Skill 名一律以 `node scripts/wind-alice.mjs list-skills` 为准，不要照抄 catalog。

### catalog 是静态快照，会过时

`references/skills-catalog.md` 随 skill 包发布，不是实时查询。本次重装拿到的版本与删除前的完全一致（`diff` 确认无差异），说明远端近期没更新。上面那个名字不一致，就是快照与实现漂移的直接证据。

---

## 四、装与不装

> **状态更新**：本报告调查期间，另一会话以 `e7d08b4` 把 `wind-find-finance-skill` 恢复到了 main 并在 CLAUDE.md 补回条目。
> 所以它当前**在仓库里**。以下讨论对"装回来"与"再删掉"两种选择都成立。

`wind-find-finance-skill` 是纯路由器，不含任何子 skill——删掉不损失能力，留着的价值是那份 catalog 加上「未装就不许降级分析」的硬门禁。本报告已把 catalog 的内容固化下来，所以即使再删一次，清单也不会丢。

注意 `e7d08b4` 补回的 CLAUDE.md 条目写的是「约 90 个可装 skill」，本报告实测为 **77 个**，建议以此为准。

需要装 catalog 里某个 skill 时，直接：

```bash
npx skills add Wind-Information-Co-Ltd/wind-skills --skill <name> -y
```

（国内网络把 source 换成 `https://gitee.com/wind_info/wind-skills.git`；加 `-g` 装到全局。）
