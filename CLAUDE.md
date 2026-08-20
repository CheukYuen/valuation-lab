# CLAUDE.md

## 项目目标

用7天零基础课程学会判断估值输出是否值得继续使用，而不是学会构建估值。本项目不产出投资结论，不输出目标价、评级、仓位或买卖动作。

## 硬边界

- 结论必须可复算：改输入重跑，不靠记忆里的数字。
- 案例一旦冻结不再改动；来源仓库的更新不同步回来。
- 答案文件记录缺陷与方向区间，不记录单一「正确数值」。
- 六类信息不得互相冒充：已发生事实、公司指引、外部预测、内部假设、派生计算、分析判断；市场共识属外部预测，单家券商预测不得冒充共识。
- 危险信号是筛查线索，不自动等于模型错误；必须同时说明为什么可疑、影响和还不能断言什么。
- 每课包含一个必做的运行环节：先写判断，再运行对应脚本复算。脚本只用 Python 标准库、可离线运行，输出只用于验证判断，不产出投资结论。
- `web/` 是纯静态离线互动版，不引入网络依赖；互动计算必须调用 `web/assets/tools.js` 中的唯一实现，该实现与 `lab/` 下对应 Python 函数由 parity 测试逐字段比对。页面内不得另写公式，也不得内联硬编码计算结果。

## 文档入口

先读 `README.md`。学习者优先进入 `web/index.html`，纯文字入口是 `course/README.md`。陌生术语查 `docs/GLOSSARY.md`；审材料时加载 `docs/AUDIT-CHECKLIST.md`；`docs/FIVE-NUMBERS.md` 只是第4课的可选补充。

## 命令

```bash
python3 lab/record_contract.py       # 第1、3课：关键数字记录契约与 PIT 校验
python3 lab/bridge.py                # 第2课：EBIT→FCFF、EV→每股价值两座桥
python3 lab/mini_dcf.py              # 第4课：最小 DCF + 弹性排序
python3 lab/reverse.py <市值>        # 第5课：反解价格隐含条件
python3 lab/methods.py               # 第6课：同一家公司的四种方法对照
python3 cases/01-yofc/knobs.py       # 第7课：案例 01 旋钮实验
python3 -m unittest discover -s tests -v  # 全部自动检查
```
