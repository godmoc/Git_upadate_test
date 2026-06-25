"""獨立測試 Plotly 圖表是否能正確產生"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
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

print("抓取資料中...")
data = yf.download(tickers, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False, threads=True)

if isinstance(data.columns, pd.MultiIndex):
    close_df = data["Close"].dropna(axis=1, how="all").tail(20)
else:
    close_df = data[["Close"]].rename(columns={"Close": tickers[0]}).tail(20)

first_close = close_df.iloc[0]
last_close = close_df.iloc[-1]
cumulative_pct = ((last_close - first_close) / first_close) * 100

rename_map = {v: k for k, v in SECTOR_INDICES.items()}
pct_df = pd.DataFrame({
    "累積漲跌幅 (%)": cumulative_pct.values,
}, index=[rename_map.get(c, c) for c in cumulative_pct.index]).sort_values("累積漲跌幅 (%)", ascending=True)

print("\npct_df:")
print(pct_df)
print(f"\n類股數: {len(pct_df)}")

# 測試 Plotly 圖表
pct_chart_df = pct_df
bar_colors = ["#16a34a" if v > 0 else "#dc2626" if v < 0 else "#9ca3af"
              for v in pct_chart_df["累積漲跌幅 (%)"].values]
text_labels = [f"{v:+.2f}%" for v in pct_chart_df["累積漲跌幅 (%)"].values]

fig = go.Figure()
fig.add_trace(go.Bar(
    x=pct_chart_df["累積漲跌幅 (%)"].values,
    y=pct_chart_df.index.tolist(),
    orientation="h",
    marker=dict(color=bar_colors, line=dict(color="white", width=1)),
    text=text_labels,
    textposition="outside",
    textfont=dict(size=14, color="black", family="Arial Black"),
))

fig.update_layout(
    title="測試圖表",
    xaxis=dict(title="累積漲跌幅 (%)", zeroline=True, zerolinecolor="black", zerolinewidth=2),
    yaxis=dict(title=""),
    plot_bgcolor="white",
    height=max(350, len(pct_chart_df) * 45),
    showlegend=False,
)

# 嘗試輸出 HTML 確認圖表能正常產生
try:
    html = fig.to_html()
    print(f"\nPlotly 圖表 HTML 產生成功，長度: {len(html)} 字元")
    # 寫入檔案供瀏覽器檢視
    with open("test_chart.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("已寫入 test_chart.html，可直接用瀏覽器開啟檢視")
except Exception as e:
    print(f"Plotly 圖表產生失敗: {e}")
    raise

print("\n所有測試通過!")