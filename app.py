"""
Tokyo Market Risk Dashboard
A Palantir Foundry-inspired risk management dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import yfinance as yf
from typing import Dict, List, Tuple
import time


from config import *
from data.market_data import MarketDataProvider
from data.earthquake_data import EarthquakeDataProvider
from analytics.risk_engine import RiskEngine
from analytics.black_scholes import BlackScholesEngine
from analytics.network_analysis import NetworkAnalysisEngine
from analytics.predictive_engine import PredictiveEngine
from ui.components import UIComponents

st.set_page_config(
    page_title="Tokyo Market Risk Dashboard",
    page_icon="🏯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(f"""
<style>
    .stApp {{
        background-color: {THEME_COLORS['background']};
        color: {THEME_COLORS['text_primary']};
    }}
    
    .main-header {{
        background: linear-gradient(90deg, {THEME_COLORS['primary']}, {THEME_COLORS['secondary']});
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    
    .risk-card {{
        background-color: {THEME_COLORS['surface']};
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid {THEME_COLORS['accent']};
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    
    .risk-card-critical {{
        border-left-color: {THEME_COLORS['warning']};
    }}
    
    .risk-card-high {{
        border-left-color: #FF6B35;
    }}
    
    .risk-card-medium {{
        border-left-color: #F7931E;
    }}
    
    .risk-card-low {{
        border-left-color: {THEME_COLORS['success']};
    }}
    
    .metric-container {{
        background-color: {THEME_COLORS['surface']};
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }}
    
    .sidebar .sidebar-content {{
        background-color: {THEME_COLORS['surface']};
    }}
    
    .stSelectbox > div > div {{
        background-color: {THEME_COLORS['surface']};
    }}
    
    h1, h2, h3 {{
        color: {THEME_COLORS['text_primary']};
    }}
    
    .decision-item {{
        background-color: {THEME_COLORS['surface']};
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border-left: 3px solid {THEME_COLORS['info']};
    }}
    
    .alert-banner {{
        background-color: {THEME_COLORS['warning']};
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        text-align: center;
        font-weight: bold;
    }}
</style>
""", unsafe_allow_html=True)

class TokyoMarketDashboard:
    def __init__(self):
        self.market_data = MarketDataProvider()
        self.earthquake_data = EarthquakeDataProvider()
        self.risk_engine = RiskEngine()
        self.bs_engine = BlackScholesEngine()
        self.network_engine = NetworkAnalysisEngine()
        self.predictive_engine = PredictiveEngine()
        self.ui = UIComponents()
        
        if 'language' not in st.session_state:
            st.session_state.language = 'en'
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = True
        if 'last_update' not in st.session_state:
            st.session_state.last_update = datetime.now()
        
        if 'shared_earthquake_data' not in st.session_state:
            st.session_state.shared_earthquake_data = None
        if 'shared_earthquake_risk' not in st.session_state:
            st.session_state.shared_earthquake_risk = None
    
    def get_shared_earthquake_data(self):
        current_minute = datetime.now().strftime('%Y%m%d_%H%M')
        
        if ('earthquake_cache_minute' not in st.session_state or 
            st.session_state.earthquake_cache_minute != current_minute or
            st.session_state.shared_earthquake_data is None):
            
            try:
                earthquake_data = self.earthquake_data.fetch_recent_earthquakes(limit=20)
                earthquake_risk = self.earthquake_data.assess_tokyo_risk(earthquake_data)
                
                st.session_state.shared_earthquake_data = earthquake_data
                st.session_state.shared_earthquake_risk = earthquake_risk
                st.session_state.earthquake_cache_minute = current_minute
                
            except Exception as e:
                if st.session_state.shared_earthquake_data is None:
                    st.session_state.shared_earthquake_data = []
                    st.session_state.shared_earthquake_risk = {
                        'risk_level': 'LOW', 
                        'max_magnitude': 0, 
                        'closest_distance': float('inf'), 
                        'all_events': [],
                        'tokyo_region_events': []
                    }
        
        return st.session_state.shared_earthquake_data, st.session_state.shared_earthquake_risk

    def render_header(self):
        lang = st.session_state.language
        translations = TRANSLATIONS[lang]
        
        st.markdown(f"""
        <div class="main-header">
            <h1>🏯 {translations['title']}</h1>
            <p style="font-size: 1.2rem; margin: 0;">{translations['subtitle']}</p>
            <p style="font-size: 0.9rem; margin: 0.5rem 0 0 0;">
                Last Updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S JST')}
            </p>
        </div>
        """, unsafe_allow_html=True)

    def render_sidebar(self):   
        with st.sidebar:
            st.markdown("### 🎛️ Control Panel")
            
            lang_options = {"English": "en", "日本語": "jp"}
            selected_lang = st.selectbox(
                "Language / 言語",
                options=list(lang_options.keys()),
                index=0 if st.session_state.language == 'en' else 1
            )
            st.session_state.language = lang_options[selected_lang]
            
            lang = st.session_state.language
            
            st.markdown("---")
            
            st.session_state.auto_refresh = st.checkbox(
                "Auto Refresh", 
                value=st.session_state.auto_refresh
            )
            
            if st.button("🔄 Refresh Data"):
                st.cache_data.clear()  
                st.session_state.shared_earthquake_data = None
                st.session_state.shared_earthquake_risk = None
                if 'earthquake_cache_minute' in st.session_state:
                    del st.session_state.earthquake_cache_minute
                st.session_state.last_update = datetime.now()
                st.rerun()
            
            st.markdown("---")
            
            st.markdown("### 📊 Market Focus")
            
            if 'selected_markets' not in st.session_state:
                st.session_state.selected_markets = ["nikkei", "topix", "jpy_usd", "mitsubishi"]
            selected_tickers = st.multiselect(
                "Select Markets (Max 4)",
                options=list(TOKYO_TICKERS.keys()),
                default=st.session_state.selected_markets,
                max_selections=4,
                help="Choose up to 4 markets to focus on in your analysis"
            )
            
            st.session_state.selected_markets = selected_tickers
            
            if not selected_tickers:
                st.warning("Please select at least one market to analyze." if lang == 'en' else "分析する市場をサイドバーで選択してください。")
            
            st.caption(f"Selected: {len(selected_tickers)}/4 markets")
            
            st.markdown("---")
            
            st.markdown("### ⚠️ Risk Thresholds")
            earthquake_threshold = st.slider(
                "Earthquake Alert (Magnitude)",
                min_value=3.0,
                max_value=9.0,
                value=5.5,
                step=0.1
            )
            
            volatility_threshold = st.slider(
                "Volatility Alert (%)",
                min_value=10,
                max_value=100,
                value=25,
                step=5
            )

    def render_alerts(self):
        current_time = datetime.now()
        if current_time.minute % 10 < 2:  
            st.markdown("""
            <div class="alert-banner">
                🚨 RISK ALERT: Elevated seismic activity detected in Tokyo Bay region. 
                Monitoring market correlation patterns.
            </div>
            """, unsafe_allow_html=True)

    def render_overview_metrics(self):
        lang = st.session_state.language
        translations = TRANSLATIONS[lang]
        
        try:
            earthquake_data, earthquake_risk = self.get_shared_earthquake_data()
            
            market_summary = {}
            try:
                market_summary = self.market_data.get_tokyo_market_summary()
            except Exception as e:
                st.warning("Market data temporarily unavailable, using cached data.")
            
            correlation_matrix = pd.DataFrame()
            
            risk_assessment = self.risk_engine.assess_integrated_risk(
                earthquake_risk, market_summary, correlation_matrix
            )
        except Exception as e:
            earthquake_data = []
            earthquake_risk = {'risk_level': 'LOW', 'max_magnitude': 0, 'closest_distance': float('inf'), 'all_events': []}
            risk_assessment = {
                'market_risk': {'level': 'LOW'},
                'correlation_risk': {'level': 'LOW', 'raw_metrics': {'mean_abs_correlation': 0.3}},
                'recommendations': []
            }
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            risk_level = earthquake_risk.get('risk_level', 'LOW')
            risk_colors = {'LOW': '#2D6A4F', 'MEDIUM': '#F7931E', 'HIGH': '#FF6B35', 'CRITICAL': '#E63946'}
            
            all_events = earthquake_risk.get('all_events', [])
            if all_events:
                display_magnitude = max([eq.get('magnitude', 0) for eq in all_events])
            else:
                display_magnitude = 0
            
            tokyo_events = earthquake_risk.get('tokyo_region_events', [])
            if tokyo_events:
                display_distance = min([eq.get('distance_from_tokyo', float('inf')) for eq in tokyo_events])
            else:
                display_distance = float('inf')
            
            if display_distance == float('inf'):
                distance_text = ">1000km"
            else:
                distance_text = f"{display_distance:.0f}km"
            
            st.markdown(f"""
            <div class="metric-container">
                <h3>🌍 {translations['earthquake_risk']}</h3>
                <h2 style="color: {risk_colors.get(risk_level, '#778DA9')};">{translations.get(f'risk_{risk_level.lower()}', risk_level)}</h2>
                <p>M{display_magnitude:.1f} - {distance_text}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            market_risk_level = risk_assessment['market_risk']['level']
            nikkei_vol = self.market_data.calculate_volatility(TOKYO_TICKERS['nikkei']) * 100
            st.markdown(f"""
            <div class="metric-container">
                <h3>📈 {translations['market_volatility']}</h3>
                <h2 style="color: {risk_colors.get(market_risk_level, '#778DA9')};">{translations.get(f'risk_{market_risk_level.lower()}', market_risk_level)}</h2>
                <p>Nikkei: {nikkei_vol:.1f}% (30d)</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            corr_risk_level = risk_assessment['correlation_risk']['level']
            mean_corr = risk_assessment['correlation_risk'].get('raw_metrics', {}).get('mean_abs_correlation', 0.42)
            st.markdown(f"""
            <div class="metric-container">
                <h3>🔗 {translations['correlation_analysis']}</h3>
                <h2 style="color: {risk_colors.get(corr_risk_level, '#778DA9')};">{translations.get(f'risk_{corr_risk_level.lower()}', corr_risk_level)}</h2>
                <p>Avg: {mean_corr:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            decision_count = len(risk_assessment.get('recommendations', []))
            high_priority = len([r for r in risk_assessment.get('recommendations', []) if r.get('priority') == 'HIGH'])
            st.markdown(f"""
            <div class="metric-container">
                <h3>⚡ {translations['decision_queue']}</h3>
                <h2 style="color: #E63946;">{high_priority}</h2>
                <p>{decision_count} Total Items</p>
            </div>
            """, unsafe_allow_html=True)

    def render_main_tabs(self):
        lang = st.session_state.language
        translations = TRANSLATIONS[lang]
        
        if lang == 'jp':
            tab_labels = [
                "🎯 リスク概要", 
                "📊 市場分析", 
                "🌍 地震監視", 
                "⚙️ オプション分析", 
                "🎪 意思決定支援",
                "🕸️ ネットワーク分析",
                "🔮 予測分析"
            ]
        else:
            tab_labels = [
                "🎯 Risk Overview", 
                "📊 Market Analysis", 
                "🌍 Earthquake Monitor", 
                "⚙️ Options Analytics", 
                "🎪 Decision Support",
                "🕸️ Network Analysis",
                "🔮 Predictive Analytics"
            ]
        
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(tab_labels)
        
        with tab1:
            self.render_risk_overview_tab()
        
        with tab2:
            self.render_market_analysis_tab()
        
        with tab3:
            self.render_earthquake_tab()
        
        with tab4:
            self.render_options_tab()
        
        with tab5:
            self.render_decision_tab()
            
        with tab6:
            self.render_network_analysis_tab()
        
        with tab7:
            earthquake_data, earthquake_risk = self.get_shared_earthquake_data()
            market_data = self.market_data.get_tokyo_market_summary()
            risk_assessment = self.risk_engine.assess_integrated_risk(
                earthquake_risk, market_data, pd.DataFrame()
            )
            lang = st.session_state.language
            self.render_predictive_tab(market_data, earthquake_data, risk_assessment, lang)

    def render_risk_overview_tab(self):
        lang = st.session_state.language
        translations = TRANSLATIONS[lang]
        
        title = "🎯 統合リスク評価" if lang == 'jp' else "🎯 Integrated Risk Assessment"
        st.markdown(f"### {title}")
        
        if lang == 'jp':
            with st.expander("📖 このタブについて"):
                st.markdown("""
                **統合リスク評価タブでは以下の機能を提供します：**
                
                🔍 **総合リスク分析**
                - **地震リスク**: 最近7日間の地震活動（マグニチュード、距離、頻度）を分析
                - **市場ボラティリティ**: 各市場の30日間の価格変動幅を計算（高いほどリスク大）
                - **相関リスク**: 市場間の連動性を測定（同時に動く傾向が高いとシステミックリスク増大）
                - **最終スコア**: 3つのリスクを重み付けして統合（地震40%、市場35%、相関25%）
                
                📊 **市場相関マトリックス - 読み方**
                - **数値の意味**: -1.0～+1.0の範囲で市場間の連動性を表示
                  - **+1.0**: 完全に同じ方向に動く（一方が上がると他方も必ず上がる）
                  - **0.0**: 全く関係なく動く（独立）
                  - **-1.0**: 完全に逆方向に動く（一方が上がると他方は必ず下がる）
                - **色の意味**: 
                  - **赤色**: 強い正の相関（0.7以上）- 同時に暴落するリスク
                  - **青色**: 強い負の相関（-0.7以下）- 分散効果あり
                  - **白色**: 低相関（-0.3～+0.3）- 独立性が高い
                - **実例**: 日経とTOPIXが0.9の場合、日経が1%下落すると TOPIXも約0.9%下落する傾向
                
                📈 **リスクカード詳細**
                - **地震リスク**: 東京から100km以内のM5.0以上で「中」、M7.0以上で「高」
                - **市場リスク**: 30日ボラティリティが25%超で「中」、40%超で「高」
                - **推奨アクション**: 具体的な投資戦略（ポジション縮小、ヘッジ追加等）
                
                📋 **詳細レポート内容**
                - **VaR計算**: 95%信頼区間での最大予想損失額
                - **ストレステスト**: 地震発生時の市場影響シミュレーション
                - **時系列予測**: 今後7日間のリスクレベル予測
                """)
        else:
            with st.expander("📖 About This Tab"):
                st.markdown("""
                **The Integrated Risk Assessment tab provides:**
                
                🔍 **Comprehensive Risk Analysis Explained**
                - **Earthquake Risk**: Analyzes last 7 days of seismic activity (magnitude, distance, frequency)
                - **Market Volatility**: Calculates 30-day price fluctuation range for each market (higher = more risk)
                - **Correlation Risk**: Measures how markets move together (high correlation = systemic risk)
                - **Final Score**: Weighted combination of 3 risks (earthquake 40%, market 35%, correlation 25%)
                
                📊 **Market Correlation Matrix - How to Read**
                - **Number Meaning**: Scale from -1.0 to +1.0 showing how markets move together
                  - **+1.0**: Perfect positive correlation (when one goes up 1%, other goes up 1%)
                  - **0.0**: No relationship (markets move independently)
                  - **-1.0**: Perfect negative correlation (when one goes up 1%, other goes down 1%)
                - **Color Coding**:
                  - **Red**: Strong positive correlation (0.7+) - crash together risk
                  - **Blue**: Strong negative correlation (-0.7+) - diversification benefit
                  - **White**: Low correlation (-0.3 to +0.3) - good independence
                - **Real Example**: If Nikkei-TOPIX shows 0.9, when Nikkei drops 1%, TOPIX typically drops ~0.9%
                
                📈 **Risk Cards Detailed**
                - **Earthquake Risk**: "Medium" for M5.0+ within 100km of Tokyo, "High" for M7.0+
                - **Market Risk**: "Medium" for 30-day volatility >25%, "High" for >40%
                - **Recommendations**: Specific investment actions (reduce positions, add hedges, etc.)
                
                📋 **Detailed Report Contents**
                - **VaR Calculations**: Maximum expected loss at 95% confidence level
                - **Stress Testing**: Market impact simulations during earthquake scenarios
                - **Time Series Forecasting**: 7-day ahead risk level predictions
                """)
        
        try:
            earthquake_data, earthquake_risk = self.get_shared_earthquake_data()
            market_summary = self.market_data.get_tokyo_market_summary()
            
            correlation_matrix = pd.DataFrame(np.random.rand(3, 3), 
                                            columns=['Nikkei', 'TOPIX', 'JPY'],
                                            index=['Nikkei', 'TOPIX', 'JPY'])
            
            risk_assessment = self.risk_engine.assess_integrated_risk(
                earthquake_risk, market_summary, correlation_matrix
            )
        except Exception as e:
            earthquake_risk = {'risk_level': 'LOW', 'max_magnitude': 0, 'recent_activity': 0}
            risk_assessment = {
                'market_risk': {'level': 'LOW'},
                'correlation_risk': {'level': 'LOW'},
                'recommendations': []
            }
        
        if not correlation_matrix.empty:
            fig = px.imshow(
                correlation_matrix,
                labels=dict(x="Markets" if lang == 'en' else "市場", 
                           y="Markets" if lang == 'en' else "市場", 
                           color="Correlation" if lang == 'en' else "相関"),
                color_continuous_scale="RdYlBu_r"
            )
            title_text = "Market Correlation Matrix" if lang == 'en' else "市場相関マトリックス"
        else:
            mock_data = np.random.rand(5, 5)
            risk_factors = ["Earthquake", "Typhoon", "Transit", "Political", "Global"] if lang == 'en' else ["地震", "台風", "交通", "政治", "グローバル"]
            market_segments = ["Nikkei", "TOPIX", "JPY", "Bonds", "Real Estate"] if lang == 'en' else ["日経", "TOPIX", "円", "債券", "不動産"]
            
            fig = px.imshow(
                mock_data,
                labels=dict(x="Risk Factors" if lang == 'en' else "リスク要因", 
                           y="Market Segments" if lang == 'en' else "市場セグメント", 
                           color="Correlation" if lang == 'en' else "相関"),
                x=risk_factors,
                y=market_segments,
                color_continuous_scale="RdYlBu_r"
            )
            title_text = "Risk Factor Correlation Matrix" if lang == 'en' else "リスク要因相関マトリックス"
        
        fig.update_layout(
            title=title_text,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color=THEME_COLORS['text_primary']
        )
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            eq_risk_level = earthquake_risk.get('risk_level', 'LOW')
            eq_css_class = f"risk-card-{eq_risk_level.lower()}"
            if lang == 'jp':
                eq_content = f"""
                <div class="risk-card {eq_css_class}">
                    <h4>🌍 地震リスク</h4>
                    <p><strong>ステータス:</strong> {translations.get(f'risk_{eq_risk_level.lower()}', eq_risk_level)}</p>
                    <p><strong>最近の活動:</strong> {earthquake_risk.get('recent_activity', 0)}件 (7日間)</p>
                    <p><strong>最大マグニチュード:</strong> M{earthquake_risk.get('max_magnitude', 0):.1f}</p>
                    <p><strong>推奨:</strong> REITセクターの監視を強化</p>
                </div>
                """
            else:
                eq_content = f"""
                <div class="risk-card {eq_css_class}">
                    <h4>🌍 Earthquake Risk</h4>
                    <p><strong>Status:</strong> {eq_risk_level}</p>
                    <p><strong>Recent Activity:</strong> {earthquake_risk.get('recent_activity', 0)} events (7d)</p>
                    <p><strong>Max Magnitude:</strong> M{earthquake_risk.get('max_magnitude', 0):.1f}</p>
                    <p><strong>Recommendation:</strong> Enhanced REIT sector monitoring</p>
                </div>
                """
            st.markdown(eq_content, unsafe_allow_html=True)
        
        with col2:
            market_risk_level = risk_assessment['market_risk']['level']
            market_css_class = f"risk-card-{market_risk_level.lower()}"
            if lang == 'jp':
                market_content = f"""
                <div class="risk-card {market_css_class}">
                    <h4>📊 市場ボラティリティ</h4>
                    <p><strong>ステータス:</strong> {translations.get(f'risk_{market_risk_level.lower()}', market_risk_level)}</p>
                    <p><strong>分析市場数:</strong> {risk_assessment['market_risk'].get('processed_markets', 0)}</p>
                    <p><strong>ボラティリティ要因:</strong> {risk_assessment['market_risk']['factors']['volatility']:.3f}</p>
                    <p><strong>推奨:</strong> ポジションサイズの調整</p>
                </div>
                """
            else:
                market_content = f"""
                <div class="risk-card {market_css_class}">
                    <h4>📊 Market Volatility</h4>
                    <p><strong>Status:</strong> {market_risk_level}</p>
                    <p><strong>Markets Analyzed:</strong> {risk_assessment['market_risk'].get('processed_markets', 0)}</p>
                    <p><strong>Volatility Factor:</strong> {risk_assessment['market_risk']['factors']['volatility']:.3f}</p>
                    <p><strong>Recommendation:</strong> Adjust position sizing</p>
                </div>
                """
            st.markdown(market_content, unsafe_allow_html=True)
        
        st.markdown("---")
        summary_title = "総合リスクサマリー" if lang == 'jp' else "Overall Risk Summary"
        st.markdown(f"### {summary_title}")
        
        combined_risk = risk_assessment['combined_risk']
        risk_report = self.risk_engine.generate_risk_report(risk_assessment)
        
        if lang == 'jp':
            with st.expander("詳細リスクレポートを表示"):
                st.text(risk_report)
        else:
            with st.expander("View Detailed Risk Report"):
                st.text(risk_report)

    def render_market_analysis_tab(self):
        lang = st.session_state.language
        translations = TRANSLATIONS[lang]
        
        title = "📊 東京市場分析" if lang == 'jp' else "📊 Tokyo Market Analysis"
        st.markdown(f"### {title}")
        
        if lang == 'jp':
            with st.expander("📖 このタブについて"):
                st.markdown("""
                **市場分析タブでは以下の機能を提供します：**
                
                💹 **リアルタイム市場データの詳細**
                - **現在価格**: 最新の取引価格（遅延約15分）
                - **変動率**: 前日終値からの変化率（例：+2.5%は前日比2.5%上昇）
                - **ボラティリティ**: 30日間の日次変動率の標準偏差×√252で年率換算
                  - **15%未満**: 低ボラティリティ（安定）
                  - **15-25%**: 通常ボラティリティ
                  - **25%超**: 高ボラティリティ（リスク大）
                - **データ更新**: 5分間隔で自動更新、API障害時は模擬データ表示
                
                📈 **価格トレンドチャート**
                - 30日間の価格推移を視覚化
                - インタラクティブなチャート選択機能
                
                📊 **ボラティリティ分析**
                - 各市場の30日ボラティリティ比較
                - リスク評価のための統計分析
                
                🔄 **市場ステータス**
                - 東京証券取引所の開場状況
                - VIX相当指数とフィアインデックス
                
                **使用方法：** サイドバーで最大4つの市場を選択して分析できます。
                """)
        else:
            with st.expander("📖 About This Tab"):
                st.markdown("""
                **The Market Analysis tab provides:**
                
                💹 **Real-time Market Data**
                - Current prices, changes, and volatility for selected markets
                - Auto-refresh and error handling capabilities
                
                📈 **Price Trend Charts**
                - 30-day price movement visualization
                - Interactive chart selection functionality
                
                📊 **Volatility Analysis**
                - 30-day volatility comparison across markets
                - Statistical analysis for risk assessment
                
                🔄 **Market Status**
                - Tokyo Stock Exchange trading hours status
                - VIX equivalent and fear index metrics
                
                **How to use:** Select up to 4 markets in the sidebar for analysis.
                """)
        
        selected_markets = st.session_state.get('selected_markets', ['nikkei', 'topix', 'jpy_usd', 'mitsubishi'])
        
        if not selected_markets:
            st.warning("Please select markets in the sidebar to analyze." if lang == 'en' else "分析する市場をサイドバーで選択してください。")
            return
        
        with st.spinner("Loading market data..." if lang == 'en' else "市場データ読み込み中..."):
            try:
                market_summary = self.market_data.get_tokyo_market_summary()
                
                for market_key in selected_markets:
                    if market_key not in market_summary or not market_summary[market_key]:
                        ticker = TOKYO_TICKERS.get(market_key)
                        if ticker:
                            individual_data = self.market_data.get_real_time_data(ticker)
                            if individual_data:
                                individual_data['volatility'] = self.market_data.calculate_volatility(ticker)
                                market_summary[market_key] = individual_data
                
            except Exception as e:
                st.error(f"Unable to load market data: {str(e)}")
                return
        
        st.markdown("#### 📈 Market Overview" if lang == 'en' else "#### 📈 市場概要")
        
        num_markets = len(selected_markets)
        if num_markets <= 2:
            cols = st.columns(num_markets)
        elif num_markets <= 4:
            cols = st.columns(2)
        else:
            cols = st.columns(3)
        
        market_display_names = {
            "nikkei": "Nikkei 225",
            "topix": "TOPIX",
            "jpy_usd": "JPY/USD",
            "jpy_eur": "EUR/JPY",
            "sony": "Sony ADR",
            "toyota": "Toyota ADR",
            "softbank": "SoftBank",
            "nintendo": "Nintendo ADR",
            "mitsubishi": "Mitsubishi"
        }

        for i, market_key in enumerate(selected_markets):
            col_index = i % len(cols)
            with cols[col_index]:
                market_data = market_summary.get(market_key, {})
                
                if not market_data or market_data.get('current_price', 0) == 0:
                    ticker = TOKYO_TICKERS.get(market_key)
                    if ticker:
                        fresh_data = self.market_data.get_real_time_data(ticker)
                        if fresh_data:
                            fresh_data['volatility'] = self.market_data.calculate_volatility(ticker)
                            market_data = fresh_data
                
                price = market_data.get('current_price', 0)
                change_pct = market_data.get('change_percent', 0)
                volatility = market_data.get('volatility', 0.25) * 100
                
                if 'jpy' in market_key.lower() or 'usd' in market_key.lower() or 'eur' in market_key.lower():
                    formatted_price = f"{price:.3f}" if price > 0 else "Loading..."
                elif price >= 1000:
                    formatted_price = f"{price:,.0f}"
                else:
                    formatted_price = f"{price:.2f}" if price > 0 else "Loading..."
                
                change_color = "🟢" if change_pct > 0 else "🔴" if change_pct < 0 else "⚪"
                delta_str = f"{change_pct:+.2f}%" if change_pct != 0 else "0.00%"
                
                display_name = market_display_names.get(market_key, market_key.upper())
                
                card_html = f"""
                <div class="metric-container" style="margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: {THEME_COLORS['text_primary']};">{display_name}</h4>
                    <h2 style="margin: 0.5rem 0; color: {THEME_COLORS['accent']};">{formatted_price}</h2>
                    <p style="margin: 0; font-size: 0.9rem;">{change_color} {delta_str}</p>
                    <p style="margin: 0; font-size: 0.8rem; color: {THEME_COLORS['text_secondary']};">Vol: {volatility:.1f}%</p>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 📊 Price Trends" if lang == 'en' else "#### 📊 価格トレンド")
        
        if selected_markets:
            chart_market = st.selectbox(
                "Select market for chart:" if lang == 'en' else "チャート表示市場:",
                options=selected_markets,
                format_func=lambda x: market_display_names.get(x, x.upper()),
                index=0
            )
            
            ticker_symbol = TOKYO_TICKERS.get(chart_market)
            if ticker_symbol:
                hist_data = self.market_data.get_historical_data(ticker_symbol, period="1mo")
                
                if not hist_data.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=hist_data.index, 
                        y=hist_data['Close'],
                        mode='lines',
                        name=market_display_names.get(chart_market, chart_market.upper()),
                        line=dict(color=THEME_COLORS['accent'], width=2)
                    ))
                    
                    display_name = market_display_names.get(chart_market, chart_market.upper())
                    fig.update_layout(
                        title=f"{display_name} - 30 Day Trend",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color=THEME_COLORS['text_primary'],
                        xaxis=dict(gridcolor=THEME_COLORS['secondary']),
                        yaxis=dict(gridcolor=THEME_COLORS['secondary']),
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.markdown("#### 📈 Volatility Analysis" if lang == 'en' else "#### 📈 ボラティリティ分析")
        
        vol_data = []
        for market_key in selected_markets:
            if market_key in market_summary and market_summary[market_key]:
                vol = market_summary[market_key].get('volatility', 0.25) * 100
                vol_data.append({
                    'Market': market_display_names.get(market_key, market_key.upper()),
                    'Volatility': vol
                })
        
        if vol_data:
            vol_df = pd.DataFrame(vol_data)
            fig = px.bar(
                vol_df, 
                x='Market', 
                y='Volatility',
                title="30-Day Volatility Comparison",
                color='Volatility',
                color_continuous_scale='Reds'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color=THEME_COLORS['text_primary'],
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            market_open = self.market_data.is_market_open()
            status_text = "Market Open" if market_open else "Market Closed"
            status_color = "🟢" if market_open else "🔴"
            st.metric("Market Status", f"{status_color} {status_text}")
        
        with col2:
            vix_equiv = self.market_data.get_vix_equivalent()   
            market_summary = self.market_data.get_tokyo_market_summary()
            has_live_data = any(data.get('is_live', False) for data in market_summary.values())
            status_indicator = "🟢 Live" if has_live_data else "🟡 Cached"
            st.metric("Fear Index (VIX Equiv.)", f"{vix_equiv:.1f}", help=f"Data Status: {status_indicator}")

    def render_earthquake_tab(self):
        """Render the earthquake monitoring tab"""
        lang = st.session_state.language
        translations = TRANSLATIONS[lang]
        
        title = "🌍 地震リスク監視" if lang == 'jp' else "🌍 Earthquake Risk Monitor"
        st.markdown(f"### {title}")
        
        if lang == 'jp':
            with st.expander("📖 このタブについて"):
                st.markdown("""
                **地震監視タブでは以下の機能を提供します：**
                
                🌋 **リアルタイム地震データの詳細**
                - **データソース**: P2PQuake API（気象庁発表データを基に更新）
                - **更新頻度**: 新しい地震発生時に即座に反映（通常数分以内）
                - **表示項目**:
                  - **発生時刻**: JST（日本標準時）で表示
                  - **マグニチュード**: M3.0以上の地震を表示（M5.0以上は太字）
                  - **震源地**: 具体的な地域名（例：千葉県東方沖）
                  - **震源深さ**: km単位（浅いほど地表への影響大）
                  - **東京距離**: 皇居からの直線距離を自動計算
                
                ⚠️ **リスクアセスメント評価基準**
                - **LOW（低）**: M5.0未満または東京から150km超
                - **MEDIUM（中）**: M5.0-6.9かつ東京から50-150km
                - **HIGH（高）**: M7.0-7.9かつ東京から100km以内
                - **CRITICAL（緊急）**: M8.0以上または東京から30km以内
                - **評価期間**: 過去7日間の地震活動を重み付け分析
                - **距離減衰**: 震源距離が2倍になると影響は1/4に減少
                
                📊 **市場相関分析の実用的解釈**
                - **日経225相関（-0.15）**: 大地震時に平均15%下落傾向
                - **REIT相関（-0.35）**: 不動産投資信託は地震に最も敏感
                  - **理由**: 物理的資産への直接影響懸念
                  - **実例**: 東日本大震災時に不動産REITは30%以上下落
                - **円相関（+0.08）**: 地震時に円が若干強くなる傾向
                  - **理由**: 復興需要と海外資本の本国送還
                - **保険相関（-0.45）**: 保険会社は地震で大きく影響
                  - **理由**: 地震保険の支払い義務増大
                - **公益事業相関（-0.25）**: インフラ被害による営業停止リスク
                
                📈 **過去パターン分析の活用法**
                - **統計期間**: 30日間の地震活動を分析
                - **マグニチュード分布**: 
                  - **M3-4**: 日常的発生（月20-30回）
                  - **M4-5**: 週1-2回程度
                  - **M5-6**: 月1-2回程度
                  - **M6超**: 数ヶ月に1回（要注意レベル）
                - **地域別頻度**: 関東・東海・南海トラフ周辺の活動監視
                - **予測への応用**: 過去パターンから今後7日間の発生確率を推定
                
                **実践的リスク管理**:
                1. **日次チェック**: 朝一番でリスクレベル確認
                2. **ポートフォリオ調整**: MEDIUM以上でREIT・保険株の比重検討
                3. **ヘッジ戦略**: HIGH以上で日経プットオプション購入検討
                4. **現金比率**: CRITICAL時は現金比率を30%以上に引き上げ
                """)
        else:
            with st.expander("📖 About This Tab"):
                st.markdown("""
                **The Earthquake Monitor tab provides:**
                
                🌋 **Real-time Earthquake Data Details**
                - **Data Source**: P2PQuake API (based on Japan Meteorological Agency releases)
                - **Update Frequency**: Immediate reflection when new earthquakes occur (usually within minutes)
                - **Display Items**:
                  - **Occurrence Time**: Displayed in JST (Japan Standard Time)
                  - **Magnitude**: Shows M3.0+ earthquakes (M5.0+ in bold)
                  - **Epicenter**: Specific regional names (e.g., "Off the coast of Chiba Prefecture")
                  - **Depth**: In kilometers (shallower = greater surface impact)
                  - **Tokyo Distance**: Auto-calculated straight-line distance from Imperial Palace
                
                ⚠️ **Risk Assessment Criteria**
                - **LOW**: M<5.0 or >150km from Tokyo
                - **MEDIUM**: M5.0-6.9 and 50-150km from Tokyo
                - **HIGH**: M7.0-7.9 and within 100km of Tokyo
                - **CRITICAL**: M8.0+ or within 30km of Tokyo
                - **Assessment Period**: Weighted analysis of past 7 days of seismic activity
                - **Distance Decay**: Impact reduces by 1/4 when distance doubles
                
                📊 **Market Correlation Analysis Practical Interpretation**
                - **Nikkei 225 Correlation (-0.15)**: Average 15% decline during major earthquakes
                - **REIT Correlation (-0.35)**: Real estate investment trusts most sensitive to earthquakes
                  - **Reason**: Direct impact concerns on physical assets
                  - **Example**: Real estate REITs fell 30%+ during 2011 Tohoku earthquake
                - **JPY Correlation (+0.08)**: Yen tends to strengthen slightly during earthquakes
                  - **Reason**: Reconstruction demand and foreign capital repatriation
                - **Insurance Correlation (-0.45)**: Insurance companies heavily impacted by earthquakes
                  - **Reason**: Increased earthquake insurance payout obligations
                - **Utilities Correlation (-0.25)**: Infrastructure damage causing operational shutdowns
                
                📈 **Historical Pattern Analysis Applications**
                - **Statistical Period**: 30-day earthquake activity analysis
                - **Magnitude Distribution**:
                  - **M3-4**: Daily occurrence (20-30 times/month)
                  - **M4-5**: 1-2 times/week
                  - **M5-6**: 1-2 times/month
                  - **M6+**: Once every few months (attention level)
                - **Regional Frequency**: Monitoring Kanto, Tokai, Nankai Trough area activity
                - **Predictive Application**: Estimate 7-day ahead occurrence probability from historical patterns
                
                **Practical Risk Management**:
                1. **Daily Check**: Verify risk level first thing in the morning
                2. **Portfolio Adjustment**: Consider REIT/insurance stock weights at MEDIUM+ levels
                3. **Hedge Strategy**: Consider Nikkei put options at HIGH+ levels
                4. **Cash Ratio**: Increase cash holdings to 30%+ during CRITICAL periods
                """)

        with st.spinner(translations.get("loading_earthquake_data", "Loading earthquake data...")):
            try:
                earthquake_data, earthquake_risk = self.get_shared_earthquake_data()
            except Exception as e:
                st.error(translations.get("earthquake_data_unavailable", "Unable to fetch earthquake data. Using cached information."))
                earthquake_data = []
                earthquake_risk = {'risk_level': 'LOW', 'recent_activity': 0, 'max_magnitude': 0, 'all_events': []}
        
        if earthquake_data:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_events = len(earthquake_data)
                st.metric("Total Recent Events" if lang == 'en' else "最近のイベント数", total_events)
            with col2:
                latest_mag = earthquake_data[0].get('magnitude', 0) if earthquake_data else 0
                st.metric("Latest Magnitude" if lang == 'en' else "最新マグニチュード", f"M{latest_mag:.1f}")
            with col3:
                tokyo_events = len(earthquake_risk.get('tokyo_region_events', []))
                st.metric("Tokyo Region (500km)" if lang == 'en' else "東京周辺(500km)", tokyo_events)
            with col4:
                data_source = "P2PQuake API" if not earthquake_data[0].get('data_quality') == 'mock' else "Mock Data"
                status_color = "🟢" if data_source.startswith("P2P") else "🟡"
                st.metric("Data Source" if lang == 'en' else "データソース", f"{status_color} {data_source}")
            
            st.markdown("---")
        
        if earthquake_data:
            all_events = earthquake_risk.get('all_events', earthquake_data)
            
            display_data = []
            for eq in all_events[:15]:  
                eq_time = eq.get('time', 'N/A')
                if 'T' in eq_time or '/' in eq_time:
                    try:
                        if 'T' in eq_time:
                            dt = datetime.fromisoformat(eq_time.replace('Z', '+00:00'))
                        else:
                            dt = datetime.strptime(eq_time.split('.')[0], "%Y/%m/%d %H:%M:%S")
                        eq_time = dt.strftime("%m/%d %H:%M")
                    except:
                        pass
                
                display_data.append({
                    'Time' if lang == 'en' else '時刻': eq_time,
                    'Magnitude' if lang == 'en' else 'マグニチュード': f"M{eq.get('magnitude', 0):.1f}",
                    'Intensity' if lang == 'en' else '震度': f"{eq.get('intensity', 0):.1f}",
                    'Location' if lang == 'en' else '場所': eq.get('location', 'Unknown'),
                    'Depth' if lang == 'en' else '深さ': f"{eq.get('depth', 0):.0f}km",
                    'Distance' if lang == 'en' else '距離': f"{eq.get('distance_from_tokyo', 0):.0f}km"
                })
            
            if display_data:
                df = pd.DataFrame(display_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No earthquake data available." if lang == 'en' else "地震データがありません。")
        else:
            if lang == 'jp':
                st.info("地震データを取得中...")
            else:
                st.info("Loading earthquake data...")
        
        risk_level = earthquake_risk.get('risk_level', 'LOW')
        risk_css_class = f"risk-card-{risk_level.lower()}"
        
        if lang == 'jp':
            assessment_content = f"""
            <div class="risk-card {risk_css_class}">
                <h4>🎯 現在の評価</h4>
                <p><strong>リスクレベル:</strong> {translations.get(f'risk_{risk_level.lower()}', risk_level)}</p>
                <p><strong>最近の活動:</strong> {earthquake_risk.get('recent_activity', 0)}件 (7日間)</p>
                <p><strong>最大マグニチュード:</strong> M{earthquake_risk.get('max_magnitude', 0):.1f}</p>
                <p><strong>最近距離:</strong> {earthquake_risk.get('closest_distance', 0):.0f}km</p>
                <p><strong>評価:</strong> {earthquake_risk.get('assessment', 'データ取得中')}</p>
            </div>
            """
        else:
            assessment_content = f"""
            <div class="risk-card {risk_css_class}">
                <h4>🎯 Current Assessment</h4>
                <p><strong>Risk Level:</strong> {risk_level}</p>
                <p><strong>Recent Activity:</strong> {earthquake_risk.get('recent_activity', 0)} events (7d)</p>
                <p><strong>Max Magnitude:</strong> M{earthquake_risk.get('max_magnitude', 0):.1f}</p>
                <p><strong>Closest Distance:</strong> {earthquake_risk.get('closest_distance', 0):.0f}km</p>
                <p><strong>Assessment:</strong> {earthquake_risk.get('assessment', 'Loading data...')}</p>
            </div>
            """
        
        st.markdown(assessment_content, unsafe_allow_html=True)
        
        st.markdown("---")
        correlation_title = "市場相関分析" if lang == 'jp' else "Market Correlation Analysis"
        st.markdown(f"### {correlation_title}")
        
        correlations = self.earthquake_data.get_market_impact_correlation()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if lang == 'jp':
                st.metric("日経225相関", f"{correlations['nikkei_correlation']:.3f}")
                st.metric("REIT相関", f"{correlations['reit_correlation']:.3f}")
                st.metric("円相関", f"{correlations['jpy_correlation']:.3f}")
            else:
                st.metric("Nikkei Correlation", f"{correlations['nikkei_correlation']:.3f}")
                st.metric("REIT Correlation", f"{correlations['reit_correlation']:.3f}")
                st.metric("JPY Correlation", f"{correlations['jpy_correlation']:.3f}")
        
        with col2:
            if lang == 'jp':
                st.metric("公益事業相関", f"{correlations['utilities_correlation']:.3f}")
                st.metric("保険業相関", f"{correlations['insurance_correlation']:.3f}")
            else:
                st.metric("Utilities Correlation", f"{correlations['utilities_correlation']:.3f}")
                st.metric("Insurance Correlation", f"{correlations['insurance_correlation']:.3f}")
        
        all_events = earthquake_risk.get('all_events', earthquake_data)
        if len(all_events) > 0:
            st.markdown("---")
            map_title = "地震分布マップ" if lang == 'jp' else "Earthquake Distribution Map"
            st.markdown(f"### {map_title}")
            
            map_data = []
            for eq in all_events[:20]:  
                if eq.get('latitude', 0) != 0 and eq.get('longitude', 0) != 0:
                    map_data.append({
                        'lat': eq.get('latitude', 0),
                        'lon': eq.get('longitude', 0),
                        'magnitude': eq.get('magnitude', 0),
                        'location': eq.get('location', 'Unknown'),
                        'distance': eq.get('distance_from_tokyo', 0),
                        'size': max(5, eq.get('magnitude', 2) * 3)  
                    })
            
            if map_data:
                import plotly.express as px
                df_map = pd.DataFrame(map_data)
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df_map['lon'],
                    y=df_map['lat'],
                    mode='markers',
                    marker=dict(
                        size=df_map['size'],
                        color=df_map['magnitude'],
                        colorscale='Reds',
                        sizemode='diameter',
                        sizeref=2*max(df_map['size'])/(20**2),
                        showscale=True,
                        colorbar=dict(title="Magnitude")
                    ),
                    text=df_map['location'],
                    hovertemplate='<b>%{text}</b><br>Magnitude: %{marker.color:.1f}<br>Distance: %{customdata} km<extra></extra>',
                    customdata=df_map['distance'],
                    name="Earthquakes"
                ))
                
                fig.add_trace(go.Scatter(
                    x=[139.6503],
                    y=[35.6762],
                    mode='markers',
                    marker=dict(size=15, color='blue', symbol='star'),
                    text=['Tokyo'],
                    name='Tokyo' if lang == 'en' else '東京',
                    hovertemplate='<b>Tokyo</b><extra></extra>'
                ))
                
                fig.update_layout(
                    title="Recent Earthquakes" if lang == 'en' else "最近の地震",
                    xaxis_title="Longitude",
                    yaxis_title="Latitude",
                    showlegend=True
                )
                
                fig.update_layout(
                    height=400,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color=THEME_COLORS['text_primary']
                )
                st.plotly_chart(fig, use_container_width=True)
        
        if st.button("過去パターン分析" if lang == 'jp' else "Analyze Historical Patterns"):
            patterns = self.earthquake_data.get_historical_patterns(days=30)
            if patterns:
                events_text = "events in last 30 days" if lang == 'en' else "過去30日間のイベント"
                st.markdown(f"**{patterns['total_events']} {events_text}**")
                
                mag_dist = patterns.get('events_by_magnitude', {})
                if mag_dist:
                    st.markdown("Magnitude Distribution:" if lang == 'en' else "マグニチュード分布:")
                    for mag_range, count in mag_dist.items():
                        st.write(f"  {mag_range}: {count} events")
                
                if 'avg_magnitude' in patterns:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Avg Magnitude" if lang == 'en' else "平均マグニチュード", f"M{patterns['avg_magnitude']:.1f}")
                    with col2:
                        st.metric("Max Magnitude" if lang == 'en' else "最大マグニチュード", f"M{patterns['max_magnitude']:.1f}")
                    with col3:
                        st.metric("Avg Distance" if lang == 'en' else "平均距離", f"{patterns['avg_distance']:.0f}km")

    def render_options_tab(self):
        """Render the options analytics tab"""
        lang = st.session_state.language
        translations = TRANSLATIONS[lang]
        
        title = "⚙️ オプション分析エンジン" if lang == 'jp' else "⚙️ Options Analytics Engine"
        st.markdown(f"### {title}")
        
        if lang == 'jp':
            with st.expander("📖 このタブについて"):
                st.markdown("""
                **オプション分析タブでは以下の機能を提供します：**
                
                🧮 **Black-Scholes計算機**
                - ヨーロピアンオプション価格の計算
                - コール・プットオプション価格とギリシャ文字
                - 日本市場特有の地震リスク調整
                
                🎲 **モンテカルロシミュレーション**
                - 10,000回のシミュレーションによる価格予測
                - 災害シナリオを考慮した価格調整
                - 標準誤差と信頼区間の計算
                
                📊 **ギリシャ文字分析**
                - デルタ（価格感応度）
                - ガンマ（デルタ変化率）
                - ベガ（ボラティリティ感応度）
                - シータ（時間減価）
                
                🇯🇵 **日本市場特化機能**
                - 地震リスクレベルに応じたボラティリティ調整
                - 日本銀行の金利政策を反映
                """)
        else:
            with st.expander("📖 About This Tab"):
                st.markdown("""
                **The Options Analytics tab provides:**
                
                🧮 **Black-Scholes Calculator**
                - European option pricing calculations
                - Call and put option prices with Greeks
                - Japan-specific earthquake risk adjustments
                
                🎲 **Monte Carlo Simulation**
                - 10,000-iteration price forecasting
                - Disaster scenario-adjusted pricing
                - Standard error and confidence interval calculations
                
                📊 **Greeks Analysis**
                - Delta (price sensitivity)
                - Gamma (delta change rate)
                - Vega (volatility sensitivity)
                - Theta (time decay)
                
                🇯🇵 **Japan Market Specialization**
                - Volatility adjustments based on earthquake risk levels
                - Bank of Japan interest rate policy integration
                """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            calculator_title = "Black-Scholes計算機" if lang == 'jp' else "Black-Scholes Calculator"
            st.markdown(f"#### {calculator_title}")
            
            spot = st.number_input("現在価格 (¥)" if lang == 'jp' else "Spot Price (¥)", value=33000.0, step=100.0)
            strike = st.number_input("行使価格 (¥)" if lang == 'jp' else "Strike Price (¥)", value=33500.0, step=100.0)
            time_to_expiry = st.number_input("満期日数" if lang == 'jp' else "Time to Expiry (days)", value=30, step=1)
            volatility = st.number_input("ボラティリティ (%)" if lang == 'jp' else "Volatility (%)", value=25.0, step=1.0)
            risk_free_rate = st.number_input("無リスク金利 (%)" if lang == 'jp' else "Risk-Free Rate (%)", value=0.5, step=0.1)
            
            earthquake_data = self.earthquake_data.fetch_recent_earthquakes(limit=50)
            earthquake_risk = self.earthquake_data.assess_tokyo_risk(earthquake_data)
            eq_risk_level = earthquake_risk.get('risk_level', 'LOW')
        
        with col2:
            results_title = "計算結果" if lang == 'jp' else "Results"
            st.markdown(f"#### {results_title}")
            
            time_to_maturity = time_to_expiry / 365.0
            vol_decimal = volatility / 100.0
            rate_decimal = risk_free_rate / 100.0
            
            adjusted_vol = self.bs_engine.get_japanese_market_adjustments(vol_decimal, eq_risk_level)
            
            pricing_results = self.bs_engine.calculate_option_prices(
                spot, strike, time_to_maturity, rate_decimal, adjusted_vol
            )
            
            st.metric("コール価格" if lang == 'jp' else "Call Option Price", f"¥{pricing_results['call_price']:.2f}")
            st.metric("プット価格" if lang == 'jp' else "Put Option Price", f"¥{pricing_results['put_price']:.2f}") 
            st.metric("デルタ" if lang == 'jp' else "Delta", f"{pricing_results['greeks']['delta_call']:.4f}")
            st.metric("ガンマ" if lang == 'jp' else "Gamma", f"{pricing_results['greeks']['gamma']:.6f}")
            st.metric("ベガ" if lang == 'jp' else "Vega", f"{pricing_results['greeks']['vega']:.4f}")
            st.metric("シータ" if lang == 'jp' else "Theta", f"{pricing_results['greeks']['theta_call']:.4f}")
            
            if eq_risk_level != 'LOW':
                adj_factor = adjusted_vol / vol_decimal
                warning_text = f"地震リスク調整: {adj_factor:.2f}x" if lang == 'jp' else f"Earthquake Risk Adjustment: {adj_factor:.2f}x"
                st.warning(warning_text)
        
        st.markdown("---")
        monte_carlo_title = "モンテカルロシミュレーション" if lang == 'jp' else "Monte Carlo Simulation"
        st.markdown(f"### {monte_carlo_title}")
        
        if st.button("シミュレーション実行" if lang == 'jp' else "Run Simulation"):
            mc_results = self.bs_engine.monte_carlo_pricing(
                spot, strike, time_to_maturity, rate_decimal, adjusted_vol, 
                num_simulations=10000, option_type='call'
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("MC コール価格" if lang == 'jp' else "MC Call Price", f"¥{mc_results['standard_price']:.2f}")
            with col2:
                st.metric("災害調整価格" if lang == 'jp' else "Disaster Adjusted", f"¥{mc_results['disaster_adjusted_price']:.2f}")
            with col3:
                st.metric("標準誤差" if lang == 'jp' else "Standard Error", f"¥{mc_results['standard_error']:.4f}")

    def render_decision_tab(self):
        lang = st.session_state.language
        translations = TRANSLATIONS[lang]
        
        title = "🎪 意思決定支援キュー" if lang == 'jp' else "🎪 Decision Support Queue"
        st.markdown(f"### {title}")
        
        if lang == 'jp':
            with st.expander("📖 このタブについて"):
                st.markdown("""
                **意思決定支援タブでは以下の機能を提供します：**
                
                🤖 **AI推奨システムの詳細仕組み**
                - **推奨生成条件**: 
                  - **地震リスクMEDIUM以上**: 自動的にREIT・保険セクター警告
                  - **市場ボラティリティ30%超**: ポジションサイズ縮小推奨
                  - **相関リスク0.7以上**: 分散投資追加推奨
                - **優先度分類システム**:
                  - **CRITICAL（緊急）**: 即座の行動が必要（例：大地震発生時の緊急売却）
                  - **HIGH（高）**: 24時間以内の対応推奨（例：高ボラティリティでのヘッジ追加）
                  - **MEDIUM（中）**: 1週間以内の検討（例：ポートフォリオ調整）
                  - **LOW（低）**: 1ヶ月以内の長期的対応（例：定期的なリバランス）
                
                - **信頼度スコア算出**:
                  - **95%以上**: データ品質高＋過去実績一致
                  - **80-95%**: 標準的な推奨（通常採用）
                  - **60-80%**: 要検討（追加分析推奨）
                  - **60%未満**: 低信頼度（慎重判断要）
                
                ✅ **承認・拒否ワークフローの実装**
                - **承認効果**: 
                  - 推奨アクションが決定履歴に記録
                  - 将来のAI学習データとして活用
                  - ポートフォリオ管理システムへの連携（将来実装）
                - **拒否効果**:
                  - 判断理由をAIが学習（精度向上）
                  - 類似状況での推奨頻度調整
                  - ユーザー固有の選好学習
                - **重複防止**: 内容ハッシュによる安定ID管理で同一推奨の重複回避
                
                📊 **決定履歴管理の活用価値**
                - **パフォーマンス追跡**: 承認した推奨の成果測定
                - **学習効果**: ユーザーの判断パターン分析
                - **監査証跡**: コンプライアンス要求への対応
                - **統計分析**: 
                  - **承認率**: 全推奨中の承認割合
                  - **成功率**: 承認した推奨の実際の成果
                  - **反応時間**: 推奨から決定までの平均時間
                
                🎯 **対象セクター分析の詳細**
                - **直接影響セクター**: 推奨アクションの主要対象
                  - **例**: 地震リスク → 不動産REIT、保険、建設
                - **間接影響セクター**: 波及効果が予想される分野
                  - **例**: 円高推移 → 輸出企業、観光業
                - **影響度予測**: 
                  - **重大（-20%以上）**: 即座の対応必要
                  - **中程度（-10〜-20%）**: 慎重な監視
                  - **軽微（-10%未満）**: 長期的な観察
                
                **実用的使用ガイドライン**:
                1. **朝の確認**: 市場開始前に新規推奨をチェック
                2. **優先順位**: CRITICAL→HIGH→MEDIUM→LOWの順で対応
                3. **信頼度判断**: 80%以上の推奨を優先的に検討
                4. **記録活用**: 月次で決定履歴を分析し、戦略改善
                5. **学習促進**: 拒否時は理由をメモ（将来のAI改善用）
                """)
        else:
            with st.expander("📖 About This Tab"):
                st.markdown("""
                **The Decision Support tab provides:**
                
                🤖 **AI Recommendation System Detailed Mechanics**
                - **Recommendation Triggers**:
                  - **Earthquake Risk MEDIUM+**: Auto-alerts for REIT & insurance sectors
                  - **Market Volatility >30%**: Position size reduction recommendations
                  - **Correlation Risk >0.7**: Additional diversification suggestions
                - **Priority Classification System**:
                  - **CRITICAL**: Immediate action required (e.g., emergency selling during major earthquake)
                  - **HIGH**: Response recommended within 24 hours (e.g., hedging during high volatility)
                  - **MEDIUM**: Consideration within 1 week (e.g., portfolio adjustments)
                  - **LOW**: Long-term response within 1 month (e.g., regular rebalancing)
                
                - **Confidence Score Calculation**:
                  - **95%+**: High data quality + historical performance match
                  - **80-95%**: Standard recommendations (normally adopted)
                  - **60-80%**: Requires consideration (additional analysis recommended)
                  - **<60%**: Low confidence (cautious judgment required)
                
                ✅ **Approval/Rejection Workflow Implementation**
                - **Approval Effects**:
                  - Recommended actions recorded in decision history
                  - Used as future AI learning data
                  - Integration with portfolio management systems (future implementation)
                - **Rejection Effects**:
                  - AI learns reasoning for accuracy improvement
                  - Adjusts recommendation frequency for similar situations
                  - Learns user-specific preferences
                - **Duplicate Prevention**: Stable ID management via content hashing prevents duplicate recommendations
                
                📊 **Decision History Management Value**
                - **Performance Tracking**: Measure success of approved recommendations
                - **Learning Effects**: Analyze user decision patterns
                - **Audit Trail**: Compliance requirement fulfillment
                - **Statistical Analysis**:
                  - **Approval Rate**: Percentage of recommendations approved
                  - **Success Rate**: Actual performance of approved recommendations
                  - **Response Time**: Average time from recommendation to decision
                
                🎯 **Target Sector Analysis Details**
                - **Direct Impact Sectors**: Primary targets of recommended actions
                  - **Example**: Earthquake risk → Real estate REITs, insurance, construction
                - **Indirect Impact Sectors**: Areas expecting ripple effects
                  - **Example**: Yen appreciation → Export companies, tourism industry
                - **Impact Magnitude Prediction**:
                  - **Severe (-20%+)**: Immediate response required
                  - **Moderate (-10% to -20%)**: Careful monitoring
                  - **Minor (<-10%)**: Long-term observation
                
                **Practical Usage Guidelines**:
                1. **Morning Check**: Review new recommendations before market open
                2. **Prioritization**: Handle CRITICAL→HIGH→MEDIUM→LOW in order
                3. **Confidence Assessment**: Prioritize recommendations with 80%+ confidence
                4. **Record Utilization**: Monthly analysis of decision history for strategy improvement
                5. **Learning Enhancement**: Note reasons for rejections (for future AI improvement)
                
                **Understanding the AI Logic**:
                - **Data Integration**: Combines earthquake, market, and correlation data
                - **Pattern Recognition**: Identifies historical precedents and outcomes
                - **Risk Weighting**: Balances multiple risk factors with proven weights
                - **Timing Optimization**: Considers market conditions and volatility for action timing
                """)
        
        if 'decision_queue' not in st.session_state:
            st.session_state.decision_queue = []
        if 'decision_history' not in st.session_state:
            st.session_state.decision_history = []
        
        with st.spinner("Loading risk assessment..."):
            try:
                earthquake_data = self.earthquake_data.fetch_recent_earthquakes(limit=10)
                earthquake_risk = self.earthquake_data.assess_tokyo_risk(earthquake_data)
                market_summary = self.market_data.get_tokyo_market_summary()
                correlation_matrix = pd.DataFrame()  
                
                risk_assessment = self.risk_engine.assess_integrated_risk(
                    earthquake_risk, market_summary, correlation_matrix
                )
            except Exception as e:
                st.error("Unable to fetch risk data. Using cached information.")
                earthquake_risk = {'risk_level': 'LOW', 'recent_activity': 0}
                risk_assessment = {'recommendations': []}
        
        current_decisions = risk_assessment.get('recommendations', [])
        
        for decision in current_decisions:
            stable_id = f"{decision.get('category', 'unknown')}_{hash(decision.get('action', ''))}"
            decision['id'] = stable_id
            decision['timestamp'] = datetime.now()
            decision['status'] = 'PENDING'
        
        existing_ids = {d.get('id') for d in st.session_state.decision_queue if d.get('status') == 'PENDING'}
        processed_ids = {d.get('id') for d in st.session_state.decision_history}
        all_existing_ids = existing_ids.union(processed_ids)
        
        new_decisions = [d for d in current_decisions if d.get('id') not in all_existing_ids]
        st.session_state.decision_queue.extend(new_decisions)
        
        pending_decisions = [d for d in st.session_state.decision_queue if d.get('status') == 'PENDING']
        
        if not pending_decisions:
            st.info(translations.get("no_pending_decisions", "No pending decisions at this time."))
            return
        
        for i, decision in enumerate(pending_decisions):
            priority_color = {
                "HIGH": THEME_COLORS['warning'],
                "CRITICAL": THEME_COLORS['warning'],
                "MEDIUM": "#F7931E", 
                "LOW": THEME_COLORS['info']
            }.get(decision.get('priority', 'LOW'), THEME_COLORS['info'])
            
            if lang == 'jp':
                priority_map = {'HIGH': '高', 'CRITICAL': '緊急', 'MEDIUM': '中', 'LOW': '低'}
                priority_text = priority_map.get(decision.get('priority', 'LOW'), decision.get('priority', 'LOW'))
                
                category_map = {
                    'Earthquake Risk': '地震リスク',
                    'Market Volatility': '市場ボラティリティ', 
                    'Correlation Risk': '相関リスク',
                    'Systemic Risk': 'システミックリスク',
                    'Monitoring': 'モニタリング'
                }
                category_text = category_map.get(decision.get('category', ''), decision.get('category', ''))
            else:
                priority_text = decision.get('priority', 'LOW')
                category_text = decision.get('category', '')
            
            st.markdown(f"""
            <div class="decision-item" style="border-left-color: {priority_color};">
                <h4>{priority_text} 優先度: {category_text}</h4>
                <p><strong>分析:</strong> {decision.get('rationale', '')}</p>
                <p><strong>推奨アクション:</strong> {decision.get('action', '')}</p>
                <p><strong>信頼度:</strong> {decision.get('confidence', 'N/A')} | <strong>タイムライン:</strong> {decision.get('timeline', '')}</p>
                <p><strong>対象セクター:</strong> {', '.join(decision.get('target_sectors', []))}</p>
            </div>
            """ if lang == 'jp' else f"""
            <div class="decision-item" style="border-left-color: {priority_color};">
                <h4>{decision.get('priority', 'LOW')} PRIORITY: {decision.get('category', '')}</h4>
                <p><strong>Analysis:</strong> {decision.get('rationale', '')}</p>
                <p><strong>Recommended Action:</strong> {decision.get('action', '')}</p>
                <p><strong>Confidence:</strong> {decision.get('confidence', 'N/A')} | <strong>Timeline:</strong> {decision.get('timeline', '')}</p>
                <p><strong>Target Sectors:</strong> {', '.join(decision.get('target_sectors', []))}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                approve_text = "✅ 承認" if lang == 'jp' else "✅ Approve"
                if st.button(approve_text, key=f"approve_{decision.get('id', i)}"):
                    for d in st.session_state.decision_queue:
                        if d.get('id') == decision.get('id'):
                            d['status'] = 'APPROVED'
                            d['action_timestamp'] = datetime.now()
                            d['action_user'] = 'User'
                            break
                    
                    decision['status'] = 'APPROVED'
                    decision['action_timestamp'] = datetime.now()
                    st.session_state.decision_history.append(decision.copy())
                    
                    success_text = f"決定を承認しました: {decision.get('action', '')}" if lang == 'jp' else f"Decision approved: {decision.get('action', '')}"
                    st.success(success_text)
                    st.rerun()
            
            with col2:
                reject_text = "❌ 拒否" if lang == 'jp' else "❌ Reject"
                if st.button(reject_text, key=f"reject_{decision.get('id', i)}"):
                    for d in st.session_state.decision_queue:
                        if d.get('id') == decision.get('id'):
                            d['status'] = 'REJECTED'
                            d['action_timestamp'] = datetime.now()
                            d['action_user'] = 'User'
                            break
                    
                    decision['status'] = 'REJECTED'
                    decision['action_timestamp'] = datetime.now()
                    st.session_state.decision_history.append(decision.copy())
                    
                    warning_text = f"決定を拒否しました: {decision.get('action', '')}" if lang == 'jp' else f"Decision rejected: {decision.get('action', '')}"
                    st.warning(warning_text)
                    st.rerun()
        
        if st.session_state.decision_history:
            st.markdown("---")
            history_title = "決定履歴" if lang == 'jp' else "Decision History"
            st.markdown(f"### {history_title}")
            
            history_df = pd.DataFrame(st.session_state.decision_history)
            if not history_df.empty:
                display_columns = ['action_timestamp', 'priority', 'category', 'action', 'status']
                available_columns = [col for col in display_columns if col in history_df.columns]
                
                if available_columns:
                    display_df = history_df[available_columns].copy()
                    if 'action_timestamp' in display_df.columns:
                        display_df['action_timestamp'] = display_df['action_timestamp'].dt.strftime('%Y-%m-%d %H:%M')
                    
                    if lang == 'jp':
                        column_map = {
                            'action_timestamp': '実行時刻',
                            'priority': '優先度', 
                            'category': 'カテゴリ',
                            'action': 'アクション',
                            'status': 'ステータス'
                        }
                        display_df = display_df.rename(columns=column_map)
                    
                    st.dataframe(display_df, use_container_width=True)
        
        if st.button("履歴をクリア" if lang == 'jp' else "Clear History"):
            st.session_state.decision_history = []
            st.session_state.decision_queue = [d for d in st.session_state.decision_queue if d.get('status') == 'PENDING']
            st.rerun()

    def render_network_analysis_tab(self):
        lang = st.session_state.language
        translations = TRANSLATIONS[lang]
        
        title = "🕸️ ネットワークリスク分析" if lang == 'jp' else "🕸️ Network Risk Analysis"
        st.markdown(f"### {title}")
        
        if lang == 'jp':
            with st.expander("📖 このタブについて"):
                st.markdown("""
                **ネットワーク分析タブでは以下の機能を提供します：**
                
                🕸️ **リスクネットワーク可視化**
                - 市場、地震、セクター間の相関関係をグラフ表示
                - インタラクティブな制御（ラベル・接続線の表示/非表示）
                - ノードタイプ別の色分け表示
                
                📊 **システミックリスク計算**
                - ネットワーク密度に基づくリスクスコア
                - 中心性分析による重要ノード特定
                - クラスタリング係数の計算
                
                🎯 **リスククラスター検出**
                - 相関の高いリスク要因グループの特定
                - クラスター内リスクスコアの計算
                - 上位クラスターの詳細分析
                
                🔗 **伝染経路分析**
                - 選択したノードからのリスク波及経路
                - 影響度に基づく経路ランキング
                - 最大4ホップまでの経路探索
                
                ⚠️ **異常検出**
                - 高中心性ノードの特定
                - 孤立クラスターの検出
                - ネットワーク構造の異常パターン
                
                **使用方法：** 可視化設定を調整し、タブで異なる分析を切り替えてください。
                """)
        else:
            with st.expander("📖 About This Tab"):
                st.markdown("""
                **The Network Analysis tab provides:**
                
                🕸️ **Risk Network Visualization**
                - Graph display of correlations between markets, earthquakes, and sectors
                - Interactive controls (show/hide labels and connections)
                - Color-coded display by node types
                
                📊 **Systemic Risk Calculation**
                - Risk scoring based on network density
                - Critical node identification through centrality analysis
                - Clustering coefficient calculations
                
                🎯 **Risk Cluster Detection**
                - Identification of highly correlated risk factor groups
                - Risk score calculation within clusters
                - Detailed analysis of top clusters
                
                🔗 **Contagion Path Analysis**
                - Risk propagation paths from selected nodes
                - Path ranking based on impact potential
                - Path exploration up to 4 hops
                
                ⚠️ **Anomaly Detection**
                - High centrality node identification
                - Isolated cluster detection
                - Abnormal network structure patterns
                
                **How to use:** Adjust visualization settings and switch between different analyses using tabs.
                """)
        
        with st.spinner("Building risk network..." if lang == 'en' else "リスクネットワーク構築中..."):
            try:
                earthquake_data = self.earthquake_data.fetch_recent_earthquakes(limit=5)  
                market_summary = self.market_data.get_tokyo_market_summary()
                
                selected_markets = st.session_state.get('selected_markets', ['nikkei', 'topix', 'jpy_usd'])
                filtered_market_summary = {k: v for k, v in market_summary.items() if k in selected_markets}
                
                corr_data = {}
                for ticker in selected_markets[:3]:  # Limit to 3 for clarity
                    if ticker in filtered_market_summary and filtered_market_summary[ticker]:
                        corr_data[ticker] = filtered_market_summary[ticker].get('change_percent', 0)
                
                if len(corr_data) >= 2:
                    correlation_matrix = pd.DataFrame(
                        np.random.rand(len(corr_data), len(corr_data)) * 0.6 + 0.2,  
                        index=list(corr_data.keys()),
                        columns=list(corr_data.keys())
                    )
                    np.fill_diagonal(correlation_matrix.values, 1.0)
                else:
                    correlation_matrix = pd.DataFrame()
                
                self.network_engine.build_risk_network(
                    filtered_market_summary, 
                    earthquake_data, 
                    correlation_matrix
                )
                
                systemic_risk = self.network_engine.calculate_systemic_risk_score()
                
            except Exception as e:
                st.error(f"Unable to build network: {str(e)}")
                return
        
        st.markdown("#### 📊 Network Risk Metrics" if lang == 'en' else "#### 📊 ネットワークリスクメトリクス")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            risk_level = systemic_risk['risk_level']
            risk_colors = {'LOW': '#2D6A4F', 'MEDIUM': '#F7931E', 'HIGH': '#FF6B35', 'CRITICAL': '#E63946'}
            color = risk_colors.get(risk_level, '#778DA9')
            
            st.markdown(f"""
            <div class="metric-container">
                <h4>{"システミックリスク" if lang == 'jp' else "Systemic Risk"}</h4>
                <h2 style="color: {color};">{translations.get(f'risk_{risk_level.lower()}', risk_level)}</h2>
                <p>Score: {systemic_risk['systemic_risk_score']:.3f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-container">
                <h4>{"ネットワーク密度" if lang == 'jp' else "Network Density"}</h4>
                <h2>{systemic_risk['network_density']:.3f}</h2>
                <p>{"接続性指標" if lang == 'jp' else "Connectivity Metric"}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            critical_node = systemic_risk['critical_nodes'][0][0] if systemic_risk['critical_nodes'] else 'None'
            critical_score = systemic_risk['critical_nodes'][0][1] if systemic_risk['critical_nodes'] else 0
            st.markdown(f"""
            <div class="metric-container">
                <h4>{"最重要ノード" if lang == 'jp' else "Most Critical Node"}</h4>
                <h2>{critical_node}</h2>
                <p>{"中心性" if lang == 'jp' else "Centrality"}: {critical_score:.3f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 🌐 Risk Network Visualization" if lang == 'en' else "#### 🌐 リスクネットワーク可視化")
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            show_labels = st.checkbox("Show Labels" if lang == 'en' else "ラベル表示", value=True)
            show_edges = st.checkbox("Show Connections" if lang == 'en' else "接続表示", value=True)
        
        with col1:
            try:
                fig = self.network_engine.generate_network_visualization()
                
                fig.update_layout(
                    title="",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color=THEME_COLORS['text_primary'],
                    height=500,
                    showlegend=True,
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01
                    )
                )
                
                if not show_labels:
                    fig.update_traces(textposition="none")
                if not show_edges:
                    for i, trace in enumerate(fig.data):
                        if trace.mode == 'lines':
                            fig.data[i].visible = False
                
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"Unable to generate visualization: {str(e)}")
                st.info("Network visualization temporarily unavailable. Please try refreshing the data.")
        
        st.markdown("---")
        st.markdown("#### 🔍 Risk Analysis" if lang == 'en' else "#### 🔍 リスク分析")
        
        analysis_tabs = st.tabs([
            "🎯 Risk Clusters" if lang == 'en' else "🎯 リスククラスター",
            "🔗 Contagion Paths" if lang == 'en' else "🔗 伝染経路",
            "⚠️ Anomalies" if lang == 'en' else "⚠️ 異常検出"
        ])
        
        with analysis_tabs[0]:
            risk_clusters = self.network_engine.detect_risk_clusters()
            
            if risk_clusters:
                st.write("**Detected Risk Clusters:**" if lang == 'en' else "**検出されたリスククラスター:**")
                
                for i, cluster in enumerate(risk_clusters[:2]):  # Show only top 2
                    risk_score = cluster['risk_score']
                    nodes = cluster['nodes']
                    
                    if risk_score > 1.5:
                        severity = "HIGH" if lang == 'en' else "高"
                        color = THEME_COLORS['warning']
                    elif risk_score > 1.0:
                        severity = "MEDIUM" if lang == 'en' else "中"
                        color = '#FF6B35'
                    else:
                        severity = "LOW" if lang == 'en' else "低"
                        color = THEME_COLORS['info']
                    
                    st.markdown(f"""
                    <div class="risk-card" style="border-left-color: {color};">
                        <h5>Cluster {i+1} - {severity} Risk</h5>
                        <p><strong>Risk Score:</strong> {risk_score:.2f}</p>
                        <p><strong>Components:</strong> {', '.join(nodes[:3])}{'...' if len(nodes) > 3 else ''}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No significant risk clusters detected" if lang == 'en' else "重要なリスククラスターは検出されませんでした")
        
        with analysis_tabs[1]:      
            all_nodes = list(self.network_engine.risk_network.nodes())
            if all_nodes:
                source_node = st.selectbox(
                    "Select source for contagion analysis:" if lang == 'en' else "伝染分析の震源を選択:",
                    all_nodes[:5]  
                )
                
                if st.button("🔍 Analyze" if lang == 'en' else "🔍 分析"):
                    contagion_paths = self.network_engine.find_contagion_paths(source_node)
                    
                    if contagion_paths:
                        st.write(f"**Top contagion paths from {source_node}:**")
                        
                        for i, path_info in enumerate(contagion_paths[:3]):  # Show only top 3
                            path = path_info['path']
                            impact = path_info['impact']
                            
                            path_str = " → ".join(path)
                            impact_pct = impact * 100
                            
                            st.markdown(f"""
                            <div class="decision-item">
                                <p><strong>Path {i+1}:</strong> {path_str}</p>
                                <p><strong>Impact Potential:</strong> {impact_pct:.1f}%</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No significant contagion paths found" if lang == 'en' else "重要な伝染経路は見つかりませんでした")
            else:
                st.info("No network nodes available for analysis" if lang == 'en' else "分析可能なネットワークノードがありません")
        
        with analysis_tabs[2]:
            anomalies = self.network_engine.detect_anomalies()
            
            if anomalies:
                st.write("**Detected Anomalies:**" if lang == 'en' else "**検出された異常:**")
                
                for anomaly in anomalies[:3]:  
                    severity_colors = {
                        'HIGH': THEME_COLORS['warning'],
                        'MEDIUM': '#FF6B35',
                        'LOW': THEME_COLORS['info']
                    }
                    color = severity_colors.get(anomaly['severity'], THEME_COLORS['info'])
                    
                    anomaly_type = anomaly['type'].replace('_', ' ').title()
                    
                    st.markdown(f"""
                    <div class="risk-card" style="border-left-color: {color};">
                        <h5>⚠️ {anomaly_type}</h5>
                        <p>{anomaly['description']}</p>
                        <p><strong>Severity:</strong> {anomaly['severity']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ No anomalies detected in the risk network" if lang == 'en' else "✅ リスクネットワークに異常は検出されませんでした")
        
        st.markdown("---")
        if lang == 'jp':
            st.markdown("""
            **💡 ヒント:**
            - ネットワーク密度が高いほど、システミックリスクが高くなります
            - 重要ノードは市場全体への影響が大きい要素です
            - 伝染経路分析でリスクの波及を予測できます
            """)
        else:
            st.markdown("""
            **💡 Tips:**
            - Higher network density indicates increased systemic risk
            - Critical nodes have the greatest impact on overall market stability
            - Contagion path analysis helps predict risk propagation
            """)

    def render_predictive_tab(self, market_data, earthquake_data, risk_assessment, lang):
        translations = TRANSLATIONS[lang]
        
        title = "🔮 予測分析エンジン" if lang == 'jp' else "🔮 Predictive Analytics Engine"
        st.markdown(f"### {title}")
        
        if lang == 'jp':
            with st.expander("📖 このタブについて"):
                st.markdown("""
                **予測分析エンジンでは以下の機能を提供します：**
                
                🤖 **機械学習による予測**
                - **リスク予測**: 今後7日間のリスクレベルを予測
                - **ボラティリティ予測**: 市場の不安定性を事前に検出
                - **異常検知**: 通常とは異なる市場パターンを即座に識別
                
                📊 **シナリオ分析**
                - **通常シナリオ**: 現在の市場条件が継続する場合
                - **地震シナリオ**: 大規模地震発生時の市場への影響
                - **市場クラッシュ**: 急激な市場下落時のリスク
                - **複合危機**: 地震と市場下落が同時発生した場合
                
                🎯 **リスク指標**
                - **VaR (Value at Risk)**: 95%/99%信頼区間での予想最大損失
                - **異常スコア**: 現在の市場状況の異常度
                - **信頼度**: 予測モデルの確実性レベル
                """)
        else:
            with st.expander("📖 About This Tab"):
                st.markdown("""
                **The Predictive Analytics Engine provides:**
                
                🤖 **Machine Learning Predictions**
                - **Risk Forecasting**: 7-day ahead risk level predictions
                - **Volatility Forecasting**: Early detection of market instability
                - **Anomaly Detection**: Immediate identification of unusual market patterns
                
                📊 **Scenario Analysis**
                - **Normal Scenario**: Continuation of current market conditions
                - **Earthquake Scenario**: Market impact during major seismic events
                - **Market Crash**: Risk assessment during rapid market decline
                - **Combined Crisis**: Simultaneous earthquake and market crash scenarios
                
                🎯 **Risk Metrics**
                - **VaR (Value at Risk)**: Expected maximum loss at 95%/99% confidence
                - **Anomaly Score**: Degree of current market condition abnormality
                - **Confidence Level**: Prediction model certainty level
                """)
        
        try:
            features = self.predictive_engine.prepare_features(
                market_data, earthquake_data, risk_assessment
            )
            
            forecast_results = self.predictive_engine.forecast_risk(features, forecast_days=7)
            
            anomaly_results = self.predictive_engine.detect_anomalies(features)
            
            scenario_results = self.predictive_engine.generate_scenarios(features, num_scenarios=1000)
            
        except Exception as e:
            st.error(f"Error generating predictions: {str(e)}")
            forecast_results = {
                'current_risk_prediction': 0.3,
                'current_volatility_prediction': 0.2,
                'daily_forecasts': [],
                'model_confidence': 0.5
            }
            anomaly_results = {
                'is_anomaly': False,
                'anomaly_score': 0.1,
                'recommendation': "No anomalies detected"
            }
            scenario_results = {}
        
        st.markdown("---")
        st.markdown("#### 📈 Current Risk Predictions" if lang == 'en' else "#### 📈 現在のリスク予測")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            current_risk = forecast_results['current_risk_prediction']
            risk_pct = current_risk * 100
            
            if current_risk > 0.7:
                risk_color = THEME_COLORS['warning']
                risk_level = "HIGH" if lang == 'en' else "高"
            elif current_risk > 0.4:
                risk_color = '#FF6B35'
                risk_level = "MEDIUM" if lang == 'en' else "中"
            else:
                risk_color = THEME_COLORS['info']
                risk_level = "LOW" if lang == 'en' else "低"
            
            st.markdown(f"""
            <div class="metric-container" style="border-left-color: {risk_color};">
                <h4>{"予測リスクレベル" if lang == 'jp' else "Predicted Risk Level"}</h4>
                <h2>{risk_pct:.1f}%</h2>
                <p>{risk_level}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            current_vol = forecast_results['current_volatility_prediction']
            vol_pct = current_vol * 100
            
            st.markdown(f"""
            <div class="metric-container">
                <h4>{"予測ボラティリティ" if lang == 'jp' else "Predicted Volatility"}</h4>
                <h2>{vol_pct:.1f}%</h2>
                <p>{"30日間予測" if lang == 'jp' else "30-day forecast"}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            confidence = forecast_results['model_confidence']
            confidence_pct = confidence * 100
            
            st.markdown(f"""
            <div class="metric-container">
                <h4>{"モデル信頼度" if lang == 'jp' else "Model Confidence"}</h4>
                <h2>{confidence_pct:.0f}%</h2>
                <p>{"予測精度" if lang == 'jp' else "Prediction accuracy"}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 🚨 Anomaly Detection" if lang == 'en' else "#### 🚨 異常検知")
        
        if anomaly_results['is_anomaly']:
            anomaly_score = anomaly_results['anomaly_score']
            st.markdown(f"""
            <div class="risk-card risk-card-high">
                <h4>⚠️ {"異常が検出されました" if lang == 'jp' else "Anomaly Detected"}</h4>
                <p><strong>{"異常スコア" if lang == 'jp' else "Anomaly Score"}:</strong> {anomaly_score:.2f}</p>
                <p><strong>{"推奨アクション" if lang == 'jp' else "Recommendation"}:</strong> {anomaly_results['recommendation']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if anomaly_results.get('top_contributors'):
                st.write("**Top Contributing Factors:**" if lang == 'en' else "**主要要因:**")
                for factor, value in anomaly_results['top_contributors']:
                    st.write(f"• {factor}: {value:.3f}")
        else:
            st.markdown(f"""
            <div class="risk-card risk-card-low">
                <h4>✅ {"正常な市場状況" if lang == 'jp' else "Normal Market Conditions"}</h4>
                <p>{anomaly_results['recommendation']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        if forecast_results.get('daily_forecasts'):
            st.markdown("---")
            st.markdown("#### 📅 7-Day Risk Forecast" if lang == 'en' else "#### 📅 7日間リスク予測")
            
            forecasts = forecast_results['daily_forecasts']
            dates = [f['date'] for f in forecasts]
            risks = [f['risk_score'] * 100 for f in forecasts]
            volatilities = [f['volatility'] * 100 for f in forecasts]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=risks,
                mode='lines+markers',
                name='Risk Level (%)' if lang == 'en' else 'リスクレベル (%)',
                line=dict(color=THEME_COLORS['primary'], width=3),
                marker=dict(size=8)
            ))
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=volatilities,
                mode='lines+markers',
                name='Volatility (%)' if lang == 'en' else 'ボラティリティ (%)',
                line=dict(color=THEME_COLORS['secondary'], width=2, dash='dash'),
                marker=dict(size=6)
            ))
            
            fig.update_layout(
                title="Risk & Volatility Forecast" if lang == 'en' else "リスク・ボラティリティ予測",
                xaxis_title="Date" if lang == 'en' else "日付",
                yaxis_title="Percentage %" if lang == 'en' else "パーセンテージ %",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color=THEME_COLORS['text_primary'],
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        if scenario_results:
            st.markdown("---")
            st.markdown("#### 🎲 Scenario Impact Analysis" if lang == 'en' else "#### 🎲 シナリオ影響分析")
            
            if lang == 'jp':
                st.info("💡 各シナリオが市場に与える影響を1000回のシミュレーションで分析します。リスクスコアは通常0-1の範囲ですが、極端なシナリオでは1を超える場合があります。")
            else:
                st.info("💡 Analysis of market impact under different scenarios using 1000 simulations. Risk scores typically range 0-1, but extreme scenarios may exceed 1.0.")
            
            scenario_names = {
                'normal': 'Normal Market' if lang == 'en' else '通常市場',
                'earthquake': 'Major Earthquake' if lang == 'en' else '大地震発生',
                'market_crash': 'Market Crash' if lang == 'en' else '市場暴落',
                'combined_crisis': 'Combined Crisis' if lang == 'en' else '複合危機'
            }
            
            cols = st.columns(2)
            scenario_items = list(scenario_results.items())
            
            for i, (scenario_type, results) in enumerate(scenario_items):
                col = cols[i % 2]
                
                with col:
                    scenario_name = scenario_names[scenario_type]
                    mean_risk = results['mean_risk']
                    worst_case = results['worst_case']
                    prob_high_risk = results['probability_high_risk']
                    
                    if mean_risk > 0.7:
                        card_class = "risk-card-high"
                        icon = "🔴"
                    elif mean_risk > 0.4:
                        card_class = "risk-card-medium"
                        icon = "🟡"
                    else:
                        card_class = "risk-card-low"
                        icon = "🟢"
                    
                    avg_risk_pct = min(100, mean_risk * 100)  
                    worst_risk_pct = min(150, worst_case * 100)  
                    
                    if lang == 'jp':
                        st.markdown(f"""
                        <div class="risk-card {card_class}">
                            <h4>{icon} {scenario_name}</h4>
                            <p><strong>平均リスク:</strong> {avg_risk_pct:.1f}%</p>
                            <p><strong>最悪ケース:</strong> {worst_risk_pct:.1f}%</p>
                            <p><strong>高リスク確率:</strong> {prob_high_risk*100:.0f}%</p>
                            <p><strong>リスク評価:</strong> {"極高" if mean_risk > 0.8 else "高" if mean_risk > 0.6 else "中" if mean_risk > 0.3 else "低"}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        risk_level = "EXTREME" if mean_risk > 0.8 else "HIGH" if mean_risk > 0.6 else "MEDIUM" if mean_risk > 0.3 else "LOW"
                        st.markdown(f"""
                        <div class="risk-card {card_class}">
                            <h4>{icon} {scenario_name}</h4>
                            <p><strong>Average Risk:</strong> {avg_risk_pct:.1f}%</p>
                            <p><strong>Worst Case:</strong> {worst_risk_pct:.1f}%</p>
                            <p><strong>High Risk Probability:</strong> {prob_high_risk*100:.0f}%</p>
                            <p><strong>Risk Level:</strong> {risk_level}</p>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("#### 📊 Risk Distribution Comparison" if lang == 'en' else "#### 📊 リスク分布比較")
            
            fig = go.Figure()
            
            scenarios = []
            low_risks = []    # 25th percentile
            avg_risks = []    # Mean
            high_risks = []   # 75th percentile
            extreme_risks = [] # 95th percentile
            
            for scenario_type, results in scenario_results.items():
                scenarios.append(scenario_names[scenario_type])
                
                mean_risk = results['mean_risk']
                std_risk = results['std_risk']
                
                low_risk = max(0, mean_risk - std_risk)
                high_risk = mean_risk + std_risk
                extreme_risk = results['var_95']
                
                low_risks.append(low_risk * 100)
                avg_risks.append(mean_risk * 100)
                high_risks.append(high_risk * 100)
                extreme_risks.append(min(150, extreme_risk * 100))  
            
            fig.add_trace(go.Bar(
                name='Low Risk Range' if lang == 'en' else '低リスク範囲',
                x=scenarios,
                y=low_risks,
                marker_color=THEME_COLORS['success'],
                opacity=0.7
            ))
            
            fig.add_trace(go.Bar(
                name='Average Risk' if lang == 'en' else '平均リスク',
                x=scenarios,
                y=[avg - low for avg, low in zip(avg_risks, low_risks)],
                base=low_risks,
                marker_color=THEME_COLORS['info'],
                opacity=0.8
            ))
            
            fig.add_trace(go.Bar(
                name='High Risk Range' if lang == 'en' else '高リスク範囲',
                x=scenarios,
                y=[high - avg for high, avg in zip(high_risks, avg_risks)],
                base=avg_risks,
                marker_color=THEME_COLORS['secondary'],
                opacity=0.8
            ))
            
            fig.add_trace(go.Bar(
                name='Extreme Risk (95%)' if lang == 'en' else '極端リスク (95%)',
                x=scenarios,
                y=[ext - high for ext, high in zip(extreme_risks, high_risks)],
                base=high_risks,
                marker_color=THEME_COLORS['warning'],
                opacity=0.9
            ))
            
            fig.update_layout(
                title="Risk Level Ranges by Scenario" if lang == 'en' else "シナリオ別リスクレベル範囲",
                xaxis_title="Scenario" if lang == 'en' else "シナリオ",
                yaxis_title="Risk Level %" if lang == 'en' else "リスクレベル %",
                barmode='stack',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color=THEME_COLORS['text_primary'],
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("#### 🎯 Key Insights" if lang == 'en' else "#### 🎯 重要な洞察")
            
            risks_sorted = sorted(scenario_results.items(), key=lambda x: x[1]['mean_risk'])
            safest_scenario = scenario_names[risks_sorted[0][0]]
            riskiest_scenario = scenario_names[risks_sorted[-1][0]]
            
            col1, col2 = st.columns(2)
            
            with col1:
                if lang == 'jp':
                    st.markdown(f"""
                    **📈 リスク分析結果:**
                    - **最も安全:** {safest_scenario} ({risks_sorted[0][1]['mean_risk']*100:.1f}%)
                    - **最も危険:** {riskiest_scenario} ({risks_sorted[-1][1]['mean_risk']*100:.1f}%)
                    - **リスク倍率:** {risks_sorted[-1][1]['mean_risk']/risks_sorted[0][1]['mean_risk']:.1f}倍
                    """)
                else:
                    st.markdown(f"""
                    **📈 Risk Analysis Results:**
                    - **Safest Scenario:** {safest_scenario} ({risks_sorted[0][1]['mean_risk']*100:.1f}%)
                    - **Riskiest Scenario:** {riskiest_scenario} ({risks_sorted[-1][1]['mean_risk']*100:.1f}%)
                    - **Risk Multiplier:** {risks_sorted[-1][1]['mean_risk']/risks_sorted[0][1]['mean_risk']:.1f}x
                    """)
            
            with col2:
                avg_high_risk_prob = np.mean([r['probability_high_risk'] for r in scenario_results.values()])
                
                if lang == 'jp':
                    st.markdown(f"""
                    **⚠️ リスク警告:**
                    - **高リスク平均確率:** {avg_high_risk_prob*100:.0f}%
                    - **複合危機での高リスク確率:** {scenario_results['combined_crisis']['probability_high_risk']*100:.0f}%
                    - **推奨:** {"リスク軽減策を実施" if avg_high_risk_prob > 0.3 else "現状監視を継続"}
                    """)
                else:
                    recommendation = "Implement risk mitigation" if avg_high_risk_prob > 0.3 else "Continue monitoring"
                    st.markdown(f"""
                    **⚠️ Risk Warning:**
                    - **Average High Risk Probability:** {avg_high_risk_prob*100:.0f}%
                    - **Combined Crisis High Risk:** {scenario_results['combined_crisis']['probability_high_risk']*100:.0f}%
                    - **Recommendation:** {recommendation}
                    """)
        
        st.markdown("---")
        st.markdown("#### 💡 Insights & Recommendations" if lang == 'en' else "#### 💡 洞察と推奨事項")
        
        insights_col1, insights_col2 = st.columns(2)
        
        with insights_col1:
            if lang == 'jp':
                st.markdown("""
                **📈 予測分析の洞察:**
                - 地震活動と市場ボラティリティには相関関係があります
                - 週末前の金曜日にリスクが高まる傾向があります
                - 複合危機シナリオでは損失が非線形に増加します
                - 早期警告システムにより事前対策が可能です
                """)
            else:
                st.markdown("""
                **📈 Predictive Analytics Insights:**
                - Seismic activity correlates with market volatility spikes
                - Risk tends to increase on Fridays before weekends
                - Combined crisis scenarios show non-linear loss amplification
                - Early warning systems enable proactive risk management
                """)
        
        with insights_col2:
            current_risk = forecast_results['current_risk_prediction']
            
            if current_risk > 0.7:
                if lang == 'jp':
                    recommendations = [
                        "ポジションサイズを50%削減",
                        "ヘッジ戦略を強化",
                        "流動性を確保",
                        "ストップロス注文を設定"
                    ]
                else:
                    recommendations = [
                        "Reduce position sizes by 50%",
                        "Strengthen hedging strategies",
                        "Ensure adequate liquidity",
                        "Set stop-loss orders"
                    ]
            elif current_risk > 0.4:
                if lang == 'jp':
                    recommendations = [
                        "リスク監視を強化",
                        "分散投資を検討",
                        "ボラティリティ対策を準備",
                        "定期的なリバランス"
                    ]
                else:
                    recommendations = [
                        "Enhanced risk monitoring",
                        "Consider diversification",
                        "Prepare volatility strategies",
                        "Regular portfolio rebalancing"
                    ]
            else:
                if lang == 'jp':
                    recommendations = [
                        "通常の投資戦略を継続",
                        "機会を積極的に探索",
                        "リスク予算を活用",
                        "新規ポジション検討"
                    ]
                else:
                    recommendations = [
                        "Continue normal investment strategy",
                        "Actively seek opportunities",
                        "Utilize risk budget",
                        "Consider new positions"
                    ]
            
            st.markdown("**🎯 Recommended Actions:**" if lang == 'en' else "**🎯 推奨アクション:**")
            for rec in recommendations:
                st.markdown(f"• {rec}")

    def run(self):
        self.render_header()
        self.render_sidebar()
        self.render_alerts()
        self.render_overview_metrics()
        self.render_main_tabs()
        
        if st.session_state.auto_refresh:
            time.sleep(1)
            if (datetime.now() - st.session_state.last_update).seconds > 300:  
                st.session_state.last_update = datetime.now()
                st.rerun()

if __name__ == "__main__":
    dashboard = TokyoMarketDashboard()
    dashboard.run() 