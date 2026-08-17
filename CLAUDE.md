# CLAUDE.md

## 项目目标

用7天零基础课程学会判断估值输出是否值得继续使用，而不是学会构建估值。本项目不产出投资结论，不输出目标价、评级、仓位或买卖动作。

## 硬边界

- 结论必须可复算：改输入重跑，不靠记忆里的数字。
- 案例一旦冻结不再改动；来源仓库的更新不同步回来。
- 答案文件记录缺陷与方向区间，不记录单一「正确数值」。
- 事实、公司指引、市场共识、券商预测和内部估计不得互相冒充。
- 危险信号是筛查线索，不自动等于模型错误；必须同时说明为什么可疑、影响和还不能断言什么。
- 前六课必须不运行代码也可完成；脚本是可选验证工具。
- `web/` 是纯静态离线互动版，不引入网络依赖；互动计算必须与对应Python公式或冻结结果保持一致。

## 文档入口

先读 `README.md`。学习者优先进入 `web/index.html`，纯文字入口是 `course/README.md`。陌生术语查 `docs/GLOSSARY.md`；审材料时加载 `docs/AUDIT-CHECKLIST.md`；`docs/FIVE-NUMBERS.md` 只是第4课的可选补充。

## 命令

```bash
python3 lab/mini_dcf.py              # 最小 DCF + 弹性排序
python3 lab/reverse.py <市值>        # 反解价格隐含条件
python3 cases/01-yofc/knobs.py       # 案例 01 旋钮实验
python3 -m unittest discover -s tests -v  # 全部自动检查
```
