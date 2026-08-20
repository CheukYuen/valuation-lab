# 互动课程使用说明

直接打开 `index.html`。全部课程和计算都能离线运行。部分浏览器对 `file://` 页面分开保存学习进度，若七课进度或笔记对不上，可改用同一浏览器窗口从首页进入各课。

互动版不请求外部网络，不上传学习记录。完成状态、复习勾选和笔记保存在浏览器本机。

## Day 1 专业参考章

Day 1 标题栏的文档图标会打开由 [`course/DAY-1.md`](../course/DAY-1.md) 生成的离线专业参考页。Markdown 是该抽屉内容的唯一来源；修改后运行：

```bash
python3 scripts/render_course_markdown.py
```

检查生成页是否仍与 Markdown 同步：

```bash
python3 scripts/render_course_markdown.py --check
```

生成器只接受课程使用的受控 Markdown 子集，遇到未支持的语法会失败，不会静默省略内容。
