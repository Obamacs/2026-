# AI 世界杯 2026 预测面板

这个项目使用真实历史世界杯数据和公开 2026 赛程 API，构建一个基于 XGBoost 的小组赛预测面板。

## 文件说明

- `generate_predictions.py`：从 openfootball 历史数据训练 XGBoost 模型，获取 2026 赛程，并生成 `predictions.json`。
- `index.html`：读取 `predictions.json` 并展示全部小组赛预测面板。
- `requirements.txt`：Python 依赖。

## 运行方法

1. 安装依赖：

```bash
cd /Users/hubin/Downloads/AI世界杯
python3 -m pip install -r requirements.txt
```

2. 生成预测数据：

```bash
python3 generate_predictions.py
```

3. 启动本地服务器查看面板：

```bash
python3 -m http.server 8000
```

然后在浏览器中打开 `http://localhost:8000`。

## 实时博彩公司赔率

本项目支持两种赔率来源：

1. 实时接口 `The Odds API` 拉取 H/D/A 赔率。
2. 本地备份文件 `bookmaker_odds.json`，用于补齐或离线回退。

请先申请 API Key，并通过环境变量 `ODDS_API_KEY` 提供给脚本：

```bash
export ODDS_API_KEY=your_api_key_here
python3 generate_predictions.py
```

脚本会优先使用实时 API 数据；当实时接口不可用时，会自动从本地 `bookmaker_odds.json` 读取缓存赔率。

如果首次运行时可正常访问 API，脚本会将实时赔率快照保存到 `bookmaker_odds.json`，确保本地文件来源于真实接口，而不是示例数据。

仅当 API 与本地缓存都不可用时，才会使用内置的示例回退赔率。
## 预测逻辑更新

- 新增博彩公司平均赔率融合，使用赔率隐含概率与 XGBoost 模型、上下文概率共同加权形成最终预测。
- 面板会展示每场比赛的 H/D/A 平均赔率，并输出最佳预测结果。

## 开源资产参考

此预测终端参考并复用了以下核心开源组件：

- `dmlc/xgboost2`：XGBoost 架构和逻辑归因算法
- `tavily-ai/tavily-python`：实时信息检索引擎
- `666ghj/MiroFish`：结构化与非结构化信息融合框架
- `3b1b/manim`：后端决策树渲染
- `d3/d3-force`：前端 SHAP 粒子风格可视化

## 已知结果覆盖

当前面板已支持已知赛果覆盖。例如：墨西哥 2-0 赢南非。