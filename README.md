# A股券商隔夜挂单排行榜

## 功能说明
- 按挂单金额 Top30 排行
- 按预期涨幅 Top30 排行
- 支持按券商筛选（全部/单个券商）
- 每日6点自动生成报告

## 快速启动
```bash
pip install -r requirements.txt
python app.py
# 访问 http://127.0.0.1:5000
```

## 目录结构
```
overnight-orders-demo/
├── app.py              # Flask 主程序
├── daily_report.py     # 每日报告生成脚本
├── requirements.txt    # 依赖
├── templates/
│   └── index.html      # 前端页面
└── reports/            # 报告输出目录（自动生成）
```

## 真实数据接入计划
确认后接入以下数据源：
1. 东方财富 Level-2 隔夜委托数据
2. 同花顺资金流向
3. 各大券商APP公开数据

## 定时任务
每日 6:00 执行 `daily_report.py` 生成报告
