#!/bin/bash

echo "🚀 启动 AnyRouter 签到管理系统..."

# 启动定时任务调度器（后台运行）
echo "📅 启动定时任务调度器..."
python3 web/scheduler.py &
SCHEDULER_PID=$!

# 等待一下确保调度器启动
sleep 2

# 启动 Web 服务
echo "🌐 启动 Web 服务..."
python3 web/api.py

# 如果 Web 服务退出，也停止调度器
kill $SCHEDULER_PID 2>/dev/null
