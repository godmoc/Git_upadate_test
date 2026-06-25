"""實測所有可能的台股類股 Ticker，找出哪些能用"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# 嘗試所有可能的台股類股 Ticker（含常見命名規則）
ALL_POSSIBLE_TICKERS = {
    "加權指數":      "^TWII",
    "電子類":        "^TELI",
    "金融類":        "^TFNI",
    "塑膠類":        "^TPLI",
    "塑化類":        "^TPII",
    "化學類":        "^TCHI",
    "航運類":        "^TTPI",
    "半導體":        "SEC.TW",
    "非金融類":      "^TIWI",
    "其他類":        "^TOTI",
    # 以下為常見 TAIEX 次指數代碼（可能可用）
    "水泥窯製":      "^TCI",     # cement
    "食品類":        "^TFO",     # food
    "紡織纖維":      "^TFB",     # fiber/textile
    "電機機械":      "^TEM",     # electric machinery
    "電器電纜":      "^TEE",     # electric
    "玻璃陶瓷":      "^TGC",     # glass ceramic
    "造紙類":        "^TPA",     # paper
    "鋼鐵類":        "^TST",     # steel
    "橡膠類":        "^TRB",     # rubber
    "汽車類":        "^TAU",     # auto
    "建材營造":      "^TCB",     # construction/building
    "觀光類":        "^TTO",     # tourism
    "金融保險":      "^TFI",     # finance insurance
    "百貨貿易":      "^TWH",     # wholesale
    "油電燃氣":      "^TOG",     # oil gas
    "生技醫療":      "^TBI",     # biotech
    "電腦設備":      "^TCI2",    # computer
    "光電類":        "^TOP",     # optoelectronics
    "通信網路":      "^TCN",     # communication
    "電子零組件":    "^TCO",     # components
    "電子通路":      "^TEC",     # channel
    "資訊服務":      "^TIS",     # info service
    "其他電子":      "^TOE",     # other electronics
    "文化創意":      "^TCU",     # culture
    "農業科技":      "^TAG",     # agri
    "環境衛生":      "^TEH",     # environment
    "居家生活":      "^TLI",     # living
    "運動休閒":      "^TSP",     # sport
    "居家用品":      "^THG",     # home goods
    "美妝醫療":      "^TCM",     # cosmetics medical
}

end = datetime.now()
start = end - timedelta(days=30)
tickers = list(ALL_POSSIBLE_TICKERS.values())

print(f"測試 {len(tickers)} 個 Ticker...")
data = yf.download(tickers, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False, threads=True)

if isinstance(data.columns, pd.MultiIndex):
    close_df = data["Close"]
else:
    close_df = data[["Close"]].rename(columns={"Close": tickers[0]})

# 找出哪些 Ticker 有資料（不全 NaN）
available = {}
unavailable = {}
reverse_map = {v: k for k, v in ALL_POSSIBLE_TICKERS.items()}

for ticker in tickers:
    if ticker in close_df.columns:
        if close_df[ticker].notna().sum() >= 5:   # 至少有 5 個交易日資料
            available[reverse_map[ticker]] = ticker
        else:
            unavailable[reverse_map[ticker]] = ticker
    else:
        unavailable[reverse_map[ticker]] = ticker

print(f"\n可用 ({len(available)}/{len(tickers)}):")
for name, ticker in available.items():
    print(f"  [OK]   {name:8s}  {ticker}")

print(f"\n不可用 ({len(unavailable)}/{len(tickers)}):")
for name, ticker in unavailable.items():
    print(f"  [NO]   {name:8s}  {ticker}")

# 輸出可用清單為 Python dict 格式，方便複製
print("\n\n=== 可用 Ticker 字典 (複製貼到 app.py) ===")
print("SECTOR_INDICES = {")
for name, ticker in available.items():
    print(f'    "{name}": "{ticker}",')
print("}")