(() => {
  const byId = id => (typeof document === "undefined" ? null : document.getElementById(id));
  const number = id => Number(byId(id)?.value || 0);
  const pct = value => `${(value * 100).toFixed(1)}%`;
  const yi = value => `${value.toFixed(1)} 亿元`;

  function setText(id, value) {
    const el = byId(id);
    if (el) el.textContent = value;
  }

  function dcf(params) {
    const { baseFcf, growth, years, terminalGrowth, discountRate, netDebt } = params;
    if (discountRate <= terminalGrowth) throw new Error("折现率必须高于永续增长率");
    const flows = Array.from({ length: years }, (_, i) => baseFcf * (1 + growth) ** (i + 1));
    const explicitPv = flows.reduce((sum, f, i) => sum + f / (1 + discountRate) ** (i + 1), 0);
    const terminalValue = flows.at(-1) * (1 + terminalGrowth) / (discountRate - terminalGrowth);
    const terminalPv = terminalValue / (1 + discountRate) ** years;
    const ev = explicitPv + terminalPv;
    return { explicitPv, terminalPv, ev, equity: ev - netDebt, terminalShare: terminalPv / ev };
  }

  // 第2课的两座价值桥。公式的唯一来源是 lab/bridge.py，这里逐字段对齐，
  // 由 tests/test_web.py 的 parity 测试比对；页面不得另写一份算式。
  const FLOW = ["ebit", "taxRate", "depreciation", "capex", "workingCapitalIncrease"];
  const STRUCTURE = ["ev", "cash", "debt", "leaseLiability", "minorityInterest", "nonOperatingAssets"];
  const DENOMINATOR = ["totalShares", "treasuryShares", "optionDilution",
                       "convertibleShares", "convertibleDebt", "floatShares"];

  function require(input, keys) {
    // 未知不等于零：缺字段必须报错，不能静默按 0 计算。
    const missing = keys.filter(k => input[k] === undefined || input[k] === null);
    if (missing.length) throw new Error(`输入缺少 ${missing.join("、")}；未知不能当作 0`);
  }

  function fcffBridge(input) {
    require(input, FLOW);
    const nopat = input.ebit * (1 - input.taxRate);
    return {
      nopat,
      fcff: nopat + input.depreciation - input.capex - input.workingCapitalIncrease,
      skippedReinvestment: input.capex + input.workingCapitalIncrease - input.depreciation
    };
  }

  function equityBridge(input) {
    require(input, STRUCTURE);
    return {
      equityValue: input.ev + input.cash - input.debt - input.leaseLiability
        - input.minorityInterest + input.nonOperatingAssets,
      netDebt: input.debt + input.leaseLiability - input.cash
    };
  }

  function perShare(input) {
    require(input, DENOMINATOR);
    const value = equityBridge(input).equityValue;
    const basic = input.totalShares - input.treasuryShares;
    if (basic <= 0) throw new Error(`扣除库存股后的外部普通股为 ${basic}，分母必须为正`);
    const diluted = basic + input.optionDilution;
    const ifConverted = diluted + input.convertibleShares;
    return {
      basicShares: basic,
      dilutedShares: diluted,
      ifConvertedShares: ifConverted,
      perShareBasic: value / basic,
      perShareDiluted: value / diluted,
      perShareIfConverted: (value + input.convertibleDebt) / ifConverted,
      perShareDoubleCounted: value / ifConverted,
      perShareFloatWrong: value / input.floatShares,
      evPerShare: input.ev / basic
    };
  }

  function bridge(input) {
    return { ...fcffBridge(input), ...equityBridge(input), ...perShare(input) };
  }

  const OCF = [...FLOW, "interest", "interestCashFlowClassification"];
  const PERIOD = ["bondIssue", "dividendCash", "ocfLow", "ocfHigh"];

  function ocfCheck(input) {
    require(input, OCF);
    const classification = input.interestCashFlowClassification;
    if (!["operating", "financing"].includes(classification)) {
      throw new Error("interestCashFlowClassification 必须是 operating 或 financing");
    }
    const netIncome = (input.ebit - input.interest) * (1 - input.taxRate);
    const interestAddback = classification === "financing" ? input.interest : 0;
    const ocf = netIncome + interestAddback + input.depreciation - input.workingCapitalIncrease;
    const ocfMinusCapex = ocf - input.capex;
    const flow = fcffBridge(input).fcff;
    const afterTaxInterest = input.interest * (1 - input.taxRate);
    const taxShield = input.interest * input.taxRate;
    const expectedGap = classification === "operating" ? afterTaxInterest : -taxShield;
    return {
      netIncome,
      interestAddback,
      ocf,
      ocfMinusCapex,
      fcff: flow,
      gap: flow - ocfMinusCapex,
      afterTaxInterest,
      taxShield,
      expectedGap
    };
  }

  function pitBridge(input) {
    require(input, ["ev", "cash", "debt", "totalShares", "treasuryShares"]);
    if (!input.period || typeof input.period !== "object") {
      throw new Error("输入缺少 period；未知不能当作 0");
    }
    require(input.period, PERIOD);
    const basic = input.totalShares - input.treasuryShares;
    if (basic <= 0) throw new Error(`扣除库存股后的外部普通股为 ${basic}，分母必须为正`);
    const reportNetDebt = input.debt - input.cash;
    const netDebtHigh = reportNetDebt + input.period.dividendCash - input.period.ocfLow;
    const netDebtLow = reportNetDebt + input.period.dividendCash - input.period.ocfHigh;
    const equityLow = input.ev - netDebtHigh;
    const equityHigh = input.ev - netDebtLow;
    return {
      reportNetDebt,
      bondIssue: input.period.bondIssue,
      dividendCash: input.period.dividendCash,
      netDebtLow,
      netDebtHigh,
      equityLow,
      equityHigh,
      basicShares: basic,
      perShareLow: equityLow / basic,
      perShareHigh: equityHigh / basic,
      stalePerShare: (input.ev - reportNetDebt) / basic
    };
  }

  function terminalBridge(input, exitMultiple) {
    // 倍数分母是第 n 年 FCFF，不是 EV/EBITDA。内部键名保持 exitMultiple 以便 parity。
    const { baseFcf, growth, years, terminalGrowth, discountRate, netDebt } = input;
    if (discountRate <= terminalGrowth) throw new Error("折现率必须高于永续增长率");
    const gordon = dcf(input);
    const lastFcf = baseFcf * (1 + growth) ** years;
    const gordonTerminalValue = lastFcf * (1 + terminalGrowth) / (discountRate - terminalGrowth);
    const out = {
      lastFcf,
      gordonTerminalValue,
      gordonTerminalPv: gordon.terminalPv,
      gordonExplicitPv: gordon.explicitPv,
      impliedExitMultiple: gordonTerminalValue / lastFcf,
      gordonEquityValue: gordon.equity
    };
    if (exitMultiple === undefined || exitMultiple === null) return out;
    const terminalValue = lastFcf * exitMultiple;
    const terminalPv = terminalValue / (1 + discountRate) ** years;
    const ev = gordon.explicitPv + terminalPv;
    const impliedG = (exitMultiple * discountRate - 1) / (exitMultiple + 1);
    return {
      ...out,
      exitMultiple,
      terminalValue,
      terminalPv,
      explicitPv: gordon.explicitPv,
      enterpriseValue: ev,
      equityValue: ev - netDebt,
      terminalShare: ev ? terminalPv / ev : 0,
      impliedTerminalGrowth: impliedG
    };
  }

  function requiredYears(input, target, maxYears = 80) {
    const at = n => dcf({ ...input, years: n }).equity;
    const atOne = at(1);
    const atCap = at(maxYears);
    if (atOne > target) {
      return { requiredYears: 1, yearsBelow: 0, equityBelow: null, equityAt: atOne };
    }
    if (atCap < target) return null;
    let previous = atOne;
    for (let n = 1; n <= maxYears; n += 1) {
      const current = at(n);
      if (current >= target) {
        return {
          requiredYears: n,
          yearsBelow: n - 1,
          equityBelow: n > 1 ? previous : null,
          equityAt: current
        };
      }
      previous = current;
    }
    return null;
  }

  // 第6课：同一家公司的四种方法。唯一来源是 lab/methods.py。
  function multiples(input) {
    return {
      dcf: dcf(input.dcf).equity,
      pe: input.netIncome * input.peerPe,
      pb: input.bookEquity * input.peerPb,
      evEbitda: input.ebitda * input.peerEvEbitda - input.netDebt
    };
  }

  function bankDemo(input) {
    const b = input.bank;
    const exDeposits = b.otherDebt - b.cash;
    return {
      evEbitdaWithDeposits: b.operatingProfitProxy * b.peerEvEbitda - (b.deposits + exDeposits),
      evEbitdaWithoutDeposits: b.operatingProfitProxy * b.peerEvEbitda - exDeposits,
      pe: b.netIncome * b.peerPe,
      pb: b.bookEquity * b.peerPb
    };
  }

  function setupCashBridge() {
    if (!byId("bridge-ebit")) return;
    const update = () => {
      const ebit = number("bridge-ebit");
      const tax = number("bridge-tax") / 100;
      const da = number("bridge-da");
      const capex = number("bridge-capex");
      const wc = number("bridge-wc");
      const { nopat, fcff } = fcffBridge({
        ebit, taxRate: tax, depreciation: da, capex, workingCapitalIncrease: wc
      });
      setText("bridge-nopat", yi(nopat));
      setText("bridge-fcff", yi(fcff));
      setText("bridge-gap", yi(ebit - fcff));
    };
    document.querySelectorAll("[data-bridge-input]").forEach(el => el.addEventListener("input", update));
    update();
  }

  function setupOcfCheck() {
    if (!byId("ocf-ocf")) return;
    const update = () => {
      const classification = byId("ocf-classification").value;
      const r = ocfCheck({
        ebit: number("bridge-ebit"),
        taxRate: number("bridge-tax") / 100,
        depreciation: number("bridge-da"),
        capex: number("bridge-capex"),
        workingCapitalIncrease: number("bridge-wc"),
        interest: number("ocf-interest"),
        interestCashFlowClassification: classification
      });
      setText("ocf-income", yi(r.netIncome));
      setText("ocf-ocf", yi(r.ocf));
      setText("ocf-minus-capex", yi(r.ocfMinusCapex));
      setText("ocf-fcff", yi(r.fcff));
      setText("ocf-gap", yi(r.gap));
      setText("ocf-gap-rule", classification === "financing"
        ? `简化条件下应为负的利息税盾：${r.expectedGap.toFixed(1)} 亿元`
        : `简化条件下应为税后利息：${r.expectedGap.toFixed(1)} 亿元`);
    };
    document.querySelectorAll("[data-bridge-input], [data-ocf-input]").forEach(el => {
      el.addEventListener("input", update);
    });
    update();
  }

  function setupPitBridge() {
    if (!byId("pit-nd-low")) return;
    const update = () => {
      const r = pitBridge({
        ev: number("pit-ev"),
        cash: number("pit-cash"),
        debt: number("pit-debt"),
        totalShares: number("pit-total-shares"),
        treasuryShares: number("pit-treasury"),
        period: {
          bondIssue: number("pit-bond"),
          dividendCash: number("pit-dividend"),
          ocfLow: number("pit-ocf-low"),
          ocfHigh: number("pit-ocf-high")
        }
      });
      setText("pit-report-nd", yi(r.reportNetDebt));
      setText("pit-nd-low", yi(r.netDebtLow));
      setText("pit-nd-high", yi(r.netDebtHigh));
      setText("pit-equity-low", yi(r.equityLow));
      setText("pit-equity-high", yi(r.equityHigh));
      setText("pit-ps-low", `${r.perShareLow.toFixed(1)} 元`);
      setText("pit-ps-high", `${r.perShareHigh.toFixed(1)} 元`);
    };
    document.querySelectorAll("[data-pit-input]").forEach(el => el.addEventListener("input", update));
    update();
  }

  function setupDcf() {
    if (!byId("dcf-fcf")) return;
    const update = () => {
      try {
        const p = {
          baseFcf: number("dcf-fcf"),
          growth: number("dcf-growth") / 100,
          years: Math.round(number("dcf-years")),
          terminalGrowth: number("dcf-terminal") / 100,
          discountRate: number("dcf-wacc") / 100,
          netDebt: number("dcf-debt")
        };
        const r = dcf(p);
        setText("dcf-ev", yi(r.ev));
        setText("dcf-equity", yi(r.equity));
        setText("dcf-terminal-share", pct(r.terminalShare));
        const up = dcf({ ...p, discountRate: p.discountRate + 0.01 });
        setText("dcf-wacc-impact", pct(up.equity / r.equity - 1));
        setText("dcf-error", "");
        setupTerminal(p);
      } catch (error) {
        setText("dcf-error", error.message);
      }
    };
    document.querySelectorAll("[data-dcf-input]").forEach(el => {
      el.addEventListener("input", update);
      el.addEventListener("change", update);
    });
    update();
  }

  function setupTerminal(params) {
    if (!byId("dcf-implied-multiple")) return;
    const p = params || {
      baseFcf: number("dcf-fcf"),
      growth: number("dcf-growth") / 100,
      years: Math.round(number("dcf-years")),
      terminalGrowth: number("dcf-terminal") / 100,
      discountRate: number("dcf-wacc") / 100,
      netDebt: number("dcf-debt")
    };
    const gordon = terminalBridge(p);
    setText("dcf-implied-multiple", `${gordon.impliedExitMultiple.toFixed(1)} 倍`);
    const multiple = number("dcf-exit-multiple");
    const alt = terminalBridge(p, multiple);
    setText("dcf-exit-equity", `${alt.equityValue.toFixed(2)} 亿元`);
    setText("dcf-implied-g", pct(alt.impliedTerminalGrowth));
  }

  function solve(target, fn, low, high) {
    if (fn(low) > target || fn(high) < target) return null;
    for (let i = 0; i < 160; i += 1) {
      const mid = (low + high) / 2;
      if (fn(mid) < target) low = mid; else high = mid;
    }
    return (low + high) / 2;
  }

  function setupReverse() {
    if (!byId("reverse-target")) return;
    const update = () => {
      const target = number("reverse-target");
      const base = {
        baseFcf: number("reverse-fcf"), growth: 0.08, years: 7,
        terminalGrowth: 0.02, discountRate: 0.09, netDebt: 20
      };
      const body = byId("reverse-body");
      body.innerHTML = "";
      [0.07, 0.08, 0.09, 0.10, 0.11].forEach(rate => {
        const growth = solve(target, g => dcf({ ...base, growth: g, discountRate: rate }).equity, -0.5, 1.0);
        const row = document.createElement("tr");
        row.innerHTML = `<td>${pct(rate)}</td><td>${growth === null ? "无解" : pct(growth)}</td><td>${growth === null ? "检查模型边界" : "拿历史与经营机制质证"}</td>`;
        body.appendChild(row);
      });
      setupRequiredYears(base, target);
    };
    document.querySelectorAll("[data-reverse-input]").forEach(el => el.addEventListener("input", update));
    update();
  }

  function setupRequiredYears(params, target) {
    if (!byId("reverse-years")) return;
    const p = params || {
      baseFcf: number("reverse-fcf"), growth: 0.08, years: 7,
      terminalGrowth: 0.02, discountRate: 0.09, netDebt: 20
    };
    const t = target === undefined ? number("reverse-target") : target;
    const r = requiredYears(p, t);
    if (r === null) {
      setText("reverse-years", "无解");
      setText("reverse-years-below", "—");
      setText("reverse-years-at", "—");
      return;
    }
    setText("reverse-years", `约 ${r.requiredYears} 年`);
    setText("reverse-years-below", r.equityBelow === null
      ? "—"
      : `${r.yearsBelow} 年 ${r.equityBelow.toFixed(2)} 亿元`);
    setText("reverse-years-at", `${r.requiredYears} 年 ${r.equityAt.toFixed(2)} 亿元`);
  }

  function setupAudit() {
    const form = document.querySelector("[data-audit-form]");
    if (!form) return;
    const update = () => {
      const values = Array.from(form.querySelectorAll("select")).map(s => s.value);
      let result = "尚未完成六道门";
      if (values.every(Boolean)) {
        if (values.includes("fail")) result = "存在失败项：先判断它是否足以使核心输出失效；若是，停止使用并重算。";
        else if (values.some(v => v === "warn" || v === "unknown")) result = "带条件使用：记录警告与未知，量化关键敏感性。";
        else result = "可继续使用：进入深入审计，但这不代表估值已经正确。";
      }
      setText("audit-summary", result);
    };
    form.querySelectorAll("select").forEach(s => s.addEventListener("change", update));
    update();
  }

  const methods = {
    stable: ["DCF / 股息折现", "重点检查现金流可预测性、折现率和剩余经营期限。"],
    cyclical: ["周期正常化 + 反向DCF", "重点检查峰值是否永久化，以及供给与价格的持续时间。"],
    bank: ["PB/ROE / 剩余收益", "存贷款和资本要求是经营本体，不机械套工业公司FCFF。"],
    heavy: ["DCF + EV/EBITDA辅助", "必须把Capex和营运资金带回现金流。"],
    group: ["满足数据门槛后SOTP", "先确认分部利润、资产、Capex和总部费用能够拆分。"],
    early: ["单位经济 + 里程碑 + 宽区间情景", "远期假设太多时，DCF只能是脆弱情景，不能伪精确。"]
  };

  function setupMethodMatcher() {
    const select = byId("method-business");
    if (!select) return;
    const update = () => {
      const [method, caution] = methods[select.value];
      setText("method-result", method);
      setText("method-caution", caution);
    };
    select.addEventListener("change", update);
    update();
  }

  function setupMethodNumbers() {
    if (!byId("method-dcf-equity")) return;
    const input = {
      netIncome: 12, bookEquity: 80, ebitda: 30, netDebt: 30,
      peerPe: 15, peerPb: 1.8, peerEvEbitda: 8,
      dcf: {
        baseFcf: 10, growth: 0.08, years: 7,
        terminalGrowth: 0.02, discountRate: 0.09, netDebt: 30
      },
      bank: {
        operatingProfitProxy: 40, deposits: 900, otherDebt: 50, cash: 60,
        bookEquity: 100, netIncome: 15, peerPe: 6, peerPb: 0.8, peerEvEbitda: 8
      }
    };
    const m = multiples(input);
    const b = bankDemo(input);
    setText("method-dcf-equity", `${m.dcf.toFixed(2)} 亿元`);
    setText("method-pe", `${m.pe.toFixed(0)} 亿元`);
    setText("method-pb", `${m.pb.toFixed(0)} 亿元`);
    setText("method-ev-ebitda", `${m.evEbitda.toFixed(0)} 亿元`);
    setText("method-bank-with", `${b.evEbitdaWithDeposits.toFixed(0)} 亿元`);
    setText("method-bank-without", `${b.evEbitdaWithoutDeposits.toFixed(0)} 亿元`);
  }

  const yofc = {
    "6.0": [425.64, 800.42, 1619.92],
    "6.6": [390.47, 707.54, 1393.73],
    "7.0": [370.92, 657.67, 1276.02],
    "8.0": [331.56, 561.12, 1055.51],
    "9.0": [301.48, 491.06, 901.54],
    "10.0": [277.47, 437.59, 787.56]
  };

  function setupYofc() {
    const rate = byId("yofc-wacc");
    if (!rate) return;
    const update = () => {
      const [bear, base, bull] = yofc[rate.value];
      const conversion = number("yofc-conversion");
      setText("yofc-conversion-label", conversion.toFixed(2));
      setText("yofc-bear", yi(bear));
      setText("yofc-base", yi(base));
      setText("yofc-bull", yi(bull));
      setText("yofc-gap", pct(1903.996 / bull - 1));
      setText("yofc-h-margin", pct(0.26381985 * 0.8 / conversion));
      setText("yofc-market-margin", pct(0.54060166 * 0.8 / conversion));
      setText("yofc-a-margin", pct(0.8320602 * 0.8 / conversion));
    };
    rate.addEventListener("change", update);
    byId("yofc-conversion").addEventListener("input", update);
    update();
  }

  const pct2 = value => `${(value * 100).toFixed(2)}%`;
  const yi2 = value => `${value.toFixed(2)} 亿元`;
  const DEFAULT_BRIDGE = {
    ebit: 20, taxRate: 0.2, depreciation: 3, capex: 5, workingCapitalIncrease: 2, interest: 2,
    interestCashFlowClassification: "operating",
    ev: 200, cash: 20, debt: 50, leaseLiability: 0, minorityInterest: 0, nonOperatingAssets: 0,
    totalShares: 10.5, treasuryShares: 0.5, optionDilution: 0, convertibleShares: 0,
    convertibleDebt: 0, floatShares: 8,
    dilutionVariant: { optionDilution: 0.4, convertibleShares: 0.6, convertibleDebt: 10 },
    period: { bondIssue: 50, dividendCash: 30, ocfLow: 0, ocfHigh: 10 }
  };
  const DEFAULT_DCF = {
    baseFcf: 10, growth: 0.08, years: 7, terminalGrowth: 0.02, discountRate: 0.09, netDebt: 20
  };
  const DEFAULT_METHODS = {
    netIncome: 12, bookEquity: 80, ebitda: 30, netDebt: 30,
    peerPe: 15, peerPb: 1.8, peerEvEbitda: 8,
    dcf: { ...DEFAULT_DCF, netDebt: 30 },
    bank: {
      operatingProfitProxy: 40, deposits: 900, otherDebt: 50, cash: 60,
      bookEquity: 100, netIncome: 15, peerPe: 6, peerPb: 0.8, peerEvEbitda: 8
    }
  };

  // 第1课校验器输出与 python3 lab/record_contract.py 对齐；浏览器离线，因此内置全文。
  const RECORD_CONTRACT_OUTPUT = `输入：cases/00-records/*.json（与 lab/record_contract.py 相同样本）

01-clean.json · 长河科技｜2026财年合并收入｜内部Base假设（语义完整）
  语义完整：没有触发任何失败状态。
  注意：这只说明这条记录说清了自己是什么，不说明数字或经营假设正确。

02-consensus.json · 单家券商预测被命名为市场共识
  [重大] consensus  labelled_as_consensus  被命名为共识，却没有样本、统计方法和截点
             → 应返回：单家外部预测；共识无法确认

03-pit.json · 研究时点之后发布的一季报被用于当时输入
  [致命] pit        source_published_at    来源发布日 2026-04-20 晚于研究时点 2026-03-31
             → 应返回：未来信息污染

04-bridge.json · 内部调整没有逐项桥
  [重大] bridge     transform              发生了变换但缺少 ['bridge']；调整后数字没有逐项桥
             → 应返回：内部假设，部分可用或无法确认

05-evidence.json · 证据指针只到机构名称和网站首页
  [重大] evidence   evidence_pointer       证据指针 '华东证券官网' 定位不到页码、表格或可复取记录
             → 应返回：证据指针缺失

06-recompute.json · 派生股权价值缺输入、公式与独立重算
  [重大] recompute  computation            派生值缺少 ['inputs_version', 'formula', 'recomputed_by']；引用不能代替复算
             → 应返回：尚未程序复核

07-model-restated.json · 派生值由另一个语言模型复述，冒充独立计算
  [重大] recompute  computation.recomputed_by 另一个语言模型复述不是独立计算；需要确定性程序或可检查公式
             → 应返回：尚未程序复核

08-conflict.json · 记录值与原文直接冲突，且没有声明任何变换
  [致命] conflict   value                  记录值 100.0 与原文 104.3 冲突，且没有声明任何变换
             → 应返回：明确错误

09-semantics.json · 只保存了一个数字：缺对象、期间、单位、性质与时点
  [重大] semantics  … 多字段语义不完整，无法确认
  [重大] evidence   evidence_pointer       缺少证据指针；来源身份不能代替定位信息

10-negative-control.json · 负对照：8家机构汇总预测，样本方法截点齐全——不应降级
  语义完整：没有触发任何失败状态。

合计 14 条发现，来自 10 条记录。
发现数量不等于严重性排序；请按对本次结论的影响判断。`;

  const KNOBS_OUTPUT = `实验 0 · 三情景基准（WACC 6.6%，税率 20%）
  bear  股权     390.5 亿   终值占 EV  37.6%   2032 利润率 10.08%
  base  股权     707.5 亿   终值占 EV  57.9%   2032 利润率 20.00%
  bull  股权    1393.7 亿   终值占 EV  69.0%   2032 利润率 28.00%
  市场   实际分类市场权益    1904.0 亿（2026-08-14 A/H 合计）

实验 1 · Bull 情景旋钮：哪个假设在决定这个数
  基准                           1393.7 亿
  WACC 6.6% -> 8.0%            1055.5 亿    -24.3%
  永续增长 2.5% -> 1.5%            1271.8 亿     -8.7%
  2032 利润率 28% -> 24%          1243.2 亿    -10.8%
  整整七年收入全部 +10%                1545.9 亿    +10.9%
  终值 ROIC 12.5% -> 10%         1327.9 亿     -4.7%

  注意：七年收入整体 +10% 只值约 +11%；折现率动 1.4 个百分点抹掉约 24%。
  程序复算不等于输入依据已复核；也不产出目标价或买卖建议。`;

  function readBridgeInput() {
    if (!byId("bridge-ebit")) return { ...DEFAULT_BRIDGE };
    return {
      ...DEFAULT_BRIDGE,
      ebit: number("bridge-ebit"),
      taxRate: number("bridge-tax") / 100,
      depreciation: number("bridge-da"),
      capex: number("bridge-capex"),
      workingCapitalIncrease: number("bridge-wc"),
      interest: byId("ocf-interest") ? number("ocf-interest") : DEFAULT_BRIDGE.interest,
      interestCashFlowClassification: byId("ocf-classification")
        ? byId("ocf-classification").value
        : DEFAULT_BRIDGE.interestCashFlowClassification
    };
  }

  function readPitInput() {
    if (!byId("pit-ev")) {
      return {
        ev: DEFAULT_BRIDGE.ev,
        cash: DEFAULT_BRIDGE.cash,
        debt: DEFAULT_BRIDGE.debt,
        totalShares: DEFAULT_BRIDGE.totalShares,
        treasuryShares: DEFAULT_BRIDGE.treasuryShares,
        period: { ...DEFAULT_BRIDGE.period }
      };
    }
    return {
      ev: number("pit-ev"),
      cash: number("pit-cash"),
      debt: number("pit-debt"),
      totalShares: number("pit-total-shares"),
      treasuryShares: number("pit-treasury"),
      period: {
        bondIssue: number("pit-bond"),
        dividendCash: number("pit-dividend"),
        ocfLow: number("pit-ocf-low"),
        ocfHigh: number("pit-ocf-high")
      }
    };
  }

  function readDcfInput() {
    if (!byId("dcf-fcf")) return { ...DEFAULT_DCF };
    return {
      baseFcf: number("dcf-fcf"),
      growth: number("dcf-growth") / 100,
      years: Math.round(number("dcf-years")),
      terminalGrowth: number("dcf-terminal") / 100,
      discountRate: number("dcf-wacc") / 100,
      netDebt: number("dcf-debt")
    };
  }

  function formatBridgeRun() {
    const p = readBridgeInput();
    const b = bridge(p);
    const o = ocfCheck(p);
    const diluted = bridge({ ...p, ...p.dilutionVariant });
    const lines = [
      "输入：lab/inputs/bridge.json（页面控件可覆盖主线现金流）",
      "",
      "第一座桥：利润怎样变成现金",
      `  EBIT                    ${yi2(p.ebit)}`,
      `  × (1 - 经营税率 ${(p.taxRate * 100).toFixed(0)}%)`,
      `  = NOPAT                 ${yi2(b.nopat)}`,
      `  + 折旧                  ${yi2(p.depreciation)}`,
      `  - 资本开支              ${yi2(p.capex)}`,
      `  - 营运资金增加          ${yi2(p.workingCapitalIncrease)}`,
      `  = FCFF                  ${yi2(b.fcff)}`,
      "",
      `  把 NOPAT 直接当 FCFF，会漏掉净投入 ${yi2(b.skippedReinvestment)}`,
      "",
      "与财报现金流交叉检查",
      `  净利润                                      ${yi2(o.netIncome)}`,
      `  经营活动现金流                              ${yi2(o.ocf)}`,
      `  经营活动现金流 - Capex                      ${yi2(o.ocfMinusCapex)}`,
      `  本课 FCFF                                   ${yi2(o.fcff)}`,
      `  FCFF - (OCF - Capex)                        ${yi2(o.gap)}`,
      p.interestCashFlowClassification === "operating"
        ? `  简化解释：税后利息                        ${yi2(o.expectedGap)}`
        : `  简化解释：负的利息税盾                    ${yi2(o.expectedGap)}`,
      "",
      "第二座桥：企业价值怎样走到每股价值",
      `  EV（输入）                 ${yi2(p.ev)}`,
      `  = 普通股股权价值           ${yi2(b.equityValue)}`,
      `  外部普通股每股             ${b.perShareBasic.toFixed(2)} 元`,
      `  错误：流通股当分母         ${b.perShareFloatWrong.toFixed(2)} 元`,
      `  错误：EV ÷ 股本           ${b.evPerShare.toFixed(2)} 元`,
      "",
      "稀释变体（dilution_variant）",
      `  ② 加期权稀释              ${diluted.perShareDiluted.toFixed(2)} 元`,
      `  ③ if-converted            ${diluted.perShareIfConverted.toFixed(2)} 元`,
      `  ④ 混用②③                  ${diluted.perShareDoubleCounted.toFixed(2)} 元`,
      "",
      "边界：脚本复算的是算式，不是事实；不产出目标价或买卖建议。"
    ];
    return lines.join("\n");
  }

  function formatPitRun() {
    const p = readPitInput();
    const t = pitBridge(p);
    return [
      "输入：lab/inputs/bridge.json · period（资本结构时点桥）",
      "",
      `  报告日净债务     ${yi2(t.reportNetDebt)}`,
      `  + 发债 ${t.bondIssue.toFixed(0)}（净债务不变）`,
      `  + 现金分红       ${yi2(t.dividendCash)}`,
      `  - 期间经营现金流 ${p.period.ocfLow.toFixed(0)} 至 ${p.period.ocfHigh.toFixed(0)}`,
      `  = 估值日净债务   ${yi2(t.netDebtLow)} 至 ${yi2(t.netDebtHigh)}`,
      `  股权价值         ${yi2(t.equityLow)} 至 ${yi2(t.equityHigh)}`,
      `  每股价值         ${t.perShareLow.toFixed(1)} 至 ${t.perShareHigh.toFixed(1)} 元`,
      `  若仍用报告日净债务，每股 ${t.stalePerShare.toFixed(2)} 元`,
      "",
      "本课必做终端命令仍是 python3 lab/record_contract.py（对 03 / 09 / 10）。",
      "上表用同一套 bridge.pitBridge()，对应课文「亲手算一遍时点桥」。"
    ].join("\n");
  }

  function formatRecordContractRun() {
    return RECORD_CONTRACT_OUTPUT;
  }

  function formatDcfRun() {
    const p = readDcfInput();
    const r = dcf(p);
    const multiple = byId("dcf-exit-multiple") ? number("dcf-exit-multiple") : 10;
    const tb = terminalBridge(p, multiple);
    return [
      "输入：lab/inputs/simple.json（页面控件可覆盖）",
      "",
      "五个数",
      `  起点自由现金流      ${yi2(p.baseFcf)}`,
      `  显性期年增长        ${pct2(p.growth)}`,
      `  显性期年数          ${p.years} 年`,
      `  永续增长            ${pct2(p.terminalGrowth)}`,
      `  折现率              ${pct2(p.discountRate)}`,
      `  （净债务）          ${yi2(p.netDebt)}`,
      "",
      "结果",
      `  显性期现值          ${yi2(r.explicitPv)}`,
      `  终值现值            ${yi2(r.terminalPv)}`,
      `  企业价值            ${yi2(r.ev)}`,
      `  股权价值            ${yi2(r.equity)}`,
      `  终值占企业价值      ${pct(r.terminalShare)}`,
      "",
      "终值的两种写法只有分母和时点对齐后才能互译",
      `  第${p.years}年 FCFF          ${yi2(tb.lastFcf)}`,
      `  永续增长终值        ${yi2(tb.gordonTerminalValue)}`,
      `  隐含FCFF终值倍数    ${tb.impliedExitMultiple.toFixed(1)} 倍`,
      `  若改用 ${multiple} 倍第${p.years}年FCFF    股权价值 ${tb.equityValue.toFixed(2)} 亿元   隐含永续增长 ${pct2(tb.impliedTerminalGrowth)}`,
      "  等价互译不改变经济假设；改用不等价倍数才改变远期假设。",
      "  -0.91% 只对应 10 倍第 n 年 FCFF，不是 10 倍 EV/EBITDA。",
      "",
      "边界：输出不是“这家公司值多少”，而是“哪个假设在决定这个数”。"
    ].join("\n");
  }

  function formatReverseRun() {
    const target = byId("reverse-target") ? number("reverse-target") : 300;
    const baseFcf = byId("reverse-fcf") ? number("reverse-fcf") : 10;
    const base = { ...DEFAULT_DCF, baseFcf };
    const model = dcf(base);
    const lines = [
      "输入：lab/inputs/simple.json",
      `模型基准股权价值   ${yi2(model.equity)}`,
      `当前市场股权价值   ${yi2(target)}`,
      `差距               ${pct(target / model.equity - 1)}`,
      "",
      "① 当前价格要求的显性期年增长（其余输入不变）",
      "   折现率               要求增长"
    ];
    [0.07, 0.08, 0.09, 0.10, 0.11].forEach(rate => {
      const growth = solve(target, g => dcf({ ...base, growth: g, discountRate: rate }).equity, -0.5, 1.0);
      const tag = Math.abs(rate - 0.09) < 1e-12 ? "  <- 基准折现率" : "";
      lines.push(`   ${pct2(rate).padEnd(10)}${growth === null ? "无解".padStart(12) : pct2(growth).padStart(12)}${tag}`);
    });
    const years = requiredYears(base, target);
    lines.push("", "③ 当前价格要求的显性期年数（增长、起点、WACC 和永续增长全部不变）");
    if (years === null) {
      lines.push("   无解：即使把显性期拉到 80 年也撑不到这个价格");
    } else {
      lines.push(`   需要约 ${years.requiredYears} 年`);
      if (years.equityBelow !== null) {
        lines.push(`   ${String(years.yearsBelow).padStart(2)} 年   股权价值 ${years.equityBelow.toFixed(2)} 亿元`);
      }
      lines.push(`   ${String(years.requiredYears).padStart(2)} 年   股权价值 ${years.equityAt.toFixed(2)} 亿元`);
    }
    lines.push("", "边界：反解结果永远是带条件的曲线，不是买卖建议。");
    return lines.join("\n");
  }

  function formatMethodsRun() {
    const m = multiples(DEFAULT_METHODS);
    const b = bankDemo(DEFAULT_METHODS);
    const values = Object.values(m);
    const high = Math.max(...values);
    const low = Math.min(...values);
    return [
      "输入：lab/inputs/methods.json",
      "",
      "同一家工业公司的四个股权价值",
      `  DCF            ${yi2(m.dcf)}`,
      `  PE             ${yi2(m.pe)}`,
      `  PB             ${yi2(m.pb)}`,
      `  EV/EBITDA      ${yi2(m.evEbitda)}`,
      "",
      `  最高 ${high.toFixed(2)} / 最低 ${low.toFixed(2)} = ${(high / low).toFixed(2)} 倍`,
      "",
      "方法错配：把银行存款当成普通有息债务",
      `  EV/EBITDA，存款按债务扣除     ${yi2(b.evEbitdaWithDeposits)}   <- 负值，经济上不成立`,
      `  EV/EBITDA，存款不按债务扣除   ${yi2(b.evEbitdaWithoutDeposits)}`,
      `  PE                            ${yi2(b.pe)}`,
      `  PB                            ${yi2(b.pb)}`,
      "",
      "机械移出存款只隔离 900 亿元影响，不构成一座正确的银行 EV 桥。",
      "40 亿元是经营利润代理量，故意误当成 EBITDA；两组输出都不是有效银行估值。",
      "",
      "边界：脚本只演示方法差距和错配，不判断哪个倍数合理。"
    ].join("\n");
  }

  function formatKnobsRun() {
    return KNOBS_OUTPUT;
  }

  const LAB_RUNNERS = {
    "record-contract": formatRecordContractRun,
    bridge: formatBridgeRun,
    pit: formatPitRun,
    "mini-dcf": formatDcfRun,
    reverse: formatReverseRun,
    methods: formatMethodsRun,
    knobs: formatKnobsRun
  };

  function setupLabRun() {
    document.querySelectorAll("[data-lab-run]").forEach(panel => {
      const kind = panel.dataset.labRun;
      const button = panel.querySelector("[data-lab-run-button]");
      const output = panel.querySelector("[data-lab-run-output]");
      if (!button || !output || !LAB_RUNNERS[kind]) return;
      output.classList.add("is-empty");
      button.addEventListener("click", () => {
        try {
          output.textContent = LAB_RUNNERS[kind]();
          output.classList.remove("is-empty");
          output.classList.add("is-ready");
          button.setAttribute("aria-pressed", "true");
          button.textContent = "已运行 · 再跑一次";
        } catch (error) {
          output.textContent = `运行失败：${error.message}`;
          output.classList.remove("is-empty");
          output.classList.add("is-ready");
        }
      });
    });
  }

  globalThis.ValuationLabTools = {
    dcf, solve, fcffBridge, equityBridge, perShare, bridge, ocfCheck, pitBridge,
    terminalBridge, requiredYears, multiples, bankDemo, LAB_RUNNERS
  };

  if (typeof document !== "undefined") {
    document.addEventListener("DOMContentLoaded", () => {
      setupCashBridge();
      setupOcfCheck();
      setupPitBridge();
      setupDcf();
      setupReverse();
      setupAudit();
      setupMethodMatcher();
      setupMethodNumbers();
      setupYofc();
      setupLabRun();
    });
  }
})();
