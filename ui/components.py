"""
UI Components for Tokyo Market Risk Dashboard
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional

class UIComponents:
    """
    Reusable UI components for the Tokyo Market Risk Dashboard
    """
    
    def __init__(self):
        pass
    
    def render_risk_card(self, title: str, risk_level: str, details: Dict, 
                        custom_color: str = None) -> None:
        """Render a risk assessment card"""
        
        # Color mapping for risk levels
        color_map = {
            'LOW': '#2D6A4F',
            'MEDIUM': '#F7931E', 
            'HIGH': '#FF6B35',
            'CRITICAL': '#E63946'
        }
        
        border_color = custom_color or color_map.get(risk_level, '#778DA9')
        
        st.markdown(f"""
        <div class="risk-card" style="border-left-color: {border_color};">
            <h4>{title}</h4>
            <p><strong>Risk Level:</strong> {risk_level}</p>
            {"".join([f"<p><strong>{k}:</strong> {v}</p>" for k, v in details.items()])}
        </div>
        """, unsafe_allow_html=True)
    
    def render_metric_grid(self, metrics: List[Dict]) -> None:
        """Render a grid of metrics"""
        
        # Create columns based on number of metrics
        cols = st.columns(len(metrics))
        
        for i, metric in enumerate(metrics):
            with cols[i]:
                st.metric(
                    metric['label'],
                    metric['value'],
                    metric.get('delta', None),
                    help=metric.get('help', None)
                )
    
    def create_correlation_heatmap(self, correlation_matrix: pd.DataFrame, 
                                 title: str = "Correlation Matrix") -> go.Figure:
        """Create a correlation heatmap"""
        
        fig = px.imshow(
            correlation_matrix,
            title=title,
            color_continuous_scale="RdBu_r",
            aspect="auto"
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        
        return fig
    
    def create_time_series_chart(self, data: pd.DataFrame, title: str,
                               y_column: str, color: str = '#778DA9') -> go.Figure:
        """Create a time series chart"""
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data[y_column],
            mode='lines',
            name=y_column,
            line=dict(color=color, width=2)
        ))
        
        fig.update_layout(
            title=title,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            xaxis=dict(gridcolor='gray'),
            yaxis=dict(gridcolor='gray')
        )
        
        return fig 