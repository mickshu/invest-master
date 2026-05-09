# Stock Invest Master — 十大师 × 志·道·势·法·术·器 投资分析体系

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ClawHub](https://img.shields.io/badge/Platform-ClawHub-blue.svg)](https://clawhub.ai/mickshu/stock-invest-master)
[![Version](https://img.shields.io/badge/version-3.0.0-green.svg)](https://github.com/mickshu/stock-invest-master)

> 整合10位投资大师的完整思维体系与"志·道·势·法·术·器"六层分析框架的结构化投资分析工具。
> 分析报告自动保存为 Markdown 格式至 `~/.stock-invest-master/` 目录。

> ⚠️ **投资免责申明**：本工具仅供学习和参考，不构成任何投资建议。所有投资决策由用户自行承担风险。

## 概述

本项目将两大互补的投资分析框架整合为一体：

1. **志·道·势·法·术·器 六层框架** — 从投资心性到量化工具的全维度递进结构
2. **十位投资大师思维体系** — 横向多视角交叉验证

### 六层分析框架

| 层次 | 核心问题 | 对应大师 | 权重 |
|------|---------|---------|------|
| **志** | 我的投资信仰是什么？心性是否成熟？ | 格雷厄姆+巴菲特+段永平 | 心性基石 |
| **道** | 这笔投资的底层逻辑是什么？ | 巴菲特+芒格+格雷厄姆 | 定性基石 |
| **势** | 市场趋势和周期处于什么阶段？ | 索罗斯+马克斯+达利欧 | 时机判断 |
| **法** | 如何系统化地判断值不值得投？ | 林奇+费雪+格雷厄姆 | 流程+方法 |
| **术** | 具体怎么操作？仓位如何管理？ | 索罗斯+十大师标准 | 技术+执行 |
| **器** | 用什么工具和技术来辅助决策？ | 西蒙斯+技术工具 | 工具+量化 |

### 十位投资大师

| 大师 | 核心方法论 | 一句话精髓 |
|------|-----------|-----------|
| 📚 **格雷厄姆** (Benjamin Graham) | 安全边际 + 内在价值 + 定量分析 | "市场短期是投票机，长期是称重机" |
| 🎩 **巴菲特** (Warren Buffett) | 能力圈 + 护城河 + 安全边际 | "风险来自不知道自己在做什么" |
| 🏃 **林奇** (Peter Lynch) | 六类分类 + PEG + 两分钟演练 | "买你了解的" |
| 🔬 **费雪** (Philip Fisher) | 15点选股 + 闲聊法 + 长期持有 | "如果买对了，几乎永远不卖" |
| 🧠 **芒格** (Charlie Munger) | 逆向思维 + 心智模型格栅 + 认知偏差 | "以合理价格买伟大生意" |
| 📊 **马克斯** (Howard Marks) | 周期定位 + 第二层次思维 + 风险聚焦 | "最危险的事是相信没有风险" |
| 🎯 **段永平** | 本分哲学 + Stop Doing List | "做对的事情，把事情做对" |
| 🌊 **达利欧** (Ray Dalio) | 经济机器 + 债务周期 + 全天候策略 | "理解因果，系统化决策" |
| 💥 **索罗斯** (George Soros) | 反身性理论 + 宏观对冲 + 泡沫识别 | "世界经济史是一部基于假象和谎言的连续剧" |
| 🤖 **西蒙斯** (James Simons) | 量化模型 + 统计套利 + 机器学习 | "市场不是不可预测的，只是需要正确的模型" |

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
├── README.md                                  # 项目说明文档
├── LICENSE                                    # MIT 开源协议
├── stock-invest-master/
│   ├── SKILL.md                               # 核心技能文件（v3.0.0）
│   ├── scripts/
│   │   ├── extract_stock_data.py              # 股票数据结构化提取脚本
│   │   └── fetch_us_stock.py                  # 美股数据获取脚本
│   └── references/
│       ├── graham-framework.md                # 格雷厄姆：安全边际+内在价值
│       ├── buffett-framework.md               # 巴菲特：能力圈+护城河
│       ├── lynch-framework.md                 # 林奇：六类分类+PEG
│       ├── fisher-framework.md                # 费雪：15点选股+闲聊法
│       ├── munger-framework.md                # 芒格：逆向思维+认知偏差
│       ├── marks-framework.md                 # 马克斯：周期定位
│       ├── duan-framework.md                  # 段永平：本分哲学
│       ├── dalio-framework.md                 # 达利欧：经济机器+债务周期
│       ├── soros-framework.md                 # 索罗斯：反身性理论+宏观对冲
│       └── simons-framework.md                # 西蒙斯：量化模型+统计套利
```

## 安装与使用

### 方式一：作为 OpenClaw 技能

```bash
# 通过 ClawHub 安装
clawhub install stock-invest-master

# 或通过 OpenClaw 安装
openclaw skills install stock-invest-master
```

### 方式二：手动克隆

```bash
git clone https://github.com/mickshu/stock-invest-master.git ~/.hermes/skills/stock-invest-master
mkdir -p ~/.stock-invest-master
```

## 分析流程

```
第一步：市场识别（A股/美股/港股）
  ↓
第二步：25问快速筛选（志/道/势/法/术/器六层主题）
  ↓ (通过)
第三步：志 → 道 → 势 → 法 → 术 → 器 逐层分析
  每层注入对应大师视角
  ↓
第四步：十大师共识结论
  ↓
第五步：违背"志·道·法"专项诊断
  ↓
第六步：保存报告至 ~/.stock-invest-master/
  文件名: yyyymmdd_X公司.md
```

## 核心特性

### 1. 六层递进分析

以"志·道·势·法·术·器"为骨架，从投资心性到量化工具逐层深入：
- **志不通过 → 停止分析**（投资信仰错误，任何方法论都会失效）
- **道不通过 → 停止分析**（底层逻辑错误，无论其余多好看都不投）
- **势不通过 → 需谨慎**（时机不对，好公司也可能长期套牢）
- **法不通过 → 等待**（价格不合适或缺乏研究）
- **术不通过 → 调整操作计划**
- **器不通过 → 数据/工具有问题，需核实**

### 2. 十大师交叉验证

每层分析注入对应大师的视角，最终形成十大师独立判断和共识：
- 一致度高 → 高信心决策
- 分歧较大 → 深入调查分歧原因

### 3. 反身性理论（索罗斯）

新增索罗斯视角，识别市场中的反身性循环和泡沫：
- 主流叙事识别
- 假象与现实分析
- 转折点判断
- 索罗斯式仓位管理（试错→确认→加码）

### 4. 量化分析（西蒙斯）

新增西蒙斯视角，用统计方法验证投资结论：
- 因子分析（价值/动量/质量/低波动/规模）
- 统计显著性检验
- 样本外回测验证
- 过拟合防范

### 5. 自动报告保存

分析完成后自动生成 Markdown 格式报告：
- 完整的六层评估 + 十大师共识
- 违背"志·道·法"专项诊断
- 关键假设、风险、监控指标
- 数据来源与校验声明
- 保存到 `~/.stock-invest-master/` 目录

### 6. 三市场覆盖

支持 A股、美股、港股 三大市场，每种市场有专门的数据源和分析考量。

## 快速筛选（25问）

| 主题 | 问题数 | 关注点 | 主导大师 |
|------|--------|--------|---------|
| A. 志 — 投资信仰 | 4 | 价值信仰、风险认知、长期主义 | 格雷厄姆+巴菲特+段永平 |
| B. 道 — 商业本质 | 5 | 能力圈、护城河、内在价值 | 巴菲特+芒格+格雷厄姆 |
| C. 势 — 市场周期 | 4 | 反身性、周期定位、债务周期 | 索罗斯+马克斯+达利欧 |
| D. 法 — 分析流程 | 5 | 盈利质量、安全边际、PEG | 林奇+费雪+格雷厄姆 |
| E. 术 — 操作执行 | 3 | 仓位管理、卖出标准 | 索罗斯+十大师 |
| F. 器 — 工具技术 | 4 | 量化验证、回测、统计显著性 | 西蒙斯 |

**自动否决规则**：Q18（管理层诚信）= 否 → 无论其他多好，自动否决

## 适用场景

- 股票/公司系统性投资分析
- 买入前全面尽调（首次建仓）
- 持仓定期体检（季度/年度审查）
- 多视角交叉验证重要投资决策
- 投资组合审查与再平衡
- 市场周期分析与宏观判断
- 量化策略验证与回测

## 与其他技能的协作

| 技能 | 关系 | 用法 |
|------|------|------|
| `dcf-model` | 互补 | 在"法"层估值时调用 |
| `comps-analysis` | 互补 | 在"法"层估值时调用 |
| `3-statement-model` | 互补 | 在"法"层财务分析时调用 |

## 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|---------|
| 3.0.0 | 2026-05-09 | 升级为六层框架(志·道·势·法·术·器)，新增格雷厄姆/索罗斯/西蒙斯三位大师，整合打法与大师理论 |
| 2.1.0 | 2026-05-09 | 新增投资免责申明（7项声明） |
| 2.0.0 | 2026-05-09 | 整合stock-dao-analysis到investment-master，重命名为stock-invest-master |

## License

本项目采用 MIT 协议开源。详见 [LICENSE](LICENSE) 文件。

## ClawHub 发布说明

本项目已发布到 ClawHub 平台：https://clawhub.ai/mickshu/stock-invest-master

遵循 ClawHub 技能规范：
- 标准 `SKILL.md` 格式，包含 YAML frontmatter（name, version, license, description）
- MIT 开源协议
- 结构化 references 目录存放参考文档
- scripts 目录存放辅助脚本
- 自包含，无外部依赖（除标准数据源 API）

## 致谢

本项目的知识体系源自十位投资大师的公开著作、演讲和访谈：
- Benjamin Graham: 《聪明的投资者》《证券分析》
- Warren Buffett: Berkshire Hathaway 股东信
- Peter Lynch: 《彼得·林奇的成功投资》(One Up On Wall Street)
- Philip Fisher: 《怎样选择成长股》(Common Stocks and Uncommon Profits)
- Charlie Munger: 《穷查理宝典》(Poor Charlie's Almanack)
- Howard Marks: 《投资最重要的事》(The Most Important Thing) + Oaktree memo
- 段永平: 公开演讲与雪球分享
- Ray Dalio: 《原则》(Principles) + 《债务危机》(Big Debt Crises)
- George Soros: 《金融炼金术》(The Alchemy of Finance)
- James Simons: 《解读量化投资》(The Man Who Solved the Market)

"志·道·势·法·术·器"框架源自中国传统哲学思想与现代投资理论的融合。
