(() => {
  // Keep in sync with docs/GLOSSARY.md — each key's `term` must match a `##` heading there.
  // tests/test_web.py checks both directions: every data-term reference resolves here,
  // and every entry here has a matching heading in docs/GLOSSARY.md.
  const ENTRIES = {
    "收入": {
      term: "收入",
      short: "公司卖产品或服务取得的钱。",
      caution: "收入大不代表赚钱多，更不代表现金多。",
    },
    "EBIT": {
      term: "EBIT · 息税前利润",
      short: "暂时不考虑利息和所得税，公司经营本身赚了多少。",
      formula: "收入 − 经营成本和费用 = EBIT",
      caution: "EBIT margin 高不代表现金转化好，还要看后续折旧、Capex 和营运资金。",
    },
    "NOPAT": {
      term: "NOPAT · 税后经营利润",
      short: "把 EBIT 扣掉经营应承担的税，但仍不混入融资利息。",
      formula: "NOPAT = EBIT × (1 − 税率)",
      caution: "税率假设本身也是判断点，需要说明依据。",
    },
    "FCFF": {
      term: "FCFF · 企业自由现金流",
      short: "公司经营产生、扣除继续经营所需投入后，可供股东和债权人共同支配的现金。",
      formula: "FCFF = NOPAT + 折旧 − 资本开支 − 营运资金增加",
      caution: "它不是财报直接给出的一个统一数字，需要由报表项目计算并解释调整；利润增长不代表 FCFF 同比例增长。",
    },
    "DCF": {
      term: "DCF · 现金流折现",
      short: "把未来每年的自由现金流折算成今天的价值。",
      caution: "未来越远、风险越高，今天值的钱通常越少；正向 DCF 先预测再计算价值，反向 DCF 从价格反推需要的条件。",
    },
    "WACC": {
      term: "WACC · 折现率",
      short: "模型用来表达时间和经营风险的折现率。",
      caution: "暂时不需要推导它，只需检查来源是否解释、币种和业务风险是否匹配、是否做了区间敏感性。",
    },
    "终值": {
      term: "终值",
      short: "显性预测期结束以后全部现金流在模型中的合计价值。",
      caution: "终值占比高，表示结论更依赖遥远未来的利润率、增长和折现率——这是需要重点质证的警告，不自动证明模型无效。",
    },
    "EV": {
      term: "EV · 企业价值",
      short: "经营资产对股东和债权人的总价值。",
      caution: "它还不是股东最终拥有的价值，走到股权价值需要处理现金、债务、租赁负债和少数股东权益。",
    },
    "股权价值": {
      term: "股权价值",
      short: "从 EV 走到股东最终拥有的价值。",
      formula: "股权价值 = EV + 现金 − 债务",
      caution: "简化公式省略了租赁负债、少数股东权益和非经营资产，实际材料里要检查是否处理了这些项。",
    },
    "每股价值": {
      term: "每股价值",
      short: "股权价值除以对应的外部普通股股数。",
      formula: "每股价值 = 股权价值 ÷ 对应的外部普通股股数",
      caution: "总股本、流通股、扣除库存股后的普通股不是一回事；双重上市、增发、回购都可能使分母出错。",
    },
    "PE": {
      term: "PE · 市盈率",
      short: "股权市值除以净利润。",
      formula: "PE = 股权市值 ÷ 净利润",
      caution: "适合盈利口径可对齐的比较；周期峰值利润、亏损公司会使 PE 容易误导。",
    },
    "PB": {
      term: "PB · 市净率",
      short: "股权市值除以净资产。",
      formula: "PB = 股权市值 ÷ 净资产",
      caution: "常与 ROE 一起用于银行、保险等资产负债表驱动的业务，不是所有公司的通用主方法。",
    },
    "EV/EBITDA": {
      term: "EV/EBITDA",
      short: "企业价值除以未扣利息、税、折旧摊销前利润。",
      caution: "能减少融资和折旧口径差异，但不会自动处理资本开支和营运资金，不能等同于现金流。",
    },
    "SOTP": {
      term: "SOTP · 分部加总估值",
      short: "把不同业务分别估值后再加总。",
      caution: "只有分部利润、资产、资本开支和总部费用能够可靠拆分时，SOTP 才有足够基础。",
    },
    "反向DCF": {
      term: "反向 DCF",
      short: "把当前价格作为输入，反推需要怎样的增长、利润率或持续时间才能解释它。",
      caution: "结果依赖折现率、现金转化和终值等假设，是“在这组假设下的成绩要求”，不是市场唯一观点，也不是未来经营事实。",
    },
  };

  globalThis.ValuationLabGlossary = ENTRIES;
})();
