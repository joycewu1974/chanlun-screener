import yfinance as yf
import pandas as pd
from fractal_analyzer import FractalAnalyzer
from typing import List, Dict
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamicChanLunScreener:
    """動態纏論掃描器 - 實時掃描符合條件的股票"""
    
    def __init__(self, min_price: float = 5.0, min_volume: int = 1000000):
        self.min_price = min_price
        self.min_volume = min_volume
        self.candidates = []
        self.scan_results = []
    
    # ============ 步驟1: 獲取候選股票 ============
    def get_candidates_from_market(self) -> List[str]:
        """從市場即時數據中篩選候選股票"""
        logger.info("Fetching market candidates...")
        candidates = set()
        
        try:
            sp500 = self._get_sp500_tickers()
            candidates.update(sp500)
            logger.info(f"S&P 500: {len(sp500)} stocks")
            
            nasdaq = self._get_nasdaq100_tickers()
            candidates.update(nasdaq)
            logger.info(f"Nasdaq 100: {len(nasdaq)} stocks")
            
            high_volume = self._get_high_volume_stocks(top_n=200)
            candidates.update(high_volume)
            logger.info(f"High Volume: {len(high_volume)} stocks")
            
        except Exception as e:
            logger.error(f"Error fetching candidates: {str(e)}")
            candidates = set(self._get_fallback_tickers())
        
        self.candidates = list(candidates)
        logger.info(f"Total candidates: {len(self.candidates)}")
        return self.candidates
    
    def _get_sp500_tickers(self) -> List[str]:
        """取得 S&P 500 成分股"""
        try:
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            tables = pd.read_html(url)
            df = tables[0]
            return df['Symbol'].tolist()
        except Exception as e:
            logger.warning(f"Failed to fetch S&P 500: {str(e)}")
            return []
    
    def _get_nasdaq100_tickers(self) -> List[str]:
        """取得 Nasdaq 100 成分股"""
        try:
            url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
            tables = pd.read_html(url)
            df = tables[4]
            tickers = df.iloc[:, 0].tolist()
            return [t.replace('.', '-') if '.' in t else t for t in tickers]
        except Exception as e:
            logger.warning(f"Failed to fetch Nasdaq 100: {str(e)}")
            return []
    
    def _get_high_volume_stocks(self, top_n: int = 200) -> List[str]:
        """取得近期高成交量的股票"""
        try:
            active_stocks = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AVGO',
                'ASML', 'NFLX', 'INTC', 'AMD', 'QCOM', 'AMAT', 'ARM', 'ADBE',
                'CRM', 'CSCO', 'ORACLE', 'PYPL', 'SHOP', 'SQ', 'UBER', 'ZOOM',
                'ROKU', 'DDOG', 'SNOW', 'CRWD', 'OKTA', 'SUMO', 'MSTR', 'COIN',
                'BA', 'GE', 'IBM', 'SAP', 'INTU', 'SNPS', 'CDNS', 'KLAC',
                'LRCX', 'ASML', 'ONTO', 'NXPI', 'QRVO', 'SWKS', 'MRVL', 'ANET',
                'SMCI', 'DELL', 'HPQ', 'KEYS', 'ENTG', 'FLEX', 'FTNT', 'PANW',
                'ZS', 'CYBR', 'CRWD', 'WDAY', 'VEEV', 'TEAM', 'NET', 'RBLX',
                'COIN', 'ABNB', 'DASH', 'UPWK', 'PTON', 'PINS', 'SNAP', 'MRNA',
                'BNTX', 'GILD', 'VRTX', 'REGN', 'ILMN', 'DXCM', 'VEEV', 'ZM',
                'SYK', 'TMO', 'LLY', 'JNJ', 'MRK', 'PFE', 'ABBV', 'AZN',
                'BMY', 'AMGN', 'GILD', 'VRTX', 'BIIB', 'ALNY', 'ARCH', 'SDGR',
                'VCYT', 'CRBU', 'CHPT', 'LRCX', 'AMAT', 'KLAC', 'MCHP', 'NXPI',
                'QRVO', 'SWKS', 'ON', 'TER', 'LSCC', 'MU', 'WDC', 'SSNC',
                'NOW', 'SNPS', 'CDNS', 'VRNT', 'SMCI', 'AVGO'
            ]
            return active_stocks[:top_n]
        except Exception as e:
            logger.warning(f"Failed to fetch high volume stocks: {str(e)}")
            return []
    
    def _get_fallback_tickers(self) -> List[str]:
        """降級方案: 使用預設的流動性好的股票"""
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AVGO',
            'ASML', 'NFLX', 'INTC', 'AMD', 'QCOM', 'AMAT', 'ARM', 'ADBE',
            'CRM', 'CSCO', 'ORACLE', 'INFY', 'PYPL', 'SHOP', 'SQ', 'UBER'
        ]
    
    # ============ 步驟2: 過濾流動性 ============
    def filter_by_liquidity(self, tickers: List[str], lookback_days: int = 20) -> List[str]:
        """過濾掉流動性不足的股票"""
        logger.info(f"Filtering {len(tickers)} stocks by liquidity...")
        valid_tickers = []
        
        for ticker in tickers:
            try:
                data = yf.download(ticker, period=f"{lookback_days}d", progress=False)
                
                if len(data) < 10:
                    continue
                
                avg_volume = data['Volume'].mean()
                current_price = data['Close'].iloc[-1]
                
                if avg_volume >= self.min_volume and current_price >= self.min_price:
                    valid_tickers.append(ticker)
                
            except Exception as e:
                logger.debug(f"Skip {ticker}: {str(e)}")
                continue
            
            time.sleep(0.1)
        
        logger.info(f"After liquidity filter: {len(valid_tickers)} stocks")
        return valid_tickers
    
    # ============ 步驟3: 掃描纏論訊號 ============
    def scan_single(self, ticker: str) -> Dict:
        """掃描單支股票"""
        try:
            analyzer = FractalAnalyzer(ticker, period="1y")
            analysis = analyzer.full_analysis()
            
            if analysis['signal_type']:
                return {
                    'ticker': ticker,
                    'scan_time': datetime.now().isoformat(),
                    'status': 'success',
                    **analysis
                }
            else:
                return None
            
        except Exception as e:
            logger.debug(f"Scan failed for {ticker}: {str(e)}")
            return None
    
    def scan_all(self, max_workers: int = 5) -> List[Dict]:
        """並發掃描所有候選股票"""
        if not self.candidates:
            self.get_candidates_from_market()
        
        valid_tickers = self.filter_by_liquidity(self.candidates)
        
        logger.info(f"Starting scan for {len(valid_tickers)} stocks...")
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.scan_single, ticker): ticker 
                for ticker in valid_tickers
            }
            
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
                
                completed += 1
                if completed % 10 == 0:
                    logger.info(f"Progress: {completed}/{len(valid_tickers)}")
        
        results.sort(key=lambda x: (x.get('signal_level', 0), x.get('signal_strength', 0)), reverse=True)
        
        self.scan_results = results
        logger.info(f"Scan complete. Found {len(results)} signals")
        return results
    
    # ============ 步驟4: 結果統計 ============
    def get_summary(self) -> Dict:
        """生成掃描摘要"""
        signal_counts = {}
        for r in self.scan_results:
            sig_type = r.get('signal_type')
            if sig_type:
                signal_counts[sig_type] = signal_counts.get(sig_type, 0) + 1
        
        return {
            'total_scanned': len(self.candidates),
            'signals_found': len(self.scan_results),
            'by_type': signal_counts,
            'by_confidence': {
                'HIGH': len([r for r in self.scan_results if r.get('confidence') == 'HIGH']),
                'MEDIUM': len([r for r in self.scan_results if r.get('confidence') == 'MEDIUM']),
                'LOW': len([r for r in self.scan_results if r.get('confidence') == 'LOW'])
            },
            'scan_time': datetime.now().isoformat()
        }
    
    # ============ 篩選方法 ============
    def filter_by_signal_type(self, signal_type: str) -> List[Dict]:
        """按訊號類型篩選"""
        return [r for r in self.scan_results if r.get('signal_type') == signal_type]
    
    def filter_by_confidence(self, confidence: str) -> List[Dict]:
        """按確信度篩選"""
        return [r for r in self.scan_results if r.get('confidence') == confidence]
    
    def filter_by_price_range(self, min_price: float, max_price: float) -> List[Dict]:
        """按進場點位篩選"""
        return [
            r for r in self.scan_results 
            if min_price <= r.get('entry_price', 0) <= max_price
        ]
    
    def get_top_signals(self, top_n: int = 20) -> List[Dict]:
        """取得前N個最強的訊號"""
        return self.scan_results[:top_n]
