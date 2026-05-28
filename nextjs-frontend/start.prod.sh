#!/bin/bash

# 构建生产版本
# bun --bun run build

# 启动 Next.js 生产服务器（前台运行）
bun --bun run start &

# 运行 watcher.js（如果需要）
bun watcher.js &

# 等待所有后台进程
wait
