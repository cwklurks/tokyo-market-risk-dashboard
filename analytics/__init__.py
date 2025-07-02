"""
Analytics module for Tokyo Market Risk Dashboard
"""

from .risk_engine import RiskEngine
from .black_scholes import BlackScholesEngine
from .network_analysis import NetworkAnalysisEngine
from .predictive_engine import PredictiveEngine

try:
    from .predictive_engine import PredictiveAnalyticsEngine
    __all__ = ['RiskEngine', 'BlackScholesEngine', 'NetworkAnalysisEngine', 'PredictiveAnalyticsEngine']
except ImportError:
    # Fallback if scikit-learn has compatibility issues
    PredictiveAnalyticsEngine = None
    __all__ = ['RiskEngine', 'BlackScholesEngine', 'NetworkAnalysisEngine', 'PredictiveEngine'] 