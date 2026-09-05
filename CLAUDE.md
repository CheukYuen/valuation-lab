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

- `wind-mcp-skill`：查询万得（Wind）行情、财务、公告、Beta、汇率等金融市场数据。走本地 CLI：`node .agents/skills/wind-mcp-skill/scripts/cli.mjs call <server_type> <tool_name> '<json>'`。
- **Wind 系密钥（`wind-mcp-skill` 与 `wind-alice` 共用同一个 `WIND_API_KEY`）**：值存在 `.env`（已 gitignore），但两个 CLI **都不会读取本仓库的 `.env` 文件**——它们只按 `~/.wind-aifinmarket/config` > skill 目录 `config.json` > `WIND_API_KEY` 环境变量 这个顺序取值。所以直接调用会报 `AUTH_ERROR` / `KEY_MISSING`，需先把它导入环境：
  ```bash
  set -a; . ./.env; set +a
  ```
  想一劳永逸就把 `WIND_API_KEY=<KEY>` 写进 `~/.wind-aifinmarket/config`（全局共享，两个 skill 都能读到）。
- `choice-quantapi-skill`：Choice 量化 API（EMQuantAPI · Python）取数与量化/回测脚本生成，覆盖截面 `css`、序列 `csd`、板块截面 `cses`、专题报表 `ctr`、板块成分 `sector` 与交易日工具 `tradedates` / `getdate` / `tradedatesnum`。技能文档见 [.agents/skills/choice-quantapi-skill/SKILL.md](.agents/skills/choice-quantapi-skill/SKILL.md)，写代码前必须先读对应的 `references/functions/<函数名>.md`。
  - 鉴权不走 `.env`（`EM_API_KEY` 与本技能无关）：凭据由本机已激活的 SDK（`~/.choice/EMQuantAPI_Python`）持有；报 `ModuleNotFoundError` 时跑 `.agents/skills/choice-quantapi-skill/scripts/install.py`，报 `10001020` / `10001019` / `10001009` 时按 `.agents/skills/choice-quantapi-skill/references/sdk-setup.md` §2 跑同目录的 `scripts/activate.py`。
- `dcf-model`：DCF 估值建模（WACC + 敏感性分析），产出机构级 Excel 模型。硬性规矩：派生单元格一律写 Excel 公式而非 Python 算好的数值、敏感性表用奇数行列且中心格 = base case、每个硬编码输入加来源批注、分阶段与用户确认后再往下建。
  - **本仓库用它要换数据源**：该 skill 面向 SEC filings + `yfinance`（本机未装 yfinance），A 股标的应改用 `wind-mcp-skill` / `choice-quantapi-skill` 取数，只复用它的建模结构与校验规矩。
  - SKILL.md 要求交付前跑 `recalc.py`，但该脚本未随包提供、本机也搜不到（文档称来自 xlsx skill），这一步当前跑不了；可用的是 `python3 .agents/skills/dcf-model/scripts/validate_dcf.py <excel_file>`（已验证可运行，openpyxl 3.1.5 在位）。
- `wind-alice`：万得 Alice 专业金融分析 Agent 的 CLI（A2A 协议 + SSE 流式），已安装于 `.agents/skills/wind-alice`。承载 14 个子 Skill：事实核验、公司一页纸、上市公司调研问题清单、全球季报点评、按主题选股、基金对比 / 筛选、宏观数据解读、债券利率走势、信用分析、市场规模测算、可比公司分析等（`node scripts/wind-alice.mjs list-skills` 可列全）。
  - 用法：`cd .agents/skills/wind-alice && node scripts/wind-alice.mjs --prompt "<用户原话>" --skill "<中文或英文 Skill 名>"`。**必须原样传用户问句**，不要改写、翻译或只提取代码；Skill 选择靠 CLI 拼的 prompt 前缀实现，`--skill` 收的是名称不是 id，中文名 / 英文名 / 口语别名都能匹配。不传 `--skill` 则由 Alice auto 路由。
  - **耗时长、费积分**：一次调用常需数分钟到十几分钟，中途不要取消或重复发起。产出的附件由 CLI 自动下载到 `.agents/download/`。
  - 定位是 `wind-mcp-skill` 的**最后兜底**：仅当所有专项 Wind 路径都因数据覆盖 / 字段 / 口径问题失败，且向用户说明后才转交，不能拿它顶替专项取数。密钥同上（与 `wind-mcp-skill` 共用 `WIND_API_KEY`）。

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
