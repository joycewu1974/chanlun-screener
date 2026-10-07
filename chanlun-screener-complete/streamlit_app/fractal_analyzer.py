import numpy as np
import pandas as pd
import yfinance as yf
from ta.momentum import MACD, StochasticOscillator
from ta.volatility import AverageTrueRange, BollingerBands
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

class FractalAnalyzer:
    """纏論K線分析器 - 完整版"""
    
    def __init__(self, ticker: str, period: str = "2y"):
        self.ticker = ticker.upper()
        try:
            self.df = yf.download(self.ticker, period=period, interval="1d", progress=False)
            if self.df.empty:
                raise ValueError(f"無法下載 {self.ticker} 的數據")
            self.df.reset_index(inplace=True)
        except Exception as e:
            raise Exception(f"下載數據失敗: {str(e)}")
    
    # ============ 1. 分型識別 ============
    def find_fractals(self) -> Dict[str, List[Dict]]:
        """識別頂分型和底分型"""
        tops = []
        bottoms = []
        
        for i in range(1, len(self.df) - 1):
            h0 = self.df['High'].iloc[i]
            h_prev = self.df['High'].iloc[i-1]
            h_next = self.df['High'].iloc[i+1]
            
            l0 = self.df['Low'].iloc[i]
            l_prev = self.df['Low'].iloc[i-1]
            l_next = self.df['Low'].iloc[i+1]
            
            # 頂分型
            if h_prev < h0 > h_next:
                tops.append({
                    'index': i,
                    'date': self.df['Date'].iloc[i],
                    'price': round(float(h0), 2),
                    'type': 'top'
                })
            
            # 底分型
            if l_prev > l0 < l_next:
                bottoms.append({
                    'index': i,
                    'date': self.df['Date'].iloc[i],
                    'price': round(float(l0), 2),
                    'type': 'bottom'
                })
        
        return {'tops': tops, 'bottoms': bottoms}
    
    # ============ 2. 筆的形成 ============
    def form_strokes(self) -> List[Dict]:
        """連接頂分型 ↔ 底分型形成筆"""
        fractals = self.find_fractals()
        tops = fractals['tops']
        bottoms = fractals['bottoms']
        
        strokes = []
        all_points = sorted(tops + bottoms, key=lambda x: x['index'])
        
        for i in range(len(all_points) - 1):
            curr = all_points[i]
            next_pt = all_points[i + 1]
            
            if curr['type'] != next_pt['type']:
                strokes.append({
                    'from': curr,
                    'to': next_pt,
                    'direction': 'up' if curr['type'] == 'bottom' else 'down',
                    'length': abs(next_pt['price'] - curr['price']),
                    'from_index': curr['index'],
                    'to_index': next_pt['index']
                })
        
        return strokes
    
    # ============ 3. 中樞識別 ============
    def find_centers(self) -> List[Dict]:
        """找出中樞區域"""
        strokes = self.form_strokes()
        centers = []
        
        for i in range(len(strokes) - 2):
            s1, s2, s3 = strokes[i], strokes[i+1], strokes[i+2]
            
            if s1['direction'] == 'up' and s2['direction'] == 'down' and s3['direction'] == 'up':
                low = max(s1['from']['price'], s3['from']['price'])
                high = min(s2['to']['price'], s1['to']['price'])
                
                if low < high:
                    centers.append({
                        'type': 'up_center',
                        'low': low,
                        'high': high,
                        'start_index': s1['from_index'],
                        'end_index': s3['to_index'],
                        'width': round(high - low, 2),
                        'midpoint': round((high + low) / 2, 2)
                    })
            elif s1['direction'] == 'down' and s2['direction'] == 'up' and s3['direction'] == 'down':
                low = min(s1['to']['price'], s3['to']['price'])
                high = max(s2['from']['price'], s1['from']['price'])
                
                if low < high:
                    centers.append({
                        'type': 'down_center',
                        'low': low,
                        'high': high,
                        'start_index': s1['from_index'],
                        'end_index': s3['to_index'],
                        'width': round(high - low, 2),
                        'midpoint': round((high + low) / 2, 2)
                    })
        
        return centers
    
    # ============ 4. 背馳判斷 ============
    def check_divergence(self) -> Dict:
        """用MACD Histogram判斷背馳"""
        macd = MACD(self.df['Close'], window_fast=12, window_slow=26, window_sign=9)
        macd_hist = macd.macd_diff()
        self.df['MACD_Hist'] = macd_hist
        
        recent_bars = 10
        recent_low_idx = self.df['Low'].iloc[-recent_bars:].idxmin()
        recent_high_idx = self.df['High'].iloc[-recent_bars:].idxmax()
        
        recent_low = self.df['Low'].iloc[-recent_bars:].min()
        recent_high = self.df['High'].iloc[-recent_bars:].max()
        
        macd_at_low = self.df['MACD_Hist'].iloc[recent_low_idx]
        macd_at_high = self.df['MACD_Hist'].iloc[recent_high_idx]
        
        last_macd = self.df['MACD_Hist'].iloc[-1]
        
        return {
            'price_new_low': self.df['Low'].iloc[-1] == recent_low,
            'price_new_high': self.df['High'].iloc[-1] == recent_high,
            'macd_at_low': round(float(macd_at_low), 4),
            'macd_at_high': round(float(macd_at_high), 4),
            'last_macd': round(float(last_macd), 4),
            'bearish_divergence': self.df['Low'].iloc[-1] < recent_low and macd_at_low < last_macd,
            'bullish_divergence': self.df['High'].iloc[-1] > recent_high and macd_at_high > last_macd
        }
    
    # ============ 5. 買賣點識別 ============
    def identify_signals(self) -> Dict:
        """識別一買/二買/三買"""
        centers = self.find_centers()
        divergence = self.check_divergence()
        current_price = round(float(self.df['Close'].iloc[-1]), 2)
        
        signals = {
            'type': None,
            'level': None,
            'strength': 0,
            'description': '',
            'confidence': 'LOW'
        }
        
        if not centers:
            return signals
        
        latest_center = centers[-1]
        center_width = latest_center['width']
        distance_to_low = abs(current_price - latest_center['low'])
        
        # ===== 一買 =====
        if distance_to_low < center_width * 0.15:
            if divergence['price_new_low'] and not divergence['bearish_divergence']:
                signals['type'] = '一買'
                signals['level'] = 1
                signals['strength'] = 0.85
                signals['description'] = '底部背馳，動能衰竭'
                signals['confidence'] = 'HIGH'
        
        # ===== 二買 =====
        if len(centers) >= 2:
            prev_low = centers[-2]['low']
            if current_price > prev_low and self.df['Low'].iloc[-3:].min() > prev_low:
                signals['type'] = '二買'
                signals['level'] = 2
                signals['strength'] = 0.75
                signals['description'] = '確認買點，回踩未破新低'
                signals['confidence'] = 'MEDIUM'
        
        # ===== 三買 =====
        if current_price > latest_center['high']:
            recent_low = self.df['Low'].iloc[-5:].min()
            if recent_low > latest_center['low']:
                signals['type'] = '三買'
                signals['level'] = 3
                signals['strength'] = 0.90
                signals['description'] = '離開中樞向上，回調未破中樞'
                signals['confidence'] = 'HIGH'
        
        return signals
    
    # ============ 6. 支撐阻力 & 目標點位 ============
    def calculate_targets(self) -> Dict:
        """計算進場、支撐、目標點位"""
        atr_obj = AverageTrueRange(
            self.df['High'], 
            self.df['Low'], 
            self.df['Close'],
            window=14
        )
        atr_values = atr_obj.average_true_range()
        current_atr = float(atr_values.iloc[-1])
        current_price = float(self.df['Close'].iloc[-1])
        
        centers = self.find_centers()
        signals = self.identify_signals()
        
        if centers:
            latest_center = centers[-1]
            
            if signals['type'] == '一買':
                entry_price = latest_center['low'] - current_atr * 0.3
            elif signals['type'] == '二買':
                entry_price = latest_center['low']
            elif signals['type'] == '三買':
                entry_price = latest_center['high'] + current_atr * 0.2
            else:
                entry_price = current_price
            
            support = entry_price - current_atr
        else:
            entry_price = current_price
            support = current_price - current_atr
        
        target_10pct = entry_price + current_atr * 1.5
        target_20pct = entry_price + current_atr * 3.0
        
        return {
            'entry_price': round(entry_price, 2),
            'support': round(support, 2),
            'target_10pct': round(target_10pct, 2),
            'target_20pct': round(target_20pct, 2),
            'atr': round(current_atr, 2),
            'current_price': round(current_price, 2)
        }
    
    # ============ 7. 完整分析 ============
    def full_analysis(self) -> Dict:
        """統合所有分析"""
        signals = self.identify_signals()
        targets = self.calculate_targets()
        centers = self.find_centers()
        fractals = self.find_fractals()
        
        return {
            'ticker': self.ticker,
            'current_price': targets['current_price'],
            'signal_type': signals['type'],
            'signal_level': signals['level'],
            'signal_strength': signals['strength'],
            'confidence': signals['confidence'],
            'description': signals['description'],
            'centers': centers[-3:] if centers else [],
            'fractals': {
                'tops': fractals['tops'][-5:] if fractals['tops'] else [],
                'bottoms': fractals['bottoms'][-5:] if fractals['bottoms'] else []
            },
            **targets
        }
