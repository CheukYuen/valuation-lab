#!/usr/bin/env python3
"""Render the controlled Day 1 Markdown subset into an offline HTML reference."""

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
SOURCE = ROOT / "course" / "DAY-1.md"
OUTPUT = ROOT / "web" / "generated" / "day-1-reference.html"
STYLESHEET = ROOT / "web" / "assets" / "styles.css"

HEADING = re.compile(r"^(#{1,4})\s+(.+)$")
LIST_ITEM = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.+)$")
SUMMARY = re.compile(r"^<summary>(.*?)</summary>$")
TABLE_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")
FENCE = re.compile(r"^```([A-Za-z0-9_-]*)$")


class MarkdownRenderError(ValueError):
    """Raised when source Markdown leaves the supported, fail-closed subset."""


def relative_href(target: Path, output: Path) -> str:
    return os.path.relpath(target, output.parent).replace(os.sep, "/")


def rewrite_link(href: str, source: Path, output: Path) -> str:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or href.startswith("#"):
        return href
    if not parsed.path:
        return href
    target = (source.parent / parsed.path).resolve()
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
            href = html.escape(rewrite_link(match.group(2), source, output), quote=True)
            return stash(f'<a href="{href}">{label}</a>')

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
            rendered.append(f"<h{level}>{render_inline(heading.group(2), source, output)}</h{level}>")
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


def build_document(source: Path = SOURCE, output: Path = OUTPUT) -> str:
    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    article = render_markdown(source_bytes.decode("utf-8"), source, output)
    stylesheet = html.escape(relative_href(STYLESHEET, output), quote=True)
    source_link = html.escape(relative_href(source, output), quote=True)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="source-sha256" content="{source_hash}">
  <title>Day 1 专业参考章</title>
  <link rel="stylesheet" href="{stylesheet}">
</head>
<body class="markdown-reference-page">
  <main class="markdown-reference-document">
    <p class="markdown-reference-source">由 <a href="{source_link}">course/DAY-1.md</a> 生成 · SHA-256 {source_hash[:12]}</p>
{article}
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify that the generated reference is current")
    args = parser.parse_args()

    try:
        expected = build_document()
    except (OSError, UnicodeError, MarkdownRenderError) as error:
        print(f"render failed: {error}", file=sys.stderr)
        return 1

    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
            print(f"generated reference is stale: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
            return 1
        print(f"generated reference is current: {OUTPUT.relative_to(ROOT)}")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(expected, encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
