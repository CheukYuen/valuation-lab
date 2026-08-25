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
      expand: "Earnings Before Interest and Taxes",
      short: "暂时不考虑利息和所得税，公司经营本身赚了多少。",
      formula: "收入 − 经营成本和费用 = EBIT",
      caution: "EBIT margin（EBIT÷收入）高不代表现金转化好，还要看后续折旧、Capex（资本开支，Capital Expenditure）和营运资金。",
    },
    "NOPAT": {
      term: "NOPAT · 税后经营利润",
      expand: "Net Operating Profit After Tax",
      short: "把 EBIT 扣掉经营应承担的税，但仍不混入融资利息。",
      formula: "NOPAT = EBIT × (1 − 税率)",
      caution: "税率假设本身也是判断点，需要说明依据。",
    },
    "FCFF": {
      term: "FCFF · 企业自由现金流",
      expand: "Free Cash Flow to the Firm（Firm = 整个公司，股东和债权人一起）",
      short: "公司经营产生、扣除继续经营所需投入后，可供股东和债权人共同支配的现金。",
      formula: "FCFF = NOPAT + 折旧 − 资本开支 − 营运资金增加",
      caution: "它不是财报直接给出的一个统一数字，需要由报表项目计算并解释调整；利润增长不代表 FCFF 同比例增长。",
    },
    "DCF": {
      term: "DCF · 现金流折现",
      expand: "Discounted Cash Flow",
      short: "把未来每年的自由现金流折算成今天的价值。",
      caution: "未来越远、风险越高，今天值的钱通常越少；正向 DCF 先预测再计算价值，反向 DCF 从价格反推需要的条件。",
    },
    "WACC": {
      term: "WACC · 折现率",
      expand: "Weighted Average Cost of Capital（加权平均资本成本）",
      short: "模型用来表达时间和经营风险的折现率。本课里把 WACC 当作这把尺子使用，暂时不要求你自己推导。",
      caution: "只需检查来源是否解释、币种和业务风险是否匹配、是否做了区间敏感性。",
    },
    "终值": {
      term: "终值",
      short: "显性预测期结束以后全部现金流在模型中的合计价值。",
      caution: "终值占比高，表示结论更依赖遥远未来的利润率、增长和折现率——这是需要重点质证的警告，不自动证明模型无效。",
    },
    "EV": {
      term: "EV · 企业价值",
      expand: "Enterprise Value",
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
      caution: "总股本、流通股、扣除库存股后的普通股不是一回事；双重上市、增发、回购都可能使分母出错。它也不是 EPS：每股价值切的是股权价值，EPS 切的是会计利润。",
    },
    "EPS": {
      term: "EPS · 每股收益",
      expand: "Earnings Per Share",
      short: "归属于普通股股东的净利润，除以对应的普通股股数。",
      formula: "EPS = 归属普通股的净利润 ÷ 对应股数",
      caution: "不是每股价值。拉长折旧年限会让 EPS 更好看，买设备的现金不变，FCFF 基本不动。改年限是会计估计，不自动等于造假，也不能单独证明公司更值钱。",
    },
    "桥": {
      term: "桥 · bridge",
      expand: "bridge；图常叫 waterfall（瀑布图），会计里更正式叫 reconciliation（调节表）",
      short: "从起点用逐项加减走到终点、每一项都能复算的调节表。",
      formula: "起点 + 逐项调整 = 终点",
      caution: "第1课指假设怎么改（量价/产能桥）；第2课指价值怎么算（EBIT→FCFF、EV→股权价值）。没有桥不等于模型算错，只说明数字尚未闭合。",
    },
    "PE": {
      term: "PE · 市盈率",
      expand: "Price-to-Earnings（Price ÷ Earnings，股价或股权市值 ÷ 净利润或 EPS）",
      short: "股权市值除以净利润。",
      formula: "PE = 股权市值 ÷ 净利润",
      caution: "分母是利润或 EPS，不是现金。适合盈利口径可对齐的比较；周期峰值利润、被折旧年限抬高的 EPS、亏损公司都会使 PE 容易误导。",
    },
    "PB": {
      term: "PB · 市净率",
      expand: "Price-to-Book（Price ÷ Book value，股权市值 ÷ 账面净资产）",
      short: "股权市值除以净资产。",
      formula: "PB = 股权市值 ÷ 净资产",
      caution: "常与 ROE（Return on Equity，净资产收益率）一起用于银行、保险等资产负债表驱动的业务，不是所有公司的通用主方法。",
    },
    "EV/EBITDA": {
      term: "EV/EBITDA",
      expand: "Enterprise Value ÷ EBITDA；EBITDA = Earnings Before Interest, Taxes, Depreciation and Amortization（未扣利息、税、折旧摊销前利润）",
      short: "企业价值除以未扣利息、税、折旧摊销前利润。",
      caution: "能减少融资和折旧口径差异，但不会自动处理资本开支和营运资金，不能等同于现金流。",
    },
    "SOTP": {
      term: "SOTP · 分部加总估值",
      expand: "Sum of the Parts",
      short: "把不同业务分别估值后再加总。",
      caution: "只有分部利润、资产、资本开支和总部费用能够可靠拆分时，SOTP 才有足够基础。",
    },
    "反向DCF": {
      term: "反向 DCF",
      expand: "reverse Discounted Cash Flow",
      short: "把当前价格作为输入，反推需要怎样的增长、利润率或持续时间才能解释它。",
      caution: "结果依赖折现率、现金转化和终值等假设，是“在这组假设下的成绩要求”，不是市场唯一观点，也不是未来经营事实。",
    },
  };

  globalThis.ValuationLabGlossary = ENTRIES;
})();
