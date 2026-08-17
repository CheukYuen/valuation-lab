# 互动课程使用说明

推荐在 macOS 中双击仓库根目录的 `open-course.command`。它会从仓库根目录启动本地课程并打开首页，因此课程可以继续访问对应Markdown、Python源码和长飞冻结材料；关闭随之出现的终端窗口即可停止。

也可以直接打开 `index.html`。全部课程和计算都能离线运行，但部分浏览器对 `file://` 页面分开保存学习进度；使用启动器可以确保七课共享同一份进度和笔记。

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
