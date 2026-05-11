"""
A股全量股票池生成器
使用腾讯行情API批量验证有效股票代码
策略: 按编码规则批量探测，过滤有效股票
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, save_stocks
from data_fetcher import fetch_quotes_batch

def build_stock_list():
    """构建全量A股股票列表"""
    print("构建全量A股股票池...")

    # 生成候选编码（覆盖所有A股编码空间）
    candidates = []

    # 沪市 sh
    for prefix in ["600", "601", "603", "605"]:
        for i in range(1000):
            candidates.append(f"sh{prefix}{i:03d}")
    # 科创板 sh
    for i in range(1000):
        candidates.append(f"sh688{i:03d}")
    # 深市 sz
    for prefix in ["000", "001", "002", "003"]:
        for i in range(1000):
            candidates.append(f"sz{prefix}{i:03d}")
    # 创业板 sz
    for prefix in ["300", "301"]:
        for i in range(1000):
            candidates.append(f"sz{prefix}{i:03d}")
    # 北交所 sz
    for prefix in ["430", "830", "831", "832", "833", "834", "835", "836", "837", "838", "839",
                    "870", "871", "872", "873", "920"]:
        for i in range(1000):
            candidates.append(f"sz{prefix}{i:03d}")

    print(f"候选编码: {len(candidates)} 个")

    valid_stocks = []
    batch_size = 80
    total_batches = (len(candidates) + batch_size - 1) // batch_size

    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i + batch_size]
        batch_num = i // batch_size + 1
        if batch_num % 20 == 0 or batch_num == 1:
            print(f"  批次 {batch_num}/{total_batches}...")

        quotes = fetch_quotes_batch(batch, batch_size=batch_size)
        for code, q in quotes.items():
            if q["price"] > 0 and q["name"]:
                market = "sh" if code.startswith("6") or code.startswith("9") else "sz"
                valid_stocks.append((code, q["name"], market))

        # 每50批次延迟避免被封
        if batch_num % 50 == 0:
            import time
            time.sleep(3)

    print(f"\n有效股票: {len(valid_stocks)} 只")
    count = save_stocks(valid_stocks)
    print(f"已保存 {count} 只到数据库")

if __name__ == "__main__":
    init_db()
    build_stock_list()
