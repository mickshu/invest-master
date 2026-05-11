"""
调试: 测试股票列表获取
"""

import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = (
    "https://push2.eastmoney.com/api/qt/clist/get?"
    "pn=1&pz=5&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
    "&fltt=2&invt=2&fid=f3&fs=m:1+t:2,m:1+t:23"
    "&fields=f12,f14"
)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://quote.eastmoney.com/center/boardlist.html",
}
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    print(f"RC: {data.get('rc')}")
    print(f"Total: {data.get('total')}")
    if data.get("data") and data["data"].get("diff"):
        print(f"Stocks returned: {len(data['data']['diff'])}")
        for s in data["data"]["diff"][:5]:
            print(f"  {s.get('f12')} {s.get('f14')}")
    else:
        print(f"No data in response: {raw[:500]}")
except Exception as e:
    print(f"Error: {e}")
