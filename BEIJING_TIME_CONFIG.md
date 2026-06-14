# ⏰ 北京时间统一配置

**更新时间**: 2026-06-14  
**时间基准**: 北京时间 (UTC+8)  
**时区标准**: Asia/Shanghai

---

## 📍 系统时间标准

本系统的所有时间处理都统一以北京时间为基准：

| 组件 | 时间标准 | 说明 |
|------|--------|------|
| **日志记录** | 北京时间 CST | 格式: `YYYY-MM-DD HH:MM:SS CST` |
| **网页显示** | 北京时间 | JavaScript使用 `Asia/Shanghai` 时区 |
| **比赛时间** | 北京时间 | 所有比赛时间转换为北京时间 |
| **定时任务** | UTC时间 | 云端任务设置见下文 |
| **数据存储** | ISO 8601 | 内部存储为ISO格式,显示时转换 |

---

## 🔧 北京时间处理模块

**文件**: `beijing_time.py`

### 可用函数

```python
from beijing_time import (
    get_beijing_time,           # 获取当前北京时间datetime对象
    get_beijing_timestamp,      # 获取北京时间戳字符串 (用于日志)
    get_beijing_date_str,       # 获取北京日期 YYYY-MM-DD
    to_beijing_time,           # 将任意datetime转换为北京时间
    get_today_range_beijing,   # 获取今日北京时间范围
    format_beijing_time,       # 格式化北京时间
    BEIJING_TZ,               # 北京时区对象
)
```

### 使用示例

```python
# 获取当前北京时间戳（用于日志）
from beijing_time import get_beijing_timestamp
timestamp = get_beijing_timestamp()  # '2026-06-14 14:30:45 CST'

# 获取今日范围（用于过滤今日比赛）
from beijing_time import get_today_range_beijing
today_start, today_end = get_today_range_beijing()

# 转换任意时间为北京时间（用于比赛时间处理）
from beijing_time import to_beijing_time
match_dt = datetime.fromisoformat('2026-06-14T06:00:00+00:00')
bj_time = to_beijing_time(match_dt)  # 2026-06-14 14:00:00 CST
```

---

## 📝 各文件的时间配置

### 1. **generate_predictions.py**
- **比赛时间**: ISO 8601格式存储
- **显示**: 通过网页JavaScript转换为北京时间
- **日志**: 使用Python标准timezone处理

### 2. **update_predictions_scheduled.py**
- **日志时间**: 北京时间戳 (`[2026-06-14 14:30:45 CST]`)
- **今日比赛判断**: 基于北京时间的00:00-23:59
- **更新频率**: 有比赛日30分钟,无比赛日2小时

### 3. **add_match_results.py**
- **显示时间**: 北京时间戳
- **用户输入处理**: 假设用户输入的是北京时间

### 4. **fetch_fifa_results.py**
- **同步时间**: 北京时间戳显示
- **API数据**: 转换为北京时间后处理
- **日志记录**: 北京时间

### 5. **index.html** (网页前端)
```javascript
// 将ISO时间转换为北京时间显示
function formatBeijingTime(datetime) {
    const date = new Date(datetime);
    return date.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', hour12: false });
}

// 获取北京时区的今日日期
const bjToday = new Date(new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }));
```

---

## 🌐 云端定时任务时间配置

**Routine ID**: `trig_01BQnT1A9bvgr7PMnAUf8sBe`

### 时间转换规则

| 北京时间 | UTC时间 | Cron表达式 |
|--------|--------|----------|
| 每天 00:00 | 前一天 16:00 | `0 16 * * *` |
| 每天 12:00 | 04:00 | `0 4 * * *` |
| 每2小时 | - | `0 */2 * * *` |
| 每30分钟 | - | `*/30 * * * *` |

**当前配置**:
```
Cron: 0 */2 * * * (UTC)
含义: 每天 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00, 22:00, 00:00, 02:00, 04:00, 06:00 (北京时间)
```

### 更新Cron表达式

如果需要在特定北京时间运行，使用以下转换：

```
北京时间 = UTC时间 + 8小时
UTC时间 = 北京时间 - 8小时

示例:
- 北京时间 09:00 (赛前检查) → UTC 01:00 → cron: "0 1 * * *"
- 北京时间 18:00 (赛后更新) → UTC 10:00 → cron: "0 10 * * *"
```

---

## ✅ 验证时间配置

### 检查系统时区

```bash
# 查看系统当前时区
date
# 输出示例: Fri Jun 14 14:30:45 CST 2026

# 查看UTC时间
date -u
# 输出示例: Fri Jun 14 06:30:45 UTC 2026
```

### 检查日志时间

```bash
# 查看update_log.txt中的时间戳
tail -5 update_log.txt
# 输出示例:
# [2026-06-14 14:30:45 CST] ✓ 预测生成成功
# [2026-06-14 14:35:22 CST] 赔率文件年龄: 5.3 分钟
```

### 验证比赛时间转换

```bash
# 运行北京时间测试
python3 -c "
from beijing_time import *
from datetime import datetime

# 测试时间转换
utc_dt = datetime.fromisoformat('2026-06-14T06:00:00+00:00')
bj_dt = to_beijing_time(utc_dt)
print(f'UTC: {utc_dt}')
print(f'Beijing: {bj_dt}')
print(f'Timestamp: {format_beijing_time(utc_dt)}')
"
```

---

## 📊 时间处理流程图

```
API数据 (UTC+0) 
    ↓
parse_2026_date() → ISO 8601 格式
    ↓
generate_predictions.py → predictions.json (ISO格式存储)
    ↓
网页JavaScript显示
    ↓
formatBeijingTime() → 北京时间显示
    ↓
用户在北京时间下查看 (Asia/Shanghai)
```

---

## 🎯 关键时间点

当前系统中的重要时间点（以北京时间显示）:

| 时间点 | 用途 | 处理方式 |
|--------|------|--------|
| **比赛开始前2小时** | 准备阶段 | 云端刷新赔率,更新预测 |
| **比赛结束后30分钟** | 更新成绩 | 自动获取结果,更新predictions |
| **每天 00:00** | 日更新 | 重新计算高风险比赛 |
| **有比赛日每30分钟** | 高频更新 | 赔率变化监控 |
| **无比赛日每2小时** | 低频更新 | 维持基础数据新鲜度 |

---

## 📌 最佳实践

### ✅ 应该做的

1. **所有日志**: 使用 `get_beijing_timestamp()`
   ```python
   from beijing_time import get_beijing_timestamp
   log(f"[{get_beijing_timestamp()}] 处理完成")
   ```

2. **时间比较**: 使用 `get_today_range_beijing()`
   ```python
   from beijing_time import get_today_range_beijing
   today_start, today_end = get_today_range_beijing()
   if today_start <= match_time <= today_end:
       # 今日比赛
   ```

3. **时间转换**: 使用 `to_beijing_time()`
   ```python
   from beijing_time import to_beijing_time
   bj_time = to_beijing_time(utc_datetime)
   ```

### ❌ 不应该做的

1. **不要** 使用 `datetime.now()` (这会返回本地时间,假设为CST)
   - 改用: `get_beijing_time()`

2. **不要** 硬编码时区偏移 (如 `timedelta(hours=8)`)
   - 改用: 从 `beijing_time` 导入 `BEIJING_TZ`

3. **不要** 混合UTC和本地时间比较
   - 改用: 统一转换为北京时间后再比较

---

## 🔄 云端任务配置更新

如果需要调整云端定时任务的运行时间，使用以下步骤：

1. **转换北京时间到UTC**
   ```
   北京时间 09:00 → UTC 01:00
   Cron: 0 1 * * *
   ```

2. **查看当前任务**
   ```bash
   # 查看云端任务信息
   # URL: https://claude.ai/code/routines/trig_01BQnT1A9bvgr7PMnAUf8sBe
   ```

3. **更新任务配置**
   - 通过Claude Code平台修改Cron表达式
   - 或联系系统管理员

---

**最后更新**: 2026-06-14 14:30 CST  
**下次审查**: 2026-07-01
