# CLAUDE.md

## 项目目标

学会审计估值，而不是学会构建估值。本项目不产出投资结论，不输出目标价、评级、仓位或买卖动作。

## 硬边界

- 结论必须可复算：改输入重跑，不靠记忆里的数字。
- 案例一旦冻结不再改动；来源仓库的更新不同步回来。
- 答案文件记录缺陷与方向区间，不记录单一「正确数值」。
- 事实、公司指引、市场共识、券商预测和内部估计不得互相冒充。

## 文档入口

先读 `README.md`。按需加载 `docs/AUDIT-CHECKLIST.md`（审材料时）或 `docs/FIVE-NUMBERS.md`（补背景时），不要同时载入。

## 命令

```bash
python3 lab/mini_dcf.py              # 最小 DCF + 弹性排序
python3 lab/reverse.py <市值>        # 反解价格隐含条件
python3 cases/01-yofc/knobs.py       # 案例 01 旋钮实验
```
