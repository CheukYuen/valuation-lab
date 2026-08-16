# 冻结说明

本目录的两个文件是**原样复制**，不要修改，也不要在这里改数字做实验。

| 文件 | 来源 |
|---|---|
| `valuation-inputs.json` | `investment-research-copilot/eval/company/yofc_valuation_20260815/valuation-inputs.json` |
| `calculate.py` | 同上目录的 `calculate.py` |

- 来源仓库：`/Users/leon/Stock/investment-research-copilot`
- 来源提交：`b7c2da0c595658eeb6cd166853312a26f0d85638`（2026-08-15）
- `valuation-inputs.json` SHA-256：`8589477eb52cdb155162a5130c828c3f8f08187cda461612ccddd3b43f29b257`
- `calculate.py` SHA-256：`64d0c404924ea58a5955d077ce7d111d24dbed5d762febefabff41206c53e0af`

## 为什么要冻结

两个原因：

1. 来源仓库的约定是「新建 `as_of` 目录不覆盖旧运行」，下一次估值会落在新日期目录里，直接引用路径迟早失效。
2. 本案例的答案是针对**这一版**的缺陷写的。如果来源模型按审计意见修好了，而本目录跟着变，学习者就会去调试一个已经不存在的问题。

教学案例必须是不动的。要看这份运算在来源仓库里的最新状态，去那边读，不要同步回来。
