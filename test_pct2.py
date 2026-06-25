"""驗證漲跌幅計算邏輯（ASCII 版本，避免 cp950 編碼問題）"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys
sys.stdout.reconfigure(encoding='utf-8')  # 強制 UTF-8 輸出

SECTOR_INDICES = {
    "加權指數":   "^TWII",
    "電子類":     "^TELI",
    "金融類":     "^TFNI",
    "塑膠類":     "^TPLI",
    "塑化類":     "^TPII",
    "化學類":     "^TCHI",
    "航運類":     "^TTPI",
    "半導體":     "SEC.TW",
    "非金融類":   "^TIWI",
    "其他類":     "^TOTI",
}

end = datetime.now()
start = end - timedelta(days=30)
tickers = list(SECTOR_INDICES.values())

print(f"抓取 {len(tickers)} 個類股資料...")
data = yf.download(tickers, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False, threads=True)

if isinstance(data.columns, pd.MultiIndex):
    close_df = data["Close"].dropna(axis=1, how="all").tail(20)
else:
    close_df = data[["Close"]].rename(columns={"Close": tickers[0]}).tail(20)

valid_tickers = list(close_df.columns)
print(f"\n實際抓到 {len(close_df)} 個交易日，{len(valid_tickers)} 個有效 Ticker: {valid_tickers}\n")

first_close = close_df.iloc[0]
last_close = close_df.iloc[-1]
cumulative_pct = ((last_close - first_close) / first_close) * 100

rename_map = {v: k for k, v in SECTOR_INDICES.items()}
pct_df = pd.DataFrame({
    "類股": [rename_map.get(c, c) for c in cumulative_pct.index],
    "起始": first_close.values,
    "最新": last_close.values,
    "累積漲跌幅(%)": cumulative_pct.values,
}).sort_values("累積漲跌幅(%)", ascending=False).reset_index(drop=True)

print("=" * 70)
print("完整排行榜（依漲跌幅排序）")
print("=" * 70)
print(pct_df.to_string(index=False))

print("\n" + "=" * 70)
print("Top 5 Gainers")
print("=" * 70)
for rank, row in pct_df.head(5).iterrows():
    pct = row["累積漲跌幅(%)"]
    sign = "+" if pct > 0 else ""
    print(f"  {rank+1}. {row['類股']:6s}  {sign}{pct:.2f}%")

print("\n" + "=" * 70)
print("Top 5 Losers")
print("=" * 70)
for rank, row in pct_df.tail(5).iloc[::-1].iterrows():
    pct = row["累積漲跌幅(%)"]
    print(f"  {rank+1}. {row['類股']:6s}  {pct:.2f}%")

print("\n驗證完成")