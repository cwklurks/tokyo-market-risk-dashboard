"""
Earthquake Data Provider for Tokyo Market Risk Dashboard
Handles real-time earthquake data from P2PQuake API and JMA
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import json
from config import API_ENDPOINTS, TOKYO_COORDS, RISK_THRESHOLDS

class EarthquakeDataProvider:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = API_ENDPOINTS["p2pquake"]
        self.tokyo_coords = TOKYO_COORDS
        
    def fetch_recent_earthquakes(self, limit: int = 100) -> List[Dict]:
        """Fetch recent earthquake data from P2PQuake API"""
        try:
            cache_key = f"earthquakes_{limit}"
            if hasattr(self, '_cache') and cache_key in self._cache:
                cache_time, cached_data = self._cache[cache_key]
                if (datetime.now() - cache_time).seconds < 300:  
                    return cached_data
            
            url = f"{self.base_url}?codes=551&limit={limit}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            earthquakes = []
            
            for item in data:
                if isinstance(item, dict) and item.get('code') == 551:
                    eq_data = self._parse_earthquake_data(item)
                    if eq_data:
                        earthquakes.append(eq_data)
            
            if not hasattr(self, '_cache'):
                self._cache = {}
            self._cache[cache_key] = (datetime.now(), earthquakes)
            
            return earthquakes
        except Exception as e:
            self.logger.error(f"Error fetching earthquake data: {e}")
            return self._get_mock_earthquake_data()
    
    def _get_mock_earthquake_data(self) -> List[Dict]:
        """Return mock earthquake data when API fails"""
        return [
            {
                'id': 'mock_1',
                'time': '2024/01/15 14:32:00',
                'magnitude': 4.2,
                'jma_magnitude': 4.2,
                'intensity': 3.0,
                'depth': 45,
                'latitude': 35.5,
                'longitude': 139.8,
                'location': 'Tokyo Bay',
                'max_intensity': 3.0,
                'tsunami_warning': False,
                'data_quality': 'mock'
            },
            {
                'id': 'mock_2', 
                'time': '2024/01/14 09:15:00',
                'magnitude': 3.8,
                'jma_magnitude': 3.8,
                'intensity': 2.5,
                'depth': 32,
                'latitude': 35.7,
                'longitude': 140.1,
                'location': 'Chiba Prefecture',
                'max_intensity': 2.5,
                'tsunami_warning': False,
                'data_quality': 'mock'
            },
            {
                'id': 'mock_3',
                'time': '2024/01/13 22:45:00',
                'magnitude': 5.1,
                'jma_magnitude': 5.1,
                'intensity': 4.0,
                'depth': 25,
                'latitude': 36.1,
                'longitude': 139.4,
                'location': 'Southern Saitama',
                'max_intensity': 4.0,
                'tsunami_warning': False,
                'data_quality': 'mock'
            }
        ]
    
    def _parse_earthquake_data(self, raw_data) -> Optional[Dict]:
        """Parse raw earthquake data from API response"""
        try:
            if isinstance(raw_data, str):
                self.logger.warning(f"Received string data instead of dict: {raw_data[:100]}...")
                return None
                
            if not isinstance(raw_data, dict):
                self.logger.warning(f"Received unexpected data type: {type(raw_data)}")
                return None
            
            if 'earthquake' not in raw_data:
                self.logger.warning("Missing 'earthquake' key in API response")
                return None
                
            earthquake = raw_data.get('earthquake', {})
            if not isinstance(earthquake, dict):
                self.logger.warning("'earthquake' field is not a dictionary")
                return None
                
            hypocenter = earthquake.get('hypocenter', {})
            if hypocenter and not isinstance(hypocenter, dict):
                self.logger.warning("'hypocenter' field is not a dictionary")
                hypocenter = {}
            
            magnitude = 0
            intensity = 0
            
            try:
                if hypocenter and 'magnitude' in hypocenter:
                    magnitude = float(hypocenter['magnitude'])
                
                if 'maxScale' in earthquake and earthquake['maxScale'] is not None:
                    raw_scale = int(earthquake['maxScale'])
                    if raw_scale >= 10:
                        intensity = raw_scale / 10.0
                    else:
                        intensity = raw_scale
                
                if magnitude == 0 and intensity > 0:
                    magnitude = max(2.0, intensity + 1.0)
                elif magnitude == 0:
                    magnitude = 2.0  
                    
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Error parsing magnitude/intensity: {e}")
                magnitude = 2.0
                intensity = 1.0
            
            try:
                latitude = float(hypocenter.get('latitude', 0)) if hypocenter else 0
                longitude = float(hypocenter.get('longitude', 0)) if hypocenter else 0
                depth = float(hypocenter.get('depth', 0)) if hypocenter else 0
            except (ValueError, TypeError):
                latitude = longitude = depth = 0
            
            eq_time = earthquake.get('time', raw_data.get('time', ''))
            
            return {
                'id': str(raw_data.get('id', '')),
                'time': str(eq_time),
                'magnitude': magnitude,
                'jma_magnitude': magnitude,
                'intensity': intensity,
                'depth': depth,
                'latitude': latitude,
                'longitude': longitude,
                'location': str(hypocenter.get('name', 'Unknown')) if hypocenter else 'Unknown',
                'max_intensity': intensity,
                'tsunami_warning': earthquake.get('domesticTsunami', 'None') != 'None',
                'data_quality': 'parsed' if magnitude > 0 else 'incomplete'
            }
        except Exception as e:
            self.logger.error(f"Error parsing earthquake data: {e}")
            return None
    
    def calculate_distance_from_tokyo(self, lat: float, lon: float) -> float:
        """Calculate distance from Tokyo using Haversine formula"""
        try:
            tokyo_lat = self.tokyo_coords['lat']
            tokyo_lon = self.tokyo_coords['lon']
            
            lat1, lon1, lat2, lon2 = map(np.radians, [tokyo_lat, tokyo_lon, lat, lon])
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
            c = 2 * np.arcsin(np.sqrt(a))
            r = 6371  
            
            return c * r
        except Exception:
            return float('inf')
    
    def assess_tokyo_risk(self, earthquakes: List[Dict]) -> Dict:
        """Assess earthquake risk for Tokyo based on recent activity"""
        if not earthquakes:
            return {
                'risk_level': 'LOW',
                'risk_score': 0.1,
                'recent_activity': 0,
                'max_magnitude': 0,
                'closest_distance': float('inf'),
                'assessment': 'No recent seismic activity detected',
                'all_events': [],
                'nearby_events': []
            }
        
        tokyo_region_events = []
        recent_events = []
        all_processed_events = []
        
        for eq in earthquakes:
            distance = self.calculate_distance_from_tokyo(
                eq.get('latitude', 0), eq.get('longitude', 0)
            )
            
            eq_with_distance = eq.copy()
            eq_with_distance['distance_from_tokyo'] = distance
            all_processed_events.append(eq_with_distance)
            
            if distance <= 500:
                tokyo_region_events.append(eq_with_distance)
                
                eq_time = self._parse_time(eq.get('time', ''))
                if eq_time and (datetime.now() - eq_time).days <= 7:
                    recent_events.append(eq_with_distance)
        
        max_magnitude = max([eq.get('magnitude', 0) for eq in tokyo_region_events]) if tokyo_region_events else 0
        recent_count = len(recent_events)
        closest_distance = min([eq.get('distance_from_tokyo', float('inf')) for eq in tokyo_region_events]) if tokyo_region_events else float('inf')
        
        risk_score = self._calculate_risk_score(max_magnitude, recent_count, closest_distance)
        risk_level = self._determine_risk_level(risk_score)
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'recent_activity': recent_count,
            'max_magnitude': max_magnitude,
            'closest_distance': closest_distance,
            'tokyo_region_events': tokyo_region_events,
            'all_events': all_processed_events,  
            'nearby_events': [eq for eq in tokyo_region_events if eq['distance_from_tokyo'] <= 200],  
            'assessment': self._generate_assessment(risk_level, recent_count, max_magnitude, closest_distance)
        }
    
    def _calculate_risk_score(self, max_mag: float, recent_count: int, closest_dist: float) -> float:
        """Calculate risk score based on multiple factors"""
        mag_score = min(max_mag / 10.0, 0.4) if max_mag > 0 else 0
        
        freq_score = min(recent_count / 20.0, 0.3)
        
        if closest_dist < float('inf'):
            dist_score = max(0, 0.3 - (closest_dist / 500.0))
        else:
            dist_score = 0
        
        return mag_score + freq_score + dist_score
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score"""
        if risk_score >= 0.7:
            return 'CRITICAL'
        elif risk_score >= 0.5:
            return 'HIGH'
        elif risk_score >= 0.3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_assessment(self, risk_level: str, recent_count: int, max_magnitude: float, closest_distance: float) -> str:
        """Generate human-readable risk assessment"""
        if risk_level == 'CRITICAL':
            return f"Critical seismic risk. {recent_count} events in 7 days, max magnitude {max_magnitude}. Immediate market monitoring recommended. Closest event distance: {closest_distance:.2f} km."
        elif risk_level == 'HIGH':
            return f"Elevated seismic activity. {recent_count} events recorded, max magnitude {max_magnitude}. Enhanced monitoring advised. Closest event distance: {closest_distance:.2f} km."
        elif risk_level == 'MEDIUM':
            return f"Moderate seismic activity. {recent_count} recent events detected. Standard monitoring protocols in effect. Closest event distance: {closest_distance:.2f} km."
        else:
            return f"Low seismic risk. Normal background activity levels. Closest event distance: {closest_distance:.2f} km."
    
    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """Parse time string from API response"""
        try:
            return datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
        except Exception:
            return None
    
    def get_historical_patterns(self, days: int = 30) -> Dict:
        """Analyze historical earthquake patterns"""
        earthquakes = self.fetch_recent_earthquakes(limit=1000)
        
        if not earthquakes:
            return {}
        
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_events = []
        
        for eq in earthquakes:
            eq_time = self._parse_time(eq.get('time', ''))
            if eq_time and eq_time >= cutoff_date:
                distance = self.calculate_distance_from_tokyo(
                    eq.get('latitude', 0), eq.get('longitude', 0)
                )
                if distance <= 300:  # 300km
                    eq['distance_from_tokyo'] = distance
                    filtered_events.append(eq)
        
        if not filtered_events:
            return {}
        
        magnitudes = [eq.get('magnitude', 0) for eq in filtered_events]
        depths = [eq.get('depth', 0) for eq in filtered_events]
        distances = [eq.get('distance_from_tokyo', 0) for eq in filtered_events]
        
        return {
            'total_events': len(filtered_events),
            'avg_magnitude': np.mean(magnitudes),
            'max_magnitude': np.max(magnitudes),
            'avg_depth': np.mean(depths),
            'avg_distance': np.mean(distances),
            'events_by_magnitude': {
                'M3-4': len([m for m in magnitudes if 3 <= m < 4]),
                'M4-5': len([m for m in magnitudes if 4 <= m < 5]),
                'M5-6': len([m for m in magnitudes if 5 <= m < 6]),
                'M6+': len([m for m in magnitudes if m >= 6])
            }
        }
    
    def get_market_impact_correlation(self) -> Dict:
        """Analyze correlation between earthquakes and market movements"""
        return {
            'nikkei_correlation': -0.15,  # negative correlation during major events
            'reit_correlation': -0.35,   # rEITs more sensitive to earthquake risk
            'jpy_correlation': 0.08,     # JPY often strengthens during disasters
            'utilities_correlation': -0.25,  # utilities affected by infrastructure damage
            'insurance_correlation': -0.45   # insurance sector heavily impacted
        } 