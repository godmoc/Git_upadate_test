# 📈 台股類股漲跌觀測 Dashboard

使用 **Streamlit** + **yfinance** 開發的台股類股漲跌即時觀測儀表板。

---

## 🚀 快速開始

### 1. 建立 Python 虛擬環境

在 VS Code 終端機（Terminal → New Terminal）執行：

```powershell
python -m venv .venv
```

### 2. 啟用虛擬環境

```powershell
.\.venv\Scripts\Activate.ps1
```

> ⚠️ 若出現「無法載入檔案」錯誤，請先以系統管理員身分執行 PowerShell：
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

啟用成功後，提示字元前方會出現 `(.venv)`。

### 3. 安裝套件

```powershell
pip install -r requirements.txt
```

或直接安裝：

```powershell
pip install streamlit yfinance pandas plotly
```

---

## ▶️ 啟動 Dashboard

```powershell
streamlit run app.py
```

瀏覽器會自動開啟 `http://localhost:8501`。

> 🛑 停止服務：在終端機按 `Ctrl + C`。

---

## 📦 套件說明

| 套件 | 用途 |
|---|---|
| `streamlit` | Web Dashboard 框架 |
| `yfinance` | 從 Yahoo Finance 抓取台股資料 |
| `pandas` | 資料處理與分析 |
| `plotly` | 互動式圖表 |

---

## 📁 專案結構

```
Git_upadate_test/
├── .venv/              # Python 虛擬環境（不加入版控）
├── app.py              # Streamlit 主程式
├── requirements.txt    # 套件相依清單
└── README.md           # 專案說明
```

---

## 🎯 下一步開發

- [ ] 使用 `yfinance` 抓取台股上市/上櫃類股清單
- [ ] 計算當日漲跌幅與成交量
- [ ] 用 `plotly` 繪製類股漲跌排行榜
- [ ] 加入定時自動刷新功能
- [ ] 部署到 Streamlit Cloud