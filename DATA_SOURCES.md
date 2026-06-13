# 📊 数据源与比赛结果管理

本项目支持从多个来源获取2026年世界杯的比赛结果。

---

## 🌐 官方数据源

### 1. FIFA官方API (worldcupjson.net)

**自动化工具**: `fetch_fifa_results.py`

```bash
python3 fetch_fifa_results.py
```

**功能**:
- ✅ 从世界杯官方数据源获取最新比赛结果
- ✅ 自动加载当前已记录的结果
- ✅ 智能合并新旧数据
- ✅ 自动更新 `generate_predictions.py`
- ✅ 生成 `fifa_match_results.json` 供查看

**工作流程**:
```
worldcupjson.net 
    ↓
fetch_fifa_results.py 获取2026年数据
    ↓
提取已完成的比赛
    ↓
与现有数据合并
    ↓
更新 generate_predictions.py
    ↓
自动触发预测重新生成
```

**当世界杯开始时**:
- API会自动提供实时的比赛数据
- 运行此脚本会自动获取最新结果
- 网页面板会实时更新显示已完成的比赛

---

## 📝 手动更新方法

### 方法 A: 直接编辑代码（最简单）

编辑 `generate_predictions.py` 中的 `ACTUAL_RESULTS` 字典：

```python
ACTUAL_RESULTS = {
    ('Mexico', 'South Africa'): {'home': 2, 'away': 0, 'status': 'completed', 'source': 'official result'},
    ('South Korea', 'Czech Republic'): {'home': 2, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('Canada', 'Bosnia & Herzegovina'): {'home': 1, 'away': 1, 'status': 'completed', 'source': 'official result'},
    # ← 在这里添加新的比赛结果
    ('Qatar', 'Switzerland'): {'home': 1, 'away': 2, 'status': 'completed', 'source': 'official result'},
}
```

详见: [HOW_TO_UPDATE_RESULTS.md](HOW_TO_UPDATE_RESULTS.md)

### 方法 B: 通过脚本添加

```bash
# 使用Python脚本添加单场比赛结果
python3 -c "
from generate_predictions import ACTUAL_RESULTS
ACTUAL_RESULTS[('Qatar', 'Switzerland')] = {'home': 1, 'away': 2, 'status': 'completed', 'source': 'official result'}
print('已添加比赛结果')
"
```

### 方法 C: 从CSV批量导入

创建 `results.csv`:
```csv
home_team,away_team,home_goals,away_goals
Qatar,Switzerland,1,2
USA,Germany,0,1
Brazil,France,2,1
```

然后运行脚本导入（待实现）。

---

## 📁 相关文件

| 文件 | 说明 |
|------|------|
| `fetch_fifa_results.py` | FIFA官方数据同步工具 |
| `generate_predictions.py` | 预测生成脚本（包含ACTUAL_RESULTS） |
| `fifa_match_results.json` | 从API获取的原始比赛结果 |
| `predictions.json` | 最终的预测结果（包含已完成比赛的实际结果） |
| `HOW_TO_UPDATE_RESULTS.md` | 详细的手动更新指南 |

---

## 🔄 完整的数据更新流程

### 场景 1: 世界杯比赛进行中（自动更新）

```
每2小时的云端定时任务:
├─ fetch_fifa_results.py
│  ├─ 连接到 worldcupjson.net
│  ├─ 获取最新的2026年比赛结果
│  └─ 更新 generate_predictions.py
│
└─ generate_predictions.py
   ├─ 读取更新后的 ACTUAL_RESULTS
   ├─ 重新生成预测 (应用新权重)
   ├─ 生成 predictions.json
   └─ 推送到 GitHub
```

**本地同步**:
```
每2小时的本地cron:
└─ pull_updates.sh
   └─ git pull 最新数据
      └─ 网页自动刷新显示
```

### 场景 2: 手动添加单场比赛结果

```
1. 编辑 generate_predictions.py 
   └─ 在 ACTUAL_RESULTS 中添加新比赛

2. 运行预测生成
   └─ python3 generate_predictions.py

3. 提交更改
   └─ git add . && git push

4. 网页自动显示最新数据
```

### 场景 3: 批量导入多场比赛结果

```
1. 从官方渠道（FIFA.com, ESPN等）获取结果

2. 使用 fetch_fifa_results.py
   └─ python3 fetch_fifa_results.py
      └─ 自动识别新结果并更新

3. 或手动编辑多行ACTUAL_RESULTS
   └─ python3 generate_predictions.py
      └─ 自动更新predictions.json

4. 网页显示所有已完成比赛
```

---

## 🎯 数据验证

### 检查是否正确导入

```bash
# 查看当前已记录的结果
python3 -c "
from generate_predictions import ACTUAL_RESULTS
print(f'已记录 {len(ACTUAL_RESULTS)} 场比赛:')
for (home, away), result in ACTUAL_RESULTS.items():
    print(f'  {home} {result[\"home\"]}:{result[\"away\"]} {away}')
"

# 查看预测结果
python3 -c "
import json
with open('predictions.json', 'r') as f:
    data = json.load(f)
    completed = sum(1 for g in data['groups'] for m in g['predictions'] if m['result_status'] == 'completed')
    print(f'预测中已显示 {completed} 场完成的比赛')
"
```

### 网页验证

打开 http://localhost:8888，查看：
- ✓ 已完成比赛显示实际比分
- ✓ 预测与实际比分对比
- ✓ 当日比赛面板实时更新

---

## 📈 实时监控

### 查看同步日志

```bash
# 云端任务日志
tail -20 update_log.txt

# 本地拉取日志
tail -10 pull_log.txt

# 官方数据同步结果
cat fifa_match_results.json | python3 -m json.tool | head -30
```

### 检查API连接状态

```bash
# 测试worldcupjson.net连接
curl -s https://worldcupjson.net/matches?year=2026 | python3 -c "
import sys, json
data = json.load(sys.stdin)
completed = [m for m in data if m.get('status', '').lower() == 'completed']
print(f'API状态: ✓ 连接成功')
print(f'总比赛数: {len(data)}')
print(f'已完成: {len(completed)}')
" || echo "API连接失败"
```

---

## 🚀 自动化配置

### 云端定时任务 (已配置)

```
Routine ID: trig_01BQnT1A9bvgr7PMnAUf8sBe
Cron: 0 */2 * * * (每2小时)
```

查看详情: https://claude.ai/code/routines/trig_01BQnT1A9bvgr7PMnAUf8sBe

### 本地cron (已配置)

```bash
# 查看本地cron任务
crontab -l | grep pull_updates

# 输出示例:
# 0 */2 * * * /Users/hubin/Downloads/AI世界杯/pull_updates.sh
```

---

## 💡 最佳实践

### ✅ 应该做的

1. **定期检查同步**
   ```bash
   python3 fetch_fifa_results.py
   ```

2. **验证数据完整性**
   ```bash
   python3 -c "from generate_predictions import ACTUAL_RESULTS; print(len(ACTUAL_RESULTS))"
   ```

3. **监控网页显示**
   - 定期刷新 http://localhost:8888
   - 检查已完成比赛是否显示正确

4. **保持Git更新**
   ```bash
   git pull origin main
   ```

### ❌ 不应该做的

1. **不要直接修改predictions.json**
   - 此文件会被自动覆盖
   - 修改ACTUAL_RESULTS然后运行generate_predictions.py

2. **不要混用数据源**
   - 使用fetch_fifa_results.py 或 手动编辑
   - 不要同时用两种方法

3. **不要删除已有的比赛结果**
   - fetch脚本会智能合并
   - 手动编辑时务必保留现有结果

---

## 📞 故障排除

### fetch_fifa_results.py无法连接

```bash
# 检查网络连接
curl -I https://worldcupjson.net/

# 检查Python环境
python3 -c "import urllib.request; print('OK')"

# 尝试代理或VPN
```

### ACTUAL_RESULTS格式错误

```bash
# 验证Python语法
python3 -m py_compile generate_predictions.py

# 查看错误信息
python3 generate_predictions.py 2>&1 | head -20
```

### 网页不显示新数据

```bash
# 1. 检查predictions.json是否更新
stat predictions.json

# 2. 刷新浏览器(Ctrl+F5)

# 3. 检查浏览器控制台是否有错误
# 打开 http://localhost:8888 → F12 → Console
```

### 云端定时任务未运行

查看: https://claude.ai/code/routines/trig_01BQnT1A9bvgr7PMnAUf8sBe

检查:
- ✓ 任务是否启用 (enabled: true)
- ✓ Cron表达式是否正确
- ✓ 环境变量是否配置

---

## 📚 相关文档

- [HOW_TO_UPDATE_RESULTS.md](HOW_TO_UPDATE_RESULTS.md) - 详细的手动更新指南
- [SYSTEM_STATUS.md](SYSTEM_STATUS.md) - 系统状态监控面板
- [weight_optimization_report.md](weight_optimization_report.md) - 权重优化分析

---

**更新时间**: 2026-06-13  
**FIFA API**: worldcupjson.net  
**数据更新**: 每2小时（自动）
