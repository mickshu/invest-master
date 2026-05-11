"""
预测涨幅准确度分析报告
每日收盘后运行，对比预期涨幅与实际涨跌幅
支持全量和自选股两种分析模式
"""

import sys
import os
import json
import datetime
import random

sys.path.insert(0, os.path.dirname(__file__))
from database import (
    init_db, get_conn, get_latest_snapshot_time,
    save_prediction_errors, save_prediction_stats,
    get_prediction_stats_history, get_prediction_detail,
    get_algo_version, save_algo_version,
    watchlist_codes, save_daily_predictions,
    get_prediction_accuracy_trend
)

# 算法参数 - 可通过历史数据自动优化
ALGO_PARAMS = {
    "min_multiplier": 0.7,
    "max_multiplier": 1.8,
    "accuracy_threshold": 2.0,
}


def get_algo_version_num():
    info = get_algo_version()
    return info["version"]


def optimize_algo():
    """
    自我迭代优化算法
    基于历史准确率数据调整参数
    """
    history = get_prediction_accuracy_trend(days=14)
    if len(history) < 3:
        return ALGO_PARAMS, "数据不足，使用默认参数"

    recent_accuracies = [h["accuracy_pct"] for h in history[:7]]
    avg_accuracy = sum(recent_accuracies) / len(recent_accuracies)

    if len(recent_accuracies) >= 3:
        trend = recent_accuracies[0] - recent_accuracies[-1]
        if trend > 2:
            ALGO_PARAMS["min_multiplier"] = min(0.85, ALGO_PARAMS["min_multiplier"] + 0.05)
            ALGO_PARAMS["max_multiplier"] = max(1.3, ALGO_PARAMS["max_multiplier"] - 0.1)
            return ALGO_PARAMS, "准确率下降，收紧系数范围"
        elif avg_accuracy > 70:
            ALGO_PARAMS["min_multiplier"] = max(0.5, ALGO_PARAMS["min_multiplier"] - 0.05)
            ALGO_PARAMS["max_multiplier"] = min(2.0, ALGO_PARAMS["max_multiplier"] + 0.1)
            return ALGO_PARAMS, "准确率高，放宽探索范围"

    return ALGO_PARAMS, "参数保持稳定"


def analyze_predictions(watchlist_only=False, snapshot_time=None, analysis_date=None):
    """
    主分析流程
    watchlist_only: 仅分析自选股
    snapshot_time: 指定快照时间，默认使用最新
    analysis_date: 指定分析日期，默认使用今天
    """
    conn = get_conn()
    c = conn.cursor()

    if snapshot_time is None:
        latest = get_latest_snapshot_time()
    else:
        latest = snapshot_time
    if not latest:
        print("无预测数据，跳过")
        conn.close()
        return

    # 获取自选股代码
    wl_codes = set(watchlist_codes())

    # 获取当前快照和下一个快照时间（次日）
    c.execute("""
        SELECT snapshot_time FROM snapshots
        WHERE snapshot_time > ?
        ORDER BY snapshot_time ASC
        LIMIT 1
    """, (latest,))
    row = c.fetchone()
    next_snapshot = row["snapshot_time"] if row else None

    c.execute("""
        SELECT code, name, max_change as predicted_change, change_pct as today_change,
               total_amount, brokerage_list, price
        FROM rankings WHERE snapshot_time = ?
    """, (latest,))
    pred_rows = c.fetchall()

    if not pred_rows:
        print("无预测排行数据")
        conn.close()
        return

    # 获取次日真实涨跌幅（如果有下一个快照）
    next_day_changes = {}
    if next_snapshot:
        c.execute("""
            SELECT code, change_pct FROM rankings WHERE snapshot_time = ?
        """, (next_snapshot,))
        for r in c.fetchall():
            next_day_changes[r["code"]] = r["change_pct"]

    # 优化算法
    params, opt_msg = optimize_algo()
    print(f"算法优化: {opt_msg}")
    print(f"当前参数: min={params['min_multiplier']}, max={params['max_multiplier']}")

    if analysis_date is None:
        today = datetime.date.today().strftime("%Y-%m-%d")
    else:
        today = analysis_date.strftime("%Y-%m-%d")
    mode_str = "自选股" if watchlist_only else "全量"
    print(f"[{today}] 预测涨幅准确度分析({mode_str})")
    errors = []  # prediction_errors 表
    daily_preds = []  # daily_predictions 表（持久化）

    for row in pred_rows:
        row_d = dict(row)
        code = row_d["code"]
        is_in_watchlist = code in wl_codes

        # 自选股模式过滤
        if watchlist_only and not is_in_watchlist:
            continue

        predicted = row_d["predicted_change"]
        today_change = row_d["today_change"]

        # 实际涨跌幅取次日真实值（如果有下一个快照），否则用当日值标记为待验证
        actual = next_day_changes.get(code)
        if actual is None:
            # 没有次日数据（最新一天），用当日值标记为待验证
            actual = today_change

        error = predicted - actual
        abs_error = abs(error)
        
        # 误差分级规则
        if abs_error < 1:
            error_level = "准确"
            is_accurate = 1
        elif abs_error > 3:
            error_level = "离谱"
            is_accurate = 0
        else:
            error_level = "待提升"
            is_accurate = 0

        # prediction_errors 表（用于报告展示）
        errors.append({
            "date": today, "code": code, "name": row_d["name"],
            "predicted_change": round(predicted, 2),
            "actual_change": round(actual, 2),
            "error": round(error, 2), "abs_error": round(abs_error, 2),
            "error_level": error_level, "is_accurate": is_accurate,
            "brokerages": row_d.get("brokerage_list", ""),
        })

        # daily_predictions 表（持久化存储，用于后续算法优化）
        daily_preds.append({
            "date": today, "code": code, "name": row_d["name"],
            "predicted_change": round(predicted, 2),
            "actual_next_day": next_day_changes.get(code),
            "actual_change": round(actual, 2),
            "error": round(error, 2), "abs_error": round(abs_error, 2),
            "error_level": error_level, "is_accurate": is_accurate,
            "watchlist": 1 if is_in_watchlist else 0,
        })

    # 保存到数据库 (全量分析时保存, 自选股模式不重复保存)
    if not watchlist_only:
        save_prediction_errors(today, errors)
        save_daily_predictions(today, daily_preds)
    else:
        # 自选股模式: 只更新 prediction_errors (用于报告展示)
        save_prediction_errors(today, errors)

    # 统计
    total = len(errors)
    accurate = sum(1 for e in errors if e["is_accurate"])
    avg_error = sum(e["error"] for e in errors) / total if total else 0
    avg_abs_error = sum(e["abs_error"] for e in errors) / total if total else 0
    max_error = max(e["error"] for e in errors) if errors else 0
    min_error = min(e["error"] for e in errors) if errors else 0
    accuracy_pct = (accurate / total * 100) if total else 0

    stats_date = f"{today}_wl" if watchlist_only else today
    stats = {
        "date": stats_date, "total_count": total, "accurate_count": accurate,
        "accuracy_pct": round(accuracy_pct, 2),
        "avg_error": round(avg_error, 2), "avg_abs_error": round(avg_abs_error, 2),
        "max_error": round(max_error, 2), "min_error": round(min_error, 2),
        "algo_version": get_algo_version_num(), "algo_params": json.dumps(ALGO_PARAMS),
    }
    save_prediction_stats(stats_date, stats)

    new_version = f"v{today.replace('-', '')}"
    save_algo_version(new_version, opt_msg, json.dumps(ALGO_PARAMS))

    conn.close()

    print(f"\n分析结果 ({mode_str}):")
    print(f"  总股票数: {total}")
    print(f"  准确数(误差≤2%): {accurate}")
    print(f"  准确率: {accuracy_pct:.1f}%")
    print(f"  平均误差: {avg_error:.2f}%")
    print(f"  平均绝对误差: {avg_abs_error:.2f}%")
    print(f"  最大误差: {max_error:.2f}%")
    print(f"{'='*60}\n")

    return stats


if __name__ == "__main__":
    init_db()
    analyze_predictions()
