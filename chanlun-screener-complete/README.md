# 🔮 纏論掃描系統 (Chanlun Screener)

基於 **Mark Minervini VCP 方法論** × **李彪纏論理論** 的美股自動化選股系統。

實時掃描美股市場，識別符合纏論買賣點的股票，提供進場點位、支撐位、獲利目標的完整分析。

---

## ✨ 核心功能

### 🎯 纏論分析
- ✅ **分型識別** - 頂分型 / 底分型自動檢測
- ✅ **筆的構建** - 連接分型形成基礎走勢單位
- ✅ **中樞辨識** - 識別多空雙方交戰區域
- ✅ **背馳判斷** - 使用 MACD 檢測動能衰竭
- ✅ **買賣點識別** - 一買 / 二買 / 三買訊號

### 📊 即時掃描
- ✅ **動態候選** - 從 S&P 500 + Nasdaq 100 + 高成交量股票篩選
- ✅ **流動性過濾** - 排除低成交量股票
- ✅ **並發掃描** - 8 個 workers 並行分析
- ✅ **即時進度** - 實時顯示掃描進度

### 💹 進出場邏輯
- ✅ **動態進場點** - 根據訊號類型自適應調整
- ✅ **支撐阻力** - 基於中樞範圍 + ATR 計算
- ✅ **獲利目標** - 10% / 20% 分層目標點位
- ✅ **風險量化** - ATR 倍數動態調整

### 📈 可視化
- ✅ **K 線圖表** - Plotly 互動式圖表
- ✅ **技術指標** - MACD / KDJ / 布林通道
- ✅ **中樞標記** - 清晰的中樞邊界視覺化
- ✅ **買賣點標註** - 進場 / 支撐 / 目標位視覺化

---

## 🚀 快速開始

### 方案 A：Streamlit MVP（最快）

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
# 訪問 http://localhost:8501
```

**優點：** 5 分鐘快速驗證，無需部署  
**缺點：** 無批量掃描功能

---

### 方案 B：本地 Docker Compose（推薦開發）

```bash
docker-compose up --build
# 後端: http://localhost:8000
# 前端: http://localhost:5173
# API 文檔: http://localhost:8000/docs
```

**特性：**
- 完整的後端 + 前端
- 即時掃描 + 互動式清單
- 自動化定時任務

---

### 方案 C：Render 雲端部署（生產環境）

見 [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 📁 項目結構

```
chanlun-screener/
│
├── backend/                          # FastAPI 後端
│   ├── main.py                       # API 主應用 + 掃描任務
│   ├── fractal_analyzer.py           # 纏論核心引擎
│   ├── screener.py                   # 動態掃描器
│   ├── requirements.txt              # Python 依賴
│   ├── Dockerfile                    # Docker 打包
│   └── .env.example                  # 環境變數範本
│
├── frontend/                         # React + Vite 前端
│   ├── src/
│   │   ├── App.jsx                   # 主應用組件
│   │   ├── main.jsx                  # 入口
│   │   ├── index.css                 # 全局樣式
│   │   ├── api.js                    # API 服務層
│   │   └── components/
│   │       ├── StockList.jsx         # 掃描結果清單
│   │       ├── Chart.jsx             # K 線圖表
│   │       └── AnalysisPanel.jsx     # 詳細分析面板
│   ├── package.json                  # npm 依賴
│   ├── vite.config.js                # Vite 配置
│   ├── Dockerfile                    # Docker 打包
│   └── index.html
│
├── streamlit_app/                    # Streamlit 快速原型
│   ├── app.py                        # Streamlit 應用
│   ├── fractal_analyzer.py           # 纏論引擎 (同步版)
│   ├── requirements.txt
│   └── .streamlit/config.toml        # Streamlit 配置
│
├── docker-compose.yml                # Docker Compose 編排
├── .gitignore                        # Git 忽略配置
├── README.md                         # 本文件
├── DEPLOYMENT.md                     # 部署指南
└── LICENSE                           # MIT License
```

---

## 🛠️ 技術棧

| 層級 | 技術 |
|------|------|
| **前端** | React 18 + Vite + Ant Design + Plotly |
| **後端** | FastAPI + Python 3.11 |
| **數據** | yfinance + Pandas |
| **技術指標** | TA-Lib + 自定義纏論算法 |
| **圖表** | Plotly (互動式) |
| **部署** | Docker + Docker Compose |
| **原型** | Streamlit |
| **調度** | APScheduler (定時掃描) |

---

## 📊 訊號解讀

### 🔴 一買 (買點1)
- **條件**: 下跌趨勢中出現背馳，動能衰竭
- **特徵**: 創新低但 MACD 不創新低
- **風險**: 最高，屬左側交易
- **收益**: 最高
- **適合**: 激進交易者

### 🟠 二買 (買點2)
- **條件**: 一買後回踩未創新低
- **特徵**: 確認買點有效性
- **風險**: 中等
- **收益**: 中等偏高
- **適合**: 平衡型交易者

### 🟢 三買 (買點3)
- **條件**: 離開中樞向上，回調未進中樞
- **特徵**: 新趨勢確立，爆發確認
- **風險**: 最低
- **收益**: 中等偏低
- **適合**: 保守型交易者

---

## 🎯 進出場邏輯

### 進場點 (Entry)
```
一買: 中樞下界 - 0.3 × ATR
二買: 中樞下界
三買: 中樞上界 + 0.2 × ATR
```

### 支撐位 (Support)
```
Support = 進場點 - 1.0 × ATR
```

### 獲利目標 (Targets)
```
10% 目標 = 進場點 + 1.5 × ATR
20% 目標 = 進場點 + 3.0 × ATR
```

---

## 🔄 掃描計劃

| 時間 | 頻率 | 說明 |
|------|------|------|
| **工作日 16:30 UTC** | 每日1次 | 美股收盤後掃描 (台北翌日 00:30) |
| **每 4 小時** | 實時 | 檢查新訊號更新 |
| **手動觸發** | 隨時 | 點擊按鈕即時掃描 |

**修改掃描時間** → 編輯 `backend/main.py` 中的：
```python
scheduler.add_job(run_full_scan, 'cron', day_of_week='mon-fri', hour=20, minute=30)
```

---

## 📌 API 端點

### 掃描相關
```
GET  /api/scan/status              # 掃描狀態 & 進度
POST /api/scan/run                 # 手動觸發掃描
GET  /api/scan/results             # 取得掃描結果 (支持篩選)
GET  /api/scan/candidates          # 候選股票清單
GET  /api/scan/summary             # 掃描統計摘要
```

### 分析相關
```
GET  /api/analyze/{ticker}         # 分析單支股票
GET  /api/chart/{ticker}           # 取得 K 線圖表
```

### 系統
```
GET  /health                       # 健康檢查
GET  /api/stats                    # 系統統計
```

### 完整 API 文檔
訪問: `http://localhost:8000/docs` (自動 Swagger UI)

---

## 🚀 部署到 Render

### 快速部署 (3 分鐘)

1. **Fork 此倉庫** 到你的 GitHub
2. **連接 Render**
   - 登入 [render.com](https://render.com)
   - 新建 Web Service → 選擇此倉庫
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **前端部署**
   - 新建 Static Site → 選擇此倉庫
   - Build Command: `cd frontend && npm install && npm run build`
   - Publish Directory: `frontend/dist`

4. **配置環境變數**
   ```
   VITE_API_URL=https://your-api.onrender.com
   ```

詳細見 [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 📖 使用示例

### Streamlit UI
```bash
streamlit run streamlit_app/app.py
# 1. 輸入股票代號 (例: AAPL)
# 2. 選擇回測期間
# 3. 點擊「分析」查看結果
```

### React UI
```bash
docker-compose up
# 訪問 http://localhost:5173
# 1. 點擊「立即掃描」或等待自動掃描
# 2. 在清單中選擇股票
# 3. 查看圖表 & 詳細分析
```

### API 調用
```bash
# 取得掃描結果
curl http://localhost:8000/api/scan/results?signal_type=一買&limit=10

# 分析單支股票
curl http://localhost:8000/api/analyze/AAPL

# 取得圖表 JSON
curl http://localhost:8000/api/chart/AAPL
```

---

## ⚙️ 配置調整

### 調整掃描範圍
編輯 `backend/screener.py`:
```python
screener = DynamicChanLunScreener(
    min_price=5.0,              # 最低股價
    min_volume=500000           # 最低日均成交量
)
```

### 調整買賣點靈敏度
編輯 `backend/fractal_analyzer.py` 中的 `check_divergence()` 和 `identify_signals()` 方法

### 調整 ATR 倍數
編輯 `backend/fractal_analyzer.py` 的 `calculate_targets()` 方法:
```python
target_10pct = entry_price + current_atr * 1.5  # 調整此處
target_20pct = entry_price + current_atr * 3.0
```

---

## 📊 數據更新頻率

| 數據源 | 頻率 | 延遲 |
|--------|------|------|
| yfinance 日線 | 每日 | T+1 日 |
| 實時掃描結果 | 自定義 | 即時 |
| 技術指標 | 跟隨 K 線 | 同步 |

---

## ⚠️ 免責聲明

- 本系統為教育用途，不構成投資建議
- 過往績效不代表未來表現
- 使用前請自行評估風險
- 建議模擬賬戶紙上交易驗證訊號

---

## 🤝 貢獻

歡迎提交 Issues & Pull Requests

常見改進方向：
- [ ] 港股 / A 股支持
- [ ] 機器學習訊號排序
- [ ] 回測歷史勝率統計
- [ ] 移動端 App
- [ ] WebSocket 實時推送
- [ ] 多時間框架分析

---

## 📜 License

MIT License - 自由使用、修改、分發

---

## 📞 聯繫方式

- **GitHub Issues** - 技術問題
- **Discussions** - 想法交流

---

## 🙏 致謝

- Mark Minervini - VCP 方法論
- 李彪 (纏中說禪) - 纏論理論
- yfinance - 數據源
- FastAPI & React 社區

---

## 📈 Roadmap

- [ ] v1.0 - MVP 完成 (當前)
- [ ] v1.1 - 港股支持
- [ ] v2.0 - ML 訊號排序
- [ ] v2.1 - 移動端 App
- [ ] v3.0 - 完整回測系統

---

**最後更新**: 2024-10-07  
**維護者**: @chanlun-screener
