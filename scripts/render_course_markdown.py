#!/usr/bin/env python3
"""Render each course DAY-*.md file into an offline HTML reference."""

from __future__ import annotations

import argparse
import hashlib
import html
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
COURSE = ROOT / "course"
OUTPUT_DIR = ROOT / "web" / "generated"
STYLESHEET = ROOT / "web" / "assets" / "styles.css"
APP_SCRIPT = ROOT / "web" / "assets" / "app.js"

LESSONS = [
    {"day": 1, "source": "DAY-1.md", "output": "day-1-reference.html", "title": "模型到底在说什么", "interactive": "day-1.html"},
    {"day": 2, "source": "DAY-2.md", "output": "day-2-reference.html", "title": "亲手打通价值桥", "interactive": "day-2.html"},
    {"day": 3, "source": "DAY-3.md", "output": "day-3-reference.html", "title": "检查估值输入", "interactive": "day-3.html"},
    {"day": 4, "source": "DAY-4.md", "output": "day-4-reference.html", "title": "完成最小 DCF", "interactive": "day-4.html"},
    {"day": 5, "source": "DAY-5.md", "output": "day-5-reference.html", "title": "反向 DCF", "interactive": "day-5.html"},
    {"day": 6, "source": "DAY-6.md", "output": "day-6-reference.html", "title": "方法适不适合", "interactive": "day-6.html"},
    {"day": 7, "source": "DAY-7.md", "output": "day-7-reference.html", "title": "长飞综合练习", "interactive": "day-7.html"},
]

DOCUMENTS = [
    {"path": "docs/AUDIT-CHECKLIST.md", "output": "audit-checklist-reference.html", "title": "分层审计清单", "eyebrow": "检查材料时使用"},
    {"path": "docs/GLOSSARY.md", "output": "glossary-reference.html", "title": "白话术语表", "eyebrow": "查陌生术语"},
    {"path": "docs/FIVE-NUMBERS.md", "output": "five-numbers-reference.html", "title": "DCF 的五个控制杆", "eyebrow": "第4课可选补充"},
    {"path": "course/PRETEST.md", "output": "pretest-reference.html", "title": "入门测验", "eyebrow": "开课前"},
    {"path": "course/POSTTEST.md", "output": "posttest-reference.html", "title": "毕业测验", "eyebrow": "第7课之后"},
]

SOURCE = COURSE / "DAY-1.md"
OUTPUT = OUTPUT_DIR / "day-1-reference.html"

HEADING = re.compile(r"^(#{1,4})\s+(.+)$")
SOURCE_ID = re.compile(r"〔(D[1-7]-S\d+)〕")
LIST_ITEM = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.+)$")
SUMMARY = re.compile(r"^<summary>(.*?)</summary>$")
TABLE_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")
FENCE = re.compile(r"^```([A-Za-z0-9_-]*)$")


class MarkdownRenderError(ValueError):
    """Raised when source Markdown leaves the supported, fail-closed subset."""


def relative_href(target: Path, output: Path) -> str:
    return os.path.relpath(target, output.parent).replace(os.sep, "/")


def generated_twin(target: Path) -> Path:
    """课程内部的链接留在 HTML 这条线上：浏览器不会渲染 .md，直接点会变成下载。"""
    for lesson in LESSONS:
        if target == COURSE / lesson["source"]:
            return OUTPUT_DIR / lesson["output"]
    for document in DOCUMENTS:
        if target == ROOT / document["path"]:
            return OUTPUT_DIR / document["output"]
    return target


def rewrite_link(href: str, source: Path, output: Path) -> str:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or href.startswith("#"):
        return href
    if not parsed.path:
        return href
    target = (source.parent / parsed.path).resolve()
    target = generated_twin(target)
    rewritten = relative_href(target, output)
    return urlunsplit(("", "", rewritten, parsed.query, parsed.fragment))


def render_inline(text: str, source: Path, output: Path, *, allow_links: bool = True) -> str:
    if "![" in text:
        raise MarkdownRenderError("images are not supported in the controlled Markdown subset")
    if text.count("`") % 2:
        raise MarkdownRenderError(f"unmatched inline code marker: {text}")

    tokens: list[str] = []

    def stash(value: str) -> str:
        token = f"\x00MDTOKEN{len(tokens)}\x00"
        tokens.append(value)
        return token

    protected = text
    if allow_links:
        def link_replacement(match: re.Match[str]) -> str:
            label = render_inline(match.group(1), source, output, allow_links=False)
            raw_href = match.group(2)
            href = html.escape(rewrite_link(raw_href, source, output), quote=True)
            parsed = urlsplit(raw_href)
            external = ' target="_blank" rel="noopener noreferrer"' if parsed.scheme in {"http", "https"} else ""
            return stash(f'<a href="{href}"{external}>{label}</a>')

        protected = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_replacement, protected)

    def code_replacement(match: re.Match[str]) -> str:
        return stash(f"<code>{html.escape(match.group(1))}</code>")

    protected = re.sub(r"`([^`]+)`", code_replacement, protected)

    rendered = html.escape(protected)
    rendered = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", rendered)
    if "**" in rendered:
        raise MarkdownRenderError(f"unmatched bold marker: {text}")

    for index, value in enumerate(tokens):
        rendered = rendered.replace(f"\x00MDTOKEN{index}\x00", value)
    return rendered


def split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        raise MarkdownRenderError(f"table row must start and end with |: {line}")
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines) or "|" not in lines[index]:
        return False
    try:
        header = split_table_row(lines[index])
        separator = split_table_row(lines[index + 1])
    except MarkdownRenderError:
        return False
    return len(header) == len(separator) and all(TABLE_SEPARATOR_CELL.fullmatch(cell) for cell in separator)


def is_raw_tag(line: str) -> bool:
    stripped = line.strip()
    return stripped in {"<details>", "</details>"} or bool(SUMMARY.fullmatch(stripped))


def is_block_start(lines: list[str], index: int) -> bool:
    line = lines[index]
    stripped = line.strip()
    return bool(
        not stripped
        or HEADING.match(stripped)
        or FENCE.match(stripped)
        or stripped.startswith(">")
        or LIST_ITEM.match(line)
        or is_table_start(lines, index)
        or is_raw_tag(stripped)
        or stripped in {"---", "***"}
    )


def render_list(entries: list[tuple[int, str, str]], source: Path, output: Path) -> str:
    def render_level(position: int, indent: int) -> tuple[str, int]:
        marker = entries[position][1]
        tag = "ul" if marker in {"-", "*"} else "ol"
        start = ""
        if tag == "ol":
            number = int(marker[:-1])
            start = f' start="{number}"' if number != 1 else ""
        parts = [f"<{tag}{start}>"]
        while position < len(entries):
            item_indent, item_marker, item_text = entries[position]
            item_tag = "ul" if item_marker in {"-", "*"} else "ol"
            if item_indent != indent or item_tag != tag:
                break
            parts.append(f"<li>{render_inline(item_text, source, output)}")
            position += 1
            while position < len(entries) and entries[position][0] > indent:
                child, position = render_level(position, entries[position][0])
                parts.append(child)
            parts.append("</li>")
        parts.append(f"</{tag}>")
        return "".join(parts), position

    rendered: list[str] = []
    position = 0
    while position < len(entries):
        block, position = render_level(position, entries[position][0])
        rendered.append(block)
    return "\n".join(rendered)


def render_markdown(markdown: str, source: Path, output: Path) -> str:
    lines = markdown.splitlines()
    rendered: list[str] = []
    index = 0
    details_depth = 0
    slugs: dict[str, int] = {}

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if line.startswith("    ") and not LIST_ITEM.match(line):
            raise MarkdownRenderError(f"indented code is not supported at line {index + 1}")

        heading = HEADING.match(stripped)
        if heading:
            level = len(heading.group(1))
            source_id = SOURCE_ID.search(heading.group(2))
            if heading.group(2) == "资料来源与核查":
                anchor = ' id="sources"'
            elif source_id:
                anchor = f' id="{source_id.group(1)}"'
            else:
                slug = heading_slug(heading.group(2))
                if slug:
                    slugs[slug] = slugs.get(slug, 0) + 1
                    if slugs[slug] > 1:
                        slug = f"{slug}-{slugs[slug] - 1}"
                anchor = f' id="{html.escape(slug, quote=True)}"' if slug else ""
            rendered.append(f"<h{level}{anchor}>{render_inline(heading.group(2), source, output)}</h{level}>")
            index += 1
            continue

        fence = FENCE.match(stripped)
        if fence:
            language = fence.group(1)
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and lines[index].strip() != "```":
                code_lines.append(lines[index])
                index += 1
            if index >= len(lines):
                raise MarkdownRenderError("unclosed fenced code block")
            language_class = f' class="language-{html.escape(language)}"' if language else ""
            rendered.append(f"<pre><code{language_class}>{html.escape(chr(10).join(code_lines))}</code></pre>")
            index += 1
            continue

        if is_table_start(lines, index):
            headers = split_table_row(lines[index])
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                row = split_table_row(lines[index])
                if len(row) != len(headers):
                    raise MarkdownRenderError(f"table width mismatch at line {index + 1}")
                rows.append(row)
                index += 1
            table = ["<div class=\"reference-table-scroll\"><table><thead><tr>"]
            table.extend(f"<th>{render_inline(cell, source, output)}</th>" for cell in headers)
            table.append("</tr></thead><tbody>")
            for row in rows:
                table.append("<tr>")
                table.extend(f"<td>{render_inline(cell, source, output)}</td>" for cell in row)
                table.append("</tr>")
            table.append("</tbody></table></div>")
            rendered.append("".join(table))
            continue

        if stripped.startswith(">"):
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip()[1:].strip())
                index += 1
            rendered.append(f"<blockquote><p>{render_inline(' '.join(quote_lines), source, output)}</p></blockquote>")
            continue

        if LIST_ITEM.match(line):
            entries: list[tuple[int, str, str]] = []
            while index < len(lines):
                item = LIST_ITEM.match(lines[index])
                if not item:
                    break
                entries.append((len(item.group(1).expandtabs(4)), item.group(2), item.group(3)))
                index += 1
            rendered.append(render_list(entries, source, output))
            continue

        if stripped in {"---", "***"}:
            rendered.append("<hr>")
            index += 1
            continue

        if stripped == "<details>":
            details_depth += 1
            rendered.append("<details>")
            index += 1
            continue
        summary = SUMMARY.fullmatch(stripped)
        if summary:
            if details_depth == 0:
                raise MarkdownRenderError(f"summary outside details at line {index + 1}")
            rendered.append(f"<summary>{render_inline(summary.group(1), source, output)}</summary>")
            index += 1
            continue
        if stripped == "</details>":
            if details_depth == 0:
                raise MarkdownRenderError(f"unmatched details close at line {index + 1}")
            details_depth -= 1
            rendered.append("</details>")
            index += 1
            continue
        if stripped.startswith("<"):
            raise MarkdownRenderError(f"unsupported raw HTML at line {index + 1}: {stripped}")

        paragraph: list[str] = []
        while index < len(lines) and not is_block_start(lines, index):
            if lines[index].strip().startswith("<"):
                raise MarkdownRenderError(f"unsupported raw HTML at line {index + 1}: {lines[index].strip()}")
            paragraph.append(lines[index].strip())
            index += 1
        if not paragraph:
            raise MarkdownRenderError(f"unsupported Markdown at line {index + 1}: {lines[index]}")
        rendered.append(f"<p>{render_inline(' '.join(paragraph), source, output)}</p>")

    if details_depth:
        raise MarkdownRenderError("unclosed details block")
    return "\n".join(rendered)


def heading_slug(text: str) -> str:
    """按 GitHub 的标题锚点规则生成 id，让 Markdown 里的 `文件.md#标题` 在生成页同样能跳。"""
    plain = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    plain = plain.replace("`", "").replace("*", "").strip().lower()
    plain = re.sub(r"[^\w\s-]", "", plain, flags=re.UNICODE)
    return re.sub(r"\s+", "-", plain).strip("-")


def lesson_nav(current_day: int) -> str:
    links = []
    for lesson in LESSONS:
        href = html.escape(lesson["output"], quote=True)
        label = html.escape(f'{lesson["day"]}. {lesson["title"]}')
        current = ' class="current" aria-current="page"' if lesson["day"] == current_day else ""
        links.append(f'<a href="{href}"{current}>{label}</a>')
    return "\n      ".join(links)


def document_nav(current_output: str) -> str:
    links = []
    for document in DOCUMENTS:
        href = html.escape(document["output"], quote=True)
        label = html.escape(document["title"])
        current = ' class="current" aria-current="page"' if document["output"] == current_output else ""
        links.append(f'<a href="{href}"{current}>{label}</a>')
    return "\n      ".join(links)


def lesson_for(source: Path) -> dict:
    try:
        return next(item for item in LESSONS if item["source"] == source.name)
    except StopIteration as error:
        raise MarkdownRenderError(f"no lesson registered for {source.name}") from error


def build_document(source: Path | dict = SOURCE, output: Path | None = OUTPUT) -> str:
    lesson = source if isinstance(source, dict) else lesson_for(Path(source))
    source = COURSE / lesson["source"]
    output = OUTPUT_DIR / lesson["output"] if output is None else output
    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    article = render_markdown(source_bytes.decode("utf-8"), source, output)
    stylesheet = html.escape(relative_href(STYLESHEET, output), quote=True)
    app_script = html.escape(relative_href(APP_SCRIPT, output), quote=True)
    source_link = html.escape(relative_href(source, output), quote=True)
    index_link = html.escape(relative_href(ROOT / "web" / "index.html", output), quote=True)
    glossary_link = html.escape(relative_href(ROOT / "web" / "glossary.html", output), quote=True)
    methods_link = html.escape(relative_href(ROOT / "web" / "study-methods.html", output), quote=True)
    interactive_link = html.escape(relative_href(ROOT / "web" / lesson["interactive"], output), quote=True)
    title = html.escape(lesson["title"])
    day = lesson["day"]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="source-sha256" content="{source_hash}">
  <title>第{day}课专业参考章 · {title}</title>
  <link rel="stylesheet" href="{stylesheet}">
  <script>
    if (window.self !== window.top) document.documentElement.classList.add("markdown-reference-embedded");
  </script>
  <script defer src="{app_script}"></script>
</head>
<body class="markdown-reference-page" data-lesson="day-{day}" data-lesson-href-prefix="../">
  <header class="reader-topbar">
    <a class="reader-brand" href="{index_link}" aria-label="返回课程首页">
      <span class="reader-brand-mark" aria-hidden="true">V</span>
      <span><strong>估值实验室</strong><small>看懂估值，不迷信数字</small></span>
    </a>
    <div class="reader-heading">
      <div class="reader-breadcrumb">
        <span>7天估值判断课</span><b>/</b><strong>{title}</strong><em>专业参考章</em>
      </div>
      <div class="reader-course-progress" aria-label="课程位置：第{day}课，共7课"><div class="day-dots" data-day-dots></div><small>{day} / 7</small></div>
    </div>
    <nav class="reader-actions" aria-label="辅助导航"><a href="{index_link}">课程首页</a><a href="{glossary_link}">术语表</a><a href="{methods_link}">学习方法</a></nav>
  </header>
  <main class="markdown-reference-document">
    <nav class="markdown-reference-lesson-nav" aria-label="七课专业参考章">
      {lesson_nav(day)}
    </nav>
    <p class="markdown-reference-source">由 <a href="{source_link}">course/{html.escape(lesson["source"])}</a> 生成 · SHA-256 {source_hash[:12]} · <a href="{interactive_link}">打开本课互动页</a></p>
{article}
  </main>
</body>
</html>
"""


def build_reference_document(document: dict, output: Path | None = None) -> str:
    source = ROOT / document["path"]
    output = OUTPUT_DIR / document["output"] if output is None else output
    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    article = render_markdown(source_bytes.decode("utf-8"), source, output)
    stylesheet = html.escape(relative_href(STYLESHEET, output), quote=True)
    app_script = html.escape(relative_href(APP_SCRIPT, output), quote=True)
    source_link = html.escape(relative_href(source, output), quote=True)
    index_link = html.escape(relative_href(ROOT / "web" / "index.html", output), quote=True)
    glossary_link = html.escape(relative_href(ROOT / "web" / "glossary.html", output), quote=True)
    methods_link = html.escape(relative_href(ROOT / "web" / "study-methods.html", output), quote=True)
    title = html.escape(document["title"])
    eyebrow = html.escape(document["eyebrow"])
    source_label = html.escape(document["path"])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="source-sha256" content="{source_hash}">
  <title>{title} · 课程资料</title>
  <link rel="stylesheet" href="{stylesheet}">
  <script>
    if (window.self !== window.top) document.documentElement.classList.add("markdown-reference-embedded");
  </script>
  <script defer src="{app_script}"></script>
</head>
<body class="markdown-reference-page" data-lesson-href-prefix="../">
  <header class="reader-topbar">
    <a class="reader-brand" href="{index_link}" aria-label="返回课程首页">
      <span class="reader-brand-mark" aria-hidden="true">V</span>
      <span><strong>估值实验室</strong><small>看懂估值，不迷信数字</small></span>
    </a>
    <div class="reader-heading">
      <div class="reader-breadcrumb">
        <span>课程资料</span><b>/</b><strong>{title}</strong><em>{eyebrow}</em>
      </div>
    </div>
    <nav class="reader-actions" aria-label="辅助导航"><a href="{index_link}">课程首页</a><a href="{glossary_link}">术语表</a><a href="{methods_link}">学习方法</a></nav>
  </header>
  <main class="markdown-reference-document">
    <nav class="markdown-reference-lesson-nav" aria-label="课程资料">
      {document_nav(document["output"])}
    </nav>
    <p class="markdown-reference-source">由 <a href="{source_link}">{source_label}</a> 生成 · SHA-256 {source_hash[:12]} · <a href="{index_link}">回到课程首页</a></p>
{article}
  </main>
</body>
</html>
"""


def expected_documents() -> list[tuple[Path, str]]:
    pages = [(OUTPUT_DIR / lesson["output"], build_document(lesson)) for lesson in LESSONS]
    pages.extend((OUTPUT_DIR / item["output"], build_reference_document(item)) for item in DOCUMENTS)
    return pages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify that generated references are current")
    args = parser.parse_args()

    try:
        documents = expected_documents()
    except (OSError, UnicodeError, MarkdownRenderError) as error:
        print(f"render failed: {error}", file=sys.stderr)
        return 1

    if args.check:
        stale = []
        for path, expected in documents:
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                stale.append(str(path.relative_to(ROOT)))
        if stale:
            print("generated reference is stale: " + ", ".join(stale), file=sys.stderr)
            return 1
        print("generated references are current: " + ", ".join(path.relative_to(ROOT).as_posix() for path, _ in documents))
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, expected in documents:
        path.write_text(expected, encoding="utf-8")
        print(f"generated {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
