"""
Risk Engine for Tokyo Market Risk Dashboard
Integrates earthquake risk, market volatility, and correlation analysis
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from config import RISK_THRESHOLDS, TOKYO_TICKERS

class RiskEngine:
    """
    Comprehensive risk analysis engine for Tokyo markets
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.risk_thresholds = RISK_THRESHOLDS
        
    def assess_integrated_risk(self, earthquake_data: Dict, market_data: Dict, 
                             correlation_matrix: pd.DataFrame) -> Dict:
        """
        Perform integrated risk assessment combining multiple risk factors
        """
        
        # Individual risk assessments
        earthquake_risk = self._assess_earthquake_risk(earthquake_data)
        market_risk = self._assess_market_risk(market_data)
        correlation_risk = self._assess_correlation_risk(correlation_matrix)
        
        # Combined risk score
        combined_score = self._calculate_combined_risk_score(
            earthquake_risk, market_risk, correlation_risk
        )
        
        # Generate risk recommendations
        recommendations = self._generate_recommendations(
            earthquake_risk, market_risk, correlation_risk, combined_score
        )
        
        return {
            'earthquake_risk': earthquake_risk,
            'market_risk': market_risk,
            'correlation_risk': correlation_risk,
            'combined_risk': {
                'score': combined_score,
                'level': self._get_risk_level(combined_score),
                'confidence': self._calculate_confidence(earthquake_data, market_data)
            },
            'recommendations': recommendations,
            'alert_triggers': self._check_alert_triggers(combined_score, earthquake_risk, market_risk),
            'timestamp': datetime.now()
        }
    
    def _assess_earthquake_risk(self, earthquake_data: Dict) -> Dict:
        """Assess earthquake-specific risk factors"""
        if not earthquake_data:
            return {
                'score': 0.1,
                'level': 'LOW',
                'factors': {'recent_activity': 0, 'magnitude': 0, 'proximity': 0}
            }
        
        # Extract key metrics
        recent_activity = earthquake_data.get('recent_activity', 0)
        max_magnitude = earthquake_data.get('max_magnitude', 0)
        closest_distance = earthquake_data.get('closest_distance', float('inf'))
        
        # Scoring components
        activity_score = min(recent_activity / 10.0, 0.4)  # Max 0.4 for activity
        magnitude_score = min(max_magnitude / 8.0, 0.4)    # Max 0.4 for magnitude
        proximity_score = max(0, 0.2 - (closest_distance / 500.0))  # Max 0.2 for proximity
        
        total_score = activity_score + magnitude_score + proximity_score
        
        return {
            'score': total_score,
            'level': self._get_risk_level(total_score),
            'factors': {
                'recent_activity': activity_score,
                'magnitude': magnitude_score,
                'proximity': proximity_score
            },
            'raw_data': {
                'event_count': recent_activity,
                'max_magnitude': max_magnitude,
                'closest_distance_km': closest_distance
            }
        }
    
    def _assess_market_risk(self, market_data: Dict) -> Dict:
        """Assess market volatility and momentum risk"""
        if not market_data:
            return {
                'score': 0.2,
                'level': 'LOW',
                'factors': {'volatility': 0.1, 'momentum': 0.1, 'volume': 0}
            }
        
        # Calculate market metrics
        volatility_score = 0
        momentum_score = 0
        volume_score = 0
        
        processed_tickers = 0
        
        for ticker, data in market_data.items():
            if data and isinstance(data, dict):
                # Volatility scoring (assuming we have volatility data)
                vol = data.get('volatility', 0.2)  # Default 20%
                volatility_score += min(vol / 0.5, 0.4)  # Max 0.4 for high vol
                
                # Momentum scoring
                change_pct = data.get('change_percent', 0)
                momentum_score += min(abs(change_pct) / 10.0, 0.3)  # Max 0.3 for momentum
                
                # Volume scoring (simplified)
                volume = data.get('volume', 0)
                avg_volume = data.get('avg_volume', volume)  # Placeholder
                if avg_volume > 0:
                    volume_ratio = volume / avg_volume
                    volume_score += min(abs(volume_ratio - 1.0), 0.2)  # Max 0.2 for volume
                
                processed_tickers += 1
        
        if processed_tickers > 0:
            volatility_score /= processed_tickers
            momentum_score /= processed_tickers
            volume_score /= processed_tickers
        
        total_score = volatility_score + momentum_score + volume_score
        
        return {
            'score': total_score,
            'level': self._get_risk_level(total_score),
            'factors': {
                'volatility': volatility_score,
                'momentum': momentum_score,
                'volume': volume_score
            },
            'processed_markets': processed_tickers
        }
    
    def _assess_correlation_risk(self, correlation_matrix: pd.DataFrame) -> Dict:
        """Assess cross-market correlation risk"""
        if correlation_matrix.empty:
            return {
                'score': 0.15,
                'level': 'LOW',
                'factors': {'mean_correlation': 0.15, 'max_correlation': 0.15}
            }
        
        # Calculate correlation metrics
        # Remove diagonal (self-correlation = 1.0)
        corr_values = correlation_matrix.values
        np.fill_diagonal(corr_values, np.nan)
        
        # Get absolute correlations (high positive or negative both indicate risk)
        abs_correlations = np.abs(corr_values)
        
        # Calculate risk metrics
        mean_correlation = np.nanmean(abs_correlations)
        max_correlation = np.nanmax(abs_correlations)
        
        # Scoring
        mean_score = min(mean_correlation / 0.8, 0.3)  # Max 0.3 for mean
        max_score = min(max_correlation / 0.9, 0.2)    # Max 0.2 for max
        
        total_score = mean_score + max_score
        
        return {
            'score': total_score,
            'level': self._get_risk_level(total_score),
            'factors': {
                'mean_correlation': mean_score,
                'max_correlation': max_score
            },
            'raw_metrics': {
                'mean_abs_correlation': mean_correlation,
                'max_abs_correlation': max_correlation,
                'correlation_matrix_size': correlation_matrix.shape[0]
            }
        }
    
    def _calculate_combined_risk_score(self, earthquake_risk: Dict, market_risk: Dict, 
                                     correlation_risk: Dict) -> float:
        """Calculate weighted combined risk score"""
        
        # Weights for different risk components
        weights = {
            'earthquake': 0.4,  # High weight for earthquake risk in Tokyo
            'market': 0.35,     # Market volatility
            'correlation': 0.25  # Cross-market correlation
        }
        
        combined_score = (
            earthquake_risk['score'] * weights['earthquake'] +
            market_risk['score'] * weights['market'] +
            correlation_risk['score'] * weights['correlation']
        )
        
        return min(combined_score, 1.0)  # Cap at 1.0
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to risk level"""
        if score >= 0.7:
            return 'CRITICAL'
        elif score >= 0.5:
            return 'HIGH'
        elif score >= 0.3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _calculate_confidence(self, earthquake_data: Dict, market_data: Dict) -> float:
        """Calculate confidence level in risk assessment"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence with more earthquake data
        if earthquake_data.get('recent_activity', 0) > 0:
            confidence += 0.2
        
        # Increase confidence with more market data
        market_data_count = len([d for d in market_data.values() if d])
        confidence += min(market_data_count / 10.0, 0.3)
        
        return min(confidence, 1.0)
    
    def _generate_recommendations(self, earthquake_risk: Dict, market_risk: Dict, 
                                correlation_risk: Dict, combined_score: float) -> List[Dict]:
        """Generate actionable risk management recommendations"""
        
        recommendations = []
        
        # Earthquake-based recommendations
        if earthquake_risk['level'] in ['HIGH', 'CRITICAL']:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Earthquake Risk',
                'action': 'Consider hedging real estate and infrastructure positions',
                'rationale': f"Elevated seismic activity detected ({earthquake_risk['score']:.2f} risk score)",
                'target_sectors': ['REITs', 'Construction', 'Insurance', 'Utilities'],
                'timeline': '24-48 hours'
            })
        
        # Market volatility recommendations  
        if market_risk['level'] in ['HIGH', 'CRITICAL']:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Market Volatility',
                'action': 'Reduce position sizes and increase cash allocation',
                'rationale': f"High market volatility detected ({market_risk['score']:.2f} risk score)",
                'target_sectors': ['All equity positions'],
                'timeline': '1-3 days'
            })
        
        # Correlation-based recommendations
        if correlation_risk['level'] in ['HIGH', 'CRITICAL']:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Correlation Risk',
                'action': 'Diversify across uncorrelated assets and currencies',
                'rationale': f"High cross-market correlation increases systemic risk ({correlation_risk['score']:.2f})",
                'target_sectors': ['Currency hedging', 'Alternative assets'],
                'timeline': '3-7 days'
            })
        
        # Combined risk recommendations
        if combined_score >= 0.7:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Systemic Risk',
                'action': 'Implement comprehensive risk reduction strategy',
                'rationale': f"Multiple risk factors elevated (combined score: {combined_score:.2f})",
                'target_sectors': ['Portfolio-wide review'],
                'timeline': 'Immediate'
            })
        
        # Always include monitoring recommendation
        recommendations.append({
            'priority': 'LOW',
            'category': 'Monitoring',
            'action': 'Continue enhanced monitoring of all risk factors',
            'rationale': 'Maintain situational awareness',
            'target_sectors': ['All'],
            'timeline': 'Ongoing'
        })
        
        return recommendations
    
    def _check_alert_triggers(self, combined_score: float, earthquake_risk: Dict, 
                            market_risk: Dict) -> List[Dict]:
        """Check if any alert thresholds are triggered"""
        
        alerts = []
        
        # Critical combined risk alert
        if combined_score >= 0.8:
            alerts.append({
                'level': 'CRITICAL',
                'type': 'Combined Risk',
                'message': f"Multiple risk factors at critical levels (score: {combined_score:.2f})",
                'requires_action': True
            })
        
        # Earthquake-specific alerts
        if earthquake_risk['level'] == 'CRITICAL':
            alerts.append({
                'level': 'HIGH',
                'type': 'Seismic Activity',
                'message': f"Critical earthquake risk detected in Tokyo region",
                'requires_action': True
            })
        
        # Market volatility alerts
        if market_risk['level'] == 'CRITICAL':
            alerts.append({
                'level': 'HIGH',
                'type': 'Market Volatility',
                'message': f"Extreme market volatility in Tokyo markets",
                'requires_action': True
            })
        
        return alerts
    
    def calculate_var_metrics(self, portfolio_value: float, risk_level: str, 
                            time_horizon_days: int = 1) -> Dict:
        """Calculate Value at Risk metrics for portfolio"""
        
        # Base volatility assumptions by risk level
        volatility_map = {
            'LOW': 0.15,
            'MEDIUM': 0.25,
            'HIGH': 0.35,
            'CRITICAL': 0.50
        }
        
        daily_vol = volatility_map.get(risk_level, 0.25) / np.sqrt(252)
        horizon_vol = daily_vol * np.sqrt(time_horizon_days)
        
        # Calculate VaR at different confidence levels
        var_95 = portfolio_value * 1.645 * horizon_vol  # 95% VaR
        var_99 = portfolio_value * 2.326 * horizon_vol  # 99% VaR
        
        # Expected Shortfall (Conditional VaR)
        es_95 = var_95 * 1.3  # Approximation
        es_99 = var_99 * 1.2  # Approximation
        
        return {
            'var_95': var_95,
            'var_99': var_99,
            'expected_shortfall_95': es_95,
            'expected_shortfall_99': es_99,
            'time_horizon_days': time_horizon_days,
            'portfolio_value': portfolio_value,
            'daily_volatility': daily_vol,
            'risk_level': risk_level
        }
    
    def generate_risk_report(self, assessment: Dict) -> str:
        """Generate a comprehensive risk report"""
        
        report = f"""
TOKYO MARKET RISK ASSESSMENT REPORT
Generated: {assessment['timestamp'].strftime('%Y-%m-%d %H:%M:%S JST')}

OVERALL RISK LEVEL: {assessment['combined_risk']['level']}
Combined Risk Score: {assessment['combined_risk']['score']:.3f}
Confidence Level: {assessment['combined_risk']['confidence']:.1%}

COMPONENT ANALYSIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 EARTHQUAKE RISK: {assessment['earthquake_risk']['level']} ({assessment['earthquake_risk']['score']:.3f})
   Recent Activity: {assessment['earthquake_risk'].get('raw_data', {}).get('event_count', 0)} events
   Max Magnitude: M{assessment['earthquake_risk'].get('raw_data', {}).get('max_magnitude', 0):.1f}
   Distance: {assessment['earthquake_risk'].get('raw_data', {}).get('closest_distance_km', 'N/A')} km

📊 MARKET RISK: {assessment['market_risk']['level']} ({assessment['market_risk']['score']:.3f})
   Markets Analyzed: {assessment['market_risk'].get('processed_markets', 0)}
   Volatility Factor: {assessment['market_risk']['factors']['volatility']:.3f}
   Momentum Factor: {assessment['market_risk']['factors']['momentum']:.3f}

🔗 CORRELATION RISK: {assessment['correlation_risk']['level']} ({assessment['correlation_risk']['score']:.3f})
   Mean Correlation: {assessment['correlation_risk'].get('raw_metrics', {}).get('mean_abs_correlation', 0):.3f}
   Max Correlation: {assessment['correlation_risk'].get('raw_metrics', {}).get('max_abs_correlation', 0):.3f}

ACTIVE ALERTS: {len(assessment['alert_triggers'])}
"""
        
        # Add alerts
        if assessment['alert_triggers']:
            report += "\n🚨 ACTIVE ALERTS:\n"
            for alert in assessment['alert_triggers']:
                report += f"   {alert['level']}: {alert['message']}\n"
        
        # Add top recommendations
        if assessment['recommendations']:
            report += "\n📋 TOP RECOMMENDATIONS:\n"
            for rec in assessment['recommendations'][:3]:  # Top 3
                report += f"   {rec['priority']}: {rec['action']}\n"
        
        return report 