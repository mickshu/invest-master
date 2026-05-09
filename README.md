# Stock Invest Master — 七大师 × 道·理·法·术 投资分析体系

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Clawhub](https://img.shields.io/badge/Platform-Clawhub-blue.svg)](https://clawhub.com)

> 整合7位投资大师的完整思维体系与"道·理·法·术"四层分析框架的结构化投资分析工具。
> 分析报告自动保存为 Markdown 格式至 `~/.stock-invest-master/` 目录。

> ⚠️ **投资免责申明**：本工具仅供学习和参考，不构成任何投资建议。所有投资决策由用户自行承担风险。详细内容见 SKILL.md 中的完整免责申明。

## 概述

本项目将两大互补的投资分析框架整合为一体：

1. **道·理·法·术四层框架** — 源自中国传统哲学的纵向递进分析结构
2. **七位投资大师思维体系** — 横向多视角交叉验证

### 框架关系

```
                    道 → 理 → 法 → 术
                    ↓     ↓     ↓     ↓
              [巴菲特] [费雪] [林奇] [七大师操作]
              [段永平] [林奇] [马克斯]
              [芒格  ]      [达利欧]
```

| 维度 | 道·理·法·术 | 七大师视角 |
|------|------------|-----------|
| 分析方向 | 纵向四层递进 | 横向七大师并行 |
| 核心功能 | 结构化分析层级，防遗漏 | 多视角交叉验证，防偏见 |
| 输出 | 每层遵循/偏离评估 | 每大师独立判断+共识 |

### 投资层级详解

| 层次 | 核心问题 | 对应大师视角 | 权重 |
|------|---------|------------|------|
| **道** | 这笔投资的底层逻辑是什么？ | 巴菲特(能力圈) + 段永平(本分) + 芒格(心智模型) | 定性基石 |
| **理** | 这家公司为什么能赚钱？ | 巴菲特(护城河) + 费雪(15点) + 林奇(分类) | 定量+定性 |
| **法** | 如何系统化地判断值不值得投？ | 林奇(PEG) + 马克斯(周期) + 达利欧(机器) | 流程+方法 |
| **术** | 具体怎么操作？ | 七大师的买卖/仓位/时机标准 | 技术+执行 |

## 七位投资大师

| 大师 | 核心方法论 | 一句话精髓 |
|------|-----------|-----------|
| 🎩 **巴菲特** (Warren Buffett) | 能力圈 + 护城河 + 安全边际 | "风险来自不知道自己在做什么" |
| 🏃 **林奇** (Peter Lynch) | 六类分类 + PEG + 两分钟演练 | "买你了解的" |
| 🔬 **费雪** (Philip Fisher) | 15点选股 + 闲聊法 + 长期持有 | "如果买对了，几乎永远不卖" |
| 🧠 **芒格** (Charlie Munger) | 逆向思维 + 心智模型格栅 + 认知偏差 | "以合理价格买伟大生意" |
| 📊 **马克斯** (Howard Marks) | 周期定位 + 第二层次思维 + 风险聚焦 | "最危险的事是相信没有风险" |
| 🎯 **段永平** | 本分哲学 + Stop Doing List + 睡得着觉 | "做对的事情，把事情做对" |
| 🌊 **达利欧** (Ray Dalio) | 经济机器 + 债务周期 + 全天候策略 | "理解因果，系统化决策" |

## 报告输出

每次分析完成后，报告自动保存为 Markdown 格式：

```
~/.stock-invest-master/yyyymmdd_X公司.md
```

**示例：**
- `~/.stock-invest-master/20260509_腾讯.md`
- `~/.stock-invest-master/20260509_Apple.md`
- `~/.stock-invest-master/20260509_茅台_quick.md`（快速筛选）
- `~/.stock-invest-master/20260509_腾讯_v2.md`（同日第二次分析）

## 项目结构

```
stock-invest-master/
├── README.md                              # 项目说明文档
├── LICENSE                                # MIT 开源协议
├── stock-invest-master/
│   ├── SKILL.md                           # 核心技能文件（整合版）
│   ├── scripts/
│   │   ├── extract_stock_data.py          # 股票数据结构化提取脚本
│   │   └── fetch_us_stock.py              # 美股数据获取脚本
│   └── references/
│       ├── buffett-framework.md           # 巴菲特分析框架
│       ├── lynch-framework.md             # 林奇分析框架
│       ├── fisher-framework.md            # 费雪分析框架
│       ├── munger-framework.md            # 芒格分析框架
│       ├── marks-framework.md             # 马克斯分析框架
│       ├── duan-framework.md              # 段永平分析框架
│       └── dalio-framework.md             # 达利欧分析框架
```

## 安装与使用

### 方式一：作为 Hermes Agent 技能

```bash
git clone https://github.com/mickshu/stock-invest-master.git ~/.hermes/skills/stock-invest-master
mkdir -p ~/.stock-invest-master
```

### 方式二：发布到 Clawhub 平台

本项目已适配 Clawhub 技能平台，可通过以下方式安装：

```bash
# 通过 clawhub CLI 安装（如平台支持）
clawhub install mickshu/stock-invest-master

# 或手动克隆
git clone https://github.com/mickshu/stock-invest-master.git
```

### 分析报告示例

```
请求: 分析腾讯00700.HK

→ Agent 加载 stock-invest-master 技能
→ 执行市场识别、数据检索
→ 道·理·法·术 四层评估 + 七大师交叉验证
→ 生成完整 Markdown 报告
→ 保存至 ~/.stock-invest-master/20260509_腾讯.md
→ 在终端输出报告摘要
```

## 分析流程

```
第一步：市场识别（A股/美股/港股）
  ↓
第二步：统一20问快速筛选
  ↓ (通过)
第三步：道 → 理 → 法 → 术 逐层分析
  每层注入对应大师视角
  ↓
第四步：七大师共识结论
  ↓
第五步：违背"道·法"专项诊断
  ↓
第六步：保存报告至 ~/.stock-invest-master/
  文件名: yyyymmdd_X公司.md
```

## 核心特性

### 1. 四层递进分析

以"道·理·法·术"为骨架，从投资哲学到具体操作逐层深入：
- **道不通过 → 停止分析**（底层逻辑错误，无论财务多好看都不投）
- **理不通过 → 高度警惕**（基本面有问题，需道的极强理由才能继续）
- **法不通过 → 等待**（价格不合适，等待安全边际出现）
- **术不通过 → 调整操作计划**（择时/仓位需要优化）

### 2. 七大师交叉验证

每层分析注入对应大师的视角，最终形成七大师独立判断和共识：
- 一致度高 → 高信心决策
- 分歧较大 → 深入调查分歧原因

### 3. 自动报告保存

分析完成后自动生成 Markdown 格式报告：
- 完整的四层评估 + 七大师共识
- 违背"道·法"专项诊断
- 关键假设、风险、监控指标
- 数据来源与校验声明
- 保存到 `~/.stock-invest-master/` 目录

### 4. 违背专项诊断

专门针对不符合投资基本原则的公司进行深度诊断：
- 6项自动否决红旗（财务造假、管理层失信等）
- 道层面6项违背检查
- 法层面5项违背检查

### 5. 三市场覆盖

支持 A股、美股、港股 三大市场，每种市场有专门的数据源和分析考量：
- A股：neodata + finance-data-retrieval
- 美股：MCP financial-datasets + finance-data-retrieval（含SEC filings）
- 港股：neodata + finance-data-retrieval（含AH股溢价分析）

## 快速筛选（20问）

分析前先运行20个核心筛选问题，按5个主题分组：

| 主题 | 问题数 | 关注点 |
|------|--------|--------|
| A. 商业本质 | 5 | 能力圈、护城河、定价权、简洁性、持久性 |
| B. 财务与估值 | 5 | 盈利质量、债务安全、安全边际、PEG、增长潜力 |
| C. 管理层与治理 | 3 | 诚信、对的事情、Stop Doing |
| D. 市场环境与周期 | 3 | 周期位置、第二层次思维、范式阶段 |
| E. 认知与决策 | 4 | 逆向思维、认知偏差、机会成本、太难测试 |

**自动否决规则**：Q11（管理层诚信）= 否 → 无论其他多好，自动否决

## 适用场景

- 股票/公司系统性投资分析
- 买入前全面尽调（首次建仓）
- 持仓定期体检（季度/年度审查）
- 多视角交叉验证重要投资决策
- 投资组合审查与再平衡
- 市场周期分析与宏观判断

## 与其他技能的协作

| 技能 | 关系 | 用法 |
|------|------|------|
| `dcf-model` | 互补 | 在"法"层估值时调用 |
| `comps-analysis` | 互补 | 在"法"层估值时调用 |
| `3-statement-model` | 互补 | 在"理"层财务分析时调用 |

## License

本项目采用 MIT 协议开源。详见 [LICENSE](LICENSE) 文件。

## Clawhub 发布说明

本项目遵循 Clawhub 技能规范：

- 标准 `SKILL.md` 格式，包含 YAML frontmatter（name, version, license, description）
- MIT 开源协议
- 结构化 references 目录存放参考文档
- scripts 目录存放辅助脚本
- 自包含，无外部依赖（除标准数据源 API）

## 致谢

本项目的知识体系源自七位投资大师的公开著作、演讲和访谈：
- Warren Buffett: Berkshire Hathaway 股东信
- Peter Lynch: 《彼得·林奇的成功投资》(One Up On Wall Street)
- Philip Fisher: 《怎样选择成长股》(Common Stocks and Uncommon Profits)
- Charlie Munger: 《穷查理宝典》(Poor Charlie's Almanack)
- Howard Marks: 《投资最重要的事》(The Most Important Thing) + Oaktree memo
- 段永平: 公开演讲与雪球分享
- Ray Dalio: 《原则》(Principles) + 《债务危机》(Big Debt Crises)

"道·理·法·术"框架源自中国传统哲学思想在现代投资分析中的应用。
