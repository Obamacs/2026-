#!/usr/bin/env python3
"""
定时更新博彩赔率和预测结果的脚本
根据最新赔率和权重融合算法，实时更新预测
所有时间基准: 北京时间 (UTC+8)
"""

import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# 导入北京时间工具
import sys
sys.path.insert(0, str(ROOT))
from beijing_time import get_beijing_timestamp, get_today_range_beijing, to_beijing_time

def log_update(message):
    """记录更新日志（北京时间）"""
    timestamp = get_beijing_timestamp()
    log_file = ROOT / 'update_log.txt'
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def run_prediction_generation():
    """运行预测生成脚本"""
    try:
        log_update("开始生成新预测...")
        result = subprocess.run(
            ['python3', str(ROOT / 'generate_predictions.py')],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            log_update("✓ 预测生成成功")
            return True
        else:
            log_update(f"✗ 预测生成失败: {result.stderr}")
            return False
    except Exception as e:
        log_update(f"✗ 预测生成异常: {str(e)}")
        return False

def check_odds_updated():
    """检查赔率是否有更新"""
    try:
        # 检查bookmaker_odds.json的修改时间
        odds_file = ROOT / 'bookmaker_odds.json'
        if not odds_file.exists():
            log_update("⚠️ 赔率文件不存在，需要运行预测生成")
            return False

        # 获取文件修改时间
        mtime = odds_file.stat().st_mtime
        now = datetime.now().timestamp()
        age_minutes = (now - mtime) / 60

        log_update(f"赔率文件年龄: {age_minutes:.1f} 分钟")

        # 如果赔率超过60分钟没有更新，认为需要更新
        return age_minutes > 60

    except Exception as e:
        log_update(f"✗ 检查赔率失败: {str(e)}")
        return False

def get_today_matches_count():
    """获取今日比赛数量（北京时间）"""
    try:
        with open(ROOT / 'predictions.json', 'r') as f:
            data = json.load(f)

        today_start, today_end = get_today_range_beijing()
        count = 0
        for group in data['groups']:
            for match in group['predictions']:
                match_dt = datetime.fromisoformat(match['datetime'].replace('Z', '+00:00'))
                bj_match_dt = to_beijing_time(match_dt)
                if today_start <= bj_match_dt <= today_end:
                    count += 1

        return count
    except Exception as e:
        log_update(f"⚠️ 获取今日比赛失败: {e}")
        return 0

def determine_update_interval():
    """根据比赛情况确定最佳更新间隔"""
    today_matches = get_today_matches_count()

    if today_matches > 0:
        # 比赛当天：每30分钟更新一次（高频率）
        log_update(f"📅 今日有{today_matches}场比赛 → 30分钟更新一次")
        return 30
    else:
        # 非比赛日期：每2小时更新一次（低频率）
        log_update("📅 今日无比赛 → 2小时更新一次")
        return 120

def main():
    """主函数"""
    log_update("=" * 80)
    log_update("📊 开始定时更新流程")
    log_update("=" * 80)

    # 1. 检查赔率是否需要更新
    odds_need_update = check_odds_updated()

    if odds_need_update:
        log_update("🔄 赔率已过期，正在从API获取最新赔率...")
        # 赔率更新会在generate_predictions.py中通过fetch_bookmaker_odds_from_api()自动处理
    else:
        log_update("✓ 赔率仍为最新，使用本地缓存")

    # 2. 运行预测生成（这会自动处理赔率更新和权重融合）
    success = run_prediction_generation()

    # 3. 确定下次更新间隔
    interval = determine_update_interval()

    if success:
        log_update(f"✓ 预测已更新，下次更新间隔: {interval}分钟")
    else:
        log_update(f"⚠️ 预测更新失败，下次重试间隔: 15分钟")
        interval = 15

    log_update("=" * 80)
    log_update(f"下次更新时间: {(datetime.now() + timedelta(minutes=interval)).isoformat()}")
    log_update("=" * 80)

    return interval

if __name__ == '__main__':
    import sys
    interval = main()
    # 返回下次更新间隔（秒）
    sys.exit(0)
