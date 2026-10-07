# 🚀 部署指南

完整的纏論掃描系統部署說明。

---

## 📋 目錄

1. [本地開發環境](#本地開發環境)
2. [Docker 部署](#docker-部署)
3. [Render 雲端部署](#render-雲端部署)
4. [環境變數](#環境變數)
5. [常見問題](#常見問題)

---

## 🖥️ 本地開發環境

### 前置要求
- Python 3.11+
- Node.js 18+
- npm / yarn
- (可選) Docker & Docker Compose

### 安裝步驟

#### 方案 A: 分開運行後端和前端

**1. 後端設置**
```bash
cd backend
python -m venv venv

# 激活虛擬環境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 運行服務
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**2. 前端設置** (新開終端)
```bash
cd frontend

# 安裝依賴
npm install

# 開發模式運行
npm run dev
```

**3. Streamlit 原型** (可選，新開終端)
```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

**訪問地址**
- 前端: http://localhost:5173
- 後端 API: http://localhost:8000
- API 文檔: http://localhost:8000/docs
- Streamlit: http://localhost:8501

---

#### 方案 B: 使用 Docker Compose (推薦)

```bash
# 構建並啟動所有服務
docker-compose up --build

# 後台運行
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

**訪問地址**
- 前端: http://localhost:5173
- 後端 API: http://localhost:8000
- API 文檔: http://localhost:8000/docs

---

## 🐳 Docker 部署

### 構建自定義鏡像

**後端鏡像**
```bash
cd backend
docker build -t chanlun-api:latest .
docker run -p 8000:8000 chanlun-api:latest
```

**前端鏡像**
```bash
cd frontend
docker build -t chanlun-web:latest .
docker run -p 5173:5173 chanlun-web:latest
```

### Docker Hub 推送 (可選)

```bash
# 登入 Docker Hub
docker login

# 標記鏡像
docker tag chanlun-api:latest your-username/chanlun-api:latest
docker tag chanlun-web:latest your-username/chanlun-web:latest

# 推送
docker push your-username/chanlun-api:latest
docker push your-username/chanlun-web:latest
```

---

## ☁️ Render 雲端部署

### 快速部署 (3 步)

#### 第一步: Fork & 連接 GitHub

1. Fork 本倉庫到你的 GitHub 賬戶
   - https://github.com/your-username/chanlun-screener

2. 登入 [render.com](https://render.com)

3. 連接 GitHub
   - Settings → Connected Services → Connect GitHub
   - 授權訪問你的倉庫

---

#### 第二步: 部署後端

1. 建立新 Web Service
   - Dashboard → New → Web Service
   - 選擇 `chanlun-screener` 倉庫
   - Branch: `main`

2. 配置後端
   ```
   Name:              chanlun-api
   Runtime:           Python 3.11
   Build Command:     cd backend && pip install -r requirements.txt
   Start Command:     cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

3. 環境變數
   ```
   PYTHONUNBUFFERED   1
   API_ENV            production
   ```

4. 其他設置
   - Instance Type: Free (或 Standard 更穩定)
   - Region: Singapore (或最近你的地區)

5. Deploy 按鈕 → 開始部署 (~2分鐘)

**記下後端 URL** 例: `https://chanlun-api-xxxxx.onrender.com`

---

#### 第三步: 部署前端

1. 建立新 Static Site
   - Dashboard → New → Static Site
   - 選擇同一倉庫
   - Branch: `main`

2. 配置前端
   ```
   Name:               chanlun-web
   Build Command:      cd frontend && npm install && npm run build
   Publish Directory:  frontend/dist
   ```

3. 環境變數
   ```
   VITE_API_URL    https://chanlun-api-xxxxx.onrender.com
   ```
   (替換為你的後端 URL)

4. Deploy 按鈕 → 開始部署 (~1分鐘)

**記下前端 URL** 例: `https://chanlun-web-xxxxx.onrender.com`

---

### Render 成本預估

| 服務 | 類型 | 價格 |
|------|------|------|
| 後端 API | Web Service | $7/月 (Free) |
| 前端靜態 | Static Site | $0 (Free) |
| 合計 | - | 免費或 $7/月 |

**優化成本:**
- 使用 Free tier 開發測試
- 生產環境改用 Standard ($12/月) 獲得更好性能

---

### Render 自動部署

配置完成後，每次 push 到 `main` 分支都會自動重新部署：

```bash
git add .
git commit -m "Update screener logic"
git push origin main
# Render 自動檢測變更並重新部署
```

---

## 🔧 環境變數

### 後端 `.env` 文件

複製 `backend/.env.example` 到 `backend/.env`:

```bash
cp backend/.env.example backend/.env
```

編輯 `backend/.env`:
```
# API 設置
API_ENV=development              # 或 production
LOG_LEVEL=INFO                   # DEBUG / INFO / WARNING / ERROR

# 掃描設置
SCAN_INTERVAL_HOURS=24           # 掃描間隔
MAX_WORKERS=8                    # 並發 workers 數

# 數據篩選
MIN_STOCK_PRICE=5.0              # 最低股價
MIN_VOLUME=500000                # 最低日均成交量
```

### 前端 `.env` 文件

創建 `frontend/.env`:
```
# 開發環境
VITE_API_URL=http://localhost:8000

# 生產環境 (Render)
# VITE_API_URL=https://chanlun-api-xxxxx.onrender.com
```

---

## 📊 監控和日誌

### 本地開發
```bash
# 查看後端日誌
tail -f backend/logs/*.log

# 查看前端構建
npm run dev --verbose
```

### Docker
```bash
# 實時日誌
docker-compose logs -f backend
docker-compose logs -f frontend

# 查看特定服務
docker logs chanlun-backend -f
docker logs chanlun-frontend -f
```

### Render 控制板
1. 登入 Render Dashboard
2. 選擇服務 (backend / frontend)
3. Logs 標籤 → 查看實時日誌
4. Metrics 標籤 → 查看 CPU / 內存使用

---

## 🔄 CI/CD 配置 (可選)

### GitHub Actions 自動化部署

創建 `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Render

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy Backend
      run: |
        curl -X POST "${{ secrets.RENDER_BACKEND_DEPLOY_URL }}"
    
    - name: Deploy Frontend
      run: |
        curl -X POST "${{ secrets.RENDER_FRONTEND_DEPLOY_URL }}"
```

---

## 🐛 常見問題

### Q: 後端無法連接到 yfinance

**A:**
```bash
# 檢查網絡連接
ping api.github.com

# 重裝依賴
pip install --upgrade yfinance

# 使用代理 (可選)
pip install pysocks
```

---

### Q: 掃描太慢怎麼辦？

**A:**
1. 減少掃描的候選股票數
   ```python
   # screener.py
   return active_stocks[:50]  # 改為 50 支
   ```

2. 增加 workers 數
   ```python
   results = screener.scan_all(max_workers=16)
   ```

3. 增加 Render 實例規格
   - Settings → Instance Type → Standard

---

### Q: React 頁面無法加載圖表

**A:**
1. 檢查 CORS 配置
   ```python
   # backend/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # 生產改為具體域名
   )
   ```

2. 檢查 API URL
   ```bash
   # 確認 frontend/.env 中的 VITE_API_URL 正確
   echo $VITE_API_URL
   ```

3. 檢查網絡請求
   - 打開瀏覽器開發工具 (F12)
   - Network 標籤 → 查看 API 請求狀態

---

### Q: Render 免費層過期怎麼辦？

**A:**

Render 免費層 15 天無活動會自動暫停。解決方案：

1. **保持活動**
   - 每 15 天訪問一次應用

2. **升級到 Pro**
   - $12/月 獲得持續運行
   - 性能提升 2-4 倍

3. **使用其他平台**
   - Heroku (已停用免費層)
   - Railway ($5/月)
   - Fly.io (免費額度)
   - AWS (首年免費)

---

### Q: API 速率限制怎麼辦？

**A:**

yfinance 有 API 限制。優化方案：

```python
# screener.py - 添加延遲
import time

for ticker in tickers:
    # ... 掃描邏輯 ...
    time.sleep(0.2)  # 每個請求間隔 200ms

# 或使用本地緩存
import cachetools
cache = cachetools.TTLCache(maxsize=100, ttl=3600)
```

---

### Q: 如何改動掃描時間？

**A:**

編輯 `backend/main.py`:

```python
# 改為工作日早上 9 點 (台北時間)
scheduler.add_job(
    run_full_scan,
    'cron',
    day_of_week='mon-fri',
    hour=1,              # UTC 時間 (台北 UTC+8)
    minute=0
)
```

---

## 📚 進階主題

### 使用 Redis 快取

```bash
# 添加 Redis 服務 (docker-compose.yml)
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
```

```python
# backend/main.py
import redis
cache = redis.Redis(host='redis', port=6379)

# 快取掃描結果
cache.setex('scan_results', 3600, json.dumps(results))
```

---

### 設置 WebSocket 實時推送

```python
# backend/main.py
from fastapi import WebSocket

@app.websocket("/ws/scan")
async def websocket_scan(websocket: WebSocket):
    await websocket.accept()
    while True:
        # 推送實時掃描進度
        await websocket.send_json({"progress": scan_state['progress']})
```

---

### 數據庫持久化

```bash
# 使用 PostgreSQL (可選)
docker run --name chanlun-db \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15
```

```python
# backend/main.py
from sqlalchemy import create_engine
engine = create_engine('postgresql://user:password@localhost/chanlun')
```

---

## 📞 支持

- 📖 [官方文檔](./README.md)
- 🐛 [報告 Bug](https://github.com/your-repo/issues)
- 💬 [討論功能](https://github.com/your-repo/discussions)

---

**最後更新**: 2024-10-07
