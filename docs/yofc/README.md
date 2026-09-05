# 长飞光纤估值实战

这里只放真实案例的学习内容和计算结果。方法先讲 `What → Why → How`，然后立即代入长飞光纤的公开数据。

## 已完成

1. [从三张报表到常用财务指标](01-FINANCIAL-METRICS.md)
2. [数据来源与页码](DATA-SOURCES.md)
3. [分部预测与 DCF](02-FORECAST-AND-DCF.md)
4. [相对估值、反向 DCF 与 PEG](03-RELATIVE-REVERSE-PEG.md)
5. [杰富瑞 2026-07-22 研报案例](04-JEFFERIES-20260722-CASE.md)
6. [杰富瑞估值方法与现有案例对比](05-JEFFERIES-METHOD-COMPARISON.md)
7. [高盛 2026-08-28 研报案例](06-GOLDMAN-20260828-CASE.md)
8. [野村 2026-08-21 研报案例](07-NOMURA-20260821-CASE.md)
9. [摩根士丹利 2026-08-23 研报案例](08-MORGAN-STANLEY-20260823-CASE.md)
10. [四家券商估值方法与本项目对比](09-FOUR-BROKER-METHOD-COMPARISON.md)
11. [四家券商产业信息对比](10-FOUR-BROKER-INDUSTRY-COMPARISON.md)
12. [2026-08-28 反向 DCF 实战](11-REVERSE-DCF-20260828.md)
13. [最小可复算估值模型](valuation_model.py)
14. [WACC 推导（CAPM、Beta 回归）](cost_of_capital.py)
15. [Beta 回归价格快照](beta_20260824_snapshot.json)
16. [2026-08-28 反向 DCF 复算](reverse_dcf_20260828.py)
17. [杰富瑞 SOTP 独立复算](jefferies_20260722_model.py)
18. [高盛折现 P/E 独立复算](goldman_20260828_model.py)
19. [野村 FY27 P/E 独立复算](nomura_20260821_model.py)
20. [摩根士丹利 RIM 可见输入复核](morgan_stanley_20260823_model.py)
21. [2026-09-02 Wind 数据独立 DCF](12-WIND-DCF-20260902.md)
22. [2026-09-02 Wind 可比公司与 DCF 交叉分析](13-WIND-COMPS-20260902.md)
23. [Task 4 离线研究图册](17-INITIATING-COVERAGE-TASK4-CHART-GENERATION-20260902.html)
24. [Task 5 完整研究报告（HTML）](18-INITIATING-COVERAGE-TASK5-REPORT-ASSEMBLY-20260902.html)

## 后续顺序

1. 补齐定价日中国 10 年期国债收益率和股权风险溢价的原始来源，把 WACC 从 `PARTIAL` 升级为已验证输入
2. 补充可公开复核的市场一致预期
3. 补充ASP、有效产能、招标量、Capex时序和营运资金的原始证据
4. 把实际发布的2026年年报与当前情景及四家券商预测对照
4. 按新事实更新正常化利润率和再投资假设

当前数字基准是 2026 年半年度报告。市场价格、汇率和可比公司数据等到相应估值章节再按统一定价日加入。
