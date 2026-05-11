"""
测试多个A股公开数据源的可用性
"""

import json
import urllib.request
import ssl

# 关闭SSL验证（测试环境）
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def fetch_with_retry(url, headers=None, timeout=10):
    """通用请求函数"""
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")


def test_sina():
    """测试新浪行情API"""
    print("\n" + "=" * 50)
    print("测试1: 新浪实时行情")
    print("=" * 50)
    try:
        # 新浪实时行情（支持批量）
        url = "https://hq.sinajs.cn/list=sh600519,sz000858,sh601318,sz300750"
        headers = {"Referer": "https://finance.sina.com.cn"}
        data = fetch_with_retry(url, headers=headers)
        print(data[:500])
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False


def test_tencent():
    """测试腾讯行情API"""
    print("\n" + "=" * 50)
    print("测试2: 腾讯实时行情")
    print("=" * 50)
    try:
        url = "https://qt.gtimg.cn/q=sh600519,sz000858,sh601318,sz300750"
        data = fetch_with_retry(url)
        print(data[:500])
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False


def test_eastmoney_simple():
    """测试东方财富简单接口"""
    print("\n" + "=" * 50)
    print("测试3: 东方财富个股行情")
    print("=" * 50)
    try:
        # 东方财富个股资金流
        url = (
            "https://push2.eastmoney.com/api/qt/stock/fflow/daykline/get?"
            "lmt=0&klt=1&fields1=f1,f2,f3&fields2=f51,f52,f53,f54,f55,f56,f57"
            "&secid=1.600519&ut=b2884a393a59ad64002292a3e90d46a5"
        )
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://quote.eastmoney.com/",
        }
        data = fetch_with_retry(url, headers=headers)
        result = json.loads(data)
        print(json.dumps(result, ensure_ascii=False, indent=2)[:800])
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False


def test_eastmoney_list():
    """测试东方财富列表接口（带更完整headers）"""
    print("\n" + "=" * 50)
    print("测试4: 东方财富板块排行")
    print("=" * 50)
    try:
        url = (
            "https://push2.eastmoney.com/api/qt/clist/get?"
            "pn=1&pz=5&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
            "&fltt=2&invt=2&fid=f3"
            "&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
            "&fields=f12,f14,f2,f3,f62"
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://quote.eastmoney.com/center/boardlist.html",
            "Accept": "application/json, text/plain, */*",
        }
        data = fetch_with_retry(url, headers=headers)
        result = json.loads(data)
        if result.get("data") and result["data"].get("diff"):
            for s in result["data"]["diff"][:5]:
                print(f"  {s.get('f12')} {s.get('f14')}  涨跌幅:{s.get('f3')}%  主力:{s.get('f62')}")
            return True
        else:
            print(f"无数据: {json.dumps(result, ensure_ascii=False)[:300]}")
            return False
    except Exception as e:
        print(f"失败: {e}")
        return False


def test_cctv():
    """测试央视/央视财经数据"""
    print("\n" + "=" * 50)
    print("测试5: AKShare替代方案 - 检查akshare是否已安装")
    print("=" * 50)
    try:
        import akshare as ak
        print(f"akshare版本: {ak.__version__}")
        # 测试获取板块资金流向
        df = ak.stock_individual_fund_flow(stock="600519", market="sh")
        print(df.head().to_string())
        return True
    except ImportError:
        print("akshare未安装")
        return False
    except Exception as e:
        print(f"akshare调用失败: {e}")
        return False


if __name__ == "__main__":
    results = {}
    results["新浪行情"] = test_sina()
    results["腾讯行情"] = test_tencent()
    results["东方财富个股"] = test_eastmoney_simple()
    results["东方财富列表"] = test_eastmoney_list()
    results["akshare"] = test_cctv()

    print("\n" + "=" * 50)
    print("数据源测试结果汇总:")
    print("=" * 50)
    for name, ok in results.items():
        status = "可用" if ok else "不可用"
        print(f"  {name}: {status}")
