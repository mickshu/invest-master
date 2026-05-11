"""
测试东方财富公开API - 验证数据源可用性
使用东方财富资金流向接口作为真实数据源
"""

import json
import urllib.request
import urllib.error
import datetime


def test_eastmoney_api():
    """测试东方财富资金流向API"""
    # 东方财富 主力资金流向 API
    # 返回: 股票代码、名称、主力净流入、超大单、大单等
    url = (
        "https://push2.eastmoney.com/api/qt/clist/get?"
        "pn=1&pz=10&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
        "&fltt=2&invt=2&fid=f62"
        "&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"
        "&fields=f12,f14,f2,f3,f62,f184,f66,f69,f72,f75"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://data.eastmoney.com/",
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print("=" * 70)
            print("东方财富API 连接成功!")
            print("=" * 70)
            print(f"状态: {data.get('rc', 'N/A')}")
            print(f"总数: {data.get('total', 0)}")

            if data.get("data") and data["data"].get("diff"):
                stocks = data["data"]["diff"]
                print(f"\n前10条数据样例:")
                print(f"{'排名':<4} {'代码':<8} {'名称':<10} {'主力净流入(万)':<15} {'涨幅%':<8} {'超大单(万)':<12}")
                print("-" * 70)
                for i, s in enumerate(stocks[:10], 1):
                    code = s.get("f12", "")
                    name = s.get("f14", "")
                    net_inflow = s.get("f62", 0)
                    change = s.get("f3", 0)
                    super_large = s.get("f66", 0)
                    # f62主力净流入单位是元，转为万元
                    net_inflow_wan = net_inflow / 10000 if net_inflow else 0
                    super_wan = super_large / 10000 if super_large else 0
                    print(f"{i:<4} {code:<8} {name:<10} {net_inflow_wan:>12,.0f}  {change:>6.2f}%  {super_wan:>10,.0f}")

                # 返回字段说明
                print("\n字段说明:")
                print("  f12: 股票代码")
                print("  f14: 股票名称")
                print("  f2:  最新价")
                print("  f3:  涨跌幅(%)")
                print("  f62: 主力净流入(元)")
                print("  f184: 主力净流入占比(%)")
                print("  f66: 超大单净流入(元)")
                print("  f69: 超大单净流入占比(%)")
                print("  f72: 大单净流入(元)")
                print("  f75: 大单净流入占比(%)")

                return True
            else:
                print("API返回无数据")
                print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
                return False

    except urllib.error.URLError as e:
        print(f"连接失败: {e}")
        return False
    except Exception as e:
        print(f"错误: {e}")
        return False


if __name__ == "__main__":
    test_eastmoney_api()
