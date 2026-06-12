#!/bin/bash
# 自动拉取GitHub最新预测数据

cd /Users/hubin/Downloads/AI世界杯
git pull origin main >> pull_log.txt 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Git pull completed" >> pull_log.txt
