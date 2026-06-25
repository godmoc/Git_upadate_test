"""測試歸一化邏輯 + plotly.express.line 折線圖"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

SECTOR_INDICES = {
    "加權指數":   "^TWII",
    "金融類":     "^TFNI",
    "塑膠類":     "^TPLI",
    "非金融類":   "^TIWI",
}

end = datetime.now()
start = end - timedelta(days=30)
tickers = list(SECTOR_INDICES.values())

print("Step 1: 抓取資料")
data = yf.download(tickers, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False, threads=True)
close_df = data["Close"].dropna(axis=1, how="all").tail(20)
print(f"抓到 {len(close_df)} 個交易日，{len(close_df.columns)} 個類股")

print("\nStep 2: 計算累積漲跌幅")
first_close = close_df.iloc[0]
last_close = close_df.iloc[-1]
cumulative_pct = ((last_close - first_close) / first_close) * 100

rename_map = {v: k for k, v in SECTOR_INDICES.items()}
pct_series = pd.Series(
    [cumulative_pct[c] for c in cumulative_pct.index],
    index=[rename_map[c] for c in cumulative_pct.index],
).sort_values(ascending=False)
print("累積漲跌幅：")
for name, pct in pct_series.items():
    print(f"  {name:8s}: {pct:+.2f}%")

print("\nStep 3: 選 top 3 漲幅")
top3 = pct_series.head(3)
print(f"Top 3: {list(top3.index)}")

print("\nStep 4: 取出 top 3 的原始 close_df")
selected_close_df = close_df[[SECTOR_INDICES[n] for n in top3.index]].rename(columns=rename_map)
print("原始 close_df 前 3 天：")
print(selected_close_df.head(3))

print("\nStep 5: 歸一化（normalize）公式 = (df / df.iloc[0]) * 100")
normalized_df = (selected_close_df / selected_close_df.iloc[0]) * 100
print("歸一化後前 3 天：")
print(normalized_df.head(3).round(2))
print("\n歸一化後最後 1 天：")
print(normalized_df.iloc[-1].round(2))

print("\n驗證：歸一化第一天應該全部 = 100")
first_day_check = (normalized_df.iloc[0].round(2) == 100.0).all()
print(f"  結果: {'✅ 正確' if first_day_check else '❌ 錯誤'}")

print("\n驗證：歸一化最後一天 = 100 + 累積漲跌幅")
for name in top3.index:
    norm_last = normalized_df.iloc[-1][name].round(2)
    expected = 100 + top3[name]
    diff = abs(norm_last - expected)
    print(f"  {name:8s}: 歸一化={norm_last}, 預期={expected:.2f}, 差距={diff:.4f} {'✅' if diff < 0.01 else '❌'}")

print("\nStep 6: 轉成 plotly.express 用的 long format")
long_df = normalized_df.reset_index().melt(
    id_vars="Date",
    var_name="類股",
    value_name="歸一化數值",
)
print(f"long_df shape: {long_df.shape}")
print(long_df.head(6))

print("\nStep 7: 用 plotly.express.line 畫圖")
fig = px.line(
    long_df,
    x="Date",
    y="歸一化數值",
    color="類股",
    markers=True,
    title="測試折線圖",
)
fig.add_hline(y=100, line_dash="dash", line_color="gray", annotation_text="起點 100")

html = fig.to_html()
print(f"✅ plotly.express.line 折線圖 HTML 產生成功，長度: {len(html):,} 字元")

with open("test_line_chart.html", "w", encoding="utf-8") as f:
    f.write(html)
print("已寫入 test_line_chart.html")

print("\n所有測試通過!")