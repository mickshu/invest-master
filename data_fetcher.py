"""
全量A股数据抓取器
- 获取A股全部股票列表（沪深主板+创业板+科创板+北交所）
- 批量查询腾讯行情API
- 生成隔夜挂单排行数据
"""

import urllib.request
import json
import ssl
import re
import time
import datetime
import random

import sys
sys.path.insert(0, "/home/admin/overnight-orders-demo")
from database import (
    get_conn, init_db, save_stocks, get_all_tencent_codes,
    save_quotes, save_rankings, save_snapshot
)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BROKERAGES = [
    "中信证券", "华泰证券", "国泰君安", "招商证券",
    "广发证券", "中信建投", "海通证券", "申万宏源",
    "银河证券", "东方财富", "同花顺"
]

# 券商市场份额权重
BROKER_WEIGHTS = {
    "中信证券": 0.15, "华泰证券": 0.12, "国泰君安": 0.10,
    "招商证券": 0.08, "广发证券": 0.07, "中信建投": 0.07,
    "海通证券": 0.06, "申万宏源": 0.06, "银河证券": 0.06,
    "东方财富": 0.12, "同花顺": 0.11,
}


def fetch_all_stock_list():
    """
    从腾讯获取A股全部股票列表
    分市场查询: 沪市主板、深市主板、创业板、科创板、北交所
    """
    all_stocks = []

    # 腾讯股票列表API参数
    # fs参数: m:0+t:6(沪主板), m:0+t:80(深主板), m:1+t:2(创业板), m:1+t:23(科创板), m:0+t:81+s:2048(北交所)
    segments = [
        "m:1+t:2,m:1+t:23",     # 沪深(深市)
        "m:0+t:6,m:0+t:80",      # 沪市主板
        "m:0+t:81+s:2048",       # 北交所
    ]

    for seg in segments:
        pn = 1
        while True:
            url = (
                f"https://push2.eastmoney.com/api/qt/clist/get?"
                f"pn={pn}&pz=500&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
                f"&fltt=2&invt=2&fid=f3&fs={seg}"
                f"&fields=f12,f14"
            )
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/center/boardlist.html",
            }
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except Exception:
                break

            if not data.get("data") or not data["data"].get("diff"):
                break

            for s in data["data"]["diff"]:
                code = s.get("f12", "")
                name = s.get("f14", "")
                if code and name:
                    market = "sh" if code.startswith("6") or code.startswith("9") else "sz"
                    all_stocks.append((code, name, market))

            total = data.get("total", 0)
            if pn * 500 >= total:
                break
            pn += 1
            time.sleep(0.5)

    return all_stocks


def sync_stock_list():
    """同步股票列表到数据库"""
    print("同步股票列表...")
    stocks = fetch_all_stock_list()
    count = save_stocks(stocks)
    print(f"  已同步 {count} 只股票到数据库")
    return count


def fetch_quotes_batch(tencent_codes, batch_size=80):
    """
    批量查询腾讯行情API
    tencent_codes: list of str, e.g. ["sh600519", "sz000858", ...]
    batch_size: 每批请求的股票数量（腾讯API支持批量，但不宜过多）
    返回: dict {code: {code, name, price, change_pct, volume, turnover, prev_close, open, high, low}}
    """
    all_quotes = {}

    for i in range(0, len(tencent_codes), batch_size):
        batch = tencent_codes[i:i + batch_size]
        url = f"https://qt.gtimg.cn/q={','.join(batch)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                raw = resp.read().decode("gbk", errors="replace")
        except Exception as e:
            print(f"  批次 [{i}:{i+len(batch)}] 请求失败: {e}")
            time.sleep(2)
            continue

        # 解析腾讯行情数据 (sh/sz/bj)
        pattern = r'v_(sh|sz|bj)(\d+)="([^"]+)"'
        for match in re.finditer(pattern, raw):
            prefix = match.group(1)
            code = match.group(2)
            fields = match.group(3).split("~")
            if len(fields) < 10:
                continue
            try:
                price = float(fields[3]) if fields[3] else 0
                prev_close = float(fields[4]) if fields[4] else 0
                today_open = float(fields[5]) if fields[5] else 0
                volume = int(fields[6]) if fields[6] else 0
                turnover = float(fields[37]) / 10000 if len(fields) > 37 and fields[37] else 0  # 元转万
                high = float(fields[33]) if len(fields) > 33 and fields[33] else 0
                low = float(fields[34]) if len(fields) > 34 and fields[34] else 0
                change_pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else 0

                all_quotes[code] = {
                    "code": code,
                    "name": fields[1],
                    "price": price,
                    "prev_close": prev_close,
                    "open": today_open,
                    "high": high,
                    "low": low,
                    "volume": volume,
                    "turnover": turnover,
                    "change_pct": change_pct,
                }
            except (ValueError, IndexError):
                continue

        # 批次间延迟，避免被封
        if i + batch_size < len(tencent_codes):
            time.sleep(1)

    return all_quotes


def get_daily_limit(code):
    """获取A股涨跌幅限制 (%)"""
    if code.startswith("300") or code.startswith("301") or code.startswith("688"):
        return 20.0
    if code.startswith("83") or code.startswith("87") or code.startswith("920") or code.startswith("43"):
        return 30.0
    return 10.0


def generate_overnight_data(quotes):
    """
    基于真实行情生成隔夜挂单数据
    - 价格和涨跌幅使用真实数据
    - 挂单金额根据成交量算法推算，区分买卖单
    - 券商分布按市场份额分配
    """
    overnight_data = []
    snapshot_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for code, q in quotes.items():
        if q["volume"] == 0 or q["price"] == 0:
            continue

        limit = get_daily_limit(code)
        num_brokers = random.randint(3, 8)
        selected_brokers = random.sample(BROKERAGES, num_brokers)

        for broker in selected_brokers:
            weight = BROKER_WEIGHTS.get(broker, 0.05)
            overnight_ratio = random.uniform(0.005, 0.10)
            order_volume = int(q["volume"] * weight * overnight_ratio)
            order_amount = round(order_volume * 100 * q["price"] / 10000, 0)
            
            # 区分买卖单 (随机分配比例 40%-60%)
            buy_ratio = random.uniform(0.4, 0.6)
            buy_amount = round(order_amount * buy_ratio, 0)
            sell_amount = order_amount - buy_amount
            
            expected_change = round(q["change_pct"] * random.uniform(0.7, 1.8), 2)
            expected_change = max(-limit, min(limit, expected_change))

            overnight_data.append({
                "code": code,
                "name": q["name"],
                "brokerage": broker,
                "order_amount": int(order_amount),
                "buy_amount": int(buy_amount),
                "sell_amount": int(sell_amount),
                "expected_change": expected_change,
                "order_volume": order_volume,
                "price": q["price"],
                "change_pct": q["change_pct"],
            })

    return overnight_data, snapshot_time


def aggregate_rankings(overnight_data):
    """聚合隔夜数据为按股票维度的排行"""
    stock_map = {}
    for d in overnight_data:
        key = d["code"]
        if key not in stock_map:
            stock_map[key] = {
                "code": d["code"],
                "name": d["name"],
                "total_amount": 0,
                "buy_amount": 0,
                "sell_amount": 0,
                "max_change": -999,
                "brokerages": set(),
                "total_volume": 0,
                "price": d["price"],
                "change_pct": d["change_pct"],
            }
        stock_map[key]["total_amount"] += d["order_amount"]
        stock_map[key]["buy_amount"] += d.get("buy_amount", 0)
        stock_map[key]["sell_amount"] += d.get("sell_amount", 0)
        stock_map[key]["max_change"] = max(stock_map[key]["max_change"], d["expected_change"])
        stock_map[key]["brokerages"].add(d["brokerage"])
        stock_map[key]["total_volume"] += d["order_volume"]

    result = []
    for item in stock_map.values():
        result.append({
            "code": item["code"],
            "name": item["name"],
            "price": item["price"],
            "change_pct": item["change_pct"],
            "total_amount": item["total_amount"],
            "buy_amount": item["buy_amount"],
            "sell_amount": item["sell_amount"],
            "max_change": item["max_change"],
            "total_volume": item["total_volume"],
            "brokerage_count": len(item["brokerages"]),
            "brokerage_list": ", ".join(sorted(item["brokerages"])),
        })
    return result


def fetch_and_store_all():
    """
    主流程: 获取全量股票 -> 批量查询行情 -> 生成排行 -> 存储数据库
    """
    print(f"\n{'='*60}")
    print(f"全量数据抓取开始: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # 1. 获取所有股票编码
    stock_rows = get_all_tencent_codes()
    if not stock_rows:
        print("数据库无股票数据，先同步股票列表...")
        sync_stock_list()
        stock_rows = get_all_tencent_codes()

    print(f"  股票池: {len(stock_rows)} 只")
    tencent_codes = [r["tencent_code"] for r in stock_rows]

    # 2. 批量查询行情
    print("  正在查询行情数据...")
    quotes = fetch_quotes_batch(tencent_codes, batch_size=80)
    print(f"  获取到 {len(quotes)} 只股票行情")

    if not quotes:
        print("  行情数据为空，跳过")
        return 0

    # 3. 生成隔夜数据
    print("  生成隔夜挂单数据...")
    overnight_data, snapshot_time = generate_overnight_data(quotes)

    # 4. 聚合排行
    print("  聚合排行数据...")
    rankings = aggregate_rankings(overnight_data)

    # 5. 存储到数据库
    print("  存储数据到数据库...")
    quotes_list = list(quotes.values())
    save_quotes(quotes_list, snapshot_time)
    save_rankings(rankings, snapshot_time)
    save_snapshot(snapshot_time, len(rankings))

    print(f"  快照时间: {snapshot_time}")
    print(f"  排行股票数: {len(rankings)}")
    print(f"  数据已存储")
    print(f"{'='*60}\n")

    return len(rankings)


if __name__ == "__main__":
    init_db()
    fetch_and_store_all()
