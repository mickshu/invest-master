"""
每日6点生成隔夜挂单排行报告 - 全量数据版
"""

import datetime
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from database import init_db, get_rankings_paged, get_latest_snapshot_time
from data_fetcher import fetch_and_store_all


def generate_daily_report(output_dir=None):
    """生成日报（使用全量数据库）"""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "reports")

    os.makedirs(output_dir, exist_ok=True)

    today = datetime.date.today().strftime("%Y-%m-%d")
    now = datetime.datetime.now().strftime("%H:%M:%S")

    print(f"[{now}] 开始生成日报...")

    # 1. 触发全量数据抓取
    print(f"[{now}] 正在获取全量行情数据...")
    count = fetch_and_store_all()
    print(f"[{now}] 获取到 {count} 只股票排行数据")

    snapshot_time = get_latest_snapshot_time()

    # 2. 获取两个维度的排行
    by_amount, total_amount = get_rankings_paged(sort_by="amount", page=1, page_size=30)
    by_change, total_change = get_rankings_paged(sort_by="change", page=1, page_size=30)

    report = {
        "date": today,
        "generated_at": datetime.datetime.now().isoformat(),
        "snapshot_time": snapshot_time,
        "data_source": "腾讯实时行情API",
        "total_stocks": total_amount,
        "top_by_amount": by_amount,
        "top_by_change": by_change,
        "summary": {
            "top_amount_stock": by_amount[0] if by_amount else None,
            "top_change_stock": by_change[0] if by_change else None,
        }
    }

    # 保存JSON
    json_path = os.path.join(output_dir, f"report_{today}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 生成文本报告
    text_path = os.path.join(output_dir, f"report_{today}.txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(f"A股券商隔夜挂单排行榜 - {today}\n")
        f.write(f"数据源: 腾讯实时行情API | 生成时间: {now}\n")
        f.write(f"全量股票池: {total_amount} 只\n")
        f.write("=" * 60 + "\n\n")

        f.write("按挂单金额 Top 10:\n")
        f.write("-" * 60 + "\n")
        f.write(f"{'排名':<4} {'代码':<8} {'名称':<8} {'金额(万)':<12} {'涨幅%':<8} {'券商数'}\n")
        for i, item in enumerate(by_amount[:10], 1):
            f.write(f"  {i:<2d}. {item['code']:<8} {item['name']:<8} "
                    f"{item['total_amount']:>10,.0f}  {item['max_change']:+7.2f}%  "
                    f"{item['brokerage_count']}家\n")

        f.write(f"\n按预期涨幅 Top 10:\n")
        f.write("-" * 60 + "\n")
        f.write(f"{'排名':<4} {'代码':<8} {'名称':<8} {'涨幅%':<8} {'金额(万)':<12} {'券商数'}\n")
        for i, item in enumerate(by_change[:10], 1):
            f.write(f"  {i:<2d}. {item['code']:<8} {item['name']:<8} "
                    f"{item['max_change']:+7.2f}%  {item['total_amount']:>10,.0f}  "
                    f"{item['brokerage_count']}家\n")

    print(f"报告已生成: {json_path}")
    print(f"文本报告: {text_path}")
    return report


if __name__ == "__main__":
    init_db()
    generate_daily_report()
