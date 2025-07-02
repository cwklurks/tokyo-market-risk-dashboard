"""
Configuration file for Tokyo Market Risk Dashboard.
"""
import os
from typing import Dict, List

API_ENDPOINTS = {
    "p2pquake": "https://api.p2pquake.net/v2/history",
    "tokyo_metro": "https://api.tokyometroapp.jp/api/v2",
    "openweather": "https://api.openweathermap.org/data/2.5",
    "boj": "https://www.boj.or.jp/statistics/market/short/jgbcm",
    "yahoo_finance": "https://finance.yahoo.com"
}

TOKYO_TICKERS = {
    "nikkei": "^N225",
    "topix": "1306.T",
    "jpy_usd": "USDJPY=X",
    "jpy_eur": "EURJPY=X",
    "sony": "SONY",
    "toyota": "TM",
    "softbank": "9984.T",
    "nintendo": "NTDOY",
    "mitsubishi": "8306.T"
}


RISK_THRESHOLDS = {
    "earthquake": {
        "low": 4.0,
        "medium": 5.5,
        "high": 7.0,
        "critical": 8.0
    },
    "market_volatility": {
        "low": 0.15,
        "medium": 0.25,
        "high": 0.35,
        "critical": 0.50
    },
    "correlation": {
        "low": 0.3,
        "medium": 0.6,
        "high": 0.8,
        "critical": 0.9
    }
}

THEME_COLORS = {
    "primary": "#1B263B",
    "secondary": "#415A77", 
    "accent": "#778DA9",
    "warning": "#E63946",
    "success": "#2D6A4F",
    "info": "#457B9D",
    "background": "#0D1117",
    "surface": "#161B22",
    "text_primary": "#F0F6FC",
    "text_secondary": "#8B949E"
}

TOKYO_COORDS = {
    "lat": 35.6762,
    "lon": 139.6503,
    "region_bounds": {
        "north": 36.0,
        "south": 35.0,
        "east": 140.0,
        "west": 139.0
    }
}

TRANSLATIONS = {
    "en": {
        "title": "Tokyo Market Risk Dashboard",
        "subtitle": "Real-time Risk Management & Decision Support",
        "earthquake_risk": "Earthquake Risk",
        "market_volatility": "Market Volatility",
        "correlation_analysis": "Correlation Analysis",
        "decision_queue": "Decision Queue",
        "risk_low": "LOW",
        "risk_medium": "MEDIUM", 
        "risk_high": "HIGH",
        "risk_critical": "CRITICAL",
        "loading_market_data": "Loading market data...",
        "loading_earthquake_data": "Loading earthquake data...",
        "loading_risk_assessment": "Loading risk assessment...",
        "market_data_unavailable": "Market data temporarily unavailable.",
        "earthquake_data_unavailable": "Unable to fetch earthquake data. Using cached information.",
        "risk_data_unavailable": "Unable to fetch risk data. Using cached information.",
        "no_pending_decisions": "No pending decisions at this time.",
        "current_assessment": "Current Assessment",
        "market_correlation_analysis": "Market Correlation Analysis",
        "analyze_historical_patterns": "Analyze Historical Patterns",
        "clear_history": "Clear History",
        "decision_history": "Decision History",
        "approve": "Approve",
        "reject": "Reject",
        "run_simulation": "Run Simulation"
    },
    "jp": {
        "title": "東京市場リスクダッシュボード",
        "subtitle": "リアルタイムリスク管理・意思決定支援",
        "earthquake_risk": "地震リスク",
        "market_volatility": "市場ボラティリティ",
        "correlation_analysis": "相関分析",
        "decision_queue": "意思決定キュー",
        "risk_low": "低",
        "risk_medium": "中",
        "risk_high": "高", 
        "risk_critical": "緊急",
        "loading_market_data": "市場データを読み込み中...",
        "loading_earthquake_data": "地震データを読み込み中...",
        "loading_risk_assessment": "リスク評価を読み込み中...",
        "market_data_unavailable": "市場データが一時的に利用できません。",
        "earthquake_data_unavailable": "地震データを取得できませんでした。キャッシュ情報を使用しています。",
        "risk_data_unavailable": "リスクデータを取得できませんでした。キャッシュ情報を使用しています。",
        "no_pending_decisions": "現在保留中の決定事項はありません。",
        "current_assessment": "現在の評価",
        "market_correlation_analysis": "市場相関分析",
        "analyze_historical_patterns": "過去パターン分析",
        "clear_history": "履歴をクリア",
        "decision_history": "決定履歴",
        "approve": "承認",
        "reject": "拒否",
        "run_simulation": "シミュレーション実行"
    }
} 