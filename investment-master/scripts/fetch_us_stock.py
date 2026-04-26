#!/usr/bin/env python3
"""美股数据获取与结构化整合脚本。

从 finance-data-retrieval API 获取美股数据并结构化输出，
支持 us_daily（行情+PE/PB）和 us_fina_indicator（财务指标）。

用法:
    # 获取完整美股数据
    python3 fetch_us_stock.py AAPL

    # 仅获取行情
    python3 fetch_us_stock.py AAPL --only daily

    # 仅获取财务指标
    python3 fetch_us_stock.py AAPL --only fina

    # 指定日期范围
    python3 fetch_us_stock.py AAPL --start 20250101 --end 20250425

注意: 此脚本需要通过 finance-data-retrieval 的 API 接口获取数据。
      如 API 不可用，请改用 MCP financial-datasets 工具或 neodata 查询。
"""

import json
import sys
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Optional


API_BASE = "https://www.codebuddy.cn/v2/tool/financedata"


def call_finance_api(api_name: str, params: dict, fields: str = "") -> dict:
    """调用 finance-data-retrieval API。"""
    payload = {
        "api_name": api_name,
        "params": {k: v for k, v in params.items() if v is not None},
    }
    if fields:
        payload["fields"] = fields

    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        API_BASE,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"❌ API 请求失败: {e}", file=sys.stderr)
        return {"code": -1, "msg": str(e)}
    except Exception as e:
        print(f"❌ 请求异常: {e}", file=sys.stderr)
        return {"code": -1, "msg": str(e)}


def fetch_us_daily(ticker: str, start_date: str = None, end_date: str = None) -> dict:
    """获取美股日线行情（含PE/PB/市值）。"""
    params = {"ts_code": ticker}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    fields = "ts_code,trade_date,open,high,low,close,pre_close,pct_change,vol,amount,pe,pb,total_mv,turnover_ratio"

    result = call_finance_api("us_daily", params, fields)
    return result


def fetch_us_fina_indicator(ticker: str, period: str = None) -> dict:
    """获取美股财务指标。"""
    params = {"ts_code": ticker}
    if period:
        params["period"] = period

    fields = ("ts_code,end_date,ind_type,security_name_abbr,operate_income,operate_income_yoy,"
              "gross_profit_ratio,net_profit_ratio,parent_holder_netprofit,parent_holder_netprofit_yoy,"
              "basic_eps,diluted_eps,roe_avg,roa,current_ratio,debt_asset_ratio,equity_ratio,"
              "currency_abbr")

    result = call_finance_api("us_fina_indicator", params, fields)
    return result


def parse_daily_to_metrics(data: dict) -> dict:
    """将 us_daily 返回数据解析为指标字典。"""
    fields = data.get('data', {}).get('fields', [])
    items = data.get('data', {}).get('items', [])

    if not items:
        return {}

    # 取最新一条
    item = items[0]
    field_map = {f: i for i, f in enumerate(fields)}

    def get_val(field_name, as_str=False):
        if field_name in field_map:
            try:
                val = item[field_map[field_name]]
                if val is None:
                    return None
                if as_str:
                    return str(int(float(val)))
                return float(val)
            except (ValueError, TypeError, IndexError):
                return None
        return None

    return {
        'ticker': get_val('ts_code', as_str=True),
        'trade_date': get_val('trade_date', as_str=True),
        'close': get_val('close'),
        'open': get_val('open'),
        'high': get_val('high'),
        'low': get_val('low'),
        'pre_close': get_val('pre_close'),
        'pct_change': get_val('pct_change'),
        'vol': get_val('vol'),
        'amount': get_val('amount'),
        'pe': get_val('pe'),
        'pb': get_val('pb'),
        'total_mv': get_val('total_mv'),
        'turnover_ratio': get_val('turnover_ratio'),
    }


def parse_fina_to_metrics(data: dict) -> dict:
    """将 us_fina_indicator 返回数据解析为指标字典。"""
    fields = data.get('data', {}).get('fields', [])
    items = data.get('data', {}).get('items', [])

    if not items:
        return {}

    # 取最新一条
    item = items[0]
    field_map = {f: i for i, f in enumerate(fields)}

    def get_val(field_name, as_str=False):
        if field_name in field_map:
            try:
                val = item[field_map[field_name]]
                if val is None:
                    return None
                if as_str:
                    return str(val)
                return float(val)
            except (ValueError, TypeError, IndexError):
                return None
        return None

    return {
        'ticker': get_val('ts_code', as_str=True),
        'end_date': get_val('end_date', as_str=True),
        'ind_type': get_val('ind_type', as_str=True),
        'security_name_abbr': get_val('security_name_abbr', as_str=True),
        'operate_income': get_val('operate_income'),
        'operate_income_yoy': get_val('operate_income_yoy'),
        'gross_profit_ratio': get_val('gross_profit_ratio'),
        'net_profit_ratio': get_val('net_profit_ratio'),
        'parent_holder_netprofit': get_val('parent_holder_netprofit'),
        'parent_holder_netprofit_yoy': get_val('parent_holder_netprofit_yoy'),
        'basic_eps': get_val('basic_eps'),
        'diluted_eps': get_val('diluted_eps'),
        'roe_avg': get_val('roe_avg'),
        'roa': get_val('roa'),
        'current_ratio': get_val('current_ratio'),
        'debt_asset_ratio': get_val('debt_asset_ratio'),
        'equity_ratio': get_val('equity_ratio'),
        'currency': get_val('currency_abbr', as_str=True),
    }


def cross_validate_us_data(daily_metrics: dict, fina_metrics: dict) -> list:
    """美股数据交叉校验。"""
    warnings = []

    pe = daily_metrics.get('pe')
    pb = daily_metrics.get('pb')
    roe = fina_metrics.get('roe_avg')

    if pe and pb and roe and roe > 0:
        expected_pe = pb / (roe / 100)
        ratio = pe / expected_pe
        if abs(ratio - 1) > 0.40:
            warnings.append(
                f"⚠️ PE/PB/ROE 不一致: PE={pe}, PB={pb}, ROE={roe}%, "
                f"预期PE≈{expected_pe:.1f}, 偏差{abs(ratio-1)*100:.0f}% "
                f"(注意：美股大量回购可能导致ROE失真)"
            )

    if pb and pb < 0:
        warnings.append(
            f"⚠️ PB为负({pb})：净资产为负，PE/PB估值可能失真，建议改用EV/EBITDA"
        )

    if roe and roe > 100:
        warnings.append(
            f"⚠️ ROE异常高({roe}%)：可能因大量回购导致净资产极低，需结合净利润绝对值分析"
        )

    # 价格一致性校验
    daily_close = daily_metrics.get('close')
    fina_name = fina_metrics.get('security_name_abbr')
    if daily_close and fina_name:
        # 简单验证：价格应为正数
        if daily_close <= 0:
            warnings.append(f"⚠️ 股价异常: {daily_close}")

    return warnings


def main():
    parser = argparse.ArgumentParser(description='美股数据获取与结构化整合')
    parser.add_argument('ticker', help='美股代码 (如 AAPL, GOOGL, NVDA)')
    parser.add_argument('--only', choices=['daily', 'fina'], default=None,
                        help='仅获取行情(daily)或财务指标(fina)，默认两者都获取')
    parser.add_argument('--start', help='行情开始日期 (YYYYMMDD)', default=None)
    parser.add_argument('--end', help='行情结束日期 (YYYYMMDD)', default=None)
    parser.add_argument('--period', help='财务指标报告期 (YYYYMMDD)', default=None)
    parser.add_argument('--output', '-o', help='输出文件路径 (默认stdout)', default=None)

    args = parser.parse_args()

    ticker = args.ticker.upper()

    # 默认日期范围：最近30天
    if not args.end:
        args.end = datetime.now().strftime('%Y%m%d')
    if not args.start:
        args.start = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

    result = {
        'stock_code': ticker,
        'market': 'US',
        'currency': 'USD',
        'daily': {},
        'fina_indicator': {},
        'warnings': [],
    }

    # 获取日线行情
    if args.only in (None, 'daily'):
        print(f"📊 获取 {ticker} 日线行情...", file=sys.stderr)
        daily_data = fetch_us_daily(ticker, args.start, args.end)

        if daily_data.get('code') == 0:
            result['daily'] = parse_daily_to_metrics(daily_data)
            if result['daily']:
                print(f"  ✓ 获取成功: {result['daily'].get('trade_date')} 收盘 {result['daily'].get('close')}", file=sys.stderr)
            else:
                print(f"  ✗ 无日线数据返回", file=sys.stderr)
        else:
            print(f"  ✗ API 返回错误: {daily_data.get('msg', '未知')}", file=sys.stderr)

    # 获取财务指标
    if args.only in (None, 'fina'):
        print(f"📊 获取 {ticker} 财务指标...", file=sys.stderr)
        fina_data = fetch_us_fina_indicator(ticker, args.period)

        if fina_data.get('code') == 0:
            result['fina_indicator'] = parse_fina_to_metrics(fina_data)
            if result['fina_indicator']:
                name = result['fina_indicator'].get('security_name_abbr', ticker)
                period = result['fina_indicator'].get('end_date', 'N/A')
                roe = result['fina_indicator'].get('roe_avg', 'N/A')
                print(f"  ✓ 获取成功: {name} {period} ROE={roe}%", file=sys.stderr)
            else:
                print(f"  ✗ 无财务指标数据返回", file=sys.stderr)
        else:
            print(f"  ✗ API 返回错误: {fina_data.get('msg', '未知')}", file=sys.stderr)

    # 交叉校验
    if result['daily'] and result['fina_indicator']:
        result['warnings'] = cross_validate_us_data(result['daily'], result['fina_indicator'])

    # 输出
    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_json)
        print(f"\n✓ 结果已保存至 {args.output}", file=sys.stderr)
    else:
        print(output_json)

    # 警告输出
    if result['warnings']:
        print("\n--- 校验警告 ---", file=sys.stderr)
        for w in result['warnings']:
            print(w, file=sys.stderr)


if __name__ == "__main__":
    main()
