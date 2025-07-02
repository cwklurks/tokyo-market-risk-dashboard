"""
Black-Scholes Options Pricing Engine for Tokyo Market Risk Dashboard
Adapted from advanced options pricing model with Japanese market considerations
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import minimize_scalar
from numpy import log, sqrt, exp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

class BlackScholesEngine:
    """
    Advanced Black-Scholes option pricing engine with Japanese market adaptations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def create_model(self, S: float, K: float, T: float, r: float, sigma: float):
        """Create a Black-Scholes model instance"""
        return BlackScholesModel(S, K, T, r, sigma)
    
    def calculate_option_prices(self, S: float, K: float, T: float, r: float, sigma: float) -> Dict:
        """Calculate both call and put option prices with Greeks"""
        model = self.create_model(S, K, T, r, sigma)
        
        return {
            'call_price': model.call_price(),
            'put_price': model.put_price(),
            'greeks': {
                'delta_call': model.delta_call(),
                'delta_put': model.delta_put(),
                'gamma': model.gamma(),
                'theta_call': model.theta_call(),
                'theta_put': model.theta_put(),
                'vega': model.vega(),
                'rho_call': model.rho_call(),
                'rho_put': model.rho_put()
            }
        }
    
    def implied_volatility(self, option_price: float, S: float, K: float, T: float, r: float, option_type: str = 'call') -> float:
        """Calculate implied volatility from market option price"""
        def objective(sigma):
            model = self.create_model(S, K, T, r, sigma)
            if option_type == 'call':
                return abs(model.call_price() - option_price)
            else:
                return abs(model.put_price() - option_price)
        
        try:
            result = minimize_scalar(objective, bounds=(0.001, 5), method='bounded')
            return result.x
        except Exception as e:
            self.logger.error(f"Error calculating implied volatility: {e}")
            return 0.25  # Default volatility
    
    def monte_carlo_pricing(self, S: float, K: float, T: float, r: float, sigma: float, 
                          num_simulations: int = 10000, option_type: str = 'call') -> Dict:
        """Monte Carlo option pricing with disaster scenarios for Japanese markets"""
        np.random.seed(42)
        
        # Standard Monte Carlo
        Z = np.random.standard_normal(num_simulations)
        ST = S * np.exp((r - 0.5 * sigma ** 2) * T + sigma * np.sqrt(T) * Z)
        
        if option_type == 'call':
            payoffs = np.maximum(ST - K, 0)
        else:
            payoffs = np.maximum(K - ST, 0)
        
        standard_price = np.exp(-r * T) * np.mean(payoffs)
        standard_se = np.std(payoffs) / np.sqrt(num_simulations)
        
        # Japanese market specific: Add earthquake scenario adjustment
        disaster_adjusted_price = self._apply_disaster_scenario(
            standard_price, S, K, T, option_type, earthquake_prob=0.05
        )
        
        return {
            'standard_price': standard_price,
            'disaster_adjusted_price': disaster_adjusted_price,
            'standard_error': standard_se,
            'simulated_prices': ST,
            'convergence_ratio': abs(disaster_adjusted_price - standard_price) / standard_price
        }
    
    def _apply_disaster_scenario(self, base_price: float, S: float, K: float, T: float, 
                               option_type: str, earthquake_prob: float = 0.05) -> float:
        """Apply earthquake disaster scenario adjustment for Japanese markets"""
        # Earthquake impact: 15-25% price drop, 50% volatility spike
        earthquake_drop = 0.20  # 20% average drop
        vol_spike = 0.50       # 50% volatility increase
        
        # Calculate disaster scenario price
        disaster_S = S * (1 - earthquake_drop)
        disaster_vol = 0.25 * (1 + vol_spike)  # Assume base vol of 25%
        
        # Re-price option under disaster scenario
        disaster_model = self.create_model(disaster_S, K, T, 0.01, disaster_vol)  # Lower rates during crisis
        
        if option_type == 'call':
            disaster_price = disaster_model.call_price()
        else:
            disaster_price = disaster_model.put_price()
        
        # Weight the scenarios
        weighted_price = (1 - earthquake_prob) * base_price + earthquake_prob * disaster_price
        
        return weighted_price
    
    def calculate_portfolio_greeks(self, positions: List[Dict]) -> Dict:
        """Calculate portfolio-level Greeks for multiple positions"""
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        total_rho = 0
        
        for position in positions:
            model = self.create_model(
                position['S'], position['K'], position['T'], 
                position['r'], position['sigma']
            )
            
            multiplier = position.get('quantity', 1)
            if position.get('is_short', False):
                multiplier *= -1
            
            if position['option_type'].lower() == 'call':
                total_delta += model.delta_call() * multiplier
                total_theta += model.theta_call() * multiplier
                total_rho += model.rho_call() * multiplier
            else:
                total_delta += model.delta_put() * multiplier
                total_theta += model.theta_put() * multiplier
                total_rho += model.rho_put() * multiplier
            
            total_gamma += model.gamma() * multiplier
            total_vega += model.vega() * multiplier
        
        return {
            'portfolio_delta': total_delta,
            'portfolio_gamma': total_gamma,
            'portfolio_theta': total_theta,
            'portfolio_vega': total_vega,
            'portfolio_rho': total_rho
        }
    
    def get_japanese_market_adjustments(self, base_vol: float, earthquake_risk_level: str) -> float:
        """Adjust volatility based on Japanese market specific risks"""
        adjustments = {
            'LOW': 1.0,
            'MEDIUM': 1.15,
            'HIGH': 1.35,
            'CRITICAL': 1.65
        }
        
        adjustment_factor = adjustments.get(earthquake_risk_level, 1.0)
        return base_vol * adjustment_factor


class BlackScholesModel:
    """
    Core Black-Scholes model implementation
    """
    
    def __init__(self, S: float, K: float, T: float, r: float, sigma: float):
        self.S = S      # Current stock price
        self.K = K      # Strike price
        self.T = T      # Time to maturity (in years)
        self.r = r      # Risk-free rate
        self.sigma = sigma  # Volatility
        
    def d1(self) -> float:
        """Calculate d1 parameter"""
        return (log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * sqrt(self.T))
    
    def d2(self) -> float:
        """Calculate d2 parameter"""
        return self.d1() - self.sigma * sqrt(self.T)
    
    def call_price(self) -> float:
        """Calculate European call option price"""
        try:
            if self.T <= 0:
                return max(self.S - self.K, 0)
            return self.S * norm.cdf(self.d1()) - self.K * exp(-self.r * self.T) * norm.cdf(self.d2())
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def put_price(self) -> float:
        """Calculate European put option price"""
        try:
            if self.T <= 0:
                return max(self.K - self.S, 0)
            return self.K * exp(-self.r * self.T) * norm.cdf(-self.d2()) - self.S * norm.cdf(-self.d1())
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def delta_call(self) -> float:
        """Calculate call option delta"""
        try:
            if self.T <= 0:
                return 1.0 if self.S > self.K else 0.0
            return norm.cdf(self.d1())
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def delta_put(self) -> float:
        """Calculate put option delta"""
        try:
            if self.T <= 0:
                return -1.0 if self.S < self.K else 0.0
            return -norm.cdf(-self.d1())
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def gamma(self) -> float:
        """Calculate option gamma"""
        try:
            if self.T <= 0:
                return 0.0
            return norm.pdf(self.d1()) / (self.S * self.sigma * sqrt(self.T))
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def theta_call(self) -> float:
        """Calculate call option theta (daily)"""
        try:
            if self.T <= 0:
                return 0.0
            term1 = -self.S * norm.pdf(self.d1()) * self.sigma / (2 * sqrt(self.T))
            term2 = -self.r * self.K * exp(-self.r * self.T) * norm.cdf(self.d2())
            return (term1 + term2) / 365
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def theta_put(self) -> float:
        """Calculate put option theta (daily)"""
        try:
            if self.T <= 0:
                return 0.0
            term1 = -self.S * norm.pdf(self.d1()) * self.sigma / (2 * sqrt(self.T))
            term2 = self.r * self.K * exp(-self.r * self.T) * norm.cdf(-self.d2())
            return (term1 + term2) / 365
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def vega(self) -> float:
        """Calculate option vega"""
        try:
            if self.T <= 0:
                return 0.0
            return self.S * norm.pdf(self.d1()) * sqrt(self.T) / 100
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def rho_call(self) -> float:
        """Calculate call option rho"""
        try:
            if self.T <= 0:
                return 0.0
            return self.K * self.T * exp(-self.r * self.T) * norm.cdf(self.d2()) / 100
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def rho_put(self) -> float:
        """Calculate put option rho"""
        try:
            if self.T <= 0:
                return 0.0
            return -self.K * self.T * exp(-self.r * self.T) * norm.cdf(-self.d2()) / 100
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def get_all_greeks(self) -> Dict:
        """Get all Greeks in a single dictionary"""
        return {
            'delta_call': self.delta_call(),
            'delta_put': self.delta_put(),
            'gamma': self.gamma(),
            'theta_call': self.theta_call(),
            'theta_put': self.theta_put(),
            'vega': self.vega(),
            'rho_call': self.rho_call(),
            'rho_put': self.rho_put()
        }


class JapaneseOptionsAnalyzer:
    """
    Specialized options analyzer for Japanese markets with disaster risk modeling
    """
    
    def __init__(self, bs_engine: BlackScholesEngine):
        self.bs_engine = bs_engine
        self.logger = logging.getLogger(__name__)
    
    def analyze_nikkei_option(self, spot_price: float, strike: float, days_to_expiry: int, 
                             implied_vol: float, earthquake_risk: str = 'LOW') -> Dict:
        """Analyze Nikkei option with earthquake risk adjustment"""
        
        # Japanese market parameters
        risk_free_rate = 0.005  # BoJ rate typically near zero
        time_to_maturity = days_to_expiry / 365.0
        
        # Adjust volatility for earthquake risk
        adjusted_vol = self.bs_engine.get_japanese_market_adjustments(implied_vol, earthquake_risk)
        
        # Calculate standard pricing
        results = self.bs_engine.calculate_option_prices(
            spot_price, strike, time_to_maturity, risk_free_rate, adjusted_vol
        )
        
        # Add Monte Carlo with disaster scenarios
        mc_results = self.bs_engine.monte_carlo_pricing(
            spot_price, strike, time_to_maturity, risk_free_rate, adjusted_vol
        )
        
        # Calculate risk metrics
        risk_metrics = self._calculate_japanese_risk_metrics(
            spot_price, strike, time_to_maturity, adjusted_vol, earthquake_risk
        )
        
        return {
            'standard_pricing': results,
            'disaster_adjusted_pricing': mc_results,
            'risk_metrics': risk_metrics,
            'market_conditions': {
                'earthquake_risk_level': earthquake_risk,
                'volatility_adjustment': adjusted_vol / implied_vol,
                'time_to_expiry': days_to_expiry,
                'risk_free_rate': risk_free_rate
            }
        }
    
    def _calculate_japanese_risk_metrics(self, S: float, K: float, T: float, 
                                       sigma: float, earthquake_risk: str) -> Dict:
        """Calculate Japan-specific risk metrics"""
        
        # VaR calculation with earthquake scenarios
        var_95 = self._calculate_var(S, sigma, T, confidence=0.95)
        var_99 = self._calculate_var(S, sigma, T, confidence=0.99)
        
        # Earthquake impact probability
        earthquake_probs = {
            'LOW': 0.02,
            'MEDIUM': 0.05,
            'HIGH': 0.10,
            'CRITICAL': 0.20
        }
        
        earthquake_prob = earthquake_probs.get(earthquake_risk, 0.02)
        
        # Maximum drawdown estimation
        max_drawdown = self._estimate_max_drawdown(S, sigma, T, earthquake_prob)
        
        return {
            'var_95': var_95,
            'var_99': var_99,
            'earthquake_probability': earthquake_prob,
            'estimated_max_drawdown': max_drawdown,
            'volatility_percentile': self._get_volatility_percentile(sigma),
            'risk_rating': self._get_risk_rating(sigma, earthquake_risk)
        }
    
    def _calculate_var(self, S: float, sigma: float, T: float, confidence: float) -> float:
        """Calculate Value at Risk"""
        z_score = norm.ppf(1 - confidence)
        return S * (1 - np.exp(z_score * sigma * np.sqrt(T)))
    
    def _estimate_max_drawdown(self, S: float, sigma: float, T: float, earthquake_prob: float) -> float:
        """Estimate maximum potential drawdown"""
        # Normal market conditions
        normal_drawdown = S * sigma * np.sqrt(T) * 2.5  # ~99% confidence
        
        # Earthquake scenario
        earthquake_drawdown = S * 0.25  # 25% drop assumption
        
        # Weighted estimate
        return normal_drawdown * (1 - earthquake_prob) + earthquake_drawdown * earthquake_prob
    
    def _get_volatility_percentile(self, sigma: float) -> str:
        """Get volatility percentile for Japanese markets"""
        if sigma < 0.15:
            return "Low (bottom 25%)"
        elif sigma < 0.25:
            return "Normal (25-75%)"
        elif sigma < 0.40:
            return "High (75-95%)"
        else:
            return "Extreme (top 5%)"
    
    def _get_risk_rating(self, sigma: float, earthquake_risk: str) -> str:
        """Comprehensive risk rating"""
        vol_score = min(int(sigma * 10), 5)
        earthquake_score = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}.get(earthquake_risk, 1)
        
        total_score = vol_score + earthquake_score
        
        if total_score <= 3:
            return "Conservative"
        elif total_score <= 5:
            return "Moderate"
        elif total_score <= 7:
            return "Aggressive"
        else:
            return "Speculative" 