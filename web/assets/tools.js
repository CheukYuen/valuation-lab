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

  function setupCashBridge() {
    if (!byId("bridge-ebit")) return;
    const update = () => {
      const ebit = number("bridge-ebit");
      const tax = number("bridge-tax") / 100;
      const da = number("bridge-da");
      const capex = number("bridge-capex");
      const wc = number("bridge-wc");
      const nopat = ebit * (1 - tax);
      const fcff = nopat + da - capex - wc;
      setText("bridge-nopat", yi(nopat));
      setText("bridge-fcff", yi(fcff));
      setText("bridge-gap", yi(ebit - fcff));
    };
    document.querySelectorAll("[data-bridge-input]").forEach(el => el.addEventListener("input", update));
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
    };
    document.querySelectorAll("[data-reverse-input]").forEach(el => el.addEventListener("input", update));
    update();
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

  globalThis.ValuationLabTools = { dcf, solve };

  if (typeof document !== "undefined") {
    document.addEventListener("DOMContentLoaded", () => {
      setupCashBridge();
      setupDcf();
      setupReverse();
      setupAudit();
      setupMethodMatcher();
      setupYofc();
    });
  }
})();
