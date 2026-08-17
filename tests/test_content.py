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
            "一页验收清单",
            "投研 Agent 开发的最低能力",
        ]
        for concept in required_concepts:
            self.assertIn(concept, text, f"DAY-1 missing {concept}")

        for information_type in ["已发生事实", "公司指引", "外部预测", "内部假设", "派生计算", "分析判断"]:
            self.assertIn(information_type, text, f"DAY-1 missing information type {information_type}")

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
