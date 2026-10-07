import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fractal_analyzer import FractalAnalyzer
from ta.momentum import MACD, StochasticOscillator
from ta.volatility import BollingerBands
import pandas as pd
import json

st.set_page_config(page_title="纏論掃描系統", layout="wide")

# CSS 美化
st.markdown("""
<style>
    .metric-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .signal-box {
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        font-weight: bold;
    }
    .signal-buy { background-color: #d4edda; color: #155724; }
    .signal-sell { background-color: #f8d7da; color: #721c24; }
    .signal-none { background-color: #e2e3e5; color: #383d41; }
</style>
""", unsafe_allow_html=True)

st.title("📊 纏論自動掃描與分析系統")
st.markdown("*基於Mark Minervini VCP方法論 × 纏論中樞理論*")

# 側邊欄設定
with st.sidebar:
    st.header("⚙️ 設定")
    
    ticker_input = st.text_input(
        "輸入股票代碼",
        value="AAPL",
        placeholder="例: AAPL, TSLA, NVDA"
    ).upper()
    
    period = st.selectbox(
        "選擇回測期間",
        ["3個月", "6個月", "1年", "2年"],
        index=3
    )
    period_map = {"3個月": "3mo", "6個月": "6mo", "1年": "1y", "2年": "2y"}
    
    if st.button("🔄 分析", use_container_width=True):
        st.session_state.analyze = True

# 主應用邏輯
if ticker_input and 'analyze' in st.session_state and st.session_state.analyze:
    try:
        with st.spinner(f"正在分析 {ticker_input}..."):
            analyzer = FractalAnalyzer(ticker_input, period=period_map[period])
            analysis = analyzer.full_analysis()
        
        # 摘要信息卡
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("目前價格", f"${analysis['current_price']}", delta=None)
        
        with col2:
            signal_type = analysis['signal_type'] or "無"
            st.metric("訊號類型", signal_type, delta=None)
        
        with col3:
            confidence = analysis['confidence']
            st.metric("確信度", confidence, delta=None)
        
        with col4:
            atr = analysis['atr']
            st.metric("波動率(ATR)", f"${atr}", delta=None)
        
        # 買賣點詳情
        st.subheader("🎯 買賣點分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if analysis['signal_type']:
                st.markdown(
                    f"""
                    <div class="signal-box signal-buy">
                    ✅ {analysis['signal_type']} 訊號
                    <br/>
                    信心度: {analysis['confidence']}
                    <br/>
                    強度: {analysis['signal_strength']:.0%}
                    <br/>
                    {analysis['description']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div class="signal-box signal-none">
                    ⚪ 暫無明確訊號
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        with col2:
            st.markdown("### 📍 進出場點位")
            targets_df = pd.DataFrame({
                '點位類型': ['進場價', '支撐位', '10%目標', '20%目標'],
                '價格 ($)': [
                    analysis['entry_price'],
                    analysis['support'],
                    analysis['target_10pct'],
                    analysis['target_20pct']
                ],
                '與現價差': [
                    f"{((analysis['entry_price']/analysis['current_price']-1)*100):+.2f}%",
                    f"{((analysis['support']/analysis['current_price']-1)*100):+.2f}%",
                    f"{((analysis['target_10pct']/analysis['current_price']-1)*100):+.2f}%",
                    f"{((analysis['target_20pct']/analysis['current_price']-1)*100):+.2f}%"
                ]
            })
            st.dataframe(targets_df, use_container_width=True, hide_index=True)
        
        # 中樞信息
        if analysis['centers']:
            st.subheader("📌 中樞結構")
            centers_df = pd.DataFrame([
                {
                    '類型': c['type'].replace('_center', ''),
                    '下界': f"${c['low']}",
                    '上界': f"${c['high']}",
                    '寬度': f"${c['width']}",
                    '中點': f"${c['midpoint']}"
                }
                for c in analysis['centers']
            ])
            st.dataframe(centers_df, use_container_width=True, hide_index=True)
        
        # K線圖表
        st.subheader("📈 K線圖表 + 技術指標")
        
        df = analyzer.df.copy()
        
        # 計算技術指標
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
                       name='BB上軌', line=dict(color='rgba(0,100,200,0.3)', dash='dash'),
                       showlegend=True),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['Date'], y=df['BB_Low'],
                       name='BB下軌', line=dict(color='rgba(0,100,200,0.3)', dash='dash'),
                       showlegend=True, fill='tonexty'),
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
        
        # 進場、支撐、目標線
        fig.add_hline(y=analysis['entry_price'], line_dash="dot", line_color="green",
                      annotation_text=f"進場: ${analysis['entry_price']}", row=1, col=1)
        fig.add_hline(y=analysis['support'], line_dash="dot", line_color="red",
                      annotation_text=f"支撐: ${analysis['support']}", row=1, col=1)
        fig.add_hline(y=analysis['target_10pct'], line_dash="dash", line_color="gold",
                      annotation_text=f"目標1: ${analysis['target_10pct']}", row=1, col=1)
        fig.add_hline(y=analysis['target_20pct'], line_dash="dash", line_color="blue",
                      annotation_text=f"目標2: ${analysis['target_20pct']}", row=1, col=1)
        
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
                   marker_color=['green' if x > 0 else 'red' for x in df['MACD_Hist']],
                   showlegend=True),
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
        fig.add_hline(y=80, line_dash="dash", line_color="gray", row=3, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="gray", row=3, col=1)
        
        fig.update_xaxes(title_text="日期", row=3, col=1)
        fig.update_yaxes(title_text="價格 ($)", row=1, col=1)
        fig.update_yaxes(title_text="MACD", row=2, col=1)
        fig.update_yaxes(title_text="KDJ", row=3, col=1)
        
        fig.update_layout(
            title=f"{ticker_input} - 纏論分析 ({analysis['signal_type'] or '無訊號'})",
            height=1000,
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 分形和筆信息
        with st.expander("🔬 分形與筆詳情"):
            col1, col2 = st.columns(2)
            
            with col1:
                if analysis['fractals']['tops']:
                    tops_df = pd.DataFrame(analysis['fractals']['tops'])
                    st.write("**頂分型 (Top Fractals)**")
                    st.dataframe(tops_df, use_container_width=True, hide_index=True)
            
            with col2:
                if analysis['fractals']['bottoms']:
                    bottoms_df = pd.DataFrame(analysis['fractals']['bottoms'])
                    st.write("**底分型 (Bottom Fractals)**")
                    st.dataframe(bottoms_df, use_container_width=True, hide_index=True)
        
        # 原始數據輸出
        with st.expander("📋 完整分析數據(JSON)"):
            st.json(analysis)
    
    except Exception as e:
        st.error(f"❌ 分析失敗: {str(e)}")
        st.info("請檢查股票代碼是否正確，或稍後重試")

else:
    st.info("👈 請在左側輸入股票代碼並點擊「分析」開始")
    st.markdown("""
    ### 📖 使用說明
    
    1. **輸入股票代碼**: 在側邊欄輸入美股代碼 (例: AAPL, TSLA)
    2. **選擇回測期間**: 預設2年，可調整
    3. **點擊分析**: 系統自動計算纏論買賣點
    
    ### 🎯 訊號解讀
    
    - **一買**: 底部背馳，動能衰竭，風險最高但收益最大
    - **二買**: 確認買點，回踩未創新低，風險較低
    - **三買**: 離開中樞向上，新趨勢確立，穩健進場
    
    ### 📍 進出場邏輯
    
    - **進場價**: 根據訊號類型動態調整
    - **支撐位**: 進場價 - 1倍ATR
    - **10%目標**: 進場價 + 1.5倍ATR
    - **20%目標**: 進場價 + 3倍ATR
    """)
