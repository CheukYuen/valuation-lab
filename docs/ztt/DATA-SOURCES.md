# 中天科技数据来源与页码

## 来源登记

| ID | 来源 | 日期/期间 | 本地位置 | 已核验内容 | 当前等级 |
|---|---|---|---|---|---|
| Z1 | Morgan Stanley, *Preliminary 2Q26 slightly below expectations due to revenue recognition; strong 3Q26 outlook* | 2026-07-14 | `/Users/leon/Stock/investment-research-reports/downloads/2026/7月/7.16/大摩-中天科技（600522.SH）：2026年二季度业绩预告略低于预期，主因收入确认节奏；三季度前景强劲-260714.pdf` | p1经营更新和2025A-2028E预测；p2 DCF方法与参数；p3-8披露 | `BROKER-EST/PARTIAL` |
| Z2 | 中天科技2025年年度报告 | 2025A | `/Users/leon/Stock/investment-research-copilot/filings/fiber_industry/ztt_2025_annual.pdf` | p40-42分产品收入、成本、毛利率与成本结构；p123-124现金流；p243现金流补充资料 | `ACTUAL` |
| Z3 | 中天科技2026年半年度报告 | 2026H1 | `https://pdf.dfcfw.com/pdf/H2_AN202608271828544120_1.pdf`，由datahub公告端点取得 | p12 AI光纤出货、海外销售及MPO订单；p20利润表与现金流摘要；p54资本开支；p157现金流补充资料 | `ACTUAL` |
| Z4 | datahub A股取数器 | 2026-08-30 | `/Users/leon/Stock/investment-research-copilot/datahub/`；选用值固化于 [datahub_20260830_snapshot.json](datahub_20260830_snapshot.json) | `fetch_quote/profile/financials/estimates`及新浪三表：股价、股本、2026H1财务、一致预期、现金与债务 | `ACTUAL/CONSENSUS` |
| Z5 | AkShare主营构成快照 | 2026-08-15抓取，覆盖2024A-2025A | `/Users/leon/Stock/investment-research-copilot/research/company/yofc/20260815/raw/round2-repair/akshare-stock-zygc-em-600522.json` | 中天分产品收入、成本、毛利润和毛利率；与Z2第41页核对一致 | `ACTUAL` |
| Z6 | Morgan Stanley, *Optical fiber demand from AIDC tailwind confirmed* | 2026-06-08 | `/Users/leon/Stock/investment-research-reports/downloads/2026/6月/6.9/大摩-中天科技（600522.SH）：人工智能数据中心（AIDC）带动光纤需求上行趋势已确认-260608.pdf` | p1 AIDC客户需求、G.657/G.652产品结构、订单占比及CRU现货价；p2估值参数 | `BROKER-EST/PARTIAL` |
| Z7 | BofA Securities, *Strong guidance for more optical fiber & subsea cable upside* | 2026-08-28 | `/Users/leon/Stock/investment-research-reports/downloads/2026/8月/8.30/美银-中天科技（600522.SH）：强劲指引预示光纤与海缆业务有望进一步上行-260828.pdf` | p1经营观点、目标价与2024A-2028E摘要；p2三表预测；p3季度业绩与光纤价格；p4预测调整及当前价格SOTP；p5 DCF参数与风险 | `BROKER-EST/PARTIAL` |

## 页码地图

### Z1：摩根士丹利 2026-07-14

| 页码 | 可用内容 | 不可从该页推出的内容 |
|---:|---|---|
| 1 | 2026Q2预告、业务解释、现货价格方向、2025A-2028E收入/EBITDA/净利润/EPS、股价、市值、EV、目标价 | 分部收入预测、产品销量、具体ASP、Capex、营运资金 |
| 2 | DCF期间2027-2037、WACC、股权成本、税后债务成本、目标资本结构、永续增长率、风险 | 逐年FCFF、折现中点、终值现金流、净债务桥、目标股权价值表 |
| 3-8 | 评级定义、利益冲突与一般披露、目标价历史 | 新的经营或估值输入 |

### Z7：美银 2026-08-28

| 页码 | 可用内容 | 不可从该页推出的内容 |
|---:|---|---|
| 1 | 2026H1/Q2经营解读、光纤与海洋业务管理层沟通、目标价变动、2024A-2028E净利润/EPS/FCF与估值摘要 | 公司分部财务原表、65元完整DCF桥 |
| 2 | 2024A-2028E利润表、现金流、资产负债表和回报率预测 | 2029E-2035E自由现金流、终值现金流 |
| 3 | 2023Q1-2026Q2季度结果、分地区/规格光纤价格表 | 价格样本定义、公司实际综合ASP、价格向集团利润的完整传导 |
| 4 | 2026E-2028E新旧预测、历史P/E图、36.08元当前价格SOTP | 65元目标SOTP倍数、DCF企业价值与股权价值桥 |
| 5 | 2026E-2035E DCF、WACC 9%、永续增长3%、Beta 0.98及风险 | WACC底层资本结构、逐年FCFF、折现时点、目标净现金 |
| 6-9 | 指标定义、评级与利益冲突披露 | 新的经营或估值输入 |

## 证据规则

- `COMPANY-GUIDANCE`：券商报告转述的公司业绩预告或经营说明；未取得公司公告原文前仍是二手来源。
- `BROKER-EST`：摩根士丹利ModelWare预测、产业判断和目标价。
- `REFINITIV-CONSENSUS`：报告列示的Refinitiv EPS；样本、截点和统计方法未披露，故同时为 `PARTIAL`。
- `CONSENSUS`：datahub从同花顺取得的FY2026-FY2028 EPS均值、区间和机构数；不是公司指引。
- `DERIVED`：只使用报告可见数字和公开公式计算。
- `PROJECT-ASSUMPTION`：本项目为完成现金流桥而采用的税率、D&A、Capex、营运资金或延长预测；不是事实或一致预期。
- `PROJECT-VALUATION`：由上述事实、外部预测和项目假设共同计算的估值输出。
- `PARTIAL`：来源明确，但定义、上游证据或完整桥缺失。
- `MISSING`：报告没有提供复算所需输入。

当前已补公司年报、半年报和datahub快照。2026H1仍未披露分部财务，因此2026E分部利润桥保持 `MISSING`；本项目估值改用集团EBITDA与显式现金流假设，不把产品出货增速直接当作集团收入增速。

三情景校准也属于 `PROJECT-ASSUMPTION`：下行/上行EBITDA相对基准在2026E为95%/105%、2027E为85%/115%、2028E为80%/120%。2027E-2028E幅度参考Z4一致预期EPS最低值和最高值相对均值的离散度，但没有把EPS机械换算成EBITDA预测。
