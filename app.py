import streamlit as st

# 必須放在程式最前面（import 之外）
st.set_page_config(
    page_title="台股類股漲跌觀測",
    page_icon="📈",
    layout="wide",
)

st.title("📈 台股類股漲跌觀測 Dashboard")
st.write("Hello World! 🎉")

st.success("✅ Streamlit 環境建置成功！準備開始抓取台股資料。")

st.markdown("---")
st.subheader("📋 環境資訊")
st.code(
    """
Python 虛擬環境：.venv
套件管理：requirements.txt
啟動指令：streamlit run app.py
    """,
    language="bash",
)

st.info("💡 接下來可以使用 yfinance 抓取台股類股資料，並用 plotly 繪製互動式漲跌圖表。")