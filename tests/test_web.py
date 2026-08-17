import json
import re
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
DOCS = ROOT / "docs"


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = []
        self.quiz_cards = 0
        self.complete_buttons = 0
        self.lesson = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "body":
            self.lesson = values.get("data-lesson")
        if "id" in values:
            self.ids.append(values["id"])
        classes = set(values.get("class", "").split())
        if "quiz-card" in classes:
            self.quiz_cards += 1
        if "data-complete-lesson" in values:
            self.complete_buttons += 1
        for attribute in ("href", "src"):
            if attribute in values:
                self.links.append(values[attribute])


def parse(path):
    parser = PageParser()
    parser.feed(path.read_text())
    return parser


class WebCourseTests(unittest.TestCase):
    def test_required_pages_exist(self):
        names = ["index.html", "study-methods.html"] + [f"day-{day}.html" for day in range(1, 8)]
        for name in names:
            self.assertTrue((WEB / name).is_file(), name)

    def test_lesson_interaction_contract(self):
        for day in range(1, 8):
            parser = parse(WEB / f"day-{day}.html")
            self.assertEqual(parser.lesson, f"day-{day}")
            self.assertGreaterEqual(parser.quiz_cards, 3, f"day-{day} quizzes")
            self.assertEqual(parser.complete_buttons, 1, f"day-{day} completion")
            self.assertEqual(len(parser.ids), len(set(parser.ids)), f"day-{day} duplicate ids")

    def test_all_local_html_links_and_assets_resolve(self):
        failures = []
        for page in WEB.glob("*.html"):
            parser = parse(page)
            for target in parser.links:
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    failures.append(f"external or unsupported link: {page.name} -> {target}")
                    continue
                path_text = target.split("#", 1)[0]
                if path_text and not (page.parent / path_text).exists():
                    failures.append(f"missing: {page.name} -> {target}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_interactive_model_contracts(self):
        expected_ids = {
            "day-2.html": {"bridge-ebit", "bridge-fcff"},
            "day-3.html": {"audit-summary"},
            "day-4.html": {"dcf-fcf", "dcf-equity", "dcf-terminal-share"},
            "day-5.html": {"reverse-target", "reverse-body"},
            "day-6.html": {"method-business", "method-result"},
            "day-7.html": {"yofc-wacc", "yofc-conversion", "yofc-bull"},
        }
        for name, expected in expected_ids.items():
            actual = set(parse(WEB / name).ids)
            self.assertTrue(expected.issubset(actual), f"{name}: {expected - actual}")

    def test_data_term_references_resolve_in_glossary(self):
        glossary_keys = set(re.findall(r'"([^"]+)":\s*\{', (WEB / "assets/glossary.js").read_text()))
        self.assertTrue(glossary_keys, "no term keys parsed from glossary.js")
        failures = []
        for page in WEB.glob("*.html"):
            used = set(re.findall(r'data-term="([^"]+)"', page.read_text()))
            missing = used - glossary_keys
            if missing:
                failures.append(f"{page.name}: {missing}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_glossary_entries_have_a_source_heading(self):
        # Guards the one drift direction that matters when web content leads docs:
        # every term the web defines must still be traceable to docs/GLOSSARY.md.
        glossary_keys = set(re.findall(r'"([^"]+)":\s*\{', (WEB / "assets/glossary.js").read_text()))
        headings = re.findall(r"^## (.+)$", (DOCS / "GLOSSARY.md").read_text(), re.MULTILINE)
        combined = "\n".join(h.replace(" ", "") for h in headings)
        missing = [key for key in glossary_keys if key.replace(" ", "") not in combined]
        self.assertEqual(missing, [], f"glossary.js keys with no docs/GLOSSARY.md heading: {missing}")

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed; browser JavaScript remains runtime-only")
    def test_javascript_syntax(self):
        for script in (WEB / "assets").glob("*.js"):
            result = subprocess.run(["node", "--check", str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed; browser model parity cannot run")
    def test_browser_dcf_matches_python_fixture(self):
        script = WEB / "assets/tools.js"
        js = (
            f"require({json.dumps(str(script))});"
            "const r=globalThis.ValuationLabTools.dcf({baseFcf:10,growth:.08,years:7,"
            "terminalGrowth:.02,discountRate:.09,netDebt:20});"
            "process.stdout.write(JSON.stringify(r));"
        )
        result = subprocess.run(["node", "-e", js], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertAlmostEqual(output["ev"], 204.08792958352166, places=10)
        self.assertAlmostEqual(output["equity"], 184.08792958352166, places=10)
        self.assertAlmostEqual(output["terminalShare"], 0.66936902981735, places=10)


if __name__ == "__main__":
    unittest.main()
