(() => {
  const byId = id => document.getElementById(id);
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

  const OCF = [...FLOW, "interest"];
  const PERIOD = ["bondIssue", "acquisitionCash", "ocfLow", "ocfHigh"];

  function ocfCheck(input) {
    require(input, OCF);
    const netIncome = (input.ebit - input.interest) * (1 - input.taxRate);
    const ocf = netIncome + input.depreciation - input.workingCapitalIncrease;
    const ocfMinusCapex = ocf - input.capex;
    const flow = fcffBridge(input).fcff;
    const afterTaxInterest = input.interest * (1 - input.taxRate);
    return {
      netIncome,
      ocf,
      ocfMinusCapex,
      fcff: flow,
      gap: flow - ocfMinusCapex,
      afterTaxInterest
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
    const netDebtHigh = reportNetDebt + input.period.acquisitionCash - input.period.ocfLow;
    const netDebtLow = reportNetDebt + input.period.acquisitionCash - input.period.ocfHigh;
    const equityLow = input.ev - netDebtHigh;
    const equityHigh = input.ev - netDebtLow;
    return {
      reportNetDebt,
      bondIssue: input.period.bondIssue,
      acquisitionCash: input.period.acquisitionCash,
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
      evEbitdaWithDeposits: b.operatingIncome * b.peerEvEbitda - (b.deposits + exDeposits),
      evEbitdaWithoutDeposits: b.operatingIncome * b.peerEvEbitda - exDeposits,
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
      const r = ocfCheck({
        ebit: number("bridge-ebit"),
        taxRate: number("bridge-tax") / 100,
        depreciation: number("bridge-da"),
        capex: number("bridge-capex"),
        workingCapitalIncrease: number("bridge-wc"),
        interest: number("ocf-interest")
      });
      setText("ocf-income", yi(r.netIncome));
      setText("ocf-ocf", yi(r.ocf));
      setText("ocf-minus-capex", yi(r.ocfMinusCapex));
      setText("ocf-fcff", yi(r.fcff));
      setText("ocf-gap", yi(r.gap));
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
          acquisitionCash: number("pit-acquisition"),
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
        operatingIncome: 40, deposits: 900, otherDebt: 50, cash: 60,
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

  globalThis.ValuationLabTools = { dcf, solve, fcffBridge, equityBridge, perShare, bridge, ocfCheck, pitBridge, terminalBridge, requiredYears, multiples, bankDemo };

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
    });
  }
})();
