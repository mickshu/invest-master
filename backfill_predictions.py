"""
回溯过去7个交易日的预测数据
- 使用当前真实行情作为基准
- 每天加随机扰动模拟历史差异
- 为每天生成独立快照并运行预测分析
"""
import sys
import os
import random
import datetime
import time

sys.path.insert(0, os.path.dirname(__file__))
from database import (
    init_db, get_conn, get_all_tencent_codes, save_snapshot,
    save_quotes, save_rankings,
)
from data_fetcher import fetch_quotes_batch, generate_overnight_data, aggregate_rankings
from prediction_analysis import analyze_predictions


def get_last_n_trading_days(n=7):
    """获取过去n个交易日（跳过周末）"""
    days = []
    d = datetime.date.today()
    while len(days) < n:
        d -= datetime.timedelta(days=1)
        if d.weekday() < 5:  # 周一到周五
            days.append(d)
    return days


def generate_day_snapshot(trading_date, quotes):
    """为指定日期生成快照（价格/成交量加扰动，但 change_pct 保持真实值）"""
    random.seed(trading_date.isoformat())

    varied_quotes = {}
    for code, q in quotes.items():
        # 价格和成交量扰动用于生成模拟的挂单金额/券商分布
        vol_var = random.uniform(-0.15, 0.15)
        varied_vol = int(q.get("volume", 0) * (1 + vol_var))

        varied_quotes[code] = {
            **q,
            # change_pct 保持真实值，不做扰动
            "volume": max(0, varied_vol),
        }

    # 生成隔夜数据（expected_change 基于真实的 change_pct）
    overnight_data, _ = generate_overnight_data(varied_quotes)
    rankings = aggregate_rankings(overnight_data)

    snapshot_time = trading_date.strftime("%Y-%m-%d 15:00:00")

    return varied_quotes, rankings, snapshot_time


def save_day_data(trading_date, quotes, rankings, snapshot_time):
    """保存一天的快照数据"""
    quotes_list = list(quotes.values())
    save_quotes(quotes_list, snapshot_time)
    save_rankings(rankings, snapshot_time)
    save_snapshot(snapshot_time, len(rankings))
    print(f"  已保存 {snapshot_time} | {len(rankings)} 只股票")


def backfill():
    init_db()

    # 1. 先拉取一次真实行情作为基准
    print("拉取真实行情基准数据...")
    stock_rows = get_all_tencent_codes()
    tencent_codes = [r["tencent_code"] for r in stock_rows]
    quotes = fetch_quotes_batch(tencent_codes, batch_size=80)
    print(f"  获取到 {len(quotes)} 只股票行情\n")

    if not quotes:
        print("行情数据为空，退出")
        return

    # 2. 获取过去7个交易日
    trading_days = get_last_n_trading_days(7)
    print(f"回溯交易日: {', '.join(d.isoformat() for d in trading_days)}\n")

    for day in trading_days:
        print(f"--- {day.isoformat()} ---")
        varied_quotes, rankings, snapshot_time = generate_day_snapshot(day, quotes)
        save_day_data(day, varied_quotes, rankings, snapshot_time)

        # 运行预测分析 - 传入正确的日期和快照时间
        try:
            analyze_predictions(snapshot_time=snapshot_time, analysis_date=day)
            analyze_predictions(watchlist_only=True, snapshot_time=snapshot_time, analysis_date=day)
            print(f"  预测分析完成")
        except Exception as e:
            print(f"  预测分析失败: {e}")

        time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"回溯完成: 已生成 {len(trading_days)} 天的预测数据")
    print(f"{'='*60}")


if __name__ == "__main__":
    backfill()
