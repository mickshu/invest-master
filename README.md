# invest-master

投资大师分析股票 —— 整合7位投资大师的完整思维体系，支持 A股 / 美股 / 港股 多市场分析。

## 项目概述

Investment Master 承载了7位投资大师毕生智慧的总和，像一个圆桌会议：7位大师同时在场，各抒己见，最终形成共识。不是套公式，而是从多维度审视投资机会。

| 大师 | 核心方法论 | 一句话精髓 |
|------|-----------|-----------|
| 🎩 **巴菲特** | 能力圈 + 护城河 + 安全边际 | "风险来自不知道自己在做什么" |
| 🏃 **林奇** | 六类分类 + PEG + 两分钟演练 | "买你了解的" |
| 🔬 **费雪** | 15点选股 + 闲聊法 + 长期持有 | "如果买对了，几乎永远不卖" |
| 🧠 **芒格** | 逆向思维 + 心智模型格栅 + 25种认知偏差 | "以合理价格买伟大生意" |
| 📊 **马克斯** | 周期定位 + 第二层次思维 + 风险即永久损失 | "最危险的事是相信没有风险" |
| 🎯 **段永平** | 本分哲学 + Stop Doing List + 睡得着觉 | "做对的事情，把事情做对" |
| 🌊 **达利欧** | 经济机器 + 债务周期 + 全天候 + 原则体系 | "理解因果，系统化决策" |

## 适用场景

- 分析股票/公司、评估投资机会
- 解读财报/年报/股东信
- 评估商业护城河/竞争优势
- 买卖持有决策、仓位建议
- 市场周期分析、风险管理
- 管理层质量评估、PEG估值
- 成长股分析、逆向思维检查
- 多大师对比分析、行业分析
- **支持 A股、美股、港股 三市场分析**

## 项目结构

```
invest-master/
├── README.md
├── investment-master/
│   ├── SKILL.md                        # 核心技能定义文件（776行）
│   ├── references/                     # 7位大师投资思维框架
│   │   ├── buffett-framework.md        # 巴菲特：8问筛选 + 5步深度分析
│   │   ├── lynch-framework.md          # 林奇：6问筛选 + 六类分类 + PEG决策
│   │   ├── fisher-framework.md         # 费雪：5问筛选 + 15点选股法 + 闲聊法
│   │   ├── munger-framework.md         # 芒格：7问筛选 + 逆向思维 + 25种认知偏差
│   │   ├── marks-framework.md          # 马克斯：6问筛选 + 周期定位 + 第二层次思维
│   │   ├── duan-framework.md           # 段永平：6问筛选 + 本分哲学 + Stop Doing List
│   │   └── dalio-framework.md          # 达利欧：7问筛选 + 经济机器 + 债务周期
│   └── scripts/                        # 数据获取与提取脚本
│       ├── extract_stock_data.py        # 三市场数据提取脚本（706行）
│       └── fetch_us_stock.py            # 美股数据获取与结构化整合（305行）
```

## 分析流程

### 1. 市场识别与数据获取

根据股票代码格式自动识别市场类型：

| 代码格式 | 市场 | 示例 |
|---------|------|------|
| `XXXXXX.SZ` / `XXXXXX.SH` | A股 | 000001.SZ, 600519.SH |
| 纯英文代码（无后缀） | 美股 | AAPL, GOOGL, NVDA, TSLA |
| `XXXXX.HK` | 港股 | 00700.HK, 09988.HK |

### 2. 快速筛选（核心20问）

按5个主题分组，快速判断是否值得深入：

- **A. 商业本质**：能力圈、护城河、定价权、商业模式简洁性、持久性
- **B. 财务与估值**：盈利质量、债务安全、安全边际、PEG、增长潜力
- **C. 管理层与治理**：管理层诚信（自动否决项）、"对的事情"、Stop Doing
- **D. 市场环境与周期**：周期位置、第二层次思维、范式阶段
- **E. 认知与决策**：逆向思维、认知偏差、机会成本、"太难"测试

### 3. 五阶段深度分析

| 阶段 | 主导大师 | 核心内容 |
|------|---------|---------|
| 第一阶段 | 巴菲特 + 段永平 + 费雪 | 商业本质：能力圈、护城河、定价权 |
| 第二阶段 | 林奇 + 费雪 | 分类与故事：六类分类、两分钟演练、15点评分 |
| 第三阶段 | 巴菲特 + 林奇 + 段永平 | 财务与估值：Owner Earnings、PEG、ROIC、安全边际 |
| 第四阶段 | 芒格 + 马克斯 | 风险与认知：逆向思维、认知偏差、周期定位 |
| 第五阶段 | 达利欧 + 马克斯 | 宏观与配置：经济机器、债务周期、全天候 |

## 脚本使用

### extract_stock_data.py

三市场数据提取脚本，从查询结果中结构化提取关键指标。

```bash
# A股
python3 scripts/query.py --query "思源电气002028 最新股价 PE PB ROE" > /tmp/result.json
python3 investment-master/scripts/extract_stock_data.py /tmp/result.json 002028.SZ

# 美股
python3 scripts/query.py --query "Apple AAPL stock price PE PB ROE" > /tmp/us_result.json
python3 investment-master/scripts/extract_stock_data.py /tmp/us_result.json AAPL --market US

# 港股
python3 scripts/query.py --query "腾讯00700.HK 最新股价 市盈率 市净率 ROE" > /tmp/hk_result.json
python3 investment-master/scripts/extract_stock_data.py /tmp/hk_result.json 00700.HK --market HK
```

输出结构化的 JSON，包含实时行情、基本面指标和交叉校验警告。

### fetch_us_stock.py

美股数据获取与结构化整合脚本。

```bash
# 获取完整美股数据
python3 investment-master/scripts/fetch_us_stock.py AAPL

# 仅获取行情
python3 investment-master/scripts/fetch_us_stock.py AAPL --only daily

# 仅获取财务指标
python3 investment-master/scripts/fetch_us_stock.py AAPL --only fina

# 指定日期范围
python3 investment-master/scripts/fetch_us_stock.py AAPL --start 20250101 --end 20250425
```

## 分析报告标准输出

所有完整分析报告均按照统一的8大板块输出：

1. **七大师共识结论** — 综合判断 + 一致度
2. **各大师独立判断** — 判断/核心理由/信心度
3. **能力圈/本分评估** + **关键假设**
4. **商业品质** — 护城河/定价权/"对的事情"/15点评分
5. **分类与故事** — 六类归属/两分钟演练/增长可持续性
6. **财务快照 + 估值** — ROIC/ROE/PEG/安全边际/"睡得着觉"测试
7. **风险与认知** — 失败路径/认知偏差/周期定位/永久损失概率
8. **宏观与配置** — 债务周期/范式/全天候/Stop Doing检查/卖出标准/监控指标

## 数据质量保障

- **一只一查**：禁止批量混查，确保数据不混淆
- **交叉校验**：PE ≈ PB/ROE 公式自动校验，偏差超标自动警告
- **来源标注**：所有客观数据标注更新日期
- **市场隔离**：A股/美股/港股数据分别提取，含货币标注（CNY/USD/HKD）
- **结构化提取**：使用脚本提取，避免手动出错

## 市场特有考量

### A股
- 会计准则：CAS（中国企业会计准则）
- 政策风险、涨跌停限制、退市规则

### 美股
- 会计准则：US GAAP / IFRS
- SEC文件：10-K、10-Q、8-K
- 回购文化、汇率风险、ADR退市风险
- 财年可能非日历年（如苹果财年截至9月底）

### 港股
- 会计准则：HKFRS
- AH股溢价、港股通资金流向
- 做空机制、流动性风险
- 港股通红利税（H股20%，红筹股28%）
- 同股不同权架构
