"""
定时全量数据抓取脚本
可被 cron 调用，每 30 分钟执行一次
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db
from data_fetcher import fetch_and_store_all

if __name__ == "__main__":
    init_db()
    print("启动定时全量数据抓取...")
    count = fetch_and_store_all()
    if count > 0:
        print(f"成功: 更新了 {count} 只股票数据")
    else:
        print("警告: 未获取到数据")
