# 毕业案例：长飞光纤 A/H 独立估值

这是第7课案例。先完成 Level A，再进入 Level B；Level C 和代码实验可选。**写完使用等级之前不要看 [`answer-key.md`](answer-key.md)。**

## 为什么把它放在最后

长飞同时包含：

- 周期利润与结构成长；
- A/H两类证券和不同报价；
- 发行人经营价值与每股证券价格；
- 正向DCF、反向DCF、终值和现金转化；
- 完整计算程序与不完整原始存证。

它适合检验综合判断，不适合作为零基础第一课。

## 先知道的背景

- 对象：长飞光纤发行人、A股 `601869.SH`、H股 `06869.HK`；
- 市场估值时点：2026-08-14；资本结构截止：2026-03-31；
- A股收盘355.18元，H股收盘132.20港元，报告计算A/H溢价约210%；
- Bear继承一家券商的预测，Base/Bull是内部情景；
- 模型状态自报 `PROVISIONAL`，不输出目标价或买卖结论。

## 材料顺序

### Level A：10分钟快速门

只读来源仓库的估值报告正文：

`/Users/leon/Stock/investment-research-copilot/eval/company/yofc_valuation_20260815/valuation-report.md`

检查对象、时点、股本、信息性质、敏感性和方法。不要打开JSON或代码。

### Level B：关键假设审计

再读来源方案：

`/Users/leon/Stock/investment-research-copilot/docs/COMPANY-YOFC-VALUATION.md`

回答正反向FCFF是否一致、终值如何正常化、三情景是否来自经营变量、2026基年是否与已知实际数据对质。

### Level C：可选复算与存证

| 文件 | 用途 |
|---|---|
| [`frozen/valuation-inputs.json`](frozen/valuation-inputs.json) | 冻结输入 |
| [`frozen/calculate.py`](frozen/calculate.py) | 冻结计算程序 |
| [`frozen/SOURCE.md`](frozen/SOURCE.md) | 来源提交与哈希 |
| [`knobs.py`](knobs.py) | 在内存中做敏感性实验 |

`frozen/` 不修改。来源模型后续更新不回写本案例。

## 交付物

复制 [`worksheet.md`](worksheet.md) 为你自己的记录，最终必须分别评价：

1. 模型工程质量；
2. 经济假设质量；
3. 方法适用性；
4. 当前材料的使用等级。

不要回答“长飞值多少钱”或“是否值得买”。
