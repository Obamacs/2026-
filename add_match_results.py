#!/usr/bin/env python3
"""
世界杯比赛成绩更新工具
支持手动输入新的比赛结果，自动更新predictions和权重配置
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent

def load_actual_results():
    """加载当前的ACTUAL_RESULTS"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("generate_predictions",
                                                    ROOT / 'generate_predictions.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(module.ACTUAL_RESULTS)

def display_current_results():
    """显示当前已记录的比赛成绩"""
    print("\n📋 当前已记录的比赛成绩:\n")
    print("="*80)

    try:
        results = load_actual_results()

        for i, ((home, away), data) in enumerate(sorted(results.items()), 1):
            print(f"{i}. {home} {data['home']}:{data['away']} {away}")

        print(f"\n总计: {len(results)} 场\n")
        return results
    except Exception as e:
        print(f"⚠️ 加载失败: {e}")
        return {}

def add_single_match():
    """添加单场比赛结果"""
    print("\n➕ 添加新的比赛成绩\n")
    print("="*80)

    home = input("主队队名: ").strip()
    away = input("客队队名: ").strip()
    home_goals = int(input("主队进球数: "))
    away_goals = int(input("客队进球数: "))

    return (home, away, home_goals, away_goals)

def add_batch_matches():
    """批量添加比赛结果"""
    print("\n📊 批量添加比赛成绩\n")
    print("="*80)
    print("请按以下格式输入比赛成绩:")
    print("格式: 主队名称 比分 客队名称 (例: Mexico 2:0 South Africa)")
    print("输入 'done' 完成输入\n")

    matches = []
    while True:
        line = input("比赛成绩: ").strip()

        if line.lower() == 'done':
            break

        try:
            parts = line.split()
            if len(parts) < 3:
                print("⚠️ 格式错误，请重试")
                continue

            # 找到比分位置
            score_part = None
            score_idx = None
            for i, part in enumerate(parts):
                if ':' in part:
                    score_part = part
                    score_idx = i
                    break

            if score_part is None:
                print("⚠️ 找不到比分，请使用 X:Y 格式")
                continue

            home = ' '.join(parts[:score_idx])
            away = ' '.join(parts[score_idx+1:])
            home_goals, away_goals = map(int, score_part.split(':'))

            matches.append((home, away, home_goals, away_goals))
            print(f"✓ 已添加: {home} {home_goals}:{away_goals} {away}")

        except Exception as e:
            print(f"⚠️ 解析失败: {e}，请重试")

    return matches

def update_actual_results(new_matches):
    """更新ACTUAL_RESULTS"""
    try:
        # 加载当前结果
        current = load_actual_results()

        # 添加新结果
        for home, away, home_goals, away_goals in new_matches:
            current[(home, away)] = {
                'home': home_goals,
                'away': away_goals,
                'status': 'completed',
                'source': 'official result'
            }

        # 更新generate_predictions.py
        gen_file = ROOT / 'generate_predictions.py'
        content = gen_file.read_text(encoding='utf-8')

        # 生成新的ACTUAL_RESULTS代码
        import re
        results_code = "ACTUAL_RESULTS = {\n"
        for (home, away), data in sorted(current.items()):
            results_code += f"    ('{home}', '{away}'): {{'home': {data['home']}, 'away': {data['away']}, 'status': 'completed', 'source': 'official result'}},\n"
        results_code += "}"

        # 替换旧的ACTUAL_RESULTS
        pattern = r'ACTUAL_RESULTS = \{[^}]*\}'
        content = re.sub(pattern, results_code, content, flags=re.DOTALL)

        gen_file.write_text(content, encoding='utf-8')

        print(f"\n✅ 已保存 {len(new_matches)} 场新比赛")
        print(f"📊 总共记录: {len(current)} 场")

        return True
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False

def regenerate_predictions():
    """重新生成预测"""
    import subprocess

    print("\n🔄 重新生成预测中...")
    try:
        result = subprocess.run(
            ['python3', str(ROOT / 'generate_predictions.py')],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            print("✓ 预测生成成功！")
            return True
        else:
            print(f"⚠️ 生成失败: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("🌍 世界杯AI预测系统 - 比赛成绩更新工具")
    print("="*80)

    # 显示当前成绩
    current_results = display_current_results()

    # 选择更新方式
    print("\n更新选项:")
    print("1. 添加单场比赛")
    print("2. 批量添加多场比赛")
    print("0. 退出")

    choice = input("\n请选择 (0-2): ").strip()

    new_matches = []

    if choice == '1':
        home, away, hg, ag = add_single_match()
        new_matches = [(home, away, hg, ag)]
    elif choice == '2':
        new_matches = add_batch_matches()
    else:
        print("退出")
        return

    if not new_matches:
        print("⚠️ 没有新的比赛成绩")
        return

    # 更新结果
    if update_actual_results(new_matches):
        # 重新生成预测
        if regenerate_predictions():
            print("\n" + "="*80)
            print("✅ 更新完成！")
            print("\n📌 后续步骤:")
            print("1. 刷新网页: http://localhost:8888")
            print("   Mac: Cmd + Shift + R")
            print("   Windows: Ctrl + Shift + R")
            print("2. 查看最新预测结果")
            print("3. 系统将在2小时内自动更新一次")
            print("="*80)
        else:
            print("⚠️ 预测生成失败，请手动运行 generate_predictions.py")
    else:
        print("❌ 更新失败")

if __name__ == '__main__':
    main()
