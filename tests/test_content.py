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

    def test_relative_markdown_links_resolve(self):
        failures = []
        for markdown in ROOT.rglob("*.md"):
            if ".git" in markdown.parts:
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

    def test_day_two_failure_matrix_uses_only_day_one_vocabulary(self):
        # 仓库里有两套词表：记录验证状态（第1课）与清单项状态（AUDIT-CHECKLIST）。
        # 失败矩阵必须只用前者，否则下游无法渲染一致的状态。
        text = (ROOT / "course" / "DAY-2.md").read_text()
        section = text.split("### 失败状态矩阵", 1)[1].split("\n## ", 1)[0]
        table = [line for line in section.splitlines() if line.startswith("|")]
        self.assertGreaterEqual(len(table), 8, "failure matrix rows not found")
        for line in table:
            for stale in ["警告", "通过"]:
                self.assertNotIn(stale, line, f"checklist vocabulary leaked into the matrix: {line}")

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


if __name__ == "__main__":
    unittest.main()
