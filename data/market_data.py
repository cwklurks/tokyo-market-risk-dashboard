"""
Market Data Provider for Tokyo Market Risk Dashboard
Handles real-time market data from Yahoo Finance and other sources
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional, Tuple
import logging
import streamlit as st
from config import TOKYO_TICKERS, API_ENDPOINTS
import pytz

class MarketDataProvider:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
    @st.cache_data(ttl=60)  # Cache for 1 minute for more current data
    def get_real_time_data(_self, ticker: str) -> Optional[Dict]:
        """Fetch real-time market data for a given ticker"""
        try:
            stock = yf.Ticker(ticker)
            
            # Try to get intraday data first for more current prices
            try:
                # Get intraday data if market is open
                if _self.is_market_open():
                    intraday = stock.history(period="1d", interval="5m")
                    if not intraday.empty:
                        current_price = intraday['Close'].iloc[-1]
                        # Get yesterday's close for comparison
                        hist = stock.history(period="5d", interval="1d")
                        if not hist.empty and len(hist) > 1:
                            prev_close = hist['Close'].iloc[-2]
                        else:
                            prev_close = intraday['Close'].iloc[0]
                    else:
                        # Fallback to daily data
                        hist = stock.history(period="5d", interval="1d")
                        if hist.empty:
                            return _self._get_mock_data(ticker)
                        current_price = hist['Close'].iloc[-1]
                        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                else:
                    # Market closed, use daily data
                    hist = stock.history(period="5d", interval="1d")
                    if hist.empty:
                        return _self._get_mock_data(ticker)
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            except:
                # Fallback to daily data
                hist = stock.history(period="5d", interval="1d")
                if hist.empty:
                    return _self._get_mock_data(ticker)
                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100 if prev_close else 0
            
            # Get volume from appropriate source
            if '_self' in locals() and hasattr(_self, 'is_market_open') and _self.is_market_open() and 'intraday' in locals() and not intraday.empty:
                volume = int(intraday['Volume'].sum()) if not intraday['Volume'].empty else 0
                high = float(intraday['High'].max())
                low = float(intraday['Low'].min())
            else:
                volume = int(hist['Volume'].iloc[-1]) if 'hist' in locals() and not hist.empty and not hist['Volume'].empty else 0
                high = float(hist['High'].iloc[-1]) if 'hist' in locals() and not hist.empty else float(current_price)
                low = float(hist['Low'].iloc[-1]) if 'hist' in locals() and not hist.empty else float(current_price)
            
            return {
                'ticker': ticker,
                'current_price': float(current_price),
                'previous_close': float(prev_close),
                'change': float(change),
                'change_percent': float(change_percent),
                'volume': volume,
                'high': high,
                'low': low,
                'timestamp': datetime.now(),
                'is_live': _self.is_market_open()
            }
        except Exception as e:
            _self.logger.error(f"Error fetching data for {ticker}: {e}")
            return _self._get_mock_data(ticker)
    
    def _get_mock_data(self, ticker: str) -> Dict:
        """Return mock data when API fails"""
        # Generate realistic mock data based on ticker
        base_prices = {
            "^N225": 33000,
            "1306.T": 2400, 
            "USDJPY=X": 150,
            "EURJPY=X": 162,
            "SONY": 85,
            "TM": 150,
            "NTDOY": 12
        }
        
        base_price = base_prices.get(ticker, 100)
        # Add some random variation
        price_variation = np.random.uniform(-0.02, 0.02)
        current_price = base_price * (1 + price_variation)
        change_percent = price_variation * 100
        
        return {
            'ticker': ticker,
            'current_price': current_price,
            'previous_close': base_price,
            'change': current_price - base_price,
            'change_percent': change_percent,
            'volume': np.random.randint(1000000, 10000000),
            'high': current_price * 1.01,
            'low': current_price * 0.99,
            'timestamp': datetime.now()
        }
    
    @st.cache_data(ttl=1800)  # Cache for 30 minutes
    def get_historical_data(_self, ticker: str, period: str = "1mo") -> pd.DataFrame:
        """Fetch historical market data"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            if hist.empty:
                return _self._get_mock_historical_data(ticker, period)
            return hist
        except Exception as e:
            _self.logger.error(f"Error fetching historical data for {ticker}: {e}")
            return _self._get_mock_historical_data(ticker, period)
    
    def _get_mock_historical_data(self, ticker: str, period: str) -> pd.DataFrame:
        """Generate mock historical data"""
        days = 30 if period == "1mo" else 90
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        base_price = 33000 if ticker == "^N225" else 100
        prices = base_price + np.cumsum(np.random.randn(days) * base_price * 0.01)
        
        return pd.DataFrame({
            'Open': prices * (1 + np.random.uniform(-0.005, 0.005, days)),
            'High': prices * (1 + np.random.uniform(0, 0.01, days)),
            'Low': prices * (1 + np.random.uniform(-0.01, 0, days)),
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, days)
        }, index=dates)
    
    @st.cache_data(ttl=1800)  # Cache for 30 minutes
    def calculate_volatility(_self, ticker: str, window: int = 30) -> float:
        """Calculate historical volatility"""
        try:
            hist = _self.get_historical_data(ticker, period="3mo")
            if hist.empty:
                return 0.25  # Default volatility
                
            returns = hist['Close'].pct_change().dropna()
            if len(returns) < window:
                return 0.25
                
            volatility = returns.std() * np.sqrt(252)
            return float(volatility) if not np.isnan(volatility) else 0.25
        except Exception as e:
            _self.logger.error(f"Error calculating volatility for {ticker}: {e}")
            return 0.25
    
    def get_correlation_matrix(self, tickers: List[str], period: str = "3mo") -> pd.DataFrame:
        """Calculate correlation matrix for given tickers"""
        try:
            data = {}
            for ticker in tickers:
                hist = self.get_historical_data(ticker, period)
                if not hist.empty:
                    data[ticker] = hist['Close'].pct_change().dropna()
            
            if not data:
                return pd.DataFrame()
                
            df = pd.DataFrame(data)
            return df.corr()
        except Exception as e:
            self.logger.error(f"Error calculating correlation matrix: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=120)  # Cache for 2 minutes for more current data
    def get_tokyo_market_summary(_self) -> Dict:
        """Get summary of major Tokyo market indices"""
        summary = {}
        
        # Get all available tickers, not just key ones
        for name, ticker in TOKYO_TICKERS.items():
            try:
                data = _self.get_real_time_data(ticker)
                if data:
                    # Ensure we have proper volatility data
                    volatility = _self.calculate_volatility(ticker)
                    data['volatility'] = volatility
                    summary[name] = data
                else:
                    # Provide fallback data if API fails
                    summary[name] = _self._get_mock_data(ticker)
                    summary[name]['volatility'] = 0.25  # Default volatility
            except Exception as e:
                _self.logger.error(f"Error fetching {ticker}: {e}")
                # Provide fallback data
                summary[name] = _self._get_mock_data(ticker)
                summary[name]['volatility'] = 0.25
        
        return summary
    
    def get_vix_equivalent(self) -> float:
        """Calculate VIX-equivalent for Nikkei (simplified)"""
        try:
            # Fetch Nikkei options data (simplified - in practice would need options chain)
            nikkei_vol = self.calculate_volatility("^N225", window=21)
            return nikkei_vol * 100  # Convert to percentage
        except Exception as e:
            self.logger.error(f"Error calculating VIX equivalent: {e}")
            return 20.0  # Default value
    
    def get_currency_pairs(self) -> Dict:
        """Get currency pair data"""
        currency_pairs = {
            'JPY/USD': 'USDJPY=X',
            'EUR/JPY': 'EURJPY=X',
            'GBP/JPY': 'GBPJPY=X'
        }
        
        results = {}
        for pair_name, ticker in currency_pairs.items():
            try:
                data = self.get_real_time_data(ticker)
                if data:
                    results[pair_name] = data
            except Exception as e:
                self.logger.error(f"Error fetching {pair_name}: {e}")
                continue
        
        return results
    
    def is_market_open(self) -> bool:
        """Check if Tokyo market is currently open"""
        try:
            # Tokyo timezone
            tokyo_tz = pytz.timezone('Asia/Tokyo')
            tokyo_time = datetime.now(tokyo_tz)
            
            # Tokyo Stock Exchange hours: 9:00-11:30, 12:30-15:00
            weekday = tokyo_time.weekday()  # 0=Monday, 6=Sunday
            hour = tokyo_time.hour
            minute = tokyo_time.minute
            
            # Weekend check
            if weekday >= 5:  # Saturday or Sunday
                return False
            
            # Market hours check
            morning_session = (9 <= hour < 11) or (hour == 11 and minute <= 30)
            afternoon_session = (12 <= hour < 15) or (hour == 12 and minute >= 30)
            
            return morning_session or afternoon_session
            
        except Exception as e:
            self.logger.error(f"Error checking market hours: {e}")
            return True  # Default to open if we can't determine
    
    def get_sector_performance(self) -> Dict:
        """Get sector performance data"""
        # Major Japanese ETFs representing different sectors
        sectors = {
            'Technology': '1321.T',  # Nikkei 225 ETF 
            'Banking': '1615.T',     # TOPIX Banks ETF
            'Real Estate': '1343.T', # NEXT FUNDS REIT ETF
            'Consumer': '1311.T',    # TOPIX ETF
            'Manufacturing': '1320.T' # Nikkei 225 ETF
        }
        
        sector_data = {}
        for sector, ticker in sectors.items():
            data = self.get_real_time_data(ticker)
            if data:
                sector_data[sector] = data
                
        return sector_data 