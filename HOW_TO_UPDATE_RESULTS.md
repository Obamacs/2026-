# 📝 如何更新比赛结果

## 当前系统状态

**已记录的比赛结果**: 3 场

```
✓ Mexico vs South Africa        2:0 (主队赢)  [预测正确]
✓ South Korea vs Czech Republic 2:1 (主队赢)  [预测错误]
✓ Canada vs Bosnia & Herzegovina 1:1 (平局)   [预测错误]
```

---

## 方法一：直接编辑代码（推荐）

### 步骤 1: 打开 `generate_predictions.py`

找到第31-35行的 `ACTUAL_RESULTS` 部分：

```python
ACTUAL_RESULTS = {
    ('Mexico', 'South Africa'): {'home': 2, 'away': 0, 'status': 'completed', 'source': 'official result'},
    ('South Korea', 'Czech Republic'): {'home': 2, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('Canada', 'Bosnia & Herzegovina'): {'home': 1, 'away': 1, 'status': 'completed', 'source': 'official result'},
}
```

### 步骤 2: 添加新比赛结果

#### 示例 1：新增 Qatar vs Switzerland (1:2 客队赢)

```python
ACTUAL_RESULTS = {
    ('Mexico', 'South Africa'): {'home': 2, 'away': 0, 'status': 'completed', 'source': 'official result'},
    ('South Korea', 'Czech Republic'): {'home': 2, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('Canada', 'Bosnia & Herzegovina'): {'home': 1, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('Qatar', 'Switzerland'): {'home': 1, 'away': 2, 'status': 'completed', 'source': 'official result'},  # ← 新增
}
```

#### 示例 2：批量添加多场

```python
ACTUAL_RESULTS = {
    ('Mexico', 'South Africa'): {'home': 2, 'away': 0, 'status': 'completed', 'source': 'official result'},
    ('South Korea', 'Czech Republic'): {'home': 2, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('Canada', 'Bosnia & Herzegovina'): {'home': 1, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('USA', 'Netherlands'): {'home': 1, 'away': 0, 'status': 'completed', 'source': 'official result'},
    ('Germany', 'France'): {'home': 2, 'away': 1, 'status': 'completed', 'source': 'official result'},
}
```

### 步骤 3: 关键规则

**球队名称必须完全匹配**预定义的列表：

✓ 正确:
- `'USA'` (不是 'United States')
- `'South Korea'` (不是 'Korea Republic')
- `'Czech Republic'` (不是 'Czechia')
- `'Germany'` (不是 'West Germany')

❌ 错误:
- `'United States'` → 应该是 `'USA'`
- `'Korea'` → 应该是 `'South Korea'`

**比分格式**:
```python
{'home': 2, 'away': 1}  # 主队2分，客队1分
```

---

## 方法二：通过脚本更新

### 创建临时脚本 `update_results.py`

```python
import json
from pathlib import Path

# 新结果
new_results = {
    ('Qatar', 'Switzerland'): {'home': 1, 'away': 2, 'status': 'completed', 'source': 'official result'},
    ('Brazil', 'Germany'): {'home': 2, 'away': 0, 'status': 'completed', 'source': 'official result'},
}

# 读取代码，更新ACTUAL_RESULTS
root = Path('.')
gen_file = root / 'generate_predictions.py'
content = gen_file.read_text()

# 找到ACTUAL_RESULTS的结束位置，插入新结果
# （这种方法略复杂，建议用方法一）
```

---

## 方法三：Git提交更新

### 通过命令行快速更新

```bash
cd /Users/hubin/Downloads/AI世界杯

# 1. 编辑generate_predictions.py，添加新比赛结果

# 2. 验证修改
git diff generate_predictions.py

# 3. 提交更改
git add generate_predictions.py
git commit -m "更新比赛结果: 新增 Qatar vs Switzerland (1:2)"

# 4. 推送到GitHub
git push origin main

# 5. 重新生成预测
python3 generate_predictions.py
```

---

## 更新后的流程

### 自动发生的事情：

1. **重新计算预测** (运行 `generate_predictions.py`)
   - XGBoost模型预测所有比赛
   - Context特征分析
   - 融合 (应用新权重)
   - 生成 `predictions.json`

2. **分析准确度**
   - 对比预测 vs 实际结果
   - 计算各模型准确度
   - 评估是否需要调整权重

3. **更新网页显示**
   - 已完成比赛显示实际结果
   - 预测与实际对比显示
   - 准确度统计更新

---

## 数据质量检查

### 验证新增结果是否有效

```bash
python3 -c "
import json
from pathlib import Path

with open('generate_predictions.py', 'r') as f:
    content = f.read()
    
# 检查球队名称是否标准化
if \"'USA'\" in content and \"'United States'\" in content:
    print('⚠️ 警告: 混用了USA和United States')
    
# 检查ACTUAL_RESULTS格式
print('✓ 检查完成')
"
```

---

## 关键提示

### 💡 添加结果时要注意

1. **球队名称**必须与其他地方一致
   - 查看 `TEAM_NORMALIZATION` 字典获取标准名称
   - 例如: `'Korea Republic'` → `'South Korea'`

2. **比分格式**总是 `{'home': X, 'away': Y}`
   - `home` = 主队进球数
   - `away` = 客队进球数

3. **保存后运行预测**
   ```bash
   python3 generate_predictions.py
   ```

4. **检查输出**
   ```bash
   # 查看是否有错误信息
   tail -20 update_log.txt
   ```

---

## 完整示例：添加5场比赛

在 `ACTUAL_RESULTS` 中添加：

```python
ACTUAL_RESULTS = {
    # 已有结果
    ('Mexico', 'South Africa'): {'home': 2, 'away': 0, 'status': 'completed', 'source': 'official result'},
    ('South Korea', 'Czech Republic'): {'home': 2, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('Canada', 'Bosnia & Herzegovina'): {'home': 1, 'away': 1, 'status': 'completed', 'source': 'official result'},
    
    # 新增结果 - 第一周比赛
    ('Qatar', 'Switzerland'): {'home': 1, 'away': 2, 'status': 'completed', 'source': 'official result'},
    ('USA', 'Netherlands'): {'home': 0, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('Germany', 'France'): {'home': 2, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('Brazil', 'England'): {'home': 1, 'away': 1, 'status': 'completed', 'source': 'official result'},
    ('Argentina', 'Italy'): {'home': 3, 'away': 0, 'status': 'completed', 'source': 'official result'},
}
```

---

## 何时更新权重？

当完成 **5-10 场新比赛**后：

1. 运行准确度分析
   ```bash
   python3 analyze_weights.py
   ```

2. 生成新的权重报告
   ```bash
   python3 generate_predictions.py --analyze
   ```

3. 如果准确度有明显变化（±10%），考虑调整权重

---

## 常见问题

### Q: 如果球队名称错误会怎样？
A: 系统会忽略该条目，不会产生错误。检查 `TEAM_NORMALIZATION` 确保名称正确。

### Q: 添加结果后需要重启网页吗？
A: 不需要。只要运行 `python3 generate_predictions.py` 更新 `predictions.json`，刷新浏览器即可看到新数据。

### Q: 可以修改已有的比赛结果吗？
A: 可以。直接修改字典中对应条目的分数，然后运行 `generate_predictions.py`。

### Q: 需要手动提交到GitHub吗？
A: 不需要。每2小时的云端任务会自动检查并推送最新数据。但为了安全，建议定期手动 `git push`。

---

**需要帮助？** 随时告诉我要添加的比赛结果！📊
