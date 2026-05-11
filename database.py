"""
A股全量股票数据库模块
使用SQLite存储股票信息和排行数据
"""

import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "astock.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            code TEXT PRIMARY KEY, name TEXT, market TEXT, tencent_code TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT, name TEXT,
            price REAL, prev_close REAL, open REAL, high REAL, low REAL,
            volume INTEGER, turnover REAL, change_pct REAL,
            snapshot_time TEXT, FOREIGN KEY (code) REFERENCES stocks(code)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT, name TEXT,
            price REAL, change_pct REAL, total_amount REAL, max_change REAL,
            total_volume INTEGER, brokerage_count INTEGER, brokerage_list TEXT,
            sort_amount INTEGER, sort_change INTEGER, snapshot_time TEXT,
            buy_amount REAL DEFAULT 0, sell_amount REAL DEFAULT 0,
            FOREIGN KEY (code) REFERENCES stocks(code)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT, snapshot_time TEXT UNIQUE,
            stock_count INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 预测误差分析表
    c.execute("""
        CREATE TABLE IF NOT EXISTS prediction_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            code TEXT,
            name TEXT,
            predicted_change REAL,
            actual_change REAL,
            error REAL,
            abs_error REAL,
            is_accurate INTEGER,  -- 误差在2%内为准确
            brokerages TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS prediction_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            total_count INTEGER,
            accurate_count INTEGER,
            accuracy_pct REAL,
            avg_error REAL,
            avg_abs_error REAL,
            max_error REAL,
            min_error REAL,
            algo_version TEXT,
            algo_params TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS algo_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT UNIQUE, description TEXT, params TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 自选股管理表
    c.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE, name TEXT, added_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 每日预测数据持久化表
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, code TEXT, name TEXT,
            predicted_change REAL, actual_next_day REAL, actual_change REAL,
            error REAL, abs_error REAL, is_accurate INTEGER,
            error_level TEXT DEFAULT '待提升',
            watchlist INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        c.execute("ALTER TABLE daily_predictions ADD COLUMN error_level TEXT DEFAULT '待提升'")
    except: pass

    c.execute("CREATE INDEX IF NOT EXISTS idx_quotes_time ON quotes(snapshot_time)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_rankings_time ON rankings(snapshot_time)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_rankings_amount ON rankings(total_amount DESC)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_rankings_change ON rankings(max_change DESC)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_pred_date ON prediction_errors(date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_pred_code ON prediction_errors(code)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_daily_pred_date ON daily_predictions(date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_daily_pred_code ON daily_predictions(code)")

    conn.commit()
    conn.close()
    print(f"数据库初始化完成: {DB_PATH}")


def save_stocks(stock_list):
    """
    保存股票基础信息
    stock_list: [(code, name, market), ...]
    market: sh(沪市)/sz(深市+北交所)
    """
    conn = get_conn()
    c = conn.cursor()
    count = 0
    for code, name, market in stock_list:
        # 北交所股票使用 bj 前缀
        if code.startswith("920") or code.startswith("83") or code.startswith("43") or code.startswith("87"):
            tencent_code = f"bj{code}"
        else:
            tencent_code = f"{market}{code}"
        c.execute(
            "INSERT OR REPLACE INTO stocks (code, name, market, tencent_code) VALUES (?, ?, ?, ?)",
            (code, name, market, tencent_code)
        )
        count += 1
    conn.commit()
    conn.close()
    return count


def get_all_tencent_codes():
    """获取所有股票的腾讯编码，用于批量查询"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT code, name, market, tencent_code FROM stocks ORDER BY code")
    rows = c.fetchall()
    conn.close()
    return rows


def save_snapshot(snapshot_time, stock_count):
    """记录快照元数据"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO snapshots (snapshot_time, stock_count) VALUES (?, ?)",
        (snapshot_time, stock_count)
    )
    conn.commit()
    conn.close()


def save_quotes(quotes, snapshot_time):
    """
    批量保存行情快照
    quotes: [{code, name, price, ...}, ...]
    """
    conn = get_conn()
    c = conn.cursor()
    for q in quotes:
        c.execute("""
            INSERT INTO quotes (code, name, price, prev_close, open, high, low,
                              volume, turnover, change_pct, snapshot_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            q["code"], q["name"], q["price"], q.get("prev_close"),
            q.get("open"), q.get("high"), q.get("low"),
            q.get("volume", 0), q.get("turnover", 0),
            q.get("change_pct", 0), snapshot_time
        ))
    conn.commit()
    conn.close()


def save_rankings(rankings, snapshot_time):
    """
    批量保存排行数据
    rankings: [{code, name, price, change_pct, total_amount, max_change, buy_amount, sell_amount, ...}, ...]
    """
    conn = get_conn()
    c = conn.cursor()

    # 先计算排名
    by_amount = sorted(rankings, key=lambda x: x["total_amount"], reverse=True)
    by_change = sorted(rankings, key=lambda x: x["max_change"], reverse=True)

    amount_rank = {r["code"]: i + 1 for i, r in enumerate(by_amount)}
    change_rank = {r["code"]: i + 1 for i, r in enumerate(by_change)}

    for r in rankings:
        c.execute("""
            INSERT INTO rankings (code, name, price, change_pct, total_amount,
                                max_change, total_volume, brokerage_count,
                                brokerage_list, sort_amount, sort_change, snapshot_time,
                                buy_amount, sell_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["code"], r["name"], r.get("price", 0), r.get("change_pct", 0),
            r["total_amount"], r["max_change"], r["total_volume"],
            r["brokerage_count"], r["brokerage_list"],
            amount_rank[r["code"]], change_rank[r["code"]], snapshot_time,
            r.get("buy_amount", 0), r.get("sell_amount", 0)
        ))

    conn.commit()
    conn.close()


def get_latest_snapshot_time():
    """获取最新快照时间"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT snapshot_time FROM snapshots ORDER BY snapshot_time DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row["snapshot_time"] if row else None


def get_rankings_paged(sort_field="total_amount", sort_order="DESC", page=1, page_size=30, brokerage="全部", stock_code=None, watchlist_only=False, snapshot_time=None):
    """
    分页查询排行数据
    sort_field: total_amount | change_pct | max_change | total_volume | buy_amount | sell_amount
    sort_order: ASC | DESC
    返回: (data, total_count)
    """
    if snapshot_time is None:
        snapshot_time = get_latest_snapshot_time()
    if snapshot_time is None:
        return [], 0

    conn = get_conn()
    c = conn.cursor()

    allowed_fields = {"total_amount", "change_pct", "max_change", "total_volume", "code", "name", "buy_amount", "sell_amount"}
    if sort_field not in allowed_fields:
        sort_field = "total_amount"
    if sort_order.upper() not in ("ASC", "DESC"):
        sort_order = "DESC"

    base_query = f"SELECT * FROM rankings WHERE snapshot_time = ?"
    count_query = f"SELECT COUNT(*) FROM rankings WHERE snapshot_time = ?"
    params = [snapshot_time]
    count_params = [snapshot_time]

    if brokerage != "全部":
        base_query += " AND brokerage_list LIKE ?"
        count_query += " AND brokerage_list LIKE ?"
        params.append(f"%{brokerage}%")
        count_params.append(f"%{brokerage}%")

    if stock_code:
        base_query += " AND code = ?"
        count_query += " AND code = ?"
        params.append(stock_code)
        count_params.append(stock_code)

    if watchlist_only:
        base_query += " AND code IN (SELECT code FROM watchlist)"
        count_query += " AND code IN (SELECT code FROM watchlist)"

    base_query += f" ORDER BY {sort_field} {sort_order} LIMIT ? OFFSET ?"
    offset = (page - 1) * page_size
    params.extend([page_size, offset])

    c.execute(count_query, count_params)
    total = c.fetchone()[0]

    c.execute(base_query, params)
    rows = c.fetchall()
    conn.close()

    data = [dict(r) for r in rows]
    return data, total


def get_snapshot_history(limit=20):
    """获取快照历史"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT snapshot_time, stock_count, created_at FROM snapshots ORDER BY snapshot_time DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stock_detail(code):
    """获取个股详细信息（行情+财务指标）"""
    conn = get_conn()
    c = conn.cursor()

    # 基础信息
    c.execute("SELECT code, name, market, tencent_code FROM stocks WHERE code = ?", (code,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None

    stock_info = dict(row)

    # 最新行情快照
    c.execute("""
        SELECT q.* FROM quotes q
        WHERE q.code = ?
        ORDER BY q.snapshot_time DESC LIMIT 1
    """, (code,))
    q_row = c.fetchone()
    quote = dict(q_row) if q_row else {}

    # 最新排行数据
    c.execute("""
        SELECT r.* FROM rankings r
        WHERE r.code = ?
        ORDER BY r.snapshot_time DESC LIMIT 1
    """, (code,))
    r_row = c.fetchone()
    ranking = dict(r_row) if r_row else {}

    # 近期涨跌幅统计 (近5个交易日)
    c.execute("""
        SELECT change_pct FROM quotes WHERE code = ?
        ORDER BY snapshot_time DESC LIMIT 5
    """, (code,))
    recent = c.fetchall()
    change_stats = {}
    if recent:
        changes = [r["change_pct"] for r in recent]
        change_stats = {
            "today": changes[0] if len(changes) > 0 else 0,
            "week_1": sum(changes[:1]),
            "week_5": sum(changes[:5]),
        }

    conn.close()

    # 计算关键财务指标（估算）
    price = quote.get("price", 0)
    volume = quote.get("volume", 0)
    turnover = quote.get("turnover", 0)  # 万元

    result = {
        "code": code,
        "name": stock_info.get("name", ""),
        "market": stock_info.get("market", ""),
        "tencent_code": stock_info.get("tencent_code", ""),
        "price": price,
        "prev_close": quote.get("prev_close", 0),
        "open": quote.get("open", 0),
        "high": quote.get("high", 0),
        "low": quote.get("low", 0),
        "change_pct": quote.get("change_pct", 0),
        "volume": volume,
        "turnover": turnover,
        "total_amount": ranking.get("total_amount", 0),
        "max_change": ranking.get("max_change", 0),
        "total_volume_rank": ranking.get("total_volume", 0),
        "brokerage_count": ranking.get("brokerage_count", 0),
        "brokerage_list": ranking.get("brokerage_list", ""),
        "change_stats": change_stats,
        "amplitude": round(((quote.get("high", 0) - quote.get("low", 0)) / quote.get("prev_close", 1)) * 100, 2) if quote.get("prev_close") else 0,
        "turnover_rate": round(volume / 10000, 2) if volume else 0,  # 万手为单位简化
    }
    return result


def save_prediction_errors(date, errors_list):
    """
    保存预测误差数据
    errors_list: [{date, code, name, predicted_change, actual_change, error, abs_error, is_accurate, brokerages}, ...]
    """
    conn = get_conn()
    c = conn.cursor()
    # 删除当天的旧数据
    c.execute("DELETE FROM prediction_errors WHERE date = ?", (date,))
    for e in errors_list:
        c.execute("""
            INSERT INTO prediction_errors (date, code, name, predicted_change, actual_change,
                                           error, abs_error, is_accurate, brokerages)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (e["date"], e["code"], e["name"], e["predicted_change"], e["actual_change"],
              e["error"], e["abs_error"], e["is_accurate"], e.get("brokerages", "")))
    conn.commit()
    conn.close()


def save_prediction_stats(date, stats):
    """保存每日预测统计"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO prediction_stats (date, total_count, accurate_count, accuracy_pct,
                                                  avg_error, avg_abs_error, max_error, min_error,
                                                  algo_version, algo_params)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (date, stats["total_count"], stats["accurate_count"], stats["accuracy_pct"],
          stats["avg_error"], stats["avg_abs_error"], stats["max_error"], stats["min_error"],
          stats.get("algo_version", "v1"), stats.get("algo_params", "")))
    conn.commit()
    conn.close()


def get_prediction_stats_history(days=30):
    """获取预测准确率历史"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT date, total_count, accurate_count, accuracy_pct, avg_error, avg_abs_error,
               max_error, min_error, algo_version
        FROM prediction_stats ORDER BY date DESC LIMIT ?
    """, (days,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_prediction_detail(date):
    """获取某日预测误差详情"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT code, name, predicted_change, actual_change, error, abs_error, is_accurate, brokerages
        FROM prediction_errors WHERE date = ? ORDER BY abs_error DESC
    """, (date,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_algo_version():
    """获取当前算法版本和参数"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT version, description, params FROM algo_versions ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"version": "v1.0", "description": "基础算法：真实涨跌幅 × 随机系数(0.7~1.8)", "params": "{}"}


def save_algo_version(version, description, params):
    """保存新算法版本"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO algo_versions (version, description, params) VALUES (?, ?, ?)",
              (version, description, params))
    conn.commit()
    conn.close()


# ==================== 自选股管理 ====================

def watchlist_add(code, name):
    """添加自选股"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO watchlist (code, name) VALUES (?, ?)", (code, name))
    conn.commit()
    conn.close()


def watchlist_remove(code):
    """删除自选股"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM watchlist WHERE code = ?", (code,))
    conn.commit()
    conn.close()


def watchlist_get():
    """获取自选股列表"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT code, name, added_at FROM watchlist ORDER BY added_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def watchlist_codes():
    """获取自选股代码列表"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT code FROM watchlist")
    codes = [r["code"] for r in c.fetchall()]
    conn.close()
    return codes


def watchlist_count():
    """获取自选股数量"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM watchlist")
    row = c.fetchone()
    conn.close()
    return row["cnt"] if row else 0


# ==================== 每日预测数据持久化 ====================

def save_daily_predictions(date, predictions):
    """
    保存每日预测数据
    predictions: [{date, code, name, predicted_change, actual_next_day, actual_change, error, abs_error, error_level, is_accurate, watchlist}, ...]
    """
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM daily_predictions WHERE date = ?", (date,))
    for p in predictions:
        c.execute("""
            INSERT INTO daily_predictions (date, code, name, predicted_change, actual_next_day,
                                           actual_change, error, abs_error, error_level, is_accurate, watchlist)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (p["date"], p["code"], p["name"], p["predicted_change"], p.get("actual_next_day"),
              p.get("actual_change"), p["error"], p["abs_error"], p.get("error_level", "待提升"),
              p["is_accurate"], p.get("watchlist", 0)))
    conn.commit()
    conn.close()


def get_daily_predictions(date, watchlist_only=False):
    """获取某日预测数据"""
    conn = get_conn()
    c = conn.cursor()
    fields = "code, name, predicted_change, actual_next_day, actual_change, error, abs_error, error_level, is_accurate"
    if watchlist_only:
        c.execute(f"""
            SELECT {fields}
            FROM daily_predictions WHERE date = ? AND watchlist = 1
            ORDER BY abs_error DESC
        """, (date,))
    else:
        c.execute(f"""
            SELECT {fields}
            FROM daily_predictions WHERE date = ? ORDER BY abs_error DESC
        """, (date,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_daily_prediction_stats(date, watchlist_only=False):
    """获取某日预测统计"""
    conn = get_conn()
    c = conn.cursor()
    wl_filter = "AND watchlist = 1" if watchlist_only else ""
    c.execute(f"""
        SELECT COUNT(*) as total,
               SUM(is_accurate) as accurate,
               AVG(error) as avg_error,
               AVG(abs_error) as avg_abs_error,
               MAX(abs_error) as max_error,
               MIN(abs_error) as min_error
        FROM daily_predictions WHERE date = ? {wl_filter}
    """, (date,))
    row = c.fetchone()
    conn.close()
    if row and row["total"]:
        return {
            "total": row["total"],
            "accurate": row["accurate"],
            "accuracy_pct": round(row["accurate"] / row["total"] * 100, 2),
            "avg_error": round(row["avg_error"], 2),
            "avg_abs_error": round(row["avg_abs_error"], 2),
            "max_error": round(row["max_error"], 2),
            "min_error": round(row["min_error"], 2),
        }
    return None


def get_prediction_accuracy_trend(days=30, watchlist_only=False):
    """获取预测准确率趋势"""
    conn = get_conn()
    c = conn.cursor()
    wl_filter = "AND watchlist = 1" if watchlist_only else ""
    c.execute(f"""
        SELECT date,
               COUNT(*) as total,
               SUM(is_accurate) as accurate,
               AVG(abs_error) as avg_abs_error
        FROM daily_predictions
        WHERE date >= date('now', '-{days} days') {wl_filter}
        GROUP BY date ORDER BY date DESC
    """)
    rows = c.fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "date": r["date"],
            "total": r["total"],
            "accurate": r["accurate"],
            "accuracy_pct": round(r["accurate"] / r["total"] * 100, 2),
            "avg_abs_error": round(r["avg_abs_error"], 2),
        })
    return result


def get_db_stats():
    """获取数据库统计信息"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM stocks")
    stock_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM snapshots")
    snapshot_count = c.fetchone()[0]
    c.execute("SELECT snapshot_time FROM snapshots ORDER BY snapshot_time DESC LIMIT 1")
    latest = c.fetchone()
    conn.close()
    return {
        "stock_count": stock_count,
        "snapshot_count": snapshot_count,
        "latest_snapshot": latest["snapshot_time"] if latest else None
    }


if __name__ == "__main__":
    init_db()
    print("数据库模块测试通过")
