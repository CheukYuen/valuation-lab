# CLAUDE.md

## 文档入口

- [项目方向与当前进展](docs/PROJECT-LOG.md)
- [长飞光纤估值实战方案](docs/YOFC-VALUATION-PRACTICE.md)
- [长飞光纤估值实战内容](docs/yofc/README.md)
- [中天科技估值实战内容](docs/ztt/README.md)
- [一个人的最小有效投研流程](docs/FIBER-MINIMUM-VIABLE-RESEARCH-WORKFLOW.md)
- [旧课程总览](README.md)
- [旧课程文字入口](course/README.md)
- [白话术语表](docs/GLOSSARY.md)
- [快速科学学习法](docs/LEARNING-METHODS.md)
- [DCF 的作用与局限](docs/DCF-AS-ASSUMPTION-TRANSLATOR.md)
- [DCF 的五个控制杆](docs/FIVE-NUMBERS.md)
- [分层审计清单](docs/AUDIT-CHECKLIST.md)
- [Claude 金融技能包快照（第三方参考）](vendor/claude-fsi-skills/README.md)

## Skills

- `wind-mcp-skill`：查询万得（Wind）行情、财务、公告、Beta、汇率等金融市场数据。密钥见 `.env` 中的 `WIND_API_KEY`。
- `choice-quantapi-skill`：Choice 量化 API（EMQuantAPI · Python）取数与量化/回测脚本生成，覆盖截面 `css`、序列 `csd`、板块截面 `cses`、专题报表 `ctr`、板块成分 `sector` 与交易日工具 `tradedates` / `getdate` / `tradedatesnum`。技能文档见 [.agents/skills/choice-quantapi-skill/SKILL.md](.agents/skills/choice-quantapi-skill/SKILL.md)，写代码前必须先读对应的 `references/functions/<函数名>.md`。
  - 鉴权不走 `.env`（`EM_API_KEY` 与本技能无关）：凭据由本机已激活的 SDK（`~/.choice/EMQuantAPI_Python`）持有；报 `ModuleNotFoundError` 时跑 `.agents/skills/choice-quantapi-skill/scripts/install.py`，报 `10001020` / `10001019` / `10001009` 时按 `.agents/skills/choice-quantapi-skill/references/sdk-setup.md` §2 跑同目录的 `scripts/activate.py`。

## 常用命令

```bash
python3 lab/record_contract.py
python3 lab/bridge.py
python3 lab/mini_dcf.py
python3 lab/reverse.py <市值>
python3 lab/methods.py
python3 cases/01-yofc/knobs.py
python3 -m unittest discover -s tests -v
python3 -m http.server 8765 --directory web
```
