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


if __name__ == "__main__":
    unittest.main()
