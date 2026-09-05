# 行业概览数据与来源说明

研究及补数日期：2026-09-05；估值冻结日：2026-09-02。报告：[行业概览](REPORT.md)。本次先读取 yofc、ztt 资料，再按用户指定的 sector-overview 工作流补数；参考了 [Wind 技能能力清单](../../WIND-SKILLS-INVENTORY.md)。没有改动历史模型、重估目标价或提交 Git。

## 回执与采用规则

| ID | 原始文件 | 路径与期间 | 采用值及单位 | 不采用或限制 |
|---|---|---|---|---|
| W1 | [行业序列](raw/wind-industry-series.json) | Wind economic 指标；S0070683；2020-01 至 2026-07 | 中国光缆累计产量；元数据单位芯千米，除以 1e8 展示亿芯千米 | 其他返回指标并非全球需求；光缆线路长度的 magnitude 单位不清，未使用 |
| W2 | [同比序列](raw/wind-production-yoy.json) | Wind economic；S0070893 | 国家统计局累计同比 %；2025-12 −5.3%，2026-07 −9.8% | 不用总量差计算值覆盖可比口径同比 |
| W3 | raw/wind-{公司}-fundamentals.json | stock_data.get_stock_fundamentals；七家公司；2025A、2026H1 | 合并收入、反推法 EBITDA；回执亿元 | 严格选字段内报告期；历史行重复的新财务值不作历史序列；正反推法未完成完整桥 |
| W4 | raw/wind-{公司}-ev.json | stock_data.get_stock_fundamentals；2026-09-02 | 企业价值 EV，回执亿元；自行除以已接受的 2025A 财务 | 返回的“TTM”倍数多数实为 FY2025；H1收入误标TTM及少数股东损益误作权益均排除 |
| W5 | [指数回执](raw/wind-csi300.json) | Wind index；沪深300 | 定价日 P/E 13.642，仅供交叉核对 | 年末请求返回次年首个交易日，未用于历史图 |
| W6 | [新闻回执](raw/wind-market-news.json) | Wind financial_docs；2026-01-06等文章 | 年初 CRU 转引全球5.77、北美1.49、亚洲除中国0.71、西欧0.53亿芯千米 | NEWS-CITED/PARTIAL；不作为最新预测；预制棒150亿元、集中度80%等线索未升级为TAM或CR5 |
| W7 | [年报并购摘录](raw/wind-acquisitions.json) | Wind financial_docs；长飞2025年报及港股年报 | 奔腾激光2025-07-15收购60.76%；现金239959832元、预计补偿6154646元、合并成本233805186元、净资产份额212998053元 | 仅为供应商提取的公告文本；不据净资产比推导EV倍数；部分表格数值提取不完整 |
| C1 | [公司月末估值](raw/choice-peer-monthly.json) | Choice CSD；PETTM；2020-01-01至2026-09-02 | 七家公司567条记录，每家公司81日期；倍 | 固定样本，不是历史行业成分；估值算法可能有追溯更新，不保证当时可见数据 |
| C2 | [沪深300月末估值](raw/choice-csi300-monthly.json) | Choice CSD；000300.SH；PETTM；同上 | 81日期；定价日13.6582倍 | DelType=1不剔除；不与不同算法或Wind序列拼接 |
| C3 | [Choice估值快照](raw/choice-valuation.json) | Choice CSS；2026-09-02 | PETTM、PSTTM、COMPVALUE、EV2MRQ、EVTOEBITDAFT | EV原数值按与Wind亿元回执相差1e8核对，单位定义仍保留PARTIAL；不以跨源接近证明EV桥正确 |

公司文件名：yofc=601869.SH；ztt=600522.SH；hengtong=600487.SH；fiberhome=600498.SH；innolight=300308.SZ；accelink=002281.SZ；tfc=300394.SZ。原始回执未更改，归一化结果为 [sector_data.json](sector_data.json)，离线生成脚本为 [build_data.py](build_data.py)。

## 本地资料与证据等级

| 编号 | 文件及定位 | 本次用途 |
|---|---|---|
| L1 | [长飞财务指标](../../yofc/01-FINANCIAL-METRICS.md) | 2026H1三表、分部收入与现金流；ACTUAL与DERIVED分开 |
| L2 | [长飞来源账本](../../yofc/DATA-SOURCES.md) S1–S4及已锁定口径；[Task 1](../../yofc/14-INITIATING-COVERAGE-TASK1-COMPANY-RESEARCH-20260902.md) | 原报告链接、页码、股本；CRU转引来源与更细分产品缺口 |
| L3 | [Wind Comps](../../yofc/13-WIND-COMPS-20260902.md) | 9月2日价格、A/H股本汇率、H1冻结比率、2026E预测及P/E；预测样本PARTIAL |
| L4 | [中天来源账本](../../ztt/DATA-SOURCES.md) Z2、Z3、Z7；[中天入口](../../ztt/README.md) | 2025分产品收入；2026H1回款、AI经营进展；美银观点保留原日期 |
| L5 | [四家券商产业信息](../../yofc/10-FOUR-BROKER-INDUSTRY-COMPARISON.md) | 杰富瑞2026-07-22、高盛2026-08-28、野村2026-08-21、大摩2026-08-23；ASP、扩产、需求和份额预测 |
| L6 | [Wind DCF](../../yofc/12-WIND-DCF-20260902.md) | 仅说明旧模型的条件与限制；不重新估值 |

本次阅读范围文件名及 SHA256 位于 [source-inventory.json](raw/source-inventory.json)。该清单用于识别本地输入版本，不表示每个模型或外部PDF均重新逐格审计。原始报告页码延用本地已建立的来源账本；Wind公告文本为补充核对。

市场份额缺口包含：统一全球光纤销量份额及CR5、七家公司的各细分市场份额、时间序列及统一客户集中度。公司或券商引用的产能份额不能替代销售份额。“头部集中度”没有企业数也不能定义为CR5。

## 查询复现与完整性

本次追加的六家公司财务及六家公司EV请求逐字保存于 [requests.jsonl](raw/requests.jsonl)。首个长飞探针、经济数据、新闻和指数的部分逐字请求未单独持久化，因此**请求日志覆盖并不完整**；原始返回值已完整留存。以下为功能等价的复现规范，不冒充原请求日志。自然语言查询接口可能变更字段或返回内容，精确复算正文应优先读取已保存回执。

Wind CLI 在 `.agents/skills/wind-mcp-skill` 目录运行，使用 `node scripts/cli.mjs call <domain> <tool> '<json>'`，凭据由已有本机配置读取。财务域是 `stock_data`，工具是 `get_stock_fundamentals`，参数为 `question`。经济域与公告域的实际工具名应先按对应技能文档确认，不凭记忆构造；查询经济指标 S0070683、S0070893 的 2020-01-01 至 2026-09-05 序列，按回执日期与元数据筛选。行业检索尝试的原始候选见 [wind-indicator-search.json](raw/wind-indicator-search.json)。

Choice 使用本机已激活的 EMQuantAPI Python SDK。已阅读 css、csd 及相关指标文档；无额外账号注册或密钥写入。公司 CSD 参数为：

```python
codes = '601869.SH,600522.SH,600487.SH,600498.SH,300308.SZ,002281.SZ,300394.SZ'
c.csd(codes, 'PETTM', '2020-01-01', '2026-09-02',
      'Period=3,AdjustFlag=1,Order=1,Ispandas=1')
c.csd('000300.SH', 'PETTM', '2020-01-01', '2026-09-02',
      'Period=3,AdjustFlag=1,Order=1,DelType=1,Ispandas=1')
c.css(codes, 'PETTM,PSTTM,COMPVALUE,EV2MRQ,EVTOEBITDAFT',
      'TradeDate=2026-09-02,CurType=2,Type=1,Ispandas=1')
```

启动后应检查 c.start 的 ErrorCode；查询成功返回 DataFrame 时先检查返回类型，再按字段名取数；失败时保留错误码；最后 c.stop。本次保存的是 DataFrame reset_index 后的 JSON，CSD 日期形式为 YYYY/MM/DD，CSS 为 YYYY-MM-DD，图表转换日期分隔符但不改变日期。

## 计算及字段交叉核对

1. H1反推法 EBITDA 利润率使用 H1 EBITDA / H1收入，未混入全年分母。反推法含非经营项的影响，不能作为正常化 EBIT 利润率。
2. 2020—2025产量CAGR是端点绝对量的算术复合变化率。官方可比同比单独取数，不要求与绝对值机械相等。
3. Choice 2020—2025历史范围为72个月末点；全序列至9月2日为81点。七家公司每个日期齐全、P/E为正，组内中位数无需排除负值；样本选择偏差仍存在。
4. 供应商EV / 2025A EBITDA为重新明确分母的DERIVED/PARTIAL。部分原始“TTM营业收入”等于H1营业收入，排除。少数股东损益不是少数股东权益，排除。无法完整桥接的TTM估值保留MISSING。
5. Choice长飞EVTOEBITDAFT为90.7213，Wind为91.1163；本报告使用Wind EV / Wind 2025A EBITDA得到91.1163。不同供应商结果不平均。
6. Choice长飞PETTM为A股价格口径，而COMPVALUE为A/H混合市值。严禁拿两者直接相乘或反推同口径净利润。历史图只标长飞A股。
7. 本地2026E P/E是已有底稿四舍五入的冻结输入。页内另算“冻结市值/冻结预测净利润”校验，可能因精度有小差异；并未用9月5日新价格更新。
8. 全球旧预测地区瀑布只使用2026-01-06同一来源，剩余地区包括中国。最新6.7亿线索不参与旧地区分配。需求指数只是按CAGR的演示，不是新增公司收入预测。
9. 中天2025五个主要分部收入合计512.01亿元，补其他及差额12.9886亿元后与总收入524.9986亿元衔接，未将未列项消失。
10. 奔腾浙江支付金额减预期补偿资产等于会计合并成本，后者减可辨认净资产份额等于商誉；1.10倍不标为交易EV倍数。

## 技术与监管网页

- ITU G.657：[正式标准](https://www.itu.int/rec/t-rec-g.657)。核对弯曲不敏感单模光纤标准属性，未将其视为AI专属。
- 欧盟2023年措施：[欧盟委员会公告](https://policy.trade.ec.europa.eu/news/eu-tightens-anti-dumping-measures-optical-fibre-cables-china-defend-significant-eu-industry-2023-08-09_en)。39.4%—88%仅指该历史公告。
- 欧盟2025年印度措施：[欧盟委员会公告](https://policy.trade.ec.europa.eu/news/eu-acts-against-unfairly-subsidised-optical-fibre-cables-india-2025-06-11_en)。未据此断言2026年所有企业现行综合税率。

## 更新顺序

先补同口径全球销量、收入和CR5，再补逐厂有效产能、公司实际ASP与客户认证；最后补完整TTM EV桥和预测机构分布。若后续仍无法通过专项Wind或Choice路径取得，可按用户给出的技能清单研究Alice市场规模或可比公司工作流。本次未调用Alice，也没有把新闻转引的总量当作已验证的全球数据库。

## 投行研报补充

按用户补充要求，将五家投行的六份本地研报案例单独纳入 HTML 第12节及 页内“投行研报”表。数据见 [broker_data.json](broker_data.json)，原报告来源及页码在长飞与中天来源账本中，当前报告只做原时点对照，不重新校准目标价。

| ID | 投行与公司 | 报告日期 | 本地案例与原表位置 | 采用口径 |
|---|---|---|---|---|
| B1 | 杰富瑞 长飞 | 2026-07-22 | [杰富瑞案例](../../yofc/04-JEFFERIES-20260722-CASE.md)及[预测汇总](../../yofc/09-FOUR-BROKER-METHOD-COMPARISON.md) §2 | 2026E—2028E收入与净利润；153.74港元SOTP目标价 |
| B2 | 高盛 长飞 | 2026-08-28 | [高盛案例](../../yofc/06-GOLDMAN-20260828-CASE.md) | 2026E—2028E收入与净利润；292港元折现P/E目标价 |
| B3 | 野村 长飞 | 2026-08-21 | [野村案例](../../yofc/07-NOMURA-20260821-CASE.md) | FY27 EPS 9.75元及23.7倍；266港元目标价；年度收入和净利润缺失 |
| B4 | 大摩 长飞 | 2026-08-23 | [大摩案例](../../yofc/08-MORGAN-STANLEY-20260823-CASE.md) | ModelWare净利润；230港元RIM目标价 |
| B5 | 大摩 中天 | 2026-07-14 | [大摩案例](../../ztt/01-MORGAN-STANLEY-20260714-CASE.md) §3—5 | ModelWare净利润、EBITDA、53.23元DCF目标价 |
| B6 | 美银 中天 | 2026-08-28 | [美银案例](../../ztt/04-BOFA-20260828-CASE.md) §3—5 | 调整后净利润、EBITDA、65元DCF目标价 |

财务原表单位为人民币百万元，本次除以100转为亿元，未把EPS或港元目标价作同样转换。各家利润调整及EPS股本分母不完全相同；图8只表示报告各自的盈利路径，不能称为同口径共识区间。美银与大摩的2027E收入差异为839.24/722.52−1≈16.2%，净利润差异为130.99/83.06−1≈57.7%；后者同时含预测、调整口径和信息集差异。

最终交付 [HTML 报告](index.html)，八张图表使用内嵌 SVG，可离线阅读；六张完整数据表、379个公式、143条来源批注及文本回执均内嵌页面。旧 Excel 与 PNG 仅作核对档案，不参与正常构建。Markdown是正文来源，不再交付Word。

## P0 增补证据与核验（2026-09-05）

新增证据详见 `p0_data.json`，各来源记录本地PDF路径、报告日期、已阅读相关页及SHA256。原五份报告外，补读野村7月集采、高盛古河扩产、康宁与日本同业、摩根大通运营商Capex、美银电子材料p9–10、野村太辰光及高盛长飞7月报告。检索摘要未作为正式数字来源。

四次Wind专项请求逐字存于 `raw/p0-requests.jsonl`。移动公告检索返回不相关半年报/股息，古河公告无结果，中天摘要未支持具体扩产数字；均不做已核验声明。移动新闻检索仅作为NEWS-CITED：6922.20万芯千米、9个月、71亿元不含税折扣前总额。总额均摊约102.57元不能替换高盛80元线索；原始标书/价格覆盖范围仍缺失。

校正与保留：美银G652.A1/A2型号不静默更名；高盛85.7元月份按p2图定位8月、保留p1文字May冲突；杰富瑞SDGI不再未经核实译为山东玻纤；杰富瑞87%/85%产能覆盖率与消除短缺叙事的解释缺口保留。中天850吨与800–1000吨不累加，古河带状光缆翻倍不当作预制棒吨数。每项价格与成本都保持其产品、期间、币种、税口径与预测性质。
