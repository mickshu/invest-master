"""
A股券商隔夜挂单排行榜 - Web服务
支持分页查询、券商筛选、多维度排序
"""

import json
import datetime
import os
import http.server
import socketserver
import urllib.parse

import sys
sys.path.insert(0, os.path.dirname(__file__))
from database import init_db, get_rankings_paged, get_db_stats, get_latest_snapshot_time, get_snapshot_history
from data_fetcher import fetch_and_store_all, BROKERAGES, sync_stock_list

PORT = 5000

# 后台抓取锁
_fetching = False
_last_fetch_time = None


def start_background_fetch():
    """启动后台数据抓取"""
    global _fetching, _last_fetch_time
    if _fetching:
        return False
    _fetching = True
    try:
        count = fetch_and_store_all()
        _last_fetch_time = datetime.datetime.now()
        print(f"数据抓取完成，{count} 只股票已更新")
        return True
    except Exception as e:
        print(f"数据抓取失败: {e}")
        return False
    finally:
        _fetching = False


def get_html():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


class Handler(http.server.SimpleHTTPRequestHandler):
    def run_prediction_task(self, watchlist_only=False):
        """Background task to update prediction data"""
        global _fetching
        if _fetching:
            return
        _fetching = True
        try:
            from prediction_analysis import analyze_predictions
            # Always run full analysis to ensure all data is consistent and up to date
            analyze_predictions()
            analyze_predictions(watchlist_only=True)
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Prediction update complete.")
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Prediction update failed: {e}")
        finally:
            _fetching = False

    def do_POST(self):
        """Handle POST requests (for watchlist add)"""
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/watchlist":
            from database import watchlist_add
            params = urllib.parse.parse_qs(parsed.query)
            code = params.get("code", [""])[0]
            name = params.get("name", [""])[0]
            if not code:
                result = json.dumps({"success": False, "error": "缺少code"}, ensure_ascii=False)
            else:
                watchlist_add(code, name)
                # Trigger background prediction update
                import threading
                threading.Thread(target=self.run_prediction_task, daemon=True).start()
                result = json.dumps({"success": True, "message": "预测分析已启动，正在更新数据..."}, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        """Handle DELETE requests (for watchlist remove)"""
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/watchlist":
            from database import watchlist_remove
            code = urllib.parse.parse_qs(parsed.query).get("code", [""])[0]
            if not code:
                result = json.dumps({"success": False, "error": "缺少code"}, ensure_ascii=False)
            else:
                watchlist_remove(code)
                result = json.dumps({"success": True}, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            html = get_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        elif path == "/api/rankings":
            try:
                params = urllib.parse.parse_qs(parsed.query)
                sort_field = params.get("sort_field", ["total_amount"])[0]
                sort_order = params.get("sort_order", ["DESC"])[0]
                page = int(params.get("page", ["1"])[0])
                page_size = int(params.get("page_size", ["30"])[0])
                brokerage = params.get("brokerage", ["全部"])[0]
                stock_code = params.get("stock_code", [None])[0]
                watchlist_only = params.get("watchlist", ["0"])[0] == "1"
                snapshot_time = params.get("snapshot_time", [None])[0]

                if page_size > 100:
                    page_size = 100
                if page < 1:
                    page = 1

                data, total = get_rankings_paged(
                    sort_field=sort_field, sort_order=sort_order.upper(),
                    page=page, page_size=page_size,
                    brokerage=brokerage, stock_code=stock_code, watchlist_only=watchlist_only, snapshot_time=snapshot_time
                )

                total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

                result = json.dumps({
                    "date": datetime.date.today().strftime("%Y-%m-%d"),
                    "update_time": get_latest_snapshot_time() or "N/A",
                    "data_source": "腾讯实时行情",
                    "brokerage": brokerage,
                    "sort_field": sort_field,
                    "sort_order": sort_order,
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages,
                    "data": data
                }, ensure_ascii=False)

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(result.encode("utf-8"))

            except Exception as e:
                error_resp = json.dumps({"error": str(e)}, ensure_ascii=False)
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(error_resp.encode("utf-8"))

        elif path == "/api/brokerages":
            result = json.dumps({
                "brokerages": ["全部"] + BROKERAGES,
                "data_source": "腾讯实时行情"
            }, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))

        elif path == "/api/status":
            stats = get_db_stats()
            result = json.dumps({
                "stock_count": stats["stock_count"],
                "snapshot_count": stats["snapshot_count"],
                "latest_snapshot": stats["latest_snapshot"],
                "fetching": _fetching,
                "last_fetch": str(_last_fetch_time) if _last_fetch_time else "N/A",
            }, ensure_ascii=False, default=str)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))

        elif path == "/api/sync":
            """手动触发全量数据同步"""
            if _fetching:
                result = json.dumps({"status": "fetching", "message": "数据抓取中，请稍后重试"}, ensure_ascii=False)
            else:
                import threading
                t = threading.Thread(target=start_background_fetch, daemon=True)
                t.start()
                result = json.dumps({"status": "started", "message": "数据抓取已启动"}, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))

        elif path == "/api/snapshots":
            """获取快照历史"""
            limit = int(urllib.parse.parse_qs(parsed.query).get("limit", ["20"])[0])
            history = get_snapshot_history(limit=min(limit, 100))
            result = json.dumps({"snapshots": history}, ensure_ascii=False, default=str)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))

        elif path == "/api/stocks":
            """股票搜索（支持代码/名称模糊匹配）"""
            from database import get_conn
            q = urllib.parse.parse_qs(parsed.query).get("q", [""])[0].strip().lower()
            conn = get_conn()
            c = conn.cursor()
            if q:
                c.execute("SELECT code, name FROM stocks WHERE code LIKE ? OR LOWER(name) LIKE ? LIMIT 50",
                          (f"%{q}%", f"%{q}%"))
            else:
                c.execute("SELECT code, name FROM stocks LIMIT 100")
            rows = [{"code": r["code"], "name": r["name"]} for r in c.fetchall()]
            conn.close()
            result = json.dumps({"stocks": rows}, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))

        elif path == "/stock":
            """个股详情页 (K线图)"""
            html_path = os.path.join(os.path.dirname(__file__), "templates", "stock.html")
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        elif path == "/api/stock-detail":
            """个股详情数据API"""
            from database import get_stock_detail
            code = urllib.parse.parse_qs(parsed.query).get("code", [""])[0]
            if not code:
                result = json.dumps({"error": "缺少code参数"}, ensure_ascii=False)
            else:
                detail = get_stock_detail(code)
                if detail:
                    result = json.dumps(detail, ensure_ascii=False)
                else:
                    result = json.dumps({"error": "未找到该股票"}, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))

        elif path == "/api/kline":
            """K线数据API"""
            code = urllib.parse.parse_qs(parsed.query).get("code", [""])[0]
            if not code:
                result = json.dumps({"error": "缺少code参数"}, ensure_ascii=False)
            else:
                import ssl
                _ctx = ssl.create_default_context()
                _ctx.check_hostname = False
                _ctx.verify_mode = ssl.CERT_NONE
                market = "sh" if code.startswith(("6","9")) else "sz"
                url = f"https://quotes.sina.cn/cn/api/jsonp_v2.php/var/CN_MarketDataService.getKLineData?symbol={market}{code}&scale=240&ma=no&datalen=60"
                headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.cn/"}
                req = urllib.request.Request(url, headers=headers)
                try:
                    with urllib.request.urlopen(req, timeout=10, context=_ctx) as resp:
                        raw = resp.read().decode("utf-8", errors="replace")
                    start = raw.find('var([')
                    if start >= 0:
                        end = raw.rfind('])')
                        if end > start:
                            items = json.loads(raw[start+4:end+1])
                            klines = []
                            for item in items:
                                klines.append({
                                    "date": item.get("day", ""),
                                    "open": float(item.get("open", 0)),
                                    "high": float(item.get("high", 0)),
                                    "low": float(item.get("low", 0)),
                                    "close": float(item.get("close", 0)),
                                    "volume": float(item.get("volume", 0)),
                                })
                            result = json.dumps({"code": code, "klines": klines}, ensure_ascii=False)
                        else:
                            result = json.dumps({"code": code, "klines": []}, ensure_ascii=False)
                    else:
                        result = json.dumps({"code": code, "klines": []}, ensure_ascii=False)
                except Exception as e:
                    result = json.dumps({"code": code, "klines": [], "error": str(e)}, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))

        elif path == "/prediction":
            """预测分析报告页面"""
            html_path = os.path.join(os.path.dirname(__file__), "templates", "prediction.html")
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        elif path == "/api/prediction-stats":
            """预测统计历史"""
            from database import get_prediction_stats_history
            days = int(urllib.parse.parse_qs(parsed.query).get("days", ["30"])[0])
            stats = get_prediction_stats_history(days=min(days, 60))
            result = json.dumps({"stats": stats}, ensure_ascii=False, default=str)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))

        elif path == "/api/prediction-detail":
            """预测误差详情"""
            from database import get_daily_predictions, get_daily_prediction_stats
            date = urllib.parse.parse_qs(parsed.query).get("date", [""])[0]
            wl_only = urllib.parse.parse_qs(parsed.query).get("mode", [""])[0] == "watchlist"
            if not date:
                result = json.dumps({"error": "缺少date参数"}, ensure_ascii=False)
            else:
                errors = get_daily_predictions(date, watchlist_only=wl_only)
                result = json.dumps({"date": date, "errors": errors}, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))

        elif path == "/api/run-prediction":
            """手动触发预测分析"""
            if _fetching:
                result = json.dumps({"status": "running", "message": "数据采集中，请稍后"}, ensure_ascii=False)
            else:
                import threading
                def run_pred():
                    global _fetching
                    _fetching = True
                    try:
                        from prediction_analysis import analyze_predictions
                        analyze_predictions()
                        analyze_predictions(watchlist_only=True)
                    except Exception as e:
                        print(f"预测分析失败: {e}")
                    finally:
                        _fetching = False
                t = threading.Thread(target=run_pred, daemon=True)
                t.start()
                result = json.dumps({"status": "started", "message": "预测分析已启动"}, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))

        elif path == "/api/prediction-stock-filter":
            """按股票代码筛选预测结果"""
            from database import get_conn
            codes_param = urllib.parse.parse_qs(parsed.query).get("codes", [""])[0].strip()
            date = urllib.parse.parse_qs(parsed.query).get("date", [""])[0].strip()
            if not codes_param:
                result = json.dumps({"error": "缺少codes参数"}, ensure_ascii=False)
            else:
                codes = [c.strip() for c in codes_param.split(",") if c.strip()]
                conn = get_conn()
                c = conn.cursor()
                # 从 daily_predictions 查询
                if date:
                    placeholders = ",".join("?" for _ in codes)
                    c.execute(f"""
                        SELECT code, name, predicted_change, actual_next_day, actual_change,
                               error, abs_error, error_level, is_accurate
                        FROM daily_predictions
                        WHERE date = ? AND code IN ({placeholders})
                        ORDER BY abs_error DESC
                    """, [date] + codes)
                else:
                    # 不指定日期则查最新日期的数据
                    placeholders = ",".join("?" for _ in codes)
                    c.execute(f"""
                        SELECT code, name, predicted_change, actual_next_day, actual_change,
                               error, abs_error, error_level, is_accurate
                        FROM daily_predictions
                        WHERE date = (SELECT MAX(date) FROM daily_predictions) AND code IN ({placeholders})
                        ORDER BY abs_error DESC
                    """, codes)
                rows = [dict(r) for r in c.fetchall()]

                # 如果 daily_predictions 查不到，回退到 prediction_errors
                if not rows and date:
                    placeholders = ",".join("?" for _ in codes)
                    c.execute(f"""
                        SELECT code, name, predicted_change, actual_change,
                               error, abs_error, is_accurate, brokerages
                        FROM prediction_errors
                        WHERE date = ? AND code IN ({placeholders})
                        ORDER BY abs_error DESC
                    """, [date] + codes)
                    rows = [dict(r) for r in c.fetchall()]

                # 标记哪些代码没找到
                found_codes = set(r["code"] for r in rows)
                not_found = [c for c in codes if c not in found_codes]

                conn.close()
                result = json.dumps({
                    "stocks": rows,
                    "not_found": not_found,
                    "total_found": len(rows),
                    "total_searched": len(codes),
                }, ensure_ascii=False, default=str)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))

        elif path == "/api/prediction-trend":
            """个股历史预测趋势 (预测值+实际值双趋势线)"""
            from database import get_conn
            code = urllib.parse.parse_qs(parsed.query).get("code", [""])[0].strip()
            if not code:
                result = json.dumps({"error": "缺少code参数"}, ensure_ascii=False)
            else:
                conn = get_conn()
                c = conn.cursor()
                c.execute("""
                    SELECT date, predicted_change, actual_change, error, error_level
                    FROM daily_predictions
                    WHERE code = ?
                    ORDER BY date ASC
                """, (code,))
                rows = [dict(r) for r in c.fetchall()]

                # 如果 daily_predictions 没有数据，回退到 prediction_errors
                if not rows:
                    c.execute("""
                        SELECT date, predicted_change, actual_change, error,
                               CASE WHEN is_accurate=1 THEN '准确'
                                    WHEN abs(error)>3 THEN '离谱'
                                    ELSE '待提升' END as error_level
                        FROM prediction_errors
                        WHERE code = ?
                        ORDER BY date ASC
                    """, (code,))
                    rows = [dict(r) for r in c.fetchall()]

                # 获取股票名称
                if rows:
                    c.execute("SELECT name FROM stocks WHERE code = ?", (code,))
                    stock_row = c.fetchone()
                    stock_name = stock_row["name"] if stock_row else rows[0].get("name", "")
                else:
                    stock_name = ""

                conn.close()
                result = json.dumps({
                    "code": code,
                    "name": stock_name,
                    "history": rows,
                }, ensure_ascii=False, default=str)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))

        elif path == "/watchlist":
            """自选股管理页面"""
            html_path = os.path.join(os.path.dirname(__file__), "templates", "watchlist.html")
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        elif path == "/api/watchlist":
            """自选股列表查询 (GET)"""
            from database import watchlist_get
            wl = watchlist_get()
            result = json.dumps({"watchlist": wl}, ensure_ascii=False, default=str)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {args[0]}")


if __name__ == "__main__":
    print("=" * 60)
    print("A股券商隔夜挂单排行榜 - 全量数据版")
    print(f"访问地址: http://127.0.0.1:{PORT}")
    print(f"券商数: {len(BROKERAGES)} 家")
    print("=" * 60)

    # 初始化数据库
    init_db()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print("服务器已启动，按 Ctrl+C 停止")
        httpd.serve_forever()
