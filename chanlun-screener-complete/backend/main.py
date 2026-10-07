from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from fractal_analyzer import FractalAnalyzer
from screener import DynamicChanLunScreener
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="纏論掃描系統 API",
    description="基於纏論理論的即時股票自動掃描系統",
    version="2.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局狀態
scan_state = {
    'results': [],
    'summary': {},
    'last_scan': None,
    'scanning': False,
    'candidates': [],
    'progress': 0,
    'total': 0
}

screener = DynamicChanLunScreener(min_price=5.0, min_volume=500000)

# ============ 後台掃描任務 ============
scheduler = BackgroundScheduler()

def run_full_scan():
    """完整的動態掃描流程"""
    if scan_state['scanning']:
        logger.info("Scan already in progress")
        return
    
    scan_state['scanning'] = True
    scan_state['progress'] = 0
    
    try:
        logger.info("=== 開始動態掃描 ===")
        
        candidates = screener.get_candidates_from_market()
        scan_state['candidates'] = candidates
        scan_state['total'] = len(candidates)
        
        logger.info("Step 2/3: 掃描候選股票...")
        results = screener.scan_all(max_workers=8)
        
        logger.info("Step 3/3: 生成統計...")
        summary = screener.get_summary()
        
        scan_state['results'] = results
        scan_state['summary'] = summary
        scan_state['last_scan'] = datetime.now().isoformat()
        
        logger.info(f"✅ 掃描完成。找到 {len(results)} 個訊號")
        logger.info(f"訊號分佈: {summary['by_type']}")
        logger.info(f"確信度分佈: {summary['by_confidence']}")
        
    except Exception as e:
        logger.error(f"❌ 掃描失敗: {str(e)}", exc_info=True)
    
    finally:
        scan_state['scanning'] = False
        scan_state['progress'] = 100

# 定時掃描: 工作日每天下午4:30 (美股收盤後)
scheduler.add_job(run_full_scan, 'cron', day_of_week='mon-fri', hour=20, minute=30)
scheduler.start()

# ============ API 端點 ============

@app.get("/health")
async def health():
    """健康檢查"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "last_scan": scan_state['last_scan']
    }

@app.get("/api/scan/status")
async def scan_status():
    """實時掃描狀態"""
    return {
        'scanning': scan_state['scanning'],
        'progress': scan_state['progress'],
        'total': scan_state['total'],
        'last_scan': scan_state['last_scan'],
        'signals_found': len(scan_state['results']),
        'summary': scan_state['summary']
    }

@app.post("/api/scan/run")
async def run_scan_manual(background_tasks: BackgroundTasks):
    """手動觸發掃描"""
    if scan_state['scanning']:
        raise HTTPException(status_code=429, detail="掃描已在進行中")
    
    background_tasks.add_task(run_full_scan)
    return {
        "message": "掃描已啟動",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/scan/results")
async def get_scan_results(
    signal_type: str = Query(None),
    confidence: str = Query(None),
    min_price: float = Query(None),
    max_price: float = Query(None),
    limit: int = Query(50)
):
    """取得掃描結果 (支持多重篩選)"""
    results = scan_state['results']
    
    if signal_type:
        results = screener.filter_by_signal_type(signal_type)
    
    if confidence:
        results = [r for r in results if r.get('confidence') == confidence]
    
    if min_price and max_price:
        results = screener.filter_by_price_range(min_price, max_price)
    
    return {
        'total': len(results),
        'data': results[:limit],
        'last_scan': scan_state['last_scan'],
        'filters_applied': {
            'signal_type': signal_type,
            'confidence': confidence,
            'price_range': f"${min_price}-${max_price}" if min_price and max_price else None
        }
    }

@app.get("/api/scan/candidates")
async def get_candidates():
    """取得候選股票清單"""
    return {
        'count': len(scan_state['candidates']),
        'tickers': scan_state['candidates'][:100],
        'total_available': len(scan_state['candidates'])
    }

@app.get("/api/scan/summary")
async def get_summary():
    """取得掃描摘要統計"""
    return {
        'summary': scan_state['summary'],
        'candidates_count': len(scan_state['candidates']),
        'signals_by_level': {
            '一買': len(screener.filter_by_signal_type('一買')),
            '二買': len(screener.filter_by_signal_type('二買')),
            '三買': len(screener.filter_by_signal_type('三買'))
        }
    }

@app.get("/api/analyze/{ticker}")
async def analyze_stock(ticker: str):
    """分析單支股票"""
    try:
        analyzer = FractalAnalyzer(ticker.upper(), period="2y")
        analysis = analyzer.full_analysis()
        return analysis
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/chart/{ticker}")
async def get_chart(ticker: str):
    """取得圖表JSON"""
    try:
        analyzer = FractalAnalyzer(ticker.upper(), period="2y")
        df = analyzer.df.copy()
        analysis = analyzer.full_analysis()
        
        # 計算技術指標
        from ta.momentum import MACD, StochasticOscillator
        from ta.volatility import BollingerBands
        
        macd = MACD(df['Close'], window_fast=12, window_slow=26, window_sign=9)
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Hist'] = macd.macd_diff()
        
        kdj = StochasticOscillator(df['High'], df['Low'], df['Close'], window=14, smooth_k=3)
        df['KDJ_K'] = kdj.stoch()
        df['KDJ_D'] = kdj.stoch_signal()
        
        bb = BollingerBands(df['Close'], window=20, window_dev=2)
        df['BB_High'] = bb.bollinger_hband()
        df['BB_Low'] = bb.bollinger_lband()
        df['BB_Mid'] = bb.bollinger_mavg()
        
        # 創建子圖
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            row_heights=[0.5, 0.25, 0.25],
            specs=[[{"secondary_y": False}], [{}], [{}]],
            vertical_spacing=0.08
        )
        
        # K線
        fig.add_trace(
            go.Candlestick(
                x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='K線',
                increasing_line_color='green',
                decreasing_line_color='red'
            ),
            row=1, col=1
        )
        
        # 布林通道
        fig.add_trace(
            go.Scatter(x=df['Date'], y=df['BB_High'],
                       name='BB上軌', line=dict(color='rgba(0,100,200,0.3)', dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['Date'], y=df['BB_Low'],
                       name='BB下軌', line=dict(color='rgba(0,100,200,0.3)', dash='dash'),
                       fill='tonexty'),
            row=1, col=1
        )
        
        # 中樞標記
        for center in analysis['centers']:
            fig.add_hrect(
                y0=center['low'], y1=center['high'],
                fillcolor="rgba(128,0,128,0.1)",
                layer="below",
                row=1, col=1
            )
        
        # MACD
        fig.add_trace(
            go.Scatter(x=df['Date'], y=df['MACD'], name='MACD',
                       line=dict(color='blue', width=1)),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['Date'], y=df['MACD_Signal'], name='Signal',
                       line=dict(color='red', width=1)),
            row=2, col=1
        )
        fig.add_trace(
            go.Bar(x=df['Date'], y=df['MACD_Hist'], name='Histogram',
                   marker_color=['green' if x > 0 else 'red' for x in df['MACD_Hist']]),
            row=2, col=1
        )
        
        # KDJ
        fig.add_trace(
            go.Scatter(x=df['Date'], y=df['KDJ_K'], name='K',
                       line=dict(color='blue', width=1.5)),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['Date'], y=df['KDJ_D'], name='D',
                       line=dict(color='red', width=1.5)),
            row=3, col=1
        )
        
        fig.update_xaxes(title_text="日期", row=3, col=1)
        fig.update_yaxes(title_text="價格 ($)", row=1, col=1)
        fig.update_yaxes(title_text="MACD", row=2, col=1)
        fig.update_yaxes(title_text="KDJ", row=3, col=1)
        
        fig.update_layout(
            title=f"{ticker} - 纏論分析 ({analysis['signal_type'] or '無訊號'})",
            height=1000,
            hovermode='x unified',
            template='plotly_white'
        )
        
        return {"chart": pio.to_json(fig)}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """系統統計"""
    return {
        'total_signals': len(scan_state['results']),
        'by_type': scan_state['summary'].get('by_type', {}),
        'by_confidence': scan_state['summary'].get('by_confidence', {}),
        'last_scan': scan_state['last_scan'],
        'cache_size_mb': len(json.dumps(scan_state)) / (1024*1024)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
