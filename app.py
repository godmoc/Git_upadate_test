import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# 必須放在程式最前面（import 之外）
st.set_page_config(
    page_title="台股類股漲跌觀測",
    page_icon="📈",
    layout="wide",
)

# ============================================================
# 台股類股指數對照表（Yahoo Finance 官方支援的 Ticker）
# ============================================================
# ✅ 狀態：已驗證可抓取 Yahoo Finance 即時資料的 Ticker（2026/06 驗證）
# ⚠️ 以下 Ticker 在 Yahoo Finance 已下架/無資料，已從清單中移除：
#     ^TELI (電子類), ^TTPI (航運類), ^TPII (塑化類), ^TCHI (化學類),
#     ^TOTI (其他類), SEC.TW (半導體)
SECTOR_INDICES = {
    "加權指數":   "^TWII",
    "金融類":     "^TFNI",
    "塑膠類":     "^TPLI",
    "非金融類":   "^TIWI",
}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_sector_close(days: int, tickers: list[str]) -> pd.DataFrame:
    """
    抓取多個台股類股指數最近 N 天的收盤價（Close）。

    參數：
        days    : 要抓取的天數（會自動往回抓，避開假日空窗）
        tickers : Ticker 代碼 list，例如 ["^TWII", "^TELI", "^TFNI"]

    回傳：
        DataFrame，索引為日期（Date），欄位為各 Ticker 的收盤價
        抓不到的欄位會自動 drop 掉
    """
    end = datetime.now()
    # 多抓一點緩衝，避開週末假日導致天數不足
    start = end - timedelta(days=days + 10)

    # 用 yf.download 一次抓多檔，效率比逐檔呼叫 yf.Ticker 更好
    data = yf.download(
        tickers=tickers,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        interval="1d",
        auto_adjust=False,   # 保留原始 Close，不做股息調整
        progress=False,
        threads=True,
    )

    # yf.download 單檔 vs 多檔回傳結構不同，要分開處理
    if isinstance(data.columns, pd.MultiIndex):
        close_df = data["Close"]
    else:
        close_df = data[["Close"]].rename(columns={"Close": tickers[0]})

    # 只保留實際抓到的欄位（避免全部變 NaN）
    close_df = close_df.dropna(axis=1, how="all")

    # 只取最後 N 個交易日
    close_df = close_df.tail(days)

    return close_df


# ============================================================
# Streamlit UI
# ============================================================
st.title("📈 台股類股漲跌觀測 Dashboard")
st.caption("資料來源：Yahoo Finance ｜ 使用 yfinance 套件")

st.markdown("---")

# --- 側邊欄控制項 ---
st.sidebar.header("⚙️ 設定參數")
st.sidebar.caption("💡 每天請自行勾選想觀察的類股（不預設選項）")

# ★ 重點：不預設任何選項，每天由使用者自行選擇
selected_tickers = st.sidebar.multiselect(
    "選擇要觀察的類股（必選）",
    options=list(SECTOR_INDICES.keys()),
    default=[],
    format_func=lambda x: f"{x} ({SECTOR_INDICES[x]})",
)

days = st.sidebar.slider(
    "抓取天數（交易日）",
    min_value=5,
    max_value=120,
    value=20,
    step=5,
)

st.sidebar.markdown("### 📋 可用類股總表")
st.sidebar.dataframe(
    pd.DataFrame(
        [(name, ticker) for name, ticker in SECTOR_INDICES.items()],
        columns=["類股名稱", "Yahoo Ticker"],
    ),
    hide_index=True,
    use_container_width=True,
)

# --- 主要內容區 ---
if not selected_tickers:
    st.info("👈 請從左側「選擇要觀察的類股」中勾選今天想看的類股，並設定天數。")
    st.stop()

# 把中文名稱對應到 Ticker
ticker_list = [SECTOR_INDICES[name] for name in selected_tickers]

st.subheader(f"📊 最近 {days} 個交易日收盤價")
st.caption(f"已選擇 {len(selected_tickers)} 個類股：{'、'.join(selected_tickers)}")

with st.spinner("正在從 Yahoo Finance 抓取資料..."):
    try:
        close_df = fetch_sector_close(days, ticker_list)
    except Exception as e:
        st.error(f"❌ 抓取失敗：{e}")
        st.stop()

if close_df.empty:
    st.error("❌ 沒有抓到任何資料，請檢查網路或 Ticker 是否正確")
    st.stop()

# 把 Ticker 換回中文欄位名（比較好讀）
rename_map = {SECTOR_INDICES[name]: name for name in selected_tickers}
close_df_display = close_df.rename(columns=rename_map)

# 格式化日期欄位（只顯示日期，不顯示時間）
close_df_display.index = close_df_display.index.date

st.success(f"✅ 成功抓取 {len(close_df_display)} 個交易日、{len(close_df_display.columns)} 個類股")

# === 重點：把抓到的原始資料表格呈現出來 ===
st.dataframe(
    close_df_display,
    use_container_width=True,
    height=400,
)

# 額外顯示：每個類股最新收盤價（讓使用者快速確認資料是新的）
st.markdown("---")
st.subheader("🔍 最新一日收盤價（資料時效檢查）")
latest_row = close_df_display.iloc[-1]
st.dataframe(
    latest_row.to_frame(name=str(close_df_display.index[-1])).T,
    use_container_width=True,
)

# ============================================================
# 📊 累積漲跌幅計算 + 漲跌排行榜
# ============================================================
st.markdown("---")
st.subheader(f"🏆 過去 {len(close_df_display)} 個交易日累積漲跌幅排行榜")

# 公式：(最後一天收盤價 - 第一天收盤價) / 第一天收盤價 * 100
first_close = close_df.iloc[0]                # 第一天（最早一天）
last_close = close_df.iloc[-1]                # 最後一天（最近一天）
cumulative_pct = ((last_close - first_close) / first_close) * 100

# 整理成 DataFrame，方便排序
pct_df = pd.DataFrame({
    "類股名稱": [rename_map.get(c, c) for c in cumulative_pct.index],
    "起始收盤價": first_close.values,
    "最新收盤價": last_close.values,
    "累積漲跌幅 (%)": cumulative_pct.values,
}).set_index("類股名稱").sort_values("累積漲跌幅 (%)", ascending=False)

# 篩選漲幅前 5 大 / 跌幅前 5 大
top5_gain = pct_df.head(5)
top5_loss = pct_df.tail(5).iloc[::-1]   # 跌幅最深排第一

# === 左右並排顯示（st.columns(2)）===
col_gain, col_loss = st.columns(2)

with col_gain:
    st.markdown("### 🚀 漲幅前 5 大")
    if top5_gain.empty:
        st.info("無資料")
    else:
        for rank, (name, row) in enumerate(top5_gain.iterrows(), start=1):
            pct = row["累積漲跌幅 (%)"]
            emoji = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else "  "))
            color = "🟢" if pct > 0 else "⚪"
            sign = "+" if pct > 0 else ""
            st.markdown(
                f"**{emoji} {rank}. {name}** &nbsp;&nbsp; "
                f"<span style='color:#16a34a;font-size:1.3em;font-weight:bold'>"
                f"{color} {sign}{pct:.2f}%</span>",
                unsafe_allow_html=True,
            )

with col_loss:
    st.markdown("### 🔻 跌幅前 5 大")
    if top5_loss.empty:
        st.info("無資料")
    else:
        for rank, (name, row) in enumerate(top5_loss.iterrows(), start=1):
            pct = row["累積漲跌幅 (%)"]
            emoji = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else "  "))
            color = "🔴" if pct < 0 else "⚪"
            st.markdown(
                f"**{emoji} {rank}. {name}** &nbsp;&nbsp; "
                f"<span style='color:#dc2626;font-size:1.3em;font-weight:bold'>"
                f"{color} {pct:.2f}%</span>",
                unsafe_allow_html=True,
            )

# ============================================================
# 📈 Plotly 互動式長條圖（左右並排）
# ============================================================
st.markdown("---")
st.subheader("📈 累積漲跌幅視覺化（Plotly 互動式長條圖）")

# 為長條圖准備資料（從小到大排，視覺效果較佳）
pct_chart_df = pct_df.sort_values("累積漲跌幅 (%)", ascending=True)

# 設定顏色：漲為綠、跌為紅
bar_colors = ["#16a34a" if v > 0 else "#dc2626" if v < 0 else "#9ca3af"
              for v in pct_chart_df["累積漲跌幅 (%)"].values]

# 文字標記：帶正負號的百分比
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
    hovertemplate="<b>%{y}</b><br>漲跌幅: %{x:+.2f}%<extra></extra>",
))

fig.update_layout(
    title=dict(
        text=f"過去 {len(close_df_display)} 個交易日 累積漲跌幅",
        font=dict(size=18),
    ),
    xaxis=dict(
        title="累積漲跌幅 (%)",
        zeroline=True,
        zerolinecolor="black",
        zerolinewidth=2,
        gridcolor="lightgray",
    ),
    yaxis=dict(title=""),
    plot_bgcolor="white",
    height=max(350, len(pct_chart_df) * 45),
    margin=dict(l=80, r=80, t=60, b=60),
    showlegend=False,
)

st.plotly_chart(fig, use_container_width=True)

# 完整排行榜表格（純表格呈現，不加色避免 matplotlib 依賴）
with st.expander("📋 查看完整排行榜數據（純表格）"):
    display_df = pct_df.copy()
    display_df["累積漲跌幅 (%)"] = display_df["累積漲跌幅 (%)"].apply(lambda x: f"{x:+.2f}%")
    display_df["起始收盤價"] = display_df["起始收盤價"].apply(lambda x: f"{x:,.2f}")
    display_df["最新收盤價"] = display_df["最新收盤價"].apply(lambda x: f"{x:,.2f}")
    st.dataframe(display_df, use_container_width=True)

# ============================================================
# 📉 歸一化折線圖（plotly.express.line）
# ============================================================
st.markdown("---")
st.subheader("📉 領漲 / 領跌類股走勢比較（歸一化折線圖）")

# 📚 什麼是歸一化？
# 為公平比較不同基期的類股（例如大盤 4 萬點、塑膠 200 點），
# 把每天的數值除以第一天的數值 × 100，讓第一天 = 100。
# 這樣所有曲線都從 100 起跑，後續數值 = 100 + 漲跌幅%。
# 公式：normalized = (df / df.iloc[0]) * 100
with st.expander("💡 什麼是「歸一化」？點此展開說明"):
    st.markdown(
        """
        **問題**：加權指數約 4 萬點、塑膠類約 200 點，原始數字無法直接比較漲跌幅走勢。

        **解法 — 歸一化（Normalization）**：
        ```python
        normalized = (df / df.iloc[0]) * 100
        ```
        把「每一天的數值」除以「第一天的數值」再乘以 100，這樣：
        - 第一天 = **100**（所有類股都從 100 出發）
        - 第二天 = 100 × (1 + 當日漲跌幅%) 
        - 依此類推...
        - 最終一天 = 100 + 累積漲跌幅%

        **範例**：塑膠類 20 天漲 43.25% → 歸一化後從 100 變 143.25

        歸一化後，所有類股都能在同一張圖上**公平比較走勢強弱**。
        """
    )

# 🟦 使用者切換按鈕
view_mode = st.radio(
    "選擇要看哪一組走勢：",
    options=["🚀 我想看領漲類股走勢", "🔻 我想看領跌類股走勢"],
    horizontal=True,
)

# 根據選擇決定要畫哪個子集
if view_mode.startswith("🚀"):
    selected_subset = top5_gain
    chart_title = "🚀 領漲前 5 名 走勢比較（歸一化）"
    empty_msg = "無漲幅資料可顯示"
else:
    selected_subset = top5_loss
    chart_title = "🔻 領跌前 5 名 走勢比較（歸一化）"
    empty_msg = "無跌幅資料可顯示"

if selected_subset.empty:
    st.info(empty_msg)
else:
    # 🎯 核心：歸一化計算
    selected_tickers_chinese = selected_subset.index.tolist()
    # 從原始 close_df 中拿出這些 Ticker 的資料，再 rename 成中文
    selected_close_df = close_df[[
        SECTOR_INDICES[name] for name in selected_tickers_chinese
    ]].rename(columns=rename_map)

    # ⭐ 歸一化公式：把每天收盤價 / 第一天收盤價 × 100
    normalized_df = (selected_close_df / selected_close_df.iloc[0]) * 100

    # 轉換成 plotly.express 適用的 long format
    # plotly.express.line 需要 index 為日期、欄位為「類股」、「數值」
    long_df = normalized_df.reset_index().melt(
        id_vars=normalized_df.index.name or "Date",
        var_name="類股",
        value_name="歸一化數值 (= 100 + 漲跌幅%)",
    )
    long_df.columns = ["日期", "類股", "歸一化數值 (= 100 + 漲跌幅%)"]

    # 畫 plotly.express 折線圖
    fig_line = px.line(
        long_df,
        x="日期",
        y="歸一化數值 (= 100 + 漲跌幅%)",
        color="類股",
        markers=True,
        title=chart_title,
    )

    # 加上一條 y=100 的參考線（表示起點）
    fig_line.add_hline(
        y=100,
        line_dash="dash",
        line_color="gray",
        annotation_text="起點 100",
        annotation_position="right",
    )

    fig_line.update_layout(
        hovermode="x unified",
        plot_bgcolor="white",
        xaxis=dict(title="日期", gridcolor="lightgray"),
        yaxis=dict(
            title="歸一化數值（第一天 = 100）",
            gridcolor="lightgray",
            zeroline=False,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
    )

    fig_line.update_traces(line=dict(width=2.5), marker=dict(size=6))

    st.plotly_chart(fig_line, use_container_width=True)

    # 提示表格：顯示各類股起點與終點
    st.caption("📋 走勢摘要：")
    summary_df = pd.DataFrame({
        "類股": selected_subset.index,
        "起點 (歸一化)": [100.00] * len(selected_subset),
        "終點 (歸一化)": normalized_df.iloc[-1].values.round(2),
        "累計漲跌 (%)": selected_subset["累積漲跌幅 (%)"].values.round(2),
    })
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

# 簡易除錯資訊
with st.expander("🔧 除錯資訊（Debug Info）"):
    st.write("**資料日期範圍：**", f"{close_df_display.index[0]} ~ {close_df_display.index[-1]}")
    st.write("**欄位資料型態：**", str(close_df_display.dtypes.to_dict()))
    st.write("**缺失值統計：**")
    st.dataframe(close_df_display.isna().sum().to_frame("NaN 數量"), use_container_width=True)