#!/usr/bin/env python3
"""
从FIFA官方数据源获取2026年世界杯的最新比赛结果

当2026年世界杯开始时，此脚本将自动从官方数据源获取实时结果。
"""

import json
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from beijing_time import get_beijing_timestamp

# 球队名称标准化映射
TEAM_NORMALIZATION = {
    'Korea Republic': 'South Korea',
    'Republic of Korea': 'South Korea',
    'Czech Republic': 'Czech Republic',
    'Czechia': 'Czech Republic',
    'United States': 'USA',
    'Korea DPR': 'North Korea',
}

def normalize_team_name(name: str) -> str:
    """规范化球队名称"""
    name = name.strip()
    return TEAM_NORMALIZATION.get(name, name)


def fetch_from_worldcupjson() -> List[Dict]:
    """从 worldcupjson.net 获取2026年世界杯数据"""
    print("🌐 尝试从 worldcupjson.net 获取官方数据...\n")
    try:
        url = 'https://worldcupjson.net/matches?year=2026'
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))

        print(f"   ✓ 成功获取 {len(data)} 场比赛数据")

        # 计算已完成的比赛数
        completed = [m for m in data if m.get('status', '').lower() == 'completed']
        print(f"   ✓ 其中 {len(completed)} 场已完成\n")

        return data
    except Exception as e:
        print(f"   ✗ 连接失败: {e}\n")
        return []


def extract_2026_results(matches: List[Dict]) -> Dict[Tuple[str, str], Dict]:
    """从原始数据提取2026年已完成的比赛结果"""
    results = {}

    for match in matches:
        try:
            # 检查年份 (只要2026年的数据)
            datetime_str = match.get('datetime', '')
            if not datetime_str.startswith('2026'):
                continue

            # 解析球队信息
            home_team_data = match.get('home_team', {})
            away_team_data = match.get('away_team', {})

            home_team = normalize_team_name(
                home_team_data.get('name', '') if isinstance(home_team_data, dict) else str(home_team_data)
            )
            away_team = normalize_team_name(
                away_team_data.get('name', '') if isinstance(away_team_data, dict) else str(away_team_data)
            )

            if not home_team or not away_team:
                continue

            # 解析进球数
            home_goals = home_team_data.get('goals') if isinstance(home_team_data, dict) else None
            away_goals = away_team_data.get('goals') if isinstance(away_team_data, dict) else None

            # 检查比赛状态
            status = match.get('status', 'scheduled').lower()

            # 只保存已完成的比赛
            if status == 'completed' and home_goals is not None and away_goals is not None:
                results[(home_team, away_team)] = {
                    'home': int(home_goals),
                    'away': int(away_goals),
                    'status': 'completed',
                    'source': 'official result',
                    'date': datetime_str[:10],
                }
        except Exception:
            continue

    return results


def load_current_results() -> Dict[Tuple[str, str], Dict]:
    """从 generate_predictions.py 加载当前的ACTUAL_RESULTS"""
    try:
        import sys
        sys.path.insert(0, str(ROOT))
        from generate_predictions import ACTUAL_RESULTS
        return dict(ACTUAL_RESULTS)
    except Exception:
        return {}


def merge_results(existing: Dict, new: Dict) -> Dict:
    """合并新旧比赛结果，新结果优先"""
    merged = existing.copy()
    merged.update(new)
    return merged


def update_actual_results(all_results: Dict[Tuple[str, str], Dict]) -> int:
    """更新 generate_predictions.py 中的 ACTUAL_RESULTS"""
    if not all_results:
        print("⚠️  没有比赛结果可更新")
        return 0

    gen_file = ROOT / 'generate_predictions.py'
    content = gen_file.read_text(encoding='utf-8')

    # 生成新的 ACTUAL_RESULTS 字典
    results_code = "ACTUAL_RESULTS = {\n"
    for (home, away), result in sorted(all_results.items()):
        results_code += f"    ('{home}', '{away}'): {{'home': {result['home']}, 'away': {result['away']}, 'status': 'completed', 'source': 'official result'}},\n"
    results_code += "}"

    # 替换旧的 ACTUAL_RESULTS
    import re
    pattern = r'ACTUAL_RESULTS = \{[^}]*\}'
    content = re.sub(pattern, results_code, content, flags=re.DOTALL)

    gen_file.write_text(content, encoding='utf-8')

    print(f"✅ 已更新 {len(all_results)} 场比赛结果\n")
    return len(all_results)


def save_results_json(results: Dict[Tuple[str, str], Dict]):
    """保存结果到JSON文件以供查看"""
    results_json = ROOT / 'fifa_match_results.json'

    # 转换为可序列化的格式
    serializable = {}
    for (home, away), data in sorted(results.items()):
        serializable[f"{home} vs {away}"] = data

    with open(results_json, 'w', encoding='utf-8') as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)

    print(f"💾 结果已保存到 fifa_match_results.json")


def print_summary(results: Dict[Tuple[str, str], Dict]):
    """打印汇总信息"""
    if not results:
        print("\nℹ️  当前没有2026年世界杯的已完成比赛数据")
        print("   2026年世界杯预计在6月中旬开始\n")
        return

    print("\n" + "="*80)
    print(f"\n📊 发现 {len(results)} 场已完成的比赛:\n")

    # 按日期分组
    by_date = {}
    for (home, away), data in results.items():
        date = data.get('date', '未知')
        if date not in by_date:
            by_date[date] = []
        by_date[date].append((home, away, data['home'], data['away']))

    for date in sorted(by_date.keys()):
        matches = by_date[date]
        print(f"📅 {date}")
        for home, away, h_goals, a_goals in matches:
            print(f"   • {home} {h_goals}:{a_goals} {away}")

    print("\n" + "="*80)


def main():
    print("\n" + "="*80)
    print("🌍 FIFA 2026年世界杯 - 官方数据同步工具")
    print(f"📍 时区: 北京时间 (UTC+8)")
    print(f"⏰ 同步时间: {get_beijing_timestamp()}")
    print("="*80 + "\n")

    # 加载当前的结果
    current_results = load_current_results()
    print(f"📦 当前系统已记录: {len(current_results)} 场比赛\n")

    if current_results:
        for (home, away), data in sorted(current_results.items()):
            print(f"   ✓ {home} vs {away} ({data['home']}:{data['away']})")
        print()

    # 尝试从官方API获取新数据
    matches = fetch_from_worldcupjson()

    if not matches:
        print("⚠️  无法连接到官方数据源")
        print("\n💡 可用的替代方案:")
        print("   1. 查看 HOW_TO_UPDATE_RESULTS.md")
        print("   2. 稍后重试此脚本")
        print("   3. 手动编辑 generate_predictions.py\n")
        return

    # 提取2026年的结果
    new_results = extract_2026_results(matches)

    if not new_results:
        print("⚠️  API中没有2026年世界杯的已完成比赛数据")
        print("   这是正常的，因为世界杯尚未开始\n")
        return

    # 合并结果
    all_results = merge_results(current_results, new_results)

    # 检查是否有新的比赛结果
    new_count = len(new_results)
    added_count = len(set(new_results.keys()) - set(current_results.keys()))

    if added_count > 0:
        print(f"🆕 发现 {added_count} 场新的比赛结果\n")
    else:
        print("✓ 没有新的比赛结果\n")

    # 保存结果
    save_results_json(new_results if new_results else current_results)

    # 如果有新结果，更新代码
    if added_count > 0:
        update_actual_results(all_results)

        # 打印汇总
        print_summary(new_results)

        print("\n✅ 完成！下一步:")
        print("   1. 运行: python3 generate_predictions.py")
        print("   2. 刷新网页查看最新数据")
    else:
        print_summary(current_results)


if __name__ == '__main__':
    main()
