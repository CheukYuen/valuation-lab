import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
DOCS = ROOT / "docs"


def camel(name):
    head, *rest = name.split("_")
    return head + "".join(word[:1].upper() + word[1:] for word in rest)


def to_js_input(payload):
    """把 lab/inputs/*.json 转成 tools.js 用的驼峰输入，跳过 _ 开头的说明字段。"""
    out = {}
    for key, value in payload.items():
        if key.startswith("_") or isinstance(value, str):
            continue
        out[camel(key)] = to_js_input(value) if isinstance(value, dict) else value
    return out


def run_node(expression):
    script = WEB / "assets/tools.js"
    js = (f"require({json.dumps(str(script))});"
          f"process.stdout.write(JSON.stringify({expression}));")
    result = subprocess.run(["node", "-e", js], capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = []
        self.quiz_cards = 0
        self.complete_buttons = 0
        self.sorter_items = 0
        self.agent_audits = 0
        self.agent_issues = 0
        self.agent_variants = 0
        self.correct_states = []
        self.markdown_openers = 0
        self.markdown_dialogs = 0
        self.markdown_frames = 0
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
        if "data-sorter-item" in values:
            self.sorter_items += 1
        if "data-agent-audit" in values:
            self.agent_audits += 1
        if "data-agent-issue" in values:
            self.agent_issues += 1
        if "data-agent-variant" in values:
            self.agent_variants += 1
        if "data-correct-state" in values:
            self.correct_states.append(values["data-correct-state"])
        if "data-markdown-reference-open" in values:
            self.markdown_openers += 1
        if "data-markdown-reference-dialog" in values:
            self.markdown_dialogs += 1
        if "data-markdown-reference-frame" in values:
            self.markdown_frames += 1
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
        for page in WEB.rglob("*.html"):
            parser = parse(page)
            for target in parser.links:
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                if target.startswith("#"):
                    if target[1:] not in parser.ids:
                        failures.append(f"missing anchor: {page.name} -> {target}")
                    continue
                path_text, _, fragment = target.partition("#")
                if path_text and not (page.parent / path_text).exists():
                    failures.append(f"missing: {page.name} -> {target}")
                    continue
                # 跨文件锚点也要真的存在，否则跳转会停在页首而不报错。
                if fragment and path_text.endswith(".html"):
                    if fragment not in parse(page.parent / path_text).ids:
                        failures.append(f"missing anchor: {page.name} -> {target}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_interactive_model_contracts(self):
        expected_ids = {
            "day-2.html": {"bridge-pre-depreciation-profit", "bridge-ebit", "bridge-fcff", "ocf-ocf"},
            "day-3.html": {"pit-nd-low"},
            "day-4.html": {"dcf-fcf", "dcf-equity", "dcf-terminal-share", "dcf-implied-multiple"},
            "day-5.html": {"reverse-target", "reverse-body", "reverse-years"},
            "day-6.html": {"method-business", "method-result"},
            "day-7.html": {"yofc-wacc", "yofc-conversion", "yofc-bull"},
        }
        for name, expected in expected_ids.items():
            actual = set(parse(WEB / name).ids)
            self.assertTrue(expected.issubset(actual), f"{name}: {expected - actual}")

    def test_day_one_dual_track_interaction_contract(self):
        parser = parse(WEB / "day-1.html")
        self.assertEqual(parser.sorter_items, 10)
        self.assertEqual(parser.agent_variants, 2)
        self.assertEqual(parser.agent_audits, 2)
        self.assertEqual(parser.agent_issues, 10)
        self.assertIn("agent-audit-summary", parser.ids)

        text = (WEB / "day-1.html").read_text()
        for value in ["fact", "guidance", "forecast", "assumption", "derived", "judgment"]:
            self.assertIn(f'data-sorter-choice="{value}"', text)
        for grade in ["usable", "partial", "unknown"]:
            self.assertIn(f'data-agent-grade="{grade}"', text)

    def test_day_one_audit_scores_judgement_not_clicks(self):
        # The old exercise shipped the answer inside the button and scored "clicked
        # all five". Every clause must now carry a hidden answer the learner picks.
        text = (WEB / "day-1.html").read_text()
        parser = parse(WEB / "day-1.html")
        self.assertEqual(len(parser.correct_states), parser.agent_issues)
        for state in ["consensus", "pit", "bridge", "evidence", "recompute", "conflict", "compliant"]:
            self.assertIn(f'data-agent-state="{state}"', text)

    def test_day_one_audit_has_a_negative_control(self):
        # CLAUDE.md: 危险信号是筛查线索，不自动等于模型错误. Without compliant clauses a
        # learner who flags everything scores full marks, which teaches the opposite.
        parser = parse(WEB / "day-1.html")
        self.assertGreaterEqual(parser.correct_states.count("compliant"), 3)

        text = (WEB / "day-1.html").read_text()
        # The two outputs must not resolve to the same usage grade, otherwise the
        # exercise never shows that a known gap can still be 带条件使用.
        self.assertIn('data-agent-answer="unknown"', text)
        self.assertIn('data-agent-answer="partial"', text)

    def test_day_one_has_a_test_authoring_exercise(self):
        parser = parse(WEB / "day-1.html")
        self.assertIn("write-test", parser.ids)
        text = (WEB / "day-1.html").read_text()
        self.assertIn('data-note="day-1-tests"', text)
        self.assertIn("什么必须<strong>不变</strong>", text)

    def test_day_one_markdown_reference_contract(self):
        parser = parse(WEB / "day-1.html")
        self.assertEqual(parser.markdown_openers, 1)
        self.assertEqual(parser.markdown_dialogs, 1)
        self.assertEqual(parser.markdown_frames, 1)
        self.assertIn("day-1-markdown-reference", parser.ids)

        generated = WEB / "generated" / "day-1-reference.html"
        self.assertTrue(generated.is_file())
        generated_text = generated.read_text()
        self.assertNotIn("\x00", generated_text)
        source_hash = hashlib.sha256((ROOT / "course" / "DAY-1.md").read_bytes()).hexdigest()
        self.assertIn(f'<meta name="source-sha256" content="{source_hash}">', generated_text)
        for heading in ["专业标注不是一个", "记录验证状态与材料使用等级", "失败状态矩阵", "一页验收清单"]:
            self.assertIn(heading, generated_text)

        result = subprocess.run(
            ["python3", str(ROOT / "scripts" / "render_course_markdown.py"), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        page_text = (WEB / "day-1.html").read_text()
        self.assertIn('aria-controls="day-1-markdown-reference"', page_text)
        self.assertIn('aria-expanded="false"', page_text)
        self.assertIn('src="generated/day-1-reference.html"', page_text)

    def test_every_lesson_uses_the_reader_chrome_and_shared_nav(self):
        nav = ["href=\"index.html\"", "href=\"glossary.html\"", "href=\"study-methods.html\""]
        for day in range(1, 8):
            page = WEB / f"day-{day}.html"
            text = page.read_text()
            parser = parse(page)
            self.assertIn('class="reader-page"', text, page.name)
            self.assertIn("reader-topbar", text, page.name)
            self.assertIn("估值实验室", text, page.name)
            self.assertIn("data-course-switcher-list", text, page.name)
            self.assertEqual(parser.markdown_openers, 1, page.name)
            self.assertEqual(parser.markdown_dialogs, 1, page.name)
            self.assertEqual(parser.markdown_frames, 1, page.name)
            self.assertIn(f"day-{day}-markdown-reference", parser.ids)
            self.assertIn(f'src="generated/day-{day}-reference.html"', text)
            self.assertIn('data-open-reference-window', text, page.name)
            self.assertIn(f'href="generated/day-{day}-reference.html"', text)
            self.assertIn("新窗口打开", text, page.name)
            for item in nav:
                self.assertIn(item, text, f"{page.name} missing {item}")

        for name in ("index.html", "glossary.html", "study-methods.html"):
            text = (WEB / name).read_text()
            self.assertIn("reader-topbar", text, name)
            self.assertIn("估值实验室", text, name)
            for item in nav:
                self.assertIn(item, text, f"{name} missing {item}")

    def test_every_lesson_has_a_generated_markdown_reference(self):
        result = subprocess.run(
            ["python3", str(ROOT / "scripts" / "render_course_markdown.py"), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for day in range(1, 8):
            generated = WEB / "generated" / f"day-{day}-reference.html"
            self.assertTrue(generated.is_file(), generated.name)
            text = generated.read_text()
            self.assertNotIn("\x00", text)
            source_hash = hashlib.sha256((ROOT / "course" / f"DAY-{day}.md").read_bytes()).hexdigest()
            self.assertIn(f'<meta name="source-sha256" content="{source_hash}">', text)
            self.assertIn("reader-topbar", text)
            self.assertIn("估值实验室", text)
            self.assertIn("markdown-reference-lesson-nav", text)
            self.assertIn("../index.html", text)
            self.assertIn("../glossary.html", text)
            self.assertIn("../study-methods.html", text)
            self.assertIn(f"../day-{day}.html", text)

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

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed; browser model parity cannot run")
    def test_browser_bridge_matches_lab_bridge_field_by_field(self):
        # CLAUDE.md：互动计算必须调用 tools.js 的唯一实现，并与 lab/ 下的 Python 函数一致。
        # 期望值不硬编码——直接从 lab/bridge.py 取真值，Python 改了公式这里立刻红。
        sys.path.insert(0, str(ROOT / "lab"))
        from bridge import bridge  # noqa: PLC0415

        params = json.loads((ROOT / "lab/inputs/bridge.json").read_text())
        expected = bridge(params)
        actual = run_node(f"globalThis.ValuationLabTools.bridge({json.dumps(to_js_input(params))})")

        self.assertEqual(sorted(actual), sorted(camel(k) for k in expected))
        for key, value in expected.items():
            self.assertAlmostEqual(actual[camel(key)], value, places=10, msg=key)

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed; browser model parity cannot run")
    def test_depreciation_change_updates_ebit_nopat_and_fcff(self):
        params = {
            "preDepreciationOperatingProfit": 23,
            "taxRate": 0.2,
            "depreciation": 1.5,
            "capex": 5,
            "workingCapitalIncrease": 2,
        }
        actual = run_node(
            f"globalThis.ValuationLabTools.fcffFromPreDepreciation({json.dumps(params)})"
        )
        self.assertAlmostEqual(actual["ebit"], 21.5)
        self.assertAlmostEqual(actual["nopat"], 17.2)
        self.assertAlmostEqual(actual["fcff"], 11.7)

    def assert_js_matches(self, expected, actual):
        self.assertEqual(sorted(actual), sorted(camel(k) for k in expected))
        for key, value in expected.items():
            if value is None:
                self.assertIsNone(actual[camel(key)], key)
            else:
                self.assertAlmostEqual(actual[camel(key)], value, places=10, msg=key)

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed; browser model parity cannot run")
    def test_browser_ocf_check_matches_lab(self):
        sys.path.insert(0, str(ROOT / "lab"))
        from bridge import ocf_check  # noqa: PLC0415

        params = json.loads((ROOT / "lab/inputs/bridge.json").read_text())
        for classification in ("operating", "financing"):
            with self.subTest(classification=classification):
                params["interest_cash_flow_classification"] = classification
                expected = ocf_check(params)
                js_params = to_js_input(params)
                js_params["interestCashFlowClassification"] = classification
                actual = run_node(
                    f"globalThis.ValuationLabTools.ocfCheck({json.dumps(js_params)})"
                )
                self.assert_js_matches(expected, actual)

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed; browser model parity cannot run")
    def test_browser_pit_bridge_matches_lab(self):
        sys.path.insert(0, str(ROOT / "lab"))
        from bridge import pit_bridge  # noqa: PLC0415

        params = json.loads((ROOT / "lab/inputs/bridge.json").read_text())
        expected = pit_bridge(params)
        actual = run_node(f"globalThis.ValuationLabTools.pitBridge({json.dumps(to_js_input(params))})")
        self.assert_js_matches(expected, actual)

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed; browser model parity cannot run")
    def test_browser_terminal_bridge_matches_lab(self):
        sys.path.insert(0, str(ROOT / "lab"))
        from mini_dcf import terminal_bridge  # noqa: PLC0415

        params = json.loads((ROOT / "lab/inputs/simple.json").read_text())
        js_input = json.dumps(to_js_input(params))
        gordon = run_node(f"globalThis.ValuationLabTools.terminalBridge({js_input})")
        self.assert_js_matches(terminal_bridge(params), gordon)
        ten = run_node(f"globalThis.ValuationLabTools.terminalBridge({js_input}, 10)")
        self.assert_js_matches(terminal_bridge(params, 10), ten)

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed; browser model parity cannot run")
    def test_browser_required_years_matches_lab(self):
        sys.path.insert(0, str(ROOT / "lab"))
        from reverse import required_years  # noqa: PLC0415

        params = json.loads((ROOT / "lab/inputs/simple.json").read_text())
        js_input = json.dumps(to_js_input(params))
        actual = run_node(f"globalThis.ValuationLabTools.requiredYears({js_input}, 300)")
        self.assert_js_matches(required_years(params, 300), actual)

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed; browser model parity cannot run")
    def test_browser_methods_match_lab_methods(self):
        sys.path.insert(0, str(ROOT / "lab"))
        from methods import bank_demo, multiples  # noqa: PLC0415

        params = json.loads((ROOT / "lab/inputs/methods.json").read_text())
        js_input = json.dumps(to_js_input(params))
        for name, expected in (("multiples", multiples(params)), ("bankDemo", bank_demo(params))):
            actual = run_node(f"globalThis.ValuationLabTools.{name}({js_input})")
            for key, value in expected.items():
                self.assertAlmostEqual(actual[camel(key)], value, places=10, msg=f"{name}.{key}")

    def test_every_lesson_has_a_lab_run_panel(self):
        expected = {
            1: ("record-contract", "运行复算"),
            2: ("bridge", "运行复算"),
            3: ("record-contract", "运行契约校验"),
            4: ("mini-dcf", "运行复算"),
            5: ("reverse", "运行复算"),
            6: ("methods", "运行复算"),
            7: ("knobs", "运行旋钮实验"),
        }
        for day, (kind, button) in expected.items():
            text = (WEB / f"day-{day}.html").read_text()
            self.assertIn('id="lab-run"', text, f"day-{day}")
            self.assertIn(f'data-lab-run="{kind}"', text, f"day-{day}")
            self.assertIn("data-lab-run-button", text, f"day-{day}")
            self.assertIn("data-lab-run-output", text, f"day-{day}")
            self.assertIn("lab-run-core", text, f"day-{day}")
            self.assertIn(button, text, f"day-{day}")
            self.assertIn("assets/tools.js", text, f"day-{day} must load tools.js")
        day3 = (WEB / "day-3.html").read_text()
        self.assertIn('data-lab-run="pit"', day3)
        self.assertIn("运行时点桥", day3)
    def test_reference_drawer_links_never_navigate_inside_the_drawer(self):
        # 参考章是在右侧抽屉的 iframe 里打开的：任何链接都不能把整页文档塞回这个窄抽屉。
        app = (WEB / "assets/app.js").read_text()
        self.assertIn("setupEmbeddedReferenceLinks();", app)
        self.assertIn('const REFERENCE_CLOSE_MESSAGE = "valuation-lab:close-reference";', app)
        # file:// 下父子文档是不同源，只能比对 window 引用，不能比对 origin。
        self.assertIn("event.source !== frame.contentWindow", app)
        self.assertNotIn("event.origin", app)
        self.assertIn('link.target = "_top";', app)
        self.assertIn('href.startsWith("#")', app)
        # file:// 新窗口不能带 noopener，否则会从 about:blank 再跳本地文件而被拦截。
        self.assertNotIn("noopener,noreferrer", app)
        self.assertIn('rel="opener"', (WEB / "day-2.html").read_text())

        for day in range(1, 8):
            text = (WEB / "generated" / f"day-{day}-reference.html").read_text()
            body = re.sub(r'<header class="reader-topbar">.*?</header>', "", text, flags=re.DOTALL)
            interactive = set(re.findall(r'href="(\.\./day-\d\.html)"', body))
            self.assertTrue(interactive, f"day-{day}-reference.html has no link back to its lesson")
            self.assertEqual(
                interactive,
                {f"../day-{day}.html"},
                f"day-{day}-reference.html links to another lesson's interactive page",
            )

    def test_course_documents_reach_the_browser_as_html(self):
        # 浏览器不渲染 .md：课程内部的材料必须有 HTML 双胞胎，否则点击变成下载。
        script = ROOT / "scripts" / "render_course_markdown.py"
        spec = importlib.util.spec_from_file_location("render_course_markdown_documents", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        twins = {ROOT / "course" / lesson["source"] for lesson in module.LESSONS}
        twins |= {ROOT / document["path"] for document in module.DOCUMENTS}

        for document in module.DOCUMENTS:
            source = ROOT / document["path"]
            generated = WEB / "generated" / document["output"]
            self.assertTrue(source.is_file(), document["path"])
            self.assertTrue(generated.is_file(), document["output"])
            text = generated.read_text()
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertIn(f'<meta name="source-sha256" content="{source_hash}">', text)
            self.assertIn("reader-topbar", text, document["output"])
            self.assertIn(document["title"], text, document["output"])

        # 唯一允许指向 .md 原文件的，是标签本身就说明这是原始材料的溯源链接。
        link = re.compile(r'<a [^>]*href="([^"#?]+\.md)"[^>]*>(.*?)</a>', re.DOTALL)
        offenders = []
        for page in sorted(WEB.rglob("*.html")):
            for href, label in link.findall(page.read_text()):
                target = (page.parent / href).resolve()
                if target not in twins:
                    continue
                text = re.sub(r"<[^>]+>", "", label).strip()
                if ".md" in text or "原始 Markdown" in text:
                    continue
                offenders.append(f"{page.relative_to(ROOT)}: {text} -> {href}")
        self.assertEqual(offenders, [], "\n".join(offenders))

    def test_the_shared_engine_is_the_only_place_formulas_live(self):
        # 页面可以读 tools.js 的结果，但不能自己再写一份算式。
        source = (WEB / "assets/tools.js").read_text()
        exported = re.search(r"globalThis\.ValuationLabTools = \{([^}]+)\}", source)
        self.assertIsNotNone(exported, "tools.js no longer exports a tool surface")
        names = {name.strip() for name in exported.group(1).split(",")}
        self.assertTrue(
            {"bridge", "fcffBridge", "fcffFromPreDepreciation", "ocfCheck", "pitBridge", "terminalBridge",
             "requiredYears", "multiples", "bankDemo", "LAB_RUNNERS"}.issubset(names),
            names,
        )

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed; browser model parity cannot run")
    def test_lab_runners_emit_script_style_output(self):
        bridge_out = run_node("globalThis.ValuationLabTools.LAB_RUNNERS.bridge()")
        self.assertIn("FCFF", bridge_out)
        self.assertIn("12.00", bridge_out)
        dcf_out = run_node('globalThis.ValuationLabTools.LAB_RUNNERS["mini-dcf"]()')
        self.assertIn("184.09", dcf_out)
        reverse_out = run_node("globalThis.ValuationLabTools.LAB_RUNNERS.reverse()")
        self.assertIn("23", reverse_out)
        methods_out = run_node("globalThis.ValuationLabTools.LAB_RUNNERS.methods()")
        self.assertIn("1.46", methods_out)
    @unittest.skipUnless(shutil.which("node"), "Node.js not installed; browser JavaScript remains runtime-only")
    def test_javascript_syntax(self):
        for script in (WEB / "assets").glob("*.js"):
            result = subprocess.run(["node", "--check", str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed; browser model parity cannot run")
    def test_browser_dcf_matches_python_fixture(self):
        sys.path.insert(0, str(ROOT / "lab"))
        from mini_dcf import value  # noqa: PLC0415

        params = json.loads((ROOT / "lab/inputs/simple.json").read_text())
        expected = value(params)
        actual = run_node(f"globalThis.ValuationLabTools.dcf({json.dumps(to_js_input(params))})")
        self.assertAlmostEqual(actual["ev"], expected["enterprise_value"], places=10)
        self.assertAlmostEqual(actual["equity"], expected["equity_value"], places=10)
        self.assertAlmostEqual(actual["terminalShare"], expected["terminal_share"], places=10)


if __name__ == "__main__":
    unittest.main()
