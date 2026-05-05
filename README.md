# 多模态 24/7 电商自动营销竞争决策 Agent

面向跨境电商（Amazon/Shopify）的四 Agent 协同 AI 系统，覆盖**竞品监控 → 舆情分析 → 内容生成 → 定价投放**全链路营销闭环。

---

## 核心痛点

电商竞争环境瞬息万变，中小商家面临四个致命问题：

| 痛点 | 现状 | 本系统解决方式 |
|------|------|---------------|
| **看不见竞品** | 竞品深夜降价毫不知情 | Recon Agent 每日自动抓取价格/库存/评分 |
| **听不到用户** | 上百条评论无法逐条分析 | Sentiment Agent 批量情感分类 + 问题提取 |
| **产不出素材** | 从洞察到文案需数天 | Creative Agent 5 种文案 + 产品图一键生成 |
| **算不清价格** | 出价和售价全凭直觉 | Pricing Agent 数据驱动多目标优化 |

---

## 四 Agent 协作架构

```
Orchestrator 中央调度器
  ├── ① Recon（侦察）    → 竞品爬取 / 价格差距 / 库存机会
  ├── ② Sentiment（舆情） → 情感分析 / 问题提取 / 智能回复
  ├── ③ Pricing（定价）  → 最优价格 / 广告出价 / 利润模拟
  └── ④ Creative（创意） → 文案生成 / 图片合成 / A/B 变体
```

### 长链协作逻辑

1. **Recon** 抓取 4 个竞品快照 → 计算价格差距百分比 → 检测库存缺口 → 写入 `strategy_insights`
2. **Sentiment** 读取评论批量调用 Claude API → 返回 JSON（sentiment/score/issues）→ 聚合 Top 5 问题
3. **Pricing** 读取竞品价格 → 生成 5 个候选价 → 加权优化 `score = 0.55×margin + 0.45×conversion` → AI 生成决策推理
4. **Creative** 检测高严重性洞察 → 生成 Listing/A+/Social/Ad 四种文案 + PIL 合成产品详情图

Agent 间通过 **SQLite 共享数据库**（7 张表）交换数据，非直接耦合，支持独立运行和异步调度。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 仪表板 | **Streamlit** — 5 个 Tab（总览/侦察/舆情/创意/定价）|
| AI 引擎 | **Claude API** — 文本分析/文案生成/决策推理 |
| 图片生成 | **PIL (Pillow)** — 产品图 + 卖点文字 + 促销角标 |
| 数据层 | **SQLite** — 7 表（products/reviews/competitors/decisions/insights/content/runs）|
| 模拟数据 | 5 款产品 × 100 条评论 × 20 条竞品快照 |
| 代码规模 | 17 个 Python 模块，约 1800 行 |

---

## 快速开始

```bash
pip install streamlit anthropic pandas plotly pillow httpx
streamlit run ecommerce-agent/main.py --server.port 8502
```

打开 http://localhost:8502，点击侧边栏 **"Run All Agents"** 即可运行完整四 Agent 流水线。

接入 Claude API 以获得真实 AI 能力：

```python
# orchestrator.py
orch = Orchestrator(api_key="sk-ant-...")
```

未配置 API Key 时自动使用 Mock 模式，完整可演示。

---

## 预期业务成果

- **运营效率提升 300%**：从人工监控到 4 Agent 自动化协同
- **广告 ROI 提升 20-40%**：出价从经验驱动转为公式驱动
- **响应速度数天 → 分钟级**：差评检测 → 分析 → 回复 → 优化全自动
- **数据驱动定价**：5 候选点加权优化，手动滑块可实时查看利润曲线
