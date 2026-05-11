"""
从新浪获取A股股票名称列表（高效方式）
新浪提供股票编码到名称的映射表
"""

import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_sina_stock_list():
    """
    新浪提供的全市场股票列表
    格式: var hq_str_sh600519="贵州茅台";
    """
    stocks = []

    # 方式1: 从新浪分类列表获取
    pages_to_fetch = [
        ("hs_a", "沪深A股"),  # 沪深全部A股
        ("sh_a", "沪市A股"),
        ("sz_a", "深市A股"),
        ("cyb", "创业板"),
    ]

    for node, name in pages_to_fetch:
        all_from_node = []
        page = 1
        while True:
            url = (
                f"http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
                f"Market_Center.getHQNodeData?page={page}&num=80&sort=symbol&asc=1&node={node}"
            )
            headers = {"User-Agent": "Mozilla/5.0"}
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                    raw = resp.read().decode("gbk", errors="replace")
                import json
                data = json.loads(raw)
                if not data:
                    break
                for s in data:
                    code = s.get("symbol", "").strip()
                    name = s.get("name", "").strip()
                    if code and name:
                        # 统一6位编码
                        code = code.lstrip("sh").lstrip("sz").lstrip("bj")
                        if code.isdigit() and len(code) == 6:
                            # 北交所
                            if code.startswith("920") or code.startswith("83") or code.startswith("43") or code.startswith("87"):
                                market = "bj"
                            elif code.startswith("6") or code.startswith("9") or code.startswith("5"):
                                market = "sh"
                            else:
                                market = "sz"
                            all_from_node.append((code, name, market))
                if len(data) < 80:
                    break
                page += 1
            except Exception as e:
                print(f"  {name} 第{page}页失败: {e}")
                break

        print(f"  {name}: {len(all_from_node)} 只")
        stocks.extend(all_from_node)

    # 去重
    seen = set()
    unique_stocks = []
    for code, name, market in stocks:
        if code not in seen:
            seen.add(code)
            unique_stocks.append((code, name, market))

    return unique_stocks


if __name__ == "__main__":
    stocks = fetch_sina_stock_list()
    print(f"\n总计: {len(stocks)} 只")
    for s in stocks[:10]:
        print(f"  {s}")

    if stocks:
        import sys
        sys.path.insert(0, "/home/admin/overnight-orders-demo")
        from database import init_db, save_stocks
        init_db()
        count = save_stocks(stocks)
        print(f"\n已保存 {count} 只股票到数据库")
