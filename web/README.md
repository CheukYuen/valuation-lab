# 互动课程使用说明

## 打开方式

**直接打开：**

```bash
open web/index.html
```

**用 HTTP 打开（推荐）：** 部分浏览器在 `file://` 下会把各课进度分开保存；用本地 HTTP 可避免这个问题。

在仓库根目录执行：

```bash
python3 -m http.server 8765 --directory web
```

浏览器打开 [http://127.0.0.1:8765/](http://127.0.0.1:8765/)，或执行 `open http://127.0.0.1:8765/`。停服务按 `Ctrl+C`。

互动版不请求外部网络，不上传学习记录。完成状态、复习勾选和笔记保存在浏览器本机。

每一课的「运行环节」展示对应 `lab/`（或案例旋钮脚本）的核心公式、运行按钮和终端风格输出。计算仍调用 `assets/tools.js`，与 Python 脚本逐字段对齐；第1课校验全文与第7课旋钮摘要在离线页内置，便于先写后跑。

## 专业参考章

每一课标题栏的文档图标会打开由对应 `course/DAY-N.md` 生成的离线专业参考页。Markdown 是该抽屉内容的唯一来源；修改后运行：

```bash
python3 scripts/render_course_markdown.py
```

检查生成页是否仍与 Markdown 同步：

```bash
python3 scripts/render_course_markdown.py --check
```

生成器只接受课程使用的受控 Markdown 子集，遇到未支持的语法会失败，不会静默省略内容。生成页在抽屉里隐藏顶栏，单独打开时使用与课程页相同的导航。

同一个生成器还会把四份课程资料和两份测验渲染成离线页：`docs/AUDIT-CHECKLIST.md`、`docs/GLOSSARY.md`、`docs/FIVE-NUMBERS.md`、`course/PRETEST.md`、`course/POSTTEST.md`。浏览器不渲染 `.md`，直接链接过去会变成下载，所以课程内部的链接一律指向这些生成页；仍指向 `.md` 原文件的，只有明确标注「打开原始 Markdown」或用文件名当标签的溯源链接。`cases/` 下的案例材料和 `lab/` 脚本保持原文件。
