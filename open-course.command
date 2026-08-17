#!/bin/zsh

set -e

SCRIPT_DIR=${0:A:h}
COURSE_PORT=8765

cd "$SCRIPT_DIR"
python3 -m http.server "$COURSE_PORT" --directory . >/tmp/valuation-lab-course.log 2>&1 &
COURSE_SERVER_PID=$!

cleanup() {
  kill "$COURSE_SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 0.5
open "http://127.0.0.1:${COURSE_PORT}/web/index.html"

echo "估值判断力课程已打开。关闭这个窗口即可停止本地课程服务。"
wait "$COURSE_SERVER_PID"
