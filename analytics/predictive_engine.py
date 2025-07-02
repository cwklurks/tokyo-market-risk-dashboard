"""
Predictive Engine for Tokyo Market Risk Dashboard
Machine learning models for risk forecasting and anomaly detection
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class PredictiveEngine:
    """
    ML-powered predictive analytics for risk forecasting
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.risk_forecaster = None
        self.volatility_forecaster = None
        self.anomaly_detector = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        
    def prepare_features(self, market_data: Dict, earthquake_data: List, 
                        risk_assessment: Dict) -> pd.DataFrame:
        """Extract features for ML models from multiple data sources"""
        features = {}
        
        # Market features
        if market_data:
            for ticker, data in market_data.items():
                if data and isinstance(data, dict):
                    features[f'{ticker}_price'] = data.get('current_price', 0)
                    features[f'{ticker}_change'] = data.get('change_percent', 0)
                    features[f'{ticker}_volatility'] = data.get('volatility', 0.2)
                    features[f'{ticker}_volume_ratio'] = 1.0  # Placeholder
        
        # Earthquake features
        if earthquake_data:
            recent_quakes = earthquake_data[:10]  # Last 10 earthquakes
            features['quake_count_24h'] = len([eq for eq in recent_quakes 
                                             if self._is_recent(eq.get('time', ''), hours=24)])
            features['quake_count_72h'] = len([eq for eq in recent_quakes 
                                             if self._is_recent(eq.get('time', ''), hours=72)])
            features['max_magnitude_24h'] = max([eq.get('magnitude', 0) for eq in recent_quakes 
                                               if self._is_recent(eq.get('time', ''), hours=24)] or [0])
            features['avg_magnitude_72h'] = np.mean([eq.get('magnitude', 0) for eq in recent_quakes 
                                                   if self._is_recent(eq.get('time', ''), hours=72)] or [0])
        
        # Risk assessment features
        if risk_assessment:
            features['earthquake_risk_score'] = risk_assessment.get('earthquake_risk', {}).get('score', 0)
            features['market_risk_score'] = risk_assessment.get('market_risk', {}).get('score', 0)
            features['correlation_risk_score'] = risk_assessment.get('correlation_risk', {}).get('score', 0)
            features['combined_risk_score'] = risk_assessment.get('combined_risk', {}).get('score', 0)
        
        # Time-based features
        now = datetime.now()
        features['hour_of_day'] = now.hour
        features['day_of_week'] = now.weekday()
        features['is_weekend'] = 1 if now.weekday() >= 5 else 0
        
        # Convert to DataFrame
        df = pd.DataFrame([features])
        self.feature_names = list(features.keys())
        
        return df
    
    def forecast_risk(self, current_features: pd.DataFrame, 
                     forecast_days: int = 7) -> Dict:
        """Generate risk forecasts for the next N days"""
        
        # Use simple statistical forecasting since models aren't trained
        return self._statistical_forecast(current_features, forecast_days)
    
    def generate_scenarios(self, current_features: pd.DataFrame, 
                         num_scenarios: int = 1000) -> Dict:
        """Generate Monte Carlo scenarios for stress testing"""
        
        scenarios = {
            'normal': [],
            'earthquake': [],
            'market_crash': [],
            'combined_crisis': []
        }
        
        # Define realistic base risk levels for each scenario
        base_risks = {
            'normal': 0.15,      # 15% base risk for normal conditions
            'earthquake': 0.35,  # 35% base risk during earthquakes
            'market_crash': 0.45, # 45% base risk during market stress
            'combined_crisis': 0.65 # 65% base risk during combined events
        }
        
        for i in range(num_scenarios):
            # Normal scenario - low volatility around base
            normal_risk = base_risks['normal'] + np.random.normal(0, 0.08)
            normal_risk = max(0.05, min(0.4, normal_risk))  # Cap between 5-40%
            scenarios['normal'].append(normal_risk)
            
            # Earthquake scenario - moderate earthquake impact
            eq_magnitude = np.random.uniform(5.5, 7.5)  # More realistic range
            eq_risk = base_risks['earthquake']
            if eq_magnitude > 7.0:
                eq_risk += 0.15  # Additional risk for major quakes
            elif eq_magnitude > 6.5:
                eq_risk += 0.1   # Additional risk for strong quakes
            eq_risk += np.random.normal(0, 0.12)
            eq_risk = max(0.1, min(0.8, eq_risk))  # Cap between 10-80%
            scenarios['earthquake'].append(eq_risk)
            
            # Market crash scenario - financial stress
            crash_severity = np.random.uniform(0.1, 0.4)  # 10-40% market decline
            crash_risk = base_risks['market_crash'] + crash_severity * 0.5
            crash_risk += np.random.normal(0, 0.1)
            crash_risk = max(0.2, min(0.85, crash_risk))  # Cap between 20-85%
            scenarios['market_crash'].append(crash_risk)
            
            # Combined crisis - worst case but still realistic
            combined_risk = base_risks['combined_crisis']
            combined_risk += np.random.uniform(0.1, 0.25)  # Additional stress
            combined_risk += np.random.normal(0, 0.08)
            combined_risk = max(0.4, min(0.95, combined_risk))  # Cap between 40-95%
            scenarios['combined_crisis'].append(combined_risk)
        
        # Calculate statistics for each scenario type
        results = {}
        for scenario_type, risks in scenarios.items():
            results[scenario_type] = {
                'mean_risk': np.mean(risks),
                'std_risk': np.std(risks),
                'var_95': np.percentile(risks, 95),
                'var_99': np.percentile(risks, 99),
                'worst_case': np.max(risks),
                'probability_high_risk': len([r for r in risks if r > 0.7]) / len(risks)
            }
        
        return results
    
    def detect_anomalies(self, features: pd.DataFrame) -> Dict:
        """Detect anomalies in current market conditions"""
        return self._statistical_anomaly_detection(features)
    
    # Private helper methods
    def _is_recent(self, time_str: str, hours: int) -> bool:
        """Check if earthquake time is within specified hours"""
        try:
            # Parse various time formats
            for fmt in ['%Y/%m/%d %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    eq_time = datetime.strptime(time_str.split('.')[0], fmt)
                    return (datetime.now() - eq_time).total_seconds() < hours * 3600
                except:
                    continue
            return False
        except:
            return False
    
    def _statistical_forecast(self, features: pd.DataFrame, days: int) -> Dict:
        """Simple statistical forecast when ML models unavailable"""
        base_risk = features.get('combined_risk_score', [0.3])[0] if not features.empty else 0.3
        
        forecasts = []
        for day in range(days):
            # Simple random walk
            risk = base_risk + np.random.normal(0, 0.05)
            risk = max(0, min(1, risk))
            
            forecasts.append({
                'day': day + 1,
                'date': (datetime.now() + timedelta(days=day+1)).strftime('%Y-%m-%d'),
                'risk_score': risk,
                'volatility': 0.2 + np.random.normal(0, 0.02),
                'confidence': 0.5  # Lower confidence for statistical method
            })
        
        return {
            'current_risk_prediction': base_risk,
            'current_volatility_prediction': 0.2,
            'anomaly_detected': False,
            'anomaly_score': 0,
            'daily_forecasts': forecasts,
            'prediction_intervals': {
                'risk_lower': base_risk - 0.2,
                'risk_upper': base_risk + 0.2
            },
            'model_confidence': 0.5
        }
    
    def _add_noise(self, df: pd.DataFrame, volatility: float) -> pd.DataFrame:
        """Add random noise to features for scenario generation"""
        noisy_df = df.copy()
        for col in noisy_df.columns:
            if noisy_df[col].dtype in [np.float64, np.int64]:
                noise = np.random.normal(0, volatility * abs(noisy_df[col].values[0]))
                noisy_df[col] += noise
        return noisy_df
    
    def _calculate_scenario_risk(self, features: pd.DataFrame) -> float:
        """Calculate risk score for a scenario (0-1 scale, but allow >1 for extreme scenarios)"""
        risk = 0.2  # Lower base risk
        
        # Earthquake contribution (more nuanced)
        if 'max_magnitude_24h' in features.columns:
            magnitude = features['max_magnitude_24h'].values[0]
            if magnitude > 7.0:
                risk += 0.4  # High earthquake risk
            elif magnitude > 6.0:
                risk += 0.2  # Medium earthquake risk
            elif magnitude > 5.0:
                risk += 0.1  # Low earthquake risk
        
        # Market volatility contribution (more realistic)
        vol_cols = [col for col in features.columns if 'volatility' in col]
        if vol_cols:
            avg_vol = features[vol_cols].mean().mean()
            risk += min(0.3, avg_vol * 0.5)  # Cap volatility contribution
        
        # Price change contribution
        price_cols = [col for col in features.columns if 'price' in col]
        if price_cols:
            # Check for negative price changes (market stress)
            for col in price_cols:
                if col in features.columns:
                    price_val = features[col].values[0]
                    if price_val < 0:  # Negative price change
                        risk += abs(price_val) * 0.01  # Small contribution per % decline
        
        return risk  # Don't cap at 1.0 to show extreme scenarios
    
    def _statistical_anomaly_detection(self, features: pd.DataFrame) -> Dict:
        """Simple anomaly detection without trained models"""
        anomaly_score = 0
        contributors = []
        
        # Check for extreme values
        for col in features.columns:
            if features[col].dtype in [np.float64, np.int64]:
                value = features[col].values[0]
                
                # Simple thresholds
                if 'magnitude' in col and value > 6:
                    anomaly_score += 0.3
                    contributors.append((col, value))
                elif 'volatility' in col and value > 0.5:
                    anomaly_score += 0.2
                    contributors.append((col, value))
                elif 'risk_score' in col and value > 0.7:
                    anomaly_score += 0.2
                    contributors.append((col, value))
        
        is_anomaly = anomaly_score > 0.5
        
        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': anomaly_score,
            'anomaly_probability': min(1.0, anomaly_score),
            'top_contributors': contributors[:5],
            'recommendation': self._get_anomaly_recommendation(is_anomaly, contributors)
        }
    
    def _get_anomaly_recommendation(self, is_anomaly: bool, 
                                   contributors: List[Tuple[str, float]]) -> str:
        """Generate recommendation based on anomaly detection"""
        if not is_anomaly:
            return "No significant anomalies detected. Continue normal operations."
        
        recommendations = []
        
        for feature, value in contributors:
            if 'magnitude' in feature:
                recommendations.append("High seismic activity detected. Review earthquake hedging positions.")
            elif 'volatility' in feature:
                recommendations.append("Extreme market volatility. Consider reducing position sizes.")
            elif 'risk_score' in feature:
                recommendations.append("Elevated risk levels. Implement defensive strategies.")
        
        return " ".join(recommendations[:2]) if recommendations else "Anomaly detected. Review all positions." 