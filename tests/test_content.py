import importlib.util
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


class ContentTests(unittest.TestCase):
    def test_required_course_files_exist(self):
        required = ["README.md", "PRETEST.md", "POSTTEST.md"]
        required += [f"DAY-{day}.md" for day in range(1, 8)]
        for name in required:
            self.assertTrue((ROOT / "course" / name).is_file(), name)

    def test_each_lesson_has_uniform_learning_sections(self):
        required_sections = ["本课目标", "10分钟白话解释", "好坏对照", "闯关", "展开答案", "本课边界"]
        for day in range(1, 8):
            text = (ROOT / "course" / f"DAY-{day}.md").read_text()
            for section in required_sections:
                self.assertIn(section, text, f"DAY-{day} missing {section}")

    def test_every_lesson_has_traceable_sources_matching_the_interactive_page(self):
        entry_pattern = re.compile(
            r"^### 〔(D[1-7]-S\d+)〕.*?(?=^### 〔D[1-7]-S\d+〕|^</details>)",
            re.MULTILINE | re.DOTALL,
        )
        citation_pattern = re.compile(r"\[〔(D[1-7]-S\d+)〕\]\(#(D[1-7]-S\d+)\)")
        address_pattern = re.compile(r"^- 地址：\[[^]]+\]\(([^)]+)\)", re.MULTILINE)
        html_source_pattern = re.compile(r'data-source-id="(D[1-7]-S\d+)" data-source-url="([^"]+)"')
        required_metadata = ["类型：", "发布机构：", "发布 / 版本：", "访问日期：", "地址：", "支持内容："]

        failures = []
        for day in range(1, 8):
            markdown_path = ROOT / "course" / f"DAY-{day}.md"
            page_path = ROOT / "web" / f"day-{day}.html"
            markdown = markdown_path.read_text()
            page = page_path.read_text()
            entries = {match.group(1): match.group(0) for match in entry_pattern.finditer(markdown)}
            html_sources = dict(html_source_pattern.findall(page))

            if "## 资料来源与核查" not in markdown or "展开本课来源、地址与用途" not in markdown:
                failures.append(f"DAY-{day}: missing expandable Markdown source section")
            if '<details class="source-details">' not in page or '<section class="reader-section sources-section" id="sources"' not in page:
                failures.append(f"day-{day}.html: missing collapsed source section")
            if len(entries) < 2:
                failures.append(f"DAY-{day}: expected at least two source entries")

            for source_id, target_id in citation_pattern.findall(markdown):
                if source_id != target_id or source_id not in entries:
                    failures.append(f"DAY-{day}: unresolved citation {source_id} -> {target_id}")
            html_citations = set(re.findall(r'class="source-citation" href="#(D[1-7]-S\d+)"', page))
            if not html_citations or not html_citations.issubset(html_sources):
                failures.append(f"day-{day}.html: unresolved inline source citation")

            markdown_sources = {}
            for source_id, block in entries.items():
                missing = [label for label in required_metadata if label not in block]
                if missing:
                    failures.append(f"{source_id}: missing metadata {missing}")
                address = address_pattern.search(block)
                if not address:
                    failures.append(f"{source_id}: missing address")
                    continue
                markdown_sources[source_id] = address.group(1)

            if markdown_sources != html_sources:
                failures.append(f"DAY-{day}: Markdown/HTML source map differs")

            for source_id, target in markdown_sources.items():
                if target.startswith("http"):
                    if not target.startswith("https://"):
                        failures.append(f"{source_id}: external source is not HTTPS")
                elif not (markdown_path.parent / target).resolve().exists():
                    failures.append(f"{source_id}: missing local target {target}")
                if target.startswith("https://"):
                    expected = f'href="{target}" target="_blank" rel="noopener noreferrer"'
                    if expected not in page:
                        failures.append(f"{source_id}: unsafe or missing external HTML link")
                elif not (page_path.parent / target).resolve().exists():
                    failures.append(f"{source_id}: missing interactive local target {target}")

        self.assertEqual(failures, [], "\n".join(failures))

    def test_relative_markdown_links_resolve(self):
        failures = []
        for markdown in ROOT.rglob("*.md"):
            if {".git", "node_modules"} & set(markdown.parts):
                continue
            text = markdown.read_text()
            for target in LINK.findall(text):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                path_text = target.split("#", 1)[0]
                if not path_text:
                    continue
                target_path = Path(path_text)
                resolved = target_path if target_path.is_absolute() else markdown.parent / target_path
                if not resolved.exists():
                    failures.append(f"{markdown.relative_to(ROOT)} -> {target}")
        self.assertEqual(failures, [], "broken links:\n" + "\n".join(failures))

    def test_beginner_cases_cover_six_single_errors(self):
        text = (ROOT / "cases/00-basics/README.md").read_text()
        for number in range(1, 7):
            self.assertIn(f"## 案例{number}", text)

    def test_day_one_covers_agent_acceptance_contract(self):
        text = (ROOT / "course" / "DAY-1.md").read_text()
        required_concepts = [
            "第一层：人能读懂六类信息",
            "专业标注不是一个“可信度分数”",
            "第二层：Agent 能记录关键数字身份证",
            "原始披露 → 提取值 → 口径调整 → 模型输入 → 计算结果 → 报告表述",
            "source_published_at <= adopted_at <= research_as_of",
            "记录验证状态与材料使用等级是两层判断",
            "AI 与多模型协作的专业边界",
            "开发者层：验收一段投研 Agent 输出",
            "失败状态矩阵",
            "正反验收测试",
            "负对照：不是所有缺口都等于停用",
            "练习：写一条验收测试",
            "一页验收清单",
            "投研 Agent 开发的最低能力",
            "交给后面几课",
        ]
        for concept in required_concepts:
            self.assertIn(concept, text, f"DAY-1 missing {concept}")

        for information_type in ["已发生事实", "公司指引", "外部预测", "内部假设", "派生计算", "分析判断"]:
            self.assertIn(information_type, text, f"DAY-1 missing information type {information_type}")

    def test_day_one_vocabulary_does_not_drift_between_markdown_and_web(self):
        # DAY-1.md and web/day-1.html are maintained by hand and already drifted
        # once (the web copy silently dropped 处理状态). Break the build instead.
        markdown = (ROOT / "course" / "DAY-1.md").read_text()
        page = (ROOT / "web" / "day-1.html").read_text()

        dimensions = ["信息性质", "来源身份", "处理状态", "验证状态"]
        natures = ["已发生事实", "公司指引", "外部预测", "内部假设", "派生计算", "分析判断"]
        failure_states = ["未来信息污染", "证据指针缺失", "明确错误"]

        missing = [term for term in dimensions + natures + failure_states
                   if term not in markdown or term not in page]
        self.assertEqual(missing, [], f"terms missing from DAY-1.md or day-1.html: {missing}")

    def test_day_one_surfaces_never_name_a_stale_information_type_count(self):
        # Narrow on purpose: this only guards the *count word* on the five day-1
        # surfaces. Stale five-item enumerations that name no count still exist in
        # DAY-3 and docs/AUDIT-CHECKLIST.md and are a later round of work.
        surfaces = [
            ROOT / "course" / "DAY-1.md",
            ROOT / "web" / "index.html",
            ROOT / "web" / "day-1.html",
            ROOT / "web" / "study-methods.html",
            ROOT / "CLAUDE.md",
        ]
        # "第七类信息" is a deliberate phrase in DAY-1 (AI is not a seventh type),
        # so only an unprefixed count is a drift.
        stale = re.compile(r"(?<!第)[四五七]类信息")
        wrong = []
        for path in surfaces:
            for hit in set(stale.findall(path.read_text())):
                wrong.append(f"{path.relative_to(ROOT)} says {hit}")
        self.assertEqual(wrong, [], "\n".join(wrong))

    def test_day_one_teaches_when_not_to_flag(self):
        # 知道何时不该报警 is half the acceptance skill; without it the course
        # rewards an agent that returns 无法确认 for everything.
        markdown = (ROOT / "course" / "DAY-1.md").read_text()
        for phrase in ["不降级", "状态不变", "负对照"]:
            self.assertIn(phrase, markdown, f"DAY-1 missing {phrase}")

    def test_stated_course_hours_reconcile_with_the_day_table(self):
        # A stated total that does not reconcile with its own parts is exactly the
        # defect class this course teaches; keep the README honest about it.
        readme = (ROOT / "README.md").read_text()
        minutes = [int(m) for m in re.findall(r"^\| \d \|[^|]+\| (\d+) 分钟 \|", readme, re.MULTILINE)]
        self.assertEqual(len(minutes), 7, f"expected 7 lesson rows, parsed {minutes}")

        stated = re.search(r"约 (\d+) 小时", readme)
        self.assertIsNotNone(stated, "README no longer states a total")
        self.assertEqual(round(sum(minutes) / 60), int(stated.group(1)),
                         f"day table sums to {sum(minutes)} minutes")

    def test_day_two_teaches_the_denominator_beyond_basic_shares(self):
        # 分母是第2课的主题之一。只讲总股本/流通股/库存股而不讲潜在稀释，
        # 会漏掉真实研报里最常见的一类每股错误。
        text = (ROOT / "course" / "DAY-2.md").read_text()
        for term in ["潜在稀释股份", "可转债", "if-converted", "优先股", "库存股法"]:
            self.assertIn(term, text, f"DAY-2 missing {term}")

    def test_day_two_never_gives_a_fixed_direction_for_skipping_the_ev_bridge(self):
        # 课文里所有例子都是净债务公司；只说"EV÷股本会高估"会训练出错误的单向直觉。
        text = (ROOT / "course" / "DAY-2.md").read_text()
        self.assertIn("净现金", text, "DAY-2 must show the net-cash case where the direction flips")

    def test_day_two_ocf_check_names_the_interest_classification(self):
        markdown = (ROOT / "course" / "DAY-2.md").read_text()
        page = (ROOT / "web" / "day-2.html").read_text()
        for term in ["利息支付列在经营活动", "利息支付列在筹资活动", "-0.4亿元"]:
            self.assertIn(term, markdown, f"DAY-2 missing OCF classification boundary: {term}")
        self.assertIn('id="ocf-classification"', page)
        self.assertNotIn("差额（应=税后利息）", page)

    def test_day_three_pit_bridge_uses_dividend_not_acquisition_cash(self):
        markdown = (ROOT / "course" / "DAY-3.md").read_text()
        page = (ROOT / "web" / "day-3.html").read_text()
        bridge = (ROOT / "lab" / "bridge.py").read_text()
        for text in [markdown, page, bridge]:
            self.assertIn("现金分红", text)
        self.assertIn("收购前 EV", markdown)
        self.assertIn("收购后净债务", markdown)
        self.assertNotIn("pit-acquisition", page)
        self.assertNotIn('period["acquisition_cash"]', bridge)

    def test_day_four_only_changes_the_terminal_assumption_for_a_nonequivalent_multiple(self):
        markdown = (ROOT / "course" / "DAY-4.md").read_text()
        page = (ROOT / "web" / "day-4.html").read_text()
        script = (ROOT / "lab" / "mini_dcf.py").read_text()
        tools = (ROOT / "web" / "assets" / "tools.js").read_text()
        self.assertIn("等价换算为14.6倍第7年FCFF，经济假设并没有改变", markdown)
        self.assertIn("终值写法等价互译时不改变经济假设", page)
        for text in [script, tools]:
            self.assertIn("等价互译不改变经济假设；改用不等价倍数才改变远期假设", text)
        self.assertNotIn("终值写法的切换永远同时切换", markdown)
        self.assertNotIn("切换终值写法等于切换远期假设", page)
        self.assertNotIn("切换写法等于切换远期假设", script)

    def test_failure_matrices_use_only_day_one_vocabulary(self):
        # 仓库里有两套词表：记录验证状态（第1课）与清单项状态（AUDIT-CHECKLIST）。
        # 失败矩阵必须只用前者，否则下游无法渲染一致的状态。
        # 切片必须在下一个任意层级标题处截断：矩阵后面还跟着「练习」和「一页验收清单」，
        # 而清单**故意**引用 AUDIT-CHECKLIST 的 通过/警告/失败 词表，切多了会误报，
        # 而「修复」误报的自然做法是删掉正确的教学内容。
        checked = []
        for day in range(1, 8):
            text = (ROOT / "course" / f"DAY-{day}.md").read_text()
            if "### 失败状态矩阵" not in text:
                continue
            checked.append(day)
            section = re.split(r"\n#{2,3} ", text.split("### 失败状态矩阵", 1)[1], 1)[0]
            table = [line for line in section.splitlines() if line.startswith("|")]
            self.assertGreaterEqual(len(table), 8, f"DAY-{day} failure matrix rows not found")
            for line in table:
                for stale in ["警告", "通过"]:
                    self.assertNotIn(stale, line, f"DAY-{day} checklist vocabulary in matrix: {line}")
        # 覆盖面由 test_every_failure_mode_lands_on... 按模式逐条保证；
        # 这里只确认确实切到了矩阵，不锁定哪几课有矩阵。
        self.assertGreaterEqual(len(checked), 6, f"matrices found on {checked}")

    def test_every_failure_mode_lands_on_a_lesson_that_ships_a_matrix_and_an_exercise(self):
        # DAY-1 和 DAY-2 都写明：六个失败模式最终都要落到一个失败状态和一条验收测试上。
        # 没有这条测试，那句承诺就是 DAY-1 自己警告过的「挂件」。
        delivered_by = {
            "利润不等于现金": 2,
            "错股本": 2,
            "错时点": 3,
            "峰值永久化": 4,
            "隐藏终值": 4,
            "方法错配": 6,
        }
        day_one = (ROOT / "course" / "DAY-1.md").read_text()
        day_seven = (ROOT / "course" / "DAY-7.md").read_text()
        for mode, day in delivered_by.items():
            self.assertIn(mode, day_one, f"DAY-1 handoff table missing {mode}")
            self.assertIn(mode, day_seven, f"DAY-7 recycling table missing {mode}")
            lesson = (ROOT / "course" / f"DAY-{day}.md").read_text()
            self.assertIn(mode, lesson, f"DAY-{day} never names {mode}")
            self.assertIn("失败状态矩阵", lesson, f"DAY-{day} delivers {mode} without a matrix")
            self.assertIn("什么必须不变", lesson, f"DAY-{day} delivers {mode} without a test exercise")

    def test_every_lesson_teaches_when_not_to_flag(self):
        # CLAUDE.md：危险信号只是检查线索，不自动等于模型错误。少了这一半，
        # 课程会奖励一个对所有材料都返回「无法确认」的验收器。
        for day in range(1, 8):
            text = (ROOT / "course" / f"DAY-{day}.md").read_text()
            for phrase in ["不降级", "状态不变", "负对照"]:
                self.assertIn(phrase, text, f"DAY-{day} missing {phrase}")

    def test_information_type_enumerations_name_all_six(self):
        # 枚举信息性质时漏掉派生计算和分析判断，正好漏掉最容易被写成事实的两类。
        # 这几个面之前分别写成三类、四类和五类。
        surfaces = [
            ROOT / "course" / "DAY-3.md",
            ROOT / "course" / "DAY-7.md",
            ROOT / "course" / "README.md",
            ROOT / "docs" / "AUDIT-CHECKLIST.md",
        ]
        types = ["已发生事实", "公司指引", "外部预测", "内部假设", "派生计算", "分析判断"]
        missing = []
        for path in surfaces:
            text = path.read_text()
            missing += [f"{path.relative_to(ROOT)} missing {t}" for t in types if t not in text]
        self.assertEqual(missing, [], "\n".join(missing))

    def test_acceptance_checklists_anchor_to_real_audit_ids(self):
        # 一页验收清单挂 D 编号才能回查。编号写错等于把读者送进空目录。
        known = set(re.findall(r"^\| (D\d+) \|", (ROOT / "docs" / "AUDIT-CHECKLIST.md").read_text(), re.MULTILINE))
        self.assertTrue(known, "no D-ids parsed from AUDIT-CHECKLIST.md")
        broken = []
        for day in range(2, 7):
            text = (ROOT / "course" / f"DAY-{day}.md").read_text()
            self.assertIn("一页验收清单", text, f"DAY-{day} missing 一页验收清单")
            section = re.split(r"\n## ", text.split("## 一页验收清单", 1)[1], 1)[0]
            broken += [f"DAY-{day} -> {i}" for i in set(re.findall(r"（(D\d+)", section)) - known]
        self.assertEqual(broken, [], "\n".join(broken))

    def test_each_lesson_states_the_same_budget_as_the_readme_table(self):
        # README 说第3课55分钟、第3课自己说35分钟，正是本课程教的那类缺陷。
        # 现有的小时数测试只解析 README，两处写岔它抓不到。
        readme = (ROOT / "README.md").read_text()
        table = {int(d): int(m) for d, m in
                 re.findall(r"^\| (\d) \|[^|]+\| (\d+) 分钟 \|", readme, re.MULTILINE)}
        self.assertEqual(len(table), 7, table)
        wrong = []
        for day, minutes in table.items():
            headline = (ROOT / "course" / f"DAY-{day}.md").read_text().split("\n")[2]
            stated = sum(int(m) for m in re.findall(r"约?(\d+)分钟", headline))
            if stated != minutes:
                wrong.append(f"DAY-{day}: lesson says {stated}, README says {minutes}")
        self.assertEqual(wrong, [], "\n".join(wrong))

    def test_day_two_hands_its_beginner_case_and_checklist_to_the_learner(self):
        # 案例3（利润不等于现金）曾经不被任何一课引用，而它正是第2课的主题。
        text = (ROOT / "course" / "DAY-2.md").read_text()
        self.assertIn("cases/00-basics", text)
        self.assertIn("docs/AUDIT-CHECKLIST.md", text)

    def test_day_two_completes_the_five_step_learning_loop(self):
        # course/README.md 声明了五步循环，第2课是最接近的一课，缺任何一步都要暴露。
        text = (ROOT / "course" / "DAY-2.md").read_text()
        for step in ["先闭卷回忆", "10分钟白话解释", "单变量实验", "一句话输出"]:
            self.assertIn(step, text, f"DAY-2 missing learning step {step}")

    def test_every_lesson_has_a_mandatory_run_step(self):
        # CLAUDE.md 的硬边界：每课包含一个必做的运行环节。没有这条测试，
        # "每课必做"只是一句写在文档里的口号。
        broken = []
        for day in range(1, 8):
            text = (ROOT / "course" / f"DAY-{day}.md").read_text()
            scripts = re.findall(r"^python3 (\S+\.py)", text, re.MULTILINE)
            if "运行环节" not in text or not scripts:
                broken.append(f"DAY-{day}: no run step")
                continue
            # 命令里点名的脚本必须真的存在，否则「每课必做」只是文档里的一句话
            broken += [f"DAY-{day}: missing {s}" for s in scripts if not (ROOT / s).is_file()]
        self.assertEqual(broken, [], "\n".join(broken))

    def test_markdown_renderer_fails_closed_on_unsupported_html(self):
        script = ROOT / "scripts" / "render_course_markdown.py"
        spec = importlib.util.spec_from_file_location("render_course_markdown", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaises(module.MarkdownRenderError):
            module.render_markdown("# 合法标题\n\n<section>不支持</section>\n", ROOT / "course" / "sample.md", ROOT / "web" / "generated" / "sample.html")

    def test_markdown_renderer_marks_source_anchors_and_secures_external_links(self):
        script = ROOT / "scripts" / "render_course_markdown.py"
        spec = importlib.util.spec_from_file_location("render_course_markdown_sources", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rendered = module.render_markdown(
            "## 资料来源与核查\n\n### 〔D2-S1〕 示例\n\n[外链](https://example.com/source)\n",
            ROOT / "course" / "sample.md",
            ROOT / "web" / "generated" / "sample.html",
        )
        self.assertIn('<h2 id="sources">资料来源与核查</h2>', rendered)
        self.assertIn('<h3 id="D2-S1">〔D2-S1〕 示例</h3>', rendered)
        self.assertIn('href="https://example.com/source" target="_blank" rel="noopener noreferrer"', rendered)


if __name__ == "__main__":
    unittest.main()
